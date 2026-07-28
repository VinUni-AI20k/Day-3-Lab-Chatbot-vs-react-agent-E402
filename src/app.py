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

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import (
    get_calendar,
    send_msg,
    search_home_info,
)
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
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
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    from prompts import REACT_SYSTEM_PROMPT
    from tools import AVAILABLE_TOOLS
    import re
    import ast

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    completed = False
    
    # Lịch sử hội thoại
    history = f"User: {user_query}\n"
    
    # Mảng để lưu trace
    trace = []
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM
        response = provider.generate(history, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)
        
        # Lưu trace thought và action
        trace.append(f"LLM Response:\n{response}")
        
        history += f"{response}\n"
        
        if "Final Answer:" in response:
            completed = True
            break
            
        # Parse Action: tên_công_cụ[tham_số]
        # VD: Action: search_home_info['Quận 7', '6 tháng', 7000000, 'studio']
        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response)
        if action_match:
            tool_name = action_match.group(1)
            args_str = action_match.group(2)
            
            obs = ""
            if tool_name in AVAILABLE_TOOLS:
                try:
                    if args_str.strip():
                        # Parse argument
                        args = ast.literal_eval(f"({args_str},)")
                        # ast.literal_eval returns a tuple.
                        # If args_str is "'Quận 7', '6 tháng'", it parses to ('Quận 7', '6 tháng')
                        if type(args[0]) is tuple and len(args) == 1:
                            args = args[0]
                    else:
                        args = ()
                    obs = AVAILABLE_TOOLS[tool_name](*args)
                except Exception as e:
                    obs = f"Lỗi khi thực thi action: {e}"
            else:
                obs = f"Công cụ {tool_name} không tồn tại."
                
            print(f"👁️ Observation: {obs}")
            history += f"Observation: {obs}\n"
            trace.append(f"Observation: {obs}")
        else:
            obs = "Không thể parse Action. Hãy chắc chắn dùng đúng format Action: tên_công_cụ[tham_số, ...]"
            print(f"👁️ Observation: {obs}")
            history += f"Observation: {obs}\n"
            trace.append(f"Observation: {obs}")
            
    if not completed and step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        
    # Ghi trace ra file cho Role 5
    try:
        os.makedirs(os.path.dirname(os.path.abspath(__file__)) + "/../docs", exist_ok=True)
        trace_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "trace_eval.md")
        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Trace for query: {user_query}\n\n")
            for t in trace:
                f.write(t + "\n\n")
    except Exception as e:
        print(f"Lỗi ghi trace: {e}")


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
    
    # Chạy thử câu test số 3 (multi-step của bài toán thuê trọ)
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT (Test Multi-step) ---")
    run_react_agent(sample_query, provider)
    
    # Chạy thử câu test số 5 (bẫy Guardrail)
    print("\n--- DEMO 3: CHẠY TRÊN REACT AGENT (Test Guardrail Edge Case) ---")
    edge_case_query = tests[4]["question"]
    run_react_agent(edge_case_query, provider)
