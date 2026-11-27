"""
Scheduled Meeting routes for SynkAI (Phase 2).

Create, update, cancel, and list meetings — each workspace-scoped via
get_current_user, and each create/update/cancel sends calendar invites to every
participant, reporting per-participant success/failure rather than assuming success.
"""

import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from backend.dependencies import get_current_user
from backend.models.meeting_schedule import MeetingListResponse, MeetingOut, MeetingWriteRequest, MeetingWriteResponse
from backend.services import meeting_schedule_service as schedule_service
from backend.services.auth_service import AuthContext
from backend.services.ics_service import InvalidTimezoneError
from backend.services.meeting_schedule_service import MeetingNotFoundError
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/scheduled-meetings", tags=["Scheduled Meetings"])


def _request_to_data(request: MeetingWriteRequest) -> dict:
    return {
        "title": request.title,
        "objective": request.objective,
        "meeting_type": request.meeting_type,
        "date": request.date,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "timezone": request.timezone,
        "location": request.location,
        "participants": [p.model_dump() for p in request.participants],
        "document_ids": request.document_ids,
        "previous_document_id": request.previous_document_id,
        "reminder_24h_enabled": request.reminder_24h_enabled,
        "reminder_1h_enabled": request.reminder_1h_enabled,
    }


@router.post("", response_model=MeetingWriteResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    request: MeetingWriteRequest,
    current: AuthContext = Depends(get_current_user),
) -> MeetingWriteResponse:
    """Schedules a meeting and emails every participant a calendar invite."""
    try:
        meeting, invite_results = schedule_service.create_meeting(
            current.workspace_id, current.user_id, _request_to_data(request)
        )
    except InvalidTimezoneError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return MeetingWriteResponse(meeting=meeting, invite_results=invite_results)


@router.put("/{meeting_id}", response_model=MeetingWriteResponse)
async def update_meeting(
    meeting_id: str,
    request: MeetingWriteRequest,
    current: AuthContext = Depends(get_current_user),
) -> MeetingWriteResponse:
    """Replaces a meeting's details and emails every participant an updated invite."""
    try:
        meeting, invite_results = schedule_service.update_meeting(
            current.workspace_id, meeting_id, _request_to_data(request)
        )
    except MeetingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTimezoneError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return MeetingWriteResponse(meeting=meeting, invite_results=invite_results)


@router.post("/{meeting_id}/cancel", response_model=MeetingWriteResponse)
async def cancel_meeting(
    meeting_id: str,
    current: AuthContext = Depends(get_current_user),
) -> MeetingWriteResponse:
    """Cancels a meeting and emails every participant a cancellation notice."""
    try:
        meeting, invite_results = schedule_service.cancel_meeting(current.workspace_id, meeting_id)
    except MeetingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return MeetingWriteResponse(meeting=meeting, invite_results=invite_results)


@router.get("/{meeting_id}", response_model=MeetingOut)
async def get_meeting(
    meeting_id: str,
    current: AuthContext = Depends(get_current_user),
) -> dict:
    """Fetches one meeting's full detail — 404 if it isn't in the caller's workspace."""
    try:
        return schedule_service.get_meeting(current.workspace_id, meeting_id)
    except MeetingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    year: int,
    month: int,
    current: AuthContext = Depends(get_current_user),
) -> MeetingListResponse:
    """Lists every meeting in the caller's workspace for the given calendar month."""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="month must be 1-12.")

    meetings = schedule_service.list_meetings_by_month(current.workspace_id, year, month)
    return MeetingListResponse(meetings=meetings)
