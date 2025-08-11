# services/api_client.py
from typing import Optional, Dict, Any, List
import requests
import streamlit as st
from constants import EP
from state import auth_headers  # uses Bearer + optional name

_DEFAULT_TIMEOUT = 60

def http_get(url: str, params: Optional[Dict[str, Any]] = None, needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.get(url, params=params, headers=headers, timeout=_DEFAULT_TIMEOUT)

def http_post(url: str, json_payload: Dict[str, Any], needs_auth: bool = False, params: Optional[Dict[str, Any]] = None):
    headers = auth_headers() if needs_auth else {}
    return requests.post(url, json=json_payload, params=params, headers=headers, timeout=_DEFAULT_TIMEOUT)

def http_patch(url: str, json_payload: Dict[str, Any], needs_auth: bool = False, params: Optional[Dict[str, Any]] = None):
    headers = auth_headers() if needs_auth else {}
    return requests.patch(url, json=json_payload, params=params, headers=headers, timeout=_DEFAULT_TIMEOUT)

# Company
def fetch_company() -> Optional[Dict[str, Any]]:
    try:
        r = http_get(EP["company_get"], needs_auth=True)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (204, 404):
            return None
        st.warning(f"Company fetch {r.status_code}: {r.text}")
        return None
    except requests.RequestException as e:
        st.error(f"Network error fetching company: {e}")
        return None

def save_company(payload: Dict[str, Any]) -> bool:
    try:
        r = http_post(EP["company_post"], payload, needs_auth=True)
        if r.status_code in (200, 201):
            return True
        st.error(f"Save failed ({r.status_code}): {r.text}")
        return False
    except requests.RequestException as e:
        st.error(f"Network error saving company: {e}")
        return False

# Campaigns
def fetch_campaigns() -> List[Dict[str, Any]]:
    try:
        r = http_get(EP["campaigns"], needs_auth=True)
        if r.status_code == 200 and r.headers.get("content-type", "").lower().startswith("application/json"):
            return r.json()
        return []
    except requests.RequestException as e:
        st.error(f"Network error fetching campaigns: {e}")
        return []

def generate_campaign(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        r = http_post(EP["campaign_generate"], payload, needs_auth=True)
        if r.status_code == 200:
            return r.json()
        st.error(f"Generation failed ({r.status_code}): {r.text}")
        return None
    except requests.RequestException as e:
        st.error(f"Network error generating campaign: {e}")
        return None

def update_campaign_status(status: str, result_notes: str, product: Optional[str] = None, date_str: Optional[str] = None) -> bool:
    if not status or not result_notes:
        st.error("Status and result notes are required.")
        return False
    if not product and not date_str:
        st.error("Provide at least one of: product or date.")
        return False

    payload: Dict[str, Any] = {"status": status, "result_notes": result_notes}
    params: Dict[str, Any] = {}
    if product:
        params["product"] = product
    if date_str:
        params["date"] = date_str  # YYYY-MM-DD

    try:
        # aligns with backend: PATCH /campaign/status?product=...&date=...
        r = http_patch(EP["campaign_status"], payload, needs_auth=True, params=params)
        if r.status_code == 200:
            return True
        st.error(f"Update failed ({r.status_code}): {r.text}")
        return False
    except requests.RequestException as e:
        st.error(f"Network error updating campaign: {e}")
        return False
