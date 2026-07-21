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

## 🧪 Running Automated Tests

Run Pytest to verify health routes, file parser service, and upload endpoints:

```bash
pytest tests/
```
