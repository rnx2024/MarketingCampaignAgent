# streamlit_app.py
import json
from datetime import datetime, timezone
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
    "campaign_update_base": f"{API_BASE_URL}/campaign/status",                 # PATCH /campaign/{id}/status
    "monthly_overview": f"{API_BASE_URL}/campaign/overview/monthly",
}

# Enumerations (adjust if you have a constants endpoint later)
CAMPAIGN_TYPES = [
    "Brand Awareness",
    "Lead Generation",
    "Product Launch",
    "Retention",
    "Seasonal/Promo",
]
CHANNELS = [
    "Instagram Ads",
    "Facebook Ads",
    "TikTok Ads",
    "Google Ads",
    "Email",
    "LinkedIn",
]
OUTPUT_TYPES = [
    "Social Media Post Series",
    "Ad Creatives",
    "Email Sequence",
    "Landing Page Brief",
    "Blog Series",
    "Video Scripts"        
]

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def auth_headers() -> Dict[str, str]:
    headers = {}
    if st.session_state.get("name"):
        headers["name"] = st.session_state["name"]
    if st.session_state.get("token"):
        headers["token"] = st.session_state["token"]
    return headers

def is_authenticated() -> bool:
    name = st.session_state.get("name")
    token = st.session_state.get("token")
    expires_at = st.session_state.get("expires_at")
    if not (name and token and expires_at):
        return False
    try:
        exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) < exp
    except Exception:
        return False

def require_auth_gate():
    if not is_authenticated():
        st.warning("You’re not logged in or your session expired. Please log in.")
        st.stop()

def http_get(url: str, params: Optional[Dict[str, Any]] = None, needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.get(url, params=params, headers=headers, timeout=60)

def http_post(url: str, json_payload: Dict[str, Any], needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.post(url, json=json_payload, headers=headers, timeout=60)

def http_patch(url: str, json_payload: Dict[str, Any], needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.patch(url, json=json_payload, headers=headers, timeout=60)

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
    # Your backend accepts a string; if you later standardize to JSON, change here.
    # Keeping JSON string is convenient if you already use it.
    return json.dumps(products, ensure_ascii=False)

# -----------------------------------------------------------------------------
# Session init
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Marketing Campaign Agent", page_icon="📈", layout="wide")
for k in ["name", "token", "expires_at", "company_cache", "products_cache", "history_cache"]:
    st.session_state.setdefault(k, None)

st.title("Marketing Campaign Agent")

# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------
auth_tab, app_tab = st.tabs(["Auth", "App"])

# =========================
# Auth
# =========================
with auth_tab:
    reg_tab, login_tab = st.tabs(["Register", "Login"])

    with reg_tab:
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
                    st.success("Registered successfully. You can now log in.")
                elif resp.status_code in (403, 409, 422):
                    st.error(f"Registration failed ({resp.status_code}): {resp.text}")
                else:
                    st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
            except requests.RequestException as e:
                st.error(f"Network error during registration: {e}")

    with login_tab:
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
                    data = resp.json()
                    st.session_state["name"] = l_name.strip()
                    st.session_state["token"] = data.get("token")
                    st.session_state["expires_at"] = data.get("expires_at")
                    if is_authenticated():
                        st.success("Logged in.")
                    else:
                        st.error("Login response missing/invalid token or expiry.")
                elif resp.status_code in (401, 404):
                    st.error(f"Login failed ({resp.status_code}): {resp.text}")
                else:
                    st.error(f"Unexpected response ({resp.status_code}): {resp.text}")
            except requests.RequestException as e:
                st.error(f"Network error during login: {e}")

# =========================
# App
# =========================
with app_tab:
    if not is_authenticated():
        st.info("Please log in to access the app.")
        st.stop()

    company_tab, campaigns_tab, reports_tab = st.tabs(["Company", "Campaigns", "Reports"])

    # ----------------------
    # Company
    # ----------------------
    with company_tab:
        st.subheader("Company")
        # Load once per session (cache)
        if st.session_state["company_cache"] is None:
            try:
                r = http_get(EP["company_get"], needs_auth=True)
                if r.status_code == 200:
                    st.session_state["company_cache"] = r.json()
                elif r.status_code == 404:
                    st.session_state["company_cache"] = None
                else:
                    st.warning(f"Company fetch returned {r.status_code}: {r.text}")
            except requests.RequestException as e:
                st.error(f"Network error fetching company: {e}")

        company = st.session_state["company_cache"]

        if company:
            products = to_list_from_products_field(company.get("products", ""))
            st.session_state["products_cache"] = products
            with st.expander("Company Data", expanded=True):
                st.write(f"**Company:** {company.get('company_name','')}")
                st.write(f"**Location:** {company.get('location','')}")
                st.write(f"**Target Customer:** {company.get('target_customer','')}")
                st.write("**Products:**")
                if products:
                    for p in products:
                        st.write(f"- {p}")
                else:
                    st.write("- None")
                st.write("**Profile:**")
                st.markdown(company.get("company_profile", "") or "_No profile_")
            st.info("Company data set. You can generate campaigns or view history.")
        else:
            st.warning("No company data yet. Enter your company details once.")
            with st.form("company_form", clear_on_submit=False):
                c_name = st.text_input("Company Name")
                c_profile = st.text_area("Company Profile", height=180)
                c_products_text = st.text_area(
                    "Products (one per line)",
                    placeholder="Product A\nProduct B\nProduct C",
                    height=120,
                )
                c_location = st.text_input("Location")
                c_target = st.text_input("Target Customer")
                c_submit = st.form_submit_button("Save Company")
            if c_submit:
                products_list = [p.strip() for p in c_products_text.splitlines() if p.strip()]
                payload = {
                    "company_name": c_name.strip(),
                    "company_profile": c_profile.strip(),
                    "products": to_backend_products_field(products_list),
                    "location": c_location.strip(),
                    "target_customer": c_target.strip(),
                }
                try:
                    r = http_post(EP["company_post"], payload, needs_auth=True)
                    if r.status_code == 200:
                        st.success("Company saved.")
                        st.session_state["company_cache"] = payload
                        st.session_state["products_cache"] = products_list
                    else:
                        st.error(f"Save failed ({r.status_code}): {r.text}")
                except requests.RequestException as e:
                    st.error(f"Network error saving company: {e}")

    # ----------------------
    # Campaigns
    # ----------------------
    with campaigns_tab:
        gen_tab, history_tab = st.tabs(["Generate", "History & Update"])

        # Generate
        with gen_tab:
            st.subheader("Generate Campaign")
            require_auth_gate()

            if st.session_state["company_cache"] is None:
                st.error("Add company data first (Company tab).")
                st.stop()

            products = st.session_state.get("products_cache") or to_list_from_products_field(
                st.session_state["company_cache"].get("products", "")
            )
            if not products:
                st.error("No products found. Update company products.")
                st.stop()

            with st.form("generate_form", clear_on_submit=False):
                g_product = st.selectbox("Product", options=products)
                g_type = st.selectbox("Campaign Type", options=CAMPAIGN_TYPES)
                g_channel = st.selectbox("Channel", options=CHANNELS)
                g_output = st.selectbox("Output Type", options=OUTPUT_TYPES)
                g_duration = st.text_input("Duration", placeholder="e.g., 3 months")
                g_budget = st.text_input("Budget", placeholder="e.g., $5,000")
                g_submit = st.form_submit_button("Generate")
            if g_submit:
                payload = {
                    "product": g_product,
                    "campaign_type": g_type,
                    "channel": g_channel,
                    "output_type": g_output,
                    "duration": g_duration.strip(),
                    "budget": g_budget.strip(),
                }
                try:
                    r = http_post(EP["campaign_generate"], payload, needs_auth=True)
                    if r.status_code == 200:
                        data = r.json()
                        st.success("Campaign generated and saved (status: pending).")
                        with st.expander("Generated Campaign", expanded=True):
                            st.json(data)
                    else:
                        st.error(f"Generate failed ({r.status_code}): {r.text}")
                except requests.RequestException as e:
                    st.error(f"Network error generating campaign: {e}")

        # History & Update
        with history_tab:
            st.subheader("Campaign History & Update")
            require_auth_gate()

            products = st.session_state.get("products_cache") or []
            c1, c2, c3 = st.columns([1, 1, 0.5])
            with c1:
                h_date = st.date_input("Date (YYYY-MM-DD)", format="YYYY-MM-DD")
            with c2:
                h_product = st.selectbox("Product", options=["(All)"] + products)
            with c3:
                refresh = st.button("Refresh")

            def fetch_history():
                params = {}
                if h_date:
                    params["date"] = h_date.isoformat()
                if h_product and h_product != "(All)":
                    params["product"] = h_product
                try:
                    r = http_get(EP["campaigns"], params=params, needs_auth=True)
                    if r.status_code == 200:
                        return r.json()
                    elif r.status_code == 404:
                        return []
                    else:
                        st.error(f"History fetch returned {r.status_code}: {r.text}")
                        return []
                except requests.RequestException as e:
                    st.error(f"Network error fetching history: {e}")
                    return []

            if refresh or st.session_state.get("history_cache") is None:
                st.session_state["history_cache"] = fetch_history()
            history = st.session_state["history_cache"]

            if not history:
                st.info("No campaigns found for the selected filters.")
            else:
                for row in history:
                    header = f"[{row.get('created_at','')}] {row.get('product','')} • {row.get('campaign_type','')} • {row.get('status','')}"
                    with st.expander(header, expanded=False):
                        st.write(f"**Product:** {row.get('product','')}")
                        st.write(f"**Campaign Type:** {row.get('campaign_type','')}")
                        st.write(f"**Channel:** {row.get('channel','')}")
                        st.write(f"**Duration:** {row.get('duration','')}")
                        st.write(f"**Budget:** {row.get('budget','')}")
                        st.write(f"**Status:** {row.get('status','')}")
                        st.write("**Plan:**")
                        st.markdown(row.get("plan", "") or "_No plan text_")
                        st.write("**Result Notes:**")
                        st.write(row.get("result_notes", "") or "_None_")

                        st.markdown("---")
                        st.write("**Update Status** (requires both fields)")
                        form_key = f"upd_{row.get('id')}"
                        with st.form(form_key):
                            new_status = st.selectbox(
                                "Status",
                                options=["started", "finished"],
                                index=0,
                                key=f"status_{row.get('id')}"
                            )
                            new_notes = st.text_area(
                                "Result Notes",
                                key=f"notes_{row.get('id')}",
                                placeholder="Add concrete outcomes, metrics, learnings…",
                            )
                            upd_btn = st.form_submit_button("Save Update")

                        if upd_btn:
                            if not (new_status and new_notes.strip()):
                                st.error("Both status and result_notes are required.")
                            else:
                                payload = {
                                    "status": new_status,
                                    "result_notes": new_notes.strip(),
                                }
                                # pass current filters as guards if set
                                if h_date:
                                    payload["date"] = h_date.isoformat()
                                if h_product and h_product != "(All)":
                                    payload["product"] = h_product

                                try:
                                    url = f"{EP['campaign_update_base']}/{row.get('id')}/status"
                                    r = http_patch(url, payload, needs_auth=True)
                                    if r.status_code == 200:
                                        st.success("Campaign updated.")
                                        st.session_state["history_cache"] = fetch_history()
                                    else:
                                        st.error(f"Update failed ({r.status_code}): {r.text}")
                                except requests.RequestException as e:
                                    st.error(f"Network error updating campaign: {e}")

    # ----------------------
    # Reports
    # ----------------------
    with reports_tab:
        st.subheader("Monthly Overview")
        require_auth_gate()

        if st.button("Load Overview"):
            try:
                r = http_get(EP["monthly_overview"], needs_auth=True)
                if r.status_code == 200:
                    overview = r.json()
                    if not overview:
                        st.info("No monthly data yet.")
                    else:
                        # Show latest month metrics if available
                        try:
                            latest = sorted(overview, key=lambda x: x.get("month", ""))[-1]
                            c1, c2 = st.columns(2)
                            c1.metric("Generated (latest month)", latest.get("total_generated", 0))
                            c2.metric("Finished (latest month)", latest.get("total_finished", 0))
                        except Exception:
                            pass
                        st.markdown("#### Monthly Stats")
                        st.dataframe(overview, use_container_width=True)
                else:
                    st.error(f"Overview returned {r.status_code}: {r.text}")
            except requests.RequestException as e:
                st.error(f"Network error fetching overview: {e}")
