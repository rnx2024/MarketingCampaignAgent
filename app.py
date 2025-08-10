## app.py

import streamlit as st
from ui.auth import render_auth
from ui.company import company_gate
from ui.history import render_history
from ui.generate import render_generate
from state import init_session, is_authenticated

st.set_page_config(page_title="Marketing Agent", layout="wide")
st.title("Marketing Agent")

init_session()

if not is_authenticated():
    render_auth()
    st.stop()

company = company_gate()  # blocks until saved

hist_tab, gen_tab = st.tabs(["Campaign History", "Generate Campaign"])
with hist_tab:
    render_history()
with gen_tab:
    render_generate(company)
