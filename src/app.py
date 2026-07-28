"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import argparse
import json
import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần cho Phase 2: chatbot baseline không dùng tool.
from prompts import CHATBOT_BASELINE_PROMPT, FALLBACK_RESPONSE
from providers import get_llm_provider
from tools import get_support_resources, screen_risk_signals

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


def get_baseline_cases(test_document):
    """Lấy các câu hỏi bình thường để chạy chatbot baseline của Phase 2."""
    if not isinstance(test_document, dict):
        raise ValueError("Test cases Phase 2 phải là một object JSON.")

    groups = test_document.get("test_cases")
    if not isinstance(groups, dict):
        raise ValueError("Thiếu object 'test_cases' trong config/test_cases.json.")

    normal_cases = groups.get("normal")
    if not isinstance(normal_cases, list) or not normal_cases:
        raise ValueError("Cần ít nhất một test case trong nhóm 'normal'.")

    cases = []
    for case in normal_cases:
        if not isinstance(case, dict):
            continue

        context = case.get("input_context", {})
        user_query = context.get("user_message") if isinstance(context, dict) else None
        if isinstance(user_query, str) and user_query.strip():
            cases.append((case.get("case_id", "UNKNOWN"), user_query.strip()))

    if not cases:
        raise ValueError("Các test case normal phải có input_context.user_message.")

    return cases


def run_baseline_chatbot(user_query: str, provider, show_prompt: bool = False):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    if show_prompt:
        print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_baseline_tests(provider):
    """Chạy các case normal khi cần tạo trace cho báo cáo Phase 2."""
    tests = load_test_cases()
    baseline_cases = get_baseline_cases(tests)
    print(
        f"✅ Đã tải thành công {len(baseline_cases)} test case normal "
        "cho Phase 2 từ config/test_cases.json\n"
    )

    print("--- PHASE 2: CHẠY CHATBOT BASELINE (KHÔNG DÙNG TOOL) ---")
    for case_id, user_query in baseline_cases:
        print(f"\n[Test case: {case_id}]")
        run_baseline_chatbot(user_query, provider)


def run_direct_chat(provider):
    """Chạy chat trực tiếp; input nguy cơ cao không được gửi đến provider."""
    print("\n--- CHAT TRỰC TIẾP ---")
    print("Nhập chia sẻ hoặc câu hỏi của bạn. Gõ 'exit' để kết thúc.")

    while True:
        try:
            user_query = input("\nBạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nKết thúc cuộc trò chuyện.")
            return

        if not user_query:
            continue
        if user_query.casefold() in {"exit", "quit", "thoat", "thoát"}:
            print("Kết thúc cuộc trò chuyện.")
            return

        risk_result = screen_risk_signals(user_query)
        if risk_result.startswith("RISK_LEVEL=HIGH"):
            print("\n🛟 [HỖ TRỢ KHẨN CẤP]")
            print(FALLBACK_RESPONSE)
            print(get_support_resources("vietnam"))
            continue

        run_baseline_chatbot(user_query, provider)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Chatbot baseline cho Phase 2.")
    parser.add_argument(
        "--tests",
        action="store_true",
        help="Chạy các test case normal từ config/test_cases.json thay vì chat trực tiếp.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    if args.tests:
        run_baseline_tests(provider)
    else:
        run_direct_chat(provider)
