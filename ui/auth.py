# ui/auth.py
import streamlit as st
from constants import EP
from services.api_client import http_post
from state import store_session_from_login

FLASH_KEY = "auth_flash"  # ("success"|"error", message)
RADIO_KEY = "auth_mode"   # persistent radio state
REGISTER_FORM_KEYS = (
    "register_name",
    "register_email",
    "register_pw",
    "register_pw2",
    "register_api",
)
SESSION_KEYS_TO_CLEAR = (
    "name",
    "token",
    "expires_at",
    "company_cache",
    "register_busy",
    "login_prefill",
    "force_login",
)

def _show_flash():
    kind, msg = st.session_state.pop(FLASH_KEY, (None, None))
    if kind == "success":
        st.success(msg)
    elif kind == "error":
        st.error(msg)

def _clear_session():
    for k in SESSION_KEYS_TO_CLEAR:
        st.session_state.pop(k, None)
    st.session_state[RADIO_KEY] = "Login"


def _show_logged_in_state() -> bool:
    if not (st.session_state.get("token") and st.session_state.get("name")):
        return False

    st.info(f"Logged in as {st.session_state['name']}")
    if st.button("Logout"):
        logout()
    return True


def _select_auth_mode() -> str:
    if st.session_state.pop("force_login", False):
        st.session_state[RADIO_KEY] = "Login"

    return st.radio(
        "Welcome to your Smart Marketing Agent! If you haven't created an account yet, please register.",
        ["Login", "Register"],
        horizontal=True,
        key=RADIO_KEY,
    )


def _render_register_form():
    st.session_state.setdefault("register_busy", False)
    with st.form("register_form", clear_on_submit=False):
        values = {
            "name": st.text_input("Name", key="register_name"),
            "email": st.text_input("Email", key="register_email"),
            "password": st.text_input("Password", type="password", key="register_pw"),
            "password2": st.text_input("Confirm Password", type="password", key="register_pw2"),
            "api_key": st.text_input("API Key", key="register_api"),
        }
        submitted = st.form_submit_button(
            "Register",
            disabled=st.session_state.get("register_busy", False),
        )
    return values, submitted


def _normalize_registration(values):
    return {
        "name": (values.get("name") or "").strip(),
        "email": (values.get("email") or "").strip(),
        "password": values.get("password") or "",
        "password2": values.get("password2") or "",
        "api_key": (values.get("api_key") or "").strip(),
    }


def _validate_registration(values) -> str | None:
    labels = {
        "name": "Name",
        "email": "Email",
        "password": "Password",
        "password2": "Confirm Password",
        "api_key": "API Key",
    }
    missing = [label for key, label in labels.items() if not values[key]]
    if missing:
        return f"Missing required: {', '.join(missing)}"
    if "@" not in values["email"]:
        return "Enter a valid email."
    if values["password"] != values["password2"]:
        return "Passwords do not match."
    return None


def _clear_registration_form():
    for key in REGISTER_FORM_KEYS:
        st.session_state.pop(key, None)


def _complete_registration(name: str):
    _clear_registration_form()
    st.session_state[FLASH_KEY] = ("success", "Registration successful. Please log in.")
    st.session_state["login_prefill"] = name
    st.session_state["force_login"] = True
    st.rerun()


def _submit_registration(values) -> None:
    payload = {
        "name": values["name"],
        "password": values["password"],
        "email": values["email"],
        "api_key": values["api_key"],
    }
    with st.spinner("Creating your account..."):
        resp = http_post(EP["register"], payload)

    if resp.status_code in (200, 201):
        _complete_registration(values["name"])
        return
    if resp.status_code in (403, 409, 422):
        st.error(f"Registration failed ({resp.status_code}): {resp.text}")
        return
    st.error(f"Unexpected response ({resp.status_code}): {resp.text}")


def _handle_register_mode() -> None:
    values, submitted = _render_register_form()
    if not submitted or st.session_state.get("register_busy", False):
        return

    st.session_state["register_busy"] = True
    try:
        normalized = _normalize_registration(values)
        validation_error = _validate_registration(normalized)
        if validation_error:
            st.error(validation_error)
            return
        _submit_registration(normalized)
    finally:
        st.session_state["register_busy"] = False


def _render_login_form():
    prefill_name = st.session_state.pop("login_prefill", "")
    with st.form("login_form"):
        name = st.text_input("Name", value=prefill_name, key="login_name")
        password = st.text_input("Password", type="password", key="login_pw")
        submitted = st.form_submit_button("Login")
    return name, password, submitted


def _submit_login(name: str, password: str) -> None:
    payload = {"name": name, "password": password}
    with st.spinner("Signing in..."):
        resp = http_post(EP["login"], payload)

    if resp.status_code == 200:
        try:
            store_session_from_login(resp.json(), name)
            st.success("Login successful.")
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))
        return
    if resp.status_code in (401, 404):
        st.error(f"Login failed ({resp.status_code}): {resp.text}")
        return
    st.error(f"Unexpected response ({resp.status_code}): {resp.text}")


def _handle_login_mode() -> None:
    name, password, submitted = _render_login_form()
    if not submitted:
        return

    normalized_name = (name or "").strip()
    if not normalized_name or not password:
        st.error("Name and Password are required.")
        return
    _submit_login(normalized_name, password)

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

    if _show_logged_in_state():
        return

    mode = _select_auth_mode()
    if mode == "Register":
        _handle_register_mode()
        return
    _handle_login_mode()
