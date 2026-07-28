"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import argparse
import ast
from datetime import datetime
import inspect
import json
import os
import re
import sys

from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """Chạy đúng một lượt sinh phản hồi bằng LLM, không gọi công cụ."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(
        user_query,
        system_prompt=CHATBOT_BASELINE_PROMPT,
    )
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def parse_action(model_output: str):
    """Tách một Action dạng tool[arg1, arg2] từ phản hồi của model."""
    action_lines = re.findall(
        r"(?im)^\s*Action\s*:\s*([A-Za-z_]\w*)\s*([\[(])(.*)([\])])\s*$",
        model_output,
    )
    if len(action_lines) != 1:
        return None, None, (
            "Phản hồi phải chứa đúng một dòng Action theo mẫu "
            "Action: ten_tool[tham_so]."
        )

    tool_name, opening, raw_args, closing = action_lines[0]
    expected_closing = "]" if opening == "[" else ")"
    if closing != expected_closing:
        return None, None, "Dấu ngoặc trong Action không khớp."

    try:
        args = [] if not raw_args.strip() else ast.literal_eval(f"[{raw_args}]")
    except (SyntaxError, ValueError) as exc:
        return None, None, f"Không thể phân tích tham số Action: {exc}."

    return tool_name, args, None


def extract_final_answer(model_output: str):
    """Lấy phần Final Answer nếu model đã kết thúc đúng định dạng."""
    match = re.search(r"(?is)Final Answer\s*:\s*(.+)$", model_output)
    return match.group(1).strip() if match else None


def query_requires_tool(user_query: str) -> bool:
    """Nhận diện yêu cầu cần dữ liệu đơn hàng/vận chuyển cụ thể."""
    query = user_query.lower()
    return (
        "#" in query
        or "mã đơn" in query
        or "mã vận đơn" in query
        or "trạng thái đơn hàng" in query
        or "bao giờ thì tới" in query
    )


def validate_user_input(user_query: str):
    """Phát hiện ngày DD/MM/YYYY không hợp lệ trước khi Agent gọi tool."""
    for date_text in re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", user_query):
        try:
            datetime.strptime(date_text, "%d/%m/%Y")
        except ValueError:
            return (
                f"Ngày '{date_text}' không hợp lệ. Vui lòng cung cấp ngày "
                "theo định dạng DD/MM/YYYY và kiểm tra lại giá trị ngày/tháng."
            )
    return None


def execute_action(tool_name, args, user_query, seen_actions):
    """Kiểm tra và thực thi đúng một tool; mọi lỗi đều thành Observation."""
    if tool_name not in AVAILABLE_TOOLS:
        valid_tools = ", ".join(AVAILABLE_TOOLS)
        return (
            f"LỖI: Tool '{tool_name}' không tồn tại. "
            f"Các tool hợp lệ: {valid_tools}.",
            False,
        )

    signature_key = (tool_name, repr(args))
    if signature_key in seen_actions:
        return (
            "LỖI: Action này đã được thực hiện với cùng tham số. "
            "Hãy dùng Observation trước đó hoặc chọn hướng xử lý khác.",
            False,
        )
    seen_actions.add(signature_key)

    if tool_name == "create_return_request":
        confirmation_terms = ("xác nhận", "đồng ý tạo", "tôi đồng ý")
        if not any(term in user_query.lower() for term in confirmation_terms):
            return (
                "LỖI AN TOÀN: Chưa có xác nhận rõ ràng của người dùng, "
                "không được tạo yêu cầu đổi trả.",
                False,
            )

    tool = AVAILABLE_TOOLS[tool_name]
    try:
        inspect.signature(tool).bind(*args)
    except TypeError as exc:
        return (
            f"LỖI THAM SỐ: {tool_name}{inspect.signature(tool)}; {exc}.",
            False,
        )

    try:
        return str(tool(*args)), True
    except Exception as exc:
        return f"LỖI TOOL: {type(exc).__name__}: {exc}.", False


def build_react_system_prompt() -> str:
    """Gắn chữ ký tool thực tế vào prompt để tránh lệch contract giữa các role."""
    # Loại bỏ hai dòng phân cách conflict còn sót trong prompt đã merge.
    clean_prompt = "\n".join(
        line
        for line in REACT_SYSTEM_PROMPT.splitlines()
        if line.strip() != "======="
    )
    tool_contracts = "\n".join(
        f"- {name}{inspect.signature(tool)}"
        for name, tool in AVAILABLE_TOOLS.items()
    )
    return (
        clean_prompt.format(MAX_ITERATIONS=MAX_ITERATIONS)
        + "\n\n========================\n"
        + "TOOL CONTRACT THỰC TẾ TỪ REGISTRY (NGUỒN CHUẨN)\n"
        + "========================\n"
        + tool_contracts
        + "\nHãy ưu tiên tuyệt đối các chữ ký thực tế này khi tạo Action."
    )


def run_react_agent(user_query: str, provider) -> dict:
    """Chạy vòng lặp Thought -> Action -> Observation với phanh an toàn."""
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    validation_error = validate_user_input(user_query)
    if validation_error:
        print(f"🛡️ INPUT GUARDRAIL: {validation_error}")
        return {
            "status": "invalid_input",
            "answer": validation_error,
            "steps": 0,
            "tool_calls": 0,
            "trace": [
                {
                    "step": 0,
                    "observation": f"LỖI ĐẦU VÀO: {validation_error}",
                }
            ],
        }

    system_prompt = build_react_system_prompt()
    conversation = f"Question: {user_query}"
    trace = []
    seen_actions = set()
    tool_calls = 0

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        model_output = provider.generate(
            f"{conversation}\n\nHãy đưa ra bước ReAct tiếp theo.",
            system_prompt=system_prompt,
        ).strip()
        print(model_output)

        final_answer = extract_final_answer(model_output)
        has_action = bool(re.search(r"(?im)^\s*Action\s*:", model_output))

        if final_answer and has_action:
            observation = (
                "LỖI ĐỊNH DẠNG: Không được trả Action và Final Answer "
                "trong cùng một bước."
            )
        elif final_answer:
            if query_requires_tool(user_query) and tool_calls == 0:
                observation = (
                    "LỖI GROUNDING: Yêu cầu cần dữ liệu hệ thống nhưng chưa có "
                    "Observation từ tool. Hãy gọi tool phù hợp trước."
                )
            else:
                print("✅ Agent đã kết thúc bằng Final Answer hợp lệ.")
                trace.append(
                    {
                        "step": step,
                        "model_output": model_output,
                        "final_answer": final_answer,
                    }
                )
                return {
                    "status": "completed",
                    "answer": final_answer,
                    "steps": step,
                    "tool_calls": tool_calls,
                    "trace": trace,
                }
        else:
            tool_name, args, parse_error = parse_action(model_output)
            if parse_error:
                observation = f"LỖI PARSE: {parse_error}"
            else:
                observation, executed = execute_action(
                    tool_name,
                    args,
                    user_query,
                    seen_actions,
                )
                tool_calls += int(executed)

        print(f"👁️ Observation: {observation}")
        trace.append(
            {
                "step": step,
                "model_output": model_output,
                "observation": observation,
            }
        )
        conversation += f"\n\n{model_output}\nObservation: {observation}"

    fallback = (
        f"Đã đạt giới hạn {MAX_ITERATIONS} bước nhưng chưa đủ thông tin để "
        "hoàn thành yêu cầu. Vui lòng kiểm tra lại mã đơn/tham số hoặc liên "
        "hệ nhân viên hỗ trợ."
    )
    print(f"\n🛡️ GUARDRAIL TRIGGERED: {fallback}")
    return {
        "status": "guardrail",
        "answer": fallback,
        "steps": MAX_ITERATIONS,
        "tool_calls": tool_calls,
        "trace": trace,
    }


def select_test_cases(test_cases, test_id):
    """Chọn một test theo id; dùng 0 để chạy toàn bộ."""
    if test_id == 0:
        return test_cases

    selected = [case for case in test_cases if case["id"] == test_id]
    if not selected:
        valid_ids = ", ".join(str(case["id"]) for case in test_cases)
        raise ValueError(f"Test id không hợp lệ. Các id hợp lệ: {valid_ids}.")
    return selected


def parse_cli_args():
    """Đọc lựa chọn chế độ chạy từ command line."""
    parser = argparse.ArgumentParser(
        description="Chạy Chatbot Baseline hoặc ReAct Agent."
    )
    parser.add_argument(
        "--mode",
        choices=("baseline", "react", "compare"),
        default="react",
        help="Chế độ chạy; mặc định là react.",
    )
    parser.add_argument(
        "--test-id",
        type=int,
        default=3,
        help="ID test cần chạy; dùng 0 để chạy toàn bộ. Mặc định: 3.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(
        f"🔌 LLM Provider đang hoạt động: "
        f"{provider.__class__.__name__} (Model: {model_name})"
    )

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases\n")

    args = parse_cli_args()
    selected_tests = select_test_cases(tests, args.test_id)
    print(f"🧰 Tool registry: {', '.join(AVAILABLE_TOOLS)}")

    for test_case in selected_tests:
        print(
            f"\n{'=' * 60}\n"
            f"Test #{test_case['id']} — {test_case['category']}\n"
            f"Kỳ vọng: {test_case['expected_behavior']}"
        )

        if args.mode in ("baseline", "compare"):
            run_baseline_chatbot(test_case["question"], provider)

        if args.mode in ("react", "compare"):
            result = run_react_agent(test_case["question"], provider)
            print(
                "\n📊 Kết quả Agent:"
                f" status={result['status']},"
                f" steps={result['steps']},"
                f" tool_calls={result['tool_calls']}"
            )
