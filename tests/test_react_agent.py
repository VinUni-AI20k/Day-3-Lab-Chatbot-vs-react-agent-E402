import sys
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app import (  # noqa: E402
    execute_tool,
    load_test_cases,
    parse_react_response,
    run_react_agent,
)
from providers import MockProvider  # noqa: E402


class SequenceProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.prompts = []

    def generate(self, prompt, system_prompt=""):
        self.prompts.append(prompt)
        return next(self.responses)


class RepeatingProvider:
    def generate(self, prompt, system_prompt=""):
        return (
            "Thought: Tôi thử lấy lại cùng hồ sơ.\n"
            'Action: get_user_profile["current_user"]'
        )


class AlwaysMalformedProvider:
    def generate(self, prompt, system_prompt=""):
        return "Đây là phản hồi không theo định dạng ReAct."


class ReactParserTests(unittest.TestCase):
    def test_parser_reads_nested_literal_arguments(self):
        decision = parse_react_response(
            "Thought: Cần tính điểm.\n"
            'Action: calculate_compatibility["current_user", ["Mai", "Lan"]]'
        )
        self.assertIsNone(decision.error)
        self.assertEqual(decision.action_name, "calculate_compatibility")
        self.assertEqual(decision.action_args, ("current_user", ["Mai", "Lan"]))

    def test_parser_reads_final_answer(self):
        decision = parse_react_response(
            "Thought: Đã đủ dữ liệu.\nFinal Answer: Mai phù hợp nhất."
        )
        self.assertEqual(decision.final_answer, "Mai phù hợp nhất.")
        self.assertIsNone(decision.action_name)

    def test_parser_rejects_malformed_action(self):
        decision = parse_react_response(
            'Thought: Thử gọi tool.\nAction: get_user_profile["current_user"'
        )
        self.assertIn("sai cú pháp", decision.error)


class ToolExecutorTests(unittest.TestCase):
    def test_executor_rejects_unknown_tool(self):
        observation, executed = execute_tool("unknown_tool", ())
        self.assertFalse(executed)
        self.assertIn("không tồn tại", observation)

    def test_executor_rejects_wrong_argument_count(self):
        observation, executed = execute_tool(
            "get_user_profile",
            ("current_user", "extra"),
        )
        self.assertFalse(executed)
        self.assertIn("không hợp lệ", observation)

    def test_executor_converts_tool_exception_to_observation(self):
        def broken_tool():
            raise RuntimeError("mock failure")

        observation, executed = execute_tool(
            "broken_tool",
            (),
            available_tools={"broken_tool": broken_tool},
        )
        self.assertTrue(executed)
        self.assertIn("lỗi nội bộ", observation)

    def test_executor_enforces_timeout(self):
        def slow_tool():
            time.sleep(0.05)
            return "done"

        observation, executed = execute_tool(
            "slow_tool",
            (),
            available_tools={"slow_tool": slow_tool},
            timeout_seconds=0.001,
        )
        self.assertTrue(executed)
        self.assertIn("timeout", observation)


class ReactLoopTests(unittest.TestCase):
    def run_silently(self, *args, **kwargs):
        with redirect_stdout(StringIO()):
            return run_react_agent(*args, **kwargs)

    def test_observation_is_returned_to_next_llm_prompt(self):
        provider = SequenceProvider(
            [
                (
                    "Thought: Cần lấy hồ sơ.\n"
                    'Action: get_user_profile["current_user"]'
                ),
                (
                    "Thought: Đã có hồ sơ.\n"
                    "Final Answer: Đã truy xuất hồ sơ có căn cứ."
                ),
            ]
        )
        result = self.run_silently(
            "Hãy cho tôi xem hồ sơ của tôi.",
            provider,
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["tool_calls"], 1)
        self.assertIn("Observation:", provider.prompts[1])
        self.assertIn("Profile người dùng: Minh", provider.prompts[1])

    def test_mock_provider_completes_multi_step_path(self):
        question = load_test_cases()[2]["question"]
        result = self.run_silently(question, MockProvider())
        actions = [item.get("action_name") for item in result["trace"]]

        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            actions,
            [
                "get_user_profile",
                "search_candidate_profiles",
                "calculate_compatibility",
                "synthesize_recommendation",
            ],
        )
        self.assertIn("Mai 98/100", result["final_answer"])

    def test_edge_case_stops_without_hallucinating(self):
        question = load_test_cases()[4]["question"]
        result = self.run_silently(question, MockProvider())

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["tool_calls"], 1)
        self.assertIn("không tìm thấy", result["trace"][0]["observation"].lower())
        self.assertIn("không tìm thấy", result["final_answer"].lower())

    def test_malformed_action_can_recover(self):
        provider = SequenceProvider(
            [
                (
                    "Thought: Cần lấy hồ sơ.\n"
                    'Action: get_user_profile["current_user"'
                ),
                (
                    "Thought: Sửa lại cú pháp.\n"
                    'Action: get_user_profile["current_user"]'
                ),
                (
                    "Thought: Đã có dữ liệu.\n"
                    "Final Answer: Đã truy xuất hồ sơ có căn cứ."
                ),
            ]
        )
        result = self.run_silently(
            "Hãy cho tôi xem hồ sơ của tôi.",
            provider,
        )

        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["tool_calls"], 1)
        self.assertTrue(any("LỖI PARSER" in error for error in result["errors"]))

    def test_unknown_tool_can_recover(self):
        provider = SequenceProvider(
            [
                (
                    "Thought: Thử một tool không tồn tại.\n"
                    'Action: lookup_profile["current_user"]'
                ),
                (
                    "Thought: Dùng tên tool hợp lệ từ Observation.\n"
                    'Action: get_user_profile["current_user"]'
                ),
                (
                    "Thought: Đã có dữ liệu.\n"
                    "Final Answer: Đã truy xuất hồ sơ có căn cứ."
                ),
            ]
        )
        result = self.run_silently(
            "Hãy cho tôi xem hồ sơ của tôi.",
            provider,
        )

        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["tool_calls"], 1)
        self.assertTrue(any("không tồn tại" in error for error in result["errors"]))
        self.assertIn("Các tool hợp lệ", provider.prompts[1])

    def test_premature_final_answer_is_rejected_without_evidence(self):
        provider = SequenceProvider(
            [
                (
                    "Thought: Tôi đoán kết quả ngay.\n"
                    "Final Answer: Mai phù hợp nhất với điểm 99/100."
                ),
                (
                    "Thought: Cần lấy dữ liệu làm bằng chứng.\n"
                    'Action: get_user_profile["current_user"]'
                ),
                (
                    "Thought: Đã có dữ liệu.\n"
                    "Final Answer: Đã truy xuất hồ sơ có căn cứ."
                ),
            ]
        )
        result = self.run_silently(
            "Ai là ứng viên phù hợp với hồ sơ của tôi?",
            provider,
        )

        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["tool_calls"], 1)
        self.assertTrue(
            any("chưa có Observation" in error for error in result["errors"])
        )

    def test_repeated_action_triggers_guardrail(self):
        result = self.run_silently(
            "Hãy cho tôi xem hồ sơ của tôi.",
            RepeatingProvider(),
        )

        self.assertEqual(result["status"], "guardrail")
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["llm_calls"], 2)
        self.assertIn("Action lặp lại", result["stop_reason"])

    def test_max_iterations_triggers_safe_fallback(self):
        result = self.run_silently(
            "Hãy cho tôi xem hồ sơ của tôi.",
            AlwaysMalformedProvider(),
            max_iterations=2,
        )

        self.assertEqual(result["status"], "guardrail")
        self.assertEqual(result["llm_calls"], 2)
        self.assertIn("MAX_ITERATIONS=2", result["stop_reason"])
        self.assertIn("chưa thể hoàn thành", result["final_answer"])


if __name__ == "__main__":
    unittest.main()
