import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from app import GiftAgent


class GiftAgentTests(unittest.TestCase):
    def test_waits_for_budget_before_search(self):
        agent = GiftAgent()
        first = agent.handle_message("Quà sinh nhật cho đồng nghiệp thích cà phê")
        self.assertIn("Ngân sách", first["reply"])
        self.assertEqual(first["trace"]["tool_calls"], ["get_profile_completeness"])
        second = agent.handle_message("Khoảng 400 nghìn")
        self.assertIn("Bộ cà phê drip", second["reply"])
        self.assertIn("search_gifts", second["trace"]["tool_calls"])

    def test_complete_profile_returns_ranked_gifts(self):
        agent = GiftAgent()
        result = agent.handle_message("Quà sinh nhật cho bạn thân thích đọc sách và cà phê, ngân sách 500-800k")
        self.assertEqual(result["trace"]["node"], "rank_and_explain")
        self.assertIn("Hộp quà sách & cà phê", result["reply"])

    def test_empty_catalog_has_safe_fallback(self):
        agent = GiftAgent()
        result = agent.handle_message("Quà sinh nhật cho đồng nghiệp thích nấu ăn, ngân sách 100k")
        self.assertEqual(result["trace"]["node"], "fallback")
        self.assertIn("nới một ràng buộc", result["reply"])


if __name__ == "__main__":
    unittest.main()
