import sys
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from availability_search import (  # noqa: E402
    _effective_weekdays,
    _iter_dates,
    _parse_bool,
    _parse_weekdays,
    compact_options,
)


class AvailabilityFilterTests(unittest.TestCase):
    def test_iter_dates_excludes_weekends_by_default(self):
        days = list(_iter_dates(date(2026, 7, 4), date(2026, 7, 7), False, set()))

        self.assertEqual([day.isoformat() for day in days], ["2026-07-06", "2026-07-07"])
        self.assertEqual([day.isoweekday() for day in days], [1, 2])

    def test_iter_dates_can_include_weekends_explicitly(self):
        days = list(_iter_dates(date(2026, 7, 4), date(2026, 7, 7), True, set()))

        self.assertEqual(
            [day.isoformat() for day in days],
            ["2026-07-04", "2026-07-05", "2026-07-06", "2026-07-07"],
        )

    def test_string_false_does_not_enable_weekends(self):
        self.assertFalse(_parse_bool("false"))
        self.assertFalse(_parse_bool("0"))
        self.assertTrue(_parse_bool("true"))

    def test_weekday_filter_accepts_scalar_or_list(self):
        self.assertEqual(_parse_weekdays("1"), {1})
        self.assertEqual(_parse_weekdays("1, 5"), {1, 5})
        self.assertEqual(_parse_weekdays([1, "5"]), {1, 5})

    def test_effective_weekdays_are_visible_for_debugging(self):
        self.assertEqual(_effective_weekdays(False, set()), [1, 2, 3, 4, 5])
        self.assertEqual(_effective_weekdays(True, set()), [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(_effective_weekdays(False, {2, 4}), [2, 4])

    def test_compact_options_preserves_weekday_fields(self):
        compact = compact_options(
            {
                "ok": True,
                "service": "skin",
                "filters": {},
                "agent_notes": [],
                "options": [
                    {
                        "date": "2026-07-06",
                        "weekday": "Monday",
                        "weekday_iso": 1,
                        "weekday_cs": "pondělí",
                        "start_time": "08:30",
                        "doctor_name": "Mária Bartoňová",
                    }
                ],
            }
        )

        self.assertEqual(compact["options"][0]["weekday_iso"], 1)
        self.assertEqual(compact["options"][0]["weekday_cs"], "pondělí")
        self.assertIn('"weekday_cs":"pondělí"', compact["options_json"])


if __name__ == "__main__":
    unittest.main()
