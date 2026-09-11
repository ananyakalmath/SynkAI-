"""
Settings.

A quiet, read-mostly view of how this SynkAI workspace is wired: the backend it talks to,
the local models in use, and where data is stored.
"""

import os
from typing import Callable

import streamlit as st

from frontend.components import api, store, ui


def _definition(label: str, value: str) -> str:
    """
    Builds one label/value row for a settings panel.

    Args:
        label (str): Small uppercase label.
        value (str): Displayed value.

    Returns:
        str: Row markup.
    """
    return (
        "<div style='display:flex;justify-content:space-between;gap:2rem;"
        "padding:.72rem 0;border-top:1px solid #E8E2D9'>"
        f"<span style='font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;"
        f"color:#8C857A'>{ui.esc(label)}</span>"
        f"<span style='font-size:.85rem;color:#2E2E2C;text-align:right'>{ui.esc(value)}</span>"
        "</div>"
    )


def render(go: Callable[[str], None]) -> None:
    """
    Renders the Settings page.

    Args:
        go (Callable[[str], None]): Route switcher.
    """
    ui.page_header(
        "Configuration",
        "Settings",
        "SynkAI runs entirely on your machine. Nothing leaves this computer.",
    )
    ui.rule()

    online = api.is_backend_online()
    meetings = store.merge_with_backend(api.list_meetings())

    left, right = st.columns(2, gap="large")

    with left:
        rows = "".join([
            _definition("Backend", api.BACKEND_URL),
            _definition("Status", "Online" if online else "Offline"),
            _definition("Indexed meetings", str(len(meetings))),
        ])
        ui.panel("Connection", rows, icon_name="layers")

        rows = "".join([
            _definition("Workspace owner", os.getenv("SYNKAI_USER_NAME", "Ananya Kalmath")),
            _definition("Records file", store.STORE_PATH),
        ])
        ui.panel("Workspace", rows, icon_name="user")

    with right:
        rows = "".join([
            _definition("Language model", os.getenv("OLLAMA_MODEL", "qwen3")),
            _definition("Embeddings", os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")),
            _definition("Inference", "Ollama · local"),
            _definition("Concurrency", f"{os.getenv('OLLAMA_MAX_CONCURRENCY', '1')} request at a time"),
        ])
        ui.panel("Models", rows, icon_name="sparkle")

        rows = "".join([
            _definition("Vector store", "ChromaDB · persistent"),
            _definition("Collection", os.getenv("CHROMA_COLLECTION_NAME", "meeting_documents")),
            _definition("Retrieval", "Top-5 chunks, scoped per meeting"),
        ])
        ui.panel("Retrieval", rows, icon_name="search")

    ui.spacer(1.4)
    ui.section_header("How SynkAI works")
    ui.spacer(0.7)
    ui.panel(
        "The pipeline",
        ui.numbered_list([
            "A transcript is parsed from TXT, PDF or DOCX and saved to your uploads folder.",
            "It is split into overlapping chunks, embedded with nomic-embed-text and stored in ChromaDB.",
            "Summaries are written by qwen3 running locally through Ollama.",
            "AI Chat retrieves the five most relevant passages for each question and cites them.",
            "Meeting Analysis runs seven specialised agents in sequence through LangGraph.",
        ]),
        icon_name="analysis",
    )

    ui.spacer(1.2)
    left, _ = st.columns([1.3, 4])
    with left:
        if st.button("Back to Home", key="outline_settings_home", use_container_width=True):
            go("home")
            st.rerun()

    ui.brand_quote("Private by design. Local by default.")
