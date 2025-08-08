import streamlit as st
import requests
from fpdf import FPDF

BASE_URL = "https://marketing-agent-v1-1.onrender.com/"

st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")

# --- Session State Init ---
for key in ["registered", "company_data_entered", "just_registered", "logged_in", "name", "cookies"]:
    if key not in st.session_state:
        st.session_state[key] = False if key != "name" and key != "cookies" else ("" if key == "name" else {})

# --- Utility: Handle Session Expiry ---
def handle_session_expiry(response):
    if response.status_code == 403 and "Session expired" in response.text:
        st.warning("⚠️ Session expired. Please log in again.")
        st.session_state.logged_in = False
        st.session_state.cookies = {}
        st.experimental_rerun()

# --- Title ---
st.title("📣 Campaign Generator")

# --- BEFORE LOGIN ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Register", "Login"])

    with tab1:
        st.subheader("🔐 Register")
        reg_name = st.text_input("Name", key="reg_name_input")
        reg_password = st.text_input("Password", type="password", key="reg_password_input")
        reg_apikey = st.text_input("API Key", key="reg_apikey_input")
        if st.button("Register", key="register_button"):
            payload = {"name": reg_name, "password": reg_password, "api_key": reg_apikey}
            r = requests.post(f"{BASE_URL}/register", json=payload)
            if r.status_code == 200:
                st.success("Registered successfully. Please log in.")
                st.session_state.just_registered = True
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded.")
            else:
                st.error(r.json().get("detail", "Registration failed."))

    with tab2:
        st.subheader("🔑 Login")
        login_name = st.text_input("Name", key="login_name_input")
        login_password = st.text_input("Password", type="password", key="login_password_input")

        if st.button("Login", key="login_button"):
            payload = {"name": login_name.strip(), "password": login_password}
            session = requests.Session()
            r = session.post(f"{BASE_URL}/login", json=payload)
            if r.status_code == 200:
                token_cookie = r.cookies.get("token")
                name_cookie = r.cookies.get("name")

                if token_cookie and name_cookie:
                    st.session_state.logged_in = True
                    st.session_state.name = name_cookie
                    st.session_state.cookies = {
                        "token": token_cookie,
                        "name": name_cookie
                    }
                    st.success(f"✅ Logged in as {name_cookie}")
                else:
                    st.error("Login failed: session cookies missing")
            elif r.status_code == 404:
                st.warning("🆔 User not found. Please register first.")
            elif r.status_code == 401:
                st.error("❌ Incorrect password.")
            elif r.status_code == 429:
                st.warning("⏱️ Too many attempts. Please wait.")
            else:
                st.error("⚠️ Login failed.")

# --- AFTER LOGIN ---
elif st.session_state.logged_in:
    name = st.session_state.name
    cookies = st.session_state.cookies
    session = requests.Session()
    st.success(f"✅ Logged in as {name}")

    tab_company, tab_history, tab_generate = st.tabs([
        "🏢 Company Data", "📂 Campaign History", "🧠 Generate Campaign"
    ])

    with tab_company:
        st.header("🏢 Company Info")
        if not st.session_state.company_data_entered:
            company_name = st.text_input("Company Name", key="company_name_input")
            company_profile = st.text_area("Company Profile", key="company_profile_input")
            products = st.text_input("Main Products (comma-separated)", key="products_input")
            location = st.text_input("Location", key="location_input")
            target_customer = st.text_input("Target Customer", key="target_customer_input")

            if st.button("Submit Company Data", key="submit_company_button"):
                payload = {
                    "company_name": company_name,
                    "company_profile": company_profile,
                    "products": products,
                    "location": location,
                    "target_customer": target_customer
                }
                r = session.post(f"{BASE_URL}/company", json=payload, headers={"name": name}, cookies=cookies)
                handle_session_expiry(r)
                if r.status_code == 200:
                    st.success("✅ Company data saved")
                    st.session_state.company_data_entered = True
                else:
                    st.error("Error saving company data")
        else:
            r = session.get(f"{BASE_URL}/company", headers={"name": name}, cookies=cookies)
            handle_session_expiry(r)
            if r.status_code == 200:
                company = r.json()
                st.subheader("📄 Submitted Company Info")
                st.markdown(f"**Company Name**: {company['company_name']}")
                st.markdown(f"**Company Profile**: {company['company_profile']}")
                st.markdown(f"**Products**: {company['products']}")
                st.markdown(f"**Location**: {company['location']}")
                st.markdown(f"**Target Customer**: {company['target_customer']}")
            else:
                st.error("⚠️ Failed to load company data.")

    with tab_history:
        if not st.session_state.company_data_entered:
            st.info("📂 Submit company data first.")
        else:
            st.subheader("🗄️ Record Campaign History")
            hist_product = st.text_input("Product", key="hist_product_input")
            hist_channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube", "Tiktok", "Social Media", "Radio", "TV", "All Media"], key="hist_channel_select")
            hist_output_type = st.selectbox("Output Type", ["Video Script", "Email Copy", "Facebook Ads", "Google Ads", "Social Media Posts", "Campaign Plan", "Radio/TV Commerical"], key="hist_output_type_select")
            hist_result = st.text_area("Campaign Result", key="hist_result_input")
            hist_agent = st.selectbox("Created by Agent?", ["Yes", "No"], key="hist_agent_select")

            if st.button("🗕️ Submit Campaign History", key="submit_history_button"):
                payload = {
                    "product": hist_product,
                    "channel": hist_channel,
                    "output_type": hist_output_type,
                    "result": hist_result,
                    "agent_created": hist_agent == "Yes"
                }
                r = session.post(f"{BASE_URL}/campaign/history", json=payload, headers={"name": name}, cookies=cookies)
                handle_session_expiry(r)
                if r.status_code == 200:
                    st.success("✅ Campaign history saved")
                else:
                    st.error("❌ Failed to save campaign history")

    with tab_generate:
        if not st.session_state.company_data_entered:
            st.info("🧠 Submit company data first.")
        else:
            st.subheader("🧠 Generate Campaign Plan")
            prod = st.text_input("Product", key="gen_product_input")
            channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube", "Tiktok", "Social Media", "Radio", "TV", "All Media"], key="gen_channel_select")
            ctype = st.selectbox("Campaign Type", ["Brand Awareness", "Lead Generation", "Product Launch", "Conversion", "Customer Retention", "Sales Promotion"], key="gen_campaign_type_select")
            otype = st.selectbox("Output Type", ["Video Script", "Email Copy", "Facebook Ads", "Google Ads", "Social Media Posts", "Campaign Plan", "Radio/TV Commerical"], key="gen_output_type_select")
            budget = st.text_input("Budget", key="gen_budget_input")
            duration = st.text_input("Duration", key="gen_duration_input")

            if st.button("Generate Campaign", key="generate_campaign_button"):
                payload = {
                    "product": prod,
                    "channel": channel,
                    "campaign_type": ctype,
                    "output_type": otype,
                    "budget": budget,
                    "duration": duration
                }
                r = session.post(f"{BASE_URL}/marketing/generate", json=payload, headers={"name": name}, cookies=cookies)
                handle_session_expiry(r)
                if r.status_code == 200:
                    data = r.json()
                    st.success("✅ Campaign Generated")
                    st.text_area("📋 Campaign Output", value=data.get("result", ""), height=300, key="gen_result_output")

                    if st.button("📄 Download PDF", key="download_pdf_button"):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.multi_cell(0, 10, data.get("result", ""))
                        pdf_bytes = pdf.output(dest='S').encode('latin-1')
                        st.download_button(
                            label="Download Campaign PDF",
                            data=pdf_bytes,
                            file_name="campaign_plan.pdf",
                            mime="application/pdf",
                            key="pdf_download_btn"
                        )
                else:
                    st.error("❌ Error generating campaign")
