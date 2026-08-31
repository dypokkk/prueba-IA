import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.services.vector_store import vector_store
from app.services.telegram_service import telegram_service
from app.routers import chat, metrics, views, telegram, tools

stop_telegram_event = asyncio.Event()

# Rate limiter: 40 requests/minute per IP on AI endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure vector store is initialized
    print(f"[Lifespan] Initializing {settings.APP_NAME}...")
    if not vector_store.load():
        print("[Lifespan] Index not found. Building vector index from knowledge documents...")
        vector_store.build_index()
    else:
        print(f"[Lifespan] Vector store loaded with {len(vector_store.chunks)} chunks.")

    # Auto-start Telegram Bot Polling inside Docker if token is present
    telegram_task = None
    if telegram_service.is_configured:
        print("[Lifespan] Starting Telegram Bot background runner inside Docker...")
        stop_telegram_event.clear()
        telegram_task = asyncio.create_task(telegram_service.run_polling(stop_telegram_event))
    else:
        print("[Lifespan] TELEGRAM_BOT_TOKEN not configured in .env (Web chat active).")

    yield

    # Shutdown
    print("[Lifespan] Shutting down assistant...")
    stop_telegram_event.set()
    if telegram_task:
        await asyncio.sleep(0.5)

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Customer Support Assistant with Tiered Deterministic-RAG Routing & Automation",
    version="1.0.0",
    lifespan=lifespan
)

# Rate Limiter middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware — restrict via ALLOWED_ORIGINS env var in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Include Routers
app.include_router(views.router)
app.include_router(chat.router)
app.include_router(metrics.router)
app.include_router(telegram.router)
app.include_router(tools.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
