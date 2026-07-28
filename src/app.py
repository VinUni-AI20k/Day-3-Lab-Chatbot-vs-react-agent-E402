"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import ast
import json
import os
import re
import sys
import threading
from queue import Queue

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
TOOLS_IMPORT_ERROR = None
try:
    import tools as tools_module

    AVAILABLE_TOOLS = getattr(tools_module, "AVAILABLE_TOOLS", None)
    if AVAILABLE_TOOLS is None:
        tool_functions = getattr(tools_module, "TOOLS", [])
        AVAILABLE_TOOLS = {
            tool.__name__: tool for tool in tool_functions if callable(tool)
        }
    if not isinstance(AVAILABLE_TOOLS, dict):
        raise TypeError("Tool registry phải là dictionary hoặc danh sách callable.")
except Exception as exc:
    AVAILABLE_TOOLS = {}
    TOOLS_IMPORT_ERROR = str(exc)

from prompts import (
    CHATBOT_BASELINE_PROMPT,
    MAX_ITERATIONS,
    REACT_SYSTEM_PROMPT,
    TIMEOUT_SECONDS,
)
from providers import get_llm_provider

load_dotenv()

ACTION_PATTERN = re.compile(
    r"^Action:\s*([A-Za-z_]\w*)\[(.*)\]\s*$",
    re.MULTILINE,
)
FINAL_ANSWER_PATTERN = re.compile(
    r"^Final Answer:\s*(.+)\Z",
    re.MULTILINE | re.DOTALL,
)


def parse_action(response: str):
    """Parse đúng một dòng Action theo dạng ``tool_name[arg1, arg2]``."""
    if not isinstance(response, str):
        raise ValueError("Phản hồi của LLM phải là chuỗi.")

    matches = ACTION_PATTERN.findall(response)
    if not matches:
        raise ValueError("Không tìm thấy Action hợp lệ.")
    if len(matches) > 1:
        raise ValueError("Mỗi phản hồi chỉ được chứa một Action.")

    tool_name, raw_args = matches[0]
    try:
        args = ast.literal_eval(f"[{raw_args}]") if raw_args.strip() else []
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"Tham số Action không hợp lệ: {exc}") from exc

    return tool_name, args


def execute_tool(
    tool_name: str,
    args: list,
    tool_registry=None,
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> str:
    """Thực thi tool có giới hạn thời gian và luôn trả về Observation dạng chuỗi."""
    registry = AVAILABLE_TOOLS if tool_registry is None else tool_registry
    if tool_name not in registry:
        available = ", ".join(sorted(registry)) or "(không có)"
        return f"ERROR: Tool '{tool_name}' không tồn tại. Tool hợp lệ: {available}."

    result_queue = Queue(maxsize=1)

    def invoke_tool():
        try:
            result_queue.put((True, registry[tool_name](*args)))
        except Exception as exc:
            result_queue.put((False, exc))

    worker = threading.Thread(target=invoke_tool, daemon=True)
    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        return f"ERROR: Tool '{tool_name}' vượt quá timeout {timeout_seconds} giây."

    succeeded, payload = result_queue.get()
    if not succeeded:
        return f"ERROR: Tool '{tool_name}' thất bại: {payload}"
    return str(payload)


def load_test_cases() -> list:
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        raw_cases = json.load(f)

    if not isinstance(raw_cases, list):
        raise ValueError("File test cases phải chứa một JSON array.")

    valid_cases = []
    for index, test_case in enumerate(raw_cases, start=1):
        question = test_case.get("question") if isinstance(test_case, dict) else None
        if not isinstance(question, str) or not question.strip():
            print(
                f"⚠️ Bỏ qua test case #{index}: thiếu trường 'question' hợp lệ."
            )
            continue
        valid_cases.append(test_case)

    return valid_cases


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = str(
        provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT) or ""
    )
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider) -> dict:
    """
    Chạy vòng lặp ReAct và trả về kết quả có cấu trúc để tiện kiểm thử.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    trace = []

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        scratchpad = "\n".join(trace) if trace else "(chưa có Observation)"
        llm_prompt = (
            f"User Query:\n{user_query}\n\n"
            f"Scratchpad:\n{scratchpad}\n\n"
            "Hãy đưa ra bước ReAct tiếp theo theo đúng định dạng trong system prompt."
        )

        try:
            response = provider.generate(
                llm_prompt,
                system_prompt=REACT_SYSTEM_PROMPT,
            )
        except Exception as exc:
            fallback = f"Không thể gọi LLM để hoàn tất yêu cầu: {exc}"
            trace.append(f"LLM ERROR: {exc}")
            print(f"❌ {fallback}")
            return {
                "status": "error",
                "final_answer": fallback,
                "trace": trace,
                "iterations": step,
            }

        response = str(response or "").strip()
        trace.append(response)
        print(response)

        final_match = FINAL_ANSWER_PATTERN.search(response)
        action_matches = ACTION_PATTERN.findall(response)
        if final_match and not action_matches:
            final_answer = final_match.group(1).strip()
            print(f"🏁 Final Answer: {final_answer}")
            return {
                "status": "success",
                "final_answer": final_answer,
                "trace": trace,
                "iterations": step,
            }

        if final_match and action_matches:
            observation = (
                "ERROR: Phản hồi không được chứa đồng thời Action và Final Answer."
            )
        else:
            try:
                tool_name, args = parse_action(response)
                observation = execute_tool(tool_name, args)
            except ValueError as exc:
                observation = f"ERROR: {exc}"

        observation_line = f"Observation: {observation}"
        trace.append(observation_line)
        print(f"👁️ {observation_line}")

    fallback = (
        f"Không thể hoàn tất yêu cầu sau {MAX_ITERATIONS} bước vì chưa thu thập "
        "đủ dữ liệu đáng tin cậy."
    )
    print(f"🛡️ GUARDRAIL TRIGGERED: {fallback}")
    return {
        "status": "guardrail",
        "final_answer": fallback,
        "trace": trace,
        "iterations": MAX_ITERATIONS,
    }


def main():
    """Chạy toàn bộ test case qua cả Baseline LLM và ReAct Agent."""
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    if TOOLS_IMPORT_ERROR:
        print(
            "⚠️ Không thể nạp tool registry; ReAct Agent sẽ dùng registry rỗng. "
            f"Chi tiết: {TOOLS_IMPORT_ERROR}"
        )

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    if not tests:
        print("⚠️ Không có test case hợp lệ để chạy.")
        return

    for index, test_case in enumerate(tests, start=1):
        case_id = test_case.get("id", index)
        category = test_case.get("category", "Không phân loại")
        user_query = test_case["question"]

        print("\n" + "=" * 70)
        print(f"🧪 TEST CASE {case_id}: {category}")
        print(f"❓ {user_query}")
        print("=" * 70)

        print("\n--- VERSION 1: CHATBOT BASELINE ---")
        try:
            run_baseline_chatbot(user_query, provider)
        except Exception as exc:
            print(f"❌ Baseline thất bại ở test case {case_id}: {exc}")

        # print("\n--- VERSION 2: REACT AGENT ---")
        # try:
        #     run_react_agent(user_query, provider)
        # except Exception as exc:
        #     print(f"❌ ReAct Agent thất bại ở test case {case_id}: {exc}")


if __name__ == "__main__":
    main()
