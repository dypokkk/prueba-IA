from typing import Dict, Any
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException

from app.config import settings
from app.services.telegram_service import telegram_service
from app.services.hybrid_router import process_inquiry

router = APIRouter(prefix="/api/telegram", tags=["Telegram Bot Integration"])

def handle_telegram_message(chat_id: int | str, user_text: str):
    """Processes incoming Telegram text and dispatches reply."""
    if user_text.strip() == "/start":
        welcome_text = (
            "¡Hola! 👋 Bienvenido al Asistente Virtual de **Global Language Academy**.\n\n"
            "Puedo ayudarte con información sobre:\n"
            "- 💰 Precios y modalidades de pago (PSE, tarjetas de crédito)\n"
            "- ⏰ Horarios de clases (Mañana, noche, sábados intensivos)\n"
            "- 📍 Sedes en Bogotá (Chapinero) y Medellín (El Poblado)\n"
            "- 🎯 Prueba de nivelación gratuita online\n"
            "- 📜 Preparación para IELTS, TOEFL, Cambridge, DELF, DELE\n\n"
            "¿En qué programa o idioma estás interesado hoy?"
        )
        telegram_service.send_message(chat_id, welcome_text)
        return

    # Process inquiry through hybrid pipeline
    result = process_inquiry(message=user_text, channel="telegram")

    answer = result.get("answer", "")
    is_escalated = result.get("escalate_to_human", False)
    ticket_id = result.get("ticket_id")

    reply_text = answer
    if is_escalated and ticket_id:
        reply_text += f"\n\n🎫 **Ticket de Soporte**: `{ticket_id}`\n*Un asesor humano se comunicará contigo pronto.*"

    telegram_service.send_message(chat_id, reply_text)


@router.post("/webhook")
async def telegram_webhook_endpoint(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming Telegram updates via Webhook.
    """
    try:
        update: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True, "status": "ignored_non_message_update"}

    chat_id = message.get("chat", {}).get("id")
    user_text = message.get("text", "").strip()

    if chat_id and user_text:
        background_tasks.add_task(handle_telegram_message, chat_id, user_text)

    return {"ok": True}


@router.get("/status")
async def telegram_bot_status():
    """Returns Telegram Bot connection status and info."""
    bot_info = telegram_service.get_me() if telegram_service.is_configured else None
    return {
        "is_configured": telegram_service.is_configured,
        "bot_info": bot_info,
        "webhook_url": settings.TELEGRAM_WEBHOOK_URL or "Not registered (using polling runner)"
    }
