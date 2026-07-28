"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
Giao diện được xây dựng bằng Streamlit.
"""

import os
import sys
import json
import re
import streamlit as st
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

st.set_page_config(page_title="AI Assistant - Tìm Nhà Trọ", page_icon="🏠", layout="wide")

@st.cache_data
def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_baseline_chatbot(user_query: str, provider):
    """Chatbot cơ bản không có Tools"""
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    return response

def parse_action(text: str):
    """Trích xuất Action từ response của LLM. Vd: search_properties['Hà Nội', 'Cầu Giấy', '', 5000000]"""
    pattern = r"Action:\s*(\w+)\[(.*?)\]"
    match = re.search(pattern, text)
    if match:
        tool_name = match.group(1)
        params_str = match.group(2)
        # Parse params. Rất basic: cắt theo dấu phẩy, bỏ quote
        params = []
        if params_str.strip():
            # Xử lý cắt chuỗi tham số
            # Dùng regex cẩn thận hoặc ast.literal_eval. Tạm dùng split.
            import ast
            try:
                # Bọc lại bằng ngoặc vuông để parse như một list Python
                params = ast.literal_eval(f"[{params_str}]")
            except:
                params = [p.strip().strip("'").strip('"') for p in params_str.split(',')]
        return tool_name, params
    return None, None

def run_react_agent(user_query: str, provider):
    """Vòng lặp ReAct Agent"""
    history_prompt = f"User: {user_query}\n"
    
    with st.status("Agent đang xử lý...", expanded=True) as status:
        for step in range(1, MAX_ITERATIONS + 1):
            st.write(f"**🔄 Bước {step}/{MAX_ITERATIONS}**")
            
            # Gọi LLM với lịch sử hiện tại
            response = provider.generate(history_prompt, system_prompt=REACT_SYSTEM_PROMPT)
            history_prompt += f"{response}\n"
            
            # In ra các dòng Thought / Final Answer
            lines = response.split('\n')
            for line in lines:
                if line.startswith("Thought:"):
                    st.info(f"🧠 {line}")
                elif line.startswith("Final Answer:"):
                    status.update(label="Hoàn tất!", state="complete", expanded=False)
                    return line.replace("Final Answer:", "").strip()
            
            # Tìm Action
            tool_name, params = parse_action(response)
            if tool_name:
                st.warning(f"🛠️ **Action**: `{tool_name}({', '.join(map(str, params))})`")
                
                # Thực thi Tool
                if tool_name in AVAILABLE_TOOLS:
                    try:
                        tool_func = AVAILABLE_TOOLS[tool_name]
                        obs = tool_func(*params)
                    except Exception as e:
                        obs = f"Lỗi khi chạy tool {tool_name}: {str(e)}"
                else:
                    obs = f"Lỗi: Tool '{tool_name}' không tồn tại."
                
                st.success(f"👁️ **Observation**: \n{obs}")
                history_prompt += f"Observation: {obs}\n"
            else:
                # Nếu LLM không ra lệnh gì và không Final Answer, ép kết thúc
                if "Final Answer:" not in response:
                    status.update(label="Hoàn tất!", state="complete", expanded=False)
                    return response
                    
        status.update(label="Đã quá giới hạn bước!", state="error", expanded=False)
        return "🛡️ GUARDRAIL TRIGGERED: Vượt quá số bước suy luận tối đa."

# UI Layout
st.title("🏠 Trợ Lý AI Tìm & Đặt Lịch Xem Nhà")
st.markdown("*Phiên bản Web App với ReAct Agentic AI*")

provider = get_llm_provider()
model_name = getattr(provider, "model_name", "Offline Mock Mode")
st.sidebar.success(f"🔌 LLM Provider: **{provider.__class__.__name__}**\n\n🤖 Model: **{model_name}**")

tests = load_test_cases()
st.sidebar.subheader("Thử nghiệm Test Cases")
test_options = ["(Nhập tay)"] + [f"[{t['category']}] {t['question']}" for t in tests]
selected_test = st.sidebar.selectbox("Chọn câu hỏi mẫu:", test_options)

agent_mode = st.sidebar.radio("Chế độ:", ["ReAct Agent (Khuyên dùng)", "Chatbot Baseline (Không Tools)"])

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Bạn cần tìm phòng như thế nào?")

if user_input or selected_test != "(Nhập tay)":
    # Lấy query
    query = user_input if user_input else tests[test_options.index(selected_test) - 1]["question"]
    
    # Reset selected_test to avoid infinite loop when selecting from sidebar
    if not user_input and selected_test != "(Nhập tay)":
        pass # Note: Streamlit triggers rerun on selectbox change, this handles it properly usually by showing it as current input.
        
    # Chỉ process nếu có user_input hoặc người dùng vừa chọn test case VÀ chưa ấn gửi.
    # Để tránh run 2 lần, ta dùng cơ chế check last_query.
    if "last_query" not in st.session_state or st.session_state.last_query != query or user_input:
        st.session_state.last_query = query
        
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
            
        with st.chat_message("assistant"):
            if agent_mode == "Chatbot Baseline (Không Tools)":
                answer = run_baseline_chatbot(query, provider)
                st.markdown(answer)
            else:
                answer = run_react_agent(query, provider)
                st.markdown(answer)
                
        st.session_state.messages.append({"role": "assistant", "content": answer})
