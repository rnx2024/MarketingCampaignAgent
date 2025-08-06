import streamlit as st
import requests
import json

# --------------------------------
# CONFIG
# --------------------------------
API_BASE_URL = "https://marketing-agent-latest.onrender.com"  # <-- replace with your Render FastAPI URL

st.set_page_config(page_title="Marketing Agent", layout="centered")
st.title("📢 Marketing Agent Frontend")

def post_json(endpoint, payload):
    """Send POST request to the FastAPI backend."""
    try:
        res = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=60)
        res.raise_for_status()
        return res.json(), None
    except requests.exceptions.RequestException as e:
        return None, str(e)

# --------------------------------
# Tabs
# --------------------------------
tab1, tab2, tab3 = st.tabs(["Campaign", "Social Posts", "TikTok Script"])

# -------------------------
# Campaign Tab
# -------------------------
with tab1:
    st.subheader("Generate Campaign Plan")
    brand = st.text_input("Brand", "EcomSphere")
    product = st.text_input("Product", "Storefront Suite")
    brief = st.text_area("Brief", "Increase signups for free trial targeting boutique fashion sellers.")
    channels = st.multiselect("Channels", ["TikTok", "Facebook", "Instagram", "LinkedIn"], ["TikTok", "Facebook"])

    if st.button("Generate Campaign"):
        payload = {
            "brand": brand,
            "product": product,
            "brief": brief,
            "channels": channels
        }
        with st.spinner("Generating..."):
            data, err = post_json("/marketing/campaign", payload)
        if err:
            st.error(err)
        else:
            st.success("Done")
            st.write("**Plan**")
            st.code(data.get("plan", ""))
            st.write("**Execution**")
            st.code(data.get("execution", ""))
            st.write("**Review**")
            st.code(data.get("review", ""))

# -------------------------
# Social Posts Tab
# -------------------------
with tab2:
    st.subheader("Generate Social Posts")
    brand = st.text_input("Brand", "EcomSphere", key="s_brand")
    product = st.text_input("Product", "Storefront Suite", key="s_product")
    brief = st.text_area("Brief", "Social posts for free trial campaign.", key="s_brief")
    platforms = st.multiselect("Platforms", ["Facebook", "Instagram", "Twitter", "LinkedIn", "TikTok"], ["Facebook", "Instagram"])
    posts_per_platform = st.number_input("Posts per platform", min_value=1, max_value=10, value=3)

    if st.button("Generate Posts"):
        payload = {
            "brand": brand,
            "product": product,
            "brief": brief,
            "platforms": platforms,
            "posts_per_platform": posts_per_platform
        }
        with st.spinner("Generating..."):
            data, err = post_json("/marketing/social-posts", payload)
        if err:
            st.error(err)
        else:
            st.success("Done")
            st.json(data)

# -------------------------
# TikTok Tab
# -------------------------
with tab3:
    st.subheader("Generate TikTok Script")
    brand = st.text_input("Brand", "EcomSphere", key="t_brand")
    product = st.text_input("Product", "Storefront Suite", key="t_product")
    brief = st.text_area("Brief", "Short video for free trial promo.", key="t_brief")
    duration_seconds = st.number_input("Duration (seconds)", min_value=10, max_value=90, value=30)
    hook_style = st.selectbox("Hook Style", ["problem", "surprise", "stat", "benefit"], index=3)

    if st.button("Generate TikTok Script"):
        payload = {
            "brand": brand,
            "product": product,
            "brief": brief,
            "duration_seconds": duration_seconds,
            "hook_style": hook_style
        }
        with st.spinner("Generating..."):
            data, err = post_json("/marketing/tiktok-script", payload)
        if err:
            st.error(err)
        else:
            st.success("Done")
            st.json(data)
