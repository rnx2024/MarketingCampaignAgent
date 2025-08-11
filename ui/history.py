import streamlit as st
from services.api_client import fetch_campaigns

def render_history() -> None:
    st.subheader("Campaign History")
    rows = fetch_campaigns()
    if not rows:
        st.info("No campaigns yet.")
        return

    # Only include these columns (no status)
    cols = ["id", "created_at", "product", "campaign_type", "channel", "output_type", "result_notes"]
    table = [{k: r.get(k) for k in cols if k in r} for r in rows] if isinstance(rows, list) else rows

    st.dataframe(table, use_container_width=True)
