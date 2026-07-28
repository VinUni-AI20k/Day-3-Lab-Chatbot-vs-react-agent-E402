"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

Chạy: python src/app.py [--test-id N] [--mode baseline|react|both] [--version v1|v2]
                         [--provider mock|gemini|openai|anthropic|openrouter] [--quiet]
"""

import argparse
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
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT_V1,
    REACT_SYSTEM_PROMPT_V2,
    MAX_ITERATIONS,
    MAX_REPEATED_ACTION,
    STOP_SEQUENCES,
    SAFE_FALLBACK_MESSAGE,
    ALLOWED_TOOL_NAMES,
)
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


# =============================================================================
# 🤖 CHATBOT BASELINE (Mốc 2 — không có Tool)
# =============================================================================

def run_baseline_chatbot(user_query: str, provider, verbose: bool = True) -> str:
    """Dựng Chatbot gốc (Baseline) không có công cụ."""
    if verbose:
        print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")

    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


# =============================================================================
# 🧠 REACT AGENT — Parsing & Guardrails (Mốc 3 & Mốc 5)
# =============================================================================

# Bắt "Action: ten_tool[{...json...}]" (JSON args không lồng ngoặc nhọn sâu).
_ACTION_PATTERN = re.compile(
    r"Action\s*:\s*([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\{.*?\})?\s*\]", re.DOTALL
)
_FINAL_ANSWER_PATTERN = re.compile(r"Final Answer\s*:\s*(.*)", re.DOTALL)
_THOUGHT_PATTERN = re.compile(
    r"Thought\s*:\s*(.*?)(?=\n\s*(?:Action|Final Answer)\s*:|\Z)", re.DOTALL
)


def _extract_thought(raw_text: str) -> str:
    matches = list(_THOUGHT_PATTERN.finditer(raw_text))
    return matches[-1].group(1).strip() if matches else ""


def _parse_step(raw_text: str) -> dict:
    """Phân tích 1 lượt sinh của LLM thành Action hoặc Final Answer.

    Lấy khớp CUỐI CÙNG trong văn bản (không phải khớp đầu tiên) vì đôi khi
    model lỡ lặp lại vài dòng transcript cũ trước khi viết bước MỚI — bước mới
    luôn là khớp nằm sau cùng.
    """
    action_matches = list(_ACTION_PATTERN.finditer(raw_text))
    final_matches = list(_FINAL_ANSWER_PATTERN.finditer(raw_text))
    last_action = action_matches[-1] if action_matches else None
    last_final = final_matches[-1] if final_matches else None

    if last_final and (not last_action or last_final.start() >= last_action.start()):
        return {"type": "final_answer", "content": last_final.group(1).strip()}
    if last_action:
        return {
            "type": "action",
            "tool": last_action.group(1),
            "args_raw": (last_action.group(2) or "{}").strip(),
        }
    return {"type": "invalid"}


def _build_user_prompt(question: str, scratchpad: str) -> str:
    if not scratchpad:
        return (
            f"Question: {question}\n\n"
            "Đây là bước ĐẦU TIÊN. Hãy viết Thought và Action (hoặc Final Answer nếu đã đủ "
            "căn cứ trả lời ngay) cho bước này, đúng định dạng đã quy định."
        )
    return (
        f"Question: {question}\n\n"
        f"{scratchpad}"
        "Các dòng Thought/Action/Observation ở trên là tiến trình THẬT đã thực hiện. Hãy viết "
        "TIẾP đúng MỘT bước kế tiếp (Thought + Action, hoặc Thought + Final Answer nếu đã đủ "
        "căn cứ). KHÔNG lặp lại các bước đã có ở trên, KHÔNG tự viết dòng Observation."
    )


def _execute_tool(tool_name: str, args_raw: str) -> str:
    """Thực thi 1 Action, trả về Observation. Không bao giờ raise ra ngoài."""
    if tool_name not in ALLOWED_TOOL_NAMES:
        return f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ: {', '.join(ALLOWED_TOOL_NAMES)}."

    try:
        args = json.loads(args_raw)
        if not isinstance(args, dict):
            raise ValueError("Tham số Action phải là một JSON object, vd {\"key\": \"value\"}.")
    except (json.JSONDecodeError, ValueError) as e:
        return f"LỖI: Tham số Action không đúng định dạng JSON hợp lệ ({e}). Hãy sửa lại cú pháp rồi thử lại."

    try:
        return AVAILABLE_TOOLS[tool_name](**args)
    except TypeError as e:
        return f"LỖI: Gọi tool '{tool_name}' sai tham số ({e}). Kiểm tra lại tên/kiểu tham số theo Tool Specs."
    except Exception as e:
        return f"LỖI: Tool '{tool_name}' gặp sự cố khi thực thi: {e}"


def run_react_agent(
    user_query: str,
    provider,
    system_prompt: str,
    max_iterations: int = MAX_ITERATIONS,
    verbose: bool = True,
) -> dict:
    """
    Vòng lặp ReAct Agent thật (Thought -> Action -> Observation) với Guardrails:
    Unknown Tool, Malformed Args, Repeated Action, Max Iterations.

    Returns:
        dict: {"final_answer": str, "trace": list[dict], "guardrail": str | None}
    """
    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    scratchpad = ""
    last_action_signature = None
    repeat_count = 0
    trace = []

    for step in range(1, max_iterations + 1):
        if verbose:
            print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{max_iterations}) ---")

        user_prompt = _build_user_prompt(user_query, scratchpad)
        raw_response = provider.generate(
            user_prompt, system_prompt=system_prompt, stop_sequences=STOP_SEQUENCES
        )
        parsed = _parse_step(raw_response)

        if parsed["type"] == "final_answer":
            print(f"🏁 Final Answer: {parsed['content']}")
            trace.append({"step": step, "type": "final_answer", "content": parsed["content"]})
            return {"final_answer": parsed["content"], "trace": trace, "guardrail": None}

        if parsed["type"] != "action":
            observation = (
                "LỖI: Không đọc được Thought/Action/Final Answer hợp lệ ở bước này. "
                "Hãy tuân thủ đúng định dạng đã quy định."
            )
            if verbose:
                print("🧠 Thought: (không phân tích được định dạng phản hồi)")
                print(f"👁️ Observation: {observation}")
            scratchpad += f"Thought: (không phân tích được)\nObservation: {observation}\n\n"
            trace.append({"step": step, "type": "parse_error", "raw": raw_response})
            continue

        tool_name, args_raw = parsed["tool"], parsed["args_raw"]
        thought_text = _extract_thought(raw_response)
        if verbose:
            print(f"🧠 Thought: {thought_text}")
            print(f"🛠️ Action: {tool_name}[{args_raw}]")

        action_signature = f"{tool_name}::{args_raw}"
        if action_signature == last_action_signature:
            repeat_count += 1
        else:
            repeat_count = 1
            last_action_signature = action_signature

        if repeat_count > MAX_REPEATED_ACTION:
            observation = (
                f"LỖI: Action '{tool_name}' với cùng tham số đã lặp lại {repeat_count} lần liên tiếp "
                "mà không thành công. Hãy đổi tham số hợp lý hơn, đổi sang tool khác, hoặc hỏi lại người dùng."
            )
        else:
            observation = _execute_tool(tool_name, args_raw)

        if verbose:
            print(f"👁️ Observation: {observation}")

        scratchpad += f"Thought: {thought_text}\nAction: {tool_name}[{args_raw}]\nObservation: {observation}\n\n"
        trace.append(
            {
                "step": step,
                "type": "action",
                "thought": thought_text,
                "tool": tool_name,
                "args": args_raw,
                "observation": observation,
            }
        )

    print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {max_iterations} bước mà chưa có Final Answer.")
    print(f"🏁 Final Answer (fallback): {SAFE_FALLBACK_MESSAGE}")
    trace.append({"step": max_iterations, "type": "guardrail_max_iterations"})
    return {"final_answer": SAFE_FALLBACK_MESSAGE, "trace": trace, "guardrail": "max_iterations"}


# =============================================================================
# 🏁 CLI / DEMO
# =============================================================================

def _parse_args():
    parser = argparse.ArgumentParser(description="Chatbot Baseline vs ReAct Agent — Trợ Lý Chọn Quà Tặng")
    parser.add_argument("--test-id", type=int, default=None, help="Chỉ chạy 1 test case theo id (mặc định: chạy hết).")
    parser.add_argument("--mode", choices=["baseline", "react", "both"], default="both", help="Chạy Baseline, ReAct, hay cả hai.")
    parser.add_argument("--version", choices=["v1", "v2"], default="v2", help="v1 = chưa có Recovery Guardrails (Before), v2 = đã có (After).")
    parser.add_argument("--provider", default=None, help="Ghi đè LLM_PROVIDER (mock|gemini|openai|anthropic|openrouter).")
    parser.add_argument("--quiet", action="store_true", help="Chỉ in Final Answer, ẩn chi tiết từng bước Thought/Action/Observation.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    verbose = not args.quiet
    system_prompt = REACT_SYSTEM_PROMPT_V1 if args.version == "v1" else REACT_SYSTEM_PROMPT_V2

    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider(args.provider)
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    print(f"🧭 ReAct Prompt: {'V1 (chưa Recovery)' if args.version == 'v1' else 'V2 (đã có Recovery)'}")

    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    selected_tests = [t for t in tests if t["id"] == args.test_id] if args.test_id else tests
    if not selected_tests:
        print(f"⚠️ Không tìm thấy test case nào có id = {args.test_id}.")
        sys.exit(1)

    for test in selected_tests:
        print("\n" + "=" * 60)
        print(f"📌 TEST #{test['id']} [{test['category']}]")
        print(f"❓ {test['question']}")
        print("=" * 60)

        if args.mode in ("baseline", "both"):
            print("\n--- CHATBOT BASELINE ---")
            run_baseline_chatbot(test["question"], provider, verbose=verbose)

        if args.mode in ("react", "both"):
            print("\n--- REACT AGENT ---")
            run_react_agent(test["question"], provider, system_prompt=system_prompt, verbose=verbose)
