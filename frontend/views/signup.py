import streamlit as st

from frontend.components import api


def render(go):
    # Keep the entire signup experience in one centred column.
    left, center, right = st.columns([1, 2, 1])

    with center:
        st.html(
            """
            <div style="
                text-align: center;
                margin-top: 4rem;
                margin-bottom: 2.5rem;
            ">
                <div style="
                    font-size: 2rem;
                    font-weight: 650;
                    margin-bottom: 0.5rem;
                ">
                    Create your account
                </div>

                <div style="
                    opacity: 0.6;
                    font-size: 1rem;
                ">
                    Set up your SynkAI workspace.
                </div>
            </div>
            """
        )

        name = st.text_input(
            "Name",
            placeholder="Your name",
        )

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="At least 8 characters",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Re-enter your password",
        )

        workspace = st.text_input(
            "Workspace",
            value="SynkAI",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Create account",
            use_container_width=True,
            type="primary",
        ):
            if not name or not email or not password or not confirm_password:
                st.error("Please fill in all required fields.")
                return

            if password != confirm_password:
                st.error("Passwords do not match.")
                return

            if len(password) < 8:
                st.error("Password must be at least 8 characters long.")
                return

            try:
                result = api.signup(
                    name=name,
                    email=email,
                    password=password,
                    workspace=workspace or "SynkAI",
                )

                st.session_state.auth_token = result["auth_token"]
                st.session_state.user = result["user"]
                st.session_state.logged_in = True
                st.session_state.route = "home"
                st.session_state.bootstrapped = False

                st.rerun()

            except api.BackendError as exc:
                st.error(str(exc))

        st.html(
            """
            <div style="
                text-align: center;
                margin-top: 2.5rem;
                margin-bottom: 0.5rem;
                opacity: 0.65;
            ">
                Already have an account?
            </div>
            """
        )

        if st.button(
            "Log in",
            use_container_width=True,
        ):
            st.session_state.route = "login"
            st.rerun()