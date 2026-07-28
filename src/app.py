"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import inspect
import json
import os
import re
import textwrap
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


# ============================================================
# 📋 TOOL SPEC — Tự động sinh mô tả tools để inject vào prompt
# ============================================================

def _build_tool_spec() -> str:
    """
    Tự động sinh danh sách tool spec từ AVAILABLE_TOOLS để inject vào
    REACT_SYSTEM_PROMPT, giúp LLM biết chính xác tên tool, tham số và
    mô tả mà không cần hard-code trong prompts.py.
    """
    lines = ["DANH SÁCH CÔNG CỤ (Tools) BẠN ĐƯỢC PHÉP SỬ DỤNG:\n"]
    for name, fn in AVAILABLE_TOOLS.items():
        sig = inspect.signature(fn)
        params = ", ".join(sig.parameters.keys())
        doc_raw = (fn.__doc__ or "").strip()
        # Lấy dòng đầu tiên của docstring làm mô tả ngắn
        first_line = doc_raw.splitlines()[0].strip() if doc_raw else "(không có mô tả)"
        lines.append(f"  • {name}({params})\n    → {first_line}")
    lines.append(
        "\nQUY TẮC GỌI TOOL: Action: tên_tool[tham_số_JSON]\n"
        "Ví dụ:\n"
        '  Action: assess_user_profile[{"education": "CNTT", "skills": ["Python"], "interests": ["dữ liệu"]}]\n'
        '  Action: search_careers[{"interests": ["dữ liệu"], "skills": ["Python", "Excel"]}]\n'
        '  Action: analyze_skill_gap[{"user_skills": ["Python", "Excel"], "target_career": "data_analyst"}]\n'
        '  Action: recommend_learning_path[{"missing_skills": ["SQL", "Thống kê"], "duration_months": 6}]'
    )
    return "\n".join(lines)


def _get_react_system_prompt_with_tools() -> str:
    """Ghép REACT_SYSTEM_PROMPT gốc với tool spec sinh tự động."""
    tool_spec = _build_tool_spec()
    return f"{REACT_SYSTEM_PROMPT.rstrip()}\n\n{tool_spec}\n"


# ============================================================
# 📂 TEST CASES
# ============================================================

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 💬 CHATBOT BASELINE
# ============================================================

def run_baseline_chatbot(user_query: str, provider):
    """
    Chạy Chatbot Baseline định hướng nghề nghiệp (không dùng Tool).
    Sử dụng CHATBOT_BASELINE_PROMPT từ prompts.py, gọi LLM qua provider
    và in kết quả ra console theo định dạng chuẩn.
    """
    print("\n" + "=" * 60)
    print("💬 [CHATBOT BASELINE - Định hướng Nghề nghiệp]")
    print("=" * 60)
    print(f"📝 Câu hỏi: {user_query}")
    # Chỉ in dòng đầu của system prompt để tránh output quá dài
    first_line = CHATBOT_BASELINE_PROMPT.strip().splitlines()[0]
    print(f"⚙️  System Prompt (tóm tắt): {first_line}")
    print("-" * 60)

    # Gọi LLM Provider sinh câu trả lời (không truyền tool)
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)

    if not response or not str(response).strip():
        print("⚠️  Không nhận được phản hồi từ chatbot. Vui lòng kiểm tra lại provider.")
        return

    print(f"🤖 Chatbot trả lời:\n{response}")
    print("=" * 60)


# ============================================================
# 🔧 HELPER — Parse & Invoke Tool
# ============================================================

def _parse_action_args(raw_args: str):
    """Phân giải phần tham số trong 'Action: tool_name[tham_số]' (ưu tiên JSON)."""
    raw_args = raw_args.strip()
    if not raw_args:
        return None
    try:
        return json.loads(raw_args)
    except (json.JSONDecodeError, ValueError):
        return raw_args.strip("'\"")


def _extract_action(response: str):
    """
    Trích xuất (tool_name, raw_args) từ dòng 'Action: tool_name[...]'
    sử dụng bracket matching để xử lý JSON lồng nhiều mức (có [] trong args).
    Trả về (tool_name, args_str) hoặc None nếu không tìm thấy.
    """
    # Tìm vị trí bắt đầu của 'Action:'
    m = re.search(r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)", response, re.IGNORECASE)
    if not m:
        return None
    tool_name = m.group(1)
    rest = response[m.end():].lstrip()

    if not rest.startswith("["):
        # Action không có args
        return tool_name, ""

    # Bracket matching: đếm số '[' và ']' để tìm đầu/cuối args
    depth = 0
    end_idx = 0
    for i, ch in enumerate(rest):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end_idx = i
                break
    args_str = rest[1:end_idx].strip()  # Bỏ '[' và ']' ngoài cùng
    return tool_name, args_str


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


def _format_observation(obs) -> str:
    """Chuyển Observation (dict/list/str) thành chuỗi JSON đẹp để đưa vào transcript."""
    if isinstance(obs, (dict, list)):
        return json.dumps(obs, ensure_ascii=False, indent=2)
    return str(obs)


def _print_divider(char: str = "─", width: int = 60):
    print(char * width)


# ============================================================
# 🔄 REACT AGENT LOOP (Hoàn chỉnh)
# ============================================================

def run_react_agent(user_query: str, provider):
    """
    Vòng lặp ReAct Agent Loop hoàn chỉnh:
      • Inject tool spec vào system prompt để LLM biết tool nào có sẵn
      • Duy trì conversation history (transcript) qua các bước
      • Parse Thought / Action / Final Answer từng bước
      • Thực thi tool thật và đưa Observation vào transcript
      • Guardrail: ngắt an toàn khi vượt MAX_ITERATIONS
    """
    system_prompt = _get_react_system_prompt_with_tools()

    print("\n" + "=" * 60)
    print("🤖 [REACT AGENT LOOP - Định hướng Nghề nghiệp]")
    print("=" * 60)
    print(f"📝 Câu hỏi người dùng: {user_query}")
    print(f"🛡️  Guardrail: tối đa {MAX_ITERATIONS} vòng lặp")
    print(f"🔧 Tools đăng ký: {', '.join(AVAILABLE_TOOLS.keys())}")
    _print_divider("=")

    # Conversation transcript: nối dần qua mỗi bước
    # (tương thích với GeminiProvider / MockProvider hiện tại)
    transcript = f"Câu hỏi của người dùng: {user_query}"

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'─'*60}")
        print(f"🔄  STEP {step}/{MAX_ITERATIONS}  ─  Đang gọi LLM...")
        print(f"{'─'*60}")

        # --- Gọi LLM ---
        response = provider.generate(transcript, system_prompt=system_prompt)
        response = (response or "").strip()

        if not response:
            print("⚠️  LLM không trả về nội dung. Dừng vòng lặp.")
            break

        # Hiển thị phản hồi thô của LLM
        print(f"\n📤 LLM Response (raw):\n{response}")

        # --- Kiểm tra Final Answer trước ---
        final_match = re.search(
            r"Final Answer\s*:\s*(.*)", response, re.DOTALL | re.IGNORECASE
        )
        if final_match:
            final_text = final_match.group(1).strip()
            print(f"\n{'='*60}")
            print(f"🏁 FINAL ANSWER (sau {step} step(s)):")
            print(f"{'='*60}")
            for line in final_text.splitlines():
                print(textwrap.fill(line, width=70) if len(line) > 70 else line)
            print(f"{'='*60}")
            return  # Kết thúc thành công

        # --- Kiểm tra Action ---
        # Dùng bracket matching để xử lý JSON có array lồng trong args
        extracted = _extract_action(response)

        if not extracted:
            print("⚠️  Không nhận diện được 'Action' hoặc 'Final Answer' trong phản hồi.")
            print("💡  Nối response vào transcript rồi thử lại (LLM có thể cần thêm context).")
            transcript += (
                f"\n{response}\n"
                "Observation: Vui lòng tuân theo định dạng Thought/Action hoặc Final Answer."
            )
            continue

        tool_name, raw_args = extracted

        print(f"\n🔧 Tool được gọi   : {tool_name}")
        print(f"📥 Tham số (raw)   : {raw_args or '(không có)'}")

        # --- Thực thi Tool ---
        if tool_name not in AVAILABLE_TOOLS:
            obs_text = (
                f"LỖI: Công cụ '{tool_name}' không tồn tại trong hệ thống. "
                f"Các tool hợp lệ: {', '.join(AVAILABLE_TOOLS.keys())}."
            )
        else:
            try:
                parsed_args = _parse_action_args(raw_args)
                obs_result  = _invoke_tool(tool_name, parsed_args)
                obs_text    = _format_observation(obs_result)
            except Exception as e:
                obs_text = f"LỖI khi thực thi '{tool_name}': {e}"

        print(f"\n👁️  Observation:\n{obs_text}")

        # Nối cặp (response + Observation) vào transcript cho vòng tiếp theo
        transcript += f"\n{response}\nObservation: {obs_text}"

    # --- Guardrail kích hoạt ---
    print(f"\n🛡️  GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước.")
    print("   Agent dừng an toàn. Nếu muốn thêm bước, tăng MAX_ITERATIONS trong prompts.py.")
    print("=" * 60)


# ============================================================
# ▶️ ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 60)

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__}  |  Model: {model_name}")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json")

    # Test case đầu tiên (câu hỏi kiến thức chung) phù hợp để demo Baseline Chatbot
    sample_query = tests[0]["question"]

    print("\n" + "─" * 60)
    print("📌 DEMO 1: CHATBOT BASELINE (không dùng Tool)")
    print("─" * 60)
    run_baseline_chatbot(sample_query, provider)

    print("\n" + "─" * 60)
    print("📌 DEMO 2: REACT AGENT LOOP (có Tool - Định hướng Nghề nghiệp)")
    print("─" * 60)
    run_react_agent(REACT_DEMO_QUERY, provider)
