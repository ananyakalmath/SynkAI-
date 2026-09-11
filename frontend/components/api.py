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

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

HEALTH_TIMEOUT = 3
LIST_TIMEOUT = 15
UPLOAD_TIMEOUT = 60
INDEX_TIMEOUT = int(os.getenv("INDEX_TIMEOUT_SECONDS", "600"))
SUMMARY_TIMEOUT = int(os.getenv("SUMMARY_TIMEOUT_SECONDS", "900"))
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT_SECONDS", "900"))
ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "1800"))
AUTH_TIMEOUT = 15


class BackendError(RuntimeError):
    """Raised when the backend returns an error or cannot be reached."""


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
) -> Dict[str, Any]:
    """Upload and parse a meeting transcript."""

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
        UPLOAD_TIMEOUT,
        files=files,
    )


def index_transcript(
    filename: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Index a transcript into ChromaDB."""

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
        INDEX_TIMEOUT,
        files=files,
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
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def signup(
    name: str,
    email: str,
    password: str,
    workspace: str = "SynkAI",
) -> Dict[str, Any]:
    """Create a new SynkAI account."""

    return _request(
        "POST",
        "/auth/signup",
        AUTH_TIMEOUT,
        json={
            "name": name,
            "email": email,
            "password": password,
            "workspace": workspace,
        },
    )


def login(
    email: str,
    password: str,
) -> Dict[str, Any]:
    """Log an existing user into SynkAI."""

    return _request(
        "POST",
        "/auth/login",
        AUTH_TIMEOUT,
        json={
            "email": email,
            "password": password,
        },
    )


def get_profile(
    auth_token: str,
) -> Dict[str, Any]:
    """Fetch the profile belonging to the logged-in user."""

    return _request(
        "GET",
        "/auth/profile",
        AUTH_TIMEOUT,
        headers={
            "X-Auth-Token": auth_token,
        },
    )


def update_profile(
    auth_token: str,
    name: str,
    email: str,
    workspace: str,
) -> Dict[str, Any]:
    """Update and permanently save the user's profile."""

    return _request(
        "PUT",
        "/auth/profile",
        AUTH_TIMEOUT,
        headers={
            "X-Auth-Token": auth_token,
        },
        json={
            "name": name,
            "email": email,
            "workspace": workspace,
        },
    )


def logout(
    auth_token: str,
) -> Dict[str, Any]:
    """Log the current user out."""

    return _request(
        "POST",
        "/auth/logout",
        AUTH_TIMEOUT,
        headers={
            "X-Auth-Token": auth_token,
        },
    )