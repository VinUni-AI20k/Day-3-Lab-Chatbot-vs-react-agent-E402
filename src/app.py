"""Ứng dụng demo: Chatbot baseline vs ReAct Agent cho tuyển dụng."""

import csv
import io
import json
import os
import re
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider, MockProvider

load_dotenv()


def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base_dir, "config", "test_cases.json"), encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(user_query: str, provider) -> str:
    """Chạy đúng một LLM call, tuyệt đối không gọi tool."""
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"💬 [BASELINE] {response}")
    return response


def _candidate_and_position(query: str):
    candidate = (re.search(r"UV\d{3}", query, re.I) or ["UV001"])[0].upper()
    lower = query.lower()
    position = "UI/UX Designer" if "ui/ux" in lower or "designer" in lower else "Backend Developer"
    return candidate, position


def _offline_decision(query: str, observations: list[str]) -> str:
    """Bộ điều phối deterministic để demo offline vẫn giữ chuỗi ReAct thật."""
    candidate, position = _candidate_and_position(query)
    lower = query.lower()
    if not re.search(r"UV\d{3}", query, re.I):
        return "Final Answer: Tôi có thể giải thích quy trình tuyển dụng chung; yêu cầu này không cần tra cứu hồ sơ."
    if not observations:
        return f'Thought: Cần đọc hồ sơ ẩn danh trước khi đánh giá.\nAction: get_candidate_profile["{candidate}"]'
    if len(observations) == 1:
        return f'Thought: Cần đối chiếu hồ sơ với tiêu chí vị trí.\nAction: evaluate_candidate["{candidate}", "{position}"]'
    evaluation = next((item for item in observations if "ĐÁNH GIÁ:" in item), "")
    if "PASS" not in evaluation:
        return "Thought: Hồ sơ chưa đáp ứng tiêu chí đã công bố.\nFinal Answer: Hồ sơ hiện chưa đạt các tiêu chí công việc. HR nên xem xét thủ công hoặc phản hồi về kỹ năng còn thiếu."
    wants_booking = any(word in lower for word in ("đặt lịch", "hẹn phỏng vấn", "mời phỏng vấn"))
    has_consent = any(word in lower for word in ("đồng ý", "xác nhận", "consent"))
    if wants_booking and not has_consent:
        return "Thought: Cần có sự đồng ý rõ ràng của ứng viên trước khi đặt lịch.\nFinal Answer: Ứng viên đạt tiêu chí sơ bộ. Vui lòng xác nhận ứng viên đồng ý nhận lịch trước khi đặt lịch phỏng vấn."
    if wants_booking and has_consent and not any("Lịch trống:" in obs for obs in observations):
        return f'Thought: Ứng viên đạt tiêu chí và đã đồng ý; cần xem lịch trống.\nAction: get_interview_slots["{position}"]'
    if wants_booking and has_consent:
        slot = re.search(r"(SLOT\d+)", observations[-1])
        if slot:
            return f'Thought: Chọn khung giờ trống đầu tiên theo yêu cầu.\nAction: schedule_interview["{candidate}", "{slot.group(1)}"]'
    return "Thought: Đã có bằng chứng từ hồ sơ và tiêu chí.\nFinal Answer: Ứng viên đạt tiêu chí sơ bộ; HR cần xác nhận quyết định cuối cùng."


def _parse_action(reply: str):
    match = re.search(r"Action:\s*([a-zA-Z_]\w*)\s*\[(.*)\]", reply, re.S)
    if not match:
        return None
    try:
        args = next(csv.reader(io.StringIO(match.group(2)), skipinitialspace=True))
        return match.group(1), [arg.strip().strip("'\"") for arg in args]
    except (csv.Error, StopIteration):
        return None


def run_react_agent(user_query: str, provider) -> str:
    """Vòng lặp Thought → Action → Observation có parser, tool registry và guardrail."""
    observations, actions_seen = [], set()
    print(f"\n🤖 [REACT AGENT] {user_query}")
    for step in range(1, MAX_ITERATIONS + 1):
        context = user_query + "\n" + "\n".join(f"Observation: {item}" for item in observations)
        reply = _offline_decision(user_query, observations) if isinstance(provider, MockProvider) else provider.generate(context, REACT_SYSTEM_PROMPT)
        print(f"--- Step {step}/{MAX_ITERATIONS} ---\n{reply}")
        final = re.search(r"Final Answer:\s*(.+)", reply, re.S)
        if final:
            return final.group(1).strip()
        parsed = _parse_action(reply)
        if not parsed:
            observations.append("LỖI: Phản hồi không đúng định dạng Action. Hãy dùng tool hợp lệ hoặc Final Answer.")
            continue
        name, args = parsed
        signature = (name, tuple(args))
        if signature in actions_seen:
            observations.append("LỖI: Action trùng lặp đã bị chặn để tránh lặp vô hạn.")
            continue
        actions_seen.add(signature)
        tool = AVAILABLE_TOOLS.get(name)
        if not tool:
            observations.append(f"LỖI: Tool '{name}' không tồn tại. Tool hợp lệ: {', '.join(AVAILABLE_TOOLS)}.")
            continue
        try:
            observation = tool(*args)
        except TypeError:
            observation = f"LỖI: Tham số không hợp lệ cho tool '{name}'."
        observations.append(observation)
        print(f"Observation: {observation}")
    return f"Không thể hoàn tất an toàn sau {MAX_ITERATIONS} bước. Vui lòng để HR kiểm tra thủ công."


if __name__ == "__main__":
    provider = get_llm_provider()
    tests = load_test_cases()
    print(f"Trợ lý tuyển dụng | Provider: {provider.__class__.__name__} | {len(tests)} test cases")
    for test in tests:
        print(f"\n=== Test #{test['id']}: {test['category']} ===")
        run_baseline_chatbot(test["question"], provider)
        answer = run_react_agent(test["question"], provider)
        print(f"🏁 Final Answer: {answer}")
