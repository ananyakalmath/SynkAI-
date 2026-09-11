"""
Pydantic schemas for the indexed meeting listing used by the SynkAI dashboard.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MeetingRecord(BaseModel):
    """
    A meeting transcript that has been indexed into the vector store.
    """
    document_id: str = Field(..., description="Unique identifier assigned at indexing time")
    filename: str = Field(..., description="Name of the source transcript file")
    number_of_chunks: int = Field(default=0, description="Number of indexed chunks for this document")
    indexed_at: Optional[str] = Field(default=None, description="ISO timestamp of when the document was indexed")


class MeetingListResponse(BaseModel):
    """
    Response model for GET /meetings.
    """
    meetings: List[MeetingRecord] = Field(default_factory=list, description="Indexed meetings, newest first")
    total: int = Field(default=0, description="Total number of indexed meetings")
