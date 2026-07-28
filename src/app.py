"""Role 4 application entry point for the Chatbot Baseline and ReAct Agent."""

import json
import os
import sys

from dotenv import load_dotenv


SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from agent_core import run_react_agent as run_react_loop
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases do Role 1 quản lý từ config/test_cases.json."""
    config_path = os.path.join(os.path.dirname(SRC_DIR), "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(user_query: str, provider):
    """Chạy đúng một LLM call, tuyệt đối không đăng ký hoặc gọi tool."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT).strip()
    print(f"🤖 Chatbot trả lời:\n{response}")
    return {"answer": response, "tool_calls": 0}


def format_observation_for_console(item):
    """Keep full observations in the ReAct context, but print only score-relevant data."""
    tool_name = item["name"]
    if item["observation"].startswith("LỖI:"):
        return item["observation"]

    if tool_name in {"get_candidate_profile", "get_resume_content"}:
        user_id = item["arguments"][0] if item["arguments"] else "không rõ"
        return f"Đã đọc hồ sơ UserID {user_id} để phục vụ chấm điểm."

    if tool_name == "get_job_description":
        job_id = item["arguments"][0] if item["arguments"] else "không rõ"
        return f"Đã đọc yêu cầu JobID {job_id} để phục vụ chấm điểm."

    if tool_name == "score_candidate":
        prefixes = (
            "ĐÁNH GIÁ HỖ TRỢ HR:",
            "Điểm heuristic:",
            "- Tương đồng vị trí:",
            "- Từ khóa kỹ năng/nhiệm vụ:",
            "- Kinh nghiệm làm việc:",
            "- Ngành:",
            "Khuyến nghị:",
        )
        summary_lines = [
            line for line in item["observation"].splitlines()
            if line.startswith(prefixes)
        ]
        return "\n".join(summary_lines) or item["observation"]

    return item["observation"]


def run_react_agent(user_query: str, provider):
    """Integrate Role 2 tools and Role 3 prompts through the ReAct core."""
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    print(f"🛠️ Agent đang có {len(AVAILABLE_TOOLS)} tool: {', '.join(AVAILABLE_TOOLS)}")
    print(f"🛡️ Guardrail: tối đa {MAX_ITERATIONS} vòng lặp")

    result = run_react_loop(
        user_query=user_query,
        provider=provider,
        tools=AVAILABLE_TOOLS,
        system_prompt=REACT_SYSTEM_PROMPT,
        max_iterations=MAX_ITERATIONS,
    )

    for item in result["trace"]:
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {item['step']}/{MAX_ITERATIONS}) ---")
        if item["thought"]:
            print(f"🧠 Thought: {item['thought']}")
        print(f"🛠️ Action: {item['name']}[{', '.join(item['arguments'])}]")
        print(f"👁️ Observation: {format_observation_for_console(item)}")

    if result["termination_reason"] == "max_iterations":
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn {MAX_ITERATIONS} vòng lặp.")
    print(f"\n🏁 Final Answer: {result['answer']}")
    print(f"📊 Tool calls: {result['tool_calls']}")
    return result


if __name__ == "__main__":
    print("=" * 50)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 50)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    for test_case in tests:
        print("\n" + "=" * 50)
        print(f"TEST CASE #{test_case['id']}: {test_case['category']}")
        print(f"Câu hỏi: {test_case['question']}")
        print(f"Kỳ vọng: {test_case['expected_behavior']}")

        print("\n--- CHATBOT BASELINE ---")
        run_baseline_chatbot(test_case["question"], provider)

        print("\n--- REACT AGENT ---")
        run_react_agent(test_case["question"], provider)
