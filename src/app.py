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
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def run_tool(tool_name: str, *args):
    """Gọi một tool từ registry của tools.py."""
    tool_func = AVAILABLE_TOOLS.get(tool_name)
    if tool_func is None:
        return f"LỖI: Không tìm thấy tool '{tool_name}' trong registry."

    try:
        return tool_func(*args)
    except TypeError as exc:
        return f"LỖI: Tool '{tool_name}' không phù hợp với tham số đã truyền: {exc}"

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
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    normalized_query = user_query.lower()

    if "trạng thái đơn hàng" in normalized_query or ("đơn hàng" in normalized_query and "trạng thái" in normalized_query):
        tool_name = "get_order_status"
        tool_args = ("DH123",)
    elif "chính sách" in normalized_query and "đổi trả" in normalized_query:
        tool_name = "check_return_policy"
        tool_args = ("Thời trang",)
    elif "tạo yêu cầu đổi trả" in normalized_query or ("đổi trả" in normalized_query and "tạo" in normalized_query):
        tool_name = "create_return_request"
        tool_args = ("DH123", "Sai kích cỡ")
    else:
        print("🧠 Thought: Câu hỏi này không cần gọi tool; có thể trả lời trực tiếp.")
        print("🏁 Final Answer: Tôi sẽ trả lời dựa trên kiến thức có sẵn trong prompt.")
        return

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        if step == 1:
            print(f"🧠 Thought: Câu hỏi này cần gọi tool {tool_name} để tra cứu dữ liệu thực tế.")
            print(f"🛠️ Action: {tool_name}{tool_args}")

            obs = run_tool(tool_name, *tool_args)
            print(f"👁️ Observation: {obs}")

            final_answer = provider.generate(
                f"Dựa trên thông tin sau, hãy trả lời câu hỏi của người dùng: {user_query}\n\nObservation: {obs}",
                system_prompt=REACT_SYSTEM_PROMPT,
            )
            print(f"🏁 Final Answer:\n{final_answer}")
            break

    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


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
