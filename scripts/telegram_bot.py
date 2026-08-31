#!/usr/bin/env python3
"""
Standalone Telegram Bot Long-Polling Runner for Global Language Academy.
Runs locally or in a container without requiring a public HTTPS webhook or ngrok tunnel.
"""
import sys
import time
import json
import signal
import urllib.request
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.config import settings
from app.services.telegram_service import telegram_service
from app.services.hybrid_router import process_inquiry
from app.services.cache_service import cache_service

running = True

def signal_handler(sig, frame):
    global running
    print("\n[Telegram Bot] Stopping polling loop...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_updates(offset: int = 0, timeout: int = 20):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout={timeout}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return data.get("result", [])
    except Exception as e:
        print(f"[Telegram Bot] Polling error: {e}")
    return []

def delete_webhook():
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/deleteWebhook"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ok", False)
    except Exception:
        return False

def format_telegram_reply(res: dict) -> str:
    answer = res.get("answer", "")
    sources = res.get("sources", [])
    is_escalated = res.get("escalate_to_human", False)
    ticket_id = res.get("ticket_id")

    reply = answer
    if is_escalated and ticket_id:
        reply += f"\n\n🎫 *Ticket de Soporte*: `{ticket_id}`\n_Un asesor de admisiones se comunicará contigo._"
    elif sources and len(sources) > 0:
        source_clean = ", ".join([s.split('#')[0] for s in sources[:2]])
        reply += f"\n\n📚 _Fuente verificada: {source_clean}_"

    return reply

def main():
    print("=" * 60)
    print("🤖 GLOBAL LANGUAGE ACADEMY - TELEGRAM BOT RUNNER")
    print("=" * 60)

    if not telegram_service.is_configured:
        print("\n❌ Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        print("To configure:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions to get your API Token")
        print("3. Add TELEGRAM_BOT_TOKEN=your_token_here to your .env file")
        print("4. Re-run this script: python3 scripts/telegram_bot.py\n")
        sys.exit(1)

    bot_info = telegram_service.get_me()
    if not bot_info:
        print("\n❌ Error: Failed to connect to Telegram Bot API. Please check your TELEGRAM_BOT_TOKEN.\n")
        sys.exit(1)

    bot_name = bot_info.get("first_name", "Assistant")
    bot_username = bot_info.get("username", "bot")
    print(f"✅ Connected to Telegram as: @{bot_username} ({bot_name})")
    print("Clearing any active webhooks for polling mode...")
    delete_webhook()
    print("⚡ Polling for messages in real-time. Press Ctrl+C to stop.\n")

    offset = 0
    while running:
        updates = get_updates(offset=offset, timeout=10)
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

            print(f"📩 [{user_name} ({chat_id})]: {user_text}")

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
                telegram_service.send_message(chat_id, welcome)
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
                telegram_service.send_message(chat_id, help_text)
                continue

            if user_text.lower() == "/clear":
                cache_service.clear()
                telegram_service.send_message(chat_id, "🧹 Caché de respuestas reiniciada correctamente.")
                continue

            # Process through hybrid router
            start_time = time.time()
            res = process_inquiry(message=user_text, channel="telegram")
            latency_ms = (time.time() - start_time) * 1000

            reply = format_telegram_reply(res)
            telegram_service.send_message(chat_id, reply)
            print(f"📤 Sent reply in {latency_ms:.1f}ms (Tier: {res.get('tier')})")

        time.sleep(0.5)

    print("\n👋 Telegram Bot stopped gracefully.")

if __name__ == "__main__":
    main()
