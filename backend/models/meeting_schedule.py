"""
Pydantic schemas for scheduled meetings (Phase 2): creation, updates, listing, and the
per-participant email send results every create/update/cancel reports back.
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

from backend.config import settings


class ParticipantIn(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr


class MeetingWriteRequest(BaseModel):
    """Shared shape for creating and updating a scheduled meeting."""

    title: str = Field(..., min_length=1)
    objective: Optional[str] = None
    meeting_type: str = Field(default="Other", min_length=1)
    date: str = Field(..., description="YYYY-MM-DD, local to `timezone`")
    start_time: str = Field(..., description="HH:MM (24h), local to `timezone`")
    end_time: str = Field(..., description="HH:MM (24h), local to `timezone`")
    timezone: str = Field(default_factory=lambda: settings.DEFAULT_MEETING_TIMEZONE)
    location: Optional[str] = Field(default=None, description="Physical location or meeting link")
    participants: List[ParticipantIn] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list, description="Attached document_ids from /chat/upload")
    previous_document_id: Optional[str] = Field(
        default=None, description="A previously analyzed document_id to pull a 'from last meeting' section from"
    )
    reminder_24h_enabled: bool = True
    reminder_1h_enabled: bool = True


class ParticipantOut(ParticipantIn):
    pass


class OrganiserOut(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: str


class MeetingOut(BaseModel):
    id: str
    workspace_id: str
    organiser: OrganiserOut
    title: str
    objective: Optional[str] = None
    meeting_type: str
    date: str
    start_time: str
    end_time: str
    timezone: str
    location: Optional[str] = None
    status: str
    participants: List[ParticipantOut]
    document_ids: List[str]
    previous_document_id: Optional[str] = None
    sequence: int
    reminder_24h_enabled: bool
    reminder_1h_enabled: bool
    google_event_id: Optional[str] = None
    google_meet_link: Optional[str] = None
    calendar_sync_error: Optional[str] = None
    created_at: str
    updated_at: str


class EmailSendResultOut(BaseModel):
    email: str
    success: bool
    error: Optional[str] = None


class MeetingWriteResponse(BaseModel):
    meeting: MeetingOut
    invite_results: List[EmailSendResultOut] = Field(
        default_factory=list,
        description="Per-participant invite email outcome — never implies success when it failed",
    )


class MeetingListResponse(BaseModel):
    meetings: List[MeetingOut]
