"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
Vòng lặp ReAct (CallLLM -> Parse -> ExecuteTool -> AppendObservation -> lặp) hiện thực
bằng LangGraph StateGraph.

Hỗ trợ 2 phiên bản Agent để so sánh Before/After (Bước 5 — Failed trace -> Agent V2):
  - version="v1": bản gốc. Parser nghiêm ngặt, lỗi tool báo chung chung, không phát hiện
    lặp Action, MAX_ITERATIONS=4 (vừa đủ happy path, không có ngân sách phục hồi).
  - version="v2": bản nâng cấp. Parser linh hoạt (vá được Action thiếu ngoặc đóng),
    Unknown Tool -> liệt kê tool hợp lệ, Malformed Args -> gợi ý cú pháp đúng,
    Repeated Action -> cắt sớm tại MAX_REPEATED_ACTION, MAX_ITERATIONS=6.
"""

import inspect
import json
import os
import re
import sys
from typing import List, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import AVAILABLE_TOOLS, INTERVIEW_SLOTS, normalize_date
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    MAX_REPEATED_ACTION,
    contains_prompt_injection,
    injection_guard_status,
    INJECTION_REFUSAL_MESSAGE,
)
from providers import get_llm_provider

load_dotenv()

# MAX_ITERATIONS của bản V1 gốc — giữ lại để tái hiện failed trace khi so sánh Before/After.
V1_MAX_ITERATIONS = 4


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# 💬 BASELINE CHATBOT — đúng 1 LLM call, 0 tool call
# =============================================================================

def run_baseline_chatbot(user_query: str, provider) -> str:
    """Chatbot Baseline: system prompt + user message -> ĐÚNG MỘT LLM call -> final response.
    Không gọi tool, không nhúng kết quả tool vào prompt, không khẳng định đã thực hiện action.
    Trả về raw answer để Role 5 phân loại (correct / safe fallback / hallucinated)."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


# =============================================================================
# 🤖 REACT AGENT — LangGraph StateGraph
# =============================================================================

class AgentState(TypedDict):
    candidate_name: str
    resume_text: str
    job_description_text: str
    preferred_date: str
    question: str
    history: str
    step: int
    trace: List[dict]
    pending_action: Optional[dict]
    last_observation: Optional[str]
    final_answer: Optional[str]
    stopped: bool
    stop_reason: Optional[str]
    parse_failed: bool
    # --- Agent V2 ---
    version: str
    max_iterations: int
    action_counts: dict
    repeated_blocked: bool
    tool_calls: int
    screening_passed: bool
    screening_completed: bool
    calendar_checked: bool
    checked_date: Optional[str]
    available_slots: List[str]
    booking_confirmed: bool


_THOUGHT_RE = re.compile(r"Thought:\s*(.*)")
_ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(.*?)\]", re.DOTALL)
# V2: vá Action thiếu ngoặc đóng, VD: check_calendar_availability['05/08/2026
_ACTION_UNCLOSED_RE = re.compile(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[([^\]\n]*)$", re.MULTILINE)
_FINAL_RE = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)


def _claims_booking_success(answer: str) -> bool:
    lowered = answer.casefold()
    return any(marker in lowered for marker in ("đã đặt lịch", "đặt lịch thành công", "đã hẹn lịch"))


def _split_args(args_str: str) -> List[str]:
    if not args_str.strip():
        return []
    cleaned = []
    for part in args_str.split(","):
        p = part.strip()
        if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'":
            p = p[1:-1]
        else:
            p = p.strip("\"'")  # vá trường hợp nháy lẻ do Action bị cắt giữa
        cleaned.append(p)
    return cleaned


def _parse_step(raw: str, tolerant: bool = True) -> dict:
    """Parse output LLM thành Thought + (Action | Final Answer).
    Cắt bỏ mọi 'Observation:' mà model tự bịa (model chỉ được sinh 1 bước).
    tolerant=True (V2): vá được Action thiếu ngoặc đóng."""
    text = raw.strip()
    cut_idx = text.find("\nObservation:")
    if cut_idx != -1:
        text = text[:cut_idx]

    thought_match = _THOUGHT_RE.search(text)
    thought = thought_match.group(1).strip() if thought_match else None

    final_match = _FINAL_RE.search(text)
    action_match = _ACTION_RE.search(text)

    if final_match and (not action_match or final_match.start() <= action_match.start()):
        return {
            "thought": thought, "final_answer": final_match.group(1).strip(),
            "action_tool": None, "action_args": [], "syntax_repaired": False,
            "raw_block": text[: final_match.end()].strip(),
        }

    if action_match:
        return {
            "thought": thought, "final_answer": None,
            "action_tool": action_match.group(1).strip(),
            "action_args": _split_args(action_match.group(2)),
            "syntax_repaired": False,
            "raw_block": text[: action_match.end()].strip(),
        }

    # V2: thử vá Action thiếu ngoặc đóng trước khi bỏ cuộc
    if tolerant:
        unclosed = _ACTION_UNCLOSED_RE.search(text)
        if unclosed:
            return {
                "thought": thought, "final_answer": None,
                "action_tool": unclosed.group(1).strip(),
                "action_args": _split_args(unclosed.group(2)),
                "syntax_repaired": True,
                "raw_block": text[: unclosed.end()].strip(),
            }

    return {
        "thought": thought, "final_answer": None, "action_tool": None,
        "action_args": [], "syntax_repaired": False, "raw_block": text,
    }


def guard_input(state: AgentState) -> dict:
    """Guardrails AI trên toàn bộ dữ liệu đầu vào (CV/JD/tên/ngày) TRƯỚC khi đưa vào Agent —
    chặn injection gián tiếp nằm trong CV/JD ngay từ đầu, không tốn vòng lặp LLM nào."""
    combined = "\n".join([
        state["candidate_name"], state["resume_text"],
        state["job_description_text"], state.get("preferred_date", ""),
    ])
    if contains_prompt_injection(combined):
        guard_mode = injection_guard_status()
        return {
            "final_answer": INJECTION_REFUSAL_MESSAGE,
            "stopped": True,
            "stop_reason": "injection",
            "trace": state["trace"] + [{
                "type": "blocked",
                "text": f"{guard_mode} phát hiện dấu hiệu prompt injection trong CV/JD/đầu vào — dừng ngay, không gọi LLM/tool.",
            }],
        }
    return {}


def call_llm_node(provider):
    def call_llm(state: AgentState) -> dict:
        prompt = f"{state['question']}\n\n{state['history']}".strip()
        raw = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = _parse_step(raw, tolerant=(state["version"] == "v2"))

        trace = list(state["trace"])
        if parsed["thought"]:
            trace.append({"type": "thought", "text": parsed["thought"]})

        if parsed["final_answer"] is not None:
            final_answer = parsed["final_answer"]
            if _claims_booking_success(final_answer) and not state["booking_confirmed"]:
                final_answer = (
                    "Tôi chưa thể xác nhận lịch phỏng vấn vì hệ thống chưa nhận được "
                    "Observation đặt lịch thành công."
                )
                trace.append({
                    "type": "system",
                    "text": "Final Answer xác nhận đặt lịch nhưng chưa có booking Observation — đã chặn claim.",
                })
            trace.append({"type": "final", "text": final_answer})
            return {
                "trace": trace,
                "history": state["history"] + parsed["raw_block"] + "\n",
                "step": state["step"] + 1,
                "final_answer": final_answer,
                "stopped": True, "stop_reason": "final",
                "pending_action": None, "parse_failed": False,
            }

        if parsed["action_tool"]:
            if parsed["syntax_repaired"]:
                trace.append({
                    "type": "system",
                    "text": "Agent V2: Action thiếu ngoặc đóng ']' — parser đã tự vá và vẫn thực thi được.",
                })
            trace.append({
                "type": "action",
                "text": f'{parsed["action_tool"]}[{", ".join(parsed["action_args"])}]',
            })
            return {
                "trace": trace,
                "history": state["history"] + parsed["raw_block"] + "\n",
                "step": state["step"] + 1,
                "pending_action": {"tool": parsed["action_tool"], "args": parsed["action_args"]},
                "parse_failed": False,
            }

        trace.append({"type": "system", "text": "Không parse được Thought/Action/Final Answer hợp lệ từ phản hồi LLM."})
        return {
            "trace": trace,
            "history": state["history"] + raw.strip() + "\n",
            "step": state["step"] + 1,
            "pending_action": None, "parse_failed": True,
        }

    return call_llm


def _syntax_hint(tool_name: str) -> str:
    """Sinh gợi ý cú pháp đúng cho một tool từ signature thật của hàm (Agent V2)."""
    tool_fn = AVAILABLE_TOOLS.get(tool_name)
    if tool_fn is None:
        return ""
    if tool_name == "screen_resume":
        return "screen_resume[]"
    params = ", ".join(inspect.signature(tool_fn).parameters)
    return f"{tool_name}[{params}]"


def execute_tool(state: AgentState) -> dict:
    action = state["pending_action"]
    tool_name = action["tool"]
    args = action["args"]
    is_v2 = state["version"] == "v2"

    expected_args = {"screen_resume": 0, "check_calendar_availability": 1, "schedule_interview": 3}
    if tool_name in expected_args and len(args) != expected_args[tool_name]:
        if is_v2:
            return {
                "last_observation": (
                    f"LỖI: Sai số lượng/kiểu tham số khi gọi {tool_name}. "
                    f"Cú pháp đúng: {_syntax_hint(tool_name)}."
                ),
                "action_counts": dict(state.get("action_counts") or {}),
            }

    # --- Agent V2: Repeated Action detection (phanh sớm hơn MAX_ITERATIONS) ---
    action_key = f"{tool_name}[{'|'.join(args)}]"
    counts = dict(state.get("action_counts") or {})
    counts[action_key] = counts.get(action_key, 0) + 1
    if is_v2 and counts[action_key] >= MAX_REPEATED_ACTION:
        return {
            "action_counts": counts,
            "repeated_blocked": True,
            "last_observation": (
                f"LỖI: Agent đã gọi {action_key} tới {counts[action_key]} lần với cùng tham số — "
                "phát hiện kẹt vòng lặp, dừng an toàn."
            ),
        }

    if tool_name == "check_calendar_availability" and not state["screening_completed"]:
        return {"last_observation": "LỖI: Phải chạy screen_resume trước khi kiểm tra lịch.", "action_counts": counts, "stopped": True, "stop_reason": "workflow_blocked"}
    if tool_name == "check_calendar_availability" and not state["screening_passed"]:
        return {"last_observation": "LỖI: Ứng viên chưa đạt yêu cầu, không được kiểm tra hoặc đặt lịch.", "action_counts": counts, "stopped": True, "stop_reason": "workflow_blocked"}
    if tool_name == "schedule_interview":
        if not state["screening_completed"] or not state["screening_passed"]:
            return {"last_observation": "LỖI: Ứng viên phải đạt screen_resume trước khi đặt lịch.", "action_counts": counts, "stopped": True, "stop_reason": "workflow_blocked"}
        if not state["calendar_checked"]:
            return {"last_observation": "LỖI: Phải kiểm tra lịch trống trước khi đặt lịch.", "action_counts": counts, "stopped": True, "stop_reason": "workflow_blocked"}
        requested_date = normalize_date(args[1])
        if requested_date != state["checked_date"]:
            return {"last_observation": "LỖI: Ngày đặt lịch phải trùng với ngày vừa kiểm tra.", "action_counts": counts, "stopped": True, "stop_reason": "workflow_blocked"}
        if args[2].strip() not in state["available_slots"]:
            return {"last_observation": "LỖI: Khung giờ chưa được xác nhận là còn trống.", "action_counts": counts, "stopped": True, "stop_reason": "workflow_blocked"}

    tool_fn = AVAILABLE_TOOLS.get(tool_name)

    if tool_fn is None:
        # --- Unknown Tool ---
        if is_v2:
            obs = (
                f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ gồm: "
                f"[{', '.join(AVAILABLE_TOOLS)}]. Hãy chọn lại đúng tool trong danh sách này."
            )
        else:
            obs = f"LỖI: Agent gọi tool '{tool_name}' không tồn tại trong hệ thống."
        return {"action_counts": counts, "last_observation": obs}

    tool_calls = state.get("tool_calls", 0) + 1
    try:
        if tool_name == "screen_resume":
            # CV/JD lấy từ state, KHÔNG lấy từ tham số LLM tự sinh (tránh vỡ cú pháp
            # bracket khi text dài / có dấu phẩy / xuống dòng).
            obs = tool_fn(state["resume_text"], state["job_description_text"])
        else:
            obs = tool_fn(*args)
    except TypeError as e:
        # --- Malformed Args ---
        if is_v2:
            obs = (
                f"LỖI: Sai số lượng/kiểu tham số khi gọi {tool_name}. "
                f"Cú pháp đúng: {_syntax_hint(tool_name)}. Chi tiết: {e}"
            )
        else:
            obs = f"LỖI: tham số không hợp lệ khi gọi {tool_name}({', '.join(args)}): {e}"
    except Exception as e:
        obs = f"LỖI: {tool_name} gặp sự cố không mong muốn: {e}"

    updates = {"action_counts": counts, "last_observation": obs, "tool_calls": tool_calls}
    if tool_name == "screen_resume":
        updates["screening_completed"] = True
        updates["screening_passed"] = "Kết luận: ĐẠT" in obs and "Kết luận: KHÔNG ĐẠT" not in obs
    elif tool_name == "check_calendar_availability":
        canonical_date = normalize_date(args[0])
        slots = [slot for slot in INTERVIEW_SLOTS if slot in obs]
        updates["calendar_checked"] = bool(canonical_date and slots and not obs.startswith("LỖI:"))
        updates["checked_date"] = canonical_date if updates["calendar_checked"] else None
        updates["available_slots"] = slots if updates["calendar_checked"] else []
    elif tool_name == "schedule_interview" and obs.startswith("Đã đặt lịch"):
        updates["booking_confirmed"] = True
    return updates


def append_observation(state: AgentState) -> dict:
    obs = state["last_observation"] or ""
    return {
        "trace": state["trace"] + [{"type": "observation", "text": obs}],
        "history": state["history"] + f"Observation: {obs}\n\n",
        "pending_action": None,
    }


def append_error(state: AgentState) -> dict:
    if state["version"] == "v2":
        obs = (
            "LỖI: Không hiểu định dạng phản hồi trước đó. Hãy sinh lại ĐÚNG MỘT bước theo "
            "cú pháp: 'Thought: ...' rồi 'Action: tên_công_cụ[tham_số]' (đóng đủ ngoặc vuông), "
            "hoặc 'Final Answer: ...' nếu đã đủ dữ liệu."
        )
    else:
        obs = "LỖI: Không hiểu định dạng phản hồi trước đó. Hãy suy luận lại đúng theo format Thought/Action/Final Answer."
    return {
        "trace": state["trace"] + [{"type": "observation", "text": obs}],
        "history": state["history"] + f"Observation: {obs}\n\n",
        "parse_failed": False,
    }


def safe_fallback(state: AgentState) -> dict:
    if state.get("final_answer"):
        return {}

    if state.get("stop_reason") == "workflow_blocked":
        reason = "workflow_blocked"
        note = "Agent bị chặn vì vi phạm thứ tự hoặc điều kiện nghiệp vụ của workflow HR."
        answer = "Xin lỗi, tôi không thể tiếp tục vì yêu cầu chưa đáp ứng điều kiện sàng lọc hoặc lịch phỏng vấn."
    elif state.get("repeated_blocked"):
        reason = "repeated_action"
        note = (
            f"Agent lặp lại cùng một Action quá {MAX_REPEATED_ACTION} lần — "
            "Guardrail Repeated Action cắt sớm (Agent V2)."
        )
        answer = (
            "Xin lỗi, tôi bị kẹt khi thực hiện cùng một thao tác nhiều lần mà không có tiến triển. "
            "Vui lòng kiểm tra lại thông tin đầu vào (đặc biệt là ngày phỏng vấn) rồi thử lại."
        )
    else:
        reason = "max_iterations"
        limit = state["max_iterations"]
        note = f"Đạt giới hạn {limit} vòng lặp Thought-Action — dừng an toàn (Guardrail MAX_ITERATIONS)."
        answer = (
            f"Xin lỗi, tôi chưa thể hoàn tất yêu cầu trong giới hạn {limit} bước xử lý. "
            "Vui lòng thử lại hoặc cung cấp thông tin cụ thể hơn."
        )

    return {
        "final_answer": answer,
        "stopped": True,
        "stop_reason": reason,
        "trace": state["trace"] + [{"type": "blocked", "text": note}],
    }


def route_guard(state: AgentState) -> str:
    return "blocked" if state.get("stopped") else "ok"


def route_after_llm(state: AgentState) -> str:
    if state.get("stopped"):
        return "final"
    if state.get("parse_failed"):
        return "parse_error"
    if state.get("pending_action"):
        return "action"
    return "parse_error"


def route_budget(state: AgentState) -> str:
    if state.get("stopped") or state.get("repeated_blocked"):
        return "exhausted"
    return "continue" if state["step"] < state["max_iterations"] else "exhausted"


def build_react_graph(provider=None):
    """Dựng và compile LangGraph StateGraph cho vòng lặp ReAct Agent.
    Phiên bản (v1/v2) và max_iterations được đọc từ state, xem make_initial_state()."""
    llm_provider = provider or get_llm_provider()

    g = StateGraph(AgentState)
    g.add_node("guard_input", guard_input)
    g.add_node("call_llm", call_llm_node(llm_provider))
    g.add_node("execute_tool", execute_tool)
    g.add_node("append_observation", append_observation)
    g.add_node("append_error", append_error)
    g.add_node("safe_fallback", safe_fallback)

    g.add_edge(START, "guard_input")
    g.add_conditional_edges("guard_input", route_guard, {"blocked": END, "ok": "call_llm"})
    g.add_conditional_edges(
        "call_llm", route_after_llm, {"final": END, "action": "execute_tool", "parse_error": "append_error"}
    )
    g.add_edge("execute_tool", "append_observation")
    g.add_conditional_edges("append_observation", route_budget, {"continue": "call_llm", "exhausted": "safe_fallback"})
    g.add_conditional_edges("append_error", route_budget, {"continue": "call_llm", "exhausted": "safe_fallback"})
    g.add_edge("safe_fallback", END)

    return g.compile()


def make_initial_state(
    candidate_name: str,
    resume_text: str,
    job_description_text: str,
    preferred_date: str = "",
    version: str = "v2",
) -> AgentState:
    date_hint = f" Ngày mong muốn phỏng vấn nếu đạt yêu cầu: {preferred_date}." if preferred_date else ""
    question = (
        f"Question: Ứng viên {candidate_name} vừa nộp hồ sơ cho vị trí đang tuyển. "
        "Hãy dùng screen_resume để kiểm tra ứng viên có đạt yêu cầu không (CV và JD đã được "
        "nạp sẵn trong hệ thống). Nếu đạt yêu cầu, hãy đặt lịch phỏng vấn." + date_hint
    )
    return {
        "candidate_name": candidate_name,
        "resume_text": resume_text,
        "job_description_text": job_description_text,
        "preferred_date": preferred_date,
        "question": question,
        "history": "",
        "step": 0,
        "trace": [],
        "pending_action": None,
        "last_observation": None,
        "final_answer": None,
        "stopped": False,
        "stop_reason": None,
        "parse_failed": False,
        "version": version,
        "max_iterations": V1_MAX_ITERATIONS if version == "v1" else MAX_ITERATIONS,
        "action_counts": {},
        "repeated_blocked": False,
        "tool_calls": 0,
        "screening_passed": False,
        "screening_completed": False,
        "calendar_checked": False,
        "checked_date": None,
        "available_slots": [],
        "booking_confirmed": False,
    }


_TRACE_ICON = {"thought": "🧠", "action": "🛠️", "observation": "👁️", "final": "🏁", "blocked": "🛡️", "system": "ℹ️"}
_TRACE_LABEL = {
    "thought": "Thought", "action": "Action", "observation": "Observation",
    "final": "Final Answer", "blocked": "GUARDRAIL", "system": "System",
}


def run_react_agent(
    candidate_name: str, resume_text: str, job_description_text: str,
    preferred_date: str, provider, version: str = "v2",
):
    """Chạy ReAct Agent (LangGraph) và in từng bước Thought/Action/Observation ra console."""
    print(f"\n🤖 [REACT AGENT {version.upper()}] Ứng viên: {candidate_name}")
    graph = build_react_graph(provider)
    state = make_initial_state(candidate_name, resume_text, job_description_text, preferred_date, version)

    seen = 0
    final_state = state
    for snapshot in graph.stream(state, stream_mode="values"):
        for entry in snapshot["trace"][seen:]:
            icon = _TRACE_ICON.get(entry["type"], "•")
            label = _TRACE_LABEL.get(entry["type"], entry["type"])
            print(f"{icon} {label}: {entry['text']}")
        seen = len(snapshot["trace"])
        final_state = snapshot

    print(f"   └─ stop_reason={final_state.get('stop_reason')} | steps={final_state.get('step')} | tool_calls={final_state.get('tool_calls')}")
    return final_state


if __name__ == "__main__":
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("🗂️  Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn")
    print("=" * 60)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json")

    print("\n" + "=" * 60)
    print("BƯỚC 2 — CHATBOT BASELINE trên toàn bộ test cases (1 LLM call, 0 tool call)")
    print("=" * 60)
    for tc in tests:
        print(f"\n--- Test case #{tc['id']} | {tc['category']} ---")
        run_baseline_chatbot(tc["question"], provider)

    print("\n" + "=" * 60)
    print("BƯỚC 4 — REACT AGENT trên các test case cần tool")
    print("=" * 60)
    for tc in tests:
        if not tc.get("needs_agent"):
            print(f"\n--- Test case #{tc['id']} | BỎ QUA ReAct (câu Q&A lý thuyết, Chatbot đủ dùng) ---")
            continue
        print(f"\n--- Test case #{tc['id']} | {tc['category']} ---")
        run_react_agent(
            tc["candidate_name"], tc["resume_text"], tc["job_description_text"],
            tc.get("preferred_date", ""), provider,
        )
