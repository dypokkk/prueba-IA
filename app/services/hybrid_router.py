import time
import uuid
import re
from typing import Dict, Any, Optional

from app.config import settings
from app.services.cache_service import cache_service
from app.services.deterministic_service import deterministic_service
from app.services.vector_store import vector_store
from app.services.ai_service import ai_service
from app.services.metrics_service import metrics_service
from app.services.escalation_service import escalation_service
from app.services.session_service import session_service

def is_explicit_escalation_intent(query: str) -> bool:
    """Checks if the user's message is an explicit request for human support, tickets, or formal complaints."""
    clean = query.lower().strip()
    escalation_patterns = [
        r"\b(abrir|crear|generar|solicitar|quiero|necesito|dame)\s+(un\s+)?ticket\b",
        r"\b(hablar|comunicar(me)?|charlar|contactar)\s+(con\s+)?(un\s+)?(asesor|humano|agente|persona|soporte|alguien)\b",
        r"\b(asesor\s+humano|agente\s+humano|atenci[oó]n\s+humana|soporte\s+humano|persona\s+real)\b",
        r"\b(transferir|pasar)\s+(a\s+)?(soporte|humano|asesor)\b",
        r"\b(reembolso|devoluci[oó]n|queja|reclamo|demanda|disputa)\b",
        r"\b(beca\s+del\s+\d+%|descuento\s+del\s+[789]\d+%)\b",
        r"\b(celular|tel[eé]fono|contacto)\s+personal\s+(del|de\s+la)?\s+(director|rector|gerente)\b",
        r"^(quiero\s+hablar\s+con\s+alguien|comun[ií]came\s+con\s+un\s+humano|ayuda\s+humana)$"
    ]
    for pat in escalation_patterns:
        if re.search(pat, clean, re.IGNORECASE):
            return True
    return False

def process_inquiry(message: str, channel: str = "web", session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Central Multi-Turn Hybrid Pipeline:
    Explicit Escalation Check -> Session Context -> Cache Check -> Tier 1 Deterministic -> Tier 2 Multi-Turn Vector RAG (Gemini) -> Tier 3 Escalation
    """
    start_time = time.time()
    query = message.strip()
    
    if not session_id:
        session_id = f"{channel}_session_{uuid.uuid4().hex[:8]}"

    # Add user message to multi-turn conversation memory
    session_service.add_user_message(session_id, query)
    conversation_history = session_service.get_history(session_id)

    # 1. Step 1: Explicit Human Support & Ticket Request Check (Immediate Tier 3 Escalation)
    if is_explicit_escalation_intent(query):
        ticket = escalation_service.create_ticket(
            user_query=query,
            escalation_reason="EXPLICIT_HUMAN_SUPPORT_REQUEST",
            channel=channel,
            confidence=1.0,
            session_id=session_id
        )
        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="escalation",
            is_cache_hit=False,
            is_escalated=True,
            latency_ms=latency_ms
        )
        answer = (
            f"¡Con mucho gusto! He abierto tu ticket de soporte oficial **{ticket['ticket_id']}**.\n\n"
            f"• **Estado**: Pendiente de asignación a un asesor de admisiones.\n"
            f"• **Atención**: Un agente humano revisará tu consulta y se comunicará contigo a la brevedad.\n\n"
            f"¿Deseas dejar algún dato o comentario adicional para el asesor?"
        )
        session_service.add_assistant_message(session_id, answer)
        return {
            "answer": answer,
            "tier": "escalation",
            "confidence": 1.0,
            "sources": [],
            "escalate_to_human": True,
            "escalation_reason": "EXPLICIT_HUMAN_SUPPORT_REQUEST",
            "ticket_id": ticket["ticket_id"],
            "cached": False,
            "session_id": session_id,
            "latency_ms": round(latency_ms, 2)
        }

    # 2. Step 2: Check Cache Layer (for exact repeated queries when no active history)
    if len(conversation_history) <= 1:
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
            res["session_id"] = session_id
            session_service.add_assistant_message(session_id, res.get("answer", ""))
            return res

    # 3. Step 3: Tier 1 - Deterministic Pattern & Intent Matcher
    if settings.ENABLE_DETERMINISTIC_TIER:
        clean_q = query.lower().strip()
        is_followup = clean_q.startswith(("¿y ", "y ", "¿en ", "en ", "¿como ", "como ", "¿cuanto ", "cuanto ")) and len(clean_q.split()) <= 6
        
        if not is_followup:
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
                    "session_id": session_id,
                    "latency_ms": round(latency_ms, 2)
                }
                cache_service.set(query, result)
                metrics_service.record_query(
                    tier="deterministic",
                    is_cache_hit=False,
                    is_escalated=False,
                    latency_ms=latency_ms
                )
                session_service.add_assistant_message(session_id, result["answer"])
                return result

    # 4. Step 4: Tier 2 - Context-Enriched RAG Retrieval Engine (Top-K Chunks)
    retrieval_query = session_service.get_combined_query_context(session_id, query)

    chunks, max_sim, _ = vector_store.similarity_search(
        query=retrieval_query,
        top_k=settings.TOP_K_CHUNKS,
        threshold=0.0
    )

    # If completely empty database, escalate
    if not chunks:
        ticket = escalation_service.create_ticket(
            user_query=query,
            escalation_reason="NO_KNOWLEDGE_CHUNKS_FOUND",
            channel=channel,
            confidence=0.0,
            session_id=session_id
        )
        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="escalation",
            is_cache_hit=False,
            is_escalated=True,
            latency_ms=latency_ms
        )
        answer = f"He transferido tu consulta a nuestro equipo de admisiones humanas (**Ticket {ticket['ticket_id']}**). Un asesor se comunicará contigo en breve."
        session_service.add_assistant_message(session_id, answer)
        return {
            "answer": answer,
            "tier": "escalation",
            "confidence": 0.0,
            "sources": [],
            "escalate_to_human": True,
            "escalation_reason": "NO_KNOWLEDGE_CHUNKS_FOUND",
            "ticket_id": ticket["ticket_id"],
            "cached": False,
            "session_id": session_id,
            "latency_ms": round(latency_ms, 2)
        }

    # 5. Step 5: Tier 2 - Multi-Turn AI Grounded Reasoning (Google Gemini 3.5 Flash Lite)
    ai_result, pt, ct, ai_latency = ai_service.generate_grounded_response(
        query=query,
        context_chunks=chunks,
        conversation_history=conversation_history
    )
    latency_ms = (time.time() - start_time) * 1000

    # Detect if AI triggered escalation or mentioned escalation in answer
    is_escalated = ai_result.get("escalate_to_human", False)
    ai_answer = ai_result.get("answer", "")
    
    if not is_escalated and re.search(r"(he generado un ticket|transferido tu (solicitud|caso|consulta)|ticket de soporte|asesor humano)", ai_answer, re.IGNORECASE):
        is_escalated = True

    ticket_id = None
    if is_escalated:
        ticket = escalation_service.create_ticket(
            user_query=query,
            escalation_reason=ai_result.get("escalation_reason") or "AI_ESCALATION_TRIGGER",
            channel=channel,
            confidence=ai_result.get("confidence", 0.3),
            session_id=session_id
        )
        ticket_id = ticket["ticket_id"]

    result = {
        "answer": ai_answer,
        "tier": "escalation" if is_escalated else "ai_rag",
        "confidence": ai_result.get("confidence", 0.9),
        "sources": ai_result.get("sources", [c.get("filename", "") for c in chunks]),
        "escalate_to_human": is_escalated,
        "escalation_reason": ai_result.get("escalation_reason"),
        "ticket_id": ticket_id,
        "cached": False,
        "session_id": session_id,
        "latency_ms": round(latency_ms, 2)
    }

    # Cache successful non-escalated responses only for single-turn queries
    if not is_escalated and len(conversation_history) <= 1:
        cache_service.set(query, result)

    metrics_service.record_query(
        tier="ai_rag" if not is_escalated else "escalation",
        is_cache_hit=False,
        is_escalated=is_escalated,
        prompt_tokens=pt,
        completion_tokens=ct,
        latency_ms=latency_ms
    )

    session_service.add_assistant_message(session_id, result["answer"])
    return result
