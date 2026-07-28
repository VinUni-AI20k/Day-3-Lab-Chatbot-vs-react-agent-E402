"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import ast
import json
import os
import re
import sys
from datetime import date
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

_ACTION_RE = re.compile(r"(\w+)\s*\((.*)\)", re.DOTALL)


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
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def parse_action(action_str: str):
    """
    Phân tích một dòng Action dạng lời gọi hàm Python (VD: book_ticket(quantity=2, zone="VIP"))
    thành (tool_name, kwargs). Chỉ dùng ast.parse + ast.literal_eval (không eval()) nên an toàn,
    không thực thi mã tùy ý — chỉ chấp nhận tham số dạng key=value với giá trị literal.
    """
    match = _ACTION_RE.search(action_str.strip())
    if not match:
        raise ValueError(f"Không thể phân tích cú pháp Action: '{action_str}'")

    tool_name, args_str = match.group(1), match.group(2)
    try:
        call_node = ast.parse(f"f({args_str})", mode="eval").body
    except SyntaxError as e:
        raise ValueError(f"Cú pháp tham số không hợp lệ trong Action: '{action_str}'") from e

    if call_node.args:
        raise ValueError("Action chỉ hỗ trợ tham số dạng key=value (named arguments).")

    kwargs = {}
    for kw in call_node.keywords:
        kwargs[kw.arg] = ast.literal_eval(kw.value)
    return tool_name, kwargs


def _extract_after_label(label: str, text: str) -> str:
    match = re.search(rf"{label}\s*:\s*(.+)", text)
    if not match:
        return None
    return match.group(1).splitlines()[0].strip()


def _extract_final_answer(text: str) -> str:
    match = re.search(r"Final Answer\s*:\s*(.+)", text, re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def run_react_agent(user_query: str, provider, verbose: bool = True) -> str:
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    Agent tự quyết định mỗi bước có cần gọi Tool hay đã đủ thông tin để trả lời thẳng
    (Final Answer) — xem REACT_SYSTEM_PROMPT trong src/prompts.py.
    """
    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    scratchpad = ""
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        if verbose:
            print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        prompt = (
            f"[Hôm nay là {date.today():%Y-%m-%d}. Khi người dùng nói 'hôm nay'/'tối nay', "
            f"hãy dùng đúng ngày này cho tham số date.]\n"
            f"Câu hỏi của người dùng: {user_query}\n\n{scratchpad}"
        ).strip()
        raw_response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        cleaned = raw_response.replace("**", "")

        thought = _extract_after_label("Thought", cleaned) or ""
        if thought and verbose:
            print(f"🧠 Thought: {thought}")

        final_answer = _extract_final_answer(cleaned)
        if final_answer:
            if verbose:
                print(f"🏁 Final Answer: {final_answer}")
            return final_answer

        action_line = _extract_after_label("Action", cleaned)
        if not action_line:
            if verbose:
                print("⚠️ Không nhận được Action hay Final Answer hợp lệ từ mô hình. Dừng vòng lặp.")
            return raw_response.strip()

        if verbose:
            print(f"🛠️ Action: {action_line}")

        try:
            tool_name, kwargs = parse_action(action_line)
            if tool_name not in AVAILABLE_TOOLS:
                observation = f"LỖI: Không có công cụ tên '{tool_name}'. Các công cụ hợp lệ: {list(AVAILABLE_TOOLS.keys())}."
            else:
                observation = AVAILABLE_TOOLS[tool_name](**kwargs)
        except ValueError as e:
            observation = f"LỖI: {e}"
        except TypeError as e:
            observation = f"LỖI: Gọi công cụ với tham số không hợp lệ: {e}"
        except Exception as e:
            observation = f"LỖI: Công cụ gặp sự cố không mong muốn: {e}"

        if verbose:
            print(f"👁️ Observation: {observation}")

        scratchpad += f"Thought: {thought}\nAction: {action_line}\nObservation: {observation}\n\n"

    if verbose:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
    return (
        "Xin lỗi, yêu cầu này cần nhiều bước xử lý hơn mức cho phép hoặc liên tục gặp lỗi. "
        "Bạn vui lòng thử lại với yêu cầu cụ thể hơn hoặc liên hệ tổng đài CGV để được hỗ trợ trực tiếp."
    )


def run_test_suite(provider) -> None:
    """Chạy toàn bộ config/test_cases.json qua ReAct Agent, in kèm category & kỳ vọng của Role 1."""
    tests = load_test_cases()
    print(f"\n📋 Chạy {len(tests)} test cases qua ReAct Agent...")
    for t in tests:
        print("\n" + "=" * 70)
        print(f"#{t['id']} [{t['category']}] {t['question']}")
        print(f"Kỳ vọng: {t['expected_behavior']}")
        answer = run_react_agent(t["question"], provider)
        print(f"\n✅ Kết quả cuối cùng: {answer}")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: TRỢ LÝ ĐẶT VÉ XEM PHIM CGV")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    print("\n💬 Gõ câu hỏi để trò chuyện với ReAct Agent (VD: 'Phim Avatar 3 chiếu lúc mấy giờ ở CGV?').")
    print("   Gõ 'baseline: <câu hỏi>' để thử Chatbot Baseline (không có tool).")
    print("   Gõ 'test' để chạy toàn bộ config/test_cases.json qua ReAct Agent.")
    print("   Gõ 'exit' hoặc 'quit' để thoát.\n")

    while True:
        try:
            user_input = input("🙋 Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Tạm biệt!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "thoat"):
            print("👋 Tạm biệt!")
            break
        if user_input.lower() == "test":
            run_test_suite(provider)
            continue
        if user_input.lower().startswith("baseline:"):
            run_baseline_chatbot(user_input.split(":", 1)[1].strip(), provider)
            continue

        run_react_agent(user_input, provider)
