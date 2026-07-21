"""
Chunking Service for SynkAI.
Splits meeting transcripts into logical overlapping text chunks for RAG indexing.
"""

from typing import List, Dict, Any
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ChunkingService:
    """
    Service responsible for chunking raw text into overlapping windows.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Splits text into overlapping chunks around target size.

        Args:
            text (str): Raw transcript text.

        Returns:
            List[Dict[str, Any]]: List of chunk dictionaries containing chunk_number and text.
        """
        if not text or not text.strip():
            logger.warning("Attempted to chunk empty or whitespace text.")
            return []

        text = text.strip()
        total_len = len(text)
        chunks: List[Dict[str, Any]] = []

        start = 0
        chunk_number = 1

        while start < total_len:
            end = min(start + self.chunk_size, total_len)

            # Try to break at a sentence or line end if possible near boundary
            if end < total_len:
                boundary = text.rfind("\n", start + self.chunk_size // 2, end)
                if boundary == -1:
                    boundary = text.rfind(". ", start + self.chunk_size // 2, end)
                if boundary != -1:
                    end = boundary + (1 if text[boundary] == "\n" else 2)

            chunk_str = text[start:end].strip()
            if chunk_str:
                chunks.append({
                    "chunk_number": chunk_number,
                    "text": chunk_str,
                    "char_start": start,
                    "char_end": end
                })
                chunk_number += 1

            if end >= total_len:
                break

            start = max(start + 1, end - self.chunk_overlap)

        logger.info(f"Created {len(chunks)} chunks from transcript ({total_len} characters).")
        return chunks
