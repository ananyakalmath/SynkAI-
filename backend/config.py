"""
Application configuration module using Pydantic BaseSettings.
Loads environment variables from .env file.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings schema for SynkAI backend.
    """

    APP_NAME: str = "SynkAI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_URL: str = "http://localhost:8000"
    # 5173 is the SvelteKit app (web/); 8501 (Streamlit) stays until it's retired in Phase D.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    # Ollama LLM & Embedding Models
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # Ollama local inference throughput controls.
    # A local Ollama server can only run a small number of generations at once;
    # anything beyond that queues inside Ollama and blows through the HTTP read timeout.
    # Generation is streamed, so OLLAMA_TIMEOUT is a *stall* timeout: the maximum gap
    # allowed between two tokens, not a cap on total generation time. A slow-but-alive
    # model keeps streaming; a genuinely hung server still fails fast.
    OLLAMA_TIMEOUT: int = 120                # Max seconds without any token before giving up
    OLLAMA_MAX_DURATION: int = 900           # Hard wall-clock cap (seconds) for one generation
    OLLAMA_EMBED_TIMEOUT: int = 120          # Read timeout (seconds) for a single /api/embeddings call
    OLLAMA_MAX_CONCURRENCY: int = 1          # Max simultaneous in-flight Ollama requests for this process
    OLLAMA_QUEUE_TIMEOUT: int = 600          # Max seconds a request may wait for a free Ollama slot
    OLLAMA_KEEP_ALIVE: str = "10m"           # Keep the LLM resident between agent calls (avoids reload cost)
    OLLAMA_EMBED_KEEP_ALIVE: str = "60s"     # Release the embedding model quickly so the LLM keeps the RAM
    OLLAMA_ENABLE_THINKING: bool = False     # qwen3 thinking mode is ~16x slower; off by default
    OLLAMA_NUM_PREDICT: int = 768            # Hard cap on generated tokens (runaway-generation guard)

    # ChromaDB Vector Store
    CHROMA_DB_DIR: str = "chroma_db"
    CHROMA_COLLECTION_NAME: str = "meeting_documents"

    # File Upload Configuration
    UPLOADS_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_MEDIA_UPLOAD_SIZE_MB: int = 500  # video/audio recordings are far larger than text transcripts

    # Video/Audio Transcription (faster-whisper, local — no audio leaves the machine)
    WHISPER_MODEL_SIZE: str = "base"     # tiny/base/small/medium/large-v3 — bigger is slower but more accurate
    WHISPER_DEVICE: str = "cpu"          # local-first default; set to "cuda" if a GPU is available
    WHISPER_COMPUTE_TYPE: str = "int8"   # quantized for reasonable CPU speed
    WHISPER_BEAM_SIZE: int = 5
    FFMPEG_TIMEOUT: int = 600            # seconds allowed for audio extraction from one file

    # Accounts, sessions, workspaces
    DATABASE_PATH: str = "data/synkai.db"
    SESSION_SECRET: str = ""             # used to sign short-lived OAuth CSRF state tokens
    SESSION_TTL_DAYS: int = 30
    DEFAULT_WORKSPACE_NAME: str = "Legacy Workspace"  # holds data that existed before accounts did
    INVITE_TTL_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:5173"  # base URL used to build invite links

    # Google Sign-In (OpenID Connect) — calendar.events scope is requested later, in Phase 3
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    # The SvelteKit app's own OAuth callback route receives this (see
    # web/src/routes/login/google/callback/+server.ts) — not the app's root.
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/login/google/callback"
    TOKEN_ENCRYPTION_KEY: str = ""       # Fernet key; encrypts stored Google refresh tokens (Phase 3)

    # Email login codes (no passwords — a 6-digit code emailed to the user's work address)
    EMAIL_CODE_TTL_MINUTES: int = 10
    EMAIL_CODE_RATE_LIMIT_PER_HOUR: int = 5
    EMAIL_CODE_MAX_ATTEMPTS: int = 5

    # SMTP — used for login codes now, and meeting invites/reminders from Phase 2 onward
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = "SynkAI <noreply@synkai.local>"

    # Scheduled meetings
    DEFAULT_MEETING_TIMEZONE: str = "Asia/Kolkata"
    REMINDER_CHECK_INTERVAL_SECONDS: int = 300  # how often the background loop looks for due reminders

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate singleton settings object
settings = Settings()
