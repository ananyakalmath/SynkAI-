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

# Sequential multi-agent analysis over a local Ollama server takes minutes, not seconds.
ANALYSIS_TIMEOUT_SECONDS = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "900"))


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


def index_file_in_chromadb(uploaded_file) -> dict:
    """Triggers backend POST /chat/upload to index transcript into ChromaDB."""
    url = f"{BACKEND_URL}/chat/upload"
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    response = requests.post(url, files=files, timeout=120)
    if response.status_code in (200, 201):
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


def request_analysis_from_backend(document_id: str) -> dict:
    """Requests meeting analysis from backend POST /meeting/analyze."""
    url = f"{BACKEND_URL}/meeting/analyze"
    # The multi-agent workflow runs its LLM agents one at a time on the local Ollama
    # server, so the total wall-clock time is the sum of the agents, not the slowest one.
    response = requests.post(url, json={"document_id": document_id}, timeout=ANALYSIS_TIMEOUT_SECONDS)
    if response.status_code == 200:
        return response.json()
    else:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(f"Meeting analysis failed (HTTP {response.status_code}): {detail}")


def send_chat_query(question: str, document_id: str) -> dict:
    """Sends a question to backend POST /chat/query for RAG answer."""

    url = f"{BACKEND_URL}/chat/query"
    payload = {"question": question, "document_id": document_id}

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
    if "document_id" not in st.session_state:
        st.session_state.document_id = None
    if "summary_data" not in st.session_state:
        st.session_state.summary_data = None
    if "analysis_data" not in st.session_state:
        st.session_state.analysis_data = None
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
        st.session_state.analysis_data = None
        st.session_state.document_id = None
        st.session_state.chat_indexed = False
        st.session_state.chat_history = []

        # Step 1: Upload file
        with st.spinner("Step 1/4: Saving and parsing document..."):
            try:
                upload_res = upload_file_to_backend(uploaded_file)
                st.session_state.upload_info = upload_res
                st.toast(f"✅ Uploaded '{upload_res['filename']}'", icon="📄")
            except Exception as exc:
                st.session_state.error_message = f"Upload Error: {str(exc)}"

        # Step 2: Index into ChromaDB
        if st.session_state.upload_info and not st.session_state.error_message:
            with st.spinner("Step 2/4: Generating embeddings (nomic-embed-text) & indexing into ChromaDB..."):
                try:
                    chroma_res = index_file_in_chromadb(uploaded_file)
                    st.session_state.document_id = chroma_res.get("document_id")
                    st.session_state.chat_indexed = True
                    st.toast(f"🧠 Indexed {chroma_res['number_of_chunks']} chunks into ChromaDB!", icon="⚡")
                except Exception as exc:
                    st.session_state.error_message = f"ChromaDB Indexing Error: {str(exc)}"

        # Step 3: Summarize
        if st.session_state.chat_indexed and not st.session_state.error_message:
            with st.spinner("Step 3/4: Generating Executive Summary via Ollama (qwen3)..."):
                try:
                    summary_res = request_summary_from_backend(filename=st.session_state.upload_info["filename"])
                    st.session_state.summary_data = summary_res
                except Exception as exc:
                    st.session_state.error_message = f"Summarization Error: {str(exc)}"

        # Step 4: Multi-Agent Analysis
        if st.session_state.chat_indexed and st.session_state.document_id and not st.session_state.error_message:
            with st.spinner("Step 4/4: Running multi-agent LangGraph analysis..."):
                try:
                    analysis_res = request_analysis_from_backend(document_id=st.session_state.document_id)
                    st.session_state.analysis_data = analysis_res
                    st.toast("🎉 Meeting processing & multi-agent analysis complete!", icon="🧠")
                except Exception as exc:
                    st.session_state.error_message = f"Analysis Error: {str(exc)}"



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

            # Sprint 4 Multi-Agent Analysis
            if st.session_state.analysis_data:
                st.divider()
                st.header("🧠 Multi-Agent Analysis")
                ana_data = st.session_state.analysis_data

                # Make partial results obvious instead of showing empty sections as success.
                agent_errors = ana_data.get("agent_errors", [])
                if agent_errors:
                    st.warning(
                        "⚠️ Partial analysis: "
                        + "; ".join(f"**{err.get('agent')}** — {err.get('error')}" for err in agent_errors)
                    )

                st.subheader("📝 Executive Summary")
                st.write(ana_data.get("executive_summary", "No executive summary extracted."))

                st.subheader("🤝 Decisions")
                decisions = ana_data.get("decisions", [])
                if decisions:
                    for dec in decisions:
                        st.markdown(f"- {dec}")
                else:
                    st.write("No major decisions extracted.")

                st.subheader("📅 Deadlines")
                deadlines = ana_data.get("deadlines", [])
                if deadlines:
                    import pandas as pd
                    df_dl = pd.DataFrame(deadlines)
                    # Reorder and rename columns: Deadline, Date, Milestone, Responsible Person
                    for col in ["deadline", "date", "milestone", "responsible_person"]:
                        if col not in df_dl.columns:
                            df_dl[col] = None
                    df_dl = df_dl[["deadline", "date", "milestone", "responsible_person"]]
                    df_dl.rename(columns={
                        "deadline": "Deadline",
                        "date": "Date",
                        "milestone": "Milestone",
                        "responsible_person": "Responsible Person"
                    }, inplace=True)
                    st.table(df_dl)
                else:
                    st.write("No deadlines or milestones extracted.")

                st.subheader("⚠️ Risks / Blockers")
                risks = ana_data.get("risks", [])
                if risks:
                    import pandas as pd
                    df_risks = pd.DataFrame(risks)
                    # Reorder and rename columns: Risk, Blocker, Dependency, Unresolved Issue
                    for col in ["risk", "blocker", "dependency", "unresolved_issue"]:
                        if col not in df_risks.columns:
                            df_risks[col] = None
                    df_risks = df_risks[["risk", "blocker", "dependency", "unresolved_issue"]]
                    df_risks.rename(columns={
                        "risk": "Risk / Blocker",
                        "blocker": "Specific Blocker",
                        "dependency": "Dependency",
                        "unresolved_issue": "Unresolved Issue"
                    }, inplace=True)
                    st.table(df_risks)
                else:
                    st.write("No risks or blockers identified.")
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
                if not st.session_state.document_id:
                    st.error("No active document indexed for chat. Please upload and index a document first.")
                else:
                    with st.spinner("Searching ChromaDB & synthesizing answer with Ollama..."):
                        try:
                            res = send_chat_query(question=active_prompt, document_id=st.session_state.document_id)
                            answer_text = res.get("answer", "No answer generated.")
                            sources_list = res.get("sources", [])

                            st.write(answer_text)
                            if sources_list:
                                with st.expander("📌 Retrieved Vector Sources"):
                                    for s_idx, src in enumerate(sources_list, 1):
                                        st.markdown(f"**Chunk #{src.get('chunk_number', s_idx)}** (`{src.get('filename')}`):")
                                        st.caption(f"Source file: {src.get('filename')} | Chunk: {src.get('chunk_number')}")

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
        if st.session_state.analysis_data:
            st.subheader("✅ Action Items")
            action_items = st.session_state.analysis_data.get("action_items", [])
            if action_items:
                import pandas as pd
                df_actions = pd.DataFrame(action_items)
                # Ensure all required columns exist in the DataFrame
                for col in ["task", "owner", "status", "priority", "due_date"]:
                    if col not in df_actions.columns:
                        df_actions[col] = None

                # Reorder columns
                df_actions = df_actions[["task", "owner", "status", "priority", "due_date"]]
                # Rename columns for presentation
                df_actions.rename(columns={
                    "task": "Task",
                    "owner": "Owner",
                    "status": "Status",
                    "priority": "Priority",
                    "due_date": "Due Date"
                }, inplace=True)
                st.table(df_actions)
            else:
                st.info("No action items extracted from the meeting.")
        else:
            st.markdown(
                """
                <div class="placeholder-card">
                    <h3>✅ Action Items Placeholder</h3>
                    <p>Extracted task assignments and action item trackers will be displayed here after processing the meeting transcript.</p>
                </div>
                """,
                unsafe_allow_html=True
            )



if __name__ == "__main__":
    render_ui()
