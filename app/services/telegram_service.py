import json
import asyncio
import re
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

from app.config import settings

def markdown_to_telegram_html(text: str) -> str:
    """
    Converts standard markdown into clean, beautiful Telegram HTML format.
    Telegram HTML supports: <b>, <i>, <u>, <s>, <code>, <pre>, <a>.
    """
    if not text:
        return ""

    # Remove any internal citations or file references
    s = re.sub(r'\[\s*\d+[a-zA-Z0-9_\-\.]*\.md\s*\](?:\([^)]*\))?', '', text)
    s = re.sub(r'Fuente verificada:.*$', '', s, flags=re.MULTILINE | re.IGNORECASE)
    s = re.sub(r'Verified Sources?:.*$', '', s, flags=re.MULTILINE | re.IGNORECASE)

    # Escape HTML special chars first
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Headers: ### Header -> \n<b>Header</b>\n
    s = re.sub(r'^\s*#{1,6}\s*(.*)$', r'\n<b>\1</b>\n', s, flags=re.MULTILINE)

    # Bold: **text** or __text__ -> <b>text</b>
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'__(.+?)__', r'<b>\1</b>', s)

    # Italic: *text* or _text_ -> <i>text</i>
    s = re.sub(r'(?<!\w)\*([^\*\n]+)\*(?!\w)', r'<i>\1</i>', s)
    s = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'<i>\1</i>', s)

    # Code blocks: ```code``` -> <pre>code</pre>
    s = re.sub(r'```(?:[a-zA-Z0-9]+)?\n?(.*?)```', r'<pre>\1</pre>', s, flags=re.DOTALL)

    # Inline code: `code` -> <code>code</code>
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)

    # Bullet lists: - item or * item -> • item
    s = re.sub(r'^\s*[-*]\s+', '• ', s, flags=re.MULTILINE)

    # Collapse excessive newlines
    s = re.sub(r'\n{3,}', '\n\n', s)

    return s.strip()

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

    def send_message(self, chat_id: int | str, text: str) -> bool:
        """
        Sends a message to a Telegram chat using Bot API with HTML formatting
        and automatic fallback to plain text.
        """
        if not self.is_configured:
            print(f"[TelegramService] Cannot send message: bot not configured.", flush=True)
            return False

        url = f"{self.api_url}/bot{self.token}/sendMessage"
        html_text = markdown_to_telegram_html(text)

        payload = {
            "chat_id": chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }

        # 1. Try sending with HTML formatting
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("ok"):
                    print(f"[TelegramService] Message sent successfully (HTML) to chat_id={chat_id}", flush=True)
                    return True
        except Exception as html_err:
            print(f"[TelegramService] HTML send failed: {html_err}. Retrying with plain text...", flush=True)

        # 2. Fallback to clean plain text (100% fail-safe)
        try:
            plain_text = re.sub(r'<[^>]+>', '', html_text)
            plain_text = plain_text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            fallback_payload = {
                "chat_id": chat_id,
                "text": plain_text,
                "disable_web_page_preview": True
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(fallback_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("ok"):
                    print(f"[TelegramService] Message sent successfully (Plain Text) to chat_id={chat_id}", flush=True)
                    return True
        except Exception as plain_err:
            print(f"[TelegramService] Error sending telegram message to {chat_id}: {plain_err}", flush=True)
            return False

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
            print(f"[TelegramService] getMe failed: {e}", flush=True)
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
            print(f"[TelegramService] setWebhook failed: {e}", flush=True)
            return False

    async def run_polling(self, stop_event: asyncio.Event):
        """
        Asynchronous polling loop designed to run as a FastAPI background task inside Docker.
        """
        from app.services.hybrid_router import process_inquiry
        from app.services.cache_service import cache_service

        if not self.is_configured:
            print("[TelegramBot] TELEGRAM_BOT_TOKEN not configured in .env. Telegram polling is idle.", flush=True)
            return

        bot_info = await asyncio.to_thread(self.get_me)
        if not bot_info:
            print("[TelegramBot] Warning: Could not authenticate bot token with Telegram. Check TELEGRAM_BOT_TOKEN.", flush=True)
            return

        username = bot_info.get("username", "bot")
        print(f"[TelegramBot] 🤖 Telegram Bot connected successfully: @{username}", flush=True)
        await asyncio.to_thread(self.delete_webhook)
        print("[TelegramBot] ⚡ Polling loop active inside Docker.", flush=True)

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

                    print(f"[TelegramBot] 📩 Received from {user_name} ({chat_id}): '{user_text}'", flush=True)

                    if user_text.lower() == "/start":
                        welcome = (
                            f"¡Hola {user_name}! 👋 Bienvenido al Asistente Virtual de **Global Language Academy**.\n\n"
                            "Estoy disponible 24/7 para brindarte información oficial sobre:\n"
                            "- 💰 **Precios y Financiación** (PSE, tarjetas de crédito sin interés)\n"
                            "- ⏰ **Horarios y Modalidades** (Mañanas, noches, sábados intensivos, virtual o presencial)\n"
                            "- 📍 **Sedes** en Bogotá (Chapinero) y Medellín (El Poblado)\n"
                            "- 🎯 **Prueba de Nivelación Gratuita** online\n"
                            "- 📜 **Certificaciones** (IELTS, TOEFL, Cambridge, DELF, DELE)\n\n"
                            "¿En qué idioma o programa estás interesado hoy?"
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
                    print(f"[TelegramBot] 🧠 Processing query for {chat_id} via Hybrid Router...", flush=True)
                    res = await asyncio.to_thread(process_inquiry, user_text, "telegram")
                    answer = res.get("answer", "")
                    is_escalated = res.get("escalate_to_human", False)
                    ticket_id = res.get("ticket_id")

                    reply = answer
                    if is_escalated and ticket_id:
                        reply += f"\n\n🎫 **Ticket de Soporte**: `{ticket_id}`\n*Un asesor humano se comunicará contigo pronto.*"

                    print(f"[TelegramBot] 📤 Dispatching response to chat_id={chat_id} (Tier: {res.get('tier')})...", flush=True)
                    sent = await asyncio.to_thread(self.send_message, chat_id, reply)
                    print(f"[TelegramBot] Response dispatched: success={sent}", flush=True)

            except Exception as e:
                print(f"[TelegramBot] Polling loop exception: {e}", flush=True)
                await asyncio.sleep(2)

            await asyncio.sleep(0.5)

        print("[TelegramBot] Polling loop stopped cleanly.", flush=True)

    def _fetch_updates(self, offset: int, timeout: int):
        url = f"{self.api_url}/bot{self.token}/getUpdates?offset={offset}&timeout={timeout}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("result", []) if data.get("ok") else []
        except Exception as e:
            print(f"[TelegramBot] _fetch_updates error: {e}", flush=True)
            return []

telegram_service = TelegramService()
