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
        email = st.text_input("Email")
        apikey = st.text_input("API Key")
        if st.button("Register"):
            payload = {"name": name, "email": email, "api_key": apikey}
            r = requests.post(f"{BASE_URL}/register", json=payload)
            if r.status_code == 200:
                st.success("Registered successfully")
                st.session_state.registered = True
                st.session_state.email = email
            else:
                st.error("Registration failed")

    with tab2:
        st.subheader("🔑 Login")
        email = st.text_input("Email (Login)")
        if st.button("Login"):
            # no backend check needed, just a state change for frontend access
            st.session_state.email = email
            st.session_state.registered = True

if st.session_state.registered:
    email = st.session_state.email
    st.success(f"Logged in as {email}")

    # --- COMPANY DATA ENTRY ---
    if not st.session_state.company_data_entered:
        st.header("🏢 Company Info")
        brand = st.text_input("Brand Name")
        overview = st.text_area("Brand Overview")
        product = st.text_input("Product Name")
        features = st.text_area("Product Features (comma separated)")
        pricing = st.text_input("Product Pricing")
        brief = st.text_area("Brief")
        persona = st.text_input("Target Persona")
        location = st.text_input("Location")
        tone = st.selectbox("Tone", ["Professional", "Casual", "Funny"])
        goal = st.text_input("Marketing Goal")
        cta = st.text_input("Call to Action")
        constraints = st.text_area("Constraints (comma separated)")
        notes = st.text_area("Notes")

        if st.button("Submit Company Data"):
            payload = {
                "email": email,
                "brand": brand,
                "brand_overview": overview,
                "product": product,
                "product_features": [x.strip() for x in features.split(",")],
                "product_pricing": pricing,
                "brief": brief,
                "persona": persona,
                "location": location,
                "tone": tone,
                "goal": goal,
                "cta": cta,
                "constraints": [x.strip() for x in constraints.split(",")],
                "notes": notes
            }
            r = requests.post(f"{BASE_URL}/company", json=payload)
            if r.status_code == 200:
                st.success("Company data saved")
                st.session_state.company_data_entered = True
            else:
                st.error("Error saving company data")

    # --- CAMPAIGN HISTORY INPUT ---
    st.header("🗄️ Past Campaign History (Optional)")
    hist_product = st.text_input("Product")
    hist_channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube"])
    hist_output_type = st.selectbox("Output Type", ["Script", "Email Copy", "Ad Copy"])
    hist_result = st.text_area("Campaign Result")
    hist_agent = st.selectbox("Created by Agent?", ["Yes", "No"])

    if st.button("📅 Submit Campaign History"):
        payload = {
            "email": email,
            "product": hist_product,
            "channel": hist_channel,
            "output_type": hist_output_type,
            "result": hist_result,
            "agent_created": hist_agent == "Yes"
        }
        r = requests.post(f"{BASE_URL}/campaign/history", json=payload)
        if r.status_code == 200:
            st.success("History saved")
        else:
            st.error("Failed to save campaign history")

    # --- GENERATE CAMPAIGN ---
    st.header("🏢 Generate Campaign Plan")
    prod = st.text_input("Product (from your saved products)")
    channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube"])
    ctype = st.selectbox("Campaign Type", ["Awareness", "Conversion", "Retention"])
    otype = st.selectbox("Output Type", ["Script", "Email Copy", "Ad Copy"])
    budget = st.text_input("Budget")
    duration = st.text_input("Duration")

    if st.button("Generate Campaign"):
        payload = {
            "email": email,
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
        else:
            st.error("Error generating campaign")
