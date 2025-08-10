import streamlit as st
from constants import EP
from services.api_client import http_post
from state import store_session_from_login


def render_auth() -> None:
    st.header("Access")
    mode = st.radio("Choose an action", options=["Login", "Register"], horizontal=True, key="auth_mode")

    if mode == "Register":
        with st.form("register_form"):
            r_name = st.text_input("Name")
            r_email = st.text_input("Email")
            r_password = st.text_input("Password", type="password")
            r_api_key = st.text_input("API Key")
            r_submit = st.form_submit_button("Register")
        if r_submit:
            payload = {
                "name": r_name.strip(),
                "password": r_password,
                "email": r_email.strip(),
                "api_key": r_api_key.strip(),
            }
            resp = http_post(EP["register"], payload)
            if resp.status_code == 200:
                st.success("Registered successfully.")
                st.session_state["auth_mode"] = "Login"
                st.rerun()
            elif resp.status_code in (403, 409, 422):
                st.error(f"Registration failed ({resp.status_code}): {resp.text}")
            else:
                st.error(f"Unexpected response ({resp.status_code}): {resp.text}")

    with st.form("login_form"):
        l_name = st.text_input("Name", key="login_name")
        l_password = st.text_input("Password", type="password", key="login_pw")
        l_submit = st.form_submit_button("Login")
    if l_submit:
        payload = {"name": l_name.strip(), "password": l_password}
        resp = http_post(EP["login"], payload)
        if resp.status_code == 200:
            try:
                store_session_from_login(resp.json(), l_name.strip())
                st.success("Login successful.")
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))
        elif resp.status_code in (401, 404):
            st.error(f"Login failed ({resp.status_code}): {resp.text}")
        else:
            st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
