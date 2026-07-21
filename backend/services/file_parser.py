"""
File Parser Service for SynkAI.
Extracts raw text content from TXT, PDF, and DOCX meeting transcript files.
"""

import os
from pypdf import PdfReader
from docx import Document
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class FileParserService:
    """
    Service responsible for parsing text content from various file formats (.txt, .pdf, .docx).
    """

    SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}

    @classmethod
    def parse_file(cls, file_path: str) -> str:
        """
        Main entry point to parse text from a file based on its extension.

        Args:
            file_path (str): Path to the target file.

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

        logger.info(f"Extracting text from file '{file_path}' (type: {ext})...")

        try:
            if ext == ".txt":
                return cls._parse_txt(file_path)
            elif ext == ".pdf":
                return cls._parse_pdf(file_path)
            elif ext == ".docx":
                return cls._parse_docx(file_path)
        except Exception as exc:
            logger.error(f"Failed to parse file '{file_path}': {exc}", exc_info=True)
            raise RuntimeError(
                f"Failed to parse file '{os.path.basename(file_path)}': {str(exc)}"
            ) from exc

        return ""

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