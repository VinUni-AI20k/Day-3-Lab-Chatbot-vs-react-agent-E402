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

st.markdown("""
<style>
    /* Premium Glassmorphism UI */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 1rem !important;
    }
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 1rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="chat-message-user"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(147, 51, 234, 0.15) 100%) !important;
        border: 1px solid rgba(147, 51, 234, 0.3) !important;
    }
    section[data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stAlert {
        border-radius: 0.5rem;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        background-color: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

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
    """Trích xuất Action từ response của LLM. Vd: search_rentals[{"location":"Cầu Giấy"}]"""
    pattern = r"Action:\s*(\w+)\[(.*)\]"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        tool_name = match.group(1)
        params_str = match.group(2).strip()
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
            except:
                # Fallback nếu JSON có lỗi
                pass
        return tool_name, params
    return None, {}

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
                params_display = json.dumps(params, ensure_ascii=False) if isinstance(params, dict) else str(params)
                st.warning(f"🛠️ **Action**: `{tool_name}({params_display})`")
                
                # Thực thi Tool
                if tool_name in AVAILABLE_TOOLS:
                    try:
                        tool_func = AVAILABLE_TOOLS[tool_name]
                        if isinstance(params, dict):
                            obs = tool_func(**params)
                        elif isinstance(params, list):
                            obs = tool_func(*params)
                        else:
                            obs = tool_func()
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
