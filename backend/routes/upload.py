"""
File Upload Route Handler for SynkAI.
Handles POST /upload endpoint for TXT, PDF, and DOCX meeting transcripts.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from backend.config import settings
from backend.models.upload import UploadResponse
from backend.services.file_parser import FileParserService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse meeting transcript"
)
async def upload_meeting_file(file: UploadFile = File(...)) -> UploadResponse:
    """
    Uploads a meeting transcript file (.txt, .pdf, .docx), saves it in uploads/, and extracts raw text.

    - **file**: UploadFile binary stream.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename cannot be empty."
        )

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()

    if ext not in FileParserService.SUPPORTED_EXTENSIONS:
        logger.warning(f"Rejected upload for unsupported extension '{ext}': {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats are: {', '.join(FileParserService.SUPPORTED_EXTENSIONS)}"
        )

    # Ensure uploads directory exists
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)

    # Define destination path
    safe_filename = os.path.basename(file.filename)
    target_path = os.path.join(settings.UPLOADS_DIR, safe_filename)

    logger.info(f"Saving uploaded file '{file.filename}' to '{target_path}'...")

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        logger.error(f"Failed to save uploaded file '{file.filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file on server: {str(exc)}"
        )

    # Check file size limit
    file_size = os.path.getsize(target_path)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        os.remove(target_path)
        logger.warning(f"File size {file_size} bytes exceeds limit of {max_bytes} bytes.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # Parse extracted text using FileParserService
    try:
        extracted_text = FileParserService.parse_file(target_path)
    except Exception as exc:
        logger.error(f"Text extraction failed for '{target_path}': {exc}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse text from uploaded file: {str(exc)}"
        )

    sample = extracted_text[:200] + ("..." if len(extracted_text) > 200 else "")

    return UploadResponse(
        filename=safe_filename,
        file_path=target_path,
        file_size_bytes=file_size,
        character_count=len(extracted_text),
        sample_text=sample,
        message=f"File '{safe_filename}' uploaded and parsed successfully."
    )
