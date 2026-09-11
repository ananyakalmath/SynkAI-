"""
FastAPI route handler for Sprint 4 Multi-Agent Meeting Intelligence.
Provides POST /meeting/analyze to execute the LangGraph workflow.
"""

import asyncio
import os
from fastapi import APIRouter, HTTPException, status
from backend.config import settings
from backend.models.analysis import MeetingAnalysisRequest, MeetingAnalysisResponse
from backend.services.file_parser import FileParserService
from backend.services.vector_service import VectorService
from backend.services.meeting_analysis_service import MeetingAnalysisService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Instantiate services
meeting_analysis_service = MeetingAnalysisService()
vector_service = VectorService()


def _get_transcript_by_document_id(document_id: str) -> str:
    """
    Tries to locate the transcript text for a given document_id.
    First tries to retrieve the filename from ChromaDB and read the file from uploads/.
    If that fails, reconstructs the text directly from the stored vector chunks.
    """
    logger.info(f"Locating transcript for document_id '{document_id}'...")

    # 1. Query ChromaDB for a chunk metadata to get the filename
    try:
        results = vector_service.collection.get(
            where={"document_id": document_id},
            limit=1,
            include=["metadatas"]
        )
        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
            filename = results["metadatas"][0].get("filename")
            if filename:
                file_path = os.path.join(settings.UPLOADS_DIR, filename)
                if os.path.exists(file_path):
                    logger.info(f"Located file '{file_path}' matching document_id. Parsing file...")
                    return FileParserService.parse_file(file_path)
    except Exception as exc:
        logger.warning(f"Error querying ChromaDB metadata or parsing file: {exc}. Trying fallback...")

    # 2. Fallback: Query all chunks and sort by chunk_number to reconstruct transcript
    try:
        all_results = vector_service.collection.get(
            where={"document_id": document_id},
            include=["metadatas", "documents"]
        )
        if all_results and all_results.get("documents") and len(all_results["documents"]) > 0:
            docs = all_results["documents"]
            metas = all_results["metadatas"]

            chunks_with_idx = []
            for doc, meta in zip(docs, metas):
                chunk_num = meta.get("chunk_number", 0)
                chunks_with_idx.append((chunk_num, doc))

            # Sort by chunk sequence
            chunks_with_idx.sort(key=lambda x: x[0])
            reconstructed_text = "\n".join([chunk[1] for chunk in chunks_with_idx])
            if reconstructed_text.strip():
                logger.info(f"Reconstructed transcript of {len(chunks_with_idx)} chunks from vector database.")
                return reconstructed_text
    except Exception as exc:
        logger.error(f"Failed to query and reconstruct chunks from ChromaDB: {exc}")

    raise FileNotFoundError(f"Could not locate or reconstruct transcript for document_id '{document_id}'.")


@router.post(
    "/meeting/analyze",
    response_model=MeetingAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute multi-agent LangGraph workflow over a meeting transcript"
)
async def analyze_meeting(request: MeetingAnalysisRequest) -> MeetingAnalysisResponse:
    """
    Runs multi-agent analysis (Summary, Action Items, Decisions, Deadlines, Risks) using LangGraph.
    Accepts either an existing document_id or raw transcript text.
    """
    transcript_content = ""

    if request.document_id:
        try:
            transcript_content = _get_transcript_by_document_id(request.document_id)
        except FileNotFoundError as exc:
            logger.error(str(exc))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc)
            )
        except Exception as exc:
            logger.error(f"Error resolving document_id '{request.document_id}': {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading transcript for document: {str(exc)}"
            )
    elif request.transcript_text and request.transcript_text.strip():
        transcript_content = request.transcript_text.strip()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'document_id' or 'transcript_text' must be provided."
        )

    logger.info("Executing meeting analysis workflow...")
    try:
        # The workflow is long-running and fully synchronous; run it on a worker thread so
        # the event loop stays free to serve /health and other requests meanwhile.
        analysis_result = await asyncio.to_thread(
            meeting_analysis_service.analyze_transcript,
            transcript_content
        )
        return analysis_result
    except Exception as exc:
        logger.error(f"Meeting analysis failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        )
