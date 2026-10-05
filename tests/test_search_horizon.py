import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from availability_search import _search_end_date


class SearchHorizonTests(unittest.TestCase):
    def test_calendar_months_not_180_days(self):
        self.assertEqual(_search_end_date(date(2026, 3, 1), {}), date(2026, 9, 1))

    def test_end_of_month_and_leap_year(self):
        self.assertEqual(_search_end_date(date(2026, 8, 31), {}), date(2027, 2, 28))
        self.assertEqual(_search_end_date(date(2027, 8, 31), {}), date(2028, 2, 29))

    def test_future_control_not_capped_from_today(self):
        self.assertEqual(_search_end_date(date(2028, 10, 1), {'date_to': '2028-10-15'}), date(2028, 10, 15))

    def test_patient_end_respected(self):
        self.assertEqual(_search_end_date(date(2026, 10, 2), {'date_to': '2026-10-07'}), date(2026, 10, 7))

    def test_large_request_capped_without_overflow(self):
        self.assertEqual(_search_end_date(date(2026, 10, 2), {'days_ahead': 10**20, 'ensure_first_available': False}), date(2027, 4, 2))

    def test_reversed_range_rejected(self):
        with self.assertRaises(ValueError):
            _search_end_date(date(2026, 10, 2), {'date_to': '2026-10-01'})

    def test_short_window_without_extension(self):
        self.assertEqual(_search_end_date(date(2026, 10, 2), {'days_ahead': 14, 'ensure_first_available': False}), date(2026, 10, 15))
