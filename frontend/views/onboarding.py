"""
First-login onboarding: full name, work email (verified, read-only), role/title, and
either a company name (creates or requests to join a workspace matched by email
domain) or an invite code (joins that exact workspace directly).
"""

import streamlit as st

from frontend.components import api


def render(go) -> None:
    user = st.session_state.get("user") or {}
    invite_code = st.session_state.get("pending_invite_code")

    st.html(
        """
        <div style="margin-bottom: 2rem;">
            <div style="font-size: 2rem; font-weight: 650; margin-bottom: 0.5rem;">
                Set up your account
            </div>
            <div style="opacity: 0.6; font-size: 1rem;">
                Just a few details before your SynkAI workspace is ready.
            </div>
        </div>
        """
    )

    full_name = st.text_input("Full name", value=user.get("full_name") or "")
    st.text_input("Work email", value=user.get("email", ""), disabled=True)
    role_title = st.text_input("Role / title", placeholder="e.g. CEO, Manager, Engineer")

    company_name = ""
    if invite_code:
        st.success("You have an invite — continuing will join that workspace directly.")
    else:
        company_name = st.text_input("Company name", placeholder="Acme Inc.")
        st.caption(
            "If someone at your company already set up a SynkAI workspace, you'll be asked "
            "to wait for their approval to join it — matched by your email domain, not the "
            "company name you type here. Personal email providers (Gmail, Outlook, etc.) "
            "always get a brand new workspace; ask an admin to invite you to join an "
            "existing one instead."
        )

    if st.button("Continue", type="primary", use_container_width=True):
        if not full_name.strip() or not role_title.strip():
            st.error("Please fill in your name and role.")
            return
        if not invite_code and not company_name.strip():
            st.error("Please enter your company name.")
            return

        try:
            profile = api.submit_onboarding(
                full_name.strip(),
                role_title.strip(),
                company_name=company_name.strip() or None,
                invite_code=invite_code,
            )
        except api.BackendError as exc:
            st.error(str(exc))
            return

        st.session_state.pending_invite_code = None
        st.session_state.user = profile
        st.session_state.route = "home" if profile["membership_status"] == "active" else "pending_approval"
        st.rerun()
