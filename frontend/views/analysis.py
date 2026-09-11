"""
Meeting Analysis.

Presentation layer for the Sprint 4 LangGraph workflow. Renders exactly what
POST /meeting/analyze returns — including partial runs reported via `agent_errors`.
"""

from typing import Callable, Dict, List

import streamlit as st

from frontend.components import api, store, ui


def _run_analysis(document_id: str) -> None:
    """
    Executes the multi-agent workflow for a meeting and stores the result.

    Args:
        document_id (str): Indexed document to analyse.
    """
    st.session_state.notice = None
    try:
        with st.spinner(
            "Running the agent workflow — parser, summary, action items, decisions, "
            "deadlines and risks run one at a time on your local model."
        ):
            analysis = api.analyze(document_id=document_id)
        st.session_state.analysis_data = analysis
        store.save_analysis(document_id, analysis)
    except api.BackendError as exc:
        st.session_state.notice = str(exc)


def _render_action_items(items: List[Dict]) -> None:
    """Renders the action items panel."""
    if not items:
        ui.panel("Action Items", ui.prose("No action items were identified in this meeting."),
                 icon_name="check")
        return

    entries = [
        {
            "primary": item.get("task", ""),
            "meta": [
                ("Owner", item.get("owner")),
                ("Due", item.get("due_date")),
                ("Priority", item.get("priority")),
                ("Status", item.get("status")),
            ],
        }
        for item in items
    ]
    ui.panel("Action Items", ui.detail_list(entries), icon_name="check", count=f"{len(items)} items")


def _render_decisions(decisions: List[str]) -> None:
    """Renders the decisions panel."""
    body = (
        ui.numbered_list(decisions) if decisions
        else ui.prose("No decisions were recorded in this meeting.")
    )
    ui.panel("Decisions", body, icon_name="gavel",
             count=f"{len(decisions)} decisions" if decisions else None)


def _render_deadlines(deadlines: List[Dict]) -> None:
    """Renders the deadlines panel."""
    if not deadlines:
        ui.panel("Deadlines", ui.prose("No deadlines or milestones were mentioned."),
                 icon_name="calendar")
        return

    entries = [
        {
            "primary": deadline.get("deadline", ""),
            "meta": [
                ("Date", deadline.get("date")),
                ("Milestone", deadline.get("milestone")),
                ("Owner", deadline.get("responsible_person")),
            ],
        }
        for deadline in deadlines
    ]
    ui.panel("Deadlines", ui.detail_list(entries), icon_name="calendar",
             count=f"{len(deadlines)} dates")


def _render_risks(risks: List[Dict]) -> None:
    """Renders the risks panel."""
    if not risks:
        ui.panel("Risks & Blockers", ui.prose("No risks or blockers were raised."), icon_name="risk")
        return

    entries = [
        {
            "primary": risk.get("risk", ""),
            "meta": [
                ("Blocker", risk.get("blocker")),
                ("Dependency", risk.get("dependency")),
                ("Open issue", risk.get("unresolved_issue")),
            ],
        }
        for risk in risks
    ]
    ui.panel("Risks & Blockers", ui.detail_list(entries), icon_name="risk",
             count=f"{len(risks)} risks")


def _render_analysis(analysis: Dict) -> None:
    """
    Renders a complete analysis payload.

    Args:
        analysis (Dict): MeetingAnalysisResponse payload.
    """
    errors = analysis.get("agent_errors") or []
    if errors:
        st.warning(
            "Partial analysis — "
            + "; ".join(
                f"{error.get('agent')}: {error.get('error')}" for error in errors
            )
        )
        ui.spacer(0.8)

    ui.panel(
        "Executive Summary",
        ui.prose(analysis.get("executive_summary", "")),
        icon_name="sparkle",
    )

    overview = analysis.get("meeting_overview")
    if overview:
        ui.panel("Meeting Overview", ui.prose(overview), icon_name="layers")

    _render_action_items(analysis.get("action_items") or [])
    _render_decisions(analysis.get("decisions") or [])
    _render_deadlines(analysis.get("deadlines") or [])
    _render_risks(analysis.get("risks") or [])


def render(go: Callable[[str], None]) -> None:
    """
    Renders the Meeting Analysis page.

    Args:
        go (Callable[[str], None]): Route switcher.
    """
    ui.page_header(
        "Intelligence",
        "Meeting Analysis",
        "Seven specialised agents read the transcript in sequence and return action items, "
        "decisions, deadlines and risks.",
    )
    ui.rule()

    document_id = st.session_state.get("active_document_id")
    filename = st.session_state.get("active_filename")

    if not document_id:
        ui.empty_state(
            "No meeting selected",
            "Upload and index a transcript first — analysis runs on an indexed meeting.",
        )
        ui.spacer(1.2)
        left, _ = st.columns([1.3, 4])
        with left:
            if st.button("Upload a Meeting", key="analysis_to_upload", use_container_width=True):
                go("upload")
                st.rerun()
        ui.brand_quote("Decisions are only real once they are written down.")
        return

    stored = store.get(document_id)
    analysis = st.session_state.get("analysis_data") or stored.get("analysis")

    context_left, context_right = st.columns([2.4, 1.2], gap="large")
    with context_left:
        ui.chat_context(f"Analysing — {filename}", active=True)
    with context_right:
        label = "Re-run Analysis" if analysis else "Run Analysis"
        if st.button(label, key="run_analysis", use_container_width=True):
            _run_analysis(document_id)
            st.rerun()

    if st.session_state.get("notice"):
        ui.spacer(1.0)
        st.error(st.session_state.notice)

    ui.spacer(1.4)

    if not analysis:
        ui.empty_state(
            "Ready when you are",
            "Run the analysis to extract action items, decisions, deadlines and risks from "
            "this meeting. Agents run sequentially, so this takes a few minutes locally.",
        )
        ui.brand_quote("Decisions are only real once they are written down.")
        return

    if analysis.get("analysis_complete") is False:
        st.session_state.analysis_data = analysis

    _render_analysis(analysis)
    ui.brand_quote("Clarity today, progress tomorrow.")
