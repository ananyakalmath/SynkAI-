"""
Meeting History.

Search and filter every indexed meeting, then open one to continue in chat or analysis.
Rows come from GET /meetings merged with locally stored workspace state.
"""

from typing import Callable, Dict, List

import streamlit as st

from frontend.components import api, store, ui

FILTERS = ["All", store.STATUS_ANALYSED, store.STATUS_SUMMARISED, store.STATUS_INDEXED]


def _filtered(meetings: List[Dict], query: str, status: str) -> List[Dict]:
    """
    Applies the search query and status filter.

    Args:
        meetings (List[Dict]): Merged meeting records.
        query (str): Search text matched against the file name.
        status (str): Status filter, or "All".

    Returns:
        List[Dict]: Matching meetings.
    """
    needle = query.strip().lower()
    results = []

    for meeting in meetings:
        if needle and needle not in (meeting.get("filename") or "").lower():
            continue
        if status != "All" and meeting.get("status", store.STATUS_INDEXED) != status:
            continue
        results.append(meeting)

    return results


def _open(meeting: Dict, route: str, go: Callable[[str], None]) -> None:
    """
    Makes a meeting active and navigates to the given page.

    Args:
        meeting (Dict): Meeting record.
        route (str): Destination route key.
        go (Callable[[str], None]): Route switcher.
    """
    st.session_state.active_document_id = meeting.get("document_id")
    st.session_state.active_filename = meeting.get("filename")
    st.session_state.chat_history = []
    st.session_state.analysis_data = (meeting.get("analysis") or None)
    st.session_state.summary_data = (meeting.get("summary") or None)
    go(route)
    st.rerun()


def render(go: Callable[[str], None]) -> None:
    """
    Renders the Meeting History page.

    Args:
        go (Callable[[str], None]): Route switcher.
    """
    ui.page_header(
        "Archive",
        "Meeting History",
        "Every transcript SynkAI has indexed, with what has already been summarised or analysed.",
    )
    ui.rule()

    search_column, filter_column = st.columns([2.6, 1], gap="large")
    with search_column:
        query = st.text_input(
            "Search",
            value=st.session_state.get("search_query", ""),
            placeholder="Search meetings...",
            label_visibility="collapsed",
            key="history_search",
        )
    with filter_column:
        status = st.selectbox(
            "Status",
            FILTERS,
            index=FILTERS.index(st.session_state.get("history_filter", "All")),
            label_visibility="collapsed",
            key="history_status",
        )

    st.session_state.search_query = query
    st.session_state.history_filter = status

    meetings = store.merge_with_backend(api.list_meetings())
    results = _filtered(meetings, query, status)

    ui.spacer(1.2)

    if not meetings:
        ui.empty_state(
            "No meetings indexed yet",
            "Once you process a transcript it will be listed here with its status and date.",
        )
        ui.brand_quote("A quiet archive of everything decided.")
        return

    st.markdown(
        f"<p class='sk-meta'>{len(results)} of {len(meetings)} meetings</p>",
        unsafe_allow_html=True,
    )
    ui.spacer(0.6)

    if not results:
        ui.empty_state("Nothing matches those filters", "Try a different search term or status.")
        ui.brand_quote("A quiet archive of everything decided.")
        return

    for meeting in results:
        document_id = meeting.get("document_id") or "unknown"
        row, action = st.columns([4.4, 1], gap="small", vertical_alignment="center")

        with row:
            chunks = meeting.get("number_of_chunks") or 0
            chunk_note = f" · {chunks} chunks" if chunks else ""
            ui.meeting_card(
                title=meeting.get("filename", "Untitled transcript"),
                meta=f"{store.format_timestamp(meeting.get('created_at'))}{chunk_note}",
                status=meeting.get("status", store.STATUS_INDEXED),
            )
        with action:
            target = "analysis" if meeting.get("analysis") else "chat"
            if st.button("Open →", key=f"quiet_open_{document_id}", use_container_width=True):
                _open(meeting, target, go)

    ui.brand_quote("A quiet archive of everything decided.")
