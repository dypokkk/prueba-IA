import uuid
from typing import Optional, List, Dict, Any, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.cache_service import cache_service
from app.services.vector_store import vector_store
from app.services.hybrid_router import process_inquiry
from app.services.session_service import session_service
from app.services.escalation_service import escalation_service

router = APIRouter(tags=["Chat & Ingestion"])

class ConnectionManager:
    """Manages active WebSockets across sessions and broadcasts between human agents and students."""
    def __init__(self):
        self.active_sessions: Dict[str, Set[WebSocket]] = {}

    def register(self, session_id: str, websocket: WebSocket):
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = set()
        self.active_sessions[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_sessions:
            self.active_sessions[session_id].discard(websocket)
            if not self.active_sessions[session_id]:
                del self.active_sessions[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict, exclude_socket: Optional[WebSocket] = None):
        if session_id in self.active_sessions:
            dead_sockets = set()
            for ws in list(self.active_sessions[session_id]):
                if exclude_socket and ws == exclude_socket:
                    continue
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_sockets.add(ws)
            for dead in dead_sockets:
                self.active_sessions[session_id].discard(dead)

ws_manager = ConnectionManager()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student inquiry text")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    channel: Optional[str] = Field(default="web", description="Inquiry source channel")

class AgentReplyRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Target session identifier of the student")
    message: str = Field(..., min_length=1, description="Response from human advisor")
    ticket_id: Optional[str] = Field(default=None, description="Associated ticket ID")
    author_name: Optional[str] = Field(default="Asesor de Admisiones Humano", description="Name of the agent")

class ClearSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Session ID to clear")

class ChatResponse(BaseModel):
    answer: str
    tier: str
    confidence: float
    sources: List[str]
    escalate_to_human: bool
    escalation_reason: Optional[str] = None
    ticket_id: Optional[str] = None
    cached: bool = False
    session_id: Optional[str] = None
    latency_ms: float = 0.0

@router.post("/api/chat", response_model=ChatResponse)
async def http_chat_endpoint(payload: ChatRequest):
    """Standard REST API endpoint for student inquiries with multi-turn session memory."""
    response = process_inquiry(
        message=payload.message,
        channel=payload.channel or "api",
        session_id=payload.session_id
    )
    # Broadcast to any admin connected via WebSocket to this session
    effective_session = response.get("session_id") or payload.session_id
    if effective_session:
        await ws_manager.broadcast_to_session(effective_session, {
            "event": "user_message",
            "message": payload.message,
            "session_id": effective_session,
            "sender_role": "user"
        })
        await ws_manager.broadcast_to_session(effective_session, response)
    return response

@router.post("/api/chat/agent-reply")
async def agent_reply_endpoint(payload: AgentReplyRequest):
    """Allows an admin to send a real-time human response to a student's session."""
    session_service.add_assistant_message(payload.session_id, f"**[{payload.author_name}]** {payload.message}")
    
    reply_payload = {
        "answer": payload.message,
        "tier": "human_agent",
        "sender_role": "admin",
        "author": payload.author_name,
        "session_id": payload.session_id,
        "ticket_id": payload.ticket_id,
        "confidence": 1.0,
        "sources": [],
        "escalate_to_human": False
    }
    await ws_manager.broadcast_to_session(payload.session_id, reply_payload)
    return {"success": True, "delivered_to": payload.session_id, "ticket_id": payload.ticket_id}

@router.get("/api/chat/history/{session_id}")
async def get_session_history_endpoint(session_id: str):
    """Retrieves full conversation history for a given session / ticket."""
    messages = session_service.get_history(session_id)
    return {"session_id": session_id, "messages": messages, "count": len(messages)}

@router.post("/api/chat/clear")
async def clear_session_endpoint(payload: ClearSessionRequest):
    """Clears conversation history for a specific session."""
    session_service.clear(payload.session_id)
    await ws_manager.broadcast_to_session(payload.session_id, {
        "answer": "Conversación reiniciada.",
        "tier": "system",
        "session_id": payload.session_id,
        "confidence": 1.0,
        "sources": [],
        "escalate_to_human": False
    })
    return {"message": "Session history cleared successfully", "session_id": payload.session_id}

@router.post("/api/webhook")
async def webhook_inquiry_endpoint(payload: Dict[str, Any]):
    """Generic webhook endpoint compatible with multi-channel triggers."""
    message = payload.get("message") or payload.get("text") or payload.get("query")
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message' field in payload")
    channel = payload.get("channel", "webhook")
    session_id = payload.get("session_id") or payload.get("user_id") or payload.get("chat_id")
    return process_inquiry(message=str(message), channel=channel, session_id=session_id)

@router.get("/api/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "ai_provider": settings.AI_PROVIDER,
        "vector_store_indexed": vector_store.is_indexed(),
        "total_chunks": len(vector_store.chunks),
        "cache_size": cache_service.size()
    }

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """WebSocket endpoint supporting live 2-way student-agent communication."""
    current_session_id = f"ws_{uuid.uuid4().hex[:8]}"
    await websocket.accept()
    ws_manager.register(current_session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            role = data.get("role", "user")
            client_session = data.get("session_id") or current_session_id

            if client_session != current_session_id:
                ws_manager.disconnect(current_session_id, websocket)
                current_session_id = client_session
                ws_manager.register(current_session_id, websocket)

            if action == "join":
                await websocket.send_json({
                    "answer": f"Conectado a la sesión {current_session_id}.",
                    "tier": "system",
                    "session_id": current_session_id,
                    "confidence": 1.0,
                    "sources": [],
                    "escalate_to_human": False
                })
                continue

            if action == "clear":
                session_service.clear(current_session_id)
                await ws_manager.broadcast_to_session(current_session_id, {
                    "answer": "Conversación reiniciada.",
                    "tier": "system",
                    "session_id": current_session_id,
                    "confidence": 1.0,
                    "sources": [],
                    "escalate_to_human": False
                })
                continue

            # 1. ADMIN / HUMAN AGENT REPLY
            if role == "admin" or action == "agent_reply":
                agent_message = data.get("message", "").strip()
                if not agent_message:
                    continue

                ticket_id = data.get("ticket_id")
                author = data.get("author") or "Asesor de Admisiones Humano"

                # Persist in conversation memory
                session_service.add_assistant_message(current_session_id, f"**[{author}]** {agent_message}")

                # Broadcast to student console in real time (excluding admin socket since admin already rendered it)
                payload = {
                    "answer": agent_message,
                    "tier": "human_agent",
                    "sender_role": "admin",
                    "author": author,
                    "session_id": current_session_id,
                    "ticket_id": ticket_id,
                    "confidence": 1.0,
                    "sources": [],
                    "escalate_to_human": False
                }
                await ws_manager.broadcast_to_session(current_session_id, payload, exclude_socket=websocket)
                continue

            # 2. STUDENT INQUIRY
            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            # Broadcast user message so any connected admin console sees it in real-time
            await ws_manager.broadcast_to_session(current_session_id, {
                "event": "user_message",
                "message": user_message,
                "session_id": current_session_id,
                "sender_role": "user"
            }, exclude_socket=websocket)

            # Process inquiry through RAG / Deterministic engine
            response = process_inquiry(message=user_message, channel="websocket", session_id=current_session_id)
            
            # Broadcast response to all participants in this session
            await ws_manager.broadcast_to_session(current_session_id, response)

    except WebSocketDisconnect:
        ws_manager.disconnect(current_session_id, websocket)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        ws_manager.disconnect(current_session_id, websocket)
