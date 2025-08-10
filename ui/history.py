#ui/history.py

import streamlit as st
from services.api_client import fetch_campaigns, update_campaign_status

STATUS_OPTIONS = ["pending", "started", "finished"]

def render_history() -> None:
    st.subheader("Campaign History")
    rows = fetch_campaigns()
    if not rows:
        st.info("No campaigns yet.")
        return

    cols = ["id", "created_at", "product", "campaign_type", "channel", "output_type", "status", "result_notes"]
    table = [{k: r.get(k) for k in cols if k in r} for r in rows] if isinstance(rows, list) else rows
    st.dataframe(table, use_container_width=True)

    st.markdown("---")
    st.markdown("### Update a Campaign")

    # map id -> row
    id_rows = [r for r in rows if isinstance(r, dict) and r.get("id") is not None]
    ids = [r["id"] for r in id_rows]
    if not ids:
        st.info("No updatable rows.")
        return

    campaign_id = st.selectbox("Campaign ID", ids, key="upd_id")
    row = next((r for r in id_rows if r["id"] == campaign_id), {})
    product_val = row.get("product", "")
    created_val = (row.get("created_at") or "")[:10]  # YYYY-MM-DD

    c1, c2 = st.columns(2)
    with c1:
        new_status = st.selectbox("Status", STATUS_OPTIONS,
                                  index=STATUS_OPTIONS.index(row.get("status", "pending")) if row.get("status") in STATUS_OPTIONS else 0,
                                  key="upd_status")
    with c2:
        st.text_input("Product (from DB)", value=product_val, disabled=True, key="upd_prod_view")

    st.text_input("Date (from DB, YYYY-MM-DD)", value=created_val, disabled=True, key="upd_date_view")
    result_notes = st.text_area("Result Notes", value=row.get("result_notes") or "", key="upd_notes")

    if st.button("Update Campaign", key="upd_btn"):
        if update_campaign_status(campaign_id, new_status, result_notes, product_val or None, created_val or None):
            st.success("Campaign updated.")
            st.rerun()
