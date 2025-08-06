import streamlit as st
import requests
from fpdf import FPDF
from io import BytesIO

API_BASE = "https://marketing-agent-latest.onrender.com"

st.set_page_config(page_title="Marketing Agent", page_icon="📣", layout="centered")
st.title("📣 Marketing Campaign Generator")

# --- Fetch constants from API ---
with st.spinner("Fetching configuration from backend..."):
    constants = requests.get(f"{API_BASE}/constants").json()
    company_doc = requests.get(f"{API_BASE}/documents/company").json()["company_document"]

# --- UI Form ---
with st.form("campaign_form"):
    brand_details = st.text_area("Brand Details", company_doc)
    product = st.selectbox("Product", constants["products_available"], index=0)
    channel = st.selectbox("Channel", constants["channel_options"], index=0)
    campaign_type = st.selectbox("Campaign Type", constants["campaign_types"], index=0)
    tone = st.selectbox("Tone", ["confident", "friendly", "inspiring", "professional", "casual"])
    budget_duration = st.text_input("Budget & Duration", "P150,000 for 2 weeks")
    output = st.selectbox("Output Format", constants["output_types"], index=0)

    submit = st.form_submit_button("Generate Campaign Plan")

# --- API Call and Result Handling ---
if submit:
    with st.spinner("Calling your AI agent..."):
        payload = {
            "brand_details": brand_details,
            "product": product,
            "channel": channel,
            "campaign_type": campaign_type,
            "tone": tone,
            "budget_and_duration": budget_duration,
            "output": output
        }

        try:
            res = requests.post(f"{API_BASE}/marketing/generate", json=payload, timeout=60)
            res.raise_for_status()
            result = res.json()["result"]

            st.success("✅ Campaign Plan Generated!")
            st.subheader("📌 Generated Plan")
            st.markdown(result)

            # --- PDF Export Button ---
            def generate_pdf(content: str) -> BytesIO:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for line in content.split('\n'):
                    pdf.multi_cell(0, 10, line)
                buffer = BytesIO()
                pdf.output(buffer)
                buffer.seek(0)
                return buffer

            pdf_bytes = generate_pdf(result)
            st.download_button(
                label="📄 Download Plan as PDF",
                data=pdf_bytes,
                file_name="campaign_plan.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"❌ Error generating campaign: {e}")
