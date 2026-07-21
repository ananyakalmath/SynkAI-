"""
Streamlit Home Page for SynkAI - Agentic AI Meeting Assistant.
Sprint 2: Transcript File Upload (TXT, PDF, DOCX) and AI Summarization powered by Ollama.
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

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health() -> bool:
    """Query the backend GET /health endpoint."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if response.status_code == 200:
            return response.json().get("status") == "ok"
    except Exception:
        return False
    return False


def upload_file_to_backend(uploaded_file) -> dict:
    """
    Sends the uploaded file binary stream to backend POST /upload.

    Returns:
        dict: Server response payload on success.

    Raises:
        RuntimeError: On HTTP error or failure.
    """
    url = f"{BACKEND_URL}/upload"
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

    response = requests.post(url, files=files, timeout=30)
    if response.status_code in (200, 201):
        return response.json()
    else:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Upload failed (HTTP {response.status_code}): {detail}")


def request_summary_from_backend(filename: str = None, transcript_text: str = None) -> dict:
    """
    Requests AI summarization from backend POST /summarize.

    Returns:
        dict: Structured summary data.
    """
    url = f"{BACKEND_URL}/summarize"
    payload = {}
    if filename:
        payload["filename"] = filename
    if transcript_text:
        payload["transcript_text"] = transcript_text

    response = requests.post(url, json=payload, timeout=120)
    if response.status_code == 200:
        return response.json()
    else:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Summarization failed (HTTP {response.status_code}): {detail}")


def render_ui() -> None:
    """Main UI rendering function."""

    # Initialize Session State
    if "upload_info" not in st.session_state:
        st.session_state.upload_info = None
    if "summary_data" not in st.session_state:
        st.session_state.summary_data = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None

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
        .summary-box {
            background-color: #F8FAFC;
            border-left: 5px solid #6366F1;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .outcome-box {
            background-color: #F0FDF4;
            border-left: 5px solid #22C55E;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
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

        # Backend Health Status
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
        st.info("⚡ **Sprint 2 Active**: TXT, PDF, & DOCX Ingestion with Ollama AI Summarization (`qwen3`).")

    # Main Header
    st.markdown('<div class="brand-title">SynkAI - Agentic AI Meeting Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Automated transcript parsing and AI executive summarization</div>', unsafe_allow_html=True)

    st.divider()

    # Section 1: File Ingestion & Action Controls
    st.subheader("📤 Upload Meeting Transcript")

    uploaded_file = st.file_uploader(
        "Select a meeting transcript file (.txt, .pdf, .docx)",
        type=["txt", "pdf", "docx"],
        help="Upload text or document transcript to generate structured summaries."
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        process_btn = st.button("🚀 Upload & Summarize", use_container_width=True, disabled=uploaded_file is None)

    if process_btn and uploaded_file is not None:
        st.session_state.error_message = None
        st.session_state.summary_data = None

        with st.spinner("Step 1/2: Uploading and parsing document..."):
            try:
                upload_res = upload_file_to_backend(uploaded_file)
                st.session_state.upload_info = upload_res
                st.toast(f"✅ Uploaded '{upload_res['filename']}' successfully!", icon="📄")
            except Exception as exc:
                st.session_state.error_message = f"Upload Error: {str(exc)}"

        if st.session_state.upload_info and not st.session_state.error_message:
            with st.spinner("Step 2/2: Generating AI Summary using Ollama (qwen3)..."):
                try:
                    summary_res = request_summary_from_backend(filename=st.session_state.upload_info["filename"])
                    st.session_state.summary_data = summary_res
                    st.toast("🎉 Executive Summary Generated!", icon="🤖")
                except Exception as exc:
                    st.session_state.error_message = f"Summarization Error: {str(exc)}"

    # Render Errors if any
    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    # Render Upload Info Metadata
    if st.session_state.upload_info:
        u_info = st.session_state.upload_info
        st.success(f"📄 **Current Active Transcript**: `{u_info['filename']}` ({u_info['character_count']} characters extracted)")
        with st.expander("Preview Extracted Raw Text Sample"):
            st.text(u_info["sample_text"])

    st.divider()

    # Section 2: Summary & Workspace Tabs
    tab_summary, tab_action_items, tab_chat = st.tabs([
        "📝 Meeting Summary",
        "✅ Action Items",
        "💬 Interactive Chat"
    ])

    with tab_summary:
        if st.session_state.summary_data:
            s_data = st.session_state.summary_data

            st.subheader("📌 Executive Summary")
            st.markdown(
                f"""
                <div class="summary-box">
                    {s_data['executive_summary']}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.subheader("💡 Key Discussion Points")
            for idx, point in enumerate(s_data.get("key_discussion_points", []), 1):
                st.markdown(f"**{idx}.** {point}")

            st.write("")
            st.subheader("🎯 Meeting Outcome & Decisions")
            st.markdown(
                f"""
                <div class="outcome-box">
                    {s_data['meeting_outcome']}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(f"🤖 Summary generated by **{s_data.get('model_used', 'qwen3')}**")
        else:
            st.markdown(
                """
                <div class="placeholder-card">
                    <h3>📝 Executive Summary Placeholder</h3>
                    <p>Upload a meeting transcript (.txt, .pdf, or .docx) and click <b>Upload & Summarize</b> to generate AI summaries here.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_action_items:
        st.subheader("Action Items (Coming in Sprint 3)")
        st.markdown(
            """
            <div class="placeholder-card">
                <h3>✅ Action Items Placeholder</h3>
                <p>Action item extraction and owner assignment will be connected in upcoming sprints.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with tab_chat:
        st.subheader("Interactive Chat (Coming in Sprint 4)")
        st.markdown(
            """
            <div class="placeholder-card">
                <h3>💬 RAG Meeting Chat Placeholder</h3>
                <p>Q&A powered by LangGraph, ChromaDB, and Ollama will be available in future sprints.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.chat_input("Ask a question about the meeting... (disabled)", disabled=True)


if __name__ == "__main__":
    render_ui()
