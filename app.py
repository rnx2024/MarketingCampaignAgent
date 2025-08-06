import streamlit as st
import requests

# API base URL — your deployed FastAPI backend
API_BASE = "https://marketing-agent-latest.onrender.com"

# Page setup
st.set_page_config(page_title="Marketing Agent", page_icon="📣", layout="centered")
st.title("📣 Marketing Campaign Generator")

# Input form
with st.form("campaign_form"):
    brand = st.text_input("Brand Name", value="GlowNest")
    brand_overview = st.text_area("Brand Overview", value="GlowNest is a modern wellness brand focused on natural skincare solutions.")
    product = st.selectbox("Product", ["Radiant Day Cream", "GlowSerum", "Botanical Cleanser"])
    channels = st.multiselect(
        "Channels", 
        ["Facebook", "Instagram", "TikTok", "YouTube", "TV", "Print", "Billboard", "All Media"], 
        default=["Instagram", "TikTok"]
    )
    campaign_type = st.selectbox("Campaign Type", ["Product Launch", "Holiday Sale", "Store Sale", "Big Event", "Online Sale"])
    tone = st.selectbox("Tone", ["Playful", "Professional", "Empowering", "Urgent", "Inspirational"])
    budget = st.text_input("Budget", "$5,000")
    duration = st.text_input("Campaign Duration", "2 weeks")

    submit = st.form_submit_button("Generate Campaign Plan")

# API call
if submit:
    with st.spinner("Calling your AI agent..."):
        payload = {
            "brand": brand,
            "brand_overview": brand_overview,
            "product": product,
            "product_features": ["SPF 30", "Vitamin C", "Lightweight"],  # Fixed sample values
            "product_pricing": "$39.99",
            "brief": f"{campaign_type} campaign for {product}",
            "persona": "Urban professionals",
            "location": "US",
            "tone": tone,
            "goal": "Drive awareness and conversions",
            "cta": "Buy now",
            "constraints": ["No medical claims"],
            "notes": "Focus on summer season benefits.",
            "channels": channels,
            "budget": budget,
            "duration": duration
        }

        try:
            res = requests.post(f"{API_BASE}/marketing/campaign", json=payload, timeout=60)
            res.raise_for_status()
            result = res.json()
            st.success("✅ Campaign Plan Generated!")

            st.subheader("📌 Plan")
            st.markdown(result["plan"])

            st.subheader("🚀 Execution")
            st.markdown(result["execution"])

            st.subheader("🧐 Review")
            st.markdown(result["review"])

        except Exception as e:
            st.error(f"❌ Error generating campaign: {e}")
