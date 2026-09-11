"""
SynkAI - Agentic AI Meeting Assistant.

Application shell: page configuration, the design system, the charcoal sidebar and
routing into the individual views. All backend work lives in `frontend/components/api.py`;
the views only render.
"""

import os
import sys

import streamlit as st

# Allow `streamlit run frontend/Home.py` from the project root without PYTHONPATH.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from frontend.components import api, icons, store, ui  # noqa: E402
from frontend.components.theme import apply_theme  # noqa: E402
from frontend.views import analysis as analysis_view  # noqa: E402
from frontend.views import chat as chat_view  # noqa: E402
from frontend.views import history as history_view  # noqa: E402
from frontend.views import home as home_view  # noqa: E402
from frontend.views import settings as settings_view  # noqa: E402
from frontend.views import upload as upload_view  # noqa: E402

USER_NAME = os.getenv("SYNKAI_USER_NAME", "Ananya Kalmath")
USER_TAGLINE = os.getenv("SYNKAI_USER_TAGLINE", "Workspace owner")

NAV_ITEMS = [
    ("home", "Home", home_view.render),
    ("upload", "Upload & Summarize", upload_view.render),
    ("chat", "AI Chat", chat_view.render),
    ("analysis", "Meeting Analysis", analysis_view.render),
    ("history", "History", history_view.render),
    ("settings", "Settings", settings_view.render),
]

st.set_page_config(
    page_title="SynkAI — Meetings, made meaningful",
    page_icon="◍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_state() -> None:
    """
    Seeds the session state keys shared across views, and adopts the most recently
    indexed meeting so Chat and Analysis are usable straight away.
    """
    defaults = {
        "route": "home",
        "active_document_id": None,
        "active_filename": None,
        "summary_data": None,
        "analysis_data": None,
        "upload_info": None,
        "chat_history": [],
        "search_query": "",
        "history_filter": "All",
        "pending_question": None,
        "notice": None,
        "bootstrapped": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    if st.session_state.bootstrapped:
        return

    st.session_state.bootstrapped = True
    meetings = store.merge_with_backend(api.list_meetings())
    if not meetings:
        return

    # Only the active meeting is adopted. Stored summaries stay out of session state so
    # the Upload page never shows an older summary as if it were the current result;
    # views that want history read the store directly or are opened from History.
    latest = meetings[0]
    st.session_state.active_document_id = latest.get("document_id")
    st.session_state.active_filename = latest.get("filename")


def go(route: str) -> None:
    """
    Switches the active view.

    Args:
        route (str): Route key from NAV_ITEMS.
    """
    st.session_state.route = route


def _render_sidebar() -> None:
    """
    Renders the charcoal sidebar: brand, navigation, and clickable user profile.
    """
    with st.sidebar:
        st.markdown(
            """
            <p class="sk-brand">SynkAI</p>
            <p class="sk-brand-tag">Meetings, made meaningful.</p>
            """,
            unsafe_allow_html=True,
        )
        ui.spacer(1.6)
        st.markdown("<p class='sk-nav-label'>Workspace</p>", unsafe_allow_html=True)

        for route, label, _ in NAV_ITEMS:
            is_active = st.session_state.route == route
            wrapper = st.container(key=f"navwrap_{route}")

            if is_active:
                st.markdown(
                    f"""
                    <style>
                    [data-testid="stSidebar"] .st-key-navwrap_{route} .stButton > button {{
                        background: rgba(255, 255, 255, 0.12);
                        color: #FFFFFF;
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

            with wrapper:
                if st.button(
                    label,
                    key=f"nav_{route}",
                    icon=icons.MATERIAL.get(route),
                    use_container_width=True,
                ):
                    go(route)
                    st.rerun()

        ui.spacer(0.6)
        st.markdown("<hr/>", unsafe_allow_html=True)

        online = api.is_backend_online()
        dot = "#9CB89C" if online else "#C79B93"
        state = "Backend online" if online else "Backend offline"

        initials = "".join(
            part[0] for part in USER_NAME.split()[:2]
        ).upper()

        # Clickable profile menu
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] .st-key-profile_menu button {
                border: none;
                background: transparent;
                padding: 0.35rem 0.25rem;
                width: 100%;
                justify-content: flex-start;
            }

            [data-testid="stSidebar"] .st-key-profile_menu button:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="profile_menu"):
            with st.popover(
                f"{USER_NAME} — {USER_TAGLINE}",
                use_container_width=True,
            ):
                st.markdown(
                    f"""
                    <div style="
                        padding: 0.2rem 0 0.7rem 0;
                        border-bottom: 1px solid rgba(255,255,255,0.12);
                        margin-bottom: 0.5rem;
                    ">
                        <div style="
                            font-size: 1rem;
                            font-weight: 600;
                        ">
                            {ui.esc(USER_NAME)}
                        </div>
                        <div style="
                            font-size: 0.78rem;
                            opacity: 0.65;
                            margin-top: 0.15rem;
                        ">
                            {ui.esc(USER_TAGLINE)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Profile", key="profile_item", use_container_width=True):
                    st.session_state.notice = "Profile"
                    st.rerun()

                if st.button("Workspace", key="workspace_item", use_container_width=True):
                    st.session_state.notice = "Workspace"
                    st.rerun()

                if st.button("Settings", key="profile_settings_item", use_container_width=True):
                    go("settings")
                    st.rerun()

                if st.button("Sign out", key="signout_item", use_container_width=True):
                    st.session_state.notice = "Sign out is not configured yet."

        # Backend status
        st.markdown(
            f"""
            <div class="sk-status" style="margin-top:.9rem">
              <span class="sk-status-dot" style="background:{dot}"></span>
              {ui.esc(state)}
            </div>
            """,
            unsafe_allow_html=True,
        )

def main() -> None:
    """
    Renders the application.
    """
    _init_state()
    apply_theme()
    _render_sidebar()

    routes = {route: renderer for route, _, renderer in NAV_ITEMS}
    renderer = routes.get(st.session_state.route, home_view.render)
    renderer(go)


main()
