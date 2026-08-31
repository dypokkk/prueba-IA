import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.cache_service import cache_service
from app.services.vector_store import vector_store
from app.services.hybrid_router import process_inquiry
from app.services.session_service import session_service

router = APIRouter(tags=["Chat & Ingestion"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student inquiry text")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    channel: Optional[str] = Field(default="web", description="Inquiry source channel")

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
    return process_inquiry(
        message=payload.message,
        channel=payload.channel or "api",
        session_id=payload.session_id
    )

@router.post("/api/chat/clear")
async def clear_session_endpoint(payload: ClearSessionRequest):
    """Clears conversation history for a specific session."""
    session_service.clear(payload.session_id)
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
    """WebSocket endpoint with persistent multi-turn conversational session context."""
    await websocket.accept()
    session_id = f"ws_{uuid.uuid4().hex[:8]}"
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("action") == "clear":
                session_service.clear(session_id)
                await websocket.send_json({
                    "answer": "Conversación reiniciada.",
                    "tier": "system",
                    "session_id": session_id,
                    "confidence": 1.0,
                    "sources": [],
                    "escalate_to_human": False
                })
                continue

            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            client_session_id = data.get("session_id") or session_id
            response = process_inquiry(message=user_message, channel="websocket", session_id=client_session_id)
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        try:
            await websocket.close()
        except:
            pass
