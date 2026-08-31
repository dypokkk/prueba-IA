import json
import asyncio
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

from app.config import settings

class TelegramService:
    """
    Telegram Bot API Service.
    Handles messaging, webhook registration, and background polling runner for Docker.
    """

    def __init__(self):
        self.api_url = "https://api.telegram.org"

    @property
    def token(self) -> str:
        return settings.TELEGRAM_BOT_TOKEN

    @property
    def is_configured(self) -> bool:
        return bool(self.token and len(self.token) > 10)

    def send_message(self, chat_id: int | str, text: str, parse_mode: str = "Markdown") -> bool:
        """Sends a message to a Telegram chat using Bot API."""
        if not self.is_configured:
            return False

        url = f"{self.api_url}/bot{self.token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("ok", False)
        except Exception:
            # If Markdown parsing fails due to special characters, retry in plain text
            try:
                payload.pop("parse_mode", None)
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    return result.get("ok", False)
            except Exception as retry_err:
                print(f"[TelegramService] Error sending message to {chat_id}: {retry_err}")
                return False

    def get_me(self) -> Optional[Dict[str, Any]]:
        """Verifies bot token validity and returns bot information."""
        if not self.is_configured:
            return None

        url = f"{self.api_url}/bot{self.token}/getMe"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("result") if result.get("ok") else None
        except Exception as e:
            print(f"[TelegramService] getMe failed: {e}")
            return None

    def delete_webhook(self) -> bool:
        """Deletes active webhooks to enable long-polling mode."""
        if not self.is_configured:
            return False
        url = f"{self.api_url}/bot{self.token}/deleteWebhook"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("ok", False)
        except Exception:
            return False

    def set_webhook(self, webhook_url: str) -> bool:
        """Registers the webhook URL with Telegram."""
        if not self.is_configured:
            return False

        url = f"{self.api_url}/bot{self.token}/setWebhook"
        payload = {"url": webhook_url}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("ok", False)
        except Exception as e:
            print(f"[TelegramService] setWebhook failed: {e}")
            return False

    async def run_polling(self, stop_event: asyncio.Event):
        """
        Asynchronous polling loop designed to run as a FastAPI background task inside Docker.
        """
        from app.services.hybrid_router import process_inquiry
        from app.services.cache_service import cache_service

        if not self.is_configured:
            print("[TelegramBot] TELEGRAM_BOT_TOKEN not configured in .env. Telegram polling is idle.")
            return

        bot_info = await asyncio.to_thread(self.get_me)
        if not bot_info:
            print("[TelegramBot] Warning: Could not authenticate bot token with Telegram. Check TELEGRAM_BOT_TOKEN.")
            return

        username = bot_info.get("username", "bot")
        print(f"[TelegramBot] 🤖 Telegram Bot connected successfully: @{username}")
        await asyncio.to_thread(self.delete_webhook)
        print("[TelegramBot] ⚡ Polling loop active inside Docker.")

        offset = 0
        while not stop_event.is_set():
            try:
                updates = await asyncio.to_thread(self._fetch_updates, offset, 5)
                for update in updates:
                    update_id = update.get("update_id", 0)
                    offset = update_id + 1

                    message = update.get("message")
                    if not message:
                        continue

                    chat_id = message.get("chat", {}).get("id")
                    user_name = message.get("from", {}).get("first_name", "User")
                    user_text = message.get("text", "").strip()

                    if not user_text:
                        continue

                    print(f"[TelegramBot] 📩 [{user_name} ({chat_id})]: {user_text}")

                    if user_text.lower() == "/start":
                        welcome = (
                            f"¡Hola {user_name}! 👋 Bienvenido al Asistente Virtual de **Global Language Academy**.\n\n"
                            "Estoy disponible 24/7 para brindarte información oficial sobre:\n"
                            "- 💰 **Precios y Financiación** (PSE, tarjetas de crédito sin interés)\n"
                            "- ⏰ **Horarios y Modalidades** (Mañanas, noches, sábados intensivos, virtual o presencial)\n"
                            "- 📍 **Sedes** en Bogotá (Chapinero) y Medellín (El Poblado)\n"
                            "- 🎯 **Prueba de Nivelación Gratuita** online\n"
                            "- 📜 **Certificaciones** (IELTS, TOEFL, Cambridge, DELF, DELE)\n\n"
                            "Escribe cualquier pregunta y con gusto te respondo."
                        )
                        await asyncio.to_thread(self.send_message, chat_id, welcome)
                        continue

                    if user_text.lower() == "/help":
                        help_text = (
                            "**Comandos disponibles:**\n"
                            "- `/start` - Iniciar el asistente\n"
                            "- `/prices` - Ver tabla de precios y descuentos\n"
                            "- `/schedules` - Ver horarios de clases y sedes\n"
                            "- `/placement` - Información de la prueba de nivel gratuita\n"
                            "- `/clear` - Limpiar caché de respuestas\n\n"
                            "O simplemente escribe tu duda como si hablaras con un asesor."
                        )
                        await asyncio.to_thread(self.send_message, chat_id, help_text)
                        continue

                    if user_text.lower() == "/clear":
                        cache_service.clear()
                        await asyncio.to_thread(self.send_message, chat_id, "🧹 Caché de respuestas reiniciada.")
                        continue

                    # Process inquiry through hybrid pipeline
                    res = await asyncio.to_thread(process_inquiry, user_text, "telegram")
                    answer = res.get("answer", "")
                    sources = res.get("sources", [])
                    is_escalated = res.get("escalate_to_human", False)
                    ticket_id = res.get("ticket_id")

                    reply = answer
                    if is_escalated and ticket_id:
                        reply += f"\n\n🎫 *Ticket de Soporte*: `{ticket_id}`\n_Un asesor humano se comunicará contigo._"
                    elif sources and len(sources) > 0:
                        source_clean = ", ".join([s.split('#')[0] for s in sources[:2]])
                        reply += f"\n\n📚 _Fuente verificada: {source_clean}_"

                    await asyncio.to_thread(self.send_message, chat_id, reply)

            except Exception as e:
                print(f"[TelegramBot] Polling loop exception: {e}")
                await asyncio.sleep(2)

            await asyncio.sleep(0.5)

        print("[TelegramBot] Polling loop stopped cleanly.")

    def _fetch_updates(self, offset: int, timeout: int):
        url = f"{self.api_url}/bot{self.token}/getUpdates?offset={offset}&timeout={timeout}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("result", []) if data.get("ok") else []
        except Exception:
            return []

telegram_service = TelegramService()
