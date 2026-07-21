"""
Streamlit Home Page for SynkAI - Agentic AI Meeting Assistant.
Sprint 1 UI Shell featuring health indicators, disabled upload buttons, and component placeholders.
"""

import os
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="SynkAI - Agentic AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL setting
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health() -> bool:
    """
    Query the backend GET /health endpoint.

    Returns:
        bool: True if backend returns 200 OK and status == 'ok', False otherwise.
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if response.status_code == 200:
            return response.json().get("status") == "ok"
    except Exception:
        return False
    return False


def render_ui() -> None:
    """Renders the main Streamlit layout and placeholders."""

    # Custom styling
    st.markdown(
        """
        <style>
        .brand-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        .brand-subtitle {
            color: #6B7280;
            font-size: 1.1rem;
            margin-bottom: 25px;
        }
        .placeholder-card {
            border: 2px dashed #E5E7EB;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            background-color: #FAFAFA;
            color: #6B7280;
            margin-top: 15px;
            margin-bottom: 25px;
        }
        .health-online {
            background-color: #D1FAE5;
            color: #065F46;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .health-offline {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Sidebar Render
    with st.sidebar:
        st.markdown("<h2 style='margin-bottom:0;'>🎙️ SynkAI</h2>", unsafe_allow_html=True)
        st.caption("Agentic AI Meeting Assistant")
        st.divider()

        # Backend Health Status Indicator
        is_healthy = check_backend_health()
        if is_healthy:
            st.markdown(
                '<span class="health-online">🟢 Backend Status: Online</span>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span class="health-offline">🔴 Backend Status: Offline</span>',
                unsafe_allow_html=True
            )
            st.caption(f"Target API: `{BACKEND_URL}`")

        st.divider()
        st.info("ℹ️ **Sprint 1 Active**: Architecture setup & placeholder interfaces.")

    # Main Page Header
    st.markdown('<div class="brand-title">SynkAI - Agentic AI Meeting Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Powered by LangGraph, RAG, Ollama, and ChromaDB</div>', unsafe_allow_html=True)

    st.divider()

    # Upload Meeting Button (Disabled)
    st.subheader("📤 Upload Meeting Transcript or Audio")
    st.file_uploader(
        "Upload audio recording (.mp3, .wav) or text transcript (.txt)",
        type=["mp3", "wav", "txt"],
        disabled=True,
        help="Upload functionality disabled in Sprint 1."
    )
    st.button("Upload Meeting", disabled=True, use_container_width=True)
    st.caption("🔒 *Upload feature is disabled for Sprint 1. Processing pipeline will be integrated in Sprint 2.*")

    st.divider()

    # Placeholders: Summary, Action Items, Chat
    tab_summary, tab_action_items, tab_chat = st.tabs([
        "📝 Summary",
        "✅ Action Items",
        "💬 Interactive Chat"
    ])

    with tab_summary:
        st.subheader("Summary Placeholder")
        st.markdown(
            """
            <div class="placeholder-card">
                <h3>📝 Executive Summary Placeholder</h3>
                <p>Detailed meeting summaries, key topic breakdowns, and sentiment highlights will be displayed here once AI agent workflows are connected.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with tab_action_items:
        st.subheader("Action Items Placeholder")
        st.markdown(
            """
            <div class="placeholder-card">
                <h3>✅ Action Items Placeholder</h3>
                <p>Automatically extracted action items, assigned owners, and key deadlines will appear here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with tab_chat:
        st.subheader("Chat Placeholder")
        st.markdown(
            """
            <div class="placeholder-card">
                <h3>💬 RAG Meeting Chat Placeholder</h3>
                <p>Interactive vector-search Q&A powered by LangGraph, ChromaDB, and Ollama will be available here.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.chat_input("Ask a question about the meeting... (disabled in Sprint 1)", disabled=True)


if __name__ == "__main__":
    render_ui()
