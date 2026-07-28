import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from app import load_test_cases, run_baseline_chatbot  # noqa: E402


class CountingProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, prompt, system_prompt=""):
        self.calls += 1
        return "Phản hồi kiểm thử."


class BaselineTests(unittest.TestCase):
    def test_first_five_cases_cover_milestone_two(self):
        test_cases = load_test_cases()
        self.assertGreaterEqual(len(test_cases), 5)
        self.assertEqual([case["id"] for case in test_cases[:5]], [1, 2, 3, 4, 5])

    def test_baseline_uses_one_llm_call_and_no_tools(self):
        provider = CountingProvider()
        with redirect_stdout(StringIO()):
            result = run_baseline_chatbot("Câu hỏi kiểm thử", provider)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(result["llm_calls"], 1)
        self.assertEqual(result["tool_calls"], 0)


if __name__ == "__main__":
    unittest.main()
