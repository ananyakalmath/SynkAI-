"""
File Upload Route Handler for SynkAI.
Handles POST /upload endpoint for TXT, PDF, DOCX meeting transcripts, and recorded
video/audio meetings (transcribed locally with Whisper before text extraction).
"""

import asyncio
import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from backend.dependencies import get_current_user
from backend.models.upload import UploadResponse
from backend.services.auth_service import AuthContext
from backend.services.file_parser import FileParserService
from backend.utils.logger import get_logger
from backend.utils.uploads import save_upload_and_hash, workspace_uploads_dir

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse meeting transcript"
)
async def upload_meeting_file(
    file: UploadFile = File(...),
    current: AuthContext = Depends(get_current_user),
) -> UploadResponse:
    """
    Uploads a meeting transcript file (.txt, .pdf, .docx) or a recorded video/audio
    meeting (.mp4, .mov, .mkv, .webm, .avi, .mp3, .wav, .m4a, .aac, .flac, .ogg), saves
    it in uploads/<workspace>/, and extracts raw text — transcribing video/audio
    locally first. Scoped to the caller's workspace.

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

    # Ensure the workspace's uploads subdirectory exists
    uploads_dir = workspace_uploads_dir(current.workspace_id)
    os.makedirs(uploads_dir, exist_ok=True)

    # Define destination path
    safe_filename = os.path.basename(file.filename)
    target_path = os.path.join(uploads_dir, safe_filename)

    logger.info(f"Saving uploaded file '{file.filename}' to '{target_path}'...")

    try:
        file_hash = save_upload_and_hash(file, target_path)
    except Exception as exc:
        logger.error(f"Failed to save uploaded file '{file.filename}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file on server: {str(exc)}"
        )

    # Check file size limit (video/audio recordings get a much higher ceiling)
    file_size = os.path.getsize(target_path)
    max_size_mb = FileParserService.max_size_mb(ext)
    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        os.remove(target_path)
        logger.warning(f"File size {file_size} bytes exceeds limit of {max_bytes} bytes.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {max_size_mb} MB."
        )

    # Parse extracted text using FileParserService, keyed by content hash so a file
    # already seen by /chat/upload or /summarize isn't re-parsed (re-transcribed).
    # Video/audio transcription can take minutes, so this runs off the event loop
    # like any other blocking work in SynkAI.
    try:
        extracted_text = await asyncio.to_thread(FileParserService.parse_file, target_path, file_hash)
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
