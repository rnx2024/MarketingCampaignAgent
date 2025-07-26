import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AnyMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, List
from fpdf import FPDF
import uuid

# -- API Key Setup --
if "OPENAI_API_KEY" not in st.secrets:
    st.error("❌ OPENAI_API_KEY not found in st.secrets.")
    st.stop()

llm = ChatOpenAI(model="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])

# -- LangGraph Shared State --
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    stage: str

# -- LangGraph Nodes --
def planner_node(state: AgentState) -> AgentState:
    st.session_state['log'].append("\nPlanner Node\n" + "="*50)
    user_input = state["messages"][-1].content
    response = llm.invoke(f"You are a planner. Create a 3-step plan for:\n{user_input}")
    st.session_state['log'].append("Plan:\n" + response.content)
    return {"messages": [response], "stage": "execute"}

def executor_node(state: AgentState) -> AgentState:
    st.session_state['log'].append("\nExecutor Node\n" + "="*50)
    plan = state["messages"][-1].content
    response = llm.invoke(f"You are an executor. Implement the plan:\n{plan}")
    st.session_state['log'].append("Execution:\n" + response.content)
    return {"messages": [response], "stage": "review"}

def reviewer_node(state: AgentState) -> AgentState:
    st.session_state['log'].append("\nReviewer Node\n" + "="*50)
    result = state["messages"][-1].content
    response = llm.invoke(f"You are a reviewer. Summarize and provide feedback:\n{result}")
    st.session_state['log'].append("Review:\n" + response.content)
    return {"messages": [response], "stage": "done"}

def route_stage(state: AgentState) -> str:
    return state["stage"]

# -- Build LangGraph --
builder = StateGraph(AgentState)
builder.add_node("plan", planner_node)
builder.add_node("execute", executor_node)
builder.add_node("review", reviewer_node)

builder.set_conditional_entry_point(route_stage, {
    "plan": "plan",
    "execute": "execute",
    "review": "review"
})
builder.add_edge("plan", "execute")
builder.add_edge("execute", "review")
builder.add_edge("review", END)

graph = builder.compile()

# -- Streamlit UI Config --
st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")

# -- Custom CSS Styling --
st.markdown("""
    <style>
    body {
        background: linear-gradient(120deg, #f8fbff, #e4ecf7);
    }
    .stApp {
        background: linear-gradient(120deg, #f8fbff, #e4ecf7);
    }
    div.stButton > button {
        background-color: #3B82F6 !important;
        color: white !important;
        padding: 20px 20px !important;
        width: 80px !important;
        height: 80px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 50% !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
        cursor: pointer;
        display: block;
        margin: 30px auto;
        transition: background-color 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #2563EB !important;
    }
    div[data-testid="stForm"] {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
    }
    .stSelectbox, .stTextArea, .stRadio, .stMultiSelect {
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# -- Header --
st.markdown("""
    <div style='display: flex; align-items: center; gap: 10px;'>
        <img src='https://cdn-icons-png.flaticon.com/512/10616/10616845.png' width='40' style='margin-bottom:4px;' />
        <h1 style='margin: 0;'>Marketing Agent</h1>
    </div>
""", unsafe_allow_html=True)

st.caption("Powered by LangGraph | OpenAI")

if "log" not in st.session_state:
    st.session_state["log"] = []

# -- UI Form --
persona_profiles = {
    "Gen Z College Student": "Values authenticity, short videos, influencer content, and prepaid mobile data.",
    "Urban Working Parent": "Seeks convenience, value bundles, responsive to Facebook and YouTube promotions.",
    "Budget-conscious Remote Worker": "Uses affordable tools, responsive to Facebook ads and discounts.",
    "Affluent Tech Enthusiast": "Prefers high-end products, values innovation, follows YouTube and tech blogs.",
    "Millennial Professional": "Digital native, responds to value-driven campaigns, prefers Instagram and LinkedIn, interested in convenience and brand ethics.",
    "Gen X Executive": "Focuses on reliability, productivity, and status-driven purchases, uses LinkedIn and long-form content."
}

with st.form("marketing_form", border=False):
    col1, col2 = st.columns(2)

    with col1:
        product_type = st.selectbox("Product Type", ["Cellphone", "Clothing", "Laptop", "Furniture", "Shoes", "Tablet", "Appliances"])
        product_price = st.selectbox("Product Price Tier", ["Budget", "Mid-range", "Premium"])
        target_persona = st.selectbox("Audience Persona", list(persona_profiles.keys()))
        target_location = st.selectbox("Target Location", ["United States", "Philippines", "Canada", "Europe", "Latin America", "Asia"])
        campaign_type = st.multiselect("Campaign Channels", ["TikTok", "Facebook", "Instagram", "YouTube", "LinkedIn", "TV", "Radio", "Billboard", "Print", "Social Media", "Traditional"])
        campaign_goal = st.selectbox("Campaign Goal", ["Drive Sales", "Generate Leads", "Raise Awareness", "Promote Event", "Boost App Downloads", "Increase Website Traffic"])

    with col2:
        budget = st.selectbox("Budget Range", ["Low (<$500)", "Medium ($500-$5000)", "High (>$5000)"])
        campaign_duration = st.selectbox("Campaign Duration", ["1 week", "2 weeks", "1 month", "Ongoing"])
        call_to_action = st.selectbox("Preferred CTA", ["Buy Now", "Sign Up", "Visit Store", "Learn More"])
        brand_tone = st.selectbox("Brand Tone", ["Playful", "Professional", "Bold", "Minimalist"])
        strategy_mode = st.radio("Strategy Mode", ["General Campaign", "Content Calendar Generator", "Creative Brief Draft", "A/B Testing Planner"])
        extra_notes = st.text_area("Extra Instructions (optional)", height=100)

    submitted = st.form_submit_button("Run Agent")

# -- Agent Execution --
if submitted:
    st.session_state["log"] = []

    profile_traits = persona_profiles.get(target_persona, "")
    channels = ", ".join(campaign_type) if campaign_type else "unspecified channels"

    prompt = (
        f"Strategy Mode: {strategy_mode}.\n"
        f"Target a {target_persona} in {target_location}.\n"
        f"Product: {product_type} ({product_price}).\n"
        f"Budget: {budget}. Duration: {campaign_duration}. CTA: {call_to_action}.\n"
        f"Use these platforms: {channels}. Tone: {brand_tone}.\n"
        f"Campaign goal: {campaign_goal}. {profile_traits}"
        f"{' Extra notes: ' + extra_notes if extra_notes else ''}"
    )

    user_state = {
        "messages": [HumanMessage(content=prompt)],
        "stage": "plan"
    }

    final_state = graph.invoke(user_state)
    campaign_output = "\n\n".join(st.session_state["log"])

    st.markdown("### 📄 Clean Output")
    st.markdown(f"""
    <div style='background-color:#ffffff;border:1px solid #ccc;border-radius:10px;padding:16px;height:500px;overflow-y:scroll;white-space:pre-wrap;font-family:monospace;font-size:14px;'>
    {campaign_output}
    </div>
    """, unsafe_allow_html=True)

    def generate_pdf(text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)
        filename = f"campaign_output_{uuid.uuid4().hex[:8]}.pdf"
        pdf.output(filename)
        return filename

    if st.download_button("📅 Download as PDF", data=open(generate_pdf(campaign_output), "rb"), file_name="campaign_output.pdf", mime="application/pdf"):
        st.success("Download ready.")

    st.markdown("""
        <hr style='margin-top: 40px;'>
        <div style='text-align: center; color: #888888; font-size: 14px;'>
            © 2025 Marketing Agent by Rhanny Urbis | All rights reserved.
        </div>
    """, unsafe_allow_html=True)
