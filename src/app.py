"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Developer / Integrator)

Chủ đề nhóm: "Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý"

File chính ghép nối tất cả các thành phần của nhóm:
    config/test_cases.json (Role 1) + src/tools.py (Role 2)
    + src/prompts.py (Role 3) + src/providers.py (Multi-Provider Adapter)

⚙️ NGUYÊN TẮC THIẾT KẾ (quan trọng khi bảo vệ bài):
  1. App KHÔNG hardcode tên tool. Danh sách tool được sinh tự động từ
     AVAILABLE_TOOLS ➔ Role 2 đổi tool, app chạy ngay không cần sửa.
  2. LLM chỉ được sinh Thought/Action. Observation do APP chèn vào từ kết
     quả tool thật ➔ chống LLM tự bịa Observation.
  3. Mọi lỗi (sai tên tool, sai tham số, tool crash) đều biến thành
     Observation dạng text để Agent tự đọc và sửa hướng đi.
  4. Có 3 lớp phanh: Safety Gate ➔ Repeated Action ➔ MAX_ITERATIONS.

Cách chạy:
    python src/app.py                 # chạy toàn bộ test case, cả 2 chế độ
    python src/app.py --case 3        # chạy riêng test case số 3
    python src/app.py --mode agent    # chỉ chạy ReAct Agent
    python src/app.py --chat          # chế độ hội thoại trực tiếp (demo/cross-audit)
"""

import argparse
import datetime
import inspect
import json
import os
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
import prompts
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 🛡️ SAFETY GATE — Chủ đề tâm lý bắt buộc phải có lớp chặn khủng hoảng.
# Role 3 có thể ghi đè bằng cách khai báo CRISIS_KEYWORDS / CRISIS_RESPONSE
# trong src/prompts.py; app sẽ tự ưu tiên bản của Role 3.
DEFAULT_CRISIS_KEYWORDS = [
    "tự tử", "tự sát", "muốn chết", "kết thúc cuộc đời", "kết liễu",
    "tự làm hại", "tự hại", "không muốn sống", "biến mất khỏi thế giới",
]

DEFAULT_CRISIS_RESPONSE = (
    "Mình nhận thấy bạn đang nhắc tới việc làm hại bản thân, và mình thật sự "
    "quan tâm đến điều đó.\n"
    "Mình là một trợ lý AI trong bài tập học thuật, mình KHÔNG đủ khả năng thay thế "
    "chuyên gia trong tình huống này.\n"
    "Hãy liên hệ ngay với người bạn tin tưởng, hoặc:\n"
    "  • Cấp cứu y tế: 115\n"
    "  • Đường dây nóng Ngày Mai (hỗ trợ tâm lý): 096 306 1414\n"
    "  • Phòng Tham vấn Tâm lý học đường của trường bạn\n"
    "Bạn xứng đáng được lắng nghe bởi một con người thật."
)

CRISIS_KEYWORDS = getattr(prompts, "CRISIS_KEYWORDS", DEFAULT_CRISIS_KEYWORDS)
CRISIS_RESPONSE = getattr(prompts, "CRISIS_RESPONSE", DEFAULT_CRISIS_RESPONSE)


# =============================================================================
# 1. NẠP DỮ LIỆU & SINH TOOL MANIFEST
# =============================================================================

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1."""
    config_path = os.path.join(BASE_DIR, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_tool_manifest() -> str:
    """
    Sinh bảng mô tả tool ngay tại runtime từ dictionary AVAILABLE_TOOLS.

    Nhờ hàm này, System Prompt luôn khớp 100% với code thật của Role 2.
    Nếu Role 2 thêm/xóa/đổi tên tool, Agent biết ngay mà không ai phải sửa prompt.
    """
    lines = []
    for idx, (name, fn) in enumerate(AVAILABLE_TOOLS.items(), start=1):
        params = ", ".join(inspect.signature(fn).parameters.keys())
        doc = (inspect.getdoc(fn) or "Chưa có mô tả.").strip().splitlines()[0]
        lines.append(f"{idx}. {name}[{params}]: {doc}")
    return "\n".join(lines) if lines else "(Chưa có tool nào được đăng ký!)"


def build_react_prompt() -> str:
    """Ghép System Prompt của Role 3 với bảng tool thật đang được đăng ký."""
    return (
        f"{REACT_SYSTEM_PROMPT}\n\n"
        "=== DANH SÁCH TOOL THỰC TẾ ĐANG ĐƯỢC ĐĂNG KÝ TRONG HỆ THỐNG ===\n"
        f"{build_tool_manifest()}\n\n"
        "RÀNG BUỘC:\n"
        "- Chỉ được gọi tool có tên trong danh sách trên, đúng số lượng tham số.\n"
        "- Mỗi lượt trả lời chỉ được sinh TỐI ĐA 1 dòng Action, rồi dừng lại.\n"
        "- TUYỆT ĐỐI KHÔNG tự viết dòng 'Observation:' — hệ thống sẽ chèn kết quả thật.\n"
        "- Nếu Observation báo LỖI, hãy đổi cách tiếp cận thay vì gọi lại y hệt.\n"
        "- Chỉ trả 'Final Answer:' khi đã có dữ liệu Observation từ tool làm bằng chứng.\n"
    )


# =============================================================================
# 2. PARSER — Bóc tách Action / Final Answer từ output thô của LLM
# =============================================================================

def _split_args(raw: str):
    """Tách chuỗi tham số, tôn trọng dấu nháy: `'A', "B"` ➔ ['A', 'B']."""
    args, buf, quote = [], "", None
    for ch in raw:
        if quote:
            if ch == quote:
                quote = None
            else:
                buf += ch
        elif ch in "\"'":
            quote = ch
        elif ch == ",":
            args.append(buf.strip())
            buf = ""
        else:
            buf += ch
    args.append(buf.strip())
    return [a for a in args if a]


def parse_agent_output(text: str) -> dict:
    """
    Bóc tách output thô của LLM thành 1 trong 3 dạng:
        {"type": "action", "tool": str, "args": list, "thought": str}
        {"type": "final",  "answer": str, "thought": str}
        {"type": "error",  "message": str, "thought": str}

    Chống ảo giác: cắt bỏ mọi thứ từ dòng "Observation:" trở đi, vì Observation
    là việc của hệ thống chứ không phải của LLM.
    """
    text = (text or "").strip()

    clean_lines = []
    for line in text.splitlines():
        if line.strip().lower().startswith("observation"):
            break
        clean_lines.append(line)

    thought = ""
    for line in clean_lines:
        if line.strip().lower().startswith("thought"):
            thought = line.split(":", 1)[-1].strip()
            break

    for i, line in enumerate(clean_lines):
        stripped = line.strip()
        low = stripped.lower()

        if low.startswith("final answer"):
            answer = stripped.split(":", 1)[-1].strip()
            rest = "\n".join(clean_lines[i + 1:]).strip()
            if rest:
                answer = f"{answer}\n{rest}".strip()
            return {"type": "final", "answer": answer, "thought": thought}

        if low.startswith("action"):
            body = stripped.split(":", 1)[-1].strip()
            open_pos = min(
                (body.find(c) for c in "[(" if body.find(c) != -1),
                default=-1,
            )
            if open_pos == -1:
                return {
                    "type": "error", "thought": thought,
                    "message": (
                        f"Không đọc được cú pháp Action: '{body}'. "
                        "Đúng cú pháp phải là: ten_tool[tham_so_1, tham_so_2]"
                    ),
                }
            close_pos = max(body.rfind("]"), body.rfind(")"))
            tool_name = body[:open_pos].strip().strip("`*\"' ")
            raw_args = body[open_pos + 1:close_pos] if close_pos > open_pos else body[open_pos + 1:]
            return {
                "type": "action",
                "tool": tool_name,
                "args": _split_args(raw_args),
                "thought": thought,
            }

    return {
        "type": "error", "thought": thought,
        "message": (
            "Output không chứa dòng 'Action:' hay 'Final Answer:' nào hợp lệ. "
            "Hãy trả lời đúng định dạng ReAct."
        ),
    }


# =============================================================================
# 3. EXECUTOR — Gọi tool thật, mọi lỗi đều trả về text cho Agent đọc
# =============================================================================

def execute_tool(tool_name: str, args: list) -> str:
    """Thực thi tool trong registry. Không bao giờ ném exception ra ngoài."""
    if tool_name not in AVAILABLE_TOOLS:
        valid = ", ".join(AVAILABLE_TOOLS.keys())
        return (
            f"LỖI: Tool '{tool_name}' không tồn tại. "
            f"Các tool hợp lệ gồm: [{valid}]"
        )

    fn = AVAILABLE_TOOLS[tool_name]
    expected = list(inspect.signature(fn).parameters.keys())

    if len(args) != len(expected):
        return (
            f"LỖI: Tool '{tool_name}' cần đúng {len(expected)} tham số "
            f"({', '.join(expected)}) nhưng nhận được {len(args)}. "
            f"Cú pháp đúng: {tool_name}[{', '.join(expected)}]"
        )

    try:
        return str(fn(*args))
    except Exception as e:
        return f"LỖI: Tool '{tool_name}' gặp sự cố khi chạy: {type(e).__name__} - {e}"


def is_provider_error(text: str) -> bool:
    """Nhận diện chuỗi lỗi do providers.py trả về (VD: '[Gemini Error]: ...')."""
    head = (text or "")[:60]
    return head.startswith("[") and ("Error" in head or "Exception" in head)


def check_safety(user_query: str) -> bool:
    """🛡️ Phanh số 1: chặn ngay ở cổng vào nếu có dấu hiệu khủng hoảng."""
    text = user_query.lower()
    return any(kw in text for kw in CRISIS_KEYWORDS)


# =============================================================================
# 4. HAI CHẾ ĐỘ CHẠY: CHATBOT BASELINE & REACT AGENT
# =============================================================================

def run_baseline_chatbot(user_query: str, provider, trace: list = None) -> str:
    """
    Cấp 2 — Chatbot baseline: đúng 1 lần gọi LLM, số lần gọi tool = 0.
    Dùng làm đường cơ sở công bằng để so sánh với Agent.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Trả lời (0 tool call):\n{response}")

    if trace is not None:
        trace.append(f"### 💬 Chatbot Baseline\n**Q:** {user_query}\n\n"
                     f"**A (0 tool call):** {response}\n")
    return response


def run_react_agent(user_query: str, provider, trace: list = None) -> str:
    """
    Cấp 3 — ReAct Agent thật: LLM ➔ Parser ➔ Executor ➔ Observation ➔ lặp lại.

    Trả về câu trả lời cuối cùng (hoặc thông báo fallback lịch sự khi chạm phanh).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    log = [f"Question: {user_query}"]

    # 🛡️ PHANH 1 — SAFETY GATE: chặn trước khi tốn 1 token nào.
    if check_safety(user_query):
        print("🛡️ SAFETY GATE TRIGGERED: Phát hiện nội dung khủng hoảng, dừng Agent.")
        print(f"🏁 Final Answer:\n{CRISIS_RESPONSE}")
        log.append("🛡️ SAFETY GATE TRIGGERED — chặn tại cổng vào, không gọi LLM.")
        log.append(f"Final Answer: {CRISIS_RESPONSE}")
        if trace is not None:
            trace.append("### 🧠 ReAct Agent\n```text\n" + "\n".join(log) + "\n```\n")
        return CRISIS_RESPONSE

    system_prompt = build_react_prompt()
    transcript = f"Question: {user_query}\n"
    seen_actions = {}
    final_answer = None
    provider_failed = False

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        raw = provider.generate(transcript, system_prompt=system_prompt)

        if is_provider_error(raw):
            print(f"❌ Lỗi Provider: {raw}")
            log.append(f"[Step {step}] PROVIDER ERROR: {raw}")
            provider_failed = True
            break

        parsed = parse_agent_output(raw)

        if parsed["thought"]:
            print(f"🧠 Thought: {parsed['thought']}")
            log.append(f"Thought: {parsed['thought']}")

        # --- Trường hợp A: Agent chốt câu trả lời cuối ---
        if parsed["type"] == "final":
            final_answer = parsed["answer"]
            print(f"🏁 Final Answer: {final_answer}")
            log.append(f"Final Answer: {final_answer}")
            break

        # --- Trường hợp B: Agent sinh output sai định dạng ---
        if parsed["type"] == "error":
            observation = parsed["message"]
            print(f"⚠️ Parse Error: {observation}")
            log.append(f"[Parse Error] {observation}")
            transcript += f"{raw.strip()}\nObservation: {observation}\n"
            continue

        # --- Trường hợp C: Agent gọi tool ---
        tool, args = parsed["tool"], parsed["args"]
        action_str = f"{tool}[{', '.join(args)}]"
        print(f"🛠️ Action: {action_str}")
        log.append(f"Action: {action_str}")

        # 🛡️ PHANH 2 — REPEATED ACTION: chặn agent gọi lặp y hệt.
        key = (tool, tuple(args))
        seen_actions[key] = seen_actions.get(key, 0) + 1
        if seen_actions[key] > 1:
            observation = (
                f"LỖI LẶP: Bạn đã gọi {action_str} rồi và kết quả không đổi. "
                "Hãy đổi tham số, đổi tool khác, hoặc trả Final Answer dựa trên "
                "dữ liệu đã có."
            )
            print(f"🛡️ REPEATED ACTION GUARD: {observation}")
        else:
            observation = execute_tool(tool, args)

        print(f"👁️ Observation: {observation}")
        log.append(f"Observation: {observation}")

        # Nối Observation THẬT vào transcript làm ngữ cảnh cho vòng sau
        transcript += f"Thought: {parsed['thought']}\nAction: {action_str}\nObservation: {observation}\n"

    # 🛡️ PHANH 3 — MAX_ITERATIONS: fallback lịch sự thay vì lặp vô tận.
    if final_answer is None:
        if provider_failed:
            final_answer = (
                "Hệ thống chưa kết nối được tới LLM Provider (kiểm tra lại API key "
                "trong file .env). Agent dừng an toàn, không bịa câu trả lời."
            )
            print(f"\n🛑 DỪNG SỚM DO LỖI KẾT NỐI PROVIDER (chưa dùng hết {MAX_ITERATIONS} bước).")
            log.append("🛑 STOP: Lỗi Provider — dừng an toàn, không bịa câu trả lời.")
        else:
            final_answer = (
                f"Xin lỗi, mình đã thử {MAX_ITERATIONS} bước nhưng chưa thu thập đủ "
                "dữ liệu đáng tin cậy để trả lời câu hỏi này. Bạn có thể mô tả rõ hơn, "
                "hoặc trao đổi trực tiếp với chuyên gia tham vấn để được hỗ trợ chính xác."
            )
            print(f"\n🛡️ GUARDRAIL TRIGGERED: Chạm giới hạn {MAX_ITERATIONS} bước — ngắt lặp an toàn!")
            log.append(f"🛡️ GUARDRAIL: Đạt MAX_ITERATIONS={MAX_ITERATIONS}, ngắt lặp an toàn.")
        print(f"🏁 Safe Fallback: {final_answer}")
        log.append(f"Safe Fallback: {final_answer}")

    if trace is not None:
        trace.append("### 🧠 ReAct Agent\n```text\n" + "\n".join(log) + "\n```\n")
    return final_answer


# =============================================================================
# 5. GHI TRACE LOG CHO ROLE 5
# =============================================================================

def save_trace(trace: list, provider_label: str) -> str:
    """Xuất trace log ra file logs/ để Role 5 dán vào docs/trace_eval.md."""
    log_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(log_dir, f"trace_{stamp}.md")
    header = (
        f"# 📊 TRACE LOG — {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"*Provider: {provider_label} · MAX_ITERATIONS = {MAX_ITERATIONS}*\n\n---\n\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(trace))
    return path


# =============================================================================
# 6. ĐIỂM VÀO CHƯƠNG TRÌNH
# =============================================================================

def interactive_chat(provider):
    """Chế độ hội thoại trực tiếp — dùng khi demo & khi bị nhóm bạn cross-audit."""
    print("\n💬 CHẾ ĐỘ HỘI THOẠI TRỰC TIẾP (gõ 'exit' để thoát)")
    while True:
        try:
            query = input("\n👤 Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Kết thúc phiên hội thoại.")
            return
        if query.lower() in {"exit", "quit", "thoat", "thoát"}:
            print("👋 Kết thúc phiên hội thoại.")
            return
        if query:
            run_react_agent(query, provider)


def main():
    parser = argparse.ArgumentParser(description="Lab 3 — Chatbot vs ReAct Agent")
    parser.add_argument("--case", type=int, default=None,
                        help="Chỉ chạy 1 test case theo id (VD: --case 3)")
    parser.add_argument("--mode", choices=["both", "chatbot", "agent"], default="both",
                        help="Chạy chatbot baseline, react agent, hoặc cả hai")
    parser.add_argument("--chat", action="store_true",
                        help="Bật chế độ hội thoại trực tiếp thay vì chạy test case")
    args = parser.parse_args()

    print("=" * 62)
    print("🏫 ĐẠI HỌC VINUNI — BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("🧠 Đề tài: Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý")
    print("=" * 62)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    provider_label = f"{provider.__class__.__name__} ({model_name})"
    print(f"🔌 LLM Provider: {provider_label}")
    print(f"🛠️ Tool đã đăng ký ({len(AVAILABLE_TOOLS)}):\n{build_tool_manifest()}")
    print(f"🛡️ Guardrails: MAX_ITERATIONS={MAX_ITERATIONS} · "
          f"Repeated-Action Guard · Safety Gate ({len(CRISIS_KEYWORDS)} từ khóa)")

    if args.chat:
        interactive_chat(provider)
        return

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} test cases từ config/test_cases.json")

    if args.case is not None:
        tests = [t for t in tests if t.get("id") == args.case]
        if not tests:
            print(f"❌ Không tìm thấy test case id={args.case}")
            return

    trace = []
    for tc in tests:
        question = tc["question"]
        print("\n" + "=" * 62)
        print(f"🧪 TEST CASE #{tc.get('id')} — {tc.get('category', '')}")
        print(f"❓ {question}")
        print(f"🎯 Kỳ vọng: {tc.get('expected_behavior', 'N/A')}")
        print("=" * 62)

        trace.append(f"## 🧪 Test Case #{tc.get('id')} — {tc.get('category', '')}\n"
                     f"**Kỳ vọng:** {tc.get('expected_behavior', 'N/A')}\n")

        if args.mode in ("both", "chatbot"):
            run_baseline_chatbot(question, provider, trace)
        if args.mode in ("both", "agent"):
            run_react_agent(question, provider, trace)

        trace.append("\n---\n")

    path = save_trace(trace, provider_label)
    print(f"\n📄 Đã lưu trace log cho Role 5 tại: {os.path.relpath(path, BASE_DIR)}")


if __name__ == "__main__":
    main()
