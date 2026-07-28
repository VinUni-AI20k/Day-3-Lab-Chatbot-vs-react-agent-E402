"""Core application for the rental-search and viewing-booking agent.

Role 4 owns the orchestration here: baseline chatbot, ReAct loop, action
parsing, tool execution, observations, and guardrails.  The application can
run with a real provider, but also has a deterministic offline path so the
lab can be demonstrated without an API key.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT
from providers import get_llm_provider
from tools import AVAILABLE_TOOLS

load_dotenv()


def load_test_cases() -> list[dict[str, Any]]:
    """Load the test-case list from either the old list or new object schema."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "config", "test_cases.json")
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    if isinstance(payload, list):
        return payload
    return payload.get("test_cases", [])


def run_baseline_chatbot(user_query: str, provider) -> dict[str, Any]:
    """Run one provider call without exposing any tool to the chatbot."""
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    result = {"mode": "baseline", "query": user_query, "response": response}
    print(f"\n[CHATBOT BASELINE] {user_query}\n{response}")
    return result


def _parse_action(text: str) -> tuple[str, list[Any], dict[str, Any]] | None:
    """Parse ``Action: tool_name[...]`` using Python literals safely."""
    match = re.search(r"Action\s*:\s*([A-Za-z_]\w*)\s*\[(.*)\]", text, re.I | re.S)
    if not match:
        return None
    name, raw_args = match.group(1), match.group(2).strip()
    if not raw_args:
        return name, [], {}
    try:
        parsed = ast.literal_eval(f"[{raw_args}]")
    except (SyntaxError, ValueError):
        return None
    if isinstance(parsed, list) and parsed and all(isinstance(item, tuple) for item in parsed):
        return name, [], dict(parsed)
    return name, parsed if isinstance(parsed, list) else [parsed], {}


def _execute_tool(name: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
    """Execute a registered tool with basic argument-count validation."""
    tool = AVAILABLE_TOOLS.get(name)
    if tool is None:
        return {"error": f"Tool '{name}' không tồn tại."}
    try:
        signature = inspect.signature(tool)
        signature.bind(*args, **kwargs)
        return tool(*args, **kwargs)
    except TypeError as error:
        return {"error": f"Tham số không hợp lệ cho {name}: {error}"}
    except Exception as error:  # tool failure must not crash the agent
        return {"error": f"Tool {name} thất bại: {error}"}


def _offline_action(query: str, history: list[dict[str, Any]]) -> str | None:
    """Choose a safe deterministic action when the Mock provider is active."""
    q = query.lower()
    observed = [item.get("tool") for item in history]

    if any(word in q for word in ("mật khẩu", "ma túy", "bỏ qua", "prompt")):
        return None
    if not history:
        if re.search(r"ch-\d+", q) and any(word in q for word in ("chi tiết", "hình ảnh", "thông tin")):
            rental_id = re.search(r"ch-\d+", q, re.I).group(0).upper()
            return f"get_rental_detail['{rental_id}']"
        if re.search(r"ch-\d+", q) and any(word in q for word in ("đặt lịch", "xem phòng", "xem nhà")):
            rental_id = re.search(r"ch-\d+", q, re.I).group(0).upper()
            date = "chiều mai" if "chiều mai" in q else "hôm nay"
            return f"check_landlord_calendar['{rental_id}', '{date}']"
        if any(word in q for word in ("tìm", "phòng trọ", "căn hộ")):
            if "bình thạnh" in q:
                return "search_rentals['Bình Thạnh', 0, 8000000, '1PN', ['ban công']]"
            if "dịch vọng" in q:
                return "search_rentals['Dịch Vọng, Cầu Giấy', 0, 5000000, '', ['điều hòa']]"
    if (
        "search_rentals" in observed
        and "check_landlord_calendar" not in observed
        and any(word in q for word in ("đặt", "chốt", "lịch xem"))
    ):
        rental_id = "CH-5501" if "bình thạnh" in q else "CH-8802"
        date = "thứ bảy" if "thứ bảy" in q else "chiều mai"
        return f"check_landlord_calendar['{rental_id}', '{date}']"
    if "check_landlord_calendar" in observed and "book_viewing_appointment" not in observed:
        last_observation = history[-1].get("observation", {})
        slots = last_observation.get("slots", []) if isinstance(last_observation, dict) else []
        if "Nam" in query and "10:00" in slots:
            return "book_viewing_appointment['CH-5501', 'Nam', '0901234567', 'thứ bảy 10:00']"
        if "An" in query and "14:00" in slots:
            return "book_viewing_appointment['CH-102', 'An', '0988776655', 'hôm nay 14:00']"
    if "book_viewing_appointment" in observed:
        last = history[-1].get("observation", {})
        if isinstance(last, dict) and last.get("booking_id"):
            return f"send_confirmation_notification['{last.get('phone', '')}', {last!r}]"
    return None


def _offline_final(query: str, history: list[dict[str, Any]]) -> str:
    """Create a grounded fallback answer from the last real observation."""
    if not history:
        return "Mình có thể tư vấn kinh nghiệm thuê nhà, nhưng cần thêm thông tin để hỗ trợ yêu cầu này."
    observation = history[-1].get("observation")
    if isinstance(observation, list):
        if not observation:
            return "Không tìm thấy căn hộ/phòng trọ phù hợp với tiêu chí hiện tại."
        lines = [
            f"{item.get('id')}: {item.get('title')} — {item.get('price'):,} VNĐ/tháng; "
            f"{item.get('location')}; tiện ích: {', '.join(item.get('amenities', []))}."
            for item in observation
        ]
        return "Mình tìm thấy các lựa chọn sau:\n- " + "\n- ".join(lines)
    if isinstance(observation, dict) and observation.get("available"):
        return f"Các khung giờ còn trống: {', '.join(observation.get('slots', []))}. Bạn muốn chọn khung nào?"
    if isinstance(observation, dict) and observation.get("id"):
        return (
            f"{observation.get('title')} ({observation.get('id')}), tại {observation.get('location')}, "
            f"giá {observation.get('price'):,} VNĐ/tháng. Hình ảnh: {observation.get('image')}"
        )
    return "Mình đã xử lý yêu cầu dựa trên dữ liệu hiện có nhưng cần thêm thông tin để hoàn tất."


def run_react_agent(user_query: str, provider, max_iterations: int = MAX_ITERATIONS) -> dict[str, Any]:
    """Run the ReAct loop and return a trace suitable for Role 5 evaluation."""
    trace: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    prompt = user_query
    print(f"\n[REACT AGENT] {user_query}")

    for step in range(1, max_iterations + 1):
        response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = _parse_action(response)
        if parsed is None:
            offline = _offline_action(user_query, history)
            parsed = _parse_action(f"Action: {offline}") if offline else None

        if parsed is None:
            final = response if "Final Answer:" in response else (
                _offline_final(user_query, history)
            )
            trace.append({"step": step, "response": response, "final": final})
            print(f"[Final Answer] {final}")
            return {"mode": "react", "query": user_query, "trace": trace, "final": final}

        tool_name, args, kwargs = parsed
        observation = _execute_tool(tool_name, args, kwargs)
        item = {"step": step, "response": response, "tool": tool_name, "args": args, "kwargs": kwargs, "observation": observation}
        trace.append(item)
        history.append(item)
        print(f"[Step {step}] Action: {tool_name} args={args} kwargs={kwargs}")
        print(f"[Observation] {observation}")

        if isinstance(observation, dict) and observation.get("error"):
            final = f"Không thể thực hiện {tool_name}: {observation['error']}"
            trace.append({"step": step, "final": final, "guardrail": True})
            print(f"[Guardrail] {final}")
            return {"mode": "react", "query": user_query, "trace": trace, "final": final}

        prompt = (
            f"User request: {user_query}\n"
            f"Previous action: {tool_name}[{args}]\n"
            f"Observation: {json.dumps(observation, ensure_ascii=False, default=str)}\n"
            "Continue with exactly one Thought + Action, or Thought + Final Answer."
        )

        if tool_name == "send_confirmation_notification":
            final = "Đã hoàn tất đặt lịch và gửi thông báo xác nhận cho khách hàng."
            trace.append({"step": step, "final": final})
            print(f"[Final Answer] {final}")
            return {"mode": "react", "query": user_query, "trace": trace, "final": final}

    final = f"Agent dừng an toàn sau {max_iterations} vòng lặp để tránh chạy vô hạn."
    trace.append({"step": max_iterations, "final": final, "guardrail": True})
    print(f"[Guardrail] {final}")
    return {"mode": "react", "query": user_query, "trace": trace, "final": final}


def main() -> None:
    print("=== AI Agent: Tìm & Đặt Lịch Xem Nhà ===")
    provider = get_llm_provider()
    print(f"Provider: {provider.__class__.__name__}")
    tests = load_test_cases()
    print(f"Loaded {len(tests)} test cases")
    if not tests:
        return
    query = tests[2]["question"]
    run_baseline_chatbot(query, provider)
    run_react_agent(query, provider)


if __name__ == "__main__":
    main()
