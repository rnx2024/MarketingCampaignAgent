# app.py

import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AnyMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, List

# Set API Key (or use environment variable)
os.environ["OPENAI_API_KEY"] = st.secrets.get("OPENAI_API_KEY", "")

# -- Shared State Definition --
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    stage: str

# -- LLM Setup --
llm = ChatOpenAI(model="gpt-4o")  # or "gpt-3.5-turbo"

# -- LangGraph Nodes --
def planner_node(state: AgentState) -> AgentState:
    st.session_state['log'].append("▶️ Planner node triggered.")
    user_input = state["messages"][-1].content
    response = llm.invoke(f"You are a planner. Create a 3-step plan for:\n{user_input}")
    st.session_state['log'].append(f"🧠 Plan:\n{response.content}")
    return {"messages": [response], "stage": "execute"}

def executor_node(state: AgentState) -> AgentState:
    st.session_state['log'].append("▶️ Executor node triggered.")
    plan = state["messages"][-1].content
    response = llm.invoke(f"You are an executor. Implement the plan:\n{plan}")
    st.session_state['log'].append(f"🔧 Execution:\n{response.content}")
    return {"messages": [response], "stage": "review"}

def reviewer_node(state: AgentState) -> AgentState:
    st.session_state['log'].append("▶️ Reviewer node triggered.")
    result = state["messages"][-1].content
    response = llm.invoke(f"You are a reviewer. Summarize and provide feedback:\n{result}")
    st.session_state['log'].append(f"✅ Review:\n{response.content}")
    return {"messages": [response], "stage": "done"}

def route_stage(state: AgentState) -> str:
    return state["stage"]

# -- LangGraph Setup --
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

# -- Streamlit UI --
st.set_page_config(page_title="3-Stage LangGraph Agent", layout="wide")
st.title("🧠 3-Stage LangGraph Agent")
st.caption("Plan → Execute → Review")

if "log" not in st.session_state:
    st.session_state["log"] = []

with st.form("task_input_form"):
    task_input = st.text_area("Enter a task or instruction", height=150)
    submitted = st.form_submit_button("Run Agent")

if submitted and task_input.strip():
    st.session_state["log"] = []  # clear log
    user_state = {
        "messages": [HumanMessage(content=task_input)],
        "stage": "plan"
    }
    final_state = graph.invoke(user_state)

    st.subheader("📝 Agent Responses")
    for entry in st.session_state["log"]:
        st.markdown(entry.replace("\n", "  \n"))

    st.success("🎯 Agent run complete.")
