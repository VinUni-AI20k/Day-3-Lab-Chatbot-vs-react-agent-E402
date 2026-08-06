"""
🚀 CORE AGENT APP — Text-to-SQL trên Goodreads Books
Khớp nối Providers + Tools + Prompts + Parser trong vòng lặp ReAct ĐỘNG:
  Thought → Action (parse) → execute → Observation → append → lặp → Final Answer

Guardrails:
  - MAX_ITERATIONS (chống lặp vô hạn)
  - Repeated action detection (cùng tool+args 2 lần)
  - Tool unknown → inject error cho LLM tự sửa
"""

import json
import os
import sys
from collections import Counter
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from response_parser import parse_response

load_dotenv()


def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def execute_tool(action: str, args: list) -> str:
    """Thực thi tool an toàn, bắt mọi exception trả về string."""
    if action not in AVAILABLE_TOOLS:
        legal = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Tool '{action}' không tồn tại. Tool hợp lệ: {legal}"
    fn = AVAILABLE_TOOLS[action]
    try:
        result = fn(*args)
        if not isinstance(result, str):
            result = str(result)
        if len(result) > 3000:
            result = result[:3000] + f"\n... (cắt, tổng {len(result)} ký tự)"
        return result
    except TypeError as e:
        return f"LỖI args: {e}. Kiểm tra số lượng tham số cho tool '{action}'."
    except Exception as e:
        return f"LỖI khi chạy tool '{action}': {type(e).__name__}: {e}"


def run_baseline_chatbot(user_query: str, provider) -> dict:
    """Chatbot baseline (1 LLM call, không tool)."""
    log = {"type": "baseline", "query": user_query, "response": "", "tool_calls": 0}
    print(f"\n💬 [CHATBOT BASELINE] {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 {response}")
    log["response"] = response
    return log


def run_hybrid_agent(user_query: str, provider, verbose: bool = True) -> dict:
    """
    Chạy bộ định tuyến (Router) để quyết định giữa Chatbot và ReAct Agent.
    Đây là logic cho Hybrid Flowchart (Mốc 4).
    """
    print(f"\n🚦 [HYBRID AGENT] Q: {user_query}")

    # Bước 1: Dùng một LLM call làm Router
    router_prompt = f"""Bạn là một bộ định tuyến (router) thông minh.
    Nhiệm vụ của bạn là phân loại câu hỏi của người dùng thành một trong hai loại:
    1. 'chatbot': Nếu câu hỏi mang tính lý thuyết, hỏi đáp chung, chào hỏi, hoặc không yêu cầu dữ liệu chính xác từ database.
    2. 'agent': Nếu câu hỏi yêu cầu truy vấn dữ liệu (tìm top, lọc, đếm), tra cứu thông tin cụ thể, hoặc cần thực hiện nhiều bước suy luận.

    Câu hỏi người dùng: "{user_query}"

    Chỉ trả lời 'chatbot' hoặc 'agent'.
    """
    decision = provider.generate(router_prompt).strip().lower()
    print(f"🚦 Router decision: '{decision}'")

    # Bước 2: Dựa vào quyết định để chạy hệ thống tương ứng
    if "chatbot" in decision:
        return run_baseline_chatbot(user_query, provider)
    else:
        # Mặc định các trường hợp còn lại (agent, hoặc LLM trả linh tinh) sẽ đi vào ReAct Agent cho an toàn
        return run_react_agent(user_query, provider, verbose=verbose)


def run_react_agent(user_query: str, provider, verbose: bool = True) -> dict:
    """ReAct loop động: LLM suy nghĩ → parse Action → execute → append Observation → lặp."""
    log = {
        "type": "react_agent",
        "query": user_query,
        "steps": [],
        "final_answer": None,
        "loop_count": 0,
        "terminated_by": "max_iterations",
        "tool_calls": 0,
        "tools_used": [],
    }
    print(f"\n🧠 [REACT AGENT] Q: {user_query}")

    scratchpad = ""
    repeated_counter = Counter()

    for step in range(1, MAX_ITERATIONS + 1):
        log["loop_count"] = step
        print(f"\n--- 🔄 Vòng ReAct Step {step}/{MAX_ITERATIONS} ---")

        # Lắp prompt chứa Question + scratchpad
        user_msg = f"Question: {user_query}\n\n{scratchpad}\nThought:"
        if scratchpad:
            user_msg = f"Question: {user_query}\n\n{scratchpad}Thought:"
        else:
            user_msg = f"Question: {user_query}\n\nThought:"

        # Gọi LLM
        try:
            response = provider.generate(user_msg.strip(), system_prompt=REACT_SYSTEM_PROMPT)
        except Exception as e:
            response = f"Thought: LLM exception: {e}\nFinal Answer: Không thể xử lý ngay, thử lại sau."

        # Guardrail: Nếu LLM trả về lỗi API, thoát sớm
        if "exception]:" in response.lower() or "error]:" in response.lower():
            log["final_answer"] = f"Lỗi API từ nhà cung cấp: {response}"
            log["terminated_by"] = "api_error"
            print(f"\n⛔ API Error: {response}")
            log["steps"].append({"step": step, "thought": "API Error", "observation": response})
            break

        if not response or not response.strip():
            response = "Thought: LLM trả rỗng.\nFinal Answer: Chưa sinh được Action, vui lòng thử lại."

        # In raw response để trace
        if verbose:
            for line in response.splitlines():
                if line.strip():
                    print(f"  📜 {line}")

        parsed = parse_response(response)
        thought = parsed["thought"]
        action = parsed["action"]
        args = parsed["args"]
        final = parsed["final_answer"]

        step_record = {
            "step": step,
            "thought": thought,
            "action": action,
            "args": args,
            "observation": None,
            "final_answer": final,
        }

        # 1. Có Final Answer → kết thúc
        if final:
            log["final_answer"] = final
            log["terminated_by"] = "final_answer"
            print(f"\n🏁 Final Answer: {final[:200]}{'...' if len(final) > 200 else ''}")
            log["steps"].append(step_record)
            break

        # 2. Không có Action (LLM xài lung tung) → inject error
        if not action:
            obs = "LỖI: Output không có Action hoặc Final Answer. Tuân thủ Thought + Action hoặc Final Answer."
            scratchpad += f"\n{response}\nObservation: {obs}\n"
            step_record["observation"] = obs
            log["steps"].append(step_record)
            continue

        # 3. Repeated action detection
        action_key = (action, tuple(str(a) for a in args))
        repeated_counter[action_key] += 1
        if repeated_counter[action_key] >= 2:
            obs = f"GUARDRAIL: Action '{action}' lặp {repeated_counter[action_key]} lần với cùng tham số. Đổi cách tiếp cận hoặc trả Final Answer."
            if verbose:
                print(f"  ⚠️ {obs}")
            scratchpad += f"\nThought: {thought}\nAction: {action}[...]\nObservation: {obs}\n"
            step_record["observation"] = obs
            log["steps"].append(step_record)
            if repeated_counter[action_key] >= 3:
                log["terminated_by"] = "repeated_action"
                log["final_answer"] = "Đã thử nhiều cách nhưng chưa giải được. Vui lòng đổi câu hỏi hoặc làm rõ yêu cầu."
                print(f"\n⛔ Guardrail: repeated action → fallback.")
                break
            continue

        # 4. Thực thi tool
        arg_repr = ", ".join(repr(a) if isinstance(a, str) else str(a) for a in args)
        if verbose:
            print(f"🛠️ Calling {action}({arg_repr})")
        obs = execute_tool(action, args)
        log["tool_calls"] += 1
        log["tools_used"].append(action)
        if verbose:
            preview = obs[:200] + ("..." if len(obs) > 200 else "")
            print(f"👁️ Observation: {preview}")

        # Append vào scratchpad
        scratchpad += f"\nThought: {thought}\nAction: {action}[{arg_repr}]\nObservation: {obs}\n"
        step_record["observation"] = obs
        log["steps"].append(step_record)
    else:
        if not log["final_answer"]:
            log["terminated_by"] = "max_iterations"
            log["final_answer"] = "Đã đạt giới hạn suy luận (MAX_ITERATIONS), không thể trả lời đầy đủ. Thu hẹp câu hỏi hoặc thử lại."
            print(f"\n🛡️ GUARDRAIL: chạm MAX_ITERATIONS={MAX_ITERATIONS}.")

    print(f"\n📊 tool_calls={log['tool_calls']}, terminated_by={log['terminated_by']}")
    return log


def run_single_query(user_query: str, mode: str = "agent", verbose: bool = True) -> dict:
    provider = get_llm_provider()
    if mode == "baseline":
        return run_baseline_chatbot(user_query, provider)
    return run_react_agent(user_query, provider, verbose=verbose)


def run_test_cases(test_ids: list = None, mode: str = "agent", verbose: bool = True):
    """Chạy nhiều test case. Mặc định chạy hết."""
    tests = load_test_cases()
    if test_ids is None:
        test_ids = [t["id"] for t in tests]
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock")
    print("=" * 70)
    print("🏫 DAY 3 LAB: Text-to-SQL ReAct Agent (Goodreads Books)")
    print(f"🔌 Provider: {provider.__class__.__name__} (Model: {model_name})")
    print(f"📋 Mode: {mode} | Sẽ chạy test IDs: {test_ids}")
    print("=" * 70)

    results = []
    for test in tests:
        if test["id"] not in test_ids:
            continue
        print(f"\n\n {'='*68}")
        print(f"=== TEST #{test['id']} ({test['category']}) ===")
        print(f"Q: {test['question']}")
        print(f"Expected: {test['expected_behavior']}")
        print(f"{'='*68}")
        if mode == "baseline":
            res = run_baseline_chatbot(test["question"], provider)
        elif mode == "hybrid":
            res = run_hybrid_agent(test["question"], provider, verbose=verbose)
        else:
            res = run_react_agent(test["question"], provider, verbose=verbose)
        results.append({"test_id": test["id"], "category": test["category"], "result": res})

    print("\n\n" + "=" * 70)
    print("=== TỔNG KẾT ===")
    print("=" * 70)
    for r in results:
        res = r["result"]
        if res["type"] == "react_agent":
            fa = (res.get("final_answer") or "")[:100]
            print(f"Test #{r['test_id']:2d}: tool_calls={res['tool_calls']:2d} | terminated={res['terminated_by']:20s} | final={fa}")
        else:
            print(f"Test #{r['test_id']:2d} (baseline): {res['response'][:100]}")
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            run_test_cases()
        elif sys.argv[1] == "--baseline":
            run_test_cases(mode="baseline")
        elif sys.argv[1] == "--ids":
            ids = [int(x) for x in sys.argv[2].split(",")]
            mode = "agent" if len(sys.argv) <= 3 else sys.argv[3].replace("--", "")
            run_test_cases(test_ids=ids, mode=mode)
        elif sys.argv[1] == "--query":
            q = sys.argv[2] if len(sys.argv) > 2 else "Top 5 sách fantasy hay"
            mode = "agent" if len(sys.argv) <= 3 else sys.argv[3].replace("--", "")
            run_single_query(q, mode=mode)
        else:
            print(f"Usage: python app.py [--all | --baseline | --hybrid | --ids 1,2,3 [--hybrid|--baseline] | --query 'QUESTION' [--hybrid|--baseline]]")
            sys.exit(1)
    else:
        run_test_cases()