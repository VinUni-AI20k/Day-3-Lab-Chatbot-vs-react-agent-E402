"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

Chủ đề nhóm: Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa.

Trạng thái theo Mốc:
- ✅ Mốc 2: run_baseline_chatbot() chạy toàn bộ test cases qua Chatbot gốc (không Tool).
- ⏳ Mốc 3: run_react_agent() sẽ được lắp vòng lặp Thought -> Action -> Observation.
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


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline - Cấp 2): chỉ có LLM, KHÔNG được gọi Tool.

    Args:
        user_query: Câu hỏi của người dùng.
        provider: LLM Provider lấy từ get_llm_provider().

    Returns:
        Chuỗi phản hồi của Chatbot (để Role 5 dán vào docs/trace_eval.md).
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)

    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider):
    """
    ⏳ MỐC 3 - CHƯA TRIỂN KHAI.

    Sẽ là vòng lặp ReAct thật: gọi LLM -> parse dòng 'Action: tên_tool[tham_số]'
    -> tra AVAILABLE_TOOLS -> nối Observation vào prompt -> lặp tối đa MAX_ITERATIONS.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    print(f"⏳ Chưa triển khai (thuộc Mốc 3). Tools sẵn sàng: {list(AVAILABLE_TOOLS.keys())}")
    print(f"🛡️ Guardrail đã cấu hình: MAX_ITERATIONS = {MAX_ITERATIONS}")


def print_header(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


if __name__ == "__main__":
    print_header("🏫 BÀI LAB 3: CHATBOT VS REACT AGENT — ĐẶT LỊCH KHÁM BỆNH")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    if provider.__class__.__name__ == "MockProvider":
        print("⚠️  CẢNH BÁO: Đang chạy MockProvider (offline).")
        print("   Muốn thấy đúng hạn chế của Chatbot gốc, hãy tạo file .env từ .env.example")
        print("   và điền API key thật, rồi chạy lại.")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json")

    # ==================================================================
    # 📍 MỐC 2: Chạy TOÀN BỘ test cases qua Chatbot Baseline
    # Mục tiêu: chứng minh Chatbot gốc xử lý tốt câu 1-2, nhưng bó tay
    # hoặc ảo giác ở câu 3-8 vì không tra được dữ liệu phòng khám.
    # ==================================================================
    print_header("📍 MỐC 2 — DEMO CHATBOT BASELINE (CẤP 2: LLM, KHÔNG TOOL)")

    # Chỉ chạy các case tiêu biểu để tiết kiệm lượt gọi API.
    # 1, 2 = kiến thức chung (Chatbot làm tốt)
    # 3, 10, 16 = cần dữ liệu phòng khám (Chatbot sẽ bịa bác sĩ / giờ / mã hẹn)
    SELECTED_CASE_IDS = [1, 2, 3, 10, 16]
    selected = [c for c in tests if c["id"] in SELECTED_CASE_IDS]
    print(f"🎯 Chạy {len(selected)}/{len(tests)} case tiêu biểu: {SELECTED_CASE_IDS}")

    for case in selected:
        print("\n" + "-" * 70)
        tool_path = case.get("expected_tool_path", [])
        route = "Chatbot (không cần tool)" if not tool_path else f"Agent -> {tool_path}"
        print(f"🧪 Test #{case['id']} | {case['category']} | Kỳ vọng: {route}")
        print(f"📌 Kỳ vọng: {case['expected_behavior']}")

        run_baseline_chatbot(case["question"], provider)

    # ==================================================================
    # 📍 MỐC 3: ReAct Agent Loop (sẽ lắp ở buổi sau)
    # ==================================================================
    print_header("📍 MỐC 3 — REACT AGENT (CHƯA TRIỂN KHAI)")
    run_react_agent(tests[3]["question"], provider)
