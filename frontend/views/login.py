"""
Sign-in view: "Sign in with Google" or an emailed one-time code. No passwords.
"""

import streamlit as st

from frontend.components import api


def _start_google_login() -> None:
    try:
        result = api.google_login_url(invite_code=st.session_state.get("pending_invite_code"))
    except api.BackendError as exc:
        st.error(str(exc))
        return

    st.session_state.oauth_state = result["state"]
    st.link_button("Continue to Google →", result["authorization_url"], use_container_width=True)


def _email_code_form() -> None:
    stage = st.session_state.get("email_login_stage", "request")

    if stage == "request":
        email = st.text_input("Work email", placeholder="you@company.com", key="login_email")

        if st.button("Send sign-in code", use_container_width=True, key="send_code"):
            if not email.strip():
                st.error("Please enter your work email.")
                return
            try:
                api.request_email_code(email.strip())
            except api.BackendError as exc:
                st.error(str(exc))
                return

            st.session_state.email_login_address = email.strip()
            st.session_state.email_login_stage = "verify"
            st.rerun()

    else:
        address = st.session_state.get("email_login_address", "")
        st.caption(f"We sent a 6-digit code to **{address}**. It expires in 10 minutes.")

        code = st.text_input("Code", max_chars=6, key="login_code")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Verify and sign in", use_container_width=True, type="primary", key="verify_code"):
                if not code.strip():
                    st.error("Please enter the code.")
                    return
                try:
                    result = api.verify_email_code(address, code.strip())
                except api.BackendError as exc:
                    st.error(str(exc))
                    return

                _apply_session(result)

        with col_b:
            if st.button("Use a different email", use_container_width=True, key="restart_email_login"):
                st.session_state.email_login_stage = "request"
                st.rerun()


def _apply_session(result: dict) -> None:
    st.session_state.auth_token = result["session_token"]
    st.session_state.user = result["user"]
    st.session_state.logged_in = True
    st.session_state.bootstrapped = False
    st.session_state.email_login_stage = "request"

    if result["user"]["onboarded"]:
        st.session_state.route = "home"
    else:
        st.session_state.route = "onboarding"

    st.rerun()


def render(go) -> None:
    left, center, right = st.columns([1, 2, 1])

    with center:
        st.html(
            """
            <div style="text-align: center; margin-top: 4rem; margin-bottom: 2.5rem;">
                <div style="font-size: 2rem; font-weight: 650; margin-bottom: 0.5rem;">
                    Welcome to SynkAI
                </div>
                <div style="opacity: 0.6; font-size: 1rem;">
                    Sign in with Google, or with a code sent to your work email. No passwords.
                </div>
            </div>
            """
        )

        if st.session_state.get("pending_invite_code"):
            st.info("You're signing in to accept a workspace invite.")

        _start_google_login()

        st.html("<div style='text-align:center; margin: 1.5rem 0; opacity: 0.5;'>or</div>")

        _email_code_form()
