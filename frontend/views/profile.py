import html

import streamlit as st

from frontend.components import api


def render(go):
    user = st.session_state.get("user") or {}

    # If there is no authenticated user, return to login.
    if not st.session_state.get("logged_in") or not st.session_state.get("auth_token"):
        st.session_state.route = "login"
        st.rerun()
        return

    # Refresh the profile from the backend so we always show
    # the permanently stored account information.
    try:
        profile = api.get_profile(st.session_state.auth_token)
        st.session_state.user = profile
        user = profile
    except api.BackendError as exc:
        st.error(str(exc))
        return

    name = user.get("name", "")
    email = user.get("email", "")
    workspace = user.get("workspace", "SynkAI")
    role = user.get("role", "Workspace owner")

    initials = "".join(
        part[0] for part in name.split()[:2]
    ).upper() or "U"

    st.html(
        f"""
        <div style="margin-bottom: 2.5rem;">
            <div style="
                font-size: 0.78rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                opacity: 0.5;
                margin-bottom: 0.5rem;
            ">
                ACCOUNT
            </div>

            <h1 style="
                font-size: 2.4rem;
                margin: 0;
                font-weight: 650;
            ">
                Profile
            </h1>

            <p style="
                margin-top: 0.5rem;
                opacity: 0.6;
                font-size: 1rem;
            ">
                Manage your SynkAI account.
            </p>
        </div>
        """
    )

    st.html(
        f"""
        <div style="
            padding: 1.8rem;
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 18px;
            margin-bottom: 2rem;
        ">
            <div style="
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: #202020;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
            ">
                {html.escape(initials)}
            </div>

            <div style="
                font-size: 1.35rem;
                font-weight: 650;
            ">
                {html.escape(name)}
            </div>

            <div style="
                margin-top: 0.25rem;
                opacity: 0.55;
            ">
                {html.escape(role)}
            </div>
        </div>
        """
    )

    st.markdown("### Personal information")

    col1, col2 = st.columns(2)

    with col1:
        edited_name = st.text_input(
            "Name",
            value=name,
        )

    with col2:
        edited_email = st.text_input(
            "Email",
            value=email,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Workspace")

    col1, col2 = st.columns(2)

    with col1:
        edited_workspace = st.text_input(
            "Workspace",
            value=workspace,
        )

    with col2:
        st.text_input(
            "Role",
            value=role,
            disabled=True,
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    if st.button(
        "Save changes",
        use_container_width=True,
        type="primary",
    ):
        if not edited_name.strip():
            st.error("Name is required.")
            return

        if not edited_email.strip():
            st.error("Email is required.")
            return

        try:
            result = api.update_profile(
                auth_token=st.session_state.auth_token,
                name=edited_name,
                email=edited_email,
                workspace=edited_workspace or "SynkAI",
            )

            st.session_state.user = result["user"]
            st.success("Your profile has been updated.")
            st.rerun()

        except api.BackendError as exc:
            st.error(str(exc))

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### Account")

    if st.button(
        "Settings",
        use_container_width=True,
    ):
        go("settings")
        st.rerun()

    if st.button(
        "Sign out",
        use_container_width=True,
    ):
        try:
            api.logout(st.session_state.auth_token)
        except api.BackendError:
            # Even if the backend request fails, clear the local
            # authentication state so the user is not left logged in.
            pass

        st.session_state.logged_in = False
        st.session_state.auth_token = None
        st.session_state.user = None
        st.session_state.route = "login"

        st.rerun()