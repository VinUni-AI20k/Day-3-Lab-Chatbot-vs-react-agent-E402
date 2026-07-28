import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from agent_protocol import extract_final_answer, parse_action


class AgentProtocolTests(unittest.TestCase):
    def test_multiline_final_answer_is_not_truncated(self):
        response = """Thought: Đã có đầy đủ thông tin.
Final Answer: Qua tìm kiếm, tôi đã tìm thấy căn phù hợp sau:

- **PROP-0012**: Homestay đẹp tại Thạch Thang
- Diện tích: 17m²
- Địa chỉ: Số 155 ngõ 8 Thạch Thang, Hải Châu, Đà Nẵng
"""

        answer = extract_final_answer(response)

        self.assertIn("Qua tìm kiếm", answer)
        self.assertIn("PROP-0012", answer)
        self.assertIn("17m²", answer)
        self.assertTrue(answer.endswith("Đà Nẵng"))

    def test_markdown_final_marker_is_supported(self):
        response = "Thought: Xong.\n**Final Answer:**\n- Dòng một\n- Dòng hai"
        self.assertEqual(extract_final_answer(response), "- Dòng một\n- Dòng hai")

        alternate = "**Final Answer**: Nội dung đầy đủ"
        self.assertEqual(extract_final_answer(alternate), "Nội dung đầy đủ")

    def test_python_literal_action(self):
        name, params = parse_action(
            "Action: search_rentals['Hải Châu, Đà Nẵng', 2500000, 'homestay']"
        )
        self.assertEqual(name, "search_rentals")
        self.assertEqual(params, ["Hải Châu, Đà Nẵng", 2500000, "homestay"])

    def test_json_object_action(self):
        name, params = parse_action(
            'Action: get_rental_details[{"rental_id": "PROP-0012"}]'
        )
        self.assertEqual(name, "get_rental_details")
        self.assertEqual(params, {"rental_id": "PROP-0012"})

    def test_action_parser_does_not_consume_later_lines(self):
        response = (
            "Action: get_rental_details['PROP-0012']\n"
            "Final Answer: this line must not become an argument"
        )
        name, params = parse_action(response)
        self.assertEqual(name, "get_rental_details")
        self.assertEqual(params, ["PROP-0012"])


if __name__ == "__main__":
    unittest.main()
