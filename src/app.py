"""
Ứng dụng tích hợp Chatbot Baseline và ReAct Agent.

Role 4 chịu trách nhiệm nối Test Cases, Prompt, LLM Provider và Tool Registry.
File này không hard-code tool để có thể tự nhận các tool do Role 2 đăng ký.
"""

import argparse
import ast
import json
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

# Cho phép chạy trực tiếp bằng ``python src/app.py``.
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SRC_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT
from providers import get_llm_provider
from tools import AVAILABLE_TOOLS

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

ACTION_PATTERN = re.compile(
    r"Action:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[(.*?)\]",
    flags=re.IGNORECASE | re.DOTALL,
)
FINAL_PATTERN = re.compile(
    r"Final\s*Answer:\s*(.+)",
    flags=re.IGNORECASE | re.DOTALL,
)
PROMPT_INJECTION_PATTERNS = (
    re.compile(
        r"ignore\s+(all|any|the)?\s*(previous|prior)\s+instructions?",
        re.IGNORECASE,
    ),
    re.compile(r"(reveal|show|print|tiết lộ).{0,40}system\s+prompt", re.IGNORECASE),
    re.compile(
        r"bỏ\s+qua\s+(mọi|tất\s+cả).{0,50}(xác\s+nhận|quy\s+tắc|chỉ\s+thị)",
        re.IGNORECASE,
    ),
)
INDIRECT_INJECTION_PATTERNS = (
    re.compile(r"system\s+(instruction|prompt)\s*(override)?", re.IGNORECASE),
    re.compile(r"ignore\s+(all|previous)\s+instructions?", re.IGNORECASE),
    re.compile(r"\bAction\s*:", re.IGNORECASE),
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+84|0)\d{9,10}(?!\d)")
NATIONAL_ID_PATTERN = re.compile(r"(?<!\d)\d{12}(?!\d)")
SENSITIVE_TOOLS = {"book_viewing", "make_payment", "delete_user_data"}
MAX_QUERY_LENGTH = 4_000
MAX_TOOL_ARGUMENT_LENGTH = 2_000


def load_test_cases(path: str | None = None) -> list[dict[str, Any]]:
    """Đọc và kiểm tra cấu trúc bộ test case của Role 1."""
    config_path = path or os.path.join(PROJECT_DIR, "config", "test_cases.json")

    with open(config_path, "r", encoding="utf-8") as file:
        test_cases = json.load(file)

    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError("config/test_cases.json phải là một danh sách không rỗng.")

    required_fields = {"id", "category", "question", "expected_behavior"}
    for index, test_case in enumerate(test_cases, start=1):
        if not isinstance(test_case, dict):
            raise ValueError(f"Test case #{index} phải là một JSON object.")
        missing = required_fields.difference(test_case)
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(f"Test case #{index} thiếu field: {fields}.")

    return test_cases


def _redact_sensitive_data(text: str) -> str:
    """Che dữ liệu cá nhân trước khi gửi LLM, ghi log hoặc trả output."""
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    return NATIONAL_ID_PATTERN.sub("[REDACTED_ID]", text)


def _apply_input_guardrails(user_query: str) -> tuple[str, str | None]:
    """Trả query đã che PII và lý do chặn nếu phát hiện input nguy hiểm."""
    if not isinstance(user_query, str) or not user_query.strip():
        return "", "Yêu cầu không được để trống."
    if len(user_query) > MAX_QUERY_LENGTH:
        return "", f"Yêu cầu vượt quá giới hạn {MAX_QUERY_LENGTH} ký tự."
    if any(pattern.search(user_query) for pattern in PROMPT_INJECTION_PATTERNS):
        return "", (
            "Phát hiện chỉ thị có dấu hiệu prompt injection hoặc yêu cầu "
            "vượt qua bước xác nhận."
        )
    return _redact_sensitive_data(user_query.strip()), None


def _sanitize_observation(observation: str) -> str:
    """Vô hiệu hóa chỉ thị ẩn trong dữ liệu trả về từ tool."""
    cleaned = _redact_sensitive_data(observation)
    for pattern in INDIRECT_INJECTION_PATTERNS:
        cleaned = pattern.sub("[BLOCKED_INJECTION]", cleaned)
    return cleaned


def _requires_grounding(user_query: str) -> bool:
    """Nhận diện yêu cầu cần dữ liệu/tool thay vì kiến thức chung."""
    normalized = user_query.casefold()
    indicators = (
        "tìm giúp",
        "tìm căn",
        "tìm phòng",
        "khung giờ",
        "lịch xem",
        "listing_id",
        "đặt ngay",
        "đặt lịch",
        "chuyển tiền",
        "gọi tool",
    )
    return any(indicator in normalized for indicator in indicators)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """Chạy đúng một LLM call và không cung cấp tool cho Chatbot Baseline."""
    safe_query, block_reason = _apply_input_guardrails(user_query)
    if block_reason:
        response = f"Yêu cầu đã bị Input Guardrail từ chối: {block_reason}"
        print(f"\n🛡️ [CHATBOT BASELINE] {response}")
        return response

    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {safe_query}")
    response = provider.generate(
        safe_query,
        system_prompt=CHATBOT_BASELINE_PROMPT,
    )
    response = _redact_sensitive_data(response)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def _parse_action(raw_arguments: str) -> tuple[list[Any], dict[str, Any]]:
    """
    Chuyển phần nằm trong ``tool[...]`` thành positional hoặc keyword args.

    Hỗ trợ:
      - get_weather["Hà Nội"]
      - search_flights["TP.HCM", "Hà Nội"]
      - search_rentals[{"location": "Cầu Giấy", "max_price": 5000000}]
    """
    raw_arguments = raw_arguments.strip()
    if not raw_arguments:
        return [], {}

    try:
        # Ưu tiên JSON để hỗ trợ true/false/null, sau đó mới fallback về
        # Python literal cho định dạng quen thuộc như get_weather['Hà Nội'].
        parsed = json.loads(f"[{raw_arguments}]")
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(f"[{raw_arguments}]")
        except (SyntaxError, ValueError) as error:
            raise ValueError(
                "Tham số Action không hợp lệ; hãy dùng chuỗi, số hoặc "
                "JSON/Python literal."
            ) from error

    if len(parsed) == 1 and isinstance(parsed[0], dict):
        return [], parsed[0]
    return parsed, {}


def _execute_tool(
    tool_name: str,
    raw_arguments: str,
    *,
    side_effect_confirmed: bool = False,
) -> str:
    """Kiểm tra registry, parse tham số và thực thi một tool an toàn."""
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        available = ", ".join(sorted(AVAILABLE_TOOLS)) or "(không có)"
        return (
            f"LỖI: Tool '{tool_name}' không tồn tại. "
            f"Các tool hợp lệ: {available}."
        )

    if tool_name in SENSITIVE_TOOLS and not side_effect_confirmed:
        return (
            f"LỖI: Tool nhạy cảm '{tool_name}' cần xác nhận rõ ràng "
            "từ tầng ứng dụng trước khi thực thi."
        )

    if len(raw_arguments) > MAX_TOOL_ARGUMENT_LENGTH:
        return (
            f"LỖI: Tham số tool vượt quá giới hạn "
            f"{MAX_TOOL_ARGUMENT_LENGTH} ký tự."
        )

    try:
        args, kwargs = _parse_action(raw_arguments)
        result = tool(*args, **kwargs)
    except TypeError as error:
        return f"LỖI: Sai tham số khi gọi tool '{tool_name}': {error}"
    except Exception as error:
        # Tool error là Observation để Agent phục hồi, không làm app crash.
        return f"LỖI: Tool '{tool_name}' thực thi thất bại: {error}"

    if result is None:
        return f"LỖI: Tool '{tool_name}' không trả về dữ liệu."
    if isinstance(result, str):
        return _sanitize_observation(result)
    return _sanitize_observation(json.dumps(result, ensure_ascii=False))


def _build_react_input(user_query: str, trace: list[str]) -> str:
    """Tạo input cho bước suy luận kế tiếp, gồm câu hỏi và trace đã có."""
    sections = [f"Question: {user_query}"]
    if trace:
        sections.append("\n".join(trace))
    sections.append(
        "Hãy đưa ra đúng một Action tiếp theo, hoặc Final Answer nếu đã đủ bằng chứng."
    )
    return "\n\n".join(sections)


def run_react_agent(
    user_query: str,
    provider,
    *,
    side_effect_confirmed: bool = False,
) -> dict[str, Any]:
    """Chạy vòng lặp Thought → Action → Observation với phanh an toàn."""
    safe_query, block_reason = _apply_input_guardrails(user_query)
    if block_reason:
        fallback = f"Yêu cầu đã bị Input Guardrail từ chối: {block_reason}"
        print(f"\n🛡️ [REACT AGENT] {fallback}")
        return {
            "status": "guardrail",
            "answer": fallback,
            "steps": 0,
            "trace": [],
        }

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {safe_query}")
    trace: list[str] = []
    previous_action: tuple[str, str] | None = None
    successful_observations = 0
    grounding_required = _requires_grounding(safe_query)

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct ({step}/{MAX_ITERATIONS}) ---")
        llm_output = provider.generate(
            _build_react_input(safe_query, trace),
            system_prompt=REACT_SYSTEM_PROMPT,
        ).strip()
        llm_output = _redact_sensitive_data(llm_output)
        print(llm_output)

        final_match = FINAL_PATTERN.search(llm_output)
        if final_match:
            if grounding_required and successful_observations == 0:
                observation = (
                    "LỖI: Yêu cầu này cần dữ liệu thực tế nhưng chưa có "
                    "Observation hợp lệ. Không được tạo Final Answer có dữ liệu bịa."
                )
                trace.extend([llm_output, f"Observation: {observation}"])
                print(f"👁️ Observation: {observation}")
                continue

            final_answer = final_match.group(1).strip()
            print(f"🏁 Final Answer: {final_answer}")
            return {
                "status": "completed",
                "answer": final_answer,
                "steps": step,
                "trace": trace + [llm_output],
            }

        action_match = ACTION_PATTERN.search(llm_output)
        if not action_match:
            observation = (
                "LỖI: Không parse được phản hồi. Hãy trả về đúng định dạng "
                "Action: tool[tham_số] hoặc Final Answer: nội_dung."
            )
            trace.extend([llm_output, f"Observation: {observation}"])
            print(f"👁️ Observation: {observation}")
            continue

        tool_name = action_match.group(1)
        raw_arguments = action_match.group(2).strip()
        current_action = (tool_name, raw_arguments)

        if current_action == previous_action:
            observation = (
                "LỖI: Action này vừa được thực hiện với cùng tham số. "
                "Không lặp lại; hãy đổi hướng hoặc trả lời an toàn."
            )
        else:
            observation = _execute_tool(
                tool_name,
                raw_arguments,
                side_effect_confirmed=side_effect_confirmed,
            )
            if not observation.startswith("LỖI:"):
                successful_observations += 1

        previous_action = current_action
        trace.extend([llm_output, f"Observation: {observation}"])
        print(f"👁️ Observation: {observation}")

    fallback = (
        f"Xin lỗi, tôi chưa thể hoàn tất yêu cầu sau {MAX_ITERATIONS} bước. "
        "Tôi sẽ không khẳng định đã tìm hoặc đặt lịch khi chưa có đủ dữ liệu."
    )
    print(f"\n🛡️ GUARDRAIL: {fallback}")
    return {
        "status": "guardrail",
        "answer": fallback,
        "steps": MAX_ITERATIONS,
        "trace": trace,
    }


def _select_test_cases(
    test_cases: list[dict[str, Any]],
    case_id: int | None,
) -> list[dict[str, Any]]:
    if case_id is None:
        return test_cases

    selected = [case for case in test_cases if case["id"] == case_id]
    if not selected:
        valid_ids = ", ".join(str(case["id"]) for case in test_cases)
        raise ValueError(f"Không có test case id={case_id}. ID hợp lệ: {valid_ids}.")
    return selected


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="So sánh Chatbot Baseline và ReAct Agent.",
    )
    parser.add_argument(
        "--mode",
        choices=("baseline", "agent", "both"),
        default="both",
        help="Chế độ chạy (mặc định: both).",
    )
    parser.add_argument(
        "--case",
        type=int,
        dest="case_id",
        help="Chỉ chạy test case có ID tương ứng.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_cli_args()

    try:
        test_cases = _select_test_cases(load_test_cases(), args.case_id)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"❌ Không thể tải test cases: {error}")
        return 1

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")

    print("=" * 64)
    print("🏠 TRỢ LÝ TÌM & ĐẶT LỊCH XEM NHÀ TRỌ / CĂN HỘ CHO THUÊ")
    print("=" * 64)
    print(
        f"🔌 Provider: {provider.__class__.__name__} "
        f"(Model: {model_name})"
    )
    print(f"✅ Đã tải {len(test_cases)} test case.")
    print(f"🧰 Tool registry: {', '.join(sorted(AVAILABLE_TOOLS)) or '(trống)'}")

    for test_case in test_cases:
        print("\n" + "=" * 64)
        print(f"TEST #{test_case['id']} — {test_case['category']}")
        print(f"Kỳ vọng: {test_case['expected_behavior']}")

        if args.mode in ("baseline", "both"):
            run_baseline_chatbot(test_case["question"], provider)
        if args.mode in ("agent", "both"):
            run_react_agent(test_case["question"], provider)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
