"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import sys
import time
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


_RATE_LIMIT_MARKERS = ("RESOURCE_EXHAUSTED", "429", "rate limit")


def _is_rate_limited(response: str) -> bool:
    return any(marker.lower() in response.lower() for marker in _RATE_LIMIT_MARKERS)


def _call_llm_with_retry(provider, prompt: str, system_prompt: str, max_retries: int = 3, default_wait: float = 20.0) -> str:
    """
    🛡️ Guardrail: Gọi provider.generate() với tự động chờ + thử lại khi gặp
    lỗi rate limit (429/RESOURCE_EXHAUSTED) từ free tier LLM API, thay vì
    để cả chuỗi test case thất bại hàng loạt.
    """
    response = ""
    for attempt in range(max_retries + 1):
        response = provider.generate(prompt, system_prompt=system_prompt)
        if not _is_rate_limited(response):
            return response
        if attempt == max_retries:
            break
        wait_match = re.search(r"retry in ([\d.]+)\s*s", response)
        wait_seconds = float(wait_match.group(1)) + 2 if wait_match else default_wait
        print(f"⏳ Rate limit từ API. Chờ {wait_seconds:.0f}s rồi thử lại (lần {attempt + 1}/{max_retries})...")
        time.sleep(wait_seconds)
    return response


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    Chỉ dùng kiến thức tĩnh của LLM, không thể tra cứu dữ liệu thật.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    response = _call_llm_with_retry(provider, user_query, CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def _parse_action(action_line: str):
    """
    Parse chuỗi dạng 'ten_cong_cu["arg1", "arg2"]' thành (tool_name, [args]).
    Hỗ trợ tham số trong dấu nháy đơn hoặc kép để tránh vỡ khi arg có dấu phẩy.
    """
    match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(.*)\]\s*$", action_line.strip(), re.DOTALL)
    if not match:
        return None, []

    tool_name = match.group(1)
    args_str = match.group(2).strip()
    if not args_str:
        return tool_name, []

    quoted = re.findall(r'"([^"]*)"|\'([^\']*)\'', args_str)
    if quoted:
        args = [a or b for a, b in quoted]
    else:
        # Fallback: không có dấu nháy, tách theo dấu phẩy đơn giản
        args = [a.strip() for a in args_str.split(",")]
    return tool_name, args


def run_react_agent(user_query: str, provider) -> str:
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    Gọi LLM thật để suy luận động, không hardcode kịch bản.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    scratchpad = ""
    final_answer = None
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        prompt = f"Câu hỏi của khách hàng: {user_query}\n\n{scratchpad}".strip()
        raw = _call_llm_with_retry(provider, prompt, REACT_SYSTEM_PROMPT)

        if _is_rate_limited(raw):
            print(f"⚠️ Vẫn bị rate limit sau khi thử lại. Dừng an toàn: {raw}")
            break

        # 🛡️ Guardrail: nếu LLM tự bịa luôn "Observation" (không tuân thủ dừng lại
        # để chờ hệ thống), cắt bỏ phần đó — không tin bất kỳ Observation nào
        # không phải do hệ thống sinh ra.
        cut_idx = raw.find("Observation:")
        if cut_idx != -1:
            raw = raw[:cut_idx].strip()

        thought_match = re.search(r"Thought:\s*(.+)", raw)
        thought = thought_match.group(1).strip() if thought_match else "(không phát hiện Thought)"
        print(f"🧠 Thought: {thought}")

        final_match = re.search(r"Final Answer:\s*(.+)", raw, re.DOTALL)
        if final_match:
            final_answer = final_match.group(1).strip()
            print(f"🏁 Final Answer: {final_answer}")
            break

        action_match = re.search(r"Action:\s*(.+)", raw)
        if not action_match:
            print("⚠️ Không phát hiện Action hay Final Answer hợp lệ trong phản hồi. Dừng an toàn.")
            break

        action_line = action_match.group(1).strip()
        print(f"🛠️ Action: {action_line}")

        tool_name, args = _parse_action(action_line)

        # 🛡️ Guardrail: chỉ cho phép gọi đúng tool có trong AVAILABLE_TOOLS
        if tool_name not in AVAILABLE_TOOLS:
            obs = f"LỖI: Công cụ '{tool_name}' không có trong danh sách cho phép."
        else:
            try:
                obs = AVAILABLE_TOOLS[tool_name](*args)
            except TypeError as e:
                obs = f"LỖI: Gọi công cụ '{tool_name}' sai số lượng/kiểu tham số. Chi tiết: {e}"
            except Exception as e:
                obs = f"LỖI HỆ THỐNG: {e}"

        print(f"👁️ Observation: {obs}")
        scratchpad += f"Thought: {thought}\nAction: {action_line}\nObservation: {obs}\n\n"

    if final_answer is None:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        final_answer = (
            "Xin lỗi, tôi chưa thể xử lý xong yêu cầu này trong giới hạn cho phép. "
            "Vui lòng liên hệ bộ phận chăm sóc khách hàng để được hỗ trợ thêm."
        )
        print(f"🏁 Final Answer (fallback): {final_answer}")

    return final_answer


def run_test_case(test_case: dict, provider):
    """Chạy 1 test case qua cả Chatbot Baseline và ReAct Agent để so sánh."""
    print("\n" + "=" * 70)
    print(f"📋 TEST CASE #{test_case['id']} — {test_case['category']}")
    print(f"❓ Câu hỏi: {test_case['question']}")
    print(f"✅ Kỳ vọng: {test_case['expected_behavior']}")
    print("=" * 70)

    print("\n--- CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(test_case["question"], provider)

    print("\n--- CHẠY TRÊN REACT AGENT ---")
    run_react_agent(test_case["question"], provider)


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    # Cho phép chạy 1 test case cụ thể: python src/app.py <id>
    # Cho phép chạy toàn bộ: python src/app.py all
    # Mặc định (không tham số): chỉ chạy 1 test case (id=4) để tránh vượt
    # hạn mức free tier (Gemini free tier: 5 request/phút).
    if len(sys.argv) > 1 and sys.argv[1].lower() == "all":
        selected = tests
        print("ℹ️ Chạy toàn bộ 5 test case — có thể mất vài phút nếu bị rate limit, code sẽ tự chờ và thử lại.")
    elif len(sys.argv) > 1:
        try:
            selected_id = int(sys.argv[1])
            selected = [t for t in tests if t["id"] == selected_id]
            if not selected:
                print(f"⚠️ Không tìm thấy test case id={selected_id}. Chạy test case mặc định (id=4) thay thế.")
                selected = [t for t in tests if t["id"] == 4] or tests[:1]
        except ValueError:
            print("⚠️ Tham số phải là số nguyên hoặc 'all'. Chạy test case mặc định (id=4) thay thế.")
            selected = [t for t in tests if t["id"] == 4] or tests[:1]
    else:
        selected = [t for t in tests if t["id"] == 4] or tests[:1]
        print("ℹ️ Không truyền tham số nên chỉ chạy 1 test case (id=4, multi-step 2 tools) để tránh rate limit.")
        print("ℹ️ Chạy test khác: python src/app.py <id>  |  Chạy toàn bộ: python src/app.py all")

    for tc in selected:
        run_test_case(tc, provider)
        if len(selected) > 1:
            time.sleep(15)  # nghỉ giữa các test case để tránh dồn request
