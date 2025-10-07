# ui/auth.py
import streamlit as st
from constants import EP
from services.api_client import http_post
from state import store_session_from_login

FLASH_KEY = "auth_flash"  # ("success"|"error", message)
RADIO_KEY = "auth_mode"   # persistent radio state

def _show_flash():
    kind, msg = st.session_state.pop(FLASH_KEY, (None, None))
    if kind == "success":
        st.success(msg)
    elif kind == "error":
        st.error(msg)

def _clear_session():
    for k in ("name", "token", "company_cache", "auth_pref", "register_busy", "login_prefill"):
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
    _show_flash()

    if st.session_state.get("token") and st.session_state.get("name"):
        st.info(f"Logged in as {st.session_state['name']}")
        if st.button("Logout"):
            logout()
        return

    if st.session_state.pop("force_login", False):
        st.session_state[RADIO_KEY] = "Login"

    mode = st.radio("Choose an action", ["Login", "Register"], horizontal=True, key=RADIO_KEY)

    # -------- Register --------
    if mode == "Register":
        st.session_state.setdefault("register_busy", False)
        with st.form("register_form", clear_on_submit=False):
            r_name = st.text_input("Name", key="register_name")
            r_email = st.text_input("Email", key="register_email")
            r_password = st.text_input("Password", type="password", key="register_pw")
            r_password2 = st.text_input("Confirm Password", type="password", key="register_pw2")
            r_api_key = st.text_input("API Key", key="register_api")
            r_submit = st.form_submit_button("Register", disabled=st.session_state.get("register_busy", False))

        if r_submit and not st.session_state.get("register_busy", False):
            st.session_state["register_busy"] = True
            try:
                name = (r_name or "").strip()
                email = (r_email or "").strip()
                password = r_password or ""
                password2 = r_password2 or ""
                api_key = (r_api_key or "").strip()

                missing = [lbl for lbl, v in {
                    "Name": name, "Email": email, "Password": password, "Confirm Password": password2, "API Key": api_key
                }.items() if not v]
                if missing:
                    st.error(f"Missing required: {', '.join(missing)}")
                    return
                if "@" not in email:
                    st.error("Enter a valid email.")
                    return
                if password != password2:
                    st.error("Passwords do not match.")
                    return

                payload = {"name": name, "password": password, "email": email, "api_key": api_key}
                with st.spinner("Creating your account..."):
                    resp = http_post(EP["register"], payload)

                if resp.status_code in (200, 201):
                    # clear form values so they won't persist
                    for k in ("register_name", "register_email", "register_pw", "register_pw2", "register_api"):
                        if k in st.session_state:
                            del st.session_state[k]

                    # flash message + force login tab
                    st.session_state[FLASH_KEY] = ("success", "Registration successful. Please log in.")
                    st.session_state["login_prefill"] = name
                    st.session_state["force_login"] = True
                    st.rerun()
                elif resp.status_code in (403, 409, 422):
                    st.error(f"Registration failed ({resp.status_code}): {resp.text}")
                else:
                    st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
            finally:
                st.session_state["register_busy"] = False

    # -------- Login --------
    if mode == "Login":
        prefill_name = st.session_state.pop("login_prefill", "")
        with st.form("login_form"):
            l_name = st.text_input("Name", value=prefill_name, key="login_name")
            l_password = st.text_input("Password", type="password", key="login_pw")
            l_submit = st.form_submit_button("Login")

        if l_submit:
            name = (l_name or "").strip()
            if not name or not l_password:
                st.error("Name and Password are required.")
            else:
                payload = {"name": name, "password": l_password}
                with st.spinner("Signing in..."):
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
