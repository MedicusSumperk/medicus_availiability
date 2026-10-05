"""Execute context-selection SQL over relational fixtures, no live writes."""
import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from availability_engine import find_schedule_contexts


class ScheduleContextsTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE OBSPRAC (IDUZI, IDPRAC, TYPTYD, DENTYD, OBJED, PLATIOD, PLATIDO)')
        self.db.execute('CREATE TABLE OBSODLIS (IDUZI, IDPRAC, DATUM, OBJED)')
        self.day = date(2026, 6, 25)
        self.db.execute("INSERT INTO OBSPRAC VALUES (2,1,4,4,'A','2026-01-01',NULL)")

    def contexts(self, doctor):
        return find_schedule_contexts(self.db.cursor(), doctor, self.day)

    def test_normal_schedule(self):
        self.assertEqual(self.contexts(2), [{'idprac': 1, 'typtyd': 4, 'dentyd': 4}])

    def test_exception_only_doctor_is_discovered(self):
        # Shape observed in MAIN and LASER on 2007-10-10: no regular context.
        self.db.execute("INSERT INTO OBSODLIS VALUES (1,1,'2026-06-25','A')")
        self.assertEqual(self.contexts(1), [{'idprac': 1, 'typtyd': 4, 'dentyd': 4}])
        self.assertEqual(self.contexts(2), [])

    def test_disabled_exception_does_not_override_procedure_fallback(self):
        self.db.execute("INSERT INTO OBSODLIS VALUES (1,1,'2026-06-25','N')")
        self.assertEqual(len(self.contexts(2)), 1)
        self.assertEqual(self.contexts(1), [])

    def test_override_is_scoped_to_workplace_and_day(self):
        self.db.execute("INSERT INTO OBSODLIS VALUES (1,2,'2026-06-25','A')")
        self.db.execute("INSERT INTO OBSODLIS VALUES (1,1,'2026-06-24','A')")
        self.assertEqual(self.contexts(2), [{'idprac': 1, 'typtyd': 4, 'dentyd': 4}])
