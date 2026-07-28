"""Application entry point for the baseline chatbot and the ReAct gift agent."""

import ast
import json
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, get_weather, search_flights
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases() -> list[dict[str, Any]]:
    """Load the lab test cases regardless of the current working directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base_dir, "config", "test_cases.json"), encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(user_query: str, provider: Any) -> str:
    """Run the no-tool baseline chatbot and return its answer."""
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"\n[CHATBOT BASELINE]\n{response}")
    return response


def _tool_instructions() -> str:
    """Expose the current tool contract to the model instead of duplicating it here."""
    return (
        "Available tools (use only these names and JSON-object arguments):\n"
        f"{json.dumps(TOOL_SPECS, ensure_ascii=False)}\n\n"
        "For a tool call, respond exactly as:\n"
        "Thought: <brief reason>\n"
        'Action: <tool_name>{"argument": "value"}\n'
        "After an Observation, either call the next tool or respond with "
        "`Final Answer: <answer>` ."
    )


def _parse_action(response: str) -> tuple[str, dict[str, Any]] | None:
    """Parse ``Action: tool{json}`` (and the legacy ``tool[args]`` form)."""
    match = re.search(r"^Action:\s*([A-Za-z_]\w*)\s*(.*)$", response, re.MULTILINE)
    if not match:
        return None

    name, raw_arguments = match.groups()
    raw_arguments = raw_arguments.strip()
    if raw_arguments.startswith("{"):
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return None
        return (name, arguments) if isinstance(arguments, dict) else None

    # Accept the prompt's old ``tool[value]`` style only for one positional input.
    if raw_arguments.startswith("[") and raw_arguments.endswith("]"):
        try:
            values = ast.literal_eval(raw_arguments)
        except (SyntaxError, ValueError):
            return None
        if not isinstance(values, (list, tuple)) or len(values) != 1:
            return None
        parameter_names = {
            "extract_recipient_profile": "user_description",
            "analyze_recipient_profile": "recipient_profile",
        }
        parameter = parameter_names.get(name)
        return (name, {parameter: values[0]}) if parameter else None
    return None


def _execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call a registered tool without allowing arbitrary function execution."""
    tool = AVAILABLE_TOOLS.get(name)
    if tool is None:
        return {"error": f"Unknown tool: {name}. Available tools: {', '.join(AVAILABLE_TOOLS)}"}
    try:
        result = tool(**arguments)
        return result if isinstance(result, dict) else {"result": result}
    except (TypeError, ValueError) as error:
        return {"error": f"Invalid arguments for {name}: {error}"}
    except Exception as error:  # Keep a tool failure from crashing the agent loop.
        return {"error": f"{name} failed: {error}"}


def run_react_agent(user_query: str, provider: Any) -> str:
    """Run a bounded ReAct loop against the current gift-recommendation tool registry."""
    system_prompt = f"{REACT_SYSTEM_PROMPT}\n\n{_tool_instructions()}"
    conversation = user_query

    for step in range(1, MAX_ITERATIONS + 1):
        response = provider.generate(conversation, system_prompt=system_prompt).strip()
        print(f"\n--- ReAct step {step}/{MAX_ITERATIONS} ---\n{response}")

        if re.search(r"^Final Answer:\s*", response, re.MULTILINE):
            return response

        action = _parse_action(response)
        if action is None:
            # A normal answer without an Action is still useful; do not invent a tool call.
            return response

        name, arguments = action
        observation = _execute_tool(name, arguments)
        observation_json = json.dumps(observation, ensure_ascii=False)
        print(f"Observation: {observation_json}")
        conversation = (
            f"Original user request:\n{user_query}\n\n"
            f"Previous assistant response:\n{response}\n\n"
            f"Observation from {name}:\n{observation_json}\n\n"
            "Continue using the required ReAct format."
        )

    answer = (
        "Final Answer: Tôi đã đạt giới hạn an toàn về số bước xử lý. "
        "Vui lòng cung cấp thêm thông tin hoặc thử lại với yêu cầu cụ thể hơn."
    )
    print(answer)
    return answer


if __name__ == "__main__":
    provider = get_llm_provider()
    tests = load_test_cases()
    sample_query = tests[3]["question"]

    print(f"LLM provider: {provider.__class__.__name__}")
    print(f"Loaded {len(tests)} test cases")
    run_baseline_chatbot(sample_query, provider)
    run_react_agent(sample_query, provider)
