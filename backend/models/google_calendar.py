"""Pydantic schemas for the Google Calendar connect/disconnect routes (Phase 3)."""

from pydantic import BaseModel


class GoogleCalendarConnectResponse(BaseModel):
    authorization_url: str
    state: str


class GoogleCalendarCallbackRequest(BaseModel):
    code: str
    state: str


class GoogleCalendarStatusResponse(BaseModel):
    connected: bool
