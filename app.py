# app.py
import streamlit as st
from ui.auth import render_auth
from ui.company import company_gate
from ui.history import render_history
from ui.generate import render_generate
from ui.campaign_dashboard import render_campaign_dashboard as render_dashboard  # new
from state import init_session, is_authenticated

st.set_page_config(page_title="Marketing Agent", page_icon="📣", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        max-width: 800px;
        margin: auto;
        padding-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📣 Marketing Agent")

init_session()

def logout():
    for key in ["name", "token", "expires_at", "company_cache", "auth_pref"]:
        st.session_state.pop(key, None)
    st.rerun()

if not is_authenticated():
    render_auth()
    st.stop()

# top bar
left, right = st.columns([6, 1])
with left:
    st.caption(f"Logged in as: **{st.session_state.get('name','')}**")
with right:
    if st.button("Logout", key="logout_main"):
        logout()

# ensure company profile exists before using app features
company = company_gate()

# tabs
hist_tab, gen_tab, dash_tab = st.tabs(["Campaign History", "Generate Campaign", "Dashboard"])
with hist_tab:
    render_history()
with gen_tab:
    render_generate(company)
with dash_tab:
    render_dashboard()
