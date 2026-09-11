"""
Backend client for the SynkAI frontend.

A thin wrapper over the existing FastAPI endpoints — request and response shapes are
unchanged from Sprints 1-4:

    GET  /health
    GET  /meetings
    POST /upload
    POST /summarize
    POST /chat/upload
    POST /chat/query
    POST /meeting/analyze
"""

import os
from typing import Any, Dict, List, Optional

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

# Local inference is slow, so timeouts are per-operation rather than one global value.
HEALTH_TIMEOUT = 3
LIST_TIMEOUT = 15
UPLOAD_TIMEOUT = 60
INDEX_TIMEOUT = int(os.getenv("INDEX_TIMEOUT_SECONDS", "600"))
SUMMARY_TIMEOUT = int(os.getenv("SUMMARY_TIMEOUT_SECONDS", "900"))
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT_SECONDS", "900"))
ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "1800"))


class BackendError(RuntimeError):
    """Raised when the backend returns an error or cannot be reached."""


def _detail(response: requests.Response) -> str:
    """
    Extracts the most useful error message from a failed response.

    Args:
        response (requests.Response): Failed HTTP response.

    Returns:
        str: Error detail text.
    """
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


def _request(method: str, path: str, timeout: int, **kwargs: Any) -> Dict[str, Any]:
    """
    Issues an HTTP request to the backend and returns the decoded JSON body.

    Args:
        method (str): HTTP verb.
        path (str): Endpoint path beginning with "/".
        timeout (int): Read timeout in seconds.
        **kwargs: Passed through to `requests.request`.

    Returns:
        Dict[str, Any]: Decoded response body.

    Raises:
        BackendError: On connection failure or a non-2xx response.
    """
    url = f"{BACKEND_URL}{path}"
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
    except requests.exceptions.Timeout as exc:
        raise BackendError(
            f"The request to {path} timed out after {timeout}s. Local inference may still be running."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise BackendError(
            f"Could not reach the SynkAI backend at {BACKEND_URL}. Is it running?"
        ) from exc

    if response.status_code >= 400:
        raise BackendError(_detail(response))

    if not response.content:
        return {}

    return response.json()


def is_backend_online() -> bool:
    """
    Checks whether the backend answers the health endpoint.

    Returns:
        bool: True when the backend reports "ok".
    """
    try:
        payload = _request("GET", "/health", HEALTH_TIMEOUT)
    except BackendError:
        return False
    return payload.get("status") == "ok"


def list_meetings() -> List[Dict[str, Any]]:
    """
    Fetches meetings already indexed in the vector store.

    Returns:
        List[Dict[str, Any]]: Meeting records, newest first. Empty when unavailable.
    """
    try:
        payload = _request("GET", "/meetings", LIST_TIMEOUT)
    except BackendError:
        return []
    return payload.get("meetings", [])


def upload_transcript(filename: str, data: bytes, content_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Saves and parses a transcript via POST /upload.

    Args:
        filename (str): Original file name.
        data (bytes): File contents.
        content_type (Optional[str]): MIME type reported by the browser.

    Returns:
        Dict[str, Any]: UploadResponse payload.
    """
    files = {"file": (filename, data, content_type or "application/octet-stream")}
    return _request("POST", "/upload", UPLOAD_TIMEOUT, files=files)


def index_transcript(filename: str, data: bytes, content_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Chunks, embeds and indexes a transcript via POST /chat/upload.

    Args:
        filename (str): Original file name.
        data (bytes): File contents.
        content_type (Optional[str]): MIME type reported by the browser.

    Returns:
        Dict[str, Any]: ChatUploadResponse payload with `document_id`.
    """
    files = {"file": (filename, data, content_type or "application/octet-stream")}
    return _request("POST", "/chat/upload", INDEX_TIMEOUT, files=files)


def summarize(filename: Optional[str] = None, transcript_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates a structured summary via POST /summarize.

    Args:
        filename (Optional[str]): Name of a transcript already in uploads/.
        transcript_text (Optional[str]): Raw transcript text instead of a file.

    Returns:
        Dict[str, Any]: SummaryResponse payload.
    """
    payload: Dict[str, Any] = {}
    if filename:
        payload["filename"] = filename
    if transcript_text:
        payload["transcript_text"] = transcript_text
    return _request("POST", "/summarize", SUMMARY_TIMEOUT, json=payload)


def ask(document_id: str, question: str) -> Dict[str, Any]:
    """
    Asks a question about an indexed meeting via POST /chat/query.

    Args:
        document_id (str): Document to query.
        question (str): User question.

    Returns:
        Dict[str, Any]: ChatQueryResponse payload with `answer` and `sources`.
    """
    return _request(
        "POST", "/chat/query", CHAT_TIMEOUT,
        json={"document_id": document_id, "question": question},
    )


def analyze(document_id: Optional[str] = None, transcript_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Runs the multi-agent LangGraph workflow via POST /meeting/analyze.

    Args:
        document_id (Optional[str]): Indexed document to analyse.
        transcript_text (Optional[str]): Raw transcript text instead of a document.

    Returns:
        Dict[str, Any]: MeetingAnalysisResponse payload.
    """
    payload: Dict[str, Any] = {}
    if document_id:
        payload["document_id"] = document_id
    if transcript_text:
        payload["transcript_text"] = transcript_text
    return _request("POST", "/meeting/analyze", ANALYSIS_TIMEOUT, json=payload)
