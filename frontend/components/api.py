"""
Backend client for the SynkAI frontend.

Handles communication with the FastAPI backend, including:
- Meetings
- Uploads
- Summaries
- RAG chat
- Meeting analysis
- Authentication
- User profiles
"""

import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

HEALTH_TIMEOUT = 3
LIST_TIMEOUT = 15
UPLOAD_TIMEOUT = 60
# Video/audio is transcribed with local Whisper before text is returned, which takes far
# longer than parsing a document — give it room instead of timing out mid-transcription.
MEDIA_UPLOAD_TIMEOUT = int(os.getenv("MEDIA_UPLOAD_TIMEOUT_SECONDS", "1800"))
INDEX_TIMEOUT = int(os.getenv("INDEX_TIMEOUT_SECONDS", "600"))
SUMMARY_TIMEOUT = int(os.getenv("SUMMARY_TIMEOUT_SECONDS", "900"))
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT_SECONDS", "900"))
ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "1800"))
AUTH_TIMEOUT = 15


class BackendError(RuntimeError):
    """Raised when the backend returns an error or cannot be reached."""


def _auth_headers() -> Dict[str, str]:
    """
    Reads the current session's token from Streamlit session state and returns the
    Authorization header every workspace-scoped endpoint now requires. Every call below
    that touches meetings, documents, or RAG data sends this.
    """
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _detail(response: requests.Response) -> str:
    """Extract the most useful error message from a failed response."""

    try:
        payload = response.json()
    except Exception:
        return response.text or f"HTTP {response.status_code}"

    detail = payload.get("detail", payload) if isinstance(payload, dict) else payload

    if isinstance(detail, list) and detail:
        first = detail[0]

        if isinstance(first, dict):
            return first.get("msg", str(first))

    return str(detail)


def _request(
    method: str,
    path: str,
    timeout: int,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Send an HTTP request to the backend."""

    url = f"{BACKEND_URL}{path}"

    try:
        response = requests.request(
            method,
            url,
            timeout=timeout,
            **kwargs,
        )

    except requests.exceptions.Timeout as exc:
        raise BackendError(
            f"The request to {path} timed out after {timeout}s."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise BackendError(
            f"Could not reach the SynkAI backend at {BACKEND_URL}. "
            "Is it running?"
        ) from exc

    if response.status_code >= 400:
        raise BackendError(_detail(response))

    if not response.content:
        return {}

    return response.json()


# ============================================================
# HEALTH
# ============================================================

def is_backend_online() -> bool:
    """Check whether the backend is online."""

    try:
        payload = _request(
            "GET",
            "/health",
            HEALTH_TIMEOUT,
        )

    except BackendError:
        return False

    return payload.get("status") == "ok"


# ============================================================
# MEETINGS
# ============================================================

def list_meetings() -> List[Dict[str, Any]]:
    """Fetch meetings already indexed in the vector store."""

    try:
        payload = _request(
            "GET",
            "/meetings",
            LIST_TIMEOUT,
            headers=_auth_headers(),
        )

    except BackendError:
        return []

    return payload.get("meetings", [])


# ============================================================
# UPLOAD
# ============================================================

def upload_transcript(
    filename: str,
    data: bytes,
    content_type: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """Upload and parse a meeting transcript (or transcribe a video/audio recording)."""

    files = {
        "file": (
            filename,
            data,
            content_type or "application/octet-stream",
        )
    }

    return _request(
        "POST",
        "/upload",
        timeout or UPLOAD_TIMEOUT,
        files=files,
        headers=_auth_headers(),
    )


def index_transcript(
    filename: str,
    data: bytes,
    content_type: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """Index a transcript into ChromaDB (re-transcribes video/audio before chunking)."""

    files = {
        "file": (
            filename,
            data,
            content_type or "application/octet-stream",
        )
    }

    return _request(
        "POST",
        "/chat/upload",
        timeout or INDEX_TIMEOUT,
        files=files,
        headers=_auth_headers(),
    )


# ============================================================
# SUMMARIZATION
# ============================================================

def summarize(
    filename: Optional[str] = None,
    transcript_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a structured meeting summary."""

    payload: Dict[str, Any] = {}

    if filename:
        payload["filename"] = filename

    if transcript_text:
        payload["transcript_text"] = transcript_text

    return _request(
        "POST",
        "/summarize",
        SUMMARY_TIMEOUT,
        json=payload,
        headers=_auth_headers(),
    )


# ============================================================
# RAG CHAT
# ============================================================

def ask(
    document_id: str,
    question: str,
) -> Dict[str, Any]:
    """Ask a question about an indexed meeting."""

    return _request(
        "POST",
        "/chat/query",
        CHAT_TIMEOUT,
        json={
            "document_id": document_id,
            "question": question,
        },
        headers=_auth_headers(),
    )


# ============================================================
# ANALYSIS
# ============================================================

def analyze(
    document_id: Optional[str] = None,
    transcript_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the multi-agent meeting analysis workflow."""

    payload: Dict[str, Any] = {}

    if document_id:
        payload["document_id"] = document_id

    if transcript_text:
        payload["transcript_text"] = transcript_text

    return _request(
        "POST",
        "/meeting/analyze",
        ANALYSIS_TIMEOUT,
        json=payload,
        headers=_auth_headers(),
    )


# ============================================================
# SCHEDULED MEETINGS
# ============================================================

def list_scheduled_meetings(year: int, month: int) -> List[Dict[str, Any]]:
    """Lists every scheduled meeting in the caller's workspace for a calendar month."""

    payload = _request(
        "GET",
        "/scheduled-meetings",
        LIST_TIMEOUT,
        params={"year": year, "month": month},
        headers=_auth_headers(),
    )
    return payload.get("meetings", [])


def get_scheduled_meeting(meeting_id: str) -> Dict[str, Any]:
    """Fetches one scheduled meeting's full detail."""

    return _request(
        "GET",
        f"/scheduled-meetings/{meeting_id}",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


def create_scheduled_meeting(data: Dict[str, Any]) -> Dict[str, Any]:
    """Schedules a meeting; the backend emails every participant a calendar invite."""

    return _request(
        "POST",
        "/scheduled-meetings",
        SUMMARY_TIMEOUT,
        json=data,
        headers=_auth_headers(),
    )


def update_scheduled_meeting(meeting_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Replaces a meeting's details; the backend emails every participant an updated invite."""

    return _request(
        "PUT",
        f"/scheduled-meetings/{meeting_id}",
        SUMMARY_TIMEOUT,
        json=data,
        headers=_auth_headers(),
    )


def cancel_scheduled_meeting(meeting_id: str) -> Dict[str, Any]:
    """Cancels a meeting; the backend emails every participant a cancellation notice."""

    return _request(
        "POST",
        f"/scheduled-meetings/{meeting_id}/cancel",
        SUMMARY_TIMEOUT,
        headers=_auth_headers(),
    )


# ============================================================
# GOOGLE CALENDAR (incremental authorization, separate from sign-in)
# ============================================================

def google_calendar_connect_url() -> Dict[str, Any]:
    """Asks the backend for the calendar-scoped Google consent-screen URL."""

    return _request("GET", "/auth/google/calendar/connect", AUTH_TIMEOUT, headers=_auth_headers())


def google_calendar_callback(code: str, state: str) -> Dict[str, Any]:
    """Exchanges the authorization code for a stored (encrypted) calendar connection."""

    return _request(
        "POST",
        "/auth/google/calendar/connect/callback",
        AUTH_TIMEOUT,
        json={"code": code, "state": state},
    )


def google_calendar_status() -> Dict[str, Any]:
    """Whether the current user has connected Google Calendar."""

    return _request("GET", "/auth/google/calendar/status", AUTH_TIMEOUT, headers=_auth_headers())


def google_calendar_disconnect() -> Dict[str, Any]:
    """Disconnects Google Calendar for the current user."""

    return _request("POST", "/auth/google/calendar/disconnect", AUTH_TIMEOUT, headers=_auth_headers())


# ============================================================
# AUTHENTICATION
# ============================================================
# No passwords: accounts exist only via Google sign-in or an emailed one-time code.

def google_login_url(invite_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Asks the backend for the Google consent-screen URL and a CSRF state token. Passing
    `invite_code` (from an invite link) lets it survive the round trip to Google and back.
    """

    params = {"invite_code": invite_code} if invite_code else None
    return _request("GET", "/auth/google/login", AUTH_TIMEOUT, params=params)


def google_callback(code: str, state: str) -> Dict[str, Any]:
    """Exchanges a Google authorization code (and the state we were issued) for a session."""

    return _request(
        "POST",
        "/auth/google/callback",
        AUTH_TIMEOUT,
        json={"code": code, "state": state},
    )


def request_email_code(email: str) -> Dict[str, Any]:
    """Asks the backend to email a one-time login code to `email`."""

    return _request(
        "POST",
        "/auth/email/request-code",
        AUTH_TIMEOUT,
        json={"email": email},
    )


def verify_email_code(email: str, code: str) -> Dict[str, Any]:
    """Verifies an emailed login code and returns a session on success."""

    return _request(
        "POST",
        "/auth/email/verify-code",
        AUTH_TIMEOUT,
        json={"email": email, "code": code},
    )


def get_me() -> Dict[str, Any]:
    """Fetches the current session's user, onboarding state, and workspace/role."""

    return _request(
        "GET",
        "/auth/me",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


def submit_onboarding(
    full_name: str,
    role_title: str,
    company_name: Optional[str] = None,
    invite_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Completes onboarding: records name/role, and either joins the workspace named by
    `invite_code` directly, or creates/requests to join one matched by email domain
    (company_name names a brand-new workspace in that case).
    """

    payload: Dict[str, Any] = {"full_name": full_name, "role_title": role_title}
    if company_name:
        payload["company_name"] = company_name
    if invite_code:
        payload["invite_code"] = invite_code

    return _request(
        "POST",
        "/auth/onboarding",
        AUTH_TIMEOUT,
        json=payload,
        headers=_auth_headers(),
    )


def update_profile(full_name: str, role_title: str) -> Dict[str, Any]:
    """Updates the current user's name and role/title."""

    return _request(
        "PUT",
        "/auth/profile",
        AUTH_TIMEOUT,
        json={"full_name": full_name, "role_title": role_title},
        headers=_auth_headers(),
    )


def logout() -> Dict[str, Any]:
    """Logs out the current session only."""

    return _request(
        "POST",
        "/auth/logout",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


def logout_all_devices() -> Dict[str, Any]:
    """Logs out every session/device for the current user."""

    return _request(
        "POST",
        "/auth/logout-all",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


# ============================================================
# WORKSPACE
# ============================================================

def get_workspace_members() -> Dict[str, Any]:
    """Lists active workspace members; pending join requests are included for admins."""

    return _request(
        "GET",
        "/workspace/members",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


def rename_workspace(company_name: str) -> Dict[str, Any]:
    """Admin-only: renames the workspace's display name."""

    return _request(
        "PUT",
        "/workspace/",
        AUTH_TIMEOUT,
        json={"company_name": company_name},
        headers=_auth_headers(),
    )


def invite_to_workspace(email: str) -> Dict[str, Any]:
    """Admin-only: invites someone by email to the workspace."""

    return _request(
        "POST",
        "/workspace/invites",
        AUTH_TIMEOUT,
        json={"email": email},
        headers=_auth_headers(),
    )


def list_workspace_invites() -> Dict[str, Any]:
    """Admin-only: lists outstanding (unused, unexpired) invites."""

    return _request(
        "GET",
        "/workspace/invites",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


def approve_workspace_request(user_id: str) -> Dict[str, Any]:
    """Admin-only: approves a pending join request."""

    return _request(
        "POST",
        f"/workspace/requests/{user_id}/approve",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )


def reject_workspace_request(user_id: str) -> Dict[str, Any]:
    """Admin-only: rejects a pending join request."""

    return _request(
        "POST",
        f"/workspace/requests/{user_id}/reject",
        AUTH_TIMEOUT,
        headers=_auth_headers(),
    )