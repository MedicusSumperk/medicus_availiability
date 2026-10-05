import sys
import unittest
from pathlib import Path
from datetime import date, time
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import laser_calendar as laser
from availability_engine import load_appointments


class LaserCalendarTests(unittest.TestCase):
    day = date(2026, 10, 7)
    schedule = [(time(8), 480, 15)]

    def test_october_seventh_both_offered_scans_are_blocked(self):
        busy = [(time(14,45),time(15))]
        self.assertFalse(laser.interval_is_available(self.day,'14:45','15:00',self.schedule,busy))
        self.assertFalse(laser.interval_is_available(self.day,'14:55','15:10',self.schedule,busy))
        self.assertTrue(laser.interval_is_available(self.day,'15:00','15:15',self.schedule,busy))

    def test_schedule_gaps_and_closing_boundary(self):
        blocks = [(time(8),60,15),(time(9,15),60,15)]
        self.assertFalse(laser.interval_is_available(self.day,'08:55','09:20',blocks,[]))
        self.assertFalse(laser.interval_is_available(self.day,'15:50','16:05',self.schedule,[]))
        self.assertFalse(laser.interval_is_available(self.day,'09:00','09:15',[],[]))

    def test_invalid_booking_fails_closed(self):
        with self.assertRaises(laser.ScanCalendarUnavailable):
            laser.interval_is_available(self.day,'09:00','09:15',self.schedule,[(time(9),None)])

    def test_calendar_loads_all_activity_types_and_recurrence(self):
        cursor=Mock();cursor.fetchall.return_value=[(time(14,45),time(15))]
        self.assertEqual(load_appointments(cursor,1,5,self.day),[(time(14,45),time(15))])
        query,args=cursor.execute.call_args.args
        self.assertIn('OBJOBJ_SEL',query)
        self.assertNotIn('IDCINNOSTI',query)
        self.assertEqual(args,(1,5,self.day,self.day))

    def test_missing_config_fails_closed(self):
        with patch.object(laser,'CONFIG_PATH',Path('/not/a/real/config.json')):
            with self.assertRaises(laser.ScanCalendarUnavailable):
                with laser.open_scan_calendar():
                    self.fail('Must not yield unverified calendar')


if __name__=='__main__':unittest.main()
