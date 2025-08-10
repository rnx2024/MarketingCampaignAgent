# streamlit_app.py
import json
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional, List

import requests
import streamlit as st

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000").rstrip("/")

EP = {
    "register": f"{API_BASE_URL}/register",
    "login": f"{API_BASE_URL}/login",
    "company_get": f"{API_BASE_URL}/company",
    "company_post": f"{API_BASE_URL}/company",
    "campaign_generate": f"{API_BASE_URL}/marketing/generate",
    "campaigns": f"{API_BASE_URL}/campaigns",
}

CAMPAIGN_TYPES = ["Brand Awareness", "Lead Generation", "Product Launch", "Retention", "Seasonal/Promo"]
CHANNELS = ["Instagram Ads", "Facebook Ads", "TikTok Ads", "Google Ads", "Email", "LinkedIn"]
OUTPUT_TYPES = ["Social Media Post Series", "Ad Creatives", "Email Sequence", "Landing Page Brief", "Blog Series", "Video Scripts", "Campaign Plan"]

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _parse_iso_z(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def store_session_from_login(data: Dict[str, Any], fallback_name: str) -> None:
    token = data.get("token")
    expires_at = data.get("expires_at")
    backend_name = (data.get("name") or fallback_name or "").strip()
    if not (isinstance(token, str) and isinstance(expires_at, str) and backend_name):
        raise RuntimeError("Login response missing/invalid name, token or expires_at.")
    exp_dt = _parse_iso_z(expires_at)
    now_utc = datetime.now(timezone.utc)
    if exp_dt <= now_utc:
        raise RuntimeError("Session already expired.")
    if exp_dt.date() == now_utc.date():
        raise RuntimeError("Session expiry is today; policy requires a later date.")
    st.session_state["name"] = backend_name
    st.session_state["token"] = token
    st.session_state["expires_at"] = exp_dt.isoformat()

def is_authenticated() -> bool:
    name = st.session_state.get("name")
    token = st.session_state.get("token")
    expires_at = st.session_state.get("expires_at")
    if not (name and token and expires_at):
        return False
    try:
        exp = _parse_iso_z(expires_at)
        now_utc = datetime.now(timezone.utc)
        if exp <= now_utc:
            return False
        if exp.date() == date.today():
            return False
        return True
    except Exception:
        return False

def auth_headers() -> Dict[str, str]:
    if not is_authenticated():
        raise RuntimeError("Session invalid or expired.")
    return {"name": st.session_state["name"], "token": st.session_state["token"], "Content-Type": "application/json"}

def http_get(url: str, params: Optional[Dict[str, Any]] = None, needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.get(url, params=params, headers=headers, timeout=60)

def http_post(url: str, json_payload: Dict[str, Any], needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.post(url, json=json_payload, headers=headers, timeout=60)

def to_list_from_products_field(products_field: str | list) -> List[str]:
    if isinstance(products_field, list):
        return [str(x) for x in products_field]
    if isinstance(products_field, str):
        try:
            data = json.loads(products_field)
            if isinstance(data, list):
                return [str(x) for x in data]
        except Exception:
            pass
        return [p.strip() for p in products_field.split(",") if p.strip()]
    return []

def to_backend_products_field(products: List[str]) -> str:
    return json.dumps(products, ensure_ascii=False)

def fetch_company() -> Optional[Dict[str, Any]]:
    try:
        r = http_get(EP["company_get"], needs_auth=True)
    except requests.RequestException as e:
        st.error(f"Network error fetching company: {e}")
        return None
    if r.status_code == 200:
        try:
            return r.json()
        except Exception:
            st.warning("Company endpoint returned non-JSON payload.")
            return None
    if r.status_code in (204, 404):
        return None
    st.warning(f"Company fetch returned {r.status_code}: {r.text}")
    return None

def fetch_campaigns() -> List[Dict[str, Any]]:
    try:
        r = http_get(EP["campaigns"], needs_auth=True)
        if r.status_code == 200:
            return r.json() if r.headers.get("content-type","").lower().startswith("application/json") else []
        if r.status_code in (204, 404):
            return []
        st.warning(f"Campaigns fetch returned {r.status_code}: {r.text}")
        return []
    except requests.RequestException as e:
        st.error(f"Network error fetching campaigns: {e}")
        return []

# -----------------------------------------------------------------------------
# Session init
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Marketing Agent", layout="wide")
for k in ["name", "token", "expires_at", "company_cache", "products_cache", "just_registered"]:
    st.session_state.setdefault(k, None)

st.title("Marketing Agent")

# -----------------------------------------------------------------------------
# Flow: Auth screen (Register/Login) → Company screen → Main screen (History | Generate)
# -----------------------------------------------------------------------------
if not is_authenticated():
    # ---------- AUTH SCREEN ----------
    mode = st.radio(
        "Choose an action",
        options=["Login", "Register"] if not st.session_state["just_registered"] else ["Login"],
        index=0 if st.session_state["just_registered"] else 0,
        horizontal=True,
    )

    if mode == "Register":
        with st.form("register_form", clear_on_submit=False):
            st.subheader("Register")
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
            try:
                resp = http_post(EP["register"], payload)
                if resp.status_code == 200:
                    st.success("Registered. Proceed to Login.")
                    st.session_state["just_registered"] = True
                    st.rerun()
                elif resp.status_code in (403, 409, 422):
                    st.error(f"Registration failed ({resp.status_code}): {resp.text}")
                else:
                    st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
            except requests.RequestException as e:
                st.error(f"Network error during registration: {e}")

    # Show Login always to allow immediate login
    with st.form("login_form", clear_on_submit=False):
        st.subheader("Login")
        l_name = st.text_input("Name")
        l_password = st.text_input("Password", type="password")
        l_submit = st.form_submit_button("Login")
    if l_submit:
        payload = {"name": l_name.strip(), "password": l_password}
        try:
            resp = http_post(EP["login"], payload)
            if resp.status_code == 200:
                try:
                    login_json = resp.json()
                    store_session_from_login(login_json, l_name.strip())
                    st.success("Logged in.")
                    st.session_state["just_registered"] = None
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
            elif resp.status_code in (401, 404):
                st.error(f"Login failed ({resp.status_code}): {resp.text}")
            else:
                st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
        except requests.RequestException as e:
            st.error(f"Network error during login: {e}")

    st.stop()

# ---------- COMPANY SCREEN ----------
if st.session_state["company_cache"] is None:
    st.session_state["company_cache"] = fetch_company()

company = st.session_state["company_cache"]

if not company:
    st.subheader("Enter Company Data")
    with st.form("company_form", clear_on_submit=False):
        c_name = st.text_input("Company Name")
        c_profile = st.text_area("Company Profile", height=180)
        c_products_text = st.text_area("Products (one per line)", placeholder="Product A\nProduct B", height=120)
        c_location = st.text_input("Location")
        c_target = st.text_input("Target Customer")
        c_submit = st.form_submit_button("Save Company")

    if c_submit:
        products_list = [p.strip() for p in c_products_text.splitlines() if p.strip()]
        payload = {
            "company_name": (c_name or "").strip(),
            "company_profile": (c_profile or "").strip(),
            "products": to_backend_products_field(products_list),
            "location": (c_location or "").strip(),
            "target_customer": (c_target or "").strip(),
        }
        missing = [k for k, v in payload.items() if not v]
        if missing:
            st.error(f"Missing required fields: {', '.join(missing)}")
        else:
            try:
                r = http_post(EP["company_post"], payload, needs_auth=True)
            except requests.RequestException as e:
                st.error(f"Network error saving company: {e}")
            else:
                if r.status_code in (200, 201):
                    st.session_state["company_cache"] = fetch_company() or payload
                    st.success("Company saved.")
                    st.rerun()
                else:
                    st.error(f"Save failed ({r.status_code}): {r.text}")
    st.stop()

# ---------- MAIN SCREEN: History | Generate ----------
products = to_list_from_products_field(company.get("products", ""))
st.session_state["products_cache"] = products

tab_history, tab_generate = st.tabs(["Campaign History", "Generate Campaign"])

with tab_history:
    st.subheader("Campaign History")
    data = fetch_campaigns()
    if not data:
        st.info("No campaigns yet.")
    else:
        # Minimal columns; adjust to your /campaigns schema
        st.dataframe(data, use_container_width=True)

with tab_generate:
    st.subheader("Generate Campaign")
    if not products:
        st.warning("Add at least one product in Company data before generating campaigns.")
    else:
        with st.form("gen_form", clear_on_submit=False):
            g_product = st.selectbox("Product", products, index=0)
            g_campaign_type = st.selectbox("Campaign Type", CAMPAIGN_TYPES, index=0)
            g_channel = st.selectbox("Channel", CHANNELS, index=0)
            g_output_type = st.selectbox("Output Type", OUTPUT_TYPES, index=0)
            g_submit = st.form_submit_button("Generate")

        if g_submit:
            payload = {
                "product": g_product,
                "campaign_type": g_campaign_type,
                "channel": g_channel,
                "output_type": g_output_type,
            }
            try:
                r = http_post(EP["campaign_generate"], payload, needs_auth=True)
                if r.status_code == 200:
                    try:
                        result = r.json()
                    except Exception:
                        result = {"message": r.text}
                    st.success("Campaign generated.")
                    st.json(result)
                else:
                    st.error(f"Generation failed ({r.status_code}): {r.text}")
            except requests.RequestException as e:
                st.error(f"Network error generating campaign: {e}")
