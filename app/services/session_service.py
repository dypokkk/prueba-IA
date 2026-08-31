import time
import threading
from typing import Dict, List, Any, Optional
from app.services.database import db

class SessionService:
    """
    Hybrid In-Memory + SQLite Persistent Multi-Turn Conversational Memory Manager.
    Maintains sliding context windows in memory for ultra-fast lookup,
    and automatically commits every dialogue turn to SQLite for permanent historical preservation.
    """

    def __init__(self, max_turns_per_session: int = 10, session_ttl_seconds: int = 86400):
        self._lock = threading.Lock()
        self.max_turns = max_turns_per_session
        self.ttl_seconds = session_ttl_seconds
        # In-memory buffer: session_id -> {"last_active": float, "messages": [{"role": "user"|"assistant", "content": str, "tier": str}]}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def add_user_message(self, session_id: str, content: str, ticket_id: Optional[str] = None):
        if not session_id:
            return
        with self._lock:
            self._ensure_session(session_id)
            msg_obj = {
                "role": "user",
                "content": content.strip(),
                "tier": "user"
            }
            self._sessions[session_id]["messages"].append(msg_obj)
            self._trim_session(session_id)
            self._sessions[session_id]["last_active"] = time.time()

        # Persist to SQLite
        try:
            db.save_message(
                session_id=session_id,
                role="user",
                content=content,
                tier="user",
                ticket_id=ticket_id
            )
        except Exception as e:
            print(f"[SessionService] DB save_message error: {e}")

    def add_assistant_message(
        self,
        session_id: str,
        content: str,
        tier: Optional[str] = "assistant",
        confidence: Optional[float] = None,
        ticket_id: Optional[str] = None
    ):
        if not session_id:
            return
        with self._lock:
            self._ensure_session(session_id)
            msg_obj = {
                "role": "assistant",
                "content": content.strip(),
                "tier": tier or "assistant"
            }
            self._sessions[session_id]["messages"].append(msg_obj)
            self._trim_session(session_id)
            self._sessions[session_id]["last_active"] = time.time()

        # Persist to SQLite
        try:
            db.save_message(
                session_id=session_id,
                role="assistant",
                content=content,
                tier=tier,
                confidence=confidence,
                ticket_id=ticket_id
            )
        except Exception as e:
            print(f"[SessionService] DB save_message error: {e}")

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        if not session_id:
            return []
        with self._lock:
            if session_id in self._sessions and self._sessions[session_id]["messages"]:
                return list(self._sessions[session_id]["messages"])

        # Fallback: Load from SQLite
        try:
            db_messages = db.get_session_messages(session_id, limit=50)
            if db_messages:
                loaded = [{"role": m["role"], "content": m["content"], "tier": m.get("tier", "assistant")} for m in db_messages]
                with self._lock:
                    self._sessions[session_id] = {
                        "last_active": time.time(),
                        "messages": loaded
                    }
                return loaded
        except Exception as e:
            print(f"[SessionService] DB get_session_messages error: {e}")

        return []

    def get_combined_query_context(self, session_id: str, current_query: str) -> str:
        """
        Synthesizes recent user queries with current query for enhanced BM25/Vector retrieval.
        """
        if not session_id:
            return current_query

        history = self.get_history(session_id)
        if not history:
            return current_query

        user_queries = [m["content"] for m in history if m["role"] == "user"][-2:]
        if not user_queries:
            return current_query

        clean_curr = current_query.strip().lower()
        is_implicit = len(clean_curr.split()) <= 4 or clean_curr.startswith(("y ", "¿y ", "como ", "¿como ", "donde ", "¿donde ", "cuanto ", "¿cuanto ", "en ", "¿en "))
        
        if is_implicit:
            return f"{' '.join(user_queries)} {current_query}"
        return current_query

    def clear(self, session_id: str):
        if not session_id:
            return
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
        try:
            db.clear_session_messages(session_id)
        except Exception as e:
            print(f"[SessionService] DB clear error: {e}")

    def _ensure_session(self, session_id: str):
        if session_id not in self._sessions:
            # Check SQLite first to warm up cache
            try:
                db_messages = db.get_session_messages(session_id, limit=50)
                if db_messages:
                    self._sessions[session_id] = {
                        "last_active": time.time(),
                        "messages": [{"role": m["role"], "content": m["content"], "tier": m.get("tier", "assistant")} for m in db_messages]
                    }
                    return
            except Exception:
                pass

            self._sessions[session_id] = {
                "last_active": time.time(),
                "messages": []
            }

    def _trim_session(self, session_id: str):
        max_messages = self.max_turns * 2
        if len(self._sessions[session_id]["messages"]) > max_messages:
            self._sessions[session_id]["messages"] = self._sessions[session_id]["messages"][-max_messages:]

session_service = SessionService()
