"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

Chủ đề nhóm: Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa.

Trạng thái theo Mốc:
- ✅ Mốc 2: run_baseline_chatbot() chạy toàn bộ test cases qua Chatbot gốc (không Tool).
- ⏳ Mốc 3: run_react_agent() sẽ được lắp vòng lặp Thought -> Action -> Observation.
"""

import inspect
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
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Dựng Chatbot gốc (Baseline - Cấp 2): chỉ có LLM, KHÔNG được gọi Tool.

    Args:
        user_query: Câu hỏi của người dùng.
        provider: LLM Provider lấy từ get_llm_provider().

    Returns:
        Chuỗi phản hồi của Chatbot (để Role 5 dán vào docs/trace_eval.md).
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)

    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


ACTION_PATTERN = re.compile(r"Action:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[(.*)\]", re.DOTALL)


def parse_llm_output(text: str):
    """
    Tách phản hồi LLM thành ('final', câu trả lời) hoặc ('action', tên_tool, [tham_số]).

    Nếu LLM sinh cả Action lẫn Final Answer thì lấy cái xuất hiện TRƯỚC — chặn việc
    LLM tự bịa Observation rồi kết luận luôn mà chưa hề gọi tool.
    """
    idx_action = text.find("Action:")
    idx_final = text.find("Final Answer:")

    # Chỉ nhận Final Answer khi nó đứng trước Action (hoặc không có Action nào)
    if idx_final != -1 and (idx_action == -1 or idx_final < idx_action):
        return ("final", text[idx_final + len("Final Answer:"):].strip())

    if idx_action != -1:
        # Chỉ parse dòng Action đầu tiên, bỏ mọi thứ LLM viết sau đó
        chunk = text[idx_action:].split("\n")[0]
        match = ACTION_PATTERN.search(chunk)
        if match:
            tool_name = match.group(1).strip()
            raw_args = match.group(2).strip()
            args = [a.strip() for a in raw_args.split(",")] if raw_args else []
            return ("action", tool_name, args)

    # LLM không theo format -> coi như câu trả lời cuối
    return ("final", text.strip())


def execute_tool(tool_name: str, args: list) -> str:
    """
    Gọi tool an toàn: sai tên, sai số lượng tham số hay tool crash đều trả về
    chuỗi lỗi để Agent tự xoay xở, KHÔNG làm sập vòng lặp.
    """
    tool = AVAILABLE_TOOLS.get(tool_name)
    if tool is None:
        return (
            f"LỖI: Không có tool tên '{tool_name}'. "
            f"Chỉ được dùng: {', '.join(AVAILABLE_TOOLS.keys())}."
        )

    n_params = len(inspect.signature(tool).parameters)

    # LLM hay tách triệu chứng thành nhiều phần: suggest_specialty[đầy hơi, ợ chua]
    # -> gộp lại thành 1 chuỗi cho đúng chữ ký hàm.
    if n_params == 1 and len(args) > 1:
        args = [", ".join(args)]

    if len(args) != n_params:
        return (
            f"LỖI: Tool '{tool_name}' cần {n_params} tham số nhưng nhận được {len(args)}. "
            f"Hãy gọi lại đúng định dạng hoặc hỏi người dùng thông tin còn thiếu."
        )

    try:
        return tool(*args)
    except Exception as e:
        return f"LỖI TOOL '{tool_name}': {e}"


def run_react_agent(user_query: str, provider) -> str:
    """
    Vòng lặp ReAct (Cấp 3): Thought -> Action -> Observation, có Guardrails.

    Args:
        user_query: Câu hỏi của người dùng.
        provider: LLM Provider lấy từ get_llm_provider().

    Returns:
        Toàn bộ trace log (để Role 5 dán vào docs/trace_eval.md).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    transcript = f"Câu hỏi của người dùng: {user_query}\n"
    seen_actions = set()  # Guardrail 7: chặn lặp lại cùng Action + tham số

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Step {step}/{MAX_ITERATIONS} ---")

        raw = provider.generate(transcript, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = parse_llm_output(raw)

        # In Thought ra để Role 5 trích trace
        for line in raw.splitlines():
            if line.strip().startswith("Thought:"):
                print(f"🧠 {line.strip()}")
                break

        if parsed[0] == "final":
            print(f"🏁 Final Answer: {parsed[1]}")
            transcript += f"\nFinal Answer: {parsed[1]}"
            return transcript

        _, tool_name, args = parsed
        print(f"🛠️ Action: {tool_name}{args}")

        signature = f"{tool_name}|{args}"
        if signature in seen_actions:
            print("🛡️ GUARDRAIL: Agent lặp lại y hệt Action đã gọi. Ngắt vòng lặp.")
            fallback = (
                "Xin lỗi, hệ thống chưa lấy được thông tin bạn cần. "
                "Vui lòng liên hệ trực tiếp phòng khám để được hỗ trợ."
            )
            print(f"🏁 Final Answer: {fallback}")
            return transcript + f"\nGUARDRAIL: repeated action -> {fallback}"
        seen_actions.add(signature)

        observation = execute_tool(tool_name, args)
        print(f"👁️ Observation: {observation}")

        transcript += f"\nThought & Action: {tool_name}{args}\nObservation: {observation}\n"

    print(f"🛡️ GUARDRAIL: Đã chạm giới hạn {MAX_ITERATIONS} bước. Ngắt lặp an toàn.")
    fallback = (
        "Xin lỗi, yêu cầu của bạn cần nhiều bước hơn hệ thống cho phép. "
        "Vui lòng liên hệ phòng khám để được hỗ trợ trực tiếp."
    )
    print(f"🏁 Final Answer: {fallback}")
    return transcript + f"\nGUARDRAIL: max iterations -> {fallback}"


def print_header(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


if __name__ == "__main__":
    print_header("🏫 BÀI LAB 3: CHATBOT VS REACT AGENT — ĐẶT LỊCH KHÁM BỆNH")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")

    if provider.__class__.__name__ == "MockProvider":
        print("⚠️  CẢNH BÁO: Đang chạy MockProvider (offline).")
        print("   Muốn thấy đúng hạn chế của Chatbot gốc, hãy tạo file .env từ .env.example")
        print("   và điền API key thật, rồi chạy lại.")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json")

    # ==================================================================
    # 📍 MỐC 2: Chạy TOÀN BỘ test cases qua Chatbot Baseline
    # Mục tiêu: chứng minh Chatbot gốc xử lý tốt câu 1-2, nhưng bó tay
    # hoặc ảo giác ở câu 3-8 vì không tra được dữ liệu phòng khám.
    # ==================================================================
    print_header("📍 MỐC 2 — DEMO CHATBOT BASELINE (CẤP 2: LLM, KHÔNG TOOL)")

    # Chỉ chạy các case tiêu biểu để tiết kiệm lượt gọi API.
    # 1, 2 = kiến thức chung (Chatbot làm tốt)
    # 3, 10, 16 = cần dữ liệu phòng khám (Chatbot sẽ bịa bác sĩ / giờ / mã hẹn)
    SELECTED_CASE_IDS = [1, 2, 3, 10, 16]
    selected = [c for c in tests if c["id"] in SELECTED_CASE_IDS]
    print(f"🎯 Chạy {len(selected)}/{len(tests)} case tiêu biểu: {SELECTED_CASE_IDS}")

    for case in selected:
        print("\n" + "-" * 70)
        tool_path = case.get("expected_tool_path", [])
        route = "Chatbot (không cần tool)" if not tool_path else f"Agent -> {tool_path}"
        print(f"🧪 Test #{case['id']} | {case['category']} | Kỳ vọng: {route}")
        print(f"📌 Kỳ vọng: {case['expected_behavior']}")

        run_baseline_chatbot(case["question"], provider)

    # ==================================================================
    # 📍 MỐC 3: ReAct Agent Loop + Guardrails
    # ==================================================================
    print_header("📍 MỐC 3 — REACT AGENT (CẤP 3: THOUGHT -> ACTION -> OBSERVATION)")

    # 16 = chuỗi ReAct đầy đủ 5 tool | 28 = bẫy cấp cứu
    # 39 = bẫy Observation giả      | 46 = bẫy lặp vô hạn
    REACT_CASE_IDS = [16, 28, 39, 46]
    react_cases = [c for c in tests if c["id"] in REACT_CASE_IDS]
    print(f"🎯 Chạy {len(react_cases)}/{len(tests)} case: {REACT_CASE_IDS}")

    for case in react_cases:
        print("\n" + "-" * 70)
        print(f"🧪 Test #{case['id']} | {case['category']}")
        print(f"📌 Kỳ vọng: {case['expected_behavior']}")

        run_react_agent(case["question"], provider)
