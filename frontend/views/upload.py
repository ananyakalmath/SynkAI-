"""
Upload & Summarize.

Saves the transcript (/upload), indexes it for chat and analysis (/chat/upload), then
generates the executive summary (/summarize) — the same backend calls as before, presented
as one calm sequence.
"""

from typing import Callable, Dict, List, Optional

import streamlit as st

from frontend.components import api, store, ui
from frontend.components.api import MEDIA_UPLOAD_TIMEOUT

SUPPORTED = (
    "txt", "pdf", "docx",
    "mp4", "mov", "mkv", "webm", "avi", "m4v",
    "mp3", "wav", "m4a", "aac", "flac", "ogg",
)
MEDIA_EXTENSIONS = {"mp4", "mov", "mkv", "webm", "avi", "m4v", "mp3", "wav", "m4a", "aac", "flac", "ogg"}


def _process(uploaded_file) -> None:
    """
    Runs upload → index → summarize for the selected file, storing results in state.

    Args:
        uploaded_file: Streamlit UploadedFile instance.
    """
    data = uploaded_file.getvalue()
    name = uploaded_file.name
    content_type = uploaded_file.type
    is_media = name.rsplit(".", 1)[-1].lower() in MEDIA_EXTENSIONS if "." in name else False

    st.session_state.notice = None
    st.session_state.upload_info = None
    st.session_state.summary_data = None

    parsing_label = (
        "Transcribing audio locally with Whisper — this can take a few minutes..."
        if is_media
        else "Saving and parsing the transcript..."
    )

    try:
        with st.spinner(parsing_label):
            upload_info = api.upload_transcript(
                name, data, content_type,
                timeout=MEDIA_UPLOAD_TIMEOUT if is_media else None,
            )
        st.session_state.upload_info = upload_info

        with st.spinner("Generating embeddings and indexing into ChromaDB..."):
            indexed = api.index_transcript(
                name, data, content_type,
                timeout=MEDIA_UPLOAD_TIMEOUT if is_media else None,
            )

        document_id = indexed.get("document_id")
        st.session_state.active_document_id = document_id
        st.session_state.active_filename = name
        st.session_state.chat_history = []
        st.session_state.analysis_data = None

        store.record_meeting(
            document_id=document_id,
            filename=name,
            number_of_chunks=indexed.get("number_of_chunks", 0),
            character_count=upload_info.get("character_count"),
        )

        with st.spinner("Writing the executive summary with qwen3 — this can take a few minutes..."):
            summary = api.summarize(filename=upload_info.get("filename"))

        st.session_state.summary_data = summary
        store.save_summary(document_id, summary)

    except api.BackendError as exc:
        st.session_state.notice = str(exc)


def _render_summary(summary: Dict) -> None:
    """
    Renders the three summary sections as editorial panels.

    Args:
        summary (Dict): SummaryResponse payload.
    """
    ui.panel(
        "Executive Summary",
        ui.prose(summary.get("executive_summary", "")),
        icon_name="sparkle",
    )

    points: List[str] = summary.get("key_discussion_points") or []
    if points:
        ui.panel(
            "Key Discussion Points",
            ui.numbered_list(points),
            icon_name="layers",
            count=f"{len(points)} points",
        )

    ui.panel(
        "Meeting Outcome",
        ui.prose(summary.get("meeting_outcome", "")),
        icon_name="check",
    )

    model = summary.get("model_used", "qwen3")
    st.markdown(
        f"<p class='sk-meta' style='margin-top:.6rem'>Generated locally by {ui.esc(model)} via Ollama.</p>",
        unsafe_allow_html=True,
    )


def render(go: Callable[[str], None]) -> None:
    """
    Renders the Upload & Summarize page.

    Args:
        go (Callable[[str], None]): Route switcher.
    """
    ui.page_header(
        "Workspace",
        "Upload & Summarize",
        "Bring in a transcript, or a recorded video/audio meeting, and SynkAI will index "
        "it for chat and analysis, then write a concise executive summary.",
    )
    ui.rule()

    left, right = st.columns([2.1, 1], gap="large")

    with left:
        uploaded_file = st.file_uploader(
            "Transcript",
            type=list(SUPPORTED),
            label_visibility="collapsed",
            key="upload_file",
        )
        ui.spacer(0.4)
        st.markdown(
            "<p class='sk-meta'>Documents — TXT, PDF, DOCX (up to 10 MB) &nbsp;·&nbsp; "
            "Recordings — MP4, MOV, MKV, WEBM, AVI, MP3, WAV, M4A (up to 500 MB, "
            "transcribed locally with Whisper)</p>",
            unsafe_allow_html=True,
        )

        ui.spacer(1.0)
        if st.button(
            "Process Meeting",
            key="process_meeting",
            disabled=uploaded_file is None,
            use_container_width=False,
        ):
            _process(uploaded_file)
            st.rerun()

    with right:
        active: Optional[str] = st.session_state.get("active_filename")
        upload_info = st.session_state.get("upload_info") or {}
        if uploaded_file is not None:
            size_kb = len(uploaded_file.getvalue()) / 1024
            detail = f"{uploaded_file.name}<br/><span class='sk-meta'>{size_kb:,.0f} KB selected</span>"
        elif active:
            characters = upload_info.get("character_count")
            suffix = f"{characters:,} characters parsed" if characters else "Ready for chat and analysis"
            detail = f"{ui.esc(active)}<br/><span class='sk-meta'>{suffix}</span>"
        else:
            detail = "<span class='sk-meta'>No transcript selected yet.</span>"

        st.markdown(
            f"""
            <div class="sk-panel" style="margin:0">
              <p class="sk-eyebrow">Selected file</p>
              <p style="font-size:.9rem;color:#2E2E2C;margin:.55rem 0 0 0;line-height:1.5">{detail}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.get("notice"):
        ui.spacer(1.0)
        st.error(st.session_state.notice)

    summary = st.session_state.get("summary_data")
    if summary:
        ui.rule()
        ui.section_header("Summary")
        ui.spacer(0.7)
        _render_summary(summary)

        ui.spacer(1.2)
        action_left, action_right, _ = st.columns([1.3, 1.1, 3.6], gap="small")
        with action_left:
            if st.button("Run Deep Analysis", key="to_analysis", use_container_width=True):
                go("analysis")
                st.rerun()
        with action_right:
            if st.button("Ask a question →", key="quiet_to_chat", use_container_width=True):
                go("chat")
                st.rerun()
    elif not st.session_state.get("notice"):
        ui.rule()
        ui.empty_state(
            "Your summary will appear here",
            "Executive Summary, Key Discussion Points and Meeting Outcome are generated "
            "locally with qwen3 once a transcript is processed.",
        )

    ui.brand_quote("Every meeting deserves a clear record.")
