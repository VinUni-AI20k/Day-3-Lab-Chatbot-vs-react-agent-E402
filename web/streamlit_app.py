"""
🗂️ WEB DEMO (Streamlit) — Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn
Thư mục web/ nằm NGOÀI src/ theo yêu cầu — chỉ import lại các thành phần đã có trong
src/ (tools, prompts, app, providers), không định nghĩa lại logic ở đây.
Chạy: streamlit run web/streamlit_app.py
"""

import os
import sys

_SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, _SRC_DIR)

import streamlit as st
from dotenv import load_dotenv

from app import build_react_graph, make_initial_state
from prompts import MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

st.set_page_config(page_title="Sàng Lọc Hồ Sơ & Hẹn Phỏng Vấn", page_icon="🗂️", layout="wide")

_TRACE_ICON = {"thought": "🧠", "action": "🛠️", "observation": "👁️", "final": "🏁", "blocked": "🛡️", "system": "ℹ️"}
_TRACE_LABEL = {
    "thought": "Thought", "action": "Action", "observation": "Observation",
    "final": "Final Answer", "blocked": "GUARDRAIL", "system": "System",
}

st.title("🗂️ Trợ Lý Sàng Lọc Hồ Sơ & Hẹn Phỏng Vấn")
st.caption("ReAct Agent (LangGraph) — dán CV & JD, xem trực tiếp từng bước Thought → Action → Observation.")

with st.sidebar:
    st.subheader("⚙️ Cấu hình")
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    st.markdown(f"**Provider:** `{provider.__class__.__name__}`")
    st.markdown(f"**Model:** `{model_name}`")
    st.markdown(f"**MAX_ITERATIONS:** `{MAX_ITERATIONS}`")
    st.caption("Đổi provider/model qua biến môi trường LLM_PROVIDER trong file .env ở thư mục gốc.")

with st.form("screening_form"):
    candidate_name = st.text_input("Tên ứng viên", placeholder="Nguyễn Văn A")

    col1, col2 = st.columns(2)
    with col1:
        resume_text = st.text_area("📄 CV (resume_text)", height=280, placeholder="Dán toàn bộ nội dung CV vào đây...")
    with col2:
        job_description_text = st.text_area(
            "📋 JD (job_description_text)", height=280, placeholder="Dán toàn bộ nội dung JD vào đây..."
        )

    preferred_date = st.text_input("Ngày phỏng vấn mong muốn (dd/mm/yyyy)", value="05/08/2026")
    submitted = st.form_submit_button("🚀 Chạy ReAct Agent", use_container_width=True)

if submitted:
    if not candidate_name.strip() or not resume_text.strip() or not job_description_text.strip():
        st.error("Vui lòng nhập đủ Tên ứng viên, CV và JD trước khi chạy.")
    else:
        st.divider()
        st.subheader("🔎 Chuỗi ReAct Trace")

        graph = build_react_graph(provider)
        state = make_initial_state(candidate_name, resume_text, job_description_text, preferred_date)

        log = st.container()
        seen = 0
        final_state = state

        with st.spinner("Agent đang suy luận..."):
            for snapshot in graph.stream(state, stream_mode="values"):
                new_entries = snapshot["trace"][seen:]
                for entry in new_entries:
                    icon = _TRACE_ICON.get(entry["type"], "•")
                    label = _TRACE_LABEL.get(entry["type"], entry["type"])
                    with log:
                        if entry["type"] == "final":
                            st.success(f"{icon} **{label}**\n\n{entry['text']}")
                        elif entry["type"] == "blocked":
                            st.warning(f"{icon} **{label}**\n\n{entry['text']}")
                        elif entry["type"] == "observation":
                            st.info(f"{icon} **{label}**\n\n{entry['text']}")
                        else:
                            st.markdown(f"{icon} **{label}:** {entry['text']}")
                seen = len(snapshot["trace"])
                final_state = snapshot

        st.divider()
        stop_reason = final_state.get("stop_reason")
        if stop_reason == "max_iterations":
            st.error(f"🛡️ Agent dừng do đạt giới hạn {MAX_ITERATIONS} vòng lặp (Guardrail MAX_ITERATIONS).")
        elif stop_reason == "injection":
            st.error("🛡️ Yêu cầu bị chặn bởi Guardrails AI (nghi ngờ prompt injection trong CV/JD/đầu vào).")
        else:
            st.caption(f"Hoàn tất sau {final_state.get('step')} bước Thought-Action.")
