"""
AI Chat.

SynkAI's own assistant surface over the existing Sprint 3 RAG pipeline: retrieval stays
scoped to the active `document_id` and every answer keeps its source citations.
"""

from typing import Callable, List

import streamlit as st

from frontend.components import api, store, ui

SUGGESTIONS = [
    "What was decided?",
    "Who owns which task?",
    "When are the deadlines?",
    "What are the open risks?",
]


def _meeting_picker() -> None:
    """
    Lets the user scope the conversation to any indexed meeting.
    """
    meetings = store.merge_with_backend(api.list_meetings())
    if not meetings:
        return

    options = {
        f"{meeting.get('filename', 'Untitled transcript')}": meeting.get("document_id")
        for meeting in meetings
    }
    labels = list(options.keys())

    current_id = st.session_state.get("active_document_id")
    current_index = 0
    for index, label in enumerate(labels):
        if options[label] == current_id:
            current_index = index
            break

    chosen = st.selectbox(
        "Meeting",
        labels,
        index=current_index,
        key="chat_meeting_select",
        label_visibility="collapsed",
    )
    chosen_id = options[chosen]
    if chosen_id != current_id:
        st.session_state.active_document_id = chosen_id
        st.session_state.active_filename = chosen
        st.session_state.chat_history = []
        st.rerun()


def _answer(question: str) -> None:
    """
    Sends a question through the RAG endpoint and appends the exchange to history.

    Args:
        question (str): User question.
    """
    document_id = st.session_state.get("active_document_id")
    st.session_state.chat_history.append({"role": "user", "content": question})

    try:
        with st.spinner("Searching this meeting and composing an answer..."):
            result = api.ask(document_id, question)
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result.get("answer", ""),
            "sources": result.get("sources", []),
        })
    except api.BackendError as exc:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": None,
            "error": str(exc),
        })


def render(go: Callable[[str], None]) -> None:
    """
    Renders the AI Chat page.

    Args:
        go (Callable[[str], None]): Route switcher.
    """
    ui.page_header(
        "Assistant",
        "AI Chat",
        "Ask anything about a meeting. Answers are grounded in the indexed transcript and "
        "always cite the passages they came from.",
    )
    ui.spacer(1.0)

    document_id = st.session_state.get("active_document_id")
    filename = st.session_state.get("active_filename")

    context_left, context_right = st.columns([2.4, 1.4], gap="large")
    with context_left:
        ui.chat_context(
            f"Discussing — {filename}" if document_id else "No meeting indexed yet",
            active=bool(document_id),
        )
    with context_right:
        if document_id:
            _meeting_picker()

    ui.rule()

    if not document_id:
        ui.empty_state(
            "Index a meeting to start chatting",
            "Upload a transcript first — SynkAI keeps every answer scoped to that meeting "
            "so citations stay meaningful.",
        )
        ui.spacer(1.2)
        left, _ = st.columns([1.3, 4])
        with left:
            if st.button("Upload a Meeting", key="chat_to_upload", use_container_width=True):
                go("upload")
                st.rerun()
        ui.brand_quote("Ask better questions, get clearer answers.")
        return

    history: List[dict] = st.session_state.get("chat_history", [])

    if not history:
        st.markdown("<p class='sk-eyebrow'>Try asking</p>", unsafe_allow_html=True)
        ui.spacer(0.5)
        columns = st.columns(len(SUGGESTIONS), gap="small")
        for column, suggestion in zip(columns, SUGGESTIONS):
            with column:
                if st.button(suggestion, key=f"outline_sugg_{suggestion}", use_container_width=True):
                    st.session_state.pending_question = suggestion
                    st.rerun()
        ui.spacer(1.4)

    for message in history:
        if message["role"] == "user":
            ui.user_message(message["content"])
        elif message.get("error"):
            st.error(message["error"])
        else:
            ui.ai_message(message.get("content", ""), message.get("sources"))
        ui.spacer(0.75)

    question = st.chat_input("Ask anything about this meeting...")
    pending = st.session_state.pop("pending_question", None) if st.session_state.get("pending_question") else None
    active_question = question or pending

    if active_question:
        _answer(active_question)
        st.rerun()

    if history:
        ui.spacer(0.6)
        left, _ = st.columns([1.2, 4.5])
        with left:
            if st.button("Clear conversation", key="outline_clear_chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
