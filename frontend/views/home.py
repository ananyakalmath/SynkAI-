"""
SynkAI dashboard: greeting, search, hero, feature cards, recent meetings,
quick stats and the closing brand mark.
"""

import os
from typing import Callable, Dict, List

import streamlit as st

from frontend.components import api, store, ui

USER_FIRST_NAME = os.getenv("SYNKAI_USER_NAME", "Ananya Kalmath").split()[0]

FEATURES = [
    ("summarize", "Summarize", "Upload your meeting transcript\nand get a concise summary.", "upload"),
    ("chat", "AI Chat", "Ask questions from your\nmeetings with source citations.", "chat"),
    ("analysis", "Deep Analysis", "Extract action items,\ndecisions, deadlines and risks.", "analysis"),
    ("history", "Meeting History", "View and search your\npast meetings.", "history"),
]

FEATURE_ICONS = {
    "summarize": "summarize",
    "chat": "chat",
    "analysis": "analysis",
    "history": "history",
}


def _load_meetings() -> List[Dict]:
    """
    Fetches indexed meetings and merges them with locally stored workspace state.

    Returns:
        List[Dict]: Merged meeting records, newest first.
    """
    return store.merge_with_backend(api.list_meetings())


def _render_recent(meetings: List[Dict], go: Callable[[str], None]) -> None:
    """
    Renders the Recent Meetings section from real data.

    Args:
        meetings (List[Dict]): Merged meeting records.
        go (Callable[[str], None]): Route switcher.
    """
    if ui.section_header("Recent Meetings", "View all →", "link_view_all"):
        go("history")
        st.rerun()

    ui.spacer(0.5)

    if not meetings:
        ui.empty_state(
            "No meetings yet",
            "Upload your first transcript and it will appear here with its status, "
            "date and time.",
        )
        return

    ui.meeting_list([
        ui.meeting_row_html(
            title=meeting.get("filename", "Untitled transcript"),
            meta=store.format_timestamp(meeting.get("created_at")),
            status=meeting.get("status", store.STATUS_INDEXED),
        )
        for meeting in meetings[:4]
    ])


def _render_stats(meetings: List[Dict]) -> None:
    """
    Renders Quick Stats aggregated from stored analyses.

    Args:
        meetings (List[Dict]): Merged meeting records.
    """
    ui.section_header("Quick Stats")
    ui.spacer(0.5)

    totals = store.stats(meetings)
    cards = [
        ("layers", totals["meetings"], "Total Meetings"),
        ("check", totals["action_items"], "Action Items"),
        ("gavel", totals["decisions"], "Decisions"),
        ("calendar", totals["deadlines"], "Upcoming Deadlines"),
    ]

    with st.container(key="statrow"):
        columns = st.columns(4, gap="medium")
        for column, (icon_name, value, label) in zip(columns, cards):
            with column:
                ui.stat_card(icon_name, value, label)

    if not any(totals[key] for key in ("action_items", "decisions", "deadlines")):
        ui.spacer(0.6)
        st.markdown(
            "<p class='sk-meta'>Run Meeting Analysis on a transcript to populate these figures.</p>",
            unsafe_allow_html=True,
        )


def render(go: Callable[[str], None]) -> None:
    """
    Renders the dashboard.

    Args:
        go (Callable[[str], None]): Route switcher.
    """
    ui.greeting_header(USER_FIRST_NAME)
    ui.spacer(1.4)

    search = st.text_input(
        "Search",
        value=st.session_state.get("search_query", ""),
        placeholder="Search meetings...",
        label_visibility="collapsed",
        key="home_search",
    )
    if search != st.session_state.get("search_query"):
        st.session_state.search_query = search

    if search.strip():
        ui.spacer(0.8)
        matches = [
            meeting for meeting in _load_meetings()
            if search.strip().lower() in (meeting.get("filename") or "").lower()
        ]
        if matches:
            st.markdown(
                f"<p class='sk-meta'>{len(matches)} meeting(s) matching “{ui.esc(search.strip())}”</p>",
                unsafe_allow_html=True,
            )
            ui.spacer(0.4)
            ui.meeting_list([
                ui.meeting_row_html(
                    title=meeting.get("filename", "Untitled transcript"),
                    meta=store.format_timestamp(meeting.get("created_at")),
                    status=meeting.get("status", store.STATUS_INDEXED),
                )
                for meeting in matches[:5]
            ])
        else:
            st.markdown(
                f"<p class='sk-meta'>No meetings match “{ui.esc(search.strip())}”.</p>",
                unsafe_allow_html=True,
            )

    ui.spacer(1.6)

    st.markdown(ui.hero_background_css(), unsafe_allow_html=True)
    with st.container(key="herowrap"):
        ui.hero_copy()
        ui.spacer(1.5)
        action_left, action_right, _ = st.columns([1.3, 1, 3.3], gap="small")
        with action_left:
            if st.button("Upload a Meeting", key="hero_upload", use_container_width=True):
                go("upload")
                st.rerun()
        with action_right:
            if st.button("Learn more →", key="quiet_learn_more", use_container_width=True):
                go("settings")
                st.rerun()

    ui.rule()

    with st.container(key="cardrow"):
        columns = st.columns(4, gap="medium")
        for column, (key, title, body, target) in zip(columns, FEATURES):
            with column:
                if ui.feature_card(FEATURE_ICONS[key], title, body, key):
                    go(target)
                    st.rerun()

    ui.rule()

    meetings = _load_meetings()
    _render_recent(meetings, go)
    ui.spacer(2.4)
    _render_stats(meetings)
    ui.brand_quote()
