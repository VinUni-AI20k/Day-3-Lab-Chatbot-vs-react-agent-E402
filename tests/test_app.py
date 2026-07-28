import time
import unittest

from src.app import (
    MAX_ITERATIONS,
    call_model,
    execute_tool,
    load_test_cases,
    parse_agent_response,
    run_react_agent,
)
from src.prompts import MAX_ITERATIONS as PROMPT_MAX_ITERATIONS

CONFIG_CASES = load_test_cases()


class ScriptedProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        self.calls += 1
        if not self.responses:
            raise AssertionError("Unexpected model call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class ParserTests(unittest.TestCase):
    def test_parses_double_braced_json_from_gemini(self):
        response = parse_agent_response(
            "Thought: use score\n"
            "Action: score_candidate\n"
            'Action Input: {{"candidate_id": "candidate_001", '
            '"job_id": "python_backend"}}\nPAUSE'
        )
        self.assertEqual(response.action, "score_candidate")
        self.assertEqual(
            response.action_input,
            {"candidate_id": "candidate_001", "job_id": "python_backend"},
        )
        self.assertIsNone(response.error)

    def test_parses_single_quoted_mapping_without_eval(self):
        response = parse_agent_response(
            "Action: parse_cv\nAction Input: {'candidate_id': 'candidate_001'}"
        )
        self.assertEqual(response.action_input, {"candidate_id": "candidate_001"})

    def test_rejects_incomplete_json(self):
        response = parse_agent_response(
            'Action: parse_cv\nAction Input: {"candidate_id": "candidate_001"'
        )
        self.assertIsNotNone(response.error)
        self.assertIsNone(response.action_input)

    def test_final_answer_wins_after_action_text(self):
        response = parse_agent_response(
            "Action: parse_cv\nAction Input: {}\nFinal Answer: Hoàn tất."
        )
        self.assertEqual(response.final_answer, "Hoàn tất.")


class ToolExecutionTests(unittest.TestCase):
    def test_executes_real_tool(self):
        result = execute_tool("score_candidate", {
            "candidate_id": "candidate_001",
            "job_id": "python_backend",
        })
        self.assertTrue(result.success)
        self.assertIn("100/100", result.observation)

    def test_missing_arguments_are_reported_before_call(self):
        result = execute_tool("score_candidate", {})
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "INVALID_ARGUMENTS")
        self.assertIn("candidate_id", result.observation)
        self.assertIn("job_id", result.observation)

    def test_unknown_tool_does_not_crash(self):
        result = execute_tool("delete_everything", {})
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "UNKNOWN_TOOL")

    def test_empty_and_timeout_outputs_are_handled(self):
        empty = execute_tool("empty", {}, registry={"empty": lambda: ""})
        self.assertEqual(empty.error_code, "EMPTY_TOOL_OUTPUT")

        def slow():
            time.sleep(0.05)
            return "late"

        timeout = execute_tool(
            "slow", {}, registry={"slow": slow}, timeout_seconds=0.001
        )
        self.assertEqual(timeout.error_code, "TOOL_TIMEOUT")


class ModelCallTests(unittest.TestCase):
    def test_transient_503_is_retried(self):
        provider = ScriptedProvider([
            "[Gemini Exception]: 503 UNAVAILABLE",
            "Final Answer: Thành công sau retry.",
        ])
        result = call_model(provider, "history", max_retries=1)
        self.assertEqual(result.attempts, 2)
        self.assertIn("Final Answer", result.text)

    def test_model_exception_returns_clear_error(self):
        provider = ScriptedProvider([RuntimeError("down"), RuntimeError("down")])
        result = call_model(provider, "history", max_retries=1)
        self.assertIsNotNone(result.error)
        self.assertIn("RuntimeError", result.error)


class ReactLoopTests(unittest.TestCase):
    def test_uses_max_iterations_from_prompts(self):
        self.assertEqual(MAX_ITERATIONS, PROMPT_MAX_ITERATIONS)
        self.assertEqual(MAX_ITERATIONS, 3)

    def test_config_case_1_simple_final_answer(self):
        provider = ScriptedProvider([
            "Final Answer: Đánh giá theo năng lực, nhất quán và không phân biệt đối xử."
        ])
        trace = []
        answer = run_react_agent(CONFIG_CASES[0]["question"], provider, verbose=False, trace_sink=trace)
        self.assertIn("nhất quán", answer)
        self.assertFalse(any(event.get("action") for event in trace))

    def test_config_case_2_single_tool(self):
        provider = ScriptedProvider([
            'Action: parse_cv\nAction Input: {"candidate_id": "candidate_001"}',
            "Final Answer: Hồ sơ candidate_001 có Python, SQL và REST API.",
        ])
        trace = []
        answer = run_react_agent(CONFIG_CASES[1]["question"], provider, verbose=False, trace_sink=trace)
        self.assertIn("candidate_001", answer)
        self.assertEqual([event.get("action") for event in trace if event.get("action")], ["parse_cv"])

    def test_config_case_3_three_tool_flow(self):
        provider = ScriptedProvider([
            'Action: parse_cv\nAction Input: {{"candidate_id": "candidate_001"}}',
            'Action: get_jd\nAction Input: {"job_id": "python_backend"}',
            'Action: score_candidate\nAction Input: {{"candidate_id": "candidate_001", "job_id": "python_backend"}}',
            "Final Answer: candidate_001 đạt 100/100; đây là kết quả hỗ trợ sàng lọc.",
        ])
        trace = []
        answer = run_react_agent(CONFIG_CASES[2]["question"], provider, verbose=False, trace_sink=trace)
        actions = [event.get("action") for event in trace if event.get("action")]
        self.assertEqual(actions, ["parse_cv", "get_jd", "score_candidate"])
        self.assertIn("100/100", answer)

    def test_config_case_4_conditional_booking_flow(self):
        provider = ScriptedProvider([
            'Action: score_candidate\nAction Input: {"candidate_id": "candidate_001", "job_id": "python_backend"}',
            'Action: check_calendar\nAction Input: {"interviewer_id": "interviewer_001", "date": "2026-08-01"}',
            'Action: book_interview_slot\nAction Input: {"candidate_id": "candidate_001", "interviewer_id": "interviewer_001", "date": "2026-08-01", "time": "09:00"}',
            "Final Answer: Ứng viên đạt và lịch 09:00 đã được xác nhận.",
        ])
        trace = []
        answer = run_react_agent(CONFIG_CASES[3]["question"], provider, verbose=False, trace_sink=trace)
        actions = [event.get("action") for event in trace if event.get("action")]
        self.assertEqual(actions, ["score_candidate", "check_calendar", "book_interview_slot"])
        self.assertIn("09:00", answer)

    def test_config_case_5_error_stops_dependent_tools(self):
        provider = ScriptedProvider([
            'Action: score_candidate\nAction Input: {"candidate_id": "candidate_999", "job_id": "python_backend"}',
            "Final Answer: Không tìm thấy hồ sơ; không thể tiếp tục đặt lịch.",
        ])
        trace = []
        answer = run_react_agent(CONFIG_CASES[4]["question"], provider, verbose=False, trace_sink=trace)
        actions = [event.get("action") for event in trace if event.get("action")]
        self.assertEqual(actions, ["score_candidate"])
        self.assertNotIn("check_calendar", actions)
        self.assertNotIn("book_interview_slot", actions)
        self.assertIn("không thể", answer.casefold())

    def test_repeated_action_guardrail(self):
        action = 'Action: parse_cv\nAction Input: {"candidate_id": "candidate_001"}'
        provider = ScriptedProvider([action, action, action])
        answer = run_react_agent("repeat", provider, verbose=False)
        self.assertIn("lặp quá 2 lần", answer)

    def test_two_invalid_formats_stop_safely(self):
        provider = ScriptedProvider(["nonsense", "still nonsense"])
        answer = run_react_agent("invalid", provider, verbose=False)
        self.assertIn("sai định dạng hai lần", answer)

    def test_trace_does_not_store_private_thought(self):
        provider = ScriptedProvider([
            "Thought: private reasoning must not be logged\n"
            'Action: parse_cv\nAction Input: {"candidate_id": "candidate_001"}',
            "Final Answer: done",
        ])
        trace = []
        run_react_agent("trace", provider, verbose=False, trace_sink=trace)
        serialized = str(trace)
        self.assertNotIn("private reasoning", serialized)
        self.assertNotIn("thought", serialized.casefold())


if __name__ == "__main__":
    unittest.main()