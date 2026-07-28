"""Core ReAct loop owned by Role 4.

The core is intentionally independent from a specific LLM provider or tool
domain. Role 2 supplies the registry and Role 3 supplies the system prompt.
"""

import csv
import re
from collections.abc import Callable, Mapping
from typing import Any


ACTION_PATTERN = re.compile(
    r"^Action:\s*(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\[(?P<arguments>.*)\]\s*$",
    re.MULTILINE,
)
FINAL_ANSWER_PATTERN = re.compile(r"^Final Answer:\s*(?P<answer>.+)$", re.MULTILINE | re.DOTALL)
THOUGHT_PATTERN = re.compile(r"^Thought:\s*(?P<thought>.+)$", re.MULTILINE)


def parse_agent_response(response: str) -> dict[str, Any]:
    """Parse one LLM response without evaluating model-generated content."""
    final_match = FINAL_ANSWER_PATTERN.search(response)
    if final_match:
        return {"kind": "final", "answer": final_match.group("answer").strip()}

    action_match = ACTION_PATTERN.search(response)
    if action_match:
        raw_arguments = action_match.group("arguments").strip()
        try:
            arguments = next(csv.reader([raw_arguments], skipinitialspace=True)) if raw_arguments else []
        except csv.Error:
            return {"kind": "error", "message": "LỖI: Action có danh sách tham số không hợp lệ."}

        cleaned_arguments = [argument.strip().strip("'\"") for argument in arguments]
        return {
            "kind": "action",
            "name": action_match.group("name"),
            "arguments": cleaned_arguments,
        }

    return {
        "kind": "error",
        "message": "LỖI: Không đọc được Action hoặc Final Answer theo đúng định dạng ReAct.",
    }


def _extract_thought(response: str) -> str:
    match = THOUGHT_PATTERN.search(response)
    return match.group("thought").strip() if match else ""


def execute_tool(
    tool_name: str,
    arguments: list[str],
    tools: Mapping[str, Callable[..., str]],
) -> str:
    """Execute only a registered tool and convert runtime errors to observations."""
    tool = tools.get(tool_name)
    if tool is None:
        valid_tools = ", ".join(sorted(tools))
        return f"LỖI: Tool '{tool_name}' không tồn tại. Tool hợp lệ: {valid_tools}."

    try:
        result = tool(*arguments)
    except TypeError:
        return f"LỖI: Tham số không hợp lệ cho tool '{tool_name}'."
    except Exception as error:
        return f"LỖI: Tool '{tool_name}' gặp lỗi: {error}"

    return str(result)


def _build_user_context(user_query: str, trace: list[dict[str, Any]]) -> str:
    """Return the user query plus real observations for the next LLM turn."""
    context = [f"Câu hỏi người dùng: {user_query}"]
    for item in trace:
        if item.get("kind") != "action":
            continue
        context.extend(
            [
                "",
                f"Thought trước đó: {item.get('thought', '')}",
                f"Action đã thực hiện: {item['name']}[{', '.join(item['arguments'])}]",
                f"Observation: {item['observation']}",
            ]
        )
    return "\n".join(context)


def run_react_agent(
    user_query: str,
    provider: Any,
    tools: Mapping[str, Callable[..., str]],
    system_prompt: str,
    max_iterations: int,
) -> dict[str, Any]:
    """Run Thought -> Action -> Observation until Final Answer or guardrail.

    Returns a structured trace that Role 4 can print and Role 5 can store in
    docs/trace_eval.md.
    """
    trace: list[dict[str, Any]] = []
    seen_actions: set[tuple[str, tuple[str, ...]]] = set()

    for step in range(1, max_iterations + 1):
        context = _build_user_context(user_query, trace)
        response = str(provider.generate(context, system_prompt=system_prompt)).strip()
        parsed = parse_agent_response(response)

        if parsed["kind"] == "final":
            return {
                "answer": parsed["answer"],
                "termination_reason": "final_answer",
                "tool_calls": sum(item.get("kind") == "action" for item in trace),
                "trace": trace,
            }

        if parsed["kind"] == "error":
            trace.append(
                {
                    "step": step,
                    "kind": "action",
                    "thought": _extract_thought(response),
                    "name": "parse_error",
                    "arguments": [],
                    "observation": parsed["message"],
                    "raw_response": response,
                }
            )
            continue

        action_key = (parsed["name"], tuple(parsed["arguments"]))
        if action_key in seen_actions:
            observation = (
                "LỖI: Agent đang lặp lại đúng Action đã thực hiện. "
                "Hãy dùng Observation trước đó để chọn bước khác hoặc trả lời an toàn."
            )
        else:
            seen_actions.add(action_key)
            observation = execute_tool(parsed["name"], parsed["arguments"], tools)

        trace.append(
            {
                "step": step,
                "kind": "action",
                "thought": _extract_thought(response),
                "name": parsed["name"],
                "arguments": parsed["arguments"],
                "observation": observation,
                "raw_response": response,
            }
        )

    return {
        "answer": (
            "Tôi chưa thể hoàn thành yêu cầu một cách đáng tin cậy trong giới hạn xử lý. "
            "Vui lòng kiểm tra lại thông tin hoặc thử lại với yêu cầu cụ thể hơn."
        ),
        "termination_reason": "max_iterations",
        "tool_calls": sum(item.get("kind") == "action" for item in trace),
        "trace": trace,
    }
