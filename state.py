## state.py

from datetime import datetime, timezone, date
from typing import Dict, Any
import streamlit as st


def is_authenticated() -> bool:
    return bool(st.session_state.get("token") and st.session_state.get("name"))

def auth_headers(strict: bool = False) -> Dict[str, str]:
    """Return headers for auth. If strict=True and no token, raise."""
    h: Dict[str, str] = {"Content-Type": "application/json"}
    token = st.session_state.get("token")
    name = st.session_state.get("name")
    if token:
        h["Authorization"] = f"Bearer {token}"
    if name:
        h["name"] = name  # optional legacy
    if strict and not token:
        raise RuntimeError("Invalid session.")
    return h



def init_session():
    for k in ["name", "token", "expires_at", "company_cache", "auth_mode"]:
        st.session_state.setdefault(k, None)


def _parse_iso_z(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def store_session_from_login(data: Dict[str, Any], fallback_name: str) -> None:
    token = data.get("token")
    expires_at = data.get("expires_at")
    backend_name = (data.get("name") or fallback_name or "").strip()
    if not (token and expires_at and backend_name):
        raise RuntimeError("Login response missing name/token/expires_at.")
    exp_dt = _parse_iso_z(expires_at)
    now_utc = datetime.now(timezone.utc)
    if exp_dt <= now_utc or exp_dt.date() == now_utc.date():
        raise RuntimeError("Session expiry invalid.")
    st.session_state.update(name=backend_name, token=token, expires_at=exp_dt.isoformat())


def is_authenticated() -> bool:
    try:
        name, token, exp = (st.session_state.get("name"), st.session_state.get("token"), st.session_state.get("expires_at"))
        if not (name and token and exp):
            return False
        dt = _parse_iso_z(exp)
        return dt > datetime.now(timezone.utc) and dt.date() != date.today()
    except Exception:
        return False


def auth_headers() -> Dict[str, str]:
    if not is_authenticated():
        raise RuntimeError("Invalid session.")
    return {"name": st.session_state["name"], "token": st.session_state["token"], "Content-Type": "application/json"}
