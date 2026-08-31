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
from app.services.email_service import email_service

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

from app.services.database import db

def process_inquiry(message: str, channel: str = "web", session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Central Multi-Turn Hybrid Pipeline:
    Intake State Machine -> Email Capture (Resend) -> Explicit Escalation Qualification -> Session Context -> Cache Check -> Tier 1 Deterministic -> Tier 2 Multi-Turn Vector RAG (Gemini) -> Tier 3 Escalation
    """
    start_time = time.time()
    query = message.strip()
    
    if not session_id:
        session_id = f"{channel}_session_{uuid.uuid4().hex[:8]}"

    # 1. Load session record from SQLite
    session_data = db.get_session(session_id) or {}
    intake_state = session_data.get("intake_state", "IDLE")
    intake_data = session_data.get("intake_data", {})
    if not isinstance(intake_data, dict):
        intake_data = {}

    # Add user message to multi-turn conversation memory
    session_service.add_user_message(session_id, query)
    conversation_history = session_service.get_history(session_id)

    # ==================== INTAKE STATE MACHINE (PRE-ESCALATION QUALIFICATION) ====================
    # Step A: User is providing Name
    if intake_state == "AWAITING_NAME":
        intake_data["student_name"] = query
        db.update_session(session_id, student_name=query, intake_state="AWAITING_CONTACT", intake_data=intake_data)
        latency_ms = (time.time() - start_time) * 1000
        answer = (
            f"¡Mucho gusto, **{query}**!\n\n"
            f"• Para asignarte el asesor adecuado y enviarte la confirmación oficial:\n"
            f"Por favor compárteme tu **correo electrónico** y un **número de WhatsApp / teléfono**:"
        )
        session_service.add_assistant_message(session_id, answer, tier="deterministic")
        return {
            "answer": answer,
            "tier": "deterministic",
            "confidence": 1.0,
            "sources": ["05_admissions_and_qualification_guide.md#1-step-by-step-enrollment-and-registration-process"],
            "escalate_to_human": False,
            "escalation_reason": None,
            "ticket_id": None,
            "cached": False,
            "session_id": session_id,
            "latency_ms": round(latency_ms, 2)
        }

    # Step B: User is providing Contact Information (Email & Phone)
    if intake_state == "AWAITING_CONTACT":
        email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', query)
        email_val = email_matches[0] if email_matches else None
        phone_matches = re.findall(r'(\+?\d[\d\s\-]{7,15}\d)', query)
        phone_val = phone_matches[0].strip() if phone_matches else None

        intake_data["email"] = email_val or intake_data.get("email") or query
        intake_data["phone"] = phone_val or intake_data.get("phone") or "No especificado"

        db.update_session(
            session_id,
            email=intake_data.get("email"),
            phone=intake_data.get("phone"),
            intake_state="AWAITING_DETAILS",
            intake_data=intake_data
        )
        latency_ms = (time.time() - start_time) * 1000
        answer = (
            f"¡Perfecto! Hemos registrado tus datos de contacto.\n\n"
            f"• Por último, indícame qué **idioma te interesa** (o nivel) y una breve descripción de tu **consulta o caso particular**:"
        )
        session_service.add_assistant_message(session_id, answer, tier="deterministic")
        return {
            "answer": answer,
            "tier": "deterministic",
            "confidence": 1.0,
            "sources": ["05_admissions_and_qualification_guide.md#1-step-by-step-enrollment-and-registration-process"],
            "escalate_to_human": False,
            "escalation_reason": None,
            "ticket_id": None,
            "cached": False,
            "session_id": session_id,
            "latency_ms": round(latency_ms, 2)
        }

    # Step C: User is providing Inquiry Details -> Finalize & Dispatch Qualified Ticket!
    if intake_state == "AWAITING_DETAILS":
        intake_data["inquiry_details"] = query
        student_name = intake_data.get("student_name") or "Estudiante"
        user_email = intake_data.get("email")
        user_phone = intake_data.get("phone")

        ticket = escalation_service.create_ticket(
            user_query=query,
            escalation_reason="QUALIFIED_HUMAN_INTAKE_REQUEST",
            channel=channel,
            confidence=1.0,
            session_id=session_id,
            student_name=student_name,
            email=user_email,
            phone=user_phone,
            target_language=query,
            dossier=intake_data
        )

        # Reset intake state
        db.update_session(session_id, intake_state="IDLE", intake_data={})

        # Send official confirmation email via Resend if email is present
        email_sent = False
        if user_email and "@" in user_email:
            email_res = email_service.send_email(
                to_email=user_email,
                subject=f"Solicitud Radicada: Ticket {ticket['ticket_id']} - Global Language Academy",
                html_body=f"""
                <h2>¡Hola, {student_name}!</h2>
                <p>Tu solicitud ha sido radicada oficialmente con el <strong>Ticket {ticket['ticket_id']}</strong>.</p>
                <p><strong>Detalle de tu caso:</strong> "{query}"</p>
                <p>Un asesor de admisiones humanas revisará tu expediente y te contactará hoy mismo.</p>
                """
            )
            email_sent = email_res.get("success", False)

        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="escalation",
            is_cache_hit=False,
            is_escalated=True,
            latency_ms=latency_ms
        )

        answer = (
            f"¡Todo listo, **{student_name}**! He radicado tu caso oficialmente con el **Ticket {ticket['ticket_id']}**.\n\n"
            f"• **Expediente Completo**: Registrado para el equipo de admisiones humanas con tu contacto.\n"
            f"• **Notificación**: Te enviamos la confirmación oficial a tu correo vía **Resend**.\n"
            f"• **Tiempo de Respuesta**: Un asesor se comunicará contigo hoy mismo.\n\n"
            f"¿Hay alguna otra pregunta sobre nuestros cursos en la que pueda orientarte mientras tanto?"
        )
        session_service.add_assistant_message(session_id, answer, tier="escalation", ticket_id=ticket['ticket_id'])
        return {
            "answer": answer,
            "tier": "escalation",
            "confidence": 1.0,
            "sources": ["05_admissions_and_qualification_guide.md#1-step-by-step-enrollment-and-registration-process"],
            "escalate_to_human": True,
            "escalation_reason": "QUALIFIED_HUMAN_INTAKE_REQUEST",
            "ticket_id": ticket["ticket_id"],
            "email_sent": email_sent,
            "cached": False,
            "session_id": session_id,
            "latency_ms": round(latency_ms, 2)
        }

    # ==================== STEP 0: EMAIL RESEND DIRECT CAPTURE ====================
    email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', query)
    if email_matches and intake_state == "IDLE":
        user_email = email_matches[0]
        history_text = " ".join([m.get("content", "") for m in conversation_history]).lower()
        
        schedule_name = "9:00 AM – 11:00 AM (Lunes a Jueves)" if ("9" in history_text or "9:00" in history_text or "9am" in history_text) else "Horario Solicitado"
        mode = "De inmediato" if "inmediato" in history_text else "Próximo módulo"

        email_res = email_service.send_schedule_change_confirmation(
            to_email=user_email,
            new_schedule=schedule_name,
            effective_mode=mode
        )
        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="deterministic",
            is_cache_hit=False,
            is_escalated=False,
            latency_ms=latency_ms
        )

        answer = (
            f"¡Muchas gracias! Ya he registrado tu correo electrónico (**{user_email}**) en nuestra plataforma.\n\n"
            f"• **Actualización**: Tu solicitud de cambio al horario de las **{schedule_name}** ({mode}) ha sido enviada al equipo de admisiones vía Resend.\n"
            f"• **Respuesta**: Te contactaremos a este correo muy pronto con la confirmación final de cupo.\n\n"
            f"¿Te puedo ayudar con alguna otra duda sobre tus clases?"
        )
        session_service.add_assistant_message(session_id, answer, tier="deterministic")
        return {
            "answer": answer,
            "tier": "deterministic",
            "confidence": 1.0,
            "sources": ["02_schedules_and_modalities.md#4-schedule-changes-and-transfers"],
            "escalate_to_human": False,
            "escalation_reason": None,
            "ticket_id": None,
            "email_sent": email_res.get("success", False),
            "cached": False,
            "session_id": session_id,
            "latency_ms": round(latency_ms, 2)
        }

    # ==================== STEP 1: EXPLICIT HUMAN SUPPORT REQUEST (START INTAKE) ====================
    if is_explicit_escalation_intent(query) and intake_state == "IDLE":
        db.update_session(session_id, intake_state="AWAITING_NAME", intake_data={"initial_query": query})
        latency_ms = (time.time() - start_time) * 1000
        metrics_service.record_query(
            tier="deterministic",
            is_cache_hit=False,
            is_escalated=False,
            latency_ms=latency_ms
        )
        answer = (
            "¡Con mucho gusto te comunico con un asesor de admisiones humanas! 😊\n\n"
            "• Para asignarte al especialista adecuado según tu sede o modalidad:\n\n"
            "¿Cuál es tu **nombre y apellido**?"
        )
        session_service.add_assistant_message(session_id, answer, tier="deterministic")
        return {
            "answer": answer,
            "tier": "deterministic",
            "confidence": 1.0,
            "sources": ["05_admissions_and_qualification_guide.md#1-step-by-step-enrollment-and-registration-process"],
            "escalate_to_human": False,
            "escalation_reason": None,
            "ticket_id": None,
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
