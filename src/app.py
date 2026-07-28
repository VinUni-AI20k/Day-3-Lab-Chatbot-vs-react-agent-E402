"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
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
from tools import TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

# Registry tra tool thật theo tên để dispatch động trong vòng lặp ReAct
TOOL_REGISTRY = {fn.__name__: fn for fn in TOOLS}

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")

    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def build_tool_specs() -> str:
    """Sinh mô tả tool THẬT (tên, tham số, docstring) từ tools.py qua inspect."""
    lines = []
    for fn in TOOLS:
        params = ", ".join(inspect.signature(fn).parameters.keys())
        doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
        lines.append(f"- {fn.__name__}[{params}]: {doc}")
    return "\n".join(lines)


def build_react_system_prompt() -> str:
    """REACT_SYSTEM_PROMPT (Role 3) mô tả tool cũ get_weather/search_flights đã lỗi thời.
    Ghi đè bằng danh sách tool THẬT lấy trực tiếp từ tools.py mà không sửa prompts.py."""
    return (
        REACT_SYSTEM_PROMPT
        + "\n\n⚠️ LƯU Ý: Bỏ qua hoàn toàn danh sách tool ở trên (get_weather, search_flights) vì KHÔNG CÒN TỒN TẠI.\n"
        + "Danh sách Tool THẬT duy nhất bạn được phép gọi:\n"
        + build_tool_specs()
    )


def parse_react_response(response: str):
    """Trích Thought + (Action tool/args) hoặc Final Answer từ phản hồi thô của LLM."""
    thought_match = re.search(r"Thought:\s*(.+)", response)
    thought = thought_match.group(1).strip().splitlines()[0] if thought_match else ""

    final_match = re.search(r"Final Answer:\s*(.+)", response, re.DOTALL)
    if final_match:
        return thought, None, None, final_match.group(1).strip()

    action_match = re.search(r"Action:\s*(\w+)\[(.*)\]", response, re.DOTALL)
    if action_match:
        tool_name = action_match.group(1).strip()
        raw_args = action_match.group(2).strip()
        return thought, tool_name, raw_args, None

    return thought, None, None, None


def _parse_raw_args(raw_args: str):
    """Tách 'a, "b, c", 123' thành list giá trị. Ưu tiên parse như JSON array
    (an toàn với dấu phẩy bên trong chuỗi có ngoặc kép), fallback về split thô."""
    if not raw_args:
        return []
    try:
        return [str(v) for v in json.loads(f"[{raw_args}]")]
    except (json.JSONDecodeError, ValueError):
        return [v.strip().strip('"\'') for v in raw_args.split(",")]


def call_tool(tool_name: str, raw_args: str) -> str:
    """Gọi tool thật theo tên + args thô ('a, b, c'), tự map theo đúng thứ tự tham số của hàm."""
    func = TOOL_REGISTRY.get(tool_name)
    if not func:
        return json.dumps({"status": "error", "message": f"Tool '{tool_name}' không tồn tại."}, ensure_ascii=False)

    raw_values = _parse_raw_args(raw_args)
    params = list(inspect.signature(func).parameters.values())

    kwargs = {}
    for param, value in zip(params, raw_values):
        if param.annotation is int:
            digits = re.sub(r"[^\d-]", "", value)
            value = int(digits) if digits else 0
        kwargs[param.name] = value

    try:
        return func(**kwargs)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Lỗi khi gọi tool '{tool_name}': {str(e)}"}, ensure_ascii=False)


def run_react_agent(user_query: str, provider):
    """
    Vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails,
    gọi tool thật từ tools.py và không cho phép LLM tự bịa Observation.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    system_prompt = build_react_system_prompt()
    scratchpad = ""
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        user_prompt = f"Câu hỏi: {user_query}\n{scratchpad}"
        response = provider.generate(user_prompt, system_prompt=system_prompt)

        thought, tool_name, raw_args, final_answer = parse_react_response(response)
        if thought:
            print(f"🧠 Thought: {thought}")

        if final_answer:
            print(f"🏁 Final Answer: {final_answer}")
            return

        if not tool_name:
            print(f"⚠️ Không nhận diện được định dạng phản hồi hợp lệ từ LLM:\n{response}")
            return

        print(f"🛠️ Action: {tool_name}[{raw_args}]")
        observation = call_tool(tool_name, raw_args)
        print(f"👁️ Observation: {observation}")

        scratchpad += f"\nThought: {thought}\nAction: {tool_name}[{raw_args}]\nObservation: {observation}\n"

    print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    # config/test_cases.json vẫn là bộ câu hỏi cũ (thời tiết/chuyến bay) của Role 1.
    # Câu hỏi demo mẫu dưới đây thay thế cho tests[2]["question"], đúng chủ đề
    # "Tìm & Đặt lịch xem nhà trọ/căn hộ cho thuê" và đủ để kích hoạt chuỗi tool
    # search_rooms -> book_viewing_appointment trong giới hạn MAX_ITERATIONS.
    sample_query = (
        "Tôi muốn tìm phòng trọ ở Cầu Giấy giá dưới 4 triệu, nếu có phòng phù hợp thì "
        "đặt lịch xem nhà giúp tôi vào ngày 30/07/2026 lúc 15:00, tên tôi là Huy."
    )

    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
