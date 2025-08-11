## constants.py

import streamlit as st

API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000").rstrip("/")

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
OUTPUT_TYPES = [
    "Social Media Post Series", "Ad Creatives", "Email Sequence", "Landing Page Brief",
    "Blog Series", "Video Scripts", "Campaign Plan"
]
