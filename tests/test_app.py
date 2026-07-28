import contextlib
import io
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import app


VALID_TABLE = "\n".join([
    "| Tiêu chí | Ensure |",
    "|---|---|",
    "| Mã sản phẩm | P048 |",
    "| Giá hộp | 750.000 VNĐ |",
    "| Liều dùng | 1-2 ly/ngày |",
    "| Cách dùng | Pha nước ấm |",
    "| Chống chỉ định | Dị ứng sữa bò |",
    "| Chi phí mỗi liều | N/A |",
    "| Chi phí mỗi ngày | N/A |",
    "| Canxi | 500 mg |",
    "| Lưu ý | TPCN không phải thuốc |",
])


class SequenceProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def generate(self, prompt, system_prompt=""):
        self.calls.append((prompt, system_prompt))
        return next(self.responses)


class AppBehaviorTests(unittest.TestCase):
    def quiet_run(self, provider):
        with contextlib.redirect_stdout(io.StringIO()):
            return app.run_react_agent("query", provider)

    def test_parse_error_explains_string_quoting(self):
        with self.assertRaisesRegex(ValueError, "dấu nháy"):
            app.parse_action("Action: search_products[Ensure]")

    def test_tool_dict_is_serialized_as_utf8_json(self):
        output = app.execute_tool(
            "lookup",
            [],
            {"lookup": lambda: {"success": True, "name": "Sữa Ensure"}},
            1,
        )

        self.assertEqual(output, '{"success": true, "name": "Sữa Ensure"}')

    def test_provider_error_stops_after_one_iteration(self):
        provider = SequenceProvider(["[OpenAI Exception]: API unavailable"])

        result = self.quiet_run(provider)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["iterations"], 1)
        self.assertEqual(len(provider.calls), 1)

    def test_repeated_action_is_not_executed_twice(self):
        calls = []
        original_tools = app.AVAILABLE_TOOLS
        app.AVAILABLE_TOOLS = {"ping": lambda value: calls.append(value) or "ok"}
        provider = SequenceProvider([
            'Thought: call\nAction: ping["x"]',
            'Thought: repeat\nAction: ping["x"]',
            f"Thought: done\nFinal Answer: {VALID_TABLE}",
        ])
        try:
            result = self.quiet_run(provider)
        finally:
            app.AVAILABLE_TOOLS = original_tools

        self.assertEqual(result["status"], "success")
        self.assertEqual(calls, ["x"])
        self.assertIn("không được lặp", provider.calls[2][0])

    def test_final_answer_is_reduced_to_one_markdown_table(self):
        provider = SequenceProvider([
            f"Thought: done\nFinal Answer: Mở đầu\n{VALID_TABLE}\nKết luận",
        ])

        result = self.quiet_run(provider)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["final_answer"], VALID_TABLE)

    def test_console_prints_validated_final_table_only_once(self):
        provider = SequenceProvider([
            f"Thought: done\nFinal Answer: {VALID_TABLE}",
        ])
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            app.run_react_agent("query", provider)

        self.assertEqual(output.getvalue().count("| Tiêu chí | Ensure |"), 1)

    def test_ingredient_only_table_is_rejected(self):
        ingredient_only = "| Thành phần | Ensure |\n|---|---|\n| Canxi | 500 mg |"

        with self.assertRaisesRegex(ValueError, "thiếu hàng bắt buộc"):
            app.extract_single_markdown_table(ingredient_only)

    def test_json_escaped_newlines_are_rendered_as_markdown_lines(self):
        escaped_table = VALID_TABLE.replace("\n", r"\n")

        self.assertEqual(app.extract_single_markdown_table(escaped_table), VALID_TABLE)

    def test_multiple_tables_are_rejected_then_retried(self):
        second_table = "| A | B |\n|---|---|\n| 1 | 2 |"
        provider = SequenceProvider([
            f"Thought: done\nFinal Answer: {VALID_TABLE}\n\n{second_table}",
            f"Thought: fixed\nFinal Answer: {VALID_TABLE}",
        ])

        result = self.quiet_run(provider)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["iterations"], 2)
        self.assertIn("đúng một bảng Markdown", provider.calls[1][0])


if __name__ == "__main__":
    unittest.main()
