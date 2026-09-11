# SynkAI - Agentic AI Meeting Assistant

**Repository**: `synkai-meeting-assistant`  
**Description**: Agentic AI Meeting Assistant powered by LangGraph, RAG, Ollama, and ChromaDB.

> **Sprint 2 Status**: File upload pipeline (.txt, .pdf, .docx), FileParserService, Ollama (`qwen3`) integration, SummaryService, FastAPI endpoints (`POST /upload`, `POST /summarize`), and Streamlit UI summary rendering are active.

---

## 📂 Project Architecture

```text
synkai-meeting-assistant/
│
├── backend/
│   ├── agents/          # Modular AI Agent definitions
│   ├── graph/           # LangGraph state machine workflows
│   ├── services/        # Business logic & Ollama services
│   │   ├── file_parser.py     # TXT, PDF, & DOCX text extraction
│   │   ├── ollama_service.py  # Direct HTTP client for Ollama LLM
│   │   └── summary_service.py # Executive summary orchestration
│   ├── models/          # Pydantic schemas
│   │   ├── health.py          # GET /health response schema
│   │   ├── upload.py          # POST /upload response schema
│   │   └── summary.py         # POST /summarize request & response schemas
│   ├── prompts/         # LLM system prompts
│   ├── routes/          # API route handlers
│   │   ├── health.py          # GET /health
│   │   ├── upload.py          # POST /upload
│   │   └── summary.py         # POST /summarize
│   ├── utils/           # Helper utilities
│   │   └── logger.py          # Structured logging setup
│   ├── config.py        # Settings (Pydantic BaseSettings)
│   └── main.py          # FastAPI application entry point
│
├── frontend/
│   ├── Home.py          # Streamlit UI main dashboard
│   ├── pages/           # Multi-page views
│   └── components/     # Modular UI components
│
├── uploads/             # Meeting audio & transcript upload directory
├── chroma_db/           # Local persistent ChromaDB vector store
├── data/                # Local document storage
├── tests/               # Pytest automated test suite
│   ├── test_health.py
│   └── test_services.py
│
├── .env.example         # Environment template
├── .env                 # Environment configuration
├── .gitignore           # Version control ignores
├── requirements.txt     # Python dependencies
└── README.md            # Setup & execution instructions
```

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Backend API**: FastAPI, Uvicorn
- **Frontend Dashboard**: Streamlit
- **LLM Engine**: Ollama (`qwen3` model)
- **Document Extractors**: `pypdf`, `python-docx`
- **Configuration**: Pydantic v2, Pydantic Settings, `python-dotenv`
- **Testing**: Pytest, HTTPX

---

## 🚀 Local Setup & Running Instructions

### 1. Virtual Environment & Dependencies

Navigate to the project root:

```bash
cd /Users/ananyakalmath/.gemini/antigravity/scratch/synkai-meeting-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Ensure Ollama is Installed & Running

Install Ollama from [ollama.com](https://ollama.com) and pull the `qwen3` model:

```bash
ollama pull qwen3
ollama serve
```

*Note: By default, SynkAI expects Ollama at `http://localhost:11434`.*

---

## 🏃 Running the Application

### Option A: Launch FastAPI Backend

Run Uvicorn server from project root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health Endpoint**: `GET http://localhost:8000/health`
- **Upload Endpoint**: `POST http://localhost:8000/upload`
- **Summarize Endpoint**: `POST http://localhost:8000/summarize`
- **Swagger Documentation**: `http://localhost:8000/docs`

### Option B: Launch Streamlit Frontend

In a second terminal:

```bash
cd /Users/ananyakalmath/.gemini/antigravity/scratch/synkai-meeting-assistant
source venv/bin/activate
streamlit run frontend/Home.py
```

- **Streamlit App URL**: `http://localhost:8501`

---

## 🧠 Sprint 4: Multi-Agent Meeting Intelligence

`POST /meeting/analyze` runs a LangGraph workflow over a transcript and returns structured
meeting intelligence. Accepts either `document_id` (a transcript already indexed through
`POST /chat/upload`) or raw `transcript_text`.

```bash
curl -X POST http://localhost:8000/meeting/analyze \
  -H 'Content-Type: application/json' \
  -d '{"transcript_text": "Sarah: Mike will finish the LangGraph workflow by Wednesday."}'
```

The agents run as a **sequential chain**, one at a time:

```text
parser -> summary -> action_item -> decision -> deadline -> risk -> coordinator
```

- **Parser Agent** normalizes the transcript deterministically in Python (no LLM call).
- The five extraction agents each make exactly one `qwen3` call.
- **Coordinator Agent** assembles the validated response.

A failing agent is reported, never hidden: the response carries `analysis_complete: false`
and an `agent_errors` list. If the parser fails, or every extraction agent fails, the
endpoint returns HTTP 500 instead of an empty-looking success.

### Local Ollama throughput settings

Local Ollama serves one generation at a time, so these settings (see `.env`) keep the
workflow within what the machine can actually do:

| Setting | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_MAX_CONCURRENCY` | `1` | In-flight Ollama requests allowed per process (LLM + embeddings share the limit) |
| `OLLAMA_QUEUE_TIMEOUT` | `600` | Max seconds a caller waits for a free inference slot |
| `OLLAMA_TIMEOUT` | `120` | **Stall** timeout: max seconds without a streamed token |
| `OLLAMA_MAX_DURATION` | `900` | Hard wall-clock cap for a single generation |
| `OLLAMA_KEEP_ALIVE` | `10m` | Keeps the LLM resident across agents (no reload per agent) |
| `OLLAMA_EMBED_KEEP_ALIVE` | `60s` | Frees embedding-model memory for the LLM |
| `OLLAMA_ENABLE_THINKING` | `False` | qwen3 thinking mode measured ~16x slower for no gain here |
| `OLLAMA_NUM_PREDICT` | `768` | Cap on generated tokens per call |

On a memory-constrained machine (e.g. 8 GB RAM, where `qwen3:8b` barely fits and swaps),
the whole analysis can take several minutes. Point `OLLAMA_MODEL` at a smaller model
(`qwen3:1.7b`, `qwen2.5:7b-instruct`) for faster runs.

---

## 🧪 Running Automated Tests

Run Pytest to verify health routes, file parser service, upload endpoints, the RAG
pipeline, and the multi-agent workflow:

```bash
PYTHONPATH=. pytest tests/
```
