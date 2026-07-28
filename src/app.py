"""Core ReAct agent integrator for the recruitment assistant.

The module keeps model access, response parsing, tool validation/execution, tracing,
and the CLI independent so each responsibility can be tested without a live API.
"""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, MutableSequence, Protocol

from dotenv import load_dotenv

if __package__:
    from .prompts import (
        GUARDRAIL_INPUT_PROMPT,
        GUARDRAIL_OUTPUT_PROMPT,
        MAX_ITERATIONS,
        REACT_SYSTEM_PROMPT,
        TIMEOUT_SECONDS,
    )
    from .providers import get_llm_provider
    from .tools import AVAILABLE_TOOLS, TOOL_SCHEMAS
else:
    from prompts import (  # type: ignore[no-redef]
        GUARDRAIL_INPUT_PROMPT,
        GUARDRAIL_OUTPUT_PROMPT,
        MAX_ITERATIONS,
        REACT_SYSTEM_PROMPT,
        TIMEOUT_SECONDS,
    )
    from providers import get_llm_provider  # type: ignore[no-redef]
    from tools import AVAILABLE_TOOLS, TOOL_SCHEMAS  # type: ignore[no-redef]

load_dotenv()

CHATBOT_BASELINE_PROMPT = """Bạn là Trợ Lý Nhân Sự Ảo. Trả lời bằng kiến thức chung và nói rõ
khi không có quyền truy cập dữ liệu CV, JD hoặc lịch phỏng vấn. Không được giả vờ đã gọi tool."""

ToolFunction = Callable[..., object]
ToolRegistry = dict[str, ToolFunction]


class ModelProvider(Protocol):
    def generate(self, prompt: str, system_prompt: str = "") -> str: ...


@dataclass(frozen=True)
class AgentResponse:
    action: str | None = None
    action_input: dict[str, Any] | None = None
    final_answer: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class ModelCallResult:
    text: str | None = None
    error: str | None = None
    attempts: int = 1


@dataclass(frozen=True)
class ToolExecutionResult:
    observation: str
    success: bool
    error_code: str | None = None


MODEL_ERROR_MARKERS = (
    "[gemini error]",
    "[gemini exception]",
    "[openai error]",
    "[openai exception]",
    "[anthropic error]",
    "[anthropic exception]",
    "[openrouter api error",
    "[openrouter exception]",
)


def build_tool_registry() -> ToolRegistry:
    """Build a validated registry from the functions defined by Role 2."""
    registry: ToolRegistry = {}
    for name, function in AVAILABLE_TOOLS.items():
        if not isinstance(name, str) or not name or not callable(function):
            raise ValueError("AVAILABLE_TOOLS contains an invalid entry")
        if name not in TOOL_SCHEMAS:
            raise ValueError(f"Tool '{name}' has no TOOL_SCHEMAS contract")
        registry[name] = function
    return registry


def load_test_cases() -> list[dict[str, Any]]:
    """Load Role 1 test cases from the repository configuration."""
    path = Path(__file__).resolve().parents[1] / "config" / "test_cases.json"
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("config/test_cases.json must contain a JSON array")
    return data


def _run_with_timeout(function: Callable[[], object], timeout_seconds: float) -> object:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(function)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise TimeoutError from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _looks_like_model_error(text: str) -> bool:
    normalized = text.strip().casefold()
    return any(normalized.startswith(marker) for marker in MODEL_ERROR_MARKERS)


def call_model(
    provider: ModelProvider,
    history: str,
    *,
    system_prompt: str = REACT_SYSTEM_PROMPT,
    timeout_seconds: float = TIMEOUT_SECONDS,
    max_retries: int = 2,
) -> ModelCallResult:
    """Call the configured model with timeout and bounded transient retries."""
    last_error = "Model did not return a response."
    attempts = max_retries + 1
    for attempt in range(1, attempts + 1):
        try:
            raw = _run_with_timeout(
                lambda: provider.generate(history, system_prompt=system_prompt),
                timeout_seconds,
            )
            if not isinstance(raw, str) or not raw.strip():
                last_error = "Model returned an empty response."
            elif _looks_like_model_error(raw):
                last_error = raw.strip()
            else:
                return ModelCallResult(text=raw.strip(), attempts=attempt)
        except TimeoutError:
            last_error = f"Model timed out after {timeout_seconds:g} seconds."
        except Exception as exc:  # provider implementations are not consistent
            last_error = f"Model call failed: {type(exc).__name__}."

        if attempt < attempts:
            time.sleep(min(0.2 * (2 ** (attempt - 1)), 1.0))

    return ModelCallResult(error=last_error, attempts=attempts)


def _extract_balanced_object(text: str, start: int) -> str | None:
    opening = text.find("{", start)
    if opening < 0:
        return None
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(opening, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[opening : index + 1]
    return None


def _parse_action_input(raw: str) -> dict[str, Any] | None:
    candidate = raw.strip()
    # prompts.py contains escaped examples ({{...}}); some models reproduce them.
    if candidate.startswith("{{") and candidate.endswith("}}"):
        candidate = candidate[1:-1].strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        try:
            value = ast.literal_eval(candidate)
        except (ValueError, SyntaxError):
            return None
    return value if isinstance(value, dict) else None


def parse_agent_response(text: str) -> AgentResponse:
    """Parse one model turn without evaluating arbitrary model-generated code."""
    if not isinstance(text, str) or not text.strip():
        return AgentResponse(error="Model output is empty.")

    final_matches = list(
        re.finditer(r"(?ims)^\s*Final Answer\s*:\s*(.+)$", text)
    )
    action_matches = list(re.finditer(r"(?im)^\s*Action\s*:\s*([A-Za-z_]\w*)\s*$", text))
    if final_matches and (
        not action_matches or final_matches[-1].start() > action_matches[-1].start()
    ):
        answer = final_matches[-1].group(1).strip()
        return AgentResponse(final_answer=answer) if answer else AgentResponse(
            error="Final Answer is empty."
        )

    if not action_matches:
        return AgentResponse(error="Model output has neither Action nor Final Answer.")

    action_match = action_matches[-1]
    input_label = re.search(
        r"(?im)^\s*Action Input\s*:\s*", text[action_match.end() :]
    )
    if not input_label:
        return AgentResponse(
            action=action_match.group(1),
            error="Action Input is missing.",
        )

    input_start = action_match.end() + input_label.end()
    raw_object = _extract_balanced_object(text, input_start)
    if raw_object is None:
        return AgentResponse(
            action=action_match.group(1),
            error="Action Input does not contain a complete JSON object.",
        )
    arguments = _parse_action_input(raw_object)
    if arguments is None:
        return AgentResponse(
            action=action_match.group(1),
            error="Action Input is not a valid JSON object.",
        )
    return AgentResponse(action=action_match.group(1), action_input=arguments)


def parse_react_output(text: str) -> dict[str, Any]:
    """Backward-compatible dictionary wrapper around parse_agent_response."""
    parsed = parse_agent_response(text)
    return {
        "thought": "",  # private chain-of-thought is deliberately not retained
        "action": parsed.action,
        "action_input": parsed.action_input,
        "final_answer": parsed.final_answer,
        "error": parsed.error,
    }


def _validate_tool_arguments(function: ToolFunction, arguments: object) -> str | None:
    if not isinstance(arguments, dict):
        return "Action Input must be a JSON object."
    signature = inspect.signature(function)
    parameters = {
        name: parameter
        for name, parameter in signature.parameters.items()
        if parameter.kind
        in (parameter.POSITIONAL_OR_KEYWORD, parameter.KEYWORD_ONLY)
    }
    required = {
        name
        for name, parameter in parameters.items()
        if parameter.default is inspect.Parameter.empty
    }
    missing = sorted(required - arguments.keys())
    unexpected = sorted(arguments.keys() - parameters.keys())
    if missing:
        return f"Missing required parameters: {', '.join(missing)}."
    if unexpected:
        return f"Unexpected parameters: {', '.join(unexpected)}."
    for name, value in arguments.items():
        annotation = parameters[name].annotation
        if annotation is str and (not isinstance(value, str) or not value.strip()):
            return f"Parameter '{name}' must be a non-empty string."
    return None


def _is_tool_error(output: str) -> bool:
    normalized = output.lstrip().casefold()
    # Supports both correct UTF-8 and the mojibake prefix present in legacy data.
    return normalized.startswith("lỗi:") or normalized.startswith("lá»")


def execute_tool(
    tool_name: str | None,
    arguments: object,
    *,
    registry: Mapping[str, ToolFunction] | None = None,
    timeout_seconds: float = TIMEOUT_SECONDS,
) -> ToolExecutionResult:
    """Validate and execute a real registered tool, returning an Observation."""
    active_registry = registry or build_tool_registry()
    if not isinstance(tool_name, str) or not tool_name.strip():
        return ToolExecutionResult("LỖI: Tên tool không hợp lệ.", False, "INVALID_TOOL")
    function = active_registry.get(tool_name)
    if function is None:
        valid = ", ".join(sorted(active_registry))
        return ToolExecutionResult(
            f"LỖI: Tool '{tool_name}' không tồn tại. Tool hợp lệ: {valid}.",
            False,
            "UNKNOWN_TOOL",
        )
    validation_error = _validate_tool_arguments(function, arguments)
    if validation_error:
        return ToolExecutionResult(
            f"LỖI: Tham số không hợp lệ cho '{tool_name}': {validation_error}",
            False,
            "INVALID_ARGUMENTS",
        )
    try:
        raw = _run_with_timeout(lambda: function(**arguments), timeout_seconds)  # type: ignore[arg-type]
    except TimeoutError:
        return ToolExecutionResult(
            f"LỖI: Tool '{tool_name}' vượt quá timeout {timeout_seconds:g} giây.",
            False,
            "TOOL_TIMEOUT",
        )
    except Exception as exc:
        return ToolExecutionResult(
            f"LỖI: Tool '{tool_name}' gặp lỗi {type(exc).__name__} khi thực thi.",
            False,
            "TOOL_EXCEPTION",
        )
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return ToolExecutionResult(
            f"LỖI: Tool '{tool_name}' trả dữ liệu rỗng.",
            False,
            "EMPTY_TOOL_OUTPUT",
        )
    observation = raw if isinstance(raw, str) else str(raw)
    return ToolExecutionResult(
        observation=observation,
        success=not _is_tool_error(observation),
        error_code="TOOL_REPORTED_ERROR" if _is_tool_error(observation) else None,
    )


def _trace_event(
    trace: MutableSequence[dict[str, Any]],
    *,
    step: int,
    event: str,
    action: str | None = None,
    observation: str | None = None,
    error: str | None = None,
) -> None:
    entry: dict[str, Any] = {"step": step, "event": event}
    if action:
        entry["decision_summary"] = f"Model selected registered action '{action}'."
        entry["action"] = action
    if observation is not None:
        entry["observation"] = observation
    if error:
        entry["error"] = error
    trace.append(entry)


def run_react_agent(
    user_query: str,
    provider: ModelProvider | None = None,
    *,
    verbose: bool = True,
    registry: Mapping[str, ToolFunction] | None = None,
    trace_sink: MutableSequence[dict[str, Any]] | None = None,
    max_iterations: int = MAX_ITERATIONS,
) -> str:
    """Run a bounded multi-tool ReAct loop and return a user-facing answer."""
    if not isinstance(user_query, str) or not user_query.strip():
        return "LỖI: Yêu cầu người dùng không được để trống."
    if max_iterations < 1:
        return "LỖI: MAX_ITERATIONS phải lớn hơn 0."

    model = provider or get_llm_provider()
    active_registry = dict(registry or build_tool_registry())
    trace = trace_sink if trace_sink is not None else []
    history = f"[Yêu cầu người dùng]\n{user_query.strip()}\n"
    action_counts: dict[str, int] = {}
    action_count = 0
    format_failures = 0
    model_turn = 0
    max_model_turns = max_iterations + 3

    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query.strip()}")

    while model_turn < max_model_turns and action_count < max_iterations:
        model_turn += 1
        if verbose:
            print(f"\n--- 🔄 Lượt Model {model_turn} | Tool {action_count}/{max_iterations} ---")
        model_result = call_model(model, history)
        if model_result.error:
            message = (
                "Không thể kết nối mô hình sau "
                f"{model_result.attempts} lần thử: {model_result.error}"
            )
            _trace_event(trace, step=model_turn, event="model_error", error=message)
            if verbose:
                print(f"⚠️ {message}")
            return message

        parsed = parse_agent_response(model_result.text or "")
        if parsed.final_answer:
            _trace_event(trace, step=model_turn, event="final_answer")
            if verbose:
                print(f"🏁 Final Answer: {parsed.final_answer}")
            return parsed.final_answer

        if parsed.error or not parsed.action or parsed.action_input is None:
            format_failures += 1
            error = parsed.error or "Model output format is invalid."
            _trace_event(trace, step=model_turn, event="format_error", error=error)
            if verbose:
                print(f"⚠️ Output model sai định dạng: {error}")
            if format_failures >= 2:
                return "Không thể xử lý phản hồi của mô hình vì sai định dạng hai lần liên tiếp."
            history += (
                "\n[System feedback] Phản hồi trước sai định dạng. "
                "Hãy trả đúng Action + Action Input JSON hoặc Final Answer.\n"
            )
            continue

        format_failures = 0
        canonical_args = json.dumps(parsed.action_input, ensure_ascii=False, sort_keys=True)
        action_key = f"{parsed.action}:{canonical_args}"
        action_counts[action_key] = action_counts.get(action_key, 0) + 1
        if action_counts[action_key] > 2:
            message = f"Dừng an toàn: action '{parsed.action}' với cùng tham số bị lặp quá 2 lần."
            _trace_event(
                trace,
                step=model_turn,
                event="repeated_action",
                action=parsed.action,
                error=message,
            )
            return message

        result = execute_tool(
            parsed.action,
            parsed.action_input,
            registry=active_registry,
        )
        action_count += 1
        _trace_event(
            trace,
            step=model_turn,
            event="tool_call",
            action=parsed.action,
            observation=result.observation,
            error=result.error_code,
        )
        if verbose:
            print(f"🛠️ Action: {parsed.action}")
            print(f"📥 Action Input: {canonical_args}")
            print(f"👁️ Observation: {result.observation}")

        # Full interaction history is provided back to the model. Raw Thought text is
        # not copied into the application trace.
        history += (
            f"\nAction: {parsed.action}\n"
            f"Action Input: {canonical_args}\n"
            f"Observation: {result.observation}\n"
        )

    # MAX_ITERATIONS limits tool calls. One final, tool-free model turn is allowed
    # to summarize the last Observation, which is required by three-tool cases.
    history += (
        "\n[System feedback] Đã đạt giới hạn gọi tool. "
        "Không gọi thêm tool; hãy trả Final Answer dựa trên các Observation.\n"
    )
    final_result = call_model(model, history)
    if final_result.error:
        message = f"Đã đạt MAX_ITERATIONS và không thể tạo câu trả lời cuối: {final_result.error}"
        _trace_event(trace, step=model_turn + 1, event="model_error", error=message)
        return message
    final_parsed = parse_agent_response(final_result.text or "")
    if final_parsed.final_answer:
        _trace_event(trace, step=model_turn + 1, event="final_answer")
        if verbose:
            print(f"🏁 Final Answer: {final_parsed.final_answer}")
        return final_parsed.final_answer
    message = (
        f"GUARDRAIL: Đã đạt giới hạn {max_iterations} lần gọi tool "
        "nhưng mô hình chưa trả Final Answer hợp lệ."
    )
    _trace_event(trace, step=model_turn + 1, event="max_iterations", error=message)
    return message


def _parse_guardrail_json(text: str) -> dict[str, Any] | None:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def run_input_guardrail(user_query: str, provider: ModelProvider) -> dict[str, Any] | None:
    result = call_model(
        provider,
        GUARDRAIL_INPUT_PROMPT.format(user_input=user_query),
        system_prompt="",
    )
    if result.error:
        return None
    parsed = _parse_guardrail_json(result.text or "")
    return parsed if parsed and not parsed.get("is_safe", True) else None


def run_output_guardrail(agent_response: str, provider: ModelProvider) -> str:
    result = call_model(
        provider,
        GUARDRAIL_OUTPUT_PROMPT.format(agent_response=agent_response),
        system_prompt="",
    )
    if result.error:
        return agent_response
    parsed = _parse_guardrail_json(result.text or "")
    if not parsed:
        return agent_response
    modified = parsed.get("modified_response")
    return modified if isinstance(modified, str) and modified.strip() else agent_response


def run_baseline_chatbot(user_query: str, provider: ModelProvider) -> str:
    result = call_model(provider, user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    response = result.text or f"Không thể gọi mô hình: {result.error}"
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_test_cases(provider: ModelProvider, *, verbose: bool = True) -> list[dict[str, Any]]:
    """Run configured cases and report observed versus expected tool usage."""
    results: list[dict[str, Any]] = []
    for case in load_test_cases():
        trace: list[dict[str, Any]] = []
        answer = run_react_agent(
            case["question"],
            provider,
            verbose=verbose,
            trace_sink=trace,
        )
        observed = [event["action"] for event in trace if event.get("action")]
        expected = case.get("expected_tools", [])
        forbidden = case.get("forbidden_tools", [])
        passed = all(name in observed for name in expected) and not any(
            name in observed for name in forbidden
        )
        record = {
            "id": case.get("id"),
            "category": case.get("category"),
            "passed": passed,
            "expected_tools": expected,
            "observed_tools": observed,
            "answer": answer,
        }
        results.append(record)
        print(
            f"Test #{record['id']}: {'PASS' if passed else 'FAIL'} | "
            f"expected={expected} observed={observed}"
        )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Recruitment ReAct Agent")
    parser.add_argument("--test", action="store_true", help="run config test cases")
    parser.add_argument("--query", help="run one query and exit")
    args = parser.parse_args(argv)

    try:
        registry = build_tool_registry()
    except ValueError as exc:
        print(f"Lỗi cấu hình tool: {exc}")
        return 2
    provider = get_llm_provider()
    print("=" * 58)
    print("AI RECRUITMENT AGENT — Sàng lọc CV & phỏng vấn")
    print("=" * 58)
    print(f"Provider: {provider.__class__.__name__}; tools: {', '.join(registry)}")

    if args.test:
        results = run_test_cases(provider)
        return 0 if all(item["passed"] for item in results) else 1
    if args.query:
        print(run_react_agent(args.query, provider, registry=registry))
        return 0

    print("Nhập 'quit' để thoát.")
    while True:
        try:
            user_input = input("\n👤 Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            return 0
        if user_input.casefold() in {"quit", "exit", "q"}:
            print("Tạm biệt!")
            return 0
        if not user_input:
            continue
        violation = run_input_guardrail(user_input, provider)
        if violation:
            print(violation.get("safe_response", "Yêu cầu không hợp lệ."))
            continue
        answer = run_react_agent(user_input, provider, registry=registry)
        print(f"\n📤 {run_output_guardrail(answer, provider)}")


if __name__ == "__main__":
    raise SystemExit(main())