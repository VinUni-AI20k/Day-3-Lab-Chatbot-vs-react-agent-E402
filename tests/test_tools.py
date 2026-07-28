import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import (  # noqa: E402
    AVAILABLE_TOOLS,
    calculate_compatibility,
    get_user_profile,
    search_candidate_profiles,
    synthesize_recommendation,
)


class CupidToolsTests(unittest.TestCase):
    def test_registry_contains_canonical_tool_names(self):
        self.assertEqual(
            set(AVAILABLE_TOOLS),
            {
                "get_user_profile",
                "search_candidate_profiles",
                "calculate_compatibility",
                "synthesize_recommendation",
            },
        )

    def test_get_user_profile_accepts_key_name_and_student_id(self):
        for identifier in ("current_user", "Minh", "2A202601001"):
            with self.subTest(identifier=identifier):
                self.assertIn("Profile người dùng: Minh", get_user_profile(identifier))

    def test_get_user_profile_returns_safe_errors(self):
        self.assertTrue(get_user_profile("missing").startswith("LỖI:"))
        self.assertTrue(get_user_profile(None).startswith("LỖI:"))

    def test_search_candidate_profiles_filters_data(self):
        result = search_candidate_profiles("đọc sách")
        self.assertIn("Mai", result)
        self.assertIn("An", result)
        self.assertIn("Phương", result)
        self.assertNotIn("- Lan", result)

    def test_search_candidate_profiles_handles_no_match_and_invalid_input(self):
        self.assertIn(
            "Không tìm thấy",
            search_candidate_profiles("bạn nam chơi piano, biết nấu ăn và đan len"),
        )
        self.assertTrue(search_candidate_profiles(None).startswith("LỖI:"))

    def test_calculate_compatibility_ranks_candidates(self):
        result = calculate_compatibility("current_user", ["Mai", "Lan", "An"])
        self.assertIn("Mai: 98/100", result)
        self.assertLess(result.index("Mai:"), result.index("Lan:"))
        self.assertLess(result.index("Lan:"), result.index("An:"))

    def test_calculate_compatibility_returns_safe_errors(self):
        self.assertTrue(
            calculate_compatibility("missing", "Mai").startswith("LỖI:")
        )
        self.assertTrue(
            calculate_compatibility("current_user", 123).startswith("LỖI:")
        )
        self.assertTrue(
            calculate_compatibility("current_user", "Nobody").startswith("LỖI:")
        )

    def test_synthesize_recommendation_uses_real_score(self):
        result = synthesize_recommendation("Minh", "Mai")
        self.assertIn("Điểm vector: 98/100", result)
        self.assertIn("Điểm số chỉ hỗ trợ tham khảo", result)
        self.assertTrue(
            synthesize_recommendation("Minh", "Nobody").startswith("LỖI:")
        )


if __name__ == "__main__":
    unittest.main()
