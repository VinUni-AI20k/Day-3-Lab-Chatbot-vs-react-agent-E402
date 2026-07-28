import json
import os
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestCaseConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(
            os.path.join(PROJECT_ROOT, "config", "test_cases.json"),
            encoding="utf-8",
        ) as file:
            cls.test_cases = json.load(file)

    def test_expected_behaviors_use_current_tool_names(self):
        all_expectations = "\n".join(
            case["expected_behavior"] for case in self.test_cases
        )
        self.assertNotIn("get_property_detail", all_expectations)
        self.assertNotIn("get_viewing_slots", all_expectations)

    def test_prop_0012_expectation_matches_dataset(self):
        case = next(case for case in self.test_cases if case["id"] == 26)
        self.assertIn("17m²", case["expected_behavior"])
        self.assertIn("Số 155 ngõ 8 Thạch Thang", case["expected_behavior"])


if __name__ == "__main__":
    unittest.main()
