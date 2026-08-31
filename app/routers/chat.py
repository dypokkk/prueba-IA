from typing import Optional, List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services.cache_service import cache_service
from app.services.vector_store import vector_store
from app.services.hybrid_router import process_inquiry

router = APIRouter(tags=["Chat & Ingestion"])

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Student inquiry text")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    channel: Optional[str] = Field(default="web", description="Inquiry source channel")

class ChatResponse(BaseModel):
    answer: str
    tier: str
    confidence: float
    sources: List[str]
    escalate_to_human: bool
    escalation_reason: Optional[str] = None
    ticket_id: Optional[str] = None
    cached: bool = False
    latency_ms: float = 0.0

@router.post("/api/chat", response_model=ChatResponse)
async def http_chat_endpoint(payload: ChatRequest):
    """Standard REST API endpoint for student inquiries."""
    return process_inquiry(message=payload.message, channel=payload.channel or "api")

@router.post("/api/webhook")
async def webhook_inquiry_endpoint(payload: Dict[str, Any]):
    """Generic webhook endpoint compatible with multi-channel triggers."""
    message = payload.get("message") or payload.get("text") or payload.get("query")
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message' field in payload")
    channel = payload.get("channel", "webhook")
    return process_inquiry(message=str(message), channel=channel)

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
    """WebSocket endpoint for bidirectional real-time chat streaming."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()
            if not user_message:
                continue

            response = process_inquiry(message=user_message, channel="websocket")
            await websocket.send_json(response)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        try:
            await websocket.close()
        except:
            pass
