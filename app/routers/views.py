import markdown
from pathlib import Path
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.services.escalation_service import escalation_service
from app.services.metrics_service import metrics_service
from app.services.vector_store import vector_store

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def landing_view(request: Request):
    """Renders the comprehensive, high-converting informative Landing Page."""
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={
            "app_name": settings.APP_NAME,
            "active_tab": "home"
        }
    )

@router.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    """Renders the standalone interactive web chat interface."""
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "app_name": settings.APP_NAME,
            "active_tab": "chat"
        }
    )

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    """Renders the secluded Admin Dashboard (Analytics, Escalation Tickets & Knowledge Base)."""
    metrics = metrics_service.get_summary()
    tickets = escalation_service.get_tickets()

    # Load and render knowledge base markdown files
    documents = []
    for doc_path in sorted(settings.DATA_DIR.glob("*.md")):
        with open(doc_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        html_content = markdown.markdown(raw_text, extensions=['tables', 'fenced_code'])
        documents.append({
            "name": doc_path.stem,
            "filename": doc_path.name,
            "title": doc_path.stem.replace("_", " ").title(),
            "raw_text": raw_text,
            "html_content": html_content
        })

    pending_tickets = [t for t in tickets if t.get("status") == "PENDING"]
    resolved_tickets = [t for t in tickets if t.get("status") != "PENDING"]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "metrics": metrics,
            "documents": documents,
            "tickets": tickets,
            "pending_tickets": pending_tickets,
            "resolved_tickets": resolved_tickets,
            "pending_count": len(pending_tickets),
            "resolved_count": len(resolved_tickets),
            "total_chunks": len(vector_store.chunks),
            "active_tab": "dashboard"
        }
    )

@router.get("/escalations", response_class=RedirectResponse)
async def escalations_view():
    """Redirects to unified dashboard."""
    return RedirectResponse(url="/dashboard#tickets", status_code=302)

@router.post("/escalations/{ticket_id}/resolve")
async def resolve_ticket_action(request: Request, ticket_id: str, notes: str = Form(default="")):
    """Handles ticket resolution supporting both AJAX JSON and form redirects."""
    success = escalation_service.resolve_ticket(ticket_id=ticket_id, notes=notes)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Look up session_id of the ticket and reset session state in SQLite
    for t in escalation_service.tickets:
        if t.get("ticket_id") == ticket_id:
            s_id = t.get("session_id")
            if s_id:
                from app.services.database import db
                db.update_session(s_id, intake_state="IDLE", active_ticket_id=None)
            break

    # Check if AJAX / JSON request
    accept = request.headers.get("accept", "")
    if "application/json" in accept or request.headers.get("x-requested-with") == "XMLHttpRequest":
        return {"success": True, "ticket_id": ticket_id, "status": "RESOLVED"}
    
    return RedirectResponse(url="/dashboard#tickets", status_code=303)
