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
from frontend.views import calendar as calendar_view  # noqa: E402
from frontend.views import chat as chat_view  # noqa: E402
from frontend.views import history as history_view  # noqa: E402
from frontend.views import home as home_view  # noqa: E402
from frontend.views import login as login_view  # noqa: E402
from frontend.views import onboarding as onboarding_view  # noqa: E402
from frontend.views import pending_approval as pending_approval_view  # noqa: E402
from frontend.views import profile as profile_view  # noqa: E402
from frontend.views import settings as settings_view  # noqa: E402
from frontend.views import upload as upload_view  # noqa: E402


USER_NAME = os.getenv("SYNKAI_USER_NAME", "Ananya Kalmath")
USER_TAGLINE = os.getenv("SYNKAI_USER_TAGLINE", "Workspace owner")


NAV_ITEMS = [
    ("home", "Home", home_view.render),
    ("upload", "Upload & Summarize", upload_view.render),
    ("calendar", "Calendar", calendar_view.render),
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

        current_name = user.get("full_name") or USER_NAME
        workspace_name = (user.get("workspace") or {}).get("company_name")
        current_role = workspace_name or user.get("role_title") or USER_TAGLINE

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


def _handle_invite_link() -> None:
    """
    An invite email points at this app's own URL with ?invite=<code>. The code is
    stashed in session state (not left in the URL) so it survives both a plain rerun
    and, via the backend's oauth_states record (see login_view), a full redirect out
    to Google and back — which normally starts a fresh browser session and would
    otherwise lose anything held only in session state.
    """
    code = st.query_params.get("invite")
    if not code:
        return
    st.session_state.pending_invite_code = code
    st.query_params.clear()


def _handle_google_oauth_redirect() -> None:
    """
    Google redirects the browser back to this app's own URL with ?code=&state=.
    Streamlit sees that as a normal page load, so every run checks for it, exchanges
    the code for a session on the backend, then clears the query params so a page
    refresh doesn't try to redeem the same (already-used) code again.

    Two different flows land here with the same shape: an ordinary sign-in, and a
    "Connect Google Calendar" incremental-authorization round trip (Phase 3). The
    `state` value itself says which one — a calendar-connect state is prefixed
    "cal_" by the backend (see auth_service.create_calendar_connect_state) — so no
    extra round trip is needed just to ask which flow a redirect belongs to.
    """
    params = st.query_params
    code = params.get("code")
    state = params.get("state")
    if not code or not state:
        return

    st.query_params.clear()

    if state.startswith("cal_"):
        try:
            api.google_calendar_callback(code, state)
            st.session_state.notice = "Google Calendar connected."
        except api.BackendError as exc:
            st.session_state.notice = str(exc)
        return

    try:
        result = api.google_callback(code, state)
    except api.BackendError as exc:
        st.session_state.notice = str(exc)
        return

    st.session_state.auth_token = result["session_token"]
    st.session_state.user = result["user"]
    st.session_state.logged_in = True
    st.session_state.bootstrapped = False
    if result.get("invite_code"):
        st.session_state.pending_invite_code = result["invite_code"]
    st.session_state.route = "home" if result["user"]["onboarded"] else "onboarding"


def main() -> None:
    """
    Renders the application.
    """

    _init_state()
    apply_theme()
    _handle_invite_link()
    _handle_google_oauth_redirect()

    if st.session_state.get("notice"):
        st.info(st.session_state.notice)
        st.session_state.notice = None

    # ---------------------------------------------------------
    # AUTHENTICATION / ONBOARDING / APPROVAL GATES
    # ---------------------------------------------------------
    # Users must sign in, complete onboarding, and (if joining an existing
    # workspace) be approved, before seeing the actual SynkAI workspace.
    if not st.session_state.logged_in:
        login_view.render(go)
        return

    user = st.session_state.get("user") or {}

    if not user.get("onboarded"):
        onboarding_view.render(go)
        return

    if user.get("membership_status") == "pending":
        pending_approval_view.render(go)
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