# 🎓 Global Language Academy - Intelligent Customer Support & Academic Advising Assistant

> ### 🚀 **Live Production Deployment & Repository**
> - **Public Live URL:** [https://prueba-ia-production.up.railway.app/](https://prueba-ia-production.up.railway.app/)
> - **GitHub Repository:** [https://github.com/dypokkk/prueba-IA](https://github.com/dypokkk/prueba-IA)
> 
> | Service / View | URL | Description |
> | :--- | :--- | :--- |
> | 📦 **Source Code** | [https://github.com/dypokkk/prueba-IA](https://github.com/dypokkk/prueba-IA) | Official GitHub repository |
> | 🌐 **Landing Page & Student Chat** | [https://prueba-ia-production.up.railway.app/](https://prueba-ia-production.up.railway.app/) | Main portal with interactive Glassmorphic floating modal chat |
> | 💬 **Full-Screen Chat Interface** | [https://prueba-ia-production.up.railway.app/chat](https://prueba-ia-production.up.railway.app/chat) | Dedicated distraction-free conversational view |
> | ⚡ **Admin Escalation Dashboard** | [https://prueba-ia-production.up.railway.app/dashboard](https://prueba-ia-production.up.railway.app/dashboard) | Real-time ticket management, 2-way WebSocket console & metrics |
> | 📖 **Interactive Swagger API Docs** | [https://prueba-ia-production.up.railway.app/docs](https://prueba-ia-production.up.railway.app/docs) | OpenAPI specification with live testing tools & endpoints |
> | 🩺 **System Health & Metrics** | [https://prueba-ia-production.up.railway.app/health](https://prueba-ia-production.up.railway.app/health) | System uptime, latency, and index health verification |

---

A production-grade, highly cost-efficient, and grounded Customer Support & Academic Advising System engineered for **Global Language Academy** (*Academia de Idiomas*).

Built with **Python 3, FastAPI, Jinja2, Tailwind CSS (Glassmorphism Design System), Google Gemini 2.0 Flash Lite, SQLite Persistent Multi-Turn Session Memory, WebSockets, Resend Transactional Email API, Telegram Bot Integration, and Docker with Hot Live-Reload**.

---

## 🌟 Key Architectural Features

```
                                  +---------------------------------------+
                                  |            Inquiry Channels           |
                                  | (Landing Modal / WebSocket / Telegram)|
                                  +-------------------+-------------------+
                                                      |
                                                      v
                     +-------------------------------------------------------------------+
                     |                      FastAPI Python Backend                       |
                     |                                                                   |
                     |  +-------------------------------------------------------------+  |
                     |  | STEP 0: Multi-Turn Session Memory (SessionService)          |  |
                     |  | -> Resolves follow-ups, pronouns & anaphoric queries        |  |
                     |  +------------------------------+------------------------------+  |
                     |                                 | Context-Enriched Query          |
                     |                                 v                                 |
                     |  +-------------------------------------------------------------+  |
                     |  | STEP 1: Query Cache Layer (In-memory normalized LRU)        |  |
                     |  | -> Hit: Return response (<2ms, $0.00 cost)                  |  |
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
                     |  | STEP 3: Tier 2 - BM25 & Semantic Multilingual Retrieval    |  |
                     |  | -> 01_courses_and_pricing.md                                |  |
                     |  | -> 02_schedules_and_modalities.md                           |  |
                     |  | -> 03_enrollment_and_certifications.md                      |  |
                     |  | -> 04_student_faq_and_academic_policies.md                  |  |
                     |  +------------------------------+------------------------------+  |
                     |                                 | Top 6 Context Chunks (1500 chars)|
                     |                                 v                                 |
                     |  +-------------------------------------------------------------+  |
                     |  | STEP 4: Google Gemini 3.5 Flash Lite (Grounding & Synthesis)|  |
                     |  +------------------------------+------------------------------+  |
                     |                                 | If Out-of-Scope / Dispute       |
                     |                                 v                                 |
                     |  +-------------------------------------------------------------+  |
                     |  | STEP 5: Tier 3 - Support Escalation Queue (/dashboard)     |  |
                     |  +-------------------------------------------------------------+  |
                     |                                                                   |
                     |  +-------------------------------------------------------------+  |
                     |  | STEP 6: Real-Time Observability & Token Metrics Tracker     |  |
                     |  +-------------------------------------------------------------+  |
                     +-------------------------------------------------------------------+
```

---

## 🚀 Core Capabilities

1. **Tiered Hybrid Routing Architecture**:
   - **Tier 1 (Deterministic Engine)**: Lightning-fast pattern matcher (<2ms, \$0.00 token cost) for canonical queries (tuition matrix, payment channels, schedules, placement test guidelines, campus addresses).
   - **Tier 2 (Multi-Turn Vector RAG)**: BM25 hybrid ranking over 53 rich chunks across 4 official English documents with Spanish-to-English semantic query expansion + **Google Gemini 3.5 Flash Lite** (`temperature: 0.1`) with few-shot prompt grounding to prevent hallucinations.
   - **Tier 3 (Automated Human Escalation)**: Automatically creates a trackable support ticket (`TKT-XXXXXX`) for billing disputes, custom scholarships, or out-of-scope requests, routing them to the staff desk.

2. **In-Memory Multi-Turn Conversation Memory (`SessionService`)**:
   - Maintains sliding conversational context windows per user session (`session_id`).
   - Seamlessly resolves follow-up queries (e.g. *"¿Y los horarios?"*, *"¿Puedo pagarlo a cuotas?"*, *"¿Dónde queda en Medellín?"*) without requiring the user to repeat the language or modality.

3. **Public Landing Page with Varied Visual Rhythm (`/`)**:
   - **Cinematic Spotlight Hero**: Grand typography, floating status pill, and instant language exploration bar (🇬🇧 Inglés, 🇫🇷 Francés, 🇩🇪 Alemán, 🇮🇹 Italiano, 🇧🇷 Portugués, 🇨🇴 Español).
   - **3-Step Methodology Storytelling**: 80% oral immersion, CELTA/DELTA faculty, and unlimited conversation clubs.
   - **Bento Grid Program Catalog**: Modular showcase of languages, certifications (IELTS, TOEFL, DELF, Goethe), and VIP 1-on-1 packages.
   - **Comparative Pricing Matrix**: Highlighted Monthly Intensive ($1,450,000 COP), Standard Quarterly ($1,250,000 COP), Saturday Intensive ($1,350,000 COP), and 0% interest financing details.
   - **Dual Campus & Placement Test Feature**: Flagship campus details in Bogotá Chapinero and Medellín El Poblado alongside the Free Placement Test callout.
   - **Clean FAQ Accordion**: Instant answers to common student inquiries.

4. **Floating Action Button (FAB) & Glassmorphic Chat Modal**:
   - Glowing bottom-right button with live pulse animation.
   - Opens a frosted glass modal widget on any page with markdown rendering, prompt chips, and multi-turn memory.

5. **Secluded Unified Admin Dashboard (`/dashboard`)**:
   - **Real-Time Analytics & Observability**: Total queries, cache savings in USD, token consumption, Gemini cost estimation, and escalation rate.
   - **Support Escalation Queue**: Ticket management desk with one-click resolution.
   - **Knowledge Base Inspector**: Tabbed viewer for all 4 indexed Markdown documents.

6. **Telegram Bot Integration**:
   - Fully interactive 24/7 Telegram assistant supporting persistent per-chat session memory (`tg_{chat_id}`), welcome menus, `/start`, `/help`, and `/clear` commands.

---

## 📁 Repository Structure

```
prueba-IA/
├── data/
│   ├── 01_courses_and_pricing.md             # Document 1: Tuition matrix, language tracks, discounts, payment channels
│   ├── 02_schedules_and_modalities.md        # Document 2: Morning/evening/Saturday schedules, Bogotá & Medellín campuses
│   ├── 03_enrollment_and_certifications.md   # Document 3: Free placement diagnostic test, CEFR levels, IELTS/TOEFL/Cambridge
│   ├── 04_student_faq_and_academic_policies.md # Document 4: Communicative methodology, faculty credentials, grading criteria
│   ├── vector_store.json                     # Persistent 53-chunk vector embeddings and BM25 index
│   └── escalation_tickets.json               # Persisted human escalation ticket queue
├── app/
│   ├── config.py                             # Settings, environment variables (.env loading)
│   ├── services/
│   │   ├── session_service.py                # Multi-turn conversation context & session memory manager
│   │   ├── document_loader.py                # Markdown chunking (1500 chars, 250 overlap) with metadata
│   │   ├── vector_store.py                   # BM25 & multilingual Spanish-to-English query expansion
│   │   ├── deterministic_service.py          # Tier 1 deterministic pattern & intent matcher (<2ms)
│   │   ├── ai_service.py                     # Google Gemini 3.5 Flash Lite API & cascade failover
│   │   ├── telegram_service.py               # Telegram Bot polling runner & dispatcher
│   │   ├── cache_service.py                  # In-memory query response cache
│   │   ├── metrics_service.py                # Real-time token usage, USD cost & escalation metrics
│   │   └── escalation_service.py             # Human escalation ticket dispatcher & queue manager
│   ├── prompts/
│   │   └── system_prompt.py                  # Grounding instructions, brand persona & few-shot examples
│   ├── routers/
│   │   ├── views.py                          # Jinja2 views (/, /chat, /dashboard)
│   │   ├── chat.py                           # REST & WebSocket endpoints (/api/chat, /ws/chat, /api/chat/clear)
│   │   ├── metrics.py                        # Analytics endpoints (/api/metrics, /api/cache/clear)
│   │   └── telegram.py                       # Telegram webhook endpoint (/api/telegram/webhook)
│   └── main.py                               # FastAPI application factory & lifecycle management
├── templates/
│   ├── base.html                             # Glassmorphism header, floating FAB & chat modal container
│   ├── landing.html                          # High-converting dynamic landing page
│   ├── chat.html                             # Standalone full-screen chat interface
│   └── dashboard.html                        # Unified admin dashboard (Metrics, Tickets & Docs)
├── static/
│   ├── css/custom.css                        # Glassmorphism design system, floating ambient orbs & animations
│   └── js/
│       ├── chat.js                           # Floating modal controller, WebSocket client & Markdown renderer
│       └── dashboard.js                      # Live metrics polling & document tab switcher
├── tests/
│   └── test_rag_pipeline.py                  # Comprehensive unit test suite (16 test cases)
├── scripts/
│   ├── ingest.py                             # Offline knowledge base ingestion & indexing pipeline
│   ├── telegram_bot.py                       # Standalone Telegram long-polling runner
│   └── package_deliverable.py                # ZIP packaging utility
├── Dockerfile                                # Optimized multi-stage Python 3.11 container
├── docker-compose.yml                        # Docker Compose setup with volume bind mounts & hot-reload
├── requirements.txt                          # Python dependencies
└── .env.example                              # Environment configuration template
```

---

## ⚙️ Quick Start Guide

### 1. Clone Repository & Prerequisites
```bash
git clone https://github.com/dypokkk/prueba-IA.git
cd prueba-IA
```
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/) installed.
- Google Gemini API Key (or OpenAI API Key).

### 2. Environment Configuration
Create a `.env` file in the root directory (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```ini
APP_NAME=Global Language Academy Support Assistant
PORT=8000
HOST=0.0.0.0
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
TEMPERATURE=0.1
TOP_K_CHUNKS=6
ENABLE_DETERMINISTIC_TIER=true

# Optional: Telegram Bot Integration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

### 3. Run with Docker Compose (Live Hot-Reload)
Start the service in detached mode:

```bash
docker compose up -d --build
```

The application will start with **live hot-reload** enabled via Uvicorn. Any code edits on your host machine will immediately reflect in the container.

---

## 🌐 Web Endpoints & User Interface

| Route | Description | Target Audience |
| :--- | :--- | :--- |
| **`http://localhost:8000/`** | **Informative Landing Page**: Hero, Bento Catalog, Pricing Matrix, Campuses, Placement Test CTA & Floating Chat Modal. | Students & Public |
| **`http://localhost:8000/chat`** | **Standalone Full-Screen Chat**: Dedicated full-page interactive chat interface. | Students / Direct Link |
| **`http://localhost:8000/dashboard`** | **Unified Admin Panel**: Real-time Token Observability, Support Escalation Queue & Knowledge Base Inspector. | Staff & Administrators |
| **`http://localhost:8000/docs`** | **Interactive OpenAPI (Swagger) Documentation**. | Developers / Integrations |

---

## 🤖 Telegram Bot Integration

The Telegram Bot is configured to run automatically as a background task inside the Docker container when `TELEGRAM_BOT_TOKEN` is present in `.env`.

### Bot Commands:
- `/start` - Displays the official welcome message and capabilities menu.
- `/help` - Displays the help guide and command shortcuts.
- `/clear` - Resets conversation memory and flushes local query cache.
- *Any natural text* - Seamlessly answered by the Tiered RAG pipeline with persistent session memory (`tg_{chat_id}`).

---

## 🧪 Testing & Verification

Run the automated test suite covering all tiers, cache layer, metrics, and deterministic rules:

```bash
# Sandboxed / Host execution
python3 -m unittest discover tests

# Or inside the Docker container
docker exec global_language_academy_assistant python3 -m unittest discover tests
```

### Re-indexing the Knowledge Base
If you edit or add Markdown files in `data/`, run the ingestion script:

```bash
docker exec global_language_academy_assistant python3 scripts/ingest.py
```

---

## 📊 Live Observability & Cost Economics

- **Deterministic Tier**: Intercepts common inquiries in **$<2\text{ms}$** at **\$0.00 token cost**.
- **Gemini 3.5 Flash Lite Tier**: Synthesizes complex and multi-part queries in **$\approx 1.5 - 2.5\text{s}$** with prompt caching efficiency.
- **Estimated Savings**: In-memory caching and Tier 1 pattern matching save thousands of tokens per hundred requests, tracked in real-time in `/dashboard`.

---

## 📄 License
Developed for Global Language Academy. All rights reserved.
