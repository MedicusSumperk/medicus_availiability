import copy
import unittest
from datetime import date

from test_pilot_v2_golden import CASES, run_case
from clinic_calendar import public_holidays, is_clinic_workday


class ClinicCalendarTests(unittest.TestCase):
    def test_2026_published_calendar(self):
        # Independent expected dates: CNB, Svátky v České republice, 2026.
        expected = ('01-01', '04-03', '04-06', '05-01', '05-08', '07-05',
                    '07-06', '09-28', '10-28', '11-17', '12-24', '12-25', '12-26')
        self.assertEqual(public_holidays(2026),
                         {date.fromisoformat('2026-' + value) for value in expected})

    def test_movable_holiday_changes_year(self):
        self.assertIn(date(2027, 3, 26), public_holidays(2027))
        self.assertIn(date(2027, 3, 29), public_holidays(2027))
        self.assertNotIn(date(2027, 4, 3), public_holidays(2027))

    def test_no_substitute_monday(self):
        self.assertTrue(is_clinic_workday(date(2026, 12, 28)))
        self.assertFalse(is_clinic_workday(date(2026, 12, 27)))

    def test_schedule_cannot_override_holiday_even_with_emergency_flag(self):
        case = copy.deepcopy(next(c for c in CASES if c['id'] == 'normal_api'))
        request = case['input']['request']
        request.update(date_from='2026-10-28', date_to='2026-10-28', emergency=True)
        for row in case['input']['calendars']:
            row['date'] = '2026-10-28'
        self.assertEqual(run_case(case), {'offers': []})
