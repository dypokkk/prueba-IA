import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.config import settings

class EscalationService:
    """
    Tier 3 Human Escalation Dispatcher & Ticket Desk Manager.
    Logs unanswerable or sensitive queries and routes them to human advisors.
    """

    def __init__(self):
        self.tickets_file = settings.TICKETS_STORE_PATH
        self.tickets: List[Dict[str, Any]] = []
        self._load_tickets()

    def _load_tickets(self):
        if self.tickets_file.exists():
            try:
                with open(self.tickets_file, "r", encoding="utf-8") as f:
                    self.tickets = json.load(f)
            except Exception as e:
                print(f"[EscalationService] Error loading tickets: {e}")
                self.tickets = []

    def _save_tickets(self):
        self.tickets_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.tickets_file, "w", encoding="utf-8") as f:
                json.dump(self.tickets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[EscalationService] Error saving tickets: {e}")

    def create_ticket(
        self,
        user_query: str,
        escalation_reason: str,
        channel: str = "web",
        confidence: float = 0.0
    ) -> Dict[str, Any]:
        """Creates and persists an escalation ticket for a human advisor."""
        ticket = {
            "ticket_id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "user_query": user_query,
            "escalation_reason": escalation_reason or "UNSPECIFIED_ESCALATION",
            "confidence": round(confidence, 2),
            "channel": channel,
            "status": "PENDING",
            "resolution_notes": None
        }

        self.tickets.insert(0, ticket)
        self._save_tickets()

        # Fire and forget webhook alert if configured
        if settings.ESCALATION_WEBHOOK_URL:
            self._dispatch_webhook(ticket)

        return ticket

    def get_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns tickets prioritizing PENDING tickets at the top, followed by RESOLVED history at the bottom."""
        if status:
            return [t for t in self.tickets if t.get("status") == status]
        return sorted(self.tickets, key=lambda t: (0 if t.get("status") == "PENDING" else 1))

    def resolve_ticket(self, ticket_id: str, notes: str = "") -> bool:
        """Marks a ticket as RESOLVED."""
        for t in self.tickets:
            if t["ticket_id"] == ticket_id:
                t["status"] = "RESOLVED"
                t["resolution_notes"] = notes
                t["resolved_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                self._save_tickets()
                return True
        return False

    def _dispatch_webhook(self, ticket: Dict[str, Any]):
        """Dispatches notification to external webhook (Slack, Telegram, or custom)."""
        try:
            import urllib.request
            payload = json.dumps({
                "text": f"🚨 *New Support Ticket Escalated*\n\n"
                        f"*Ticket ID*: `{ticket['ticket_id']}`\n"
                        f"*Reason*: {ticket['escalation_reason']}\n"
                        f"*Channel*: {ticket['channel']}\n"
                        f"*Query*: \"{ticket['user_query']}\"\n"
                        f"*Time*: {ticket['timestamp']}"
            }).encode("utf-8")

            req = urllib.request.Request(
                settings.ESCALATION_WEBHOOK_URL,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=3.0)
        except Exception as e:
            print(f"[EscalationService] Webhook alert failed: {e}")

escalation_service = EscalationService()
