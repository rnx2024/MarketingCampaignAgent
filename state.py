# state.py
from datetime import datetime, timezone
from typing import Dict, Any
import streamlit as st


def init_session():
    """Initialize default session state variables."""
    for k in ["name", "token", "expires_at", "company_cache", "auth_mode"]:
        st.session_state.setdefault(k, None)


def _parse_iso_z(dt_str: str) -> datetime:
    """Parse an ISO8601 datetime string, handling trailing Z."""
    dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def store_session_from_login(data: Dict[str, Any], fallback_name: str) -> None:
    """
    Store name, token, and expiry in the session state after login.
    Ensures the token has not expired.
    """
    token = data.get("token")
    expires_at = data.get("expires_at")
    backend_name = (data.get("name") or fallback_name or "").strip()

    if not (token and expires_at and backend_name):
        raise RuntimeError("Login response missing name/token/expires_at.")

    exp_dt = _parse_iso_z(expires_at)
    if exp_dt <= datetime.now(timezone.utc):
        raise RuntimeError("Session already expired.")

    st.session_state.update(
        name=backend_name,
        token=token,
        expires_at=exp_dt.isoformat()
    )


def is_authenticated() -> bool:
    """Return True if session has valid name, token, and non-expired expiry."""
    try:
        name = st.session_state.get("name")
        token = st.session_state.get("token")
        exp = st.session_state.get("expires_at")
        if not (name and token and exp):
            return False
        return _parse_iso_z(exp) > datetime.now(timezone.utc)
    except Exception:
        return False


def auth_headers() -> Dict[str, str]:
    """
    Return headers required for authenticated API calls.
    Raises RuntimeError if not authenticated.
    """
    if not is_authenticated():
        raise RuntimeError("Invalid session.")
    return {
        "name": st.session_state["name"],
        "token": st.session_state["token"],
        "Content-Type": "application/json"
    }
