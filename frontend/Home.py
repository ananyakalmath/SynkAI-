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
from frontend.views import login as login_view  # noqa: E402
from frontend.views import profile as profile_view  # noqa: E402
from frontend.views import settings as settings_view  # noqa: E402
from frontend.views import signup as signup_view  # noqa: E402
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
        "route": "login",

        # Authentication
        "logged_in": False,
        "auth_token": None,
        "user": None,

        # Meeting/application state
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

    # Do not load meeting history while the user is on the authentication screen.
    if not st.session_state.logged_in:
        return

    meetings = store.merge_with_backend(api.list_meetings())

    if not meetings:
        return

    # Only the active meeting is adopted. Stored summaries stay out of session state
    # so the Upload page never shows an older summary as if it were the current result.
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

        st.markdown(
            "<p class='sk-nav-label'>Workspace</p>",
            unsafe_allow_html=True,
        )

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

        # Get the currently authenticated user's information.
        user = st.session_state.get("user") or {}

        current_name = user.get("name") or USER_NAME
        current_role = user.get("role") or USER_TAGLINE

        if st.button(
            f"{current_name}  ·  {current_role}",
            key="profile_button",
            use_container_width=True,
        ):
            go("profile")
            st.rerun()

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

    # ---------------------------------------------------------
    # AUTHENTICATION
    # ---------------------------------------------------------
    # Users must log in or create an account before seeing
    # the actual SynkAI workspace.
    if not st.session_state.logged_in:

        auth_routes = {
            "login": login_view.render,
            "signup": signup_view.render,
        }

        renderer = auth_routes.get(
            st.session_state.route,
            login_view.render,
        )

        renderer(go)
        return

    # ---------------------------------------------------------
    # MAIN APPLICATION
    # ---------------------------------------------------------
    _render_sidebar()

    routes = {
        route: renderer
        for route, _, renderer in NAV_ITEMS
    }

    routes["profile"] = profile_view.render

    renderer = routes.get(
        st.session_state.route,
        home_view.render,
    )

    renderer(go)


main()