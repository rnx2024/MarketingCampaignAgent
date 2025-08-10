## ui/generate.py
import streamlit as st
from constants import CAMPAIGN_TYPES, CHANNELS, OUTPUT_TYPES
from services.api_client import generate_campaign, fetch_company
from services.pdf import build_campaign_pdf  # <-- add
from util import to_list_from_products_field

def render_generate(company: dict) -> None:
    st.subheader("Generate Campaign")
    products = to_list_from_products_field(company.get("products", "")) or []

    with st.form("gen_form"):
        g_product = st.selectbox("Product", products, index=0 if products else None, disabled=not products)
        g_campaign_type = st.selectbox("Campaign Type", CAMPAIGN_TYPES, index=0)
        g_channel = st.selectbox("Channel", CHANNELS, index=0)
        g_output_type = st.selectbox("Output Type", OUTPUT_TYPES, index=0)
        g_duration = st.text_input("Duration (optional)", placeholder="e.g., 6 weeks")
        g_budget = st.text_input("Budget (optional)", placeholder="e.g., $10,000")
        g_goal = st.text_area("Goal (optional)", placeholder="Describe the business goal")
        g_submit = st.form_submit_button("Generate")

    if not g_submit:
        return

    latest_company = fetch_company()
    if not latest_company:
        st.error("No saved company data found. Save company data first.")
        st.stop()
    if not g_product:
        st.error("Select a product.")
        st.stop()

    payload = {
        "product": g_product,
        "campaign_type": g_campaign_type,
        "channel": g_channel,
        "output_type": g_output_type,
    }
    if g_duration.strip():
        payload["duration"] = g_duration.strip()
    if g_budget.strip():
        payload["budget"] = g_budget.strip()
    if g_goal.strip():
        payload["goal"] = g_goal.strip()

    result = generate_campaign(payload)
    if result is None:
        return

    st.success("Campaign generated.")
    st.markdown("### Brand Context")
    st.markdown(result.get("brand_context", ""))
    st.markdown("### Past Insights")
    st.markdown(result.get("past_insights", ""))
    st.markdown("### Plan")
    st.markdown(result.get("plan", ""))

    # Build and offer PDF download
    pdf_bytes = build_campaign_pdf(
        company_name=latest_company.get("company_name", ""),
        meta={
            "product": g_product,
            "campaign_type": g_campaign_type,
            "channel": g_channel,
            "output_type": g_output_type,
            "duration": payload.get("duration"),
            "budget": payload.get("budget"),
        },
        brand_context=result.get("brand_context", ""),
        past_insights=result.get("past_insights", ""),
        plan=result.get("plan", ""),
    )
    st.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name=f"campaign_{g_product.replace(' ', '_').lower()}.pdf",
        mime="application/pdf",
    )
