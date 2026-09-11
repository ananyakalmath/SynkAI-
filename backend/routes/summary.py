"""
Meeting Summarization Route Handler for SynkAI.
Handles POST /summarize endpoint via Ollama LLM.
"""

import asyncio
import os
from fastapi import APIRouter, HTTPException, status
from backend.config import settings
from backend.models.summary import SummaryRequest, SummaryResponse
from backend.services.file_parser import FileParserService
from backend.services.summary_service import SummaryService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
summary_service = SummaryService()


@router.post(
    "/summarize",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI summary from meeting transcript"
)
async def generate_meeting_summary(request: SummaryRequest) -> SummaryResponse:
    """
    Generates an AI summary (Executive Summary, Key Discussion Points, Meeting Outcome)
    from an uploaded filename or direct transcript text.

    - **request**: SummaryRequest containing either `filename` or `transcript_text`.
    """
    transcript_content = ""
    target_filename = request.filename

    if request.filename:
        file_path = os.path.join(settings.UPLOADS_DIR, os.path.basename(request.filename))
        if not os.path.exists(file_path):
            logger.error(f"Transcript file not found: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{request.filename}' not found in uploads directory. Please upload the file first."
            )

        try:
            transcript_content = FileParserService.parse_file(file_path)
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
