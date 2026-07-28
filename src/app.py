"""
🚀 CORE AGENT APP (Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + LLM Provider.
Sử dụng LangChain native tool calling mechanism.
"""

import json
import os
import sys
from typing import Generator
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
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

# ============================================================================
# CONVERT TOOLS TO LANGCHAIN FORMAT
# ============================================================================


@tool
def search_ai_courses(keyword: str, level: str = None, budget_level: str = None) -> str:
    """Search for AI/Python courses based on keyword, skill level, and budget.

    Args:
        keyword: Search term (e.g., "machine learning", "python", "deep learning")
        level: Filter by minimum profile level (beginner/basic/intermediate). If None, no filter.
        budget_level: Filter by maximum budget (low/medium/high). If None, no filter.

    Returns:
        Formatted string with course search results
    """
    return AVAILABLE_TOOLS["search_ai_courses"](keyword, level, budget_level)


@tool
def get_ai_course_detail(course_code: str) -> str:
    """Get complete details of a specific AI/Python course.

    Args:
        course_code: Course code (e.g., "PY101", "ML301", "DL401")

    Returns:
        Formatted string with course details including prerequisites, skills, duration, etc.
    """
    return AVAILABLE_TOOLS["get_ai_course_detail"](course_code)


@tool
def check_course_readiness(course_code: str, current_skills: list[str]) -> str:
    """Check if a learner is ready for a course based on their current skills.

    Args:
        course_code: Course code to check (e.g., "ML301")
        current_skills: List of skills the learner currently has (e.g., ["python", "math", "statistics"])

    Returns:
        Formatted string indicating readiness status and skill gaps
    """
    return AVAILABLE_TOOLS["check_course_readiness"](course_code, current_skills)


@tool
def get_learning_track(goal: str) -> str:
    """Get the standard learning path for a specific goal.

    Args:
        goal: Learning objective (e.g., "learn Python", "machine learning internship", "generative AI agent")

    Returns:
        Formatted string with recommended learning path and course sequence
    """
    return AVAILABLE_TOOLS["get_learning_track"](goal)


@tool
def filter_courses_by_constraints(
    course_codes: list[str], available_hours_per_week: int, budget_level: str
) -> str:
    """Filter courses based on time and budget constraints.

    Args:
        course_codes: List of course codes to filter (e.g., ["PY101", "ML301"])
        available_hours_per_week: Available hours per week (integer or level like "ít"/"vừa"/"nhiều")
        budget_level: Budget level (low/medium/high)

    Returns:
        Formatted string categorizing courses as suitable or unsuitable
    """
    return AVAILABLE_TOOLS["filter_courses_by_constraints"](
        course_codes, available_hours_per_week, budget_level
    )


# Map of tool names to LangChain tool objects
LANGCHAIN_TOOLS = {
    "search_ai_courses": search_ai_courses,
    "get_ai_course_detail": get_ai_course_detail,
    "check_course_readiness": check_course_readiness,
    "get_learning_track": get_learning_track,
    "filter_courses_by_constraints": filter_courses_by_constraints,
}


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_query(tc: dict) -> str:
    """Chuyển test case dạng {input: {...}} thành câu hỏi tự nhiên cho LLM."""
    inp = tc["input"]
    return (
        f"Mình {inp['level']}, "
        f"muốn {inp['goal']}, "
        f"thời gian rảnh {inp['free_time']}, "
        f"ngân sách {inp['budget']}."
    )


def run_baseline_chatbot(user_query: str, llm):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    Gọi LangChain ChatModel.invoke() với system_prompt + user_query.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()[:120]}...")

    messages = [
        SystemMessage(content=CHATBOT_BASELINE_PROMPT),
        HumanMessage(content=user_query),
    ]
    response = llm.invoke(messages)
    print(f"🤖 Chatbot trả lời:\n{response.content}")


def run_react_agent(
    user_query: str,
    llm,
    messages: list,
    step_offset: int = 0,
) -> Generator[dict, None, None]:
    """
    Vòng lặp ReAct Agent – multi-turn.

    Thêm HumanMessage(user_query) vào `messages`, chạy ReAct loop, và
    append tất cả message mới (AIMessage, ToolMessage, ...) trực tiếp vào
    `messages`. Khi generator kết thúc, `messages` đã chứa đầy đủ lịch sử
    của turn này để caller có thể tiếp tục turn kế tiếp.

    Generator yield dict tại mỗi bước:
    - {"type": "thought", "step": int, "content": str}
    - {"type": "action",  "step": int, "tool": str, "args": dict, "call_id": str}
    - {"type": "observation", "step": int, "tool": str, "content": str, "call_id": str}
    - {"type": "final",   "step": int, "content": str}
    - {"type": "guardrail", "step": int, "content": str}
    - {"type": "error",   "step": int, "content": str}

    Args:
        user_query:   Câu hỏi của người dùng ở turn này.
        llm:          LangChain ChatModel (từ get_llm_provider()).
        messages:     Danh sách message đang tích luỹ (caller-owned, mutated in-place).
        step_offset:  Giá trị bắt đầu của step counter (để đánh số step liên tục
                      qua nhiều turn).

    Yields:
        dict: Sự kiện theo thứ tự xảy ra.

    Returns (sau khi yield xong):
        int: Số bước đã chạy trong turn này (để caller cập nhật step_offset).
    """
    from langchain_core.messages import AIMessage  # local import to avoid cycle

    # Bind tools vào LLM - LangChain tự sinh JSON schema từ @tool
    tools = list(LANGCHAIN_TOOLS.values())
    llm_with_tools = llm.bind_tools(tools)

    # Append HumanMessage cho turn này
    messages.append(HumanMessage(content=user_query))

    for step_rel in range(1, MAX_ITERATIONS + 1):
        step = step_offset + step_rel

        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            yield {"type": "error", "step": step, "content": f"LLM call failed: {e}"}
            return step_rel

        # Sau khi LLM trả lời, append AI message vào messages.
        # Nếu response CÓ tool_calls, response đã chứa cả tool_calls metadata
        # → append nguyên bản, rồi sau đó append từng ToolMessage.
        # Nếu response KHÔNG có tool_calls, đó là final message.
        messages.append(AIMessage(content=response.content or "", tool_calls=getattr(response, "tool_calls", []) or []))

        if response.content:
            yield {"type": "thought", "step": step, "content": response.content}

        tool_calls = getattr(response, "tool_calls", []) or []
        if tool_calls:
            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                call_id = tc["id"]

                yield {
                    "type": "action",
                    "step": step,
                    "tool": tool_name,
                    "args": tool_args,
                    "call_id": call_id,
                }

                # Dispatch tool
                if tool_name not in LANGCHAIN_TOOLS:
                    obs = f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ: {', '.join(LANGCHAIN_TOOLS.keys())}"
                else:
                    try:
                        obs = LANGCHAIN_TOOLS[tool_name].invoke(tool_args)
                    except Exception as e:
                        obs = f"LỖI HỆ THỐNG: Tool '{tool_name}' gặp lỗi: {e}"

                # Append ToolMessage vào messages (liên kết qua call_id)
                from langchain_core.messages import ToolMessage
                messages.append(ToolMessage(content=obs, tool_call_id=call_id))

                yield {
                    "type": "observation",
                    "step": step,
                    "tool": tool_name,
                    "content": obs,
                    "call_id": call_id,
                }
        else:
            # Không có tool_calls → Final Answer
            yield {"type": "final", "step": step, "content": response.content or ""}
            return step_rel

    # Guardrail
    yield {
        "type": "guardrail",
        "step": step_offset + MAX_ITERATIONS,
        "content": f"Đã đạt giới hạn {MAX_ITERATIONS} bước. Ngắt an toàn.",
    }
    return MAX_ITERATIONS


def _init_messages() -> list:
    """Khởi tạo messages với system prompt cho ReAct Agent."""
    system_prompt = """You are a helpful ReAct Agent with access to tools.

When you need information, call the appropriate tool. When you receive tool results, use them to inform your reasoning. When you have enough information to answer, provide the final answer directly.

Be concise and specific in your reasoning."""
    return [SystemMessage(content=system_prompt)]


if __name__ == "__main__":
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 60)

    # Khởi tạo LangChain ChatModel
    try:
        llm = get_llm_provider()
    except ValueError as e:
        print(f"\n⚠️  Chưa cấu hình API key: {e}")
        print("💡 Thiết lập trong file .env (xem .env.example), hoặc chạy:")
        print('   export LLM_PROVIDER="openai" && export OPENAI_API_KEY="sk-..."')
        sys.exit(1)

    model_id = getattr(llm, "model_name", None) or getattr(llm, "model", "?")
    provider_name = getattr(llm, "_provider_name", "?")
    print(f"🔌 Provider  : {provider_name}")
    print(f"🤖 ChatModel : {llm.__class__.__name__}")
    print(f"🔧 Model     : {model_id}")

    print("\n" + "─" * 60)
    print("REACT AGENT - Multi-turn Conversation")
    print("─" * 60)
    print("Gõ câu hỏi của bạn, hoặc:")
    print("  • 'quit' / 'exit' / 'q' để thoát")
    print("  • 'reset' / 'clear' để xóa lịch sử")
    print("  • 'history' để xem toàn bộ conversation")
    print("─" * 60 + "\n")

    # Khởi tạo conversation history (sẽ được giữ qua nhiều turn)
    messages = _init_messages()
    step_offset = 0
    turn_count = 0

    while True:
        # Đọc input từ user
        try:
            user_input = input("👤 Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Tạm biệt!")
            break

        if not user_input:
            continue

        # Xử lý commands
        cmd = user_input.lower()
        if cmd in ("quit", "exit", "q"):
            print("\n👋 Tạm biệt!")
            break
        elif cmd in ("reset", "clear"):
            messages = _init_messages()
            step_offset = 0
            turn_count = 0
            print("\n🔄 Đã xóa lịch sử. Bắt đầu cuộc trò chuyện mới.\n")
            continue
        elif cmd == "history":
            print("\n" + "─" * 60)
            print(f"LỊCH SỬ CUỘC TRÒ CHUYỆN ({turn_count} turn, {len(messages)} messages)")
            print("─" * 60)
            for i, msg in enumerate(messages):
                role = msg.__class__.__name__
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                print(f"  [{i}] {role}: {content}")
            print("─" * 60 + "\n")
            continue

        # Bắt đầu turn mới
        turn_count += 1
        print(f"\n{'═' * 60}")
        print(f"TURN {turn_count}: Agent đang suy nghĩ...")
        print(f"{'═' * 60}\n")

        # Chạy ReAct agent với accumulated messages
        for event in run_react_agent(user_input, llm, messages, step_offset):
            step = event.get("step", "?")
            rtype = event["type"]

            if rtype == "thought":
                print(f"[Step {step}] 💭 Thought")
                print(f"         {event['content']}\n")

            elif rtype == "action":
                args_str = json.dumps(event["args"], ensure_ascii=False, indent=2)
                print(f"[Step {step}] 🛠️  Action: {event['tool']}")
                print(f"         Args: {args_str}\n")

            elif rtype == "observation":
                obs = event["content"]
                obs_preview = obs[:200].replace("\n", " ↵ ")
                print(f"[Step {step}] 👁️  Observation ({event['tool']})")
                print(f"         {obs_preview}{'...' if len(obs) > 200 else ''}\n")

            elif rtype == "final":
                print(f"[Step {step}] ✅ Final Answer")
                print(f"   {event['content']}\n")

            elif rtype == "guardrail":
                print(f"[Step {step}] 🛡️  Guardrail")
                print(f"   {event['content']}\n")

            elif rtype == "error":
                print(f"[Step {step}] ❌ Error")
                print(f"   {event['content']}\n")

        # Cập nhật step_offset để turn sau đánh số step liên tục
        step_offset += MAX_ITERATIONS

        print("─" * 60 + "\n")

    print("=" * 60)
