import time
import threading
from typing import Dict, List, Any, Optional

class SessionService:
    """
    In-Memory Thread-Safe Multi-Turn Conversational Memory Manager.
    Maintains sliding context windows per session (Web, WebSocket, Telegram)
    to seamlessly resolve follow-up questions, anaphoric references, and continuous dialogues.
    """

    def __init__(self, max_turns_per_session: int = 6, session_ttl_seconds: int = 3600):
        self._lock = threading.Lock()
        self.max_turns = max_turns_per_session  # 6 turns = 12 messages (user + assistant)
        self.ttl_seconds = session_ttl_seconds
        # Structure: session_id -> {"last_active": float, "messages": [{"role": "user"|"assistant", "content": str}]}
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def add_user_message(self, session_id: str, content: str):
        if not session_id:
            return
        with self._lock:
            self._ensure_session(session_id)
            self._sessions[session_id]["messages"].append({
                "role": "user",
                "content": content.strip()
            })
            self._trim_session(session_id)
            self._sessions[session_id]["last_active"] = time.time()

    def add_assistant_message(self, session_id: str, content: str):
        if not session_id:
            return
        with self._lock:
            self._ensure_session(session_id)
            self._sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": content.strip()
            })
            self._trim_session(session_id)
            self._sessions[session_id]["last_active"] = time.time()

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        if not session_id:
            return []
        with self._lock:
            if session_id not in self._sessions:
                return []
            return list(self._sessions[session_id]["messages"])

    def get_combined_query_context(self, session_id: str, current_query: str) -> str:
        """
        Synthesizes recent user queries with the current query for enhanced BM25 retrieval
        when queries are short or implicit (e.g. '¿y los horarios?', '¿cuánto cuesta?').
        """
        if not session_id:
            return current_query

        history = self.get_history(session_id)
        if not history:
            return current_query

        # Extract last 2 user messages
        user_queries = [m["content"] for m in history if m["role"] == "user"][-2:]
        if not user_queries:
            return current_query

        # If current query is short / implicit, append previous topics
        clean_curr = current_query.strip().lower()
        is_implicit = len(clean_curr.split()) <= 4 or clean_curr.startswith(("y ", "¿y ", "como ", "¿como ", "donde ", "¿donde ", "cuanto ", "¿cuanto "))
        
        if is_implicit:
            combined = f"{' '.join(user_queries)} {current_query}"
            return combined
        return current_query

    def clear(self, session_id: str):
        if not session_id:
            return
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def _ensure_session(self, session_id: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "last_active": time.time(),
                "messages": []
            }

    def _trim_session(self, session_id: str):
        max_messages = self.max_turns * 2
        if len(self._sessions[session_id]["messages"]) > max_messages:
            self._sessions[session_id]["messages"] = self._sessions[session_id]["messages"][-max_messages:]

session_service = SessionService()
