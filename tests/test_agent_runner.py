import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from scripts.test_runner import run_headless_agent


class SequenceProvider:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate(self, prompt, system_prompt=""):
        return next(self.responses)


class HeadlessAgentTests(unittest.TestCase):
    def test_search_details_and_multiline_final_answer(self):
        provider = SequenceProvider(
            [
                "Thought: Cần tìm homestay.\n"
                "Action: search_rentals['Hải Châu, Đà Nẵng', 2500000, 'homestay']",
                "Thought: Cần lấy chi tiết.\n"
                "Action: get_rental_details['PROP-0012']",
                """Thought: Đã có đầy đủ thông tin.
Final Answer: Qua tìm kiếm, tôi đã tìm thấy căn phù hợp:

- **PROP-0012**
- Diện tích: 17m²
- Địa chỉ: Số 155 ngõ 8 Thạch Thang, Hải Châu, Đà Nẵng
""",
            ]
        )

        result = run_headless_agent("Tìm homestay ở Hải Châu", provider)

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["log"]), 3)
        self.assertIn("PROP-0012", result["final_answer"])
        self.assertIn("17m²", result["final_answer"])
        self.assertIn("Số 155 ngõ 8 Thạch Thang", result["final_answer"])


if __name__ == "__main__":
    unittest.main()
