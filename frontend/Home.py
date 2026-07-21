"""
Streamlit Home Page for SynkAI - Agentic AI Meeting Assistant.
Sprint 3: RAG Chat with ChromaDB & Ollama (nomic-embed-text + qwen3).
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
    """Sends the uploaded file stream to backend POST /upload."""
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


def index_file_in_chromadb(filename: str) -> dict:
    """Triggers backend POST /chat/upload to index transcript into ChromaDB."""
    url = f"{BACKEND_URL}/chat/upload"
    response = requests.post(url, json={"filename": filename}, timeout=120)
    if response.status_code == 200:
        return response.json()
    else:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"ChromaDB Indexing failed (HTTP {response.status_code}): {detail}")


def request_summary_from_backend(filename: str = None, transcript_text: str = None) -> dict:
    """Requests AI summary from backend POST /summarize."""
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


def send_chat_query(question: str, filename: str = None) -> dict:
    """Sends a question to backend POST /chat/query for RAG answer."""
    url = f"{BACKEND_URL}/chat/query"
    payload = {"question": question}
    if filename:
        payload["filename"] = filename

    response = requests.post(url, json=payload, timeout=90)
    if response.status_code == 200:
        return response.json()
    else:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Chat query failed (HTTP {response.status_code}): {detail}")


def render_ui() -> None:
    """Main Streamlit UI renderer."""

    # Session State Initialization
    if "upload_info" not in st.session_state:
        st.session_state.upload_info = None
    if "summary_data" not in st.session_state:
        st.session_state.summary_data = None
    if "chat_indexed" not in st.session_state:
        st.session_state.chat_indexed = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

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
        st.info("🧠 **Sprint 3 RAG Active**: ChromaDB Vector Store + Ollama Embeddings (`nomic-embed-text`) & LLM (`qwen3`).")

    # Header
    st.markdown('<div class="brand-title">SynkAI - Agentic AI Meeting Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">RAG Meeting Intelligence powered by LangGraph, ChromaDB, & Ollama</div>', unsafe_allow_html=True)

    st.divider()

    # Section 1: Upload Transcript
    st.subheader("📤 Upload Meeting Transcript")
    uploaded_file = st.file_uploader(
        "Select meeting transcript (.txt, .pdf, .docx)",
        type=["txt", "pdf", "docx"],
        help="Upload document to generate summaries and chat with your meeting."
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        process_btn = st.button("🚀 Process & Index Meeting", use_container_width=True, disabled=uploaded_file is None)

    if process_btn and uploaded_file is not None:
        st.session_state.error_message = None
        st.session_state.summary_data = None
        st.session_state.chat_indexed = False
        st.session_state.chat_history = []

        # Step 1: Upload file
        with st.spinner("Step 1/3: Saving and parsing document..."):
            try:
                upload_res = upload_file_to_backend(uploaded_file)
                st.session_state.upload_info = upload_res
                st.toast(f"✅ Uploaded '{upload_res['filename']}'", icon="📄")
            except Exception as exc:
                st.session_state.error_message = f"Upload Error: {str(exc)}"

        # Step 2: Index into ChromaDB
        if st.session_state.upload_info and not st.session_state.error_message:
            with st.spinner("Step 2/3: Generating embeddings (nomic-embed-text) & indexing into ChromaDB..."):
                try:
                    chroma_res = index_file_in_chromadb(st.session_state.upload_info["filename"])
                    st.session_state.chat_indexed = True
                    st.toast(f"🧠 Indexed {chroma_res['vectors_stored']} vectors into ChromaDB!", icon="⚡")
                except Exception as exc:
                    st.session_state.error_message = f"ChromaDB Indexing Error: {str(exc)}"

        # Step 3: Summarize
        if st.session_state.chat_indexed and not st.session_state.error_message:
            with st.spinner("Step 3/3: Generating Executive Summary via Ollama (qwen3)..."):
                try:
                    summary_res = request_summary_from_backend(filename=st.session_state.upload_info["filename"])
                    st.session_state.summary_data = summary_res
                    st.toast("🎉 Meeting processing complete!", icon="🤖")
                except Exception as exc:
                    st.session_state.error_message = f"Summarization Error: {str(exc)}"

    if st.session_state.error_message:
        st.error(st.session_state.error_message)

    if st.session_state.upload_info:
        u_info = st.session_state.upload_info
        st.success(f"📄 **Active Meeting Transcript**: `{u_info['filename']}` ({u_info['character_count']} characters)")

    st.divider()

    # Section 2: Workspace Tabs
    tab_summary, tab_chat, tab_action_items = st.tabs([
        "📝 Meeting Summary",
        "💬 Interactive Chat",
        "✅ Action Items"
    ])

    # --- TAB 1: SUMMARY ---
    with tab_summary:
        if st.session_state.summary_data:
            s_data = st.session_state.summary_data
            st.subheader("📌 Executive Summary")
            st.markdown(f'<div class="summary-box">{s_data["executive_summary"]}</div>', unsafe_allow_html=True)

            st.subheader("💡 Key Discussion Points")
            for idx, point in enumerate(s_data.get("key_discussion_points", []), 1):
                st.markdown(f"**{idx}.** {point}")

            st.write("")
            st.subheader("🎯 Meeting Outcome & Decisions")
            st.markdown(f'<div class="outcome-box">{s_data["meeting_outcome"]}</div>', unsafe_allow_html=True)
            st.caption(f"🤖 Summary generated by **{s_data.get('model_used', 'qwen3')}**")
        else:
            st.markdown(
                """
                <div class="placeholder-card">
                    <h3>📝 Executive Summary Placeholder</h3>
                    <p>Upload a meeting transcript (.txt, .pdf, or .docx) and click <b>Process & Index Meeting</b> to generate AI summaries.</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- TAB 2: INTERACTIVE RAG CHAT ---
    with tab_chat:
        st.subheader("Ask questions about this meeting")
        st.caption("Contextually powered by ChromaDB vector search and Ollama `qwen3`.")

        # Sample Question Buttons / Chips
        st.markdown("**Example questions:**")
        ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(4)

        with ex_col1:
            if st.button("Who owns the embeddings task?", use_container_width=True):
                st.session_state.pending_question = "Who owns the embeddings task?"
        with ex_col2:
            if st.button("What was decided?", use_container_width=True):
                st.session_state.pending_question = "What was decided?"
        with ex_col3:
            if st.button("When is the deadline?", use_container_width=True):
                st.session_state.pending_question = "When is the deadline?"
        with ex_col4:
            if st.button("Summarize Mike's work.", use_container_width=True):
                st.session_state.pending_question = "Summarize Mike's work."

        st.write("")

        # Render Chat History
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("sources"):
                    with st.expander("📌 Retrieved Vector Sources"):
                        for s_idx, src in enumerate(msg["sources"], 1):
                            st.markdown(f"**Chunk #{src.get('chunk_number', s_idx)}** (`{src.get('filename')}`):")
                            st.caption(src.get("text"))

        # Chat Input Box
        user_input = st.chat_input("Ask a question about this meeting...")

        # Determine active prompt
        active_prompt = user_input or st.session_state.pending_question
        st.session_state.pending_question = None

        if active_prompt:
            # Append user message
            st.session_state.chat_history.append({"role": "user", "content": active_prompt})
            with st.chat_message("user"):
                st.write(active_prompt)

            # Generate response from backend
            with st.chat_message("assistant"):
                with st.spinner("Searching ChromaDB & synthesizing answer with Ollama..."):
                    try:
                        active_filename = st.session_state.upload_info["filename"] if st.session_state.upload_info else None
                        res = send_chat_query(question=active_prompt, filename=active_filename)
                        answer_text = res.get("answer", "No answer generated.")
                        sources_list = res.get("sources", [])

                        st.write(answer_text)
                        if sources_list:
                            with st.expander("📌 Retrieved Vector Sources"):
                                for s_idx, src in enumerate(sources_list, 1):
                                    st.markdown(f"**Chunk #{src.get('chunk_number', s_idx)}** (`{src.get('filename')}`):")
                                    st.caption(src.get("text"))

                        # Save to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer_text,
                            "sources": sources_list
                        })
                    except Exception as exc:
                        st.error(f"Chat Error: {str(exc)}")

    # --- TAB 3: ACTION ITEMS ---
    with tab_action_items:
        st.subheader("Action Items (Coming in Sprint 4)")
        st.markdown(
            """
            <div class="placeholder-card">
                <h3>✅ Action Items Placeholder</h3>
                <p>Extracted task assignments and action item trackers will be connected in future sprints.</p>
            </div>
            """,
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    render_ui()
