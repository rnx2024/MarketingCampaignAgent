import streamlit as st
from services.api_client import fetch_campaigns, update_campaign_status

STATUS_OPTIONS = ["pending", "started", "finished"]

def render_history() -> None:
    st.subheader("Campaign History")
    rows = fetch_campaigns()
    if not rows:
        st.info("No campaigns yet.")
        return

    # Display table
    cols = ["id", "created_at", "product", "campaign_type", "channel", "output_type", "status", "result_notes"]
    table = [{k: r.get(k) for k in cols if k in r} for r in rows] if isinstance(rows, list) else rows
    st.dataframe(table, use_container_width=True)

    st.markdown("---")
    st.markdown("### Update a Campaign")

    # Build choices
    id_rows = [r for r in rows if isinstance(r, dict) and r.get("id") is not None]
    ids = [r["id"] for r in id_rows]
    if not ids:
        st.info("No updatable rows.")
        return

    products = sorted({(r.get("product") or "") for r in id_rows if r.get("product")})
    date_options = sorted({(r.get("created_at") or "")[:10] for r in id_rows if r.get("created_at")})  # YYYY-MM-DD

    # Select campaign first
    campaign_id = st.selectbox("Campaign ID", ids, key="upd_id")
    selected = next((r for r in id_rows if r["id"] == campaign_id), {})

    # Compute defaults from selected row
    default_status = selected.get("status") if selected.get("status") in STATUS_OPTIONS else STATUS_OPTIONS[0]
    default_product = selected.get("product") or (products[0] if products else "")
    default_date = (selected.get("created_at") or "")[:10]
    if default_product and default_product not in products:
        products = [default_product] + [p for p in products if p != default_product]
    if default_date and default_date not in date_options:
        date_options = [default_date] + [d for d in date_options if d != default_date]

    col1, col2 = st.columns(2)
    with col1:
        new_status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(default_status), key="upd_status")
    with col2:
        product_guard = st.selectbox("Product", products, index=(products.index(default_product) if default_product in products else 0), key="upd_prod")

    date_guard = st.selectbox("Date (YYYY-MM-DD)", date_options, index=(date_options.index(default_date) if default_date in date_options else 0), key="upd_date")
    result_notes = st.text_area("Result Notes", value=selected.get("result_notes", ""), key="upd_notes")

    if st.button("Update Campaign", key="upd_btn"):
        if update_campaign_status(campaign_id, new_status, result_notes, product_guard or None, date_guard or None):
            st.success("Campaign updated.")
            st.rerun()
