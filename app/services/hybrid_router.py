import time
from typing import Dict, Any

from app.config import settings
from app.services.cache_service import cache_service
from app.services.deterministic_service import deterministic_service
from app.services.vector_store import vector_store
from app.services.ai_service import ai_service
from app.services.metrics_service import metrics_service
from app.services.escalation_service import escalation_service

def process_inquiry(message: str, channel: str = "web") -> Dict[str, Any]:
    """
    Central Hybrid Pipeline:
    Cache Check -> Tier 1 Deterministic -> Tier 2 Vector RAG (Gemini/OpenAI) -> Tier 3 Escalation
    """
    start_time = time.time()
    query = message.strip()

    # 1. Step 1: Check Cache Layer
    cached_data = cache_service.get(query)
    if cached_data:
        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="cache",
            is_cache_hit=True,
            is_escalated=False,
            latency_ms=latency_ms
        )
        res = dict(cached_data)
        res["cached"] = True
        res["latency_ms"] = round(latency_ms, 2)
        res["tier"] = "cache"
        return res

    # 2. Step 2: Tier 1 - Deterministic Pattern & Intent Matcher
    if settings.ENABLE_DETERMINISTIC_TIER:
        det_match = deterministic_service.match(query)
        if det_match:
            latency_ms = (time.time() - start_time) * 1000
            result = {
                "answer": det_match["answer"],
                "tier": "deterministic",
                "confidence": 1.0,
                "sources": det_match["sources"],
                "escalate_to_human": False,
                "escalation_reason": None,
                "ticket_id": None,
                "cached": False,
                "latency_ms": round(latency_ms, 2)
            }
            cache_service.set(query, result)
            metrics_service.record_query(
                tier="deterministic",
                is_cache_hit=False,
                is_escalated=False,
                latency_ms=latency_ms
            )
            return result

    # 3. Step 3: Tier 2 - RAG Retrieval Engine (Top-K Chunks)
    chunks, max_sim, _ = vector_store.similarity_search(
        query=query,
        top_k=settings.TOP_K_CHUNKS,
        threshold=0.0  # Retrieve top chunks for AI context
    )

    # If completely empty database, escalate
    if not chunks:
        ticket = escalation_service.create_ticket(
            user_query=query,
            escalation_reason="NO_KNOWLEDGE_CHUNKS_FOUND",
            channel=channel,
            confidence=0.0
        )
        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="escalation",
            is_cache_hit=False,
            is_escalated=True,
            latency_ms=latency_ms
        )
        return {
            "answer": "He transferido tu consulta a nuestro equipo de admisiones humanas para brindarte información exacta y personalizada. Un asesor se comunicará contigo en breve.",
            "tier": "escalation",
            "confidence": 0.0,
            "sources": [],
            "escalate_to_human": True,
            "escalation_reason": "NO_KNOWLEDGE_CHUNKS_FOUND",
            "ticket_id": ticket["ticket_id"],
            "cached": False,
            "latency_ms": round(latency_ms, 2)
        }

    # 4. Step 4: Tier 2 - AI Grounded Reasoning (Google Gemini)
    ai_result, pt, ct, ai_latency = ai_service.generate_grounded_response(query, chunks)
    latency_ms = (time.time() - start_time) * 1000

    is_escalated = ai_result.get("escalate_to_human", False)
    ticket_id = None

    if is_escalated:
        ticket = escalation_service.create_ticket(
            user_query=query,
            escalation_reason=ai_result.get("escalation_reason", "AI_ESCALATION_FLAG"),
            channel=channel,
            confidence=ai_result.get("confidence", 0.3)
        )
        ticket_id = ticket["ticket_id"]

    result = {
        "answer": ai_result.get("answer", ""),
        "tier": "escalation" if is_escalated else "ai_rag",
        "confidence": ai_result.get("confidence", 0.9),
        "sources": ai_result.get("sources", [c.get("filename", "") for c in chunks]),
        "escalate_to_human": is_escalated,
        "escalation_reason": ai_result.get("escalation_reason"),
        "ticket_id": ticket_id,
        "cached": False,
        "latency_ms": round(latency_ms, 2)
    }

    # Cache successful non-escalated responses
    if not is_escalated:
        cache_service.set(query, result)

    metrics_service.record_query(
        tier="ai_rag" if not is_escalated else "escalation",
        is_cache_hit=False,
        is_escalated=is_escalated,
        prompt_tokens=pt,
        completion_tokens=ct,
        latency_ms=latency_ms
    )

    return result
