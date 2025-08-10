## services/api_client.py

from typing import Optional, Dict, Any, List
import requests
import streamlit as st
from state import auth_headers
from constants import EP


def http_get(url: str, params: Optional[Dict[str, Any]] = None, needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.get(url, params=params, headers=headers, timeout=60)


def http_post(url: str, json_payload: Dict[str, Any], needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.post(url, json=json_payload, headers=headers, timeout=60)


def http_patch(url: str, json_payload: Dict[str, Any], needs_auth: bool = False):
    headers = auth_headers() if needs_auth else {}
    return requests.patch(url, json=json_payload, headers=headers, timeout=60)


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
