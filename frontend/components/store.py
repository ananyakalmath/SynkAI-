"""
Local meeting record store for the SynkAI dashboard.

The backend keeps transcripts and vectors; this file keeps the small amount of *workspace*
state the UI needs to show real history and statistics across restarts: which meetings were
summarised or analysed, and the results that were produced.

Everything shown in the dashboard comes from here or from GET /meetings — no invented rows.
"""

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

STORE_PATH = os.getenv("SYNKAI_UI_STORE", os.path.join("data", "meeting_records.json"))

STATUS_INDEXED = "Indexed"
STATUS_SUMMARISED = "Summarised"
STATUS_ANALYSED = "Analysed"

# Ordered by completeness, so a later stage never downgrades an earlier badge.
_STATUS_RANK = {STATUS_INDEXED: 0, STATUS_SUMMARISED: 1, STATUS_ANALYSED: 2}


def _read() -> Dict[str, Dict[str, Any]]:
    """
    Loads the store from disk.

    Returns:
        Dict[str, Dict[str, Any]]: Records keyed by document_id. Empty if missing/corrupt.
    """
    if not os.path.exists(STORE_PATH):
        return {}

    try:
        with open(STORE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}

    return data.get("meetings", {}) if isinstance(data, dict) else {}


def _write(records: Dict[str, Dict[str, Any]]) -> None:
    """
    Persists the store atomically so a crash mid-write cannot corrupt history.

    Args:
        records (Dict[str, Dict[str, Any]]): Records keyed by document_id.
    """
    directory = os.path.dirname(STORE_PATH) or "."
    os.makedirs(directory, exist_ok=True)

    payload = {"version": 1, "meetings": records}
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
    )
    try:
        with handle:
            json.dump(payload, handle, indent=2)
        os.replace(handle.name, STORE_PATH)
    except OSError:
        if os.path.exists(handle.name):
            os.remove(handle.name)


def record_meeting(
    document_id: str,
    filename: str,
    number_of_chunks: int = 0,
    character_count: Optional[int] = None,
) -> None:
    """
    Registers a newly indexed meeting (or refreshes its metadata).

    Args:
        document_id (str): Identifier returned by /chat/upload.
        filename (str): Transcript file name.
        number_of_chunks (int): Chunks indexed for the document.
        character_count (Optional[int]): Parsed transcript length.
    """
    records = _read()
    record = records.get(document_id, {})
    record.update({
        "document_id": document_id,
        "filename": filename,
        "number_of_chunks": number_of_chunks or record.get("number_of_chunks", 0),
        "created_at": record.get("created_at") or datetime.now().astimezone().isoformat(),
        "status": record.get("status") or STATUS_INDEXED,
    })
    if character_count is not None:
        record["character_count"] = character_count

    records[document_id] = record
    _write(records)


def _set_status(record: Dict[str, Any], status: str) -> None:
    """Raises a record's status without ever downgrading it."""
    current = record.get("status", STATUS_INDEXED)
    if _STATUS_RANK.get(status, 0) >= _STATUS_RANK.get(current, 0):
        record["status"] = status


def save_summary(document_id: str, summary: Dict[str, Any]) -> None:
    """
    Stores a summary result and marks the meeting as summarised.

    Args:
        document_id (str): Meeting identifier.
        summary (Dict[str, Any]): SummaryResponse payload.
    """
    records = _read()
    record = records.setdefault(document_id, {"document_id": document_id})
    record["summary"] = summary
    record["summarised_at"] = datetime.now().astimezone().isoformat()
    _set_status(record, STATUS_SUMMARISED)
    _write(records)


def save_analysis(document_id: str, analysis: Dict[str, Any]) -> None:
    """
    Stores an analysis result and marks the meeting as analysed.

    Args:
        document_id (str): Meeting identifier.
        analysis (Dict[str, Any]): MeetingAnalysisResponse payload.
    """
    records = _read()
    record = records.setdefault(document_id, {"document_id": document_id})
    record["analysis"] = analysis
    record["analysed_at"] = datetime.now().astimezone().isoformat()
    _set_status(record, STATUS_ANALYSED)
    _write(records)


def get(document_id: str) -> Dict[str, Any]:
    """
    Returns a single stored record.

    Args:
        document_id (str): Meeting identifier.

    Returns:
        Dict[str, Any]: The record, or an empty dict when unknown.
    """
    return _read().get(document_id, {})


def merge_with_backend(backend_meetings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Combines indexed meetings from the backend with locally stored workspace state.

    The backend is the source of truth for what exists; the local store adds status,
    summaries and analyses. Records known only locally are kept so nothing disappears.

    Args:
        backend_meetings (List[Dict[str, Any]]): Records from GET /meetings.

    Returns:
        List[Dict[str, Any]]: Merged meetings, newest first.
    """
    local = _read()
    merged: Dict[str, Dict[str, Any]] = {}

    for meeting in backend_meetings:
        document_id = meeting.get("document_id")
        if not document_id:
            continue
        stored = local.get(document_id, {})
        merged[document_id] = {
            **stored,
            "document_id": document_id,
            "filename": meeting.get("filename") or stored.get("filename") or "Untitled transcript",
            "number_of_chunks": meeting.get("number_of_chunks") or stored.get("number_of_chunks", 0),
            "created_at": meeting.get("indexed_at") or stored.get("created_at"),
            "status": stored.get("status", STATUS_INDEXED),
        }

    for document_id, stored in local.items():
        if document_id not in merged:
            merged[document_id] = {**stored, "document_id": document_id}

    meetings = list(merged.values())
    meetings.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return meetings


def stats(meetings: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregates dashboard statistics from real stored analyses.

    Args:
        meetings (List[Dict[str, Any]]): Merged meeting records.

    Returns:
        Dict[str, int]: Totals for meetings, action items, decisions and deadlines.
    """
    totals = {"meetings": len(meetings), "action_items": 0, "decisions": 0, "deadlines": 0}

    for meeting in meetings:
        analysis = meeting.get("analysis") or {}
        totals["action_items"] += len(analysis.get("action_items") or [])
        totals["decisions"] += len(analysis.get("decisions") or [])
        totals["deadlines"] += len(analysis.get("deadlines") or [])

    return totals


def format_timestamp(value: Optional[str]) -> str:
    """
    Formats a stored ISO timestamp as "11 Sep 2026 · 2:30 PM".

    Args:
        value (Optional[str]): ISO 8601 timestamp.

    Returns:
        str: Display string, or "Date unavailable" when missing/unparseable.
    """
    if not value:
        return "Date unavailable"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "Date unavailable"

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()

    return f"{parsed.strftime('%d %b %Y')} · {parsed.strftime('%I:%M %p').lstrip('0')}"
