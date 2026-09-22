import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from langchain_core.messages import HumanMessage

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.orchestrator import logix_agent

st.set_page_config(
    page_title="Logix AI: Cold-Chain Incident & Dispatch Console",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "ui_messages" not in st.session_state:
    st.session_state.ui_messages = []

thread_config = {"configurable": {"thread_id": st.session_state.thread_id}}

with st.sidebar:
    st.title("Logix AI Command Center")
    st.caption(f"Session Token: `{st.session_state.thread_id[:8]}...`")
    st.markdown(f"**Reasoning Architecture:** `{os.getenv('Agent_llm', 'DEEPSEEK')}`")

st.title("Cold-Chain Incident Control Dashboard")
st.caption("Production Data Engineering Pipeline • Real-Time Decision Optimization Platform")

for entry in st.session_state.ui_messages:
    with st.chat_message(entry["role"]):
        st.markdown(entry["content"])

if user_input := st.chat_input("Query fleet telemetry, corridor updates, or compliance thresholds..."):
    st.session_state.ui_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response = logix_agent.invoke({"messages": [HumanMessage(content=user_input)]}, config=thread_config)
        final_text = response["messages"][-1].content
        st.markdown(final_text)
        st.session_state.ui_messages.append({"role": "assistant", "content": final_text})
