## ui/company.py
import streamlit as st
from services.api_client import fetch_company, save_company
from util import to_list_from_products_field, to_backend_products_field

def company_gate():
    if st.session_state.get("company_cache") is None:
        st.session_state["company_cache"] = fetch_company()
    company = st.session_state.get("company_cache")

    if company:
        st.success("Company data loaded.")
        with st.expander("Company", expanded=True):
            st.write(f"**Company:** {company.get('company_name','')}")
            st.write(f"**Location:** {company.get('location','')}")
            st.write(f"**Target Customer:** {company.get('target_customer','')}")
            st.write("**Products:**")
            for p in to_list_from_products_field(company.get("products", "")) or ["None"]:
                st.write(f"- {p}")
            st.write("**Profile:**")
            st.markdown(company.get("company_profile", "") or "_No profile_")
        return company

    # If no company data exists, inform the user explicitly
    st.warning("No company data found for this account. Please register your company details.")

    st.header("Enter Company Data")
    with st.form("company_form"):
        c_name = st.text_input("Company Name")
        c_profile = st.text_area("Company Profile", height=160)
        c_products_text = st.text_area(
            "Products (one per line)",
            height=110,
            placeholder="Product A
Product B"
        )
        c_location = st.text_input("Location")
        c_target = st.text_input("Target Customer")
        c_submit = st.form_submit_button("Save Company")

    if c_submit:
        products_list = [p.strip() for p in c_products_text.splitlines() if p.strip()]
        payload = {
            "company_name": (c_name or "").strip(),
            "company_profile": (c_profile or "").strip(),
            "products": to_backend_products_field(products_list),
            "location": (c_location or "").strip(),
            "target_customer": (c_target or "").strip(),
        }
        missing = [k for k, v in payload.items() if not v]
        if missing:
            st.error(f"Missing required fields: {', '.join(missing)}")
        else:
            if save_company(payload):
                st.success("Company data saved successfully.")
                st.session_state["company_cache"] = fetch_company() or payload
                st.rerun()

    st.stop()  # Block until company exists
