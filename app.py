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

# --- REGISTER OR LOGIN ---
st.title("📣 Campaign Generator")

if not st.session_state.registered:
    tab1, tab2 = st.tabs(["Register", "Login"])

    with tab1:
        st.subheader("🔐 Register")
        reg_name = st.text_input("Name", key="reg_name")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_apikey = st.text_input("API Key", key="reg_apikey")
        if st.button("Register"):
            payload = {"name": reg_name, "password": reg_password, "api_key": reg_apikey}
            r = requests.post(f"{BASE_URL}/register", json=payload)
            if r.status_code == 200:
                st.success("Registered successfully")
                st.session_state.registered = True
                st.session_state.name = reg_name
                st.session_state.api_key = reg_apikey
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
            else:
                st.error(r.json().get("detail", "Registration failed"))

    with tab2:
        st.subheader("🔑 Login")
        login_name = st.text_input("Name (Login)", key="login_name")
        login_apikey = st.text_input("API Key (Login)", key="login_apikey")
        if st.button("Login"):
            st.session_state.name = login_name
            st.session_state.api_key = login_apikey
            st.session_state.registered = True

# --- AFTER LOGIN & API KEY SET ---
if st.session_state.registered and st.session_state.api_key:
    name = st.session_state.name
    st.success(f"Logged in as {name}")

    tab_company, tab_history, tab_generate = st.tabs(["🏢 Company Data", "📂 Campaign History", "🧠 Generate Campaign"])

    # --- COMPANY DATA ENTRY ---
    with tab_company:
        st.header("🏢 Company Info")
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
            headers = {"x-api-key": st.session_state.api_key}
            r = requests.post(f"{BASE_URL}/company", json=payload, headers=headers)
            if r.status_code == 200:
                st.success("Company data saved")
                st.session_state.company_data_entered = True
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
            else:
                st.error("Error saving company data")
