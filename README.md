# Multi-Agentic AI for Business Intelligence

> An AI-powered business intelligence platform where specialized agents collaborate to analyze your data, generate insights, and deliver professional reports — all from a single natural language query.

🔗 **Live Demo**: [multi-agentic-ai-for-business-intelligence](https://multi-agentic-ai-for-business-intelligence-hb85fwc0a.vercel.app/)

![Dashboard Demo](dashboard.jpg)
---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS 4, Lucide Icons |
| **Backend** | FastAPI, Python 3.12, Pandas, NumPy, SciPy |
| **AI / LLM** | Groq API — multi-model (GPT-OSS-120B, Qwen3-32B, Kimi-K2, Llama-3.3-70B, Llama-3.1-8B) |
| **Visualization** | Matplotlib, Seaborn |
| **Reporting** | ReportLab (PDF generation) |
| **Logging & Monitoring** | Supabase (PostgreSQL) — structured agent logs with session tracking |
| **Deployment** | Render (backend), Vercel (frontend), Docker |

---

## Architecture Overview

```
User Query (Natural Language)
        │
        ▼
┌─────────────────────┐
│  Orchestrator Agent  │ ← LLM intent detection + keyword fallback
│  (kimi-k2-instruct)  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Data Ingestion      │ ← CSV upload / REST API (JSON/XML/CSV) / Demo datasets
│  Agent               │   + auto-cleaning + data quality validation
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Column Mapper       │ ← Fuzzy synonym matching for arbitrary column names
│                      │   Falls back to General Analysis if no match
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Specialist Agent    │ ← One of: Analysis / Pricing / Churn / Forecasting
│  (domain-specific)   │   All math done by pandas/numpy — LLM only narrates
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Hallucination Guard │ ← Cross-references LLM numbers against computed data
│                      │   Flags ungrounded claims with disclaimers
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Output Agent        │ ← Text / Charts / PDF — ZERO LLM calls (reuses insights)
│  (no LLM)            │
└────────┬────────────┘
         │
         ▼
   SSE Stream → Frontend (real-time agent trace)
         │
         ▼
   Supabase Logging (every event persisted with session ID)
```

---

## Agent Architecture

| Agent | Responsibility | Default Model | Input | Output |
|-------|---------------|--------------|-------|--------|
| **Orchestrator** | Intent detection, pipeline routing | `kimi-k2-instruct` | Query + config | Task plan + SSE events |
| **Data Ingestion** | Load & validate data | — (no LLM) | File/URL/demo name | DataFrame + quality report |
| **Column Mapper** | Fuzzy-match columns to specialist schemas | — (no LLM) | DataFrame + intent | Renamed DataFrame / fallback |
| **General Analysis** | Stats, correlations, anomalies | `llama-3.1-8b` | DataFrame + query | Insights + analysis dict |
| **Dynamic Pricing** | Elasticity, margins, discounts | `qwen3-32b` | DataFrame + query | Pricing analysis + recommendations |
| **Employee Churn** | Churn rates, risk flags, cost | `gpt-oss-120b` | DataFrame + query | Churn analysis + risk flags |
| **Demand Forecasting** | Trends, seasonality, stockout | `qwen3-32b` | DataFrame + query | Forecast data + insights |
| **Hallucination Guard** | Validate LLM output vs computed data | — (no LLM) | Insights + analysis dict | Grounded insights |
| **Output** | Render text/charts/PDF | — (no LLM) | Insights + data + format | Final output |

---

## Key Features

### 🧠 Multi-Agent Intelligence
- 5 specialized AI agents, each with a purpose-selected LLM
- Automatic intent detection (LLM + keyword fallback)
- Graceful cascading fallback — if a specialist fails, General Analysis takes over

### 🔄 Smart Column Mapping
- Fuzzy synonym matching maps arbitrary column names to expected schemas
- `unit_price` → `price`, `qty_sold` → `units_sold`, `dept` → `department`, etc.
- If columns don't match any specialist, automatically falls back to General Analysis
- Any CSV or REST API data produces meaningful results

### 🛡️ Hallucination Prevention
- **All calculations are deterministic** — done by pandas, numpy, scipy
- **LLM only narrates** pre-computed results, never does math
- **Hallucination guard** cross-references every number in LLM output against computed data
- Ungrounded claims (numbers not found in analysis) are flagged with disclaimers
- Grounding score logged for every request

### 📊 Multi-Format Data Ingestion
- **CSV/Excel upload** — auto-detects format, handles tab-separated
- **REST API** — supports JSON (flat + nested), XML, CSV/TSV responses
- **Nested JSON flattening** — `{"user": {"name": "X"}}` → `user_name` column
- **Auto-cleaning** — strips headers, drops empty rows, coerces numeric strings
- **Data quality validation** — warns about nulls, duplicates, zero-variance columns

### 📈 Logging & Monitoring (Supabase)
- Every agent event logged with session ID, timestamps, and structured metadata
- Batched async writes — zero impact on request latency
- Query traceability — search logs by session, agent, time, or error
- Grounding scores persisted for insight quality monitoring
- Works both locally (console) and in production (Supabase + console)

---

## Central Config Design

All configuration lives in `backend/config.py` — the single source of truth:
- Zero magic strings scattered across the codebase
- Changing a model or threshold requires editing exactly one file
- New agents can reference existing config values with a single import

---

## Resilient Fallback Router

The `utils/llm.py` implements cascading fallback:

1. System catches the error and logs a warning
2. Finds the failed model's position in `MODEL_FALLBACK_CHAIN`
3. Tries the next model after a 1.5s cooldown
4. Continues until a model responds or the chain is exhausted

Chain: `gpt-oss-120b` → `llama-3.3-70b` → `qwen3-32b` → `kimi-k2` → `llama-3.1-8b`

Additionally, `<think>...</think>` reasoning blocks from models like Qwen3 are automatically stripped.

---

## Directory Structure

```
Multi-Agentic AI for Business Intelligence/
├── backend/
│   ├── main.py                      # FastAPI app + routes + Supabase logging init
│   ├── config.py                    # Central config (single source of truth)
│   ├── agents/
│   │   ├── orchestrator.py          # Query routing + column mapping + pipeline
│   │   ├── ingestion.py             # CSV / REST (JSON/XML/CSV) / demo loading
│   │   ├── analysis.py              # General statistical analysis
│   │   ├── pricing.py               # Dynamic pricing agent
│   │   ├── churn.py                 # Employee churn agent
│   │   ├── forecasting.py           # Demand forecasting agent
│   │   └── output.py                # Text / Charts / PDF rendering (no LLM)
│   ├── utils/
│   │   ├── llm.py                   # Groq client + fallback chain + think-stripping
│   │   ├── demo_data.py             # 6 seeded demo datasets
│   │   ├── column_mapper.py         # Fuzzy column matching + viability checks
│   │   ├── validators.py            # Output validation + hallucination grounding
│   │   ├── hallucination_guard.py   # Number extraction + cross-referencing
│   │   └── supabase_logger.py       # Batched async Supabase logging handler
│   ├── outputs/                     # Generated PDF reports
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # Root layout + navbar
│   │   ├── page.tsx                 # Landing page
│   │   ├── demo/page.tsx            # Interactive demo
│   │   └── docs/page.tsx            # Documentation
│   ├── components/
│   │   ├── landing/                 # Hero, Features, HowItWorks, AgentShowcase, Footer
│   │   └── demo/                    # DataSourcePanel, QueryPanel, AgentTrace, OutputPanel
│   ├── lib/
│   │   ├── api.ts                   # API client + SSE parser
│   │   └── types.ts                 # TypeScript interfaces
│   └── .env.example
├── Dockerfile
├── .gitignore
└── README.md
```

---

## Local Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Add GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local  # Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | ✅ | Groq API key for LLM calls |
| `SUPABASE_URL` | Optional | Supabase project URL for logging |
| `SUPABASE_KEY` | Optional | Supabase anon/service key for logging |

### Frontend (`frontend/.env.local`)

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL |

> **Note:** Supabase logging is optional. If `SUPABASE_URL`/`SUPABASE_KEY` are not set, logging falls back to console only — the app works fine without it.

---

## Deployment

### Backend → Render

1. Create a **Web Service** on Render
2. Connect your GitHub repo, set **Root Directory** to `backend`
3. **Build**: `pip install -r requirements.txt`
4. **Start**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`

### Frontend → Vercel

1. Import repo, set **Root Directory** to `frontend`
2. Add env var: `NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com`

### Supabase Logging Setup

1. Create a Supabase project
2. Run the `agent_logs` table SQL in the SQL Editor (see docs)
3. Copy the project URL and anon key to your backend `.env`

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Pure Python agents** over LangChain/CrewAI | Minimal dependencies, full control, easier debugging |
| **Central `config.py`** | Single source of truth prevents config drift |
| **SSE streaming** over polling | Real-time agent progress, lower latency perception |
| **Cascading LLM fallback** | No single model failure crashes the system |
| **Strict token economy** | Output Agent reuses specialist insights — saves 40%+ API calls |
| **Deterministic calculations** | All math by pandas/numpy, LLM only narrates — prevents hallucination |
| **Hallucination guard** | Cross-references LLM numbers against computed data |
| **Fuzzy column mapping** | Any CSV/REST data works, not just demo datasets |
| **Supabase logging** | Structured, queryable, persistent logs with zero latency impact |
| **Graceful degradation** | Missing columns → General Analysis, not crashes |

---

## Author

**Sujato Dutta**  
[LinkedIn](https://www.linkedin.com/in/sujato-dutta/)

---

## License

MIT License
