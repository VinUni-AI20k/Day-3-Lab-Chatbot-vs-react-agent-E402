import inspect
import unittest

from src.tools import (
    AVAILABLE_TOOLS,
    TOOL_SCHEMAS,
    book_interview_slot,
    check_calendar,
    get_jd,
    parse_cv,
    score_candidate,
)


class ToolContractTests(unittest.TestCase):
    def test_every_registered_tool_has_schema_and_docstring(self):
        self.assertEqual(set(AVAILABLE_TOOLS), set(TOOL_SCHEMAS))
        for name, function in AVAILABLE_TOOLS.items():
            self.assertTrue(inspect.getdoc(function), name)
            self.assertIn("input", TOOL_SCHEMAS[name])
            self.assertIn("output", TOOL_SCHEMAS[name])
            self.assertIn("error", TOOL_SCHEMAS[name])

    def test_parse_cv(self):
        self.assertIn("CV candidate_001", parse_cv("candidate_001"))
        self.assertTrue(parse_cv("unknown").startswith("L"))
        self.assertTrue(parse_cv("").startswith("L"))

    def test_get_jd(self):
        self.assertIn("Python Backend Developer", get_jd("python_backend"))
        self.assertTrue(get_jd("unknown").startswith("L"))

    def test_score_candidate(self):
        self.assertIn("100/100", score_candidate("candidate_001", "python_backend"))
        self.assertIn("30/100", score_candidate("candidate_002", "python_backend"))
        self.assertTrue(score_candidate("unknown", "python_backend").startswith("L"))

    def test_check_calendar(self):
        self.assertIn("09:00", check_calendar("interviewer_001", "2026-08-01"))
        self.assertTrue(check_calendar("interviewer_001", "2026-13-32").startswith("L"))
        self.assertTrue(check_calendar("interviewer_001", "2026-08-03").startswith("L"))

    def test_book_interview_slot(self):
        result = book_interview_slot(
            "candidate_001", "interviewer_001", "2026-08-01", "09:00"
        )
        self.assertIn("candidate_001", result)
        self.assertTrue(
            book_interview_slot(
                "candidate_001", "interviewer_001", "2026-08-01", "25:99"
            ).startswith("L")
        )
        self.assertTrue(
            book_interview_slot(
                "candidate_001", "interviewer_001", "2026-01-01", "09:00"
            ).startswith("L")
        )


if __name__ == "__main__":
    unittest.main()
