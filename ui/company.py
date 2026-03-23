# ui/company.py
import streamlit as st
from services.api_client import fetch_company, save_company
from util import to_list_from_products_field
from state import auth_headers  # ensure we can attach auth headers

def _load_company():
    if st.session_state.get("company_cache") is None:
        try:
            st.session_state["company_cache"] = fetch_company()
        except RuntimeError as e:
            st.error(f"Session error: {e}")
            st.stop()
    return st.session_state.get("company_cache")


def _render_company(company):
    st.success("Company data loaded.")
    with st.expander("Company", expanded=True):
        st.write(f"**Company:** {company.get('company_name', '')}")
        st.write(f"**Location:** {company.get('location', '')}")
        st.write(f"**Target Customer:** {company.get('target_customer', '')}")
        st.write("**Products:**")
        for product in to_list_from_products_field(company.get("products", "")) or ["None"]:
            st.write(f"- {product}")
        st.write("**Profile:**")
        st.markdown(company.get("company_profile", "") or "_No profile_")


def _render_company_form():
    st.header("Enter Company Data")
    with st.form("company_form"):
        company_name = st.text_input("Company Name")
        company_profile = st.text_area("Company Profile", height=160)
        products_text = st.text_area(
            "Products (one per line)",
            height=110,
            placeholder="Product A\nProduct B",
        )
        location = st.text_input("Location")
        target_customer = st.text_input("Target Customer")
        submitted = st.form_submit_button("Save Company")

    products = [product.strip() for product in products_text.splitlines() if product.strip()]
    payload = {
        "company_name": (company_name or "").strip(),
        "company_profile": (company_profile or "").strip(),
        "products": ",".join(products),
        "location": (location or "").strip(),
        "target_customer": (target_customer or "").strip(),
    }
    return payload, submitted


def _validate_company_payload(payload):
    missing = [key for key, value in payload.items() if not value]
    if missing:
        st.error(f"Missing required fields: {', '.join(missing)}")
        return False
    return True


def _save_company_payload(payload):
    try:
        if not save_company(payload, headers=auth_headers()):
            return
        st.success("Company data saved successfully.")
        st.session_state["company_cache"] = fetch_company() or payload
        st.rerun()
    except RuntimeError as e:
        st.error(f"Session error: {e}")
        st.stop()


def company_gate():
    company = _load_company()
    if company:
        _render_company(company)
        return company

    st.warning("No company data found for this account. Please register your company details.")
    payload, submitted = _render_company_form()
    if submitted and _validate_company_payload(payload):
        _save_company_payload(payload)

    st.stop()  # Block until company exists
