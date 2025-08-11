# state.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import streamlit as st


# ---------- session bootstrapping ----------
def init_session() -> None:
    """Ensure required keys exist in session_state."""
    st.session_state.setdefault("name", None)
    st.session_state.setdefault("token", None)
    # store epoch seconds for expiry (backend v2 uses epoch)
    st.session_state.setdefault("expires_at", None)  # int | None
    st.session_state.setdefault("company_cache", None)
    st.session_state.setdefault("auth_pref", "Login")


# ---------- helpers ----------
def _now_epoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _to_epoch(v: Any) -> Optional[int]:
    """
    Convert backend 'expires_at' to epoch seconds.
    Accepts int epoch or ISO string (legacy).
    """
    if v is None:
        return None
    # already epoch?
    try:
        iv = int(v)
        # treat suspicious small/negative as invalid
        if iv > 0:
            return iv
    except (ValueError, TypeError):
        pass
    # try ISO
    try:
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


# ---------- public API ----------
def store_session_from_login(data: Dict[str, Any], fallback_name: str) -> None:
    """
    Persist login response into session_state.
    Backend returns: { name, token, token_type, expires_at }.
    expires_at is epoch seconds (v2). We still accept ISO for safety.
    """
    token = (data.get("token") or "").strip()
    backend_name = (data.get("name") or fallback_name or "").strip()
    exp_epoch = _to_epoch(data.get("expires_at"))

    if not token or not backend_name or exp_epoch is None:
        raise RuntimeError("Login response missing name/token/expires_at.")

    if exp_epoch <= _now_epoch():
        raise RuntimeError("Session already expired.")

    st.session_state.update(
        name=backend_name,
        token=token,
        expires_at=exp_epoch,
    )


def is_authenticated() -> bool:
    name = st.session_state.get("name")
    token = st.session_state.get("token")
    exp = st.session_state.get("expires_at")
    if not (name and token and isinstance(exp, int)):
        return False
    return _now_epoch() < exp


def auth_headers(strict: bool = False) -> Dict[str, str]:
    """
    Build auth headers for API calls.
    - Always sets Content-Type.
    - Adds Authorization: Bearer <token> when present.
    - Optionally includes legacy `name` header (backend accepts it).
    - If strict=True and no token, raises.
    """
    h: Dict[str, str] = {"Content-Type": "application/json"}
    token = st.session_state.get("token")
    name = st.session_state.get("name")

    if token:
        h["Authorization"] = f"Bearer {token}"
    if name:
        h["name"] = name  # legacy guard, safe to remove later

    if strict and not token:
        raise RuntimeError("Invalid session.")

    return h


def session_seconds_left() -> Optional[int]:
    """Utility for UI: seconds until session expiry, or None if unknown."""
    exp = st.session_state.get("expires_at")
    if not isinstance(exp, int):
        return None
    return max(0, exp - _now_epoch())
