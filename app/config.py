import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Try loading via python-dotenv if installed, else fallback to standard library parser
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
except ImportError:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

class Settings:
    def __init__(self):
        self.APP_NAME = os.getenv("APP_NAME", "Global Language Academy Assistant")
        self.APP_ENV = os.getenv("APP_ENV", "development")
        self.DEBUG = os.getenv("DEBUG", "true").lower() == "true"
        self.PORT = int(os.getenv("PORT", "8000"))
        self.HOST = os.getenv("HOST", "0.0.0.0")

        self.AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")

        # Google Gemini Model (Default: gemini-2.0-flash-lite for ultra-fast, low-cost RAG)
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite").strip()
        self.GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004").strip()

        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip()

        # Telegram Bot Settings
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip()

        # Resend Email API Settings
        self.RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
        self.RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Global Language Academy <onboarding@resend.dev>").strip()

        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.20"))
        self.TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "6"))
        self.ENABLE_DETERMINISTIC_TIER = os.getenv("ENABLE_DETERMINISTIC_TIER", "true").lower() == "true"
        self.TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
        self.MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "450"))

        self.CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        self.MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "500"))
        self.ESCALATION_WEBHOOK_URL = os.getenv("ESCALATION_WEBHOOK_URL", "")

        # CORS — restrict to your production domain in production
        _allowed = os.getenv("ALLOWED_ORIGINS", "*")
        self.ALLOWED_ORIGINS = [o.strip() for o in _allowed.split(",") if o.strip()]

        self.DATA_DIR = BASE_DIR / "data"
        self.STATIC_DIR = BASE_DIR / "static"
        self.TEMPLATES_DIR = BASE_DIR / "templates"
        self.VECTOR_STORE_PATH = BASE_DIR / "data" / "vector_store.json"
        self.TICKETS_STORE_PATH = BASE_DIR / "data" / "escalation_tickets.json"

        # SQLite DB path — override via DB_PATH env var to point to a Railway persistent volume
        # e.g. DB_PATH=/data/conversations.db
        _db_path = os.getenv("DB_PATH", "")
        if _db_path:
            self.DB_PATH = Path(_db_path)
        else:
            self.DB_PATH = self.DATA_DIR / "conversations.db"

settings = Settings()
