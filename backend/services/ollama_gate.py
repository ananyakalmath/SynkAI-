"""
Ollama Concurrency Gate for SynkAI.

A local Ollama server running an 8B model on a laptop can realistically serve only one
generation at a time. When several callers (the LangGraph agents, /summarize and the RAG
chat) hit `/api/generate` simultaneously, Ollama queues or time-slices them, every request
slows down proportionally, and the HTTP read timeout fires even though the server is healthy.

This module exposes a single process-wide gate that all Ollama callers (LLM generation and
embeddings) pass through, so at most `OLLAMA_MAX_CONCURRENCY` requests are ever in flight.
Waiting for a slot happens *before* the HTTP request is issued, so queueing never eats into
the per-request read timeout.
"""

import threading
from contextlib import contextmanager
from typing import Iterator, Optional

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaBusyError(RuntimeError):
    """Raised when no Ollama slot became available within the configured queue timeout."""


class OllamaGate:
    """
    Bounded-concurrency gate around the local Ollama server.
    """

    def __init__(self, max_concurrency: Optional[int] = None, queue_timeout: Optional[int] = None):
        if max_concurrency is None:
            max_concurrency = settings.OLLAMA_MAX_CONCURRENCY
        if queue_timeout is None:
            queue_timeout = settings.OLLAMA_QUEUE_TIMEOUT

        self.max_concurrency = max(1, max_concurrency)
        self.queue_timeout = max(0, queue_timeout)
        self._semaphore = threading.BoundedSemaphore(self.max_concurrency)

    @contextmanager
    def slot(self, label: str = "ollama-request") -> Iterator[None]:
        """
        Acquires an execution slot for the duration of the context.

        Args:
            label (str): Human-readable name of the caller, used in logs.

        Raises:
            OllamaBusyError: If no slot frees up within the queue timeout.
        """
        acquired = self._semaphore.acquire(timeout=self.queue_timeout)
        if not acquired:
            message = (
                f"Ollama is busy: '{label}' waited {self.queue_timeout}s without getting one of the "
                f"{self.max_concurrency} available inference slot(s). Retry once current work finishes."
            )
            logger.error(message)
            raise OllamaBusyError(message)

        logger.debug(f"Ollama slot acquired by '{label}'.")
        try:
            yield
        finally:
            self._semaphore.release()
            logger.debug(f"Ollama slot released by '{label}'.")


# Process-wide gate shared by OllamaService (generation) and VectorService (embeddings).
ollama_gate = OllamaGate()
