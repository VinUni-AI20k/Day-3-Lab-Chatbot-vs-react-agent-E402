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
    Chạy đúng một lượt sinh phản hồi bằng LLM, không gọi công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    # Baseline protocol: system prompt + user query -> đúng một LLM call.
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider):
    """
    Điểm tích hợp ReAct Agent dành cho Mốc 3.

    Mốc 2 chỉ nghiệm thu Chatbot Baseline nên không thực thi tool tại đây.
    """
    print("\nℹ️ ReAct Agent sẽ được tích hợp và nghiệm thu tại Mốc 3.")


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
    
    print("--- MỐC 2: CHẠY CHATBOT BASELINE TRÊN 5 TEST CASES ---")
    baseline_results = []

    for test_case in tests:
        print(
            f"\n{'-' * 50}\n"
            f"Test #{test_case['id']} — {test_case['category']}\n"
            f"Kỳ vọng: {test_case['expected_behavior']}"
        )
        response = run_baseline_chatbot(test_case["question"], provider)
        baseline_results.append(
            {
                "id": test_case["id"],
                "question": test_case["question"],
                "response": response,
            }
        )

    print(
        "\n✅ HOÀN THÀNH BASELINE:"
        f" {len(baseline_results)} LLM calls / {len(tests)} test cases,"
        " 0 tool calls."
    )
    print(f"🧰 Tool registry đã nhận: {', '.join(AVAILABLE_TOOLS)}")
