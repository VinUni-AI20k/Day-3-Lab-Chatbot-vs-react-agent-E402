"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import re

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

import ast

def execute_tool_call(action_str: str) -> str:
    """
    Bóc tách và thực thi Tool từ chuỗi Action của LLM (dạng: tool_name['arg1', 'arg2'])
    """
    match = re.search(r"(\w+)\[(.*)\]", action_str)
    if not match:
        return f"LỖI: Định dạng Action không hợp lệ ({action_str}). Cần có dạng: tên_tool['tham_số']"
    
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    
    if tool_name not in AVAILABLE_TOOLS:
        return f"LỖI: Công cụ '{tool_name}' không tồn tại. Danh sách công cụ: {list(AVAILABLE_TOOLS.keys())}"
    
    tool_func = AVAILABLE_TOOLS[tool_name]
    
    try:
        if not raw_args:
            args = []
        else:
            try:
                parsed = ast.literal_eval(f"[{raw_args}]")
                if isinstance(parsed, list):
                    args = [str(x) for x in parsed]
                else:
                    args = [str(parsed)]
            except Exception:
                args = [arg.strip().strip("'\"") for arg in raw_args.split(",") if arg.strip()]
                
        return str(tool_func(*args))
    except Exception as e:
        return f"LỖI khi thực thi công cụ '{tool_name}': {str(e)}"


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    conversation_history = f"Câu hỏi của sinh viên: {user_query}"
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM sinh bước tiếp theo
        llm_output = provider.generate(conversation_history, system_prompt=REACT_SYSTEM_PROMPT)
        
        if not llm_output:
            print("⚠️ LLM trả về phản hồi rỗng!")
            break
            
        print(llm_output)
        
        # Thêm kết quả của LLM vào lịch sử hội thoại
        conversation_history += f"\n{llm_output}"
        
        # Kiểm tra xem LLM đã đưa ra Final Answer chưa
        if "Final Answer:" in llm_output:
            print("\n🏁 Hoàn thành luồng suy luận ReAct!")
            break
            
        # Kiểm tra xem LLM có sinh ra Action để gọi Tool hay không
        if "Action:" in llm_output:
            action_line = [line for line in llm_output.split("\n") if "Action:" in line][0]
            action_str = action_line.replace("Action:", "").strip()
            
            # Thực thi Tool
            obs = execute_tool_call(action_str)
            print(f"👁️ Observation:\n{obs}")
            
            # Đưa Observation vào lịch sử để lượt sau LLM đọc được
            conversation_history += f"\nObservation: {obs}"
        else:
            # Nếu LLM không sinh ra cả Action lẫn Final Answer
            break
            
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")




if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 3
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
