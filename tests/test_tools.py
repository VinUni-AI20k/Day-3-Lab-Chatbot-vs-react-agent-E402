import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from tools import book_viewing, check_viewing_availability, get_rental_details, search_rentals


class RentalToolTests(unittest.TestCase):
    def test_example_homestay_is_found(self):
        result = search_rentals("Hải Châu, Đà Nẵng", 2_500_000, "homestay")
        self.assertIn("PROP-0012", result)
        self.assertIn("17m²", result)

    def test_common_hcm_alias_is_supported(self):
        result = search_rentals("Quận 10, TP.HCM", 3_500_000, "phòng trọ")
        self.assertIn("PROP-0020", result)

    def test_min_price_and_amenities_are_applied(self):
        result = search_rentals(
            "Quận 10, TP.HCM",
            7_000_000,
            "căn hộ mini",
            6_000_000,
            ["khóa vân tay", "thang máy"],
        )
        self.assertIn("PROP-0008", result)

    def test_invalid_calendar_date_is_rejected(self):
        result = check_viewing_availability("PROP-0001", "31/02/2026")
        self.assertTrue(result.startswith("LỖI:"))

    def test_availability_can_list_all_dates(self):
        result = check_viewing_availability("PROP-0001")
        self.assertIn("15:30 ngày 26/08/2026", result)

    def test_invalid_parameter_types_return_errors_instead_of_raising(self):
        self.assertTrue(get_rental_details(12).startswith("LỖI:"))
        self.assertTrue(check_viewing_availability(12).startswith("LỖI:"))
        self.assertTrue(
            book_viewing("PROP-0001", "26/08/2026", None, "Hoàng", "0912345678").startswith("LỖI:")
        )


if __name__ == "__main__":
    unittest.main()
