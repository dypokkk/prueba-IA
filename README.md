# Intelligent Customer Support Assistant with Tiered Deterministic-RAG & Multi-Channel Automation

A production-grade, highly cost-efficient, and grounded Customer Support Assistant tailored for **Global Language Academy** (*Academia de Idiomas*). Engineered with **Python 3, FastAPI, Jinja2, Tailwind CSS, Google Gemini API, WebSockets, Telegram Bot Integration, and Docker with Live-Reload**.

---

## 🌟 Key Architectural Features

1. **Tiered Hybrid Routing Strategy**:
   - **Tier 1 (Deterministic Engine)**: High-speed pattern & FAQ matcher for standard queries (pricing tables, payment methods, campus locations, schedules). Responds in **$<2\text{ms}$** with **\$0.00 AI token cost**.
   - **Tier 2 (AI Grounded RAG)**: BM25 + semantic vector retrieval over 3 official English markdown knowledge documents + **Google Gemini API** (`gemini-3.6-flash` / `gemini-3.7-flash` cascade) with few-shot prompt grounding (`temperature: 0.1`) to eliminate hallucinations.
   - **Tier 3 (Automated Human Escalation)**: Automatically routes out-of-scope, refund, or sensitive inquiries to the human support queue (`/escalations`) with webhook dispatch.
2. **In-Memory Query Response Cache**:
   - Normalized LRU cache returning instant zero-cost responses for repeated inquiries.
3. **Multi-Channel Support (WebSockets & Telegram Bot)**:
   - **Web UI**: Modern Jinja2 + Tailwind CSS interface with bidirectional WebSockets (`/ws/chat`), instant prompt chips, 3 animated thinking dots, and full Markdown rendering via `Marked.js`.
   - **Telegram Bot**: Full integration with two modes: **Standalone Long-Polling Runner** (`scripts/telegram_bot.py`) and **FastAPI Webhook** (`POST /api/telegram/webhook`).
4. **Real-Time Operational Metrics Dashboard (`/dashboard`)**:
   - Tracks total queries, cache hit rate %, token consumption, estimated USD costs, and human escalation rates.
5. **Developer Experience (Docker with Hot Live-Reload)**:
   - Volume bind-mounted Docker Compose setup so code changes take effect immediately without rebuilding containers.

---

## 🏗️ System Architecture Flow

```
                                  +---------------------------------------+
                                  |            Inquiry Channels           |
                                  | (Tailwind UI / WebSocket / Telegram)  |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                    +-------------------------------------------------------------------+
                    |                      FastAPI Python Backend                       |
                    |                                                                   |
                    |  +-------------------------------------------------------------+  |
                    |  | STEP 1: Query Cache Layer (In-memory normalized LRU)        |  |
                    |  | -> Hit: Return response (<5ms, $0.00 cost)                  |  |
                    |  +------------------------------+------------------------------+  |
                    |                                 | Cache Miss                      |
                    |                                 v                                 |
                    |  +-------------------------------------------------------------+  |
                    |  | STEP 2: Tier 1 - Deterministic Rule & Pattern Matcher       |  |
                    |  | -> Match: Return verified factual answer (<2ms, $0.00 cost) |  |
                    |  +------------------------------+------------------------------+  |
                    |                                 | No Match                        |
                    |                                 v                                 |
                    |  +-------------------------------------------------------------+  |
                    |  | STEP 3: Tier 2 - BM25 & Semantic Knowledge Retrieval        |  |
                    |  | -> 01_courses_and_pricing.md                                |  |
                    |  | -> 02_schedules_and_modalities.md                           |  |
                    |  | -> 03_enrollment_and_certifications.md                      |  |
                    |  +------------------------------+------------------------------+  |
                    |                                 | Context Chunks Retrieved        |
                    |                                 v                                 |
                    |  +-------------------------------------------------------------+  |
                    |  | STEP 4: Google Gemini API (Grounding & Few-Shots)           |  |
                    |  +------------------------------+------------------------------+  |
                    |                                 | If Out-of-Scope / Low Score     |
                    |                                 v                                 |
                    |  +-------------------------------------------------------------+  |
                    |  | STEP 5: Tier 3 - Human Escalation Queue (/escalations)      |  |
                    |  +-------------------------------------------------------------+  |
                    |                                                                   |
                    |  +-------------------------------------------------------------+  |
                    |  | STEP 6: Real-Time Operational Metrics Tracker (/api/metrics)|  |
                    |  +-------------------------------------------------------------+  |
                    +-------------------------------------------------------------------+
```

---

## 📁 Project Structure

```
prueba-IA/
├── data/
│   ├── 01_courses_and_pricing.md             # Document 1: Tuition rates (COP/USD), discounts, payment channels
│   ├── 02_schedules_and_modalities.md        # Document 2: Morning/evening/Saturday schedules, campuses
│   ├── 03_enrollment_and_certifications.md   # Document 3: CEFR levels, diagnostic test, IELTS/TOEFL/Cambridge
│   ├── vector_store.json                     # Persistent vector embeddings and chunk index
│   └── escalation_tickets.json               # Persisted human escalation ticket queue
├── app/
│   ├── config.py                             # Settings, environment variables (.env loading)
│   ├── services/
│   │   ├── document_loader.py                # Markdown chunking with overlap & metadata extraction
│   │   ├── vector_store.py                   # BM25 & multilingual query expansion retrieval engine
│   │   ├── deterministic_service.py          # Tier 1 deterministic pattern & FAQ rule matcher
│   │   ├── ai_service.py                     # Google Gemini API & model cascade failover
│   │   ├── telegram_service.py               # Telegram Bot API client & dispatcher
│   │   ├── cache_service.py                  # In-memory query response cache (cost & latency optimizer)
│   │   ├── metrics_service.py                # Analytics: query counts, token cost estimation, escalation rate
│   │   └── escalation_service.py             # Human escalation dispatcher & ticket queue manager
│   ├── prompts/
│   │   └── system_prompt.py                  # Grounding instructions, brand persona & few-shot examples
│   ├── tools/
│   │   └── custom_tools.py                   # Custom skills (Course quoter & CEFR level placement advisor)
│   ├── routers/
│   │   ├── chat.py                           # REST & WebSocket endpoints (/api/chat, /ws/chat, /api/webhook)
│   │   ├── telegram.py                       # Telegram Webhook & Status endpoints (/api/telegram/webhook)
│   │   ├── metrics.py                        # Analytics endpoints (/api/metrics, /api/cache/clear)
│   │   └── views.py                          # Jinja2 template views (Chat, Dashboard, Escalations)
│   └── main.py                               # FastAPI application entrypoint with lifespan startup
├── templates/
│   ├── base.html                             # Base layout with Tailwind CSS CDN & Marked.js
│   ├── chat.html                             # Chat interface with WebSockets & thinking animation
│   ├── dashboard.html                        # Real-time metrics & Knowledge Base inspector
│   └── escalation_queue.html                 # Human support escalation desk
├── static/
│   ├── css/custom.css                        # Custom styling, markdown typography & thinking dots
│   ├── js/chat.js                            # Bidirectional WebSocket client & Marked.js rendering
│   └── js/dashboard.js                       # Real-time polling & metrics graphs
├── scripts/
│   ├── ingest.py                             # Knowledge Base chunking & BM25 indexing pipeline
│   ├── telegram_bot.py                       # Standalone Telegram Bot Long-Polling runner
│   ├── test_pipeline.py                      # End-to-end integration test runner (6/6 tests)
│   └── package_deliverable.py                # Automated .zip packaging script
├── tests/
│   └── test_unit_suite.py                    # Complete unit test suite (16/16 tests passing)
├── Dockerfile                                # Python 3.11-slim container with live-reload
├── docker-compose.yml                        # Docker Compose with bind mount (.:/app)
├── requirements.txt                          # Python dependencies
├── .env.example                              # Environment variable template
└── README.md                                 # Complete documentation
```

---

## 🚀 Quick Start Guide

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your `GEMINI_API_KEY` is set in `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash
```

### 2. Run with Docker Compose (Recommended)
```bash
docker compose up --build
```
The server will start at **http://localhost:8000** with hot-reload enabled.

### 3. Access Web Interfaces
- **Chat Interface**: [http://localhost:8000/chat](http://localhost:8000/chat)
- **Analytics Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Escalation Desk**: [http://localhost:8000/escalations](http://localhost:8000/escalations)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🤖 Telegram Bot Integration

### Setup Telegram Bot in 1 Minute:
1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`, name your bot (e.g. `GlobalLanguageAcademyBot`), and copy the provided **HTTP API Token**.
3. Add the token to your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
   ```

### Running the Telegram Bot:
#### Option A: Standalone Polling Mode (Local Development)
No public IP or ngrok needed! Run:
```bash
python3 scripts/telegram_bot.py
# Or inside docker:
docker exec -it global_language_academy_assistant python3 scripts/telegram_bot.py
```

#### Option B: Webhook Mode (Production)
Set your public URL in `.env`:
```env
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
```
Telegram will automatically push updates to `/api/telegram/webhook`.

---

## 🧪 Running Unit Tests
Execute the 16-test automated suite:
```bash
python3 -m unittest discover tests
# Or inside Docker:
docker exec global_language_academy_assistant python3 -m unittest discover tests
```

---

## 📦 Packaging Deliverable
Generate the submission `.zip` file:
```bash
python3 scripts/package_deliverable.py
```
Outputs `customer_support_rag_assistant.zip`.
