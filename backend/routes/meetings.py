"""
Meeting listing route for SynkAI.

Read-only view over the documents already indexed in ChromaDB, so the dashboard can show
real meeting history instead of placeholder rows. Does not touch the RAG or agent pipelines.
"""

import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import get_current_user
from backend.models.meeting import MeetingListResponse, MeetingRecord
from backend.services.auth_service import AuthContext
from backend.services.vector_service import VectorService
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

vector_service = VectorService()


def _collect_meetings(workspace_id: str) -> List[MeetingRecord]:
    """
    Groups the stored vector chunks by document_id into one record per meeting,
    scoped to a single workspace.

    Returns:
        List[MeetingRecord]: Indexed meetings, newest first.
    """
    results = vector_service.collection.get(where={"workspace_id": workspace_id}, include=["metadatas"])
    metadatas = (results or {}).get("metadatas") or []

    grouped: Dict[str, Dict[str, Any]] = {}

    for meta in metadatas:
        document_id = (meta or {}).get("document_id")
        if not document_id:
            continue

        record = grouped.setdefault(document_id, {
            "document_id": document_id,
            "filename": meta.get("filename") or "Untitled transcript",
            "number_of_chunks": 0,
            "indexed_at": meta.get("upload_timestamp"),
        })
        record["number_of_chunks"] += 1

        # Keep the earliest timestamp seen for the document.
        timestamp = meta.get("upload_timestamp")
        if timestamp and (not record["indexed_at"] or timestamp < record["indexed_at"]):
            record["indexed_at"] = timestamp

    meetings = [MeetingRecord(**record) for record in grouped.values()]
    meetings.sort(key=lambda m: m.indexed_at or "", reverse=True)
    return meetings


@router.get(
    "/meetings",
    response_model=MeetingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List meeting transcripts indexed in the vector store"
)
async def list_meetings(current: AuthContext = Depends(get_current_user)) -> MeetingListResponse:
    """
    Returns every meeting transcript indexed in ChromaDB for the caller's workspace,
    newest first.
    """
    logger.info(f"Listing indexed meetings for workspace '{current.workspace_id}'...")

    try:
        meetings = await asyncio.to_thread(_collect_meetings, current.workspace_id)
    except Exception as exc:
        logger.error(f"Failed to list indexed meetings: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read meeting history: {str(exc)}"
        )

    logger.info(f"Found {len(meetings)} indexed meeting(s).")
    return MeetingListResponse(meetings=meetings, total=len(meetings))
