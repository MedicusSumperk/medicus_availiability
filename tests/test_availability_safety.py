import sys
import unittest
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from availability_engine import compute_slots
import availability_search as search


class AvailabilitySafetyTests(unittest.TestCase):
    def test_unresolved_doctor_never_substitutes_other_doctors(self):
        doctors = [{'doctor_id':2,'doctor_name':'Anna Testova'}, {'doctor_id':3,'doctor_name':'Eva Testova'}]
        for doctor_id, name in [(999,None),(None,'Unknown'),(None,'Testova')]:
            matches, details, notes = search._resolve_doctor_filter(doctors,doctor_id,name)
            self.assertEqual(matches,[])
            self.assertIn(details['match_type'],{'not_found','ambiguous'})
    def test_partial_overlap_blocks_entire_slot(self):
        blocks = [(time(15, 30), 30, 10)]
        _, occupied, free = compute_slots(blocks, [(time(15, 45), time(15, 55))])
        self.assertEqual(free, [time(15, 30)])
        self.assertEqual(occupied, [time(15, 40), time(15, 50)])

    def test_adjacent_appointments_do_not_block(self):
        _, _, free = compute_slots([(time(9), 10, 10)], [(time(8, 50), time(9)), (time(9, 10), time(9, 20))])
        self.assertEqual(free, [time(9)])

    def test_slot_must_fit_in_schedule(self):
        _, _, free = compute_slots([(time(9), 15, 10)], [])
        self.assertEqual(free, [time(9)])

    def test_past_scan_blocks_future_doctor_time(self):
        now = datetime(2026, 10, 1, 14, 20, tzinfo=timezone(timedelta(hours=2)))
        self.assertFalse(search._option_is_future({'start_time':'14:30','scan_slot':{'start_time':'14:15'}}, now.date(), now))
        self.assertFalse(search._option_is_future({'start_time':'14:20'}, now.date(), now))
        self.assertTrue(search._option_is_future({'start_time':'14:30'}, now.date(), now))

    def test_search_filters_past_before_candidate_limit(self):
        now = datetime(2026, 10, 1, 14, 20, tzinfo=timezone(timedelta(hours=2)))
        availability = {'has_schedule':True, 'contexts':[{'idprac':1,'slot_interval_minutes':10,'free_slots':['08:00','13:00','14:20','14:30','14:40']}]}
        with patch.object(search, '_clinic_now', return_value=now), patch.object(search, 'load_doctors', return_value=[{'doctor_id':2,'doctor_name':'Test doctor'}]), patch.object(search, 'compute_day_availability', return_value=availability) as load_day, patch.object(search,'load_dermatoscope_blockers',return_value=[]):
            response = search.search_availability(None, {'service':'skin','date_from':'2026-10-01','date_to':'2026-10-01','limit':1}, call_started_at=now-timedelta(hours=1))
            self.assertEqual(response['options'][0]['start_time'], '14:30')
            load_day.reset_mock()
            response = search.search_availability(None, {'service':'skin','date_from':'2026-09-30','date_to':'2026-09-30'})
            self.assertEqual(response['options'], [])
            load_day.assert_not_called()


if __name__ == '__main__':
    unittest.main()
