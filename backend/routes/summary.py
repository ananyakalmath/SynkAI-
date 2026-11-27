"""
Meeting Summarization Route Handler for SynkAI.
Handles POST /summarize endpoint via Ollama LLM.
"""

import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status
from backend.dependencies import get_current_user
from backend.models.summary import SummaryRequest, SummaryResponse
from backend.services.auth_service import AuthContext
from backend.services.file_parser import FileParserService
from backend.services.summary_service import SummaryService
from backend.utils.logger import get_logger
from backend.utils.uploads import hash_file, workspace_uploads_dir

logger = get_logger(__name__)
router = APIRouter()
summary_service = SummaryService()


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI summary from meeting transcript"
)
async def generate_meeting_summary(
    request: SummaryRequest,
    current: AuthContext = Depends(get_current_user),
) -> SummaryResponse:
    """
    Generates an AI summary (Executive Summary, Key Discussion Points, Meeting Outcome)
    from an uploaded filename or direct transcript text. A filename is only ever looked
    up inside the caller's own workspace folder.

    - **request**: SummaryRequest containing either `filename` or `transcript_text`.
    """
    transcript_content = ""
    target_filename = request.filename

    if request.filename:
        file_path = os.path.join(workspace_uploads_dir(current.workspace_id), os.path.basename(request.filename))
        if not os.path.exists(file_path):
            logger.error(f"Transcript file not found: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{request.filename}' not found in uploads directory. Please upload the file first."
            )

        try:
            # Hash the on-disk file so a content match already extracted by /upload or
            # /chat/upload (video/audio transcription especially) is reused rather than
            # re-run. Hashing is a cheap disk read; it's the parse/transcription it
            # guards against that's expensive, so this still runs off the event loop.
            file_hash = await asyncio.to_thread(hash_file, file_path)
            transcript_content = await asyncio.to_thread(
                FileParserService.parse_file, file_path, file_hash
            )
        except Exception as exc:
            logger.error(f"Error parsing file '{file_path}': {exc}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse text from file '{request.filename}': {str(exc)}"
            )
    elif request.transcript_text and request.transcript_text.strip():
        transcript_content = request.transcript_text.strip()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'filename' or 'transcript_text' must be provided in the request body."
        )

    if not transcript_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript content is empty. Cannot generate summary."
        )

    logger.info(f"Generating summary for transcript (filename: '{target_filename}')...")

    try:
        # Blocking Ollama call: run off the event loop so other requests stay responsive.
        summary_response = await asyncio.to_thread(
            summary_service.generate_summary,
            transcript_content,
            target_filename
        )
        return summary_response

    except ConnectionError as exc:
        logger.error(f"Ollama connection error during summarization: {exc}")
        raise HTTPException(
            status_code=status.HTTP_530_SITE_IS_FROZEN if hasattr(status, "HTTP_530_SITE_IS_FROZEN") else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )
    except Exception as exc:
        logger.error(f"Summarization processing failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(exc)}"
        )
