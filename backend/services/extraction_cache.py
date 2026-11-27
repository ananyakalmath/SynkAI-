"""
Extraction Cache for SynkAI.

/upload, /chat/upload, and /summarize each end up handling the same uploaded file
independently — the frontend posts a meeting to /upload and /chat/upload back-to-back,
then /summarize re-reads it by filename — and each used to re-run FileParserService on
it from scratch. For a text document that's a wasted PDF/DOCX parse; for a recorded
video or audio meeting it meant running the whole ffmpeg + Whisper transcription
pipeline up to three times for a single upload.

This module is a small process-wide cache from a file's content hash (SHA-256 of its raw
bytes, see backend.utils.uploads) to its already-extracted text, so identical bytes are
only ever parsed/transcribed once, however many endpoints see them.
"""

import threading
from typing import Dict, Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ExtractionCache:
    """
    Thread-safe, process-wide cache of extracted text keyed by file content hash.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, str] = {}

    def get(self, file_hash: str) -> Optional[str]:
        """Returns previously extracted text for `file_hash`, or None if not cached."""
        with self._lock:
            return self._store.get(file_hash)

    def set(self, file_hash: str, text: str) -> None:
        """Stores extracted text for `file_hash`."""
        with self._lock:
            self._store[file_hash] = text

    def clear(self) -> None:
        """Drops every cached entry. Mainly useful for tests."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# Process-wide cache shared by every route that extracts text from an uploaded file.
extraction_cache = ExtractionCache()
