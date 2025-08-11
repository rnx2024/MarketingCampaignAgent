from typing import Optional, Dict, Any, List
import requests
import streamlit as st
from state import auth_headers
from constants import EP


def _merge_headers(needs_auth: bool, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h: Dict[str, str] = {}
    if needs_auth:
        h.update(auth_headers())
    if extra:
        h.update(extra)
    return h


def http_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    needs_auth: bool = False,
    headers: Optional[Dict[str, str]] = None
):
    return requests.get(url, params=params, headers=_merge_headers(needs_auth, headers), timeout=60)


def http_post(
    url: str,
    json_payload: Dict[str, Any],
    needs_auth: bool = False,
    headers: Optional[Dict[str, str]] = None
):
    return requests.post(url, json=json_payload, headers=_merge_headers(needs_auth, headers), timeout=60)


def http_patch(
    url: str,
    json_payload: Dict[str, Any],
    needs_auth: bool = False,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None
):
    return requests.patch(
        url,
        json=json_payload,
        params=params,
        headers=_merge_headers(needs_auth, headers),
        timeout=60,
    )


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


def save_company(payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> bool:
    try:
        r = http_post(EP["company_post"], payload, needs_auth=True, headers=headers)
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
