import streamlit as st
import requests
from fpdf import FPDF

# --- CONFIG ---
BASE_URL = "https://marketing-agent-api-latest.onrender.com"

st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")

# --- SESSION STATE INIT ---
if "registered" not in st.session_state:
    st.session_state.registered = False
if "company_data_entered" not in st.session_state:
    st.session_state.company_data_entered = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "name" not in st.session_state:
    st.session_state.name = ""
if "just_registered" not in st.session_state:
    st.session_state.just_registered = False

# --- UI TITLE ---
st.title("📣 Campaign Generator")

# --- BEFORE LOGIN: Show Register and Login Tabs ---
if not st.session_state.api_key:
    tab1, tab2 = st.tabs(["Register", "Login"])

    # --- REGISTER TAB ---
    with tab1:
        st.subheader("🔐 Register")
        reg_name = st.text_input("Name", key="reg_name")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_apikey = st.text_input("API Key", key="reg_apikey")
        if st.button("Register"):
            payload = {"name": reg_name, "password": reg_password, "api_key": reg_apikey}
            r = requests.post(f"{BASE_URL}/register", json=payload)
            if r.status_code == 200:
                st.success("Registered successfully. Now please log in.")
                st.session_state.just_registered = True
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
            else:
                st.error(r.json().get("detail", "Registration failed"))

    # --- LOGIN TAB ---
    with tab2:
        st.subheader("🔑 Login")
        login_name = st.text_input("Name (Login)", key="login_name")
        login_apikey = st.text_input("API Key (Login)", key="login_apikey")
        if st.button("Login"):
            st.session_state.name = login_name
            st.session_state.api_key = login_apikey
            st.session_state.registered = True
            st.session_state.just_registered = False

    # Info after successful register
    if st.session_state.just_registered:
        st.info("✅ Now go to the Login tab and enter your credentials to continue.")

# --- AFTER LOGIN: Show Functional Tabs ---
elif st.session_state.registered and st.session_state.api_key:
    name = st.session_state.name
    st.success(f"✅ Logged in as {name}")

    tab_company, tab_history, tab_generate = st.tabs([
        "🏢 Company Data",
        "📂 Campaign History",
        "🧠 Generate Campaign"
    ])

    # --- COMPANY DATA TAB ---
    with tab_company:
        st.header("🏢 Company Info")

        headers = {"x-api-key": st.session_state.api_key}

        if not st.session_state.company_data_entered:
            company_name = st.text_input("Company Name")
            company_profile = st.text_area("Company Profile")
            products = st.text_input("Main Products (comma-separated)")
            location = st.text_input("Location")
            target_customer = st.text_input("Target Customer (e.g. students, professionals)")

            if st.button("Submit Company Data"):
                payload = {
                    "company_name": company_name,
                    "company_profile": company_profile,
                    "products": products,
                    "location": location,
                    "target_customer": target_customer
                }
                r = requests.post(f"{BASE_URL}/company", json=payload, headers=headers)
                if r.status_code == 200:
                    st.success("✅ Company data saved")
                    st.session_state.company_data_entered = True
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
                else:
                    st.error("Error saving company data")
        else:
            # Show read-only company data
            r = requests.get(f"{BASE_URL}/company", headers=headers)
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

    # --- CAMPAIGN HISTORY TAB ---
    with tab_history:
        if not st.session_state.company_data_entered:
            st.info("📂 Submit company data first to record campaign history.")
        else:
            st.subheader("🗄️ Record Campaign History")

            hist_product = st.text_input("Product", key="hist_product")
            hist_channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube"], key="hist_channel")
            hist_output_type = st.selectbox("Output Type", ["Script", "Email Copy", "Ad Copy"], key="hist_output_type")
            hist_result = st.text_area("Campaign Result", key="hist_result")
            hist_agent = st.selectbox("Created by Agent?", ["Yes", "No"], key="hist_agent")

            if st.button("📅 Submit Campaign History"):
                payload = {
                    "name": st.session_state.name,
                    "product": hist_product,
                    "channel": hist_channel,
                    "output_type": hist_output_type,
                    "result": hist_result,
                    "agent_created": hist_agent == "Yes"
                }
                headers = {"x-api-key": st.session_state.api_key}
                r = requests.post(f"{BASE_URL}/campaign/history", json=payload, headers=headers)
                if r.status_code == 200:
                    st.success("✅ Campaign history saved")
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
                else:
