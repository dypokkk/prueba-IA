from fastapi import APIRouter
from app.services.metrics_service import metrics_service
from app.services.cache_service import cache_service

router = APIRouter(prefix="/api", tags=["Metrics & Observability"])

@router.get("/metrics")
async def get_system_metrics():
    """
    Returns real-time analytics including query counts, token usage,
    estimated USD costs, cache savings, and escalation rates.
    """
    summary = metrics_service.get_summary()
    summary["active_cache_entries"] = cache_service.size()
    return summary

@router.post("/cache/clear")
async def clear_cache():
    """Flushes all in-memory query response cache entries."""
    cache_service.clear()
    return {"message": "Cache successfully cleared", "active_cache_entries": 0}
