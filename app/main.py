from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.vector_store import vector_store
from app.routers import chat, metrics, views

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure vector store is initialized
    print(f"[Lifespan] Initializing {settings.APP_NAME}...")
    if not vector_store.load():
        print("[Lifespan] Index not found. Building vector index from knowledge documents...")
        vector_store.build_index()
    else:
        print(f"[Lifespan] Vector store loaded with {len(vector_store.chunks)} chunks.")
    yield
    # Shutdown
    print("[Lifespan] Shutting down assistant...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Customer Support Assistant with Tiered Deterministic-RAG Routing & Automation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
