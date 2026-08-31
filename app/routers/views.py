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
@router.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    """Renders the interactive web chat interface."""
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
    """Renders the real-time analytics dashboard and knowledge base inspector."""
    metrics = metrics_service.get_summary()

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

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": settings.APP_NAME,
            "metrics": metrics,
            "documents": documents,
            "total_chunks": len(vector_store.chunks),
            "active_tab": "dashboard"
        }
    )

@router.get("/escalations", response_class=HTMLResponse)
async def escalations_view(request: Request):
    """Renders the human support ticket management desk."""
    tickets = escalation_service.get_tickets()
    return templates.TemplateResponse(
        request=request,
        name="escalation_queue.html",
        context={
            "app_name": settings.APP_NAME,
            "tickets": tickets,
            "pending_count": len([t for t in tickets if t.get("status") == "PENDING"]),
            "active_tab": "escalations"
        }
    )

@router.post("/escalations/{ticket_id}/resolve")
async def resolve_ticket_action(ticket_id: str, notes: str = Form(default="")):
    """Handles ticket resolution form submission."""
    success = escalation_service.resolve_ticket(ticket_id=ticket_id, notes=notes)
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return RedirectResponse(url="/escalations", status_code=303)
