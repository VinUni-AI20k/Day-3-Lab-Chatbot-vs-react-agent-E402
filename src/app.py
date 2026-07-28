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
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

# Câu hỏi mẫu cho demo ReAct Agent (config/test_cases.json vẫn đang là bộ câu hỏi
# thời tiết/vé máy bay cũ của Role 1, chưa được cập nhật theo bộ tool định hướng
# nghề nghiệp hiện tại trong tools.py, nên demo ReAct dùng câu hỏi riêng ở đây).
REACT_DEMO_QUERY = (
    "Tôi tốt nghiệp Công nghệ Thông tin, biết Python và Excel, thích làm việc với "
    "dữ liệu và logic. Tôi nên theo nghề gì và cần học thêm những kỹ năng nào?"
)

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


def run_baseline_chatbot(user_query: str, provider):
    """
    Chạy Chatbot Baseline định hướng nghề nghiệp (không dùng Tool).
    Sử dụng CHATBOT_BASELINE_PROMPT từ prompts.py, gọi LLM qua provider
    và in kết quả ra console theo định dạng chuẩn.
    """
    print("\n" + "=" * 50)
    print("💬 [CHATBOT BASELINE - Định hướng Nghề nghiệp]")
    print("=" * 50)
    print(f"📝 Câu hỏi: {user_query}")
    # Chỉ in dòng đầu của system prompt để tránh output quá dài
    first_line = CHATBOT_BASELINE_PROMPT.strip().splitlines()[0]
    print(f"⚙️  System Prompt (tóm tắt): {first_line}")
    print("-" * 50)

    # Gọi LLM Provider sinh câu trả lời (không truyền tool)
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)

    if not response or not str(response).strip():
        print("⚠️  Không nhận được phản hồi từ chatbot. Vui lòng kiểm tra lại provider.")
        return

    print(f"🤖 Chatbot trả lời:\n{response}")
    print("=" * 50)


def _parse_action_args(raw_args: str):
    """Phân giải phần tham số trong 'Action: tool_name[tham_số]' (ưu tiên JSON)."""
    raw_args = raw_args.strip()
    if not raw_args:
        return None
    try:
        return json.loads(raw_args)
    except (json.JSONDecodeError, ValueError):
        return raw_args.strip("'\"")


def _invoke_tool(tool_name: str, args):
    """Gọi tool trong AVAILABLE_TOOLS, ánh xạ args theo chữ ký thực tế của tool."""
    fn = AVAILABLE_TOOLS[tool_name]
    params = list(inspect.signature(fn).parameters.keys())

    if args is None:
        return fn()
    if len(params) == 1:
        # VD: assess_user_profile(profile), get_career_details(career_name)
        return fn(args)
    if isinstance(args, dict):
        # VD: search_careers(interests, skills), analyze_skill_gap(user_skills, target_career)
        return fn(**args)
    raise ValueError(f"Không thể ánh xạ tham số {args!r} cho công cụ '{tool_name}' (cần {params}).")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails,
    thực thi tool thật từ AVAILABLE_TOOLS (Role 2) theo định dạng của REACT_SYSTEM_PROMPT (Role 3).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    transcript = f"Câu hỏi của người dùng: {user_query}"
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        response = provider.generate(transcript, system_prompt=REACT_SYSTEM_PROMPT)
        print(response)

        final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
        if final_match:
            print(f"\n🏁 Câu trả lời cuối cùng: {final_match.group(1).strip()}")
            return

        action_match = re.search(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(.*)\]", response, re.DOTALL)
        if not action_match:
            print("⚠️ Không nhận diện được Action hoặc Final Answer hợp lệ trong phản hồi. Dừng vòng lặp an toàn.")
            return

        tool_name = action_match.group(1).strip()
        raw_args = action_match.group(2).strip()

        if tool_name not in AVAILABLE_TOOLS:
            obs = f"LỖI: Công cụ '{tool_name}' không tồn tại trong hệ thống đã đăng ký."
        else:
            try:
                obs = _invoke_tool(tool_name, _parse_action_args(raw_args))
            except Exception as e:
                obs = f"LỖI khi thực thi công cụ '{tool_name}': {e}"

        print(f"👁️ Observation: {obs}")
        transcript += f"\n{response}\nObservation: {obs}"

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

    # Test case đầu tiên (câu hỏi kiến thức chung) phù hợp để demo Baseline Chatbot
    sample_query = tests[0]["question"]

    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)

    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(REACT_DEMO_QUERY, provider)
