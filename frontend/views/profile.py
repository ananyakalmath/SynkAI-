import html

import streamlit as st

from frontend.components import api


def render(go) -> None:
    if not st.session_state.get("logged_in") or not st.session_state.get("auth_token"):
        st.session_state.route = "login"
        st.rerun()
        return

    try:
        user = api.get_me()
        st.session_state.user = user
    except api.BackendError as exc:
        st.error(str(exc))
        return

    name = user.get("full_name") or ""
    email = user.get("email", "")
    role_title = user.get("role_title") or ""
    workspace = user.get("workspace") or {}
    is_admin = user.get("membership_role") == "admin"

    initials = "".join(part[0] for part in name.split()[:2]).upper() or "U"

    st.html(
        f"""
        <div style="margin-bottom: 2rem;">
            <div style="font-size:0.78rem; font-weight:600; letter-spacing:0.08em;
                        text-transform:uppercase; opacity:0.5; margin-bottom:0.5rem;">ACCOUNT</div>
            <h1 style="font-size:2.4rem; margin:0; font-weight:650;">Profile</h1>
            <p style="margin-top:0.5rem; opacity:0.6; font-size:1rem;">Manage your SynkAI account.</p>
        </div>
        """
    )

    st.html(
        f"""
        <div style="padding:1.8rem; border:1px solid rgba(0,0,0,0.08); border-radius:18px; margin-bottom:2rem;">
            <div style="width:64px; height:64px; border-radius:50%; background:#202020; color:white;
                        display:flex; align-items:center; justify-content:center; font-size:1.2rem;
                        font-weight:600; margin-bottom:1rem;">{html.escape(initials)}</div>
            <div style="font-size:1.35rem; font-weight:650;">{html.escape(name or email)}</div>
            <div style="margin-top:0.25rem; opacity:0.55;">{html.escape(role_title)}</div>
        </div>
        """
    )

    st.markdown("### Personal information")

    col1, col2 = st.columns(2)
    with col1:
        edited_name = st.text_input("Full name", value=name)
    with col2:
        st.text_input("Work email (verified)", value=email, disabled=True)

    edited_role = st.text_input("Role / title", value=role_title)

    if st.button("Save changes", type="primary"):
        if not edited_name.strip() or not edited_role.strip():
            st.error("Name and role cannot be empty.")
        else:
            try:
                updated = api.update_profile(edited_name.strip(), edited_role.strip())
                st.session_state.user = updated
                st.success("Profile updated.")
                st.rerun()
            except api.BackendError as exc:
                st.error(str(exc))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Google account")
    if user.get("google_connected"):
        st.success("Connected via Google Sign-In.")
    else:
        st.caption("Not connected. You're signed in with an emailed code.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Google Calendar")
    st.caption(
        "Connect your Google Calendar so meetings you organise are created there directly, "
        "with a Google Meet link — attendees are invited by Google itself. If you don't "
        "connect this, invites are still emailed with a standard calendar attachment."
    )
    try:
        calendar_status = api.google_calendar_status()
    except api.BackendError as exc:
        calendar_status = None
        st.error(str(exc))

    if calendar_status and calendar_status.get("connected"):
        st.success("Google Calendar is connected.")
        if st.button("Disconnect Google Calendar"):
            try:
                api.google_calendar_disconnect()
                st.rerun()
            except api.BackendError as exc:
                st.error(str(exc))
    elif calendar_status is not None:
        try:
            connect_result = api.google_calendar_connect_url()
            st.link_button("Connect Google Calendar →", connect_result["authorization_url"])
        except api.BackendError as exc:
            st.error(str(exc))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Workspace")
    st.write(f"**{workspace.get('company_name', '—')}**  ·  {'Admin' if is_admin else 'Member'}")

    try:
        members_payload = api.get_workspace_members()
    except api.BackendError as exc:
        members_payload = None
        st.error(str(exc))

    if members_payload:
        for member in members_payload.get("members", []):
            label = f"{member.get('full_name') or member['email']} — {member.get('title') or member['role']}"
            st.write(f"• {label}")

        pending = members_payload.get("pending", [])
        if is_admin and pending:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Pending join requests")
            for member in pending:
                p_col1, p_col2, p_col3 = st.columns([3, 1, 1])
                with p_col1:
                    st.write(f"{member.get('full_name') or member['email']} ({member['email']})")
                with p_col2:
                    if st.button("Approve", key=f"approve_{member['user_id']}"):
                        try:
                            api.approve_workspace_request(member["user_id"])
                            st.rerun()
                        except api.BackendError as exc:
                            st.error(str(exc))
                with p_col3:
                    if st.button("Reject", key=f"reject_{member['user_id']}"):
                        try:
                            api.reject_workspace_request(member["user_id"])
                            st.rerun()
                        except api.BackendError as exc:
                            st.error(str(exc))

    if is_admin:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Invite someone")
        st.caption(
            "The only way to add someone whose email isn't on this workspace's own "
            "domain — including anyone on Gmail, Outlook, or another personal provider."
        )
        invite_col1, invite_col2 = st.columns([3, 1])
        with invite_col1:
            invite_email = st.text_input("Email to invite", key="invite_email", label_visibility="collapsed", placeholder="person@example.com")
        with invite_col2:
            if st.button("Send invite", use_container_width=True):
                if not invite_email.strip():
                    st.error("Enter an email address first.")
                else:
                    try:
                        result = api.invite_to_workspace(invite_email.strip())
                        if result.get("email_sent"):
                            st.success(f"Invite emailed to {result['invited_email']}.")
                        else:
                            st.warning(
                                f"Couldn't email the invite ({result.get('email_error')}). "
                                f"Share this link instead: {result['invite_url']}"
                            )
                    except api.BackendError as exc:
                        st.error(str(exc))

        try:
            invites = api.list_workspace_invites().get("invites", [])
        except api.BackendError:
            invites = []

        if invites:
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Outstanding invites")
            for invite in invites:
                st.write(f"• {invite['invited_email']} — expires {invite['expires_at'][:10]}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Account")

    if st.button("Settings", use_container_width=True):
        go("settings")
        st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Sign out", use_container_width=True):
            try:
                api.logout()
            except api.BackendError:
                pass
            _clear_session()
            st.rerun()
    with col_b:
        if st.button("Sign out of all devices", use_container_width=True):
            try:
                api.logout_all_devices()
            except api.BackendError:
                pass
            _clear_session()
            st.rerun()


def _clear_session() -> None:
    st.session_state.logged_in = False
    st.session_state.auth_token = None
    st.session_state.user = None
    st.session_state.route = "login"
