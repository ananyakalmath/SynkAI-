# SynkAI - Agentic AI Meeting Assistant

**Repository**: `synkai-meeting-assistant`  
**Description**: Agentic AI Meeting Assistant powered by LangGraph, RAG, Ollama, and ChromaDB.

> **Sprint 1 Notice**: Only core project foundation, FastAPI server, Streamlit UI shell, environment configuration, structured logging, health endpoints, and UI placeholders are initialized. AI agent logic, LangGraph graphs, RAG services, ChromaDB vector databases, and Ollama integration will be implemented in subsequent sprints.

---

## 📂 Project Architecture

```text
synkai-meeting-assistant/
│
├── backend/
│   ├── agents/          # Modular AI Agent definitions (Sprint 2+)
│   ├── graph/           # LangGraph state machine workflows (Sprint 2+)
│   ├── services/        # Business logic, RAG, & ChromaDB services (Sprint 2+)
│   ├── models/          # Pydantic data schemas & response models
│   ├── prompts/         # LLM system prompts & template strings (Sprint 2+)
│   ├── routes/          # API route handlers (GET /health)
│   ├── utils/           # Helper utilities (Structured Logging)
│   │   └── logger.py
│   ├── config.py        # Environment settings (Pydantic BaseSettings)
│   └── main.py          # FastAPI application entry point
│
├── frontend/
│   ├── Home.py          # Streamlit UI main dashboard
│   ├── pages/           # Multi-page views (Sprint 2+)
│   └── components/     # Modular UI components (Sprint 2+)
│
├── uploads/             # Meeting audio & transcript upload directory
├── chroma_db/           # Local persistent ChromaDB vector store
├── data/                # Meeting metadata & local document storage
├── tests/
│   └── test_health.py   # Automated Pytest suite
│
├── .env.example         # Environment template
├── .env                 # Environment configuration
├── .gitignore           # Version control ignores
├── requirements.txt     # Python dependencies
└── README.md            # Documentation & setup instructions
```

---

## 🛠️ Tech Stack (Sprint 1)

- **Language**: Python 3.10+
- **Backend**: FastAPI, Uvicorn
- **Frontend**: Streamlit
- **Configuration & Validation**: Pydantic v2, Pydantic Settings, `python-dotenv`
- **Testing**: Pytest, HTTPX

---

## 🚀 Local Setup & Running Instructions

### 1. Repository Navigation & Virtual Environment

Navigate to the project directory:

```bash
cd /Users/ananyakalmath/.gemini/antigravity/scratch/synkai-meeting-assistant
```

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

Install required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Default configuration in `.env`:
```env
APP_NAME=SynkAI
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
BACKEND_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:8501", "http://127.0.0.1:8501"]
```

---

## 🏃 Running the Application

### Option A: Launch Backend (FastAPI)

Run Uvicorn server from the project root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health Endpoint**: `GET http://localhost:8000/health`  
  Response: `{"status": "ok"}`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

### Option B: Launch Frontend (Streamlit)

In a separate terminal (with virtual environment activated):

```bash
streamlit run frontend/Home.py
```

- **Streamlit App URL**: `http://localhost:8501`

---

## 🧪 Running Automated Tests

Run Pytest to verify health routes and server setup:

```bash
pytest tests/
```
