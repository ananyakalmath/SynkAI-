"""
File Parser Service for SynkAI.
Extracts raw text content from TXT, PDF, and DOCX meeting transcript files, and from
recorded video/audio meetings via local Whisper transcription.
"""

import os
from typing import Optional
from pypdf import PdfReader
from docx import Document
from backend.config import settings
from backend.services.extraction_cache import extraction_cache
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FileParserService:
    """
    Service responsible for parsing text content from documents (.txt, .pdf, .docx) and
    from video/audio recordings, which are transcribed before any text is extracted.
    """

    DOCUMENT_EXTENSIONS = {".txt", ".pdf", ".docx"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
    AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
    MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    SUPPORTED_EXTENSIONS = DOCUMENT_EXTENSIONS | MEDIA_EXTENSIONS

    @classmethod
    def parse_file(cls, file_path: str, file_hash: Optional[str] = None) -> str:
        """
        Main entry point to parse text from a file based on its extension.

        Args:
            file_path (str): Path to the target file.
            file_hash: Optional SHA-256 hex digest of the file's content (see
                backend.utils.uploads). When provided, a previous extraction for the
                same hash is reused instead of re-parsing identical bytes — callers
                that see the same upload more than once (/upload, /chat/upload, and
                /summarize all handle the same file) pass this so the expensive work,
                video/audio transcription especially, only ever runs once per file.

        Returns:
            str: Extracted clean text content.

        Raises:
            ValueError: If file extension is unsupported or file is missing.
            RuntimeError: If parsing fails due to corrupted content.
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise ValueError(f"File not found at path: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in cls.SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file extension '{ext}' for file {file_path}")
            raise ValueError(
                f"Unsupported file type '{ext}'. Supported extensions are: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
            )

        if file_hash is not None:
            cached_text = extraction_cache.get(file_hash)
            if cached_text is not None:
                logger.info(
                    f"Reusing cached extraction for '{file_path}' "
                    f"(hash {file_hash[:12]}...) — skipping re-parse/transcription."
                )
                return cached_text

        logger.info(f"Extracting text from file '{file_path}' (type: {ext})...")

        try:
            if ext == ".txt":
                text = cls._parse_txt(file_path)
            elif ext == ".pdf":
                text = cls._parse_pdf(file_path)
            elif ext == ".docx":
                text = cls._parse_docx(file_path)
            elif ext in cls.MEDIA_EXTENSIONS:
                text = cls._parse_media(file_path)
            else:
                text = ""
        except Exception as exc:
            logger.error(f"Failed to parse file '{file_path}': {exc}", exc_info=True)
            raise RuntimeError(
                f"Failed to parse file '{os.path.basename(file_path)}': {str(exc)}"
            ) from exc

        if file_hash is not None:
            extraction_cache.set(file_hash, text)

        return text

    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """
        Parses plain text (.txt) files with fallback encoding support.
        """
        encodings = ["utf-8", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read().strip()
                    logger.debug(f"Successfully parsed TXT using '{encoding}' encoding.")
                    return content
            except UnicodeDecodeError:
                continue

        raise ValueError(
            "Could not decode text file using standard encodings (utf-8, latin-1, cp1252)."
        )

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """
        Parses PDF (.pdf) files using pypdf.
        """
        reader = PdfReader(file_path)
        extracted_text = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text.append(page_text)

        full_text = "\n".join(extracted_text).strip()

        if not full_text:
            logger.warning(
                f"No text extracted from PDF file '{file_path}' (may be scanned images)."
            )

        return full_text

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """
        Parses Word document (.docx) files using python-docx.
        """
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()

    @staticmethod
    def _parse_media(file_path: str) -> str:
        """
        Transcribes a recorded video or audio meeting into plain text via
        TranscriptionService (ffmpeg + local Whisper). Imported lazily so loading a
        document-only transcript never pulls in the transcription stack.
        """
        from backend.services.transcription_service import TranscriptionService

        return TranscriptionService.transcribe(file_path)

    @classmethod
    def max_size_mb(cls, ext: str) -> int:
        """
        Returns the upload size ceiling (MB) appropriate for a given extension —
        video/audio recordings are allowed far larger than text documents.
        """
        return settings.MAX_MEDIA_UPLOAD_SIZE_MB if ext in cls.MEDIA_EXTENSIONS else settings.MAX_UPLOAD_SIZE_MB