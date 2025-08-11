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
    try:
        http_post(EP["logout"], {})
    except Exception:
        pass
    _clear_session()
    st.success("Logged out.")
    st.rerun()

def render_auth() -> None:
    st.header("Access")

    # already logged in
    if st.session_state.get("token") and st.session_state.get("name"):
        st.info(f"Logged in as {st.session_state['name']}")
        if st.button("Logout"):
            logout()
        return

    pref = st.session_state.pop("auth_pref", "Login")
    mode = st.radio("Choose an action", ["Login", "Register"], horizontal=True,
                    index=(0 if pref == "Login" else 1))

    # --- Register ---
    if mode == "Register":
        with st.form("register_form"):
            r_name = st.text_input("Name")
            r_email = st.text_input("Email")
            r_password = st.text_input("Password", type="password")
            r_api_key = st.text_input("API Key")
            r_submit = st.form_submit_button("Register")  # validate on submit

        if r_submit:
            name = r_name.strip()
            email = r_email.strip()
            password = r_password
            api_key = r_api_key.strip()

            missing = [lbl for lbl, v in {
                "Name": name, "Email": email, "Password": password, "API Key": api_key
            }.items() if not v]
            if missing:
                st.error(f"Missing required: {', '.join(missing)}")
            elif "@" not in email:
                st.error("Enter a valid email.")
            else:
                payload = {"name": name, "password": password, "email": email, "api_key": api_key}
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
        l_submit = st.form_submit_button("Login")  # validate on submit

    if l_submit:
        name = l_name.strip()
        if not name or not l_password:
            st.error("Name and Password are required.")
        else:
            payload = {"name": name, "password": l_password}
            resp = http_post(EP["login"], payload)
            if resp.status_code == 200:
                try:
                    store_session_from_login(resp.json(), name)
                    st.success("Login successful.")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
            elif resp.status_code in (401, 404):
                st.error(f"Login failed ({resp.status_code}): {resp.text}")
            else:
                st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
