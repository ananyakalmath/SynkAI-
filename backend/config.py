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
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate singleton settings object
settings = Settings()
