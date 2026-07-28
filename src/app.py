"""
Ứng dụng Cupid Chatbot và ReAct Agent.

Mốc 3 triển khai một vòng lặp ReAct tổng quát:
LLM -> parser -> tool executor -> Observation -> LLM, kèm guardrails.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from prompts import (  # noqa: E402
    CHATBOT_BASELINE_PROMPT,
    MAX_ITERATIONS,
    MAX_REPEATED_ACTIONS,
    REACT_SYSTEM_PROMPT,
    TIMEOUT_SECONDS,
)
from providers import get_llm_provider  # noqa: E402
from tools import AVAILABLE_TOOLS  # noqa: E402


MILESTONE_2_TEST_COUNT = 5
ACTION_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\[(?P<args>.*)\]\s*$"
)


@dataclass
class AgentDecision:
    thought: str = ""
    action_name: str | None = None
    action_args: tuple = ()
    final_answer: str | None = None
    error: str | None = None


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def run_baseline_chatbot(user_query: str, provider):
    """Gọi LLM đúng một lần và không cấp tool cho Baseline Chatbot."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    print("📈 Telemetry: LLM calls = 1 | Tool calls = 0")
    return {
        "question": user_query,
        "response": response,
        "llm_calls": 1,
        "tool_calls": 0,
    }


def run_baseline_suite(test_cases, provider):
    """Chạy Baseline trên danh sách test cases và trả raw results."""
    results = []
    for test_case in test_cases:
        print(
            f"\n{'=' * 60}\n"
            f"TEST CASE #{test_case['id']} - {test_case['category']}\n"
            f"{'=' * 60}"
        )
        result = run_baseline_chatbot(test_case["question"], provider)
        result["id"] = test_case["id"]
        results.append(result)

    print(
        f"\n📊 TỔNG KẾT BASELINE: {len(results)} test cases | "
        f"LLM calls = {sum(item['llm_calls'] for item in results)} | "
        f"Tool calls = {sum(item['tool_calls'] for item in results)}"
    )
    return results


def parse_react_response(raw_response: str) -> AgentDecision:
    """Parse đúng một Action hoặc Final Answer từ phản hồi LLM."""
    if not isinstance(raw_response, str) or not raw_response.strip():
        return AgentDecision(error="Phản hồi LLM rỗng.")

    thought_match = re.search(
        r"(?ims)^\s*Thought:\s*(.*?)(?=^\s*(?:Action|Final Answer):|\Z)",
        raw_response,
    )
    action_match = re.search(r"(?im)^\s*Action:\s*(.+?)\s*$", raw_response)
    final_match = re.search(
        r"(?ims)^\s*Final Answer:\s*(.+?)\s*$",
        raw_response,
    )
    thought = thought_match.group(1).strip() if thought_match else ""

    if action_match and final_match:
        return AgentDecision(
            thought=thought,
            error="Mỗi lượt chỉ được chứa Action hoặc Final Answer, không được có cả hai.",
        )
    if final_match:
        return AgentDecision(
            thought=thought,
            final_answer=final_match.group(1).strip(),
        )
    if not action_match:
        return AgentDecision(
            thought=thought,
            error="Không tìm thấy Action hoặc Final Answer đúng định dạng.",
        )

    action_text = action_match.group(1).strip()
    action_parts = ACTION_PATTERN.fullmatch(action_text)
    if not action_parts:
        return AgentDecision(
            thought=thought,
            error=(
                "Action sai cú pháp. Định dạng đúng là "
                'tool_name["arg1", "arg2"].'
            ),
        )

    args_text = action_parts.group("args").strip()
    try:
        action_args = (
            ast.literal_eval(f"({args_text},)")
            if args_text
            else ()
        )
    except (SyntaxError, ValueError) as exc:
        return AgentDecision(
            thought=thought,
            error=f"Không parse được tham số Action: {exc}.",
        )

    return AgentDecision(
        thought=thought,
        action_name=action_parts.group("name"),
        action_args=action_args,
    )


def execute_tool(
    tool_name: str,
    tool_args: tuple,
    available_tools=None,
    timeout_seconds: int = TIMEOUT_SECONDS,
):
    """Thực thi một tool hợp lệ và chuyển mọi lỗi thành Observation dạng chuỗi."""
    registry = AVAILABLE_TOOLS if available_tools is None else available_tools
    if tool_name not in registry:
        valid_tools = ", ".join(sorted(registry))
        return (
            f"LỖI: Tool '{tool_name}' không tồn tại. "
            f"Các tool hợp lệ: {valid_tools}.",
            False,
        )

    tool = registry[tool_name]
    try:
        inspect.signature(tool).bind(*tool_args)
    except TypeError as exc:
        return f"LỖI: Tham số của tool '{tool_name}' không hợp lệ: {exc}.", False

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(tool, *tool_args)
    try:
        result = future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        return (
            f"LỖI: Tool '{tool_name}' vượt quá timeout {timeout_seconds} giây.",
            True,
        )
    except Exception as exc:
        executor.shutdown(wait=True)
        return f"LỖI: Tool '{tool_name}' gặp lỗi nội bộ: {exc}.", True

    executor.shutdown(wait=True)
    return str(result), True


def _format_trace(trace):
    if not trace:
        return "(Chưa có Action hoặc Observation.)"

    blocks = []
    for item in trace:
        lines = [f"Thought: {item.get('thought') or '(không có)'}"]
        if item.get("action_name"):
            args_text = ", ".join(repr(arg) for arg in item.get("action_args", ()))
            lines.append(f"Action: {item['action_name']}[{args_text}]")
        elif item.get("raw_action"):
            lines.append(f"Action: {item['raw_action']}")
        lines.append(f"Observation: {item['observation']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_react_prompt(user_query: str, trace):
    """Tạo prompt lượt kế tiếp, luôn chứa đầy đủ Observation trước đó."""
    return (
        "USER QUESTION:\n"
        f"{user_query}\n\n"
        "TRACE SO FAR:\n"
        f"{_format_trace(trace)}\n\n"
        "Hãy trả về đúng một Thought và một Action, hoặc một Thought và "
        "Final Answer. Không tự viết Observation."
    )


def _action_key(tool_name: str, tool_args: tuple) -> str:
    return json.dumps(
        [tool_name, tool_args],
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def _query_requires_tool_evidence(user_query: str) -> bool:
    normalized = user_query.lower()
    keywords = (
        "hồ sơ",
        "ứng viên",
        "phù hợp",
        "tìm cho tôi",
        "so sánh",
        "mssv",
        "điểm tương thích",
    )
    return any(keyword in normalized for keyword in keywords)


def _is_safe_direct_answer(answer: str) -> bool:
    normalized = answer.lower()
    safe_phrases = (
        "cung cấp",
        "không hỗ trợ",
        "không thể",
        "chưa đủ",
        "cần tên",
        "cần mssv",
        "ngoài phạm vi",
    )
    return any(phrase in normalized for phrase in safe_phrases)


def _guardrail_result(
    user_query,
    trace,
    llm_calls,
    tool_calls,
    errors,
    stop_reason,
):
    final_answer = (
        "Xin lỗi, tôi chưa thể hoàn thành yêu cầu một cách có căn cứ. "
        "Vui lòng kiểm tra lại thông tin hoặc thử tiêu chí rõ ràng hơn."
    )
    print(f"🛡️ GUARDRAIL TRIGGERED: {stop_reason}")
    print(f"🏁 Safe Fallback: {final_answer}")
    return {
        "question": user_query,
        "status": "guardrail",
        "final_answer": final_answer,
        "trace": trace,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "errors": errors,
        "stop_reason": stop_reason,
    }


def run_react_agent(
    user_query: str,
    provider,
    available_tools=None,
    max_iterations: int = MAX_ITERATIONS,
):
    """Chạy ReAct loop thật với parser, executor, trace và guardrails."""
    registry = AVAILABLE_TOOLS if available_tools is None else available_tools
    trace = []
    errors = []
    seen_actions = set()
    repeated_actions = 0
    llm_calls = 0
    tool_calls = 0

    print(f"\n🤖 [CUPID REACT AGENT] Câu hỏi: {user_query}")

    for step in range(1, max_iterations + 1):
        print(f"\n--- 🔄 ReAct Step {step}/{max_iterations} ---")
        prompt = build_react_prompt(user_query, trace)
        raw_response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        llm_calls += 1
        decision = parse_react_response(raw_response)

        if decision.thought:
            print(f"🧠 Thought: {decision.thought}")

        if decision.error:
            observation = f"LỖI PARSER: {decision.error}"
            print(f"⚠️ {observation}")
            errors.append(observation)
            trace.append(
                {
                    "thought": decision.thought,
                    "raw_action": raw_response.strip(),
                    "observation": observation,
                }
            )
            continue

        if decision.final_answer is not None:
            if (
                _query_requires_tool_evidence(user_query)
                and tool_calls == 0
                and not _is_safe_direct_answer(decision.final_answer)
            ):
                observation = (
                    "LỖI GUARDRAIL: Final Answer cần dữ liệu tool nhưng chưa có "
                    "Observation làm bằng chứng."
                )
                print(f"⚠️ {observation}")
                errors.append(observation)
                trace.append(
                    {
                        "thought": decision.thought,
                        "observation": observation,
                    }
                )
                continue

            status = "recovered" if errors else "completed"
            print(f"🏁 Final Answer: {decision.final_answer}")
            return {
                "question": user_query,
                "status": status,
                "final_answer": decision.final_answer,
                "trace": trace,
                "llm_calls": llm_calls,
                "tool_calls": tool_calls,
                "errors": errors,
                "stop_reason": "final_answer",
            }

        action_key = _action_key(decision.action_name, decision.action_args)
        print(
            f"🛠️ Action: {decision.action_name}"
            f"[{', '.join(repr(arg) for arg in decision.action_args)}]"
        )

        if action_key in seen_actions:
            repeated_actions += 1
            observation = (
                "LỖI GUARDRAIL: Action này đã được gọi với cùng tham số. "
                "Hãy đổi chiến lược hoặc trả Safe Fallback."
            )
            print(f"👁️ Observation: {observation}")
            errors.append(observation)
            trace.append(
                {
                    "thought": decision.thought,
                    "action_name": decision.action_name,
                    "action_args": decision.action_args,
                    "observation": observation,
                }
            )
            if repeated_actions >= MAX_REPEATED_ACTIONS:
                return _guardrail_result(
                    user_query,
                    trace,
                    llm_calls,
                    tool_calls,
                    errors,
                    "Phát hiện Action lặp lại với cùng tham số.",
                )
            continue

        seen_actions.add(action_key)
        observation, was_executed = execute_tool(
            decision.action_name,
            decision.action_args,
            registry,
        )
        if was_executed:
            tool_calls += 1
        if observation.startswith("LỖI:"):
            errors.append(observation)

        print(f"👁️ Observation: {observation}")
        trace.append(
            {
                "thought": decision.thought,
                "action_name": decision.action_name,
                "action_args": decision.action_args,
                "observation": observation,
            }
        )

    return _guardrail_result(
        user_query,
        trace,
        llm_calls,
        tool_calls,
        errors,
        f"Đạt MAX_ITERATIONS={max_iterations}.",
    )


def run_react_suite(test_cases, provider):
    """Chạy ReAct Agent trên toàn bộ test cases và in telemetry tổng hợp."""
    results = []
    for test_case in test_cases:
        print(
            f"\n{'=' * 60}\n"
            f"TEST CASE #{test_case['id']} - {test_case['category']}\n"
            f"{'=' * 60}"
        )
        result = run_react_agent(test_case["question"], provider)
        result["id"] = test_case["id"]
        results.append(result)

    statuses = {}
    for result in results:
        statuses[result["status"]] = statuses.get(result["status"], 0) + 1
    print(
        f"\n📊 TỔNG KẾT REACT: {len(results)} test cases | "
        f"LLM calls = {sum(item['llm_calls'] for item in results)} | "
        f"Tool calls = {sum(item['tool_calls'] for item in results)} | "
        f"Status = {statuses}"
    )
    return results


def main():
    print("=" * 60)
    print("🏫 VINUNI - LAB 3: CHATBOT VS REACT AGENT")
    print("💘 CUPID AGENT")
    print("=" * 60)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(
        f"🔌 Provider: {provider.__class__.__name__} "
        f"(Model: {model_name})"
    )

    test_cases = load_test_cases()
    print(f"✅ Đã tải {len(test_cases)} test cases.")
    mode = os.getenv("APP_MODE", "react").lower().strip()

    if mode in {"baseline", "compare"}:
        print("\n--- BASELINE CHATBOT - MỐC 2 ---")
        run_baseline_suite(test_cases[:MILESTONE_2_TEST_COUNT], provider)
    if mode in {"react", "compare"}:
        print("\n--- REACT AGENT & SAFEGUARDS - MỐC 3 ---")
        run_react_suite(test_cases, provider)
    if mode not in {"baseline", "react", "compare"}:
        raise ValueError("APP_MODE phải là baseline, react hoặc compare.")


if __name__ == "__main__":
    main()
