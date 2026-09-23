import os
import sys
import uuid
import json
import urllib
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from langchain_core.messages import HumanMessage, ToolMessage

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
    with st.chat_message(entry["role"], avatar="👤" if entry["role"] == "user" else "🤖"):
        if "traces" in entry:
            for trace in entry["traces"]:
                if trace["type"] == "tool_input":
                    st.markdown(f"**⚡ Intent Recognized:** `{trace['name']}`")
                    with st.expander(f"📥 View Generated Input ({trace['name']})", expanded=False):
                        st.json(trace["args"])
                elif trace["type"] == "tool_output":
                    with st.expander(f"📤 View Raw Output ({trace['name']})", expanded=False):
                        st.code(trace["content"], language="text")
        st.markdown(entry["content"])

if user_input := st.chat_input("Query fleet telemetry, corridor updates, or compliance thresholds..."):
    st.session_state.ui_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        final_response = ""
        current_traces = [] 
        
        with st.status("🧠 Initializing Core Reasoner Node...", expanded=True) as status:
            events = logix_agent.stream(
                {"messages": [HumanMessage(content=user_input)]}, 
                config=thread_config,
                stream_mode="updates"
            )
            
            for event in events:
                for node_name, node_state in event.items():
                    if node_name == "reasoner":
                        latest_msg = node_state["messages"][-1]
                        if hasattr(latest_msg, "tool_calls") and latest_msg.tool_calls:
                            status.update(label="🧠 Agent generated tool parameters...")
                            for tool_call in latest_msg.tool_calls:
                                st.markdown(f"**⚡ Intent Recognized:** `{tool_call['name']}`")
                                with st.expander(f"📥 View Generated Input ({tool_call['name']})", expanded=False):
                                    st.json(tool_call['args'])
                                current_traces.append({
                                    "type": "tool_input",
                                    "name": tool_call['name'],
                                    "args": tool_call['args']
                                })
                        if latest_msg.content:
                            final_response = latest_msg.content
                            status.update(label="📝 Generating Operational Resolution Report...")
                    elif node_name == "tools":
                        status.update(label="🔧 Executing Enterprise Subsystem Tools...")
                        for msg in node_state.get("messages", []):
                            if isinstance(msg, ToolMessage):
                                with st.expander(f"📤 View Raw Output ({msg.name})", expanded=False):
                                    st.code(msg.content, language="text")
                                current_traces.append({
                                    "type": "tool_output",
                                    "name": msg.name,
                                    "content": msg.content
                                })
            status.update(label="Incident Matrix Evaluation Complete", state="complete", expanded=False)
            
        if final_response:
            st.markdown(final_response)
            st.session_state.ui_messages.append({
                "role": "assistant",
                "content": final_response,
                "traces": current_traces
            })
