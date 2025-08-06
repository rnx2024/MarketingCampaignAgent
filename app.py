import streamlit as st
import requests
from fpdf import FPDF
from io import BytesIO

# API base URL — your deployed FastAPI backend
API_BASE = "https://marketing-agent-api-latest.onrender.com"

# Page setup
st.set_page_config(page_title="Marketing Agent", page_icon="📣", layout="centered")
st.title("📣 Marketing Campaign Generator")

# Fetch constants from backend using query parameters
query_params = {
    "include_company": "true",
    "include_products": "true",
    "include_channels": "true",
    "include_campaigns": "true",
    "include_outputs": "true"
}

try:
    constants_res = requests.get(f"{API_BASE}/constants", params=query_params)
    constants_res.raise_for_status()
    constants = constants_res.json()
except Exception as e:
    st.error(f"Failed to fetch constants from API: {e}")
    st.stop()

# Input form
with st.form("campaign_form"):
    brand = st.text_input("Brand Name", value=constants.get("company_name", ""), disabled=True)
    brand_overview = st.text_area(
        "Brand Overview",
        value=f"{constants.get('company_name', '')} is {constants.get('company_document', '')}",
        disabled=True
    )
    product = st.selectbox("Product", constants.get("products_available", []))
    channels = st.multiselect("Channels", constants.get("channel_options", []), default=["Instagram", "TikTok"])
    campaign_type = st.selectbox("Campaign Type", constants.get("campaign_types", []))
    tone = st.selectbox("Tone", ["Playful", "Professional", "Empowering", "Urgent", "Inspirational"])
    budget = st.text_input("Budget", "$5,000", disabled=True)
    duration = st.text_input("Campaign Duration", "2 weeks", disabled=True)
    output = st.selectbox("Output Type", constants.get("output_types", []))

    submit = st.form_submit_button("Generate Campaign Plan")

# API call
if submit:
    with st.spinner("Calling your AI agent..."):
        payload = {
            "brand": brand,
            "brand_overview": brand_overview,
            "product": product,
            "product_features": ["SPF 30", "Vitamin C", "Lightweight"],
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
            "duration": duration,
            "output": output
        }

        try:
            res = requests.post(f"{API_BASE}/marketing/campaign", json=payload, timeout=60)
            res.raise_for_status()
            result = res.json()
            st.success("✅ Campaign Plan Generated!")

            st.subheader("📌 Plan")
            st.markdown(result["result"])

            # PDF generation
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in result["result"].split("\n"):
                pdf.multi_cell(0, 10, line)

            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)

            st.download_button(
                label="📄 Download Campaign Plan as PDF",
                data=buffer,
                file_name="campaign_plan.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"❌ Error generating campaign: {e}")
