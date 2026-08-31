import sqlite3
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.config import settings

DB_PATH = settings.DATA_DIR / "conversations.db"

class DatabaseManager:
    """
    SQLite Persistence Engine for Global Language Academy.
    Maintains ACID-compliant tables for sessions, messages, and escalation tickets.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable Write-Ahead Logging (WAL) for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            # 1. Sessions Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at REAL,
                    last_active REAL,
                    student_name TEXT,
                    email TEXT,
                    phone TEXT,
                    target_language TEXT,
                    modality TEXT,
                    intake_state TEXT DEFAULT 'IDLE',
                    active_ticket_id TEXT,
                    intake_data TEXT
                )
            """)
            try:
                conn.execute("ALTER TABLE sessions ADD COLUMN active_ticket_id TEXT;")
            except Exception:
                pass

            # 2. Messages Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tier TEXT,
                    confidence REAL,
                    ticket_id TEXT,
                    timestamp REAL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);")

            # 3. Tickets Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    student_name TEXT,
                    email TEXT,
                    phone TEXT,
                    target_language TEXT,
                    modality TEXT,
                    user_query TEXT NOT NULL,
                    escalation_reason TEXT,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    resolution_notes TEXT,
                    resolved_at TEXT,
                    dossier TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);")

    # ==================== SESSIONS ====================
    def ensure_session(self, session_id: str) -> Dict[str, Any]:
        now = time.time()
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not row:
                conn.execute(
                    "INSERT INTO sessions (session_id, created_at, last_active, intake_state, intake_data) VALUES (?, ?, ?, 'IDLE', '{}')",
                    (session_id, now, now)
                )
                return {
                    "session_id": session_id,
                    "created_at": now,
                    "last_active": now,
                    "student_name": None,
                    "email": None,
                    "phone": None,
                    "target_language": None,
                    "modality": None,
                    "intake_state": "IDLE",
                    "intake_data": {}
                }
            return self._row_to_dict(row)

    def update_session(self, session_id: str, **kwargs):
        self.ensure_session(session_id)
        now = time.time()
        fields = ["last_active = ?"]
        values = [now]

        for k, v in kwargs.items():
            if k == "intake_data" and isinstance(v, dict):
                v = json.dumps(v)
            fields.append(f"{k} = ?")
            values.append(v)

        values.append(session_id)
        with self._get_connection() as conn:
            conn.execute(f"UPDATE sessions SET {', '.join(fields)} WHERE session_id = ?", values)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                d = self._row_to_dict(row)
                if d.get("intake_data") and isinstance(d["intake_data"], str):
                    try:
                        d["intake_data"] = json.loads(d["intake_data"])
                    except Exception:
                        d["intake_data"] = {}
                return d
            return None

    # ==================== MESSAGES ====================
    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tier: Optional[str] = None,
        confidence: Optional[float] = None,
        ticket_id: Optional[str] = None
    ) -> int:
        self.ensure_session(session_id)
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, tier, confidence, ticket_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, role, content.strip(), tier, confidence, ticket_id, now)
            )
            # Update session last active
            conn.execute("UPDATE sessions SET last_active = ? WHERE session_id = ?", (now, session_id))
            return cur.lastrowid

    def get_session_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def clear_session_messages(self, session_id: str):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("UPDATE sessions SET intake_state = 'IDLE', active_ticket_id = NULL, intake_data = '{}' WHERE session_id = ?", (session_id,))

    def get_active_ticket_for_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE session_id = ? AND status = 'PENDING' ORDER BY timestamp DESC LIMIT 1",
                (session_id,)
            ).fetchone()
            if row:
                t = self._row_to_dict(row)
                if t.get("dossier") and isinstance(t["dossier"], str):
                    try:
                        t["dossier"] = json.loads(t["dossier"])
                    except Exception:
                        t["dossier"] = {}
                return t
            return None

    # ==================== TICKETS ====================
    def save_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._get_connection() as conn:
            dossier_str = json.dumps(ticket_data.get("dossier", {})) if isinstance(ticket_data.get("dossier"), dict) else "{}"
            conn.execute(
                """
                INSERT OR REPLACE INTO tickets (
                    ticket_id, session_id, timestamp, student_name, email, phone,
                    target_language, modality, user_query, escalation_reason, status,
                    resolution_notes, resolved_at, dossier
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_data.get("ticket_id"),
                    ticket_data.get("session_id"),
                    ticket_data.get("timestamp"),
                    ticket_data.get("student_name"),
                    ticket_data.get("email"),
                    ticket_data.get("phone"),
                    ticket_data.get("target_language"),
                    ticket_data.get("modality"),
                    ticket_data.get("user_query"),
                    ticket_data.get("escalation_reason"),
                    ticket_data.get("status", "PENDING"),
                    ticket_data.get("resolution_notes"),
                    ticket_data.get("resolved_at"),
                    dossier_str
                )
            )
        return ticket_data

    def get_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM tickets WHERE status = ? ORDER BY timestamp DESC",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tickets ORDER BY CASE WHEN status = 'PENDING' THEN 0 ELSE 1 END, timestamp DESC"
                ).fetchall()
            
            results = []
            for r in rows:
                t = self._row_to_dict(r)
                if t.get("dossier") and isinstance(t["dossier"], str):
                    try:
                        t["dossier"] = json.loads(t["dossier"])
                    except Exception:
                        t["dossier"] = {}
                results.append(t)
            return results

    def resolve_ticket(self, ticket_id: str, notes: str = "", resolved_at: str = "") -> bool:
        with self._get_connection() as conn:
            cur = conn.execute(
                "UPDATE tickets SET status = 'RESOLVED', resolution_notes = ?, resolved_at = ? WHERE ticket_id = ?",
                (notes, resolved_at, ticket_id)
            )
            return cur.rowcount > 0

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {key: row[key] for key in row.keys()}

db = DatabaseManager()
