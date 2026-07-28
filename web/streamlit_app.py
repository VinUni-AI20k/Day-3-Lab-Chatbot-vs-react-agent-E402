"""
Basic Streamlit demo chatbot for the HR ReAct Agent.

Run:
    streamlit run web/streamlit_app.py
"""

import os
import sys

import streamlit as st
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
sys.path.insert(0, SRC_DIR)

from app import build_react_graph, make_initial_state
from prompts import MAX_ITERATIONS
from providers import get_llm_provider
from tools import reset_calendar

load_dotenv()

SAMPLE_RESUME = """Nguyen Van A - Email: nguyenvana@gmail.com - SDT: 0901234567
Backend Developer, 3 nam kinh nghiem.
Ky nang: Python, Django, PostgreSQL, Docker, REST API, Git, Linux."""

SAMPLE_JD = """Cong ty ABC tuyen Backend Developer - Lien he HR: hr@abc.com
Yeu cau: Python, Django, PostgreSQL, Docker, REST API, Git."""

TRACE_LABELS = {
    "thought": "Thought",
    "action": "Action",
    "observation": "Observation",
    "final": "Final Answer",
    "blocked": "Guardrail",
    "system": "System",
}


def run_agent_turn(provider, candidate_name, resume_text, jd_text, preferred_date, user_question=""):
    graph = build_react_graph(provider)
    state = make_initial_state(
        candidate_name, resume_text, jd_text, preferred_date, user_question=user_question
    )
    final_state = state

    for snapshot in graph.stream(state, stream_mode="values"):
        final_state = snapshot

    return final_state


def render_trace(trace):
    for entry in trace:
        label = TRACE_LABELS.get(entry["type"], entry["type"])
        if entry["type"] == "final":
            st.success(f"{label}: {entry['text']}")
        elif entry["type"] == "blocked":
            st.warning(f"{label}: {entry['text']}")
        elif entry["type"] == "observation":
            st.info(f"{label}: {entry['text']}")
        else:
            st.markdown(f"**{label}:** {entry['text']}")


st.set_page_config(
    page_title="HR ReAct Agent Chatbot",
    page_icon="HR",
    layout="wide",
)

provider = get_llm_provider()
model_name = getattr(provider, "model_name", "Offline Mock Mode")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Paste a candidate resume and job description in the sidebar, "
                "then ask me to screen and schedule an interview."
            ),
            "trace": [],
        }
    ]

st.title("HR ReAct Agent Chatbot")
st.caption("Basic Streamlit demo for resume screening and interview scheduling.")

with st.sidebar:
    st.subheader("Agent setup")
    st.write(f"Provider: `{provider.__class__.__name__}`")
    st.write(f"Model: `{model_name}`")
    st.write(f"Max iterations: `{MAX_ITERATIONS}`")

    candidate_name = st.text_input("Candidate name", value="Nguyen Van A")
    preferred_date = st.text_input("Preferred interview date", value="05/08/2026")
    resume_text = st.text_area("Resume", value=SAMPLE_RESUME, height=220)
    jd_text = st.text_area("Job description", value=SAMPLE_JD, height=220)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("Reset calendar", use_container_width=True):
            reset_calendar()
            st.toast("Calendar reset")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("trace"):
            with st.expander("View ReAct trace"):
                render_trace(message["trace"])

user_prompt = st.chat_input("Ask the agent to screen this candidate and schedule if qualified")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt, "trace": []})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        missing_fields = [
            label
            for label, value in (
                ("candidate name", candidate_name),
                ("resume", resume_text),
                ("job description", jd_text),
            )
            if not value.strip()
        ]

        if missing_fields:
            answer = "Please fill in: " + ", ".join(missing_fields) + "."
            trace = []
            st.warning(answer)
        else:
            with st.spinner("Running ReAct agent..."):
                final_state = run_agent_turn(
                    provider, candidate_name, resume_text, jd_text, preferred_date,
                    user_question=user_prompt,
                )

            answer = final_state.get("final_answer") or "The agent stopped without a final answer."
            trace = final_state.get("trace", [])
            st.markdown(answer)
            st.caption(
                "stop_reason="
                f"{final_state.get('stop_reason')} | steps={final_state.get('step')} | "
                f"tool_calls={final_state.get('tool_calls')}"
            )
            with st.expander("View ReAct trace", expanded=True):
                render_trace(trace)

    st.session_state.messages.append({"role": "assistant", "content": answer, "trace": trace})
