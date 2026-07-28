"""
🚀 CORE AGENT APP — Real ReAct Agent Loop + Workflow Integration

Modes:
    1. Interactive CLI: ``python -m src.app``
    2. Batch test runner: ``python -m src.app --test``
    3. Workflow demo: ``python -m src.app --workflow``

The ReAct agent uses the LLM to generate Thought → Action → Action Input,
dispatches tool calls dynamically, and feeds Observations back into context.
"""

import json
import os
import re
import sys
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
from tools import AVAILABLE_TOOLS, TOOL_SCHEMAS
from prompts import (
    REACT_SYSTEM_PROMPT,
    GUARDRAIL_INPUT_PROMPT,
    GUARDRAIL_OUTPUT_PROMPT,
)

# Chatbot baseline prompt (not part of prompts.py — defined here for the baseline demo)
CHATBOT_BASELINE_PROMPT = """Bạn là Trợ Lý Nhân Sự Ảo. Hãy trả lời câu hỏi của người dùng
về quy trình tuyển dụng bằng kiến thức chung của bạn. Bạn KHÔNG có quyền truy cập vào
hệ thống tra cứu CV, JD hay lịch phỏng vấn. Nếu người dùng hỏi thông tin cụ thể về
ứng viên hoặc vị trí, hãy thông báo rằng bạn không có truy cập dữ liệu thực tế."""
from providers import get_llm_provider

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_ITERATIONS = 8  # Guardrail: giới hạn số vòng lặp ReAct


# ---------------------------------------------------------------------------
# Test case loader
# ---------------------------------------------------------------------------
def load_test_cases() -> list[dict]:
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# ReAct output parser
# ---------------------------------------------------------------------------
def parse_react_output(text: str) -> dict:
    """Parse LLM output to extract Thought, Action, Action Input, or Final Answer.

    Returns a dict with keys:
        - ``thought``: the reasoning text (may be empty)
        - ``action``: tool name (None if Final Answer)
        - ``action_input``: dict of tool arguments (None if Final Answer)
        - ``final_answer``: the final response text (None if not final)
    """
    result = {
        "thought": "",
        "action": None,
        "action_input": None,
        "final_answer": None,
    }

    # Extract Thought
    thought_match = re.search(r"Thought\s*:\s*(.+?)(?=\nAction\s*:|$)", text, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    # Check for Final Answer
    final_match = re.search(r"Final Answer\s*:\s*(.+)", text, re.DOTALL)
    if final_match:
        # If there's also an Action in the text, only use Final Answer
        # if it appears AFTER the last Action block
        action_check = re.search(r"Action\s*:\s*\w+", text)
        if not action_check or text.rfind("Final Answer") > text.rfind("Action"):
            result["final_answer"] = final_match.group(1).strip()
            return result

    # Extract Action
    action_match = re.search(r"Action\s*:\s*(\w+)", text)
    if action_match:
        result["action"] = action_match.group(1).strip()

    # Extract Action Input (JSON)
    input_match = re.search(r"Action Input\s*:\s*(\{.*?\})", text, re.DOTALL)
    if input_match:
        try:
            result["action_input"] = json.loads(input_match.group(1))
        except json.JSONDecodeError:
            # Try to fix common LLM JSON errors (single quotes)
            raw = input_match.group(1).replace("'", '"')
            try:
                result["action_input"] = json.loads(raw)
            except json.JSONDecodeError:
                result["action_input"] = None

    return result


# ---------------------------------------------------------------------------
# Input Guardrail
# ---------------------------------------------------------------------------
def run_input_guardrail(user_query: str, provider) -> dict | None:
    """Check user input for safety violations. Returns None if safe, dict if blocked."""
    prompt = GUARDRAIL_INPUT_PROMPT.format(user_input=user_query)
    response = provider.generate(prompt)

    # Try to parse the guardrail JSON response
    try:
        # Strip markdown code fences if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
            cleaned = cleaned.rstrip("`").strip()
        guardrail_result = json.loads(cleaned)
        if not guardrail_result.get("is_safe", True):
            return guardrail_result
    except (json.JSONDecodeError, KeyError):
        pass  # If guardrail fails to parse, allow through
    return None


# ---------------------------------------------------------------------------
# Output Guardrail
# ---------------------------------------------------------------------------
def run_output_guardrail(agent_response: str, provider) -> str:
    """Sanitize agent output before showing to user."""
    prompt = GUARDRAIL_OUTPUT_PROMPT.format(agent_response=agent_response)
    response = provider.generate(prompt)

    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"```(?:json)?\s*", "", cleaned)
            cleaned = cleaned.rstrip("`").strip()
        result = json.loads(cleaned)
        return result.get("modified_response", agent_response)
    except (json.JSONDecodeError, KeyError):
        return agent_response


# ---------------------------------------------------------------------------
# Baseline Chatbot
# ---------------------------------------------------------------------------
def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


# ---------------------------------------------------------------------------
# ReAct Agent Loop (REAL IMPLEMENTATION)
# ---------------------------------------------------------------------------
def run_react_agent(user_query: str, provider, *, verbose: bool = True) -> str:
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    Gọi Tool thực từ AVAILABLE_TOOLS dựa trên LLM output.
    """
    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    # Build conversation context
    conversation = f"[Yêu cầu người dùng]\n{user_query}\n"
    trace_log: list[dict] = []

    for step in range(1, MAX_ITERATIONS + 1):
        if verbose:
            print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        # Call LLM with the system prompt + accumulated conversation
        llm_response = provider.generate(conversation, system_prompt=REACT_SYSTEM_PROMPT)

        if verbose:
            print(f"📝 LLM Output:\n{llm_response}")

        # Parse the LLM output
        parsed = parse_react_output(llm_response)
        trace_entry = {"step": step, **parsed}

        if parsed["thought"]:
            if verbose:
                print(f"🧠 Thought: {parsed['thought']}")

        # Check for Final Answer
        if parsed["final_answer"]:
            if verbose:
                print(f"🏁 Final Answer: {parsed['final_answer']}")
            trace_entry["type"] = "final_answer"
            trace_log.append(trace_entry)
            return parsed["final_answer"]

        # Execute Action
        if parsed["action"]:
            tool_name = parsed["action"]
            tool_args = parsed["action_input"] or {}

            if tool_name not in AVAILABLE_TOOLS:
                observation = f"LỖI: Công cụ '{tool_name}' không tồn tại. Các công cụ có sẵn: {', '.join(AVAILABLE_TOOLS.keys())}."
                if verbose:
                    print(f"❌ Tool không tồn tại: {tool_name}")
            else:
                if verbose:
                    print(f"🛠️ Action: {tool_name}")
                    print(f"📥 Action Input: {json.dumps(tool_args, ensure_ascii=False)}")

                try:
                    tool_fn = AVAILABLE_TOOLS[tool_name]
                    observation = tool_fn(**tool_args)
                except TypeError as e:
                    observation = f"LỖI: Tham số không hợp lệ cho '{tool_name}': {e}"
                except Exception as e:
                    observation = f"LỖI: Lỗi khi gọi '{tool_name}': {e}"

            if verbose:
                print(f"👁️ Observation: {observation}")

            trace_entry["observation"] = observation
            trace_entry["type"] = "tool_call"
            trace_log.append(trace_entry)

            # Append observation to conversation for next iteration
            conversation += f"\n{llm_response}\nObservation: {observation}\n"
        else:
            # LLM didn't produce a valid Action or Final Answer
            if verbose:
                print("⚠️ LLM không sinh ra Action hoặc Final Answer hợp lệ.")
            conversation += f"\n{llm_response}\n"
            conversation += "\nHãy tiếp tục với Thought, Action, Action Input hoặc Final Answer.\n"
            trace_entry["type"] = "unparseable"
            trace_log.append(trace_entry)

    # Guardrail: max iterations reached
    guardrail_msg = f"🛡️ GUARDRAIL: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Xin lỗi, tôi không thể hoàn thành yêu cầu trong số bước cho phép."
    if verbose:
        print(guardrail_msg)
    return guardrail_msg


# ---------------------------------------------------------------------------
# Workflow demo
# ---------------------------------------------------------------------------
def run_workflow_demo():
    """Run the structured workflow engine (non-LLM, deterministic)."""
    from recruitment.workflow import RecruitmentWorkflow
    from recruitment.models import RecruitmentRunRequest
    from recruitment.tracing import export_trace_markdown, setup_logging

    setup_logging(json_output=False)

    print("\n" + "=" * 60)
    print("📋 WORKFLOW DEMO — Deterministic State Machine")
    print("=" * 60)

    # Test case 1: PASS
    print("\n--- Test 1: Ứng viên ĐẠT (candidate_001 → python_backend) ---")
    request = RecruitmentRunRequest(
        candidate_id="candidate_001",
        job_id="python_backend",
        interviewer_id="interviewer_001",
        interview_date="2026-08-01",
    )
    wf = RecruitmentWorkflow(max_retries=1)
    state = wf.run(request)
    print(f"✅ Decision: {state.decision}")
    print(f"📊 Score: {state.matching.total_score if state.matching else 'N/A'}")
    print(f"📧 Email:\n{state.email_draft}")
    print(f"\n{export_trace_markdown(state)}")

    # Test case 2: REJECT
    print("\n--- Test 2: Ứng viên KHÔNG ĐẠT (candidate_002 → python_backend) ---")
    request2 = RecruitmentRunRequest(
        candidate_id="candidate_002",
        job_id="python_backend",
        interviewer_id="interviewer_001",
        interview_date="2026-08-01",
    )
    state2 = wf.run(request2)
    print(f"❌ Decision: {state2.decision}")
    print(f"📊 Score: {state2.matching.total_score if state2.matching else 'N/A'}")
    print(f"📧 Email:\n{state2.email_draft}")
    print(f"\n{export_trace_markdown(state2)}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("==================================================")
    print("🏫 AI RECRUITMENT AGENT — Sàng lọc CV & Điều phối phỏng vấn")
    print("==================================================")

    # Parse CLI arguments
    args = sys.argv[1:]

    if "--workflow" in args:
        run_workflow_demo()
        sys.exit(0)

    # Khởi tạo Multi-Provider LLM Adapter
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    if "--test" in args:
        # Batch test mode: run all test cases
        tests = load_test_cases()
        print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json\n")

        for tc in tests:
            print(f"\n{'='*60}")
            print(f"📝 Test #{tc['id']} [{tc['category']}]")
            print(f"❓ Câu hỏi: {tc['question']}")
            print(f"🎯 Expected tools: {tc.get('expected_tools', [])}")
            print(f"{'='*60}")

            print("\n--- CHATBOT BASELINE ---")
            run_baseline_chatbot(tc["question"], provider)

            print("\n--- REACT AGENT ---")
            result = run_react_agent(tc["question"], provider)

    else:
        # Interactive mode
        print("\n💡 Chế độ tương tác. Gõ 'quit' để thoát.")
        print("💡 Gõ 'workflow' để chạy demo workflow.\n")

        while True:
            try:
                user_input = input("👤 Bạn: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Tạm biệt!")
                break

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("👋 Tạm biệt!")
                break
            if user_input.lower() == "workflow":
                run_workflow_demo()
                continue

            # Input Guardrail
            violation = run_input_guardrail(user_input, provider)
            if violation:
                print(f"🛡️ [INPUT GUARDRAIL] Bị chặn: {violation.get('reason', 'N/A')}")
                print(f"📝 {violation.get('safe_response', 'Yêu cầu không hợp lệ.')}")
                continue

            # Run ReAct Agent
            final_answer = run_react_agent(user_input, provider)

            # Output Guardrail
            sanitized = run_output_guardrail(final_answer, provider)
            print(f"\n📤 [FINAL OUTPUT] {sanitized}")
