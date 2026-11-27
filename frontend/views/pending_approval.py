"""
Shown to a user whose join request is awaiting approval from their workspace's admin.
"""

import streamlit as st

from frontend.components import api


def render(go) -> None:
    user = st.session_state.get("user") or {}
    workspace = user.get("workspace") or {}

    st.html(
        f"""
        <div style="text-align:center; margin-top: 4rem;">
            <div style="font-size: 1.8rem; font-weight: 650; margin-bottom: 0.75rem;">
                Waiting for approval
            </div>
            <div style="opacity: 0.65; font-size: 1rem; max-width: 32rem; margin: 0 auto;">
                Your request to join <b>{workspace.get("company_name", "this workspace")}</b>
                is pending. An admin there needs to approve it before you can use SynkAI.
            </div>
        </div>
        """
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        if st.button("Check again", use_container_width=True):
            try:
                profile = api.get_me()
            except api.BackendError as exc:
                st.error(str(exc))
                return

            st.session_state.user = profile
            if profile["membership_status"] == "active":
                st.session_state.route = "home"
                st.session_state.bootstrapped = False
            st.rerun()

        if st.button("Sign out", use_container_width=True):
            try:
                api.logout()
            except api.BackendError:
                pass
            st.session_state.logged_in = False
            st.session_state.auth_token = None
            st.session_state.user = None
            st.session_state.route = "login"
            st.rerun()
