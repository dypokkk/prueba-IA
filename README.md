# Intelligent Customer Support Assistant with Tiered Deterministic-RAG & Multi-Channel Automation

A production-grade, highly cost-efficient, and grounded Customer Support Assistant tailored for **Global Language Academy** (*Academia de Idiomas*). Engineered with **Python 3, FastAPI, Jinja2, Tailwind CSS, Google Gemini API, WebSockets, and Docker with Live-Reload**.

---

## 🌟 Key Architectural Features

1. **Tiered Hybrid Routing Strategy**:
   - **Tier 1 (Deterministic Engine)**: High-speed pattern & FAQ matcher for standard queries (pricing tables, payment methods, campus locations, schedules). Responds in **$<2\text{ms}$** with **\$0.00 AI token cost**.
   - **Tier 2 (AI Grounded RAG)**: Semantic vector retrieval over 3 official English markdown knowledge documents + **Google Gemini API** (`gemini-1.5-flash` / `text-embedding-004`) with few-shot prompt grounding (`temperature: 0.1`) to eliminate hallucinations.
   - **Tier 3 (Automated Human Escalation)**: Automatically routes out-of-scope, refund, or low-similarity inquiries to the human support queue (`/escalations`) with webhook dispatch.
2. **In-Memory Query Response Cache**:
   - Normalized LRU cache returning instant zero-cost responses for repeated inquiries.
3. **Real-Time WebSockets & Interactive Web UI**:
   - Modern Jinja2 + Tailwind CSS interface with bidirectional WebSockets (`/ws/chat`), instant prompt chips, live typing indicators, and collapsible RAG source citations.
4. **Real-Time Operational Metrics Dashboard (`/dashboard`)**:
   - Tracks total queries, cache hit rate %, token consumption, estimated USD costs, and human escalation rates.
5. **Developer Experience (Docker with Hot Live-Reload)**:
   - Volume bind-mounted Docker Compose setup so code changes take effect immediately without rebuilding containers.

---

## 🏗️ System Architecture Flow

```
                                  +---------------------------------------+
                                  |            Inquiry Channels           |
                                  | (Tailwind UI / WebSocket / REST API)  |
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
                    |  | STEP 3: Tier 2 - Vector RAG Engine (Cosine Similarity)      |  |
                    |  | -> 01_courses_and_pricing.md                                |  |
                    |  | -> 02_schedules_and_modalities.md                           |  |
                    |  | -> 03_enrollment_and_certifications.md                      |  |
                    |  | -> Check SIMILARITY_THRESHOLD (0.65)                        |  |
                    |  +------------------------------+------------------------------+  |
                    |                                 | Similarity >= 0.65              |
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
│   │   ├── vector_store.py                   # Vector embeddings, indexing & cosine similarity retrieval
│   │   ├── deterministic_service.py          # Tier 1 deterministic pattern & FAQ rule matcher
│   │   ├── ai_service.py                     # Google Gemini API & OpenAI provider integration
│   │   ├── cache_service.py                  # In-memory query response cache (cost & latency optimizer)
│   │   ├── metrics_service.py                # Analytics: query counts, token cost estimation, escalation rate
│   │   └── escalation_service.py             # Human escalation dispatcher & ticket queue manager
│   ├── prompts/
│   │   └── system_prompt.py                  # Grounding instructions, brand persona & 3+ few-shot examples
│   ├── tools/
│   │   └── custom_tools.py                   # Custom skills (Course quoter & CEFR level placement advisor)
│   ├── routers/
│   │   ├── chat.py                           # REST & WebSocket endpoints (/api/chat, /ws/chat, /api/webhook)
│   │   ├── metrics.py                        # Analytics endpoints (/api/metrics, /api/cache/clear)
│   │   └── views.py                          # Jinja2 + Tailwind frontend views (Chat, Dashboard, Escalations)
│   └── main.py                               # FastAPI application setup, static mounting & lifespan startup
├── templates/
│   ├── base.html                             # Tailwind CSS base layout & navigation bar
│   ├── chat.html                             # Interactive Web Chat customer interface with live streaming
│   ├── dashboard.html                        # Real-time Metrics & Knowledge Base Explorer
│   └── escalation_queue.html                 # Human Agent Escalation Management Panel
├── static/
│   ├── css/
│   │   └── custom.css                        # Supplementary custom styling & animations
│   └── js/
│       ├── chat.js                           # Asynchronous REST & WebSocket chat client logic
│       └── dashboard.js                      # Real-time metrics auto-refresh logic
├── scripts/
│   ├── ingest.py                             # Standalone script to populate & verify vector index
│   ├── test_pipeline.py                      # Automated end-to-end unit & integration verification
│   └── package_deliverable.py                # Automated packaging to create final .zip bundle
├── requirements.txt                          # Python dependencies
├── .env.example                              # Comprehensive environment variables template
├── Dockerfile                                # Container definition with hot-reload support
├── docker-compose.yml                        # Docker Compose setup with volume bind mounts
└── README.md                                 # Complete documentation
```

---

## 🚀 Quickstart Guide

### Option 1: Local Execution with Python 3.11+

1. **Clone or Navigate to the Project**:
   ```bash
   cd prueba-IA
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` and insert your `GEMINI_API_KEY` (or `OPENAI_API_KEY`). Note: The app also includes an offline fallback synthesizer if no API key is provided.*

5. **Run Knowledge Base Ingestion**:
   ```bash
   python scripts/ingest.py
   ```

6. **Start the FastAPI Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Open Your Browser**:
   - 💬 **Interactive Chat**: [http://localhost:8000/chat](http://localhost:8000/chat)
   - 📊 **Metrics & Knowledge Base**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
   - 🚨 **Human Escalation Desk**: [http://localhost:8000/escalations](http://localhost:8000/escalations)
   - 📚 **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Run with Docker Compose (Auto Live-Reload)

The container uses volume bind-mounts (`.:/app`) so any edits in Python files, Jinja2 templates, or Markdown documents update live without rebuilding the container.

1. **Launch Container**:
   ```bash
   docker compose up --build
   ```

2. **Access Web Application**:
   Open [http://localhost:8000](http://localhost:8000)

3. **Stop Container**:
   ```bash
   docker compose down
   ```

---

## 📡 API & Multi-Channel Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat` | Standard JSON REST endpoint for student inquiries. |
| `WS` | `/ws/chat` | Real-time bidirectional WebSocket chat with status badges. |
| `POST` | `/api/webhook` | Generic multi-channel webhook endpoint (Telegram/CRM compatible). |
| `GET` | `/api/metrics` | Returns real-time metrics (query volume, token costs, cache savings). |
| `POST` | `/api/cache/clear` | Flushes all in-memory query response cache entries. |
| `GET` | `/api/health` | Health check reporting vector store index status. |

### Sample cURL Request (`POST /api/chat`):
```bash
curl -X POST "http://localhost:8000/api/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What are the Saturday intensive class schedules?", "channel": "api"}'
```

### Sample JSON Response:
```json
{
  "answer": "Our Saturday Intensive Track runs from 8:00 AM to 1:00 PM (5 continuous hours with a 20-minute break). You complete 60 class hours in 12 consecutive Saturdays. Tuition is $1,350,000 COP (~$345 USD).",
  "tier": "deterministic",
  "confidence": 1.0,
  "sources": [
    "02_schedules_and_modalities.md#1-class-schedules-and-timetables"
  ],
  "escalate_to_human": false,
  "escalation_reason": null,
  "ticket_id": null,
  "cached": false,
  "latency_ms": 1.45
}
```

---

## 🧪 Automated Testing & Verification

Run the comprehensive end-to-end test suite:
```bash
python scripts/test_pipeline.py
```
This tests:
1. **Tier 1**: Deterministic rule matcher execution and response accuracy.
2. **Cache**: Sub-millisecond response and zero-token consumption on repeated queries.
3. **Tier 2**: Vector similarity search and RAG grounding.
4. **Tier 3**: Automatic ticket generation and human escalation on complex/unanswerable queries.
5. **Custom Skills**: Tuition quote calculation and CEFR level placement advisor.
6. **Observability**: Metrics calculation and cost estimation accuracy.

---

## 📦 Packaging Deliverable Bundle

To generate the final `.zip` file for submission:
```bash
python scripts/package_deliverable.py
```
This creates `customer_support_rag_assistant.zip` excluding virtual environments, cache, and sensitive `.env` files.
