"""
Analysis Store for SynkAI.

/meeting/analyze returns its result synchronously and (until now) kept no record of
it. Phase 2's "from last meeting" section — pending action items, decisions, and risks
pulled into the next meeting's invite and agenda — needs that history to exist
somewhere, so every analysis is now saved here, scoped by workspace.
"""

import datetime
import json
from typing import Any, Dict, Optional

from backend.db import get_db
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def save_analysis(workspace_id: str, document_id: str, analysis: Dict[str, Any]) -> None:
    """Persists a snapshot of an analysis result for later "from last meeting" lookups."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO meeting_analyses (workspace_id, document_id, analysis_json, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                workspace_id,
                document_id,
                json.dumps(analysis),
                datetime.datetime.now(datetime.timezone.utc).isoformat(),
            ),
        )


def get_latest_analysis(workspace_id: str, document_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns the most recent analysis saved for `document_id`, scoped to `workspace_id`
    so a meeting can never pull "last meeting" content from another workspace's
    document, even if it somehow knew the document_id.
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT analysis_json FROM meeting_analyses "
            "WHERE workspace_id = ? AND document_id = ? ORDER BY created_at DESC LIMIT 1",
            (workspace_id, document_id),
        ).fetchone()

    if row is None:
        return None

    try:
        return json.loads(row["analysis_json"])
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error(f"Corrupt stored analysis for document '{document_id}': {exc}")
        return None
