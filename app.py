import streamlit as st
import requests
from fpdf import FPDF

BASE_URL = import streamlit as st
import requests
from fpdf import FPDF

BASE_URL = "https://marketing-agent-v1-1.onrender.com/"

st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")

# --- Initialize session state ---
if "session" not in st.session_state:
    st.session_state.session = requests.Session()

for key in ["registered", "company_data_entered", "just_registered", "logged_in", "name"]:
    if key not in st.session_state:
        st.session_state[key] = False if key != "name" else ""

# --- UI TITLE ---
st.title("📣 Campaign Generator")

# --- BEFORE LOGIN ---
if not st.session_state.logged_in:
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
                st.success("Registered successfully. Please log in.")
                st.session_state.just_registered = True
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded.")
            else:
                st.error(r.json().get("detail", "Registration failed."))

    # -- LOGIN TAB --
with tab2:
    st.subheader("🔑 Login")
    login_name = st.text_input("Name", key="login_name")
    login_password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        payload = {"name": login_name, "password": login_password}
        session = requests.Session()
        r = session.post(f"{BASE_URL}/login", json=payload)

        if r.status_code == 200:
            st.session_state.session = session
            st.session_state.name = login_name
            st.session_state.logged_in = True
            st.session_state.registered = True
            st.session_state.just_registered = False
            st.success(f"✅ Logged in as {login_name}")
        else:
            st.error("Invalid credentials or login failed.")

# --- AFTER LOGIN ---
elif st.session_state.logged_in:
    name = st.session_state.name
    session = st.session_state.session

    st.success(f"✅ Logged in as {name}")

    tab_company, tab_history, tab_generate = st.tabs([
        "🏢 Company Data", "📂 Campaign History", "🧠 Generate Campaign"
    ])

    # --- COMPANY DATA TAB ---
    with tab_company:
        st.header("🏢 Company Info")
        if not st.session_state.company_data_entered:
            company_name = st.text_input("Company Name")
            company_profile = st.text_area("Company Profile")
            products = st.text_input("Main Products (comma-separated)")
            location = st.text_input("Location")
            target_customer = st.text_input("Target Customer")

            if st.button("Submit Company Data"):
                payload = {
                    "company_name": company_name,
                    "company_profile": company_profile,
                    "products": products,
                    "location": location,
                    "target_customer": target_customer
                }
                r = session.post(f"{BASE_URL}/company", json=payload)
                if r.status_code == 200:
                    st.success("✅ Company data saved")
                    st.session_state.company_data_entered = True
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded.")
                else:
                    st.error("Error saving company data")
        else:
            r = session.get(f"{BASE_URL}/company")
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
            st.info("📂 Submit company data first.")
        else:
            st.subheader("🗄️ Record Campaign History")

            hist_product = st.text_input("Product", key="hist_product")
            hist_channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube", "Tiktok", "Social Media", "Radio", "TV", "All Media"])
            hist_output_type = st.selectbox("Output Type", ["Video Script", "Email Copy", "Facebook Ads", "Google Ads","Social Media Posts", "Campaign Plan", "Radio/TV Commerical"])
            hist_result = st.text_area("Campaign Result")
            hist_agent = st.selectbox("Created by Agent?", ["Yes", "No"])

            if st.button("📅 Submit Campaign History"):
                payload = {
                    "product": hist_product,
                    "channel": hist_channel,
                    "output_type": hist_output_type,
                    "result": hist_result,
                    "agent_created": hist_agent == "Yes"
                }
                r = session.post(f"{BASE_URL}/campaign/history", json=payload)
                if r.status_code == 200:
                    st.success("✅ Campaign history saved")
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded.")
                else:
                    st.error("❌ Failed to save campaign history")

    # --- GENERATE CAMPAIGN TAB ---
    with tab_generate:
        if not st.session_state.company_data_entered:
            st.info("🧠 Submit company data first.")
        else:
            st.subheader("🧠 Generate Campaign Plan")

            prod = st.text_input("Product", key="gen_product")
            channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube", "Tiktok", "Social Media", "Radio", "TV", "All Media"])
            ctype = st.selectbox("Campaign Type", ["Brand Awareness", "Lead Generation", "Product Launch", "Conversion", "Customer Retention", "Sales Promotion"])
            otype = st.selectbox("Output Type", ["Video Script", "Email Copy", "Facebook Ads", "Google Ads","Social Media Posts", "Campaign Plan", "Radio/TV Commerical"])
            budget = st.text_input("Budget")
            duration = st.text_input("Duration")

            if st.button("Generate Campaign"):
                payload = {
                    "product": prod,
                    "channel": channel,
                    "campaign_type": ctype,
                    "output_type": otype,
                    "budget": budget,
                    "duration": duration
                }
                r = session.post(f"{BASE_URL}/marketing/generate", json=payload)
                if r.status_code == 200:
                    data = r.json()
                    st.success("✅ Campaign Generated")
                    st.text_area("📋 Campaign Output", value=data.get("campaign", ""), height=300)

                    if st.button("📄 Download PDF"):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.multi_cell(0, 10, data.get("campaign", ""))
                        pdf_bytes = pdf.output(dest='S').encode('latin-1')
                        st.download_button(
                            label="Download Campaign PDF",
                            data=pdf_bytes,
                            file_name="campaign_plan.pdf",
                            mime="application/pdf"
                        )
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded.")
                else:
                    st.error("❌ Error generating campaign.")


st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")

# --- Initialize session state ---
if "session" not in st.session_state:
    st.session_state.session = requests.Session()

for key in ["registered", "company_data_entered", "just_registered", "logged_in", "name"]:
    if key not in st.session_state:
        st.session_state[key] = False if key != "name" else ""

# --- UI TITLE ---
st.title("📣 Campaign Generator")

# --- BEFORE LOGIN ---
if not st.session_state.logged_in:
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
                st.success("Registered successfully. Please log in.")
                st.session_state.just_registered = True
            elif r.status_code == 429:
                st.warning("⏱️ Rate limit exceeded.")
            else:
                st.error(r.json().get("detail", "Registration failed."))

    with tab2:
        st.subheader("🔑 Login")
        login_name = st.text_input("Name", key="login_name")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            payload = {"name": login_name, "password": login_password}
            session = requests.Session()
            r = session.post(f"{BASE_URL}/login", json=payload)

            if r.status_code == 200:
                st.session_state.session = session
                st.session_state.name = login_name
                st.session_state.logged_in = True
                st.session_state.registered = True
                st.session_state.just_registered = False
                st.success(f"✅ Logged in as {login_name}")
            else:
                st.error("Invalid credentials or login failed.")

    if st.session_state.just_registered:
        st.info("✅ Now go to the Login tab and log in.")

# --- AFTER LOGIN ---
elif st.session_state.logged_in:
    name = st.session_state.name
    session = st.session_state.session

    st.success(f"✅ Logged in as {name}")

    tab_company, tab_history, tab_generate = st.tabs([
        "🏢 Company Data", "📂 Campaign History", "🧠 Generate Campaign"
    ])

    # --- COMPANY DATA TAB ---
    with tab_company:
        st.header("🏢 Company Info")
        if not st.session_state.company_data_entered:
            company_name = st.text_input("Company Name")
            company_profile = st.text_area("Company Profile")
            products = st.text_input("Main Products (comma-separated)")
            location = st.text_input("Location")
            target_customer = st.text_input("Target Customer")

            if st.button("Submit Company Data"):
                payload = {
                    "company_name": company_name,
                    "company_profile": company_profile,
                    "products": products,
                    "location": location,
                    "target_customer": target_customer
                }
                r = session.post(f"{BASE_URL}/company", json=payload)
                if r.status_code == 200:
                    st.success("✅ Company data saved")
                    st.session_state.company_data_entered = True
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded.")
                else:
                    st.error("Error saving company data")
        else:
            r = session.get(f"{BASE_URL}/company")
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
            st.info("📂 Submit company data first.")
        else:
            st.subheader("🗄️ Record Campaign History")

            hist_product = st.text_input("Product", key="hist_product")
            hist_channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube", "Tiktok", "Social Media", "Radio", "TV", "All Media"])
            hist_output_type = st.selectbox("Output Type", ["Video Script", "Email Copy", "Facebook Ads", "Google Ads","Social Media Posts", "Campaign Plan", "Radio/TV Commerical"])
            hist_result = st.text_area("Campaign Result")
            hist_agent = st.selectbox("Created by Agent?", ["Yes", "No"])

            if st.button("📅 Submit Campaign History"):
                payload = {
                    "product": hist_product,
                    "channel": hist_channel,
                    "output_type": hist_output_type,
                    "result": hist_result,
                    "agent_created": hist_agent == "Yes"
                }
                r = session.post(f"{BASE_URL}/campaign/history", json=payload)
                if r.status_code == 200:
                    st.success("✅ Campaign history saved")
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded.")
                else:
                    st.error("❌ Failed to save campaign history")

    # --- GENERATE CAMPAIGN TAB ---
    with tab_generate:
        if not st.session_state.company_data_entered:
            st.info("🧠 Submit company data first.")
        else:
            st.subheader("🧠 Generate Campaign Plan")

            prod = st.text_input("Product", key="gen_product")
            channel = st.selectbox("Channel", ["Facebook", "Instagram", "Email", "YouTube", "Tiktok", "Social Media", "Radio", "TV", "All Media"])
            ctype = st.selectbox("Campaign Type", ["Brand Awareness", "Lead Generation", "Product Launch", "Conversion", "Customer Retention", "Sales Promotion"])
            otype = st.selectbox("Output Type", ["Video Script", "Email Copy", "Facebook Ads", "Google Ads","Social Media Posts", "Campaign Plan", "Radio/TV Commerical"])
            budget = st.text_input("Budget")
            duration = st.text_input("Duration")

            if st.button("Generate Campaign"):
                payload = {
                    "product": prod,
                    "channel": channel,
                    "campaign_type": ctype,
                    "output_type": otype,
                    "budget": budget,
                    "duration": duration
                }
                r = session.post(f"{BASE_URL}/marketing/generate", json=payload)
                if r.status_code == 200:
                    data = r.json()
                    st.success("✅ Campaign Generated")
                    st.text_area("📋 Campaign Output", value=data.get("campaign", ""), height=300)

                    if st.button("📄 Download PDF"):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.multi_cell(0, 10, data.get("campaign", ""))
                        pdf_bytes = pdf.output(dest='S').encode('latin-1')
                        st.download_button(
                            label="Download Campaign PDF",
                            data=pdf_bytes,
                            file_name="campaign_plan.pdf",
                            mime="application/pdf"
                        )
                elif r.status_code == 429:
                    st.warning("⏱️ Rate limit exceeded.")
                else:
                    st.error("❌ Error generating campaign.")
