# ui_auth.py
import streamlit as st
from constants import EP
from services.api_client import http_post
from state import store_session_from_login

def _clear_session():
    for k in ("name", "token", "company_cache", "auth_pref"):
        st.session_state.pop(k, None)
    st.session_state["auth_pref"] = "Login"

def logout() -> None:
    # Tell backend to invalidate current session (Bearer token sent by api_client)
    try:
        http_post(EP["logout"], {})
    except Exception:
        pass  # ignore network hiccups on logout
    _clear_session()
    st.success("Logged out.")
    st.rerun()

def render_auth() -> None:
    st.header("Access")

    # Already logged in
    if st.session_state.get("token") and st.session_state.get("name"):
        st.info(f"Logged in as {st.session_state['name']}")
        if st.button("Logout"):
            logout()
        return

    pref = st.session_state.pop("auth_pref", "Login")
    mode = st.radio(
        "Choose an action",
        ["Login", "Register"],
        horizontal=True,
        index=(0 if pref == "Login" else 1),
    )

    # --- Register ---
    if mode == "Register":
        with st.form("register_form"):
            r_name = st.text_input("Name")
            r_email = st.text_input("Email")
            r_password = st.text_input("Password", type="password")
            r_api_key = st.text_input("API Key")
            can_submit = all([r_name, r_email, r_password, r_api_key])
            r_submit = st.form_submit_button("Register", disabled=not can_submit)

        if r_submit:
            payload = {
                "name": r_name.strip(),
                "password": r_password,          # backend hashes
                "email": r_email.strip(),
                "api_key": r_api_key.strip(),
            }
            resp = http_post(EP["register"], payload)
            if resp.status_code in (200, 201):
                st.success("Registered successfully. Please log in.")
                st.session_state["auth_pref"] = "Login"
                st.rerun()
            elif resp.status_code in (403, 409, 422):
                st.error(f"Registration failed ({resp.status_code}): {resp.text}")
            else:
                st.error(f"Unexpected response ({resp.status_code}): {resp.text}")

    # --- Login ---
    with st.form("login_form"):
        l_name = st.text_input("Name", key="login_name")
        l_password = st.text_input("Password", type="password", key="login_pw")
        l_submit = st.form_submit_button("Login", disabled=not (l_name and l_password))

    if l_submit:
        payload = {"name": l_name.strip(), "password": l_password}
        resp = http_post(EP["login"], payload)
        if resp.status_code == 200:
            try:
                # expects backend: {name, token, token_type, expires_at}
                store_session_from_login(resp.json(), l_name.strip())
                st.success("Login successful.")
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))
        elif resp.status_code in (401, 404):
            st.error(f"Login failed ({resp.status_code}): {resp.text}")
        else:
            st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
