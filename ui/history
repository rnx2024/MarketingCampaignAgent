## ui/history.py

import streamlit as st
from datetime import date
from services.api_client import fetch_campaigns, update_campaign_status


STATUS_OPTIONS = ["pending", "started", "finished"]


def render_history() -> None:
    st.subheader("Campaign History")
    rows = fetch_campaigns()
    if not rows:
        st.info("No campaigns yet.")
        return

    # Display
    cols = ["id", "created_at", "product", "campaign_type", "channel", "output_type", "status", "result_notes"]
    table = [{k: r.get(k) for k in cols if k in r} for r in rows] if isinstance(rows, list) else rows
    st.dataframe(table, use_container_width=True)

    st.markdown("---")
    st.markdown("### Update a Campaign")

    # Simple selector by id
    ids = [r.get("id") for r in rows if isinstance(r, dict) and r.get("id") is not None]
    if not ids:
        st.info("No updatable rows.")
        return

    campaign_id = st.selectbox("Campaign ID", ids)
    col1, col2 = st.columns(2)
    with col1:
        new_status = st.selectbox("Status", STATUS_OPTIONS)
    with col2:
        product_guard = st.text_input("Guard by Product (optional)")

    date_guard = st.text_input("Guard by Date YYYY-MM-DD (optional)")
    result_notes = st.text_area("Result Notes", placeholder="What happened? Metrics, notes, etc.")

    if st.button("Update Campaign"):
        if update_campaign_status(campaign_id, new_status, result_notes, product_guard or None, date_guard or None):
            st.success("Campaign updated.")
            st.rerun()
