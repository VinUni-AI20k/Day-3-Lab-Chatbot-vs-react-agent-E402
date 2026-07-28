import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import (  # noqa: E402
    AVAILABLE_TOOLS,
    USER_DATABASE,
    calculate_compatibility,
    get_user_profile,
    search_candidate_profiles,
    synthesize_recommendation,
)

# USER_DATABASE khởi đầu RỖNG (chưa ai nộp form trên web) — các test dưới đây mô
# phỏng trạng thái "người dùng đã nộp form" bằng cách tự seed 1 "current_user"
# tạm thời trong setUp/tearDown, giống hệt cách web/server.py ghi hồ sơ thật.
MINH_PROFILE = {
    "student_id": "2A202601001",
    "name": "Minh",
    "age": 21,
    "gender": "Nam",
    "personality": "Hướng nội, điềm tĩnh",
    "interests": ["đọc sách", "cà phê yên tĩnh", "công nghệ"],
    "goal": "Mối quan hệ nghiêm túc",
    "vector": [0.2, 0.9, 0.8, 0.95],
}


class CupidToolsTests(unittest.TestCase):
    def setUp(self):
        self._original_current_user = USER_DATABASE.get("current_user")
        USER_DATABASE["current_user"] = dict(MINH_PROFILE)

    def tearDown(self):
        if self._original_current_user is None:
            USER_DATABASE.pop("current_user", None)
        else:
            USER_DATABASE["current_user"] = self._original_current_user

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

    def test_get_user_profile_can_read_candidate_by_student_id(self):
        result = get_user_profile("2A202601315")
        self.assertIn("Profile ứng viên: Phương", result)

    def test_get_user_profile_returns_safe_errors(self):
        self.assertTrue(get_user_profile("missing").startswith("LỖI:"))
        self.assertTrue(get_user_profile(None).startswith("LỖI:"))

    def test_get_user_profile_handles_empty_user_database_gracefully(self):
        # Trước khi người dùng nộp form trên web, USER_DATABASE không có "current_user"
        # — tool phải trả về LỖI: sạch sẽ, không được ném KeyError/crash.
        USER_DATABASE.pop("current_user", None)
        result = get_user_profile("current_user")
        self.assertTrue(result.startswith("LỖI:"))

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
