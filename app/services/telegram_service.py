import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

from app.config import settings

class TelegramService:
    """
    Telegram Bot API Service.
    Handles messaging, webhook registration, and response dispatching for Telegram users.
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
            print("[TelegramService] Cannot send message: TELEGRAM_BOT_TOKEN is not configured.")
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
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("ok", False)
        except Exception as e:
            # If Markdown parsing fails due to special chars, retry with plain text
            try:
                payload.pop("parse_mode", None)
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    return result.get("ok", False)
            except Exception as retry_err:
                print(f"[TelegramService] Error sending telegram message to {chat_id}: {retry_err}")
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

telegram_service = TelegramService()
