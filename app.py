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

# --- REGISTER OR LOGIN ---
st.title("📣 Campaign Generator")

if not st.session_state.registered:
    tab1, tab2 = st.tabs(["Register", "Login"])

    with tab1:
        st.subheader("🔐 Register")
        name = st.text_input("Name")
        password = st.text_input("Password", type="password")
        apikey = st.text_input("API Key")
        if st.button("Register"):
            payload = {"name": name, "password": password, "api_key": apikey}
            r = requests.post(f"{BASE_URL}/register", json=payload)
            if r.status_code == 200:
                st.success("Registered successfully")
                st.session_state.registered = True
                st.session_state.name = name
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
            else:
                st.error(r.json().get("detail", "Registration failed"))

    with tab2:
        st.subheader("🔑 Login")
        name = st.text_input("Name (Login)")
        if st.button("Login"):
            st.session_state.name = name
            st.session_state.registered = True

# --- AFTER LOGIN ---
if st.session_state.registered:
    name = st.session_state.name
    st.success(f"Logged in as {name}")

    # Tabs for company data, campaign history, and campaign generation
    tab_company, tab_history, tab_generate = st.tabs(["🏢 Company Data", "📂 Campaign History", "🧠 Generate Campaign"])

    # --- COMPANY DATA ENTRY ---
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

    # --- CAMPAIGN HISTORY INPUT ---
    with tab_history:
        st.header("🗄️ Past Campaign History (Optional)")
        hist_product = st.text_input("Product", key="hist_product")
        hist_channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube"], key="hist_channel")
        hist_output_type = st.selectbox("Output Type", ["Script", "Email Copy", "Ad Copy"], key="hist_output_type")
        hist_result = st.text_area("Campaign Result", key="hist_result")
        hist_agent = st.selectbox("Created by Agent?", ["Yes", "No"], key="hist_agent")

        if st.button("📅 Submit Campaign History"):
            payload = {
                "name": name,
                "product": hist_product,
                "channel": hist_channel,
                "output_type": hist_output_type,
                "result": hist_result,
                "agent_created": hist_agent == "Yes"
            }
            r = requests.post(f"{BASE_URL}/campaign/history", json=payload)
            if r.status_code == 200:
                st.success("History saved")
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
            else:
                st.error("Failed to save campaign history")

    # --- GENERATE CAMPAIGN ---
    with tab_generate:
        st.header("🧠 Generate Campaign Plan")
        prod = st.text_input("Product (from your saved products)", key="gen_product")
        channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube"], key="gen_channel")
        ctype = st.selectbox("Campaign Type", ["Awareness", "Conversion", "Retention"], key="gen_type")
        otype = st.selectbox("Output Type", ["Script", "Email Copy", "Ad Copy"], key="gen_output")
        budget = st.text_input("Budget", key="gen_budget")
        duration = st.text_input("Duration", key="gen_duration")

        if st.button("Generate Campaign"):
            payload = {
                "name": name,
                "product": prod,
                "channel": channel,
                "campaign_type": ctype,
                "output_type": otype,
                "budget": budget,
                "duration": duration
            }
            r = requests.post(f"{BASE_URL}/marketing/generate", json=payload)
            if r.status_code == 200:
                data = r.json()
                st.success("Campaign Generated")
                st.text_area("📋 Campaign Output", value=data.get("campaign_plan"), height=300)

                # --- PDF Download ---
                if st.button("📄 Download PDF"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, data.get("campaign_plan"))

                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="Download Campaign PDF",
                        data=pdf_bytes,
                        file_name="campaign_plan.pdf",
                        mime="application/pdf"
                    )
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded. Please wait and try again.")
            else:
                st.error("Error generating campaign")
