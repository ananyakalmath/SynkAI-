import streamlit as st

from frontend.components import api


def render(go):
    # Create one centred column for the entire login experience.
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
                    Welcome back
                </div>

                <div style="
                    opacity: 0.6;
                    font-size: 1rem;
                ">
                    Log in to your SynkAI account.
                </div>
            </div>
            """
        )

        email = st.text_input(
            "Email",
            placeholder="you@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Log in",
            use_container_width=True,
            type="primary",
        ):
            if not email or not password:
                st.error("Please enter your email and password.")
                return

            try:
                result = api.login(email, password)

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
                Don't have an account?
            </div>
            """
        )

        if st.button(
            "Create an account",
            use_container_width=True,
        ):
            st.session_state.route = "signup"
            st.rerun()