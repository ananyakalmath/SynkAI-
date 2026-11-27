"""
Agenda Service for SynkAI.

Builds the two content blocks a meeting invite needs beyond its own fields: a
generated agenda from the stated objective, and — when the meeting is linked to a
previously analyzed transcript — a "from last meeting" summary of what's still open.

Deliberately deterministic, not an LLM call: an invite email has to go out reliably
and quickly regardless of whether Ollama is even running, and a template built from
structured fields is honest about being "generated" without overstating it as
AI-written prose.
"""

from typing import Any, Dict, List, Optional

DONE_STATUSES = {"done", "completed", "complete", "closed"}


def generate_agenda(objective: Optional[str]) -> List[str]:
    """
    Turns the organiser's stated objective into agenda line items. A multi-line
    objective (one point per line) becomes one agenda item per line; a single
    paragraph becomes one agenda item.
    """
    objective = (objective or "").strip()
    if not objective:
        return ["(No objective provided.)"]

    lines = [line.strip(" \t-•*") for line in objective.splitlines() if line.strip()]
    return lines if len(lines) > 1 else [objective]


def build_last_meeting_section(analysis: Optional[Dict[str, Any]]) -> Optional[Dict[str, List[str]]]:
    """
    Extracts pending action items, open risks, and decisions from a stored analysis
    snapshot. Returns None when there's nothing to show (no linked analysis, or an
    analysis with nothing outstanding) — the invite simply omits the section, exactly
    as the "when available" requirement intends.
    """
    if not analysis:
        return None

    pending_action_items = [
        f"{item.get('task', '').strip()} (owner: {item.get('owner', 'unassigned')})"
        for item in analysis.get("action_items", [])
        if (item.get("status") or "").strip().lower() not in DONE_STATUSES and item.get("task")
    ]

    risks = [
        (risk.get("risk") or risk.get("blocker") or risk.get("unresolved_issue") or "").strip()
        for risk in analysis.get("risks", [])
    ]
    risks = [r for r in risks if r]

    decisions = [d.strip() for d in analysis.get("decisions", []) if d and d.strip()]

    if not pending_action_items and not risks and not decisions:
        return None

    return {
        "decisions": decisions,
        "pending_action_items": pending_action_items,
        "risks": risks,
    }
