import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_store import ApprovalStore
import availability_search as search


class CallLeadTimeTests(unittest.TestCase):
    def test_anchor_survives_reopening_and_is_tenant_scoped(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'calls.sqlite'
            with patch('approval_store.time.time',return_value=100):
                self.assertEqual(ApprovalStore(path).first_seen('t','c'),100)
            with patch('approval_store.time.time',return_value=400):
                store=ApprovalStore(path)
                self.assertEqual(store.first_seen('t','c'),100)
                self.assertEqual(store.first_seen('other','c'),400)

    def options(self, anchor=None, forged=None):
        now=datetime(2026,10,1,8,30,tzinfo=timezone(timedelta(hours=2)))
        availability={'has_schedule':True,'contexts':[{'idprac':1,'slot_interval_minutes':10,
                       'free_slots':['09:20','09:30','09:40']}]}
        with (patch.object(search,'_clinic_now',return_value=now),
              patch.object(search,'load_doctors',return_value=[{'doctor_id':2,'doctor_name':'Test doctor'}]),
              patch.object(search,'compute_day_availability',return_value=availability),
              patch.object(search,'load_dermatoscope_blockers',return_value=[])):
            response=search.search_availability(None,{'service':'skin','date_from':'2026-10-01',
                'date_to':'2026-10-01','limit':3,'call_started_at':forged},call_started_at=anchor)
        return [o['start_time'] for o in response['options']]

    def test_one_hour_boundary_inclusive(self):
        self.assertEqual(self.options(),['09:30','09:40'])

    def test_followup_search_keeps_original_anchor(self):
        self.assertEqual(self.options(datetime(2026,10,1,8,20,tzinfo=timezone(timedelta(hours=2)))),
                         ['09:20','09:30','09:40'])

    def test_request_body_cannot_backdate_call(self):
        self.assertEqual(self.options(forged='2026-10-01T01:00:00+02:00'),['09:30','09:40'])
