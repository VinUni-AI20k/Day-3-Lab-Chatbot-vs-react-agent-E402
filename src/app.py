"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
Chủ đề: Trợ Lý Đặt Lịch Khám Bệnh & Tư Vấn Chuyên Khoa

File chính ghép nối:
  - Tools      (src/tools.py)
  - Prompts    (src/prompts.py)
  - Test Cases (config/test_cases.json)
  - Provider   (src/providers.py)

Bao gồm:
  [Cấp 2] run_baseline_chatbot()   — Chatbot thuần LLM, 0 tool calls
  [Cấp 3] run_react_agent()        — ReAct Loop thực sự: parse → execute → observe
  [Cấp 4] AutonomousAgent (BONUS)  — Tự chia nhỏ mục tiêu (Planning) + Memory
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
from tools import (
    AVAILABLE_TOOLS,
    check_doctor_schedule,
    get_symptom_advice,
    book_appointment,
    cancel_appointment,
)
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    GUARDRAIL_MESSAGE,
)
from providers import get_llm_provider

load_dotenv()

# =============================================================================
# 📂 HELPER: Đọc Test Cases từ config/test_cases.json
# =============================================================================

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# 🔍 PARSER: Trích xuất Action từ text LLM sinh ra
# =============================================================================

def parse_action(text: str):
    """
    Parse chuỗi Action từ LLM output.

    Cú pháp kỳ vọng:
        Action: tool_name["arg1", "arg2"]
        Action: tool_name['arg1', 'arg2']
        Action: tool_name[arg1, arg2]

    Returns:
        tuple(tool_name: str, args: list[str]) nếu tìm thấy
        None nếu không tìm thấy Action hợp lệ
    """
    # Pattern tìm "Action: tool_name[...]"
    pattern = r'Action:\s*(\w+)\[([^\]]*)\]'
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    tool_name = match.group(1).strip()
    args_raw   = match.group(2).strip()

    # Parse arguments: xử lý dấu nháy đơn/kép hoặc không có nháy
    if not args_raw:
        args = []
    else:
        # Lấy tất cả giá trị trong nháy đôi/đơn hoặc tách bằng dấu phẩy
        quoted = re.findall(r'["\']([^"\']*)["\']', args_raw)
        if quoted:
            args = quoted
        else:
            args = [a.strip() for a in args_raw.split(",") if a.strip()]

    return tool_name, args


def parse_final_answer(text: str):
    """
    Trích xuất nội dung Final Answer từ LLM output.

    Returns:
        str nội dung Final Answer, hoặc None nếu không tìm thấy
    """
    pattern = r'Final Answer:\s*(.+)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


# =============================================================================
# ⚙️ EXECUTOR: Gọi Tool và bắt lỗi an toàn
# =============================================================================

def execute_tool(tool_name: str, args: list) -> str:
    """
    Tra cứu tool trong AVAILABLE_TOOLS và thực thi với args cho trước.

    Returns:
        str: Kết quả từ tool, hoặc thông báo lỗi nếu tool không tồn tại / crash
    """
    if tool_name not in AVAILABLE_TOOLS:
        valid = ", ".join(AVAILABLE_TOOLS.keys())
        return (f"LỖI: Tool '{tool_name}' không tồn tại trong hệ thống. "
                f"Các tool hợp lệ gồm: {valid}.")
    try:
        fn = AVAILABLE_TOOLS[tool_name]
        return fn(*args)
    except TypeError as te:
        return (f"LỖI: Sai tham số khi gọi tool '{tool_name}': {str(te)}. "
                f"Hãy kiểm tra lại số lượng và kiểu dữ liệu tham số.")
    except Exception as e:
        return f"LỖI không xác định khi chạy tool '{tool_name}': {str(e)}"


# =============================================================================
# 💬 CẤP 2: Chatbot Baseline (Không có Tool)
# =============================================================================

def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Chạy Chatbot Baseline (Cấp 2): 1 LLM call duy nhất, 0 tool calls.

    Returns:
        str: Phản hồi của Chatbot
    """
    print(f"\n{'='*60}")
    print(f"💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"{'='*60}")
    print(f"⚙️  System Prompt đang dùng: CHATBOT_BASELINE_PROMPT")

    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)

    print(f"\n🤖 Chatbot trả lời:")
    print(f"   {response}")
    return response


# =============================================================================
# 🤖 CẤP 3: ReAct Agent Loop (Thực sự parse + execute + observe)
# =============================================================================

def run_react_agent(user_query: str, provider) -> str:
    """
    Chạy ReAct Agent Loop (Cấp 3):
      1. Gọi LLM với system prompt + history
      2. Parse Action từ output LLM
      3. Execute Tool thực tế
      4. Append Observation vào history
      5. Lặp lại cho đến khi có Final Answer hoặc đạt MAX_ITERATIONS

    Returns:
        str: Final Answer của Agent, hoặc GUARDRAIL_MESSAGE nếu hết bước
    """
    print(f"\n{'='*60}")
    print(f"🤖 [REACT AGENT] Câu hỏi: {user_query}")
    print(f"{'='*60}")

    # History: chuỗi conversation tích lũy (system prompt + các bước)
    history = f"Question: {user_query}\n"
    final_answer = None
    consecutive_errors = 0  # Đếm lỗi liên tiếp để kích hoạt guardrail sớm

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Bước {step}/{MAX_ITERATIONS} ---")

        # Gọi LLM với toàn bộ history
        llm_input = history
        llm_output = provider.generate(llm_input, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"📝 LLM output:\n{llm_output}")

        # Kiểm tra Final Answer trước
        final = parse_final_answer(llm_output)
        if final:
            print(f"\n✅ FINAL ANSWER TÌM THẤY!")
            print(f"🏁 Final Answer: {final}")
            final_answer = final
            history += f"{llm_output}\n"
            break

        # Parse Action
        parsed = parse_action(llm_output)

        if not parsed:
            # LLM không sinh ra Action hợp lệ — thêm nhắc nhở vào history
            error_msg = "LỖI PARSE: Không tìm thấy Action hợp lệ. Hãy dùng đúng định dạng: Action: tool_name[\"arg\"]"
            print(f"⚠️  {error_msg}")
            history += f"{llm_output}\nObservation: {error_msg}\n"
            consecutive_errors += 1
        else:
            tool_name, args = parsed
            print(f"🛠️  Calling Tool: {tool_name}({args})")

            # Execute tool
            observation = execute_tool(tool_name, args)
            print(f"👁️  Observation: {observation}")

            # Kiểm tra lỗi từ tool
            if observation.startswith("LỖI"):
                consecutive_errors += 1
            else:
                consecutive_errors = 0  # Reset khi tool thành công

            # Append vào history
            history += f"{llm_output}\nObservation: {observation}\n"

        # Guardrail: dừng sớm nếu lỗi liên tiếp 3 lần
        if consecutive_errors >= 3:
            print(f"\n🛡️  GUARDRAIL EARLY STOP: {consecutive_errors} lỗi liên tiếp. Ngắt an toàn!")
            break

    if not final_answer:
        print(f"\n🛡️  GUARDRAIL TRIGGERED: Đạt giới hạn tối đa {MAX_ITERATIONS} bước.")
        print(f"📢  Fallback message: {GUARDRAIL_MESSAGE}")
        final_answer = GUARDRAIL_MESSAGE

    return final_answer


# =============================================================================
# 🎯 CẤP 4 (BONUS): Autonomous Agent với Planning + Memory
# =============================================================================

class AutonomousAgent:
    """
    🎁 BONUS Cấp 4: Autonomous Agent với:
      - Planning: Tự chia nhỏ mục tiêu phức tạp thành sub-tasks
      - Memory  : Lưu lịch sử hội thoại qua nhiều lượt (multi-turn)

    Khác với ReAct Agent (Cấp 3):
      - ReAct giải quyết 1 câu hỏi trong 1 vòng lặp.
      - Autonomous Agent nhớ ngữ cảnh qua nhiều câu hỏi liên tiếp
        và tự lên kế hoạch (Planning) cho các tác vụ phức tạp hơn.
    """

    def __init__(self, provider):
        self.provider = provider
        self.memory = []          # Long-term memory: list of (role, content)
        self.session_id = "S001"

    def _plan(self, goal: str) -> list:
        """
        Tự chia nhỏ mục tiêu thành danh sách sub-tasks.
        Trong bản demo, Planning được thực hiện bằng heuristics đơn giản.
        """
        sub_tasks = []

        if any(kw in goal.lower() for kw in ["triệu chứng", "đau", "sốt", "chóng mặt", "khó thở"]):
            sub_tasks.append(("get_symptom_advice", "Phân tích triệu chứng → xác định chuyên khoa"))

        if any(kw in goal.lower() for kw in ["đặt lịch", "book", "hẹn"]):
            sub_tasks.append(("check_doctor_schedule", "Kiểm tra lịch trống → chọn slot phù hợp"))
            sub_tasks.append(("book_appointment", "Xác nhận và đặt lịch hẹn"))

        if any(kw in goal.lower() for kw in ["hủy", "cancel"]):
            sub_tasks.append(("cancel_appointment", "Hủy lịch hẹn đã đặt"))

        if not sub_tasks:
            sub_tasks.append(("llm_only", "Trả lời từ kiến thức LLM"))

        return sub_tasks

    def chat(self, user_message: str) -> str:
        """
        Nhận tin nhắn từ người dùng, ghi vào Memory, lập kế hoạch và thực hiện.
        """
        print(f"\n{'='*60}")
        print(f"🧠 [AUTONOMOUS AGENT Cấp 4] Input: {user_message}")
        print(f"📚 Memory hiện tại: {len(self.memory)} lượt hội thoại trước")
        print(f"{'='*60}")

        # Lưu user message vào memory
        self.memory.append(("User", user_message))

        # Planning: chia nhỏ mục tiêu
        plan = self._plan(user_message)
        print(f"\n📋 PLANNING — Kế hoạch thực hiện ({len(plan)} bước):")
        for i, (tool, desc) in enumerate(plan, 1):
            print(f"   Bước {i}: [{tool}] {desc}")

        # Xây dựng context từ memory
        memory_context = ""
        if len(self.memory) > 1:
            memory_context = "\n\n--- LỊCH SỬ HỘI THOẠI TRƯỚC ---\n"
            for role, msg in self.memory[:-1][-4:]:  # Chỉ lấy 4 lượt gần nhất
                memory_context += f"{role}: {msg}\n"
            memory_context += "--- HẾT LỊCH SỬ ---\n\n"

        # Thực thi từng sub-task theo plan
        observations = []
        for tool_name, desc in plan:
            if tool_name == "llm_only":
                continue

            # Extract params từ message (simplified heuristics)
            if tool_name == "get_symptom_advice":
                obs = get_symptom_advice(user_message)
                observations.append(f"[Phân tích triệu chứng] {obs}")
                print(f"   ✅ Bước hoàn thành: {obs[:80]}...")

            elif tool_name == "check_doctor_schedule":
                # Heuristic: tìm chuyên khoa từ observations trước
                specialty = "Nội tổng quát"
                for o in observations:
                    for sp in ["Tim mạch", "Thần kinh", "Nội tổng quát", "Ngoại"]:
                        if sp in o:
                            specialty = sp
                            break
                obs = check_doctor_schedule(specialty, "hôm nay")
                observations.append(f"[Lịch bác sĩ] {obs}")
                print(f"   ✅ Bước hoàn thành: {obs[:80]}...")

            elif tool_name == "book_appointment":
                specialty = "Nội tổng quát"
                for o in observations:
                    for sp in ["Tim mạch", "Thần kinh", "Nội tổng quát", "Ngoại"]:
                        if sp in o:
                            specialty = sp
                            break
                # Tìm tên bệnh nhân trong message
                name_match = re.search(r'tên\s+(?:là\s+)?([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯA-zàáâãèéêìíòóôõùúăđĩũơư\s]+?)(?:\.|,|$)', user_message, re.IGNORECASE)
                patient_name = name_match.group(1).strip() if name_match else "Bệnh nhân"
                obs = book_appointment(patient_name, specialty, "hôm nay", "14:00")
                observations.append(f"[Đặt lịch] {obs}")
                print(f"   ✅ Bước hoàn thành: {obs[:80]}...")

            elif tool_name == "cancel_appointment":
                apt_match = re.search(r'APT-\d+', user_message, re.IGNORECASE)
                apt_id = apt_match.group(0) if apt_match else "APT-UNKNOWN"
                obs = cancel_appointment(apt_id)
                observations.append(f"[Hủy lịch] {obs}")
                print(f"   ✅ Bước hoàn thành: {obs[:80]}...")

        # Gọi LLM tổng hợp kết quả
        obs_context = "\n".join(observations) if observations else "Không có dữ liệu từ tool."
        synthesis_prompt = (
            f"{memory_context}"
            f"Câu hỏi của người dùng: {user_message}\n\n"
            f"Dữ liệu thu thập được:\n{obs_context}\n\n"
            f"Hãy tổng hợp và trả lời người dùng một cách rõ ràng, ân cần và đầy đủ."
        )

        final_response = self.provider.generate(synthesis_prompt, system_prompt=CHATBOT_BASELINE_PROMPT)

        # Lưu response vào memory
        self.memory.append(("Agent", final_response))

        print(f"\n🏁 [AUTONOMOUS AGENT] Final Response:")
        print(f"   {final_response}")
        return final_response


# =============================================================================
# 🧪 CHẠY TOÀN BỘ TEST CASES
# =============================================================================

def run_all_test_cases(provider, mode: str = "both"):
    """
    Chạy toàn bộ 5 test cases, in kết quả so sánh Chatbot vs Agent.

    Args:
        mode: 'chatbot' | 'agent' | 'both'
    """
    tests = load_test_cases()
    print(f"\n{'='*60}")
    print(f"📋 BẮT ĐẦU CHẠY {len(tests)} TEST CASES — Mode: {mode.upper()}")
    print(f"{'='*60}")

    results = []
    for tc in tests:
        tc_id       = tc["id"]
        category    = tc["category"]
        question    = tc["question"]
        expected    = tc["expected_behavior"]

        print(f"\n{'─'*60}")
        print(f"📌 Test Case #{tc_id} [{category}]")
        print(f"❓ Câu hỏi: {question}")
        print(f"🎯 Kỳ vọng: {expected}")

        chatbot_ans = None
        agent_ans   = None

        if mode in ("chatbot", "both"):
            chatbot_ans = run_baseline_chatbot(question, provider)

        if mode in ("agent", "both"):
            agent_ans = run_react_agent(question, provider)

        results.append({
            "id": tc_id,
            "category": category,
            "question": question,
            "chatbot_answer": chatbot_ans,
            "agent_answer":   agent_ans,
        })

    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH {len(results)} TEST CASES")
    print(f"{'='*60}")
    return results


# =============================================================================
# 🚀 MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 VINHEALTH — TRỢ LÝ ĐẶT LỊCH KHÁM BỆNH")
    print("🏫 ĐẠI HỌC VINUNI — BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 60)

    # Khởi tạo LLM Provider
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"\n🔌 Provider: {provider.__class__.__name__} | Model: {model_name}")

    # Tải test cases
    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json")

    # ─────────────────────────────────────────────
    # DEMO 1: Chatbot Baseline vs ReAct Agent
    # Chạy test case #3 (Multi-step, cần 1 Tool)
    # ─────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("🎬 DEMO: Test Case #3 — So sánh Chatbot vs ReAct Agent")
    sample_query = tests[2]["question"]

    print("\n--- ❶ CHẠY CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)

    print("\n--- ❷ CHẠY REACT AGENT ---")
    run_react_agent(sample_query, provider)

    # ─────────────────────────────────────────────
    # NOTE: Để chạy thêm test cases hoặc Bonus Cấp 4,
    # gọi riêng từng hàm để tránh rate limit API:
    #   run_react_agent(tests[4]["question"], provider)  # Edge case #5
    #   autonomous = AutonomousAgent(provider)           # Cấp 4
    #   autonomous.chat("Tôi bị đau đầu...")
    # ─────────────────────────────────────────────

    print(f"\n{'='*60}")
    print("✅ KẾT THÚC DEMO — Cảm ơn bạn đã sử dụng VinHealth Agent!")
    print(f"{'='*60}")
