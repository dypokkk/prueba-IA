import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.config import settings
from app.services.database import db

class EscalationService:
    """
    Tier 3 Human Escalation Dispatcher & Ticket Desk Manager.
    Persists tickets to SQLite with dual-save to JSON for resilience.
    """

    def __init__(self):
        self.tickets_file = settings.TICKETS_STORE_PATH
        self.tickets: List[Dict[str, Any]] = []
        self._load_tickets()

    def _load_tickets(self):
        # 1. Load from SQLite first
        try:
            db_tickets = db.get_tickets()
            if db_tickets:
                self.tickets = db_tickets
                self._save_json()
                return
        except Exception as e:
            print(f"[EscalationService] DB load error: {e}")

        # 2. Fallback to JSON
        if self.tickets_file.exists():
            try:
                with open(self.tickets_file, "r", encoding="utf-8") as f:
                    self.tickets = json.load(f)
            except Exception as e:
                print(f"[EscalationService] Error loading tickets JSON: {e}")
                self.tickets = []

    def _save_json(self):
        self.tickets_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.tickets_file, "w", encoding="utf-8") as f:
                json.dump(self.tickets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[EscalationService] Error saving tickets JSON: {e}")

    def create_ticket(
        self,
        user_query: str,
        escalation_reason: str,
        channel: str = "web",
        confidence: float = 0.0,
        session_id: Optional[str] = None,
        student_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        target_language: Optional[str] = None,
        modality: Optional[str] = None,
        dossier: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Creates and persists an escalation ticket for a human advisor."""
        ticket = {
            "ticket_id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "user_query": user_query,
            "escalation_reason": escalation_reason or "UNSPECIFIED_ESCALATION",
            "confidence": round(confidence, 2),
            "channel": channel,
            "session_id": session_id or f"web_session_{uuid.uuid4().hex[:8]}",
            "student_name": student_name,
            "email": email,
            "phone": phone,
            "target_language": target_language,
            "modality": modality,
            "status": "PENDING",
            "resolution_notes": None,
            "resolved_at": None,
            "dossier": dossier or {}
        }

        # 1. Save to SQLite
        try:
            db.save_ticket(ticket)
        except Exception as e:
            print(f"[EscalationService] DB save_ticket error: {e}")

        # 2. Keep in memory and sync JSON
        self.tickets.insert(0, ticket)
        self._save_json()

        # 3. Webhook notification
        if settings.ESCALATION_WEBHOOK_URL:
            self._dispatch_webhook(ticket)

        return ticket

    def get_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns tickets prioritizing PENDING tickets at the top, followed by RESOLVED history at the bottom."""
        try:
            db_tickets = db.get_tickets(status)
            if db_tickets:
                self.tickets = db_tickets
                return db_tickets
        except Exception:
            pass

        if status:
            return [t for t in self.tickets if t.get("status") == status]
        return sorted(self.tickets, key=lambda t: (0 if t.get("status") == "PENDING" else 1))

    def resolve_ticket(self, ticket_id: str, notes: str = "") -> bool:
        """Marks a ticket as RESOLVED."""
        resolved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # 1. Update SQLite
        try:
            db.resolve_ticket(ticket_id, notes=notes, resolved_at=resolved_at)
        except Exception as e:
            print(f"[EscalationService] DB resolve_ticket error: {e}")

        # 2. Update memory & JSON
        for t in self.tickets:
            if t["ticket_id"] == ticket_id:
                t["status"] = "RESOLVED"
                t["resolution_notes"] = notes
                t["resolved_at"] = resolved_at
                self._save_json()
                return True
        return False

    def mark_in_progress(self, ticket_id: str, advisor: str = "Asesor") -> bool:
        """Marks a ticket as IN_PROGRESS with advisor attribution."""
        notes = f"Siendo atendido por {advisor}"
        # 1. Update SQLite
        try:
            db.update_ticket_status(ticket_id, "IN_PROGRESS", notes=notes)
        except Exception as e:
            print(f"[EscalationService] DB mark_in_progress error: {e}")

        # 2. Update memory & JSON
        for t in self.tickets:
            if t["ticket_id"] == ticket_id:
                t["status"] = "IN_PROGRESS"
                t["resolution_notes"] = notes
                self._save_json()
                return True
        return False

    def _dispatch_webhook(self, ticket: Dict[str, Any]):
        """Dispatches notification to external webhook."""
        try:
            import urllib.request
            payload = json.dumps({
                "text": f"🚨 *Nuevo Ticket de Soporte*\n\n"
                        f"*Ticket ID*: `{ticket['ticket_id']}`\n"
                        f"*Estudiante*: {ticket.get('student_name') or 'N/A'}\n"
                        f"*Email*: {ticket.get('email') or 'N/A'}\n"
                        f"*Teléfono*: {ticket.get('phone') or 'N/A'}\n"
                        f"*Motivo*: {ticket['escalation_reason']}\n"
                        f"*Consulta*: \"{ticket['user_query']}\""
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
