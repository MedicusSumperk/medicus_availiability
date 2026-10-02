import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from approval_store import ApprovalStore, ProposalConflict, ProposalNotFound
from handoff_delivery import deliver_one, deliver_failure_alert


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store=ApprovalStore(Path(self.tmp.name)/'q.sqlite')
        self.store.store_handoff('t','c','r',{'mode':'callback','summary_for_staff':'Request'})
        self.config={'operator_tenant_key':'t','operator_ingest_url':'http://127.0.0.1:8100','operator_ingest_token':'test'}

    def test_ack_marks_delivered_and_does_not_resend(self):
        response=Mock(status=200); response.read.return_value=b'{"accepted":true,"duplicate":true}'
        with patch('handoff_delivery.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value=response
            self.assertEqual(deliver_one(self.store,self.config),'stored_in_operator')
            self.assertEqual(deliver_one(self.store,self.config),'idle')
            self.assertEqual(opener.return_value.open.call_count,1)

    def test_timeout_retries_after_delay_with_same_event_id(self):
        with patch('approval_store.time.time',return_value=100):
            with patch('handoff_delivery.build_opener') as opener:
                opener.return_value.open.side_effect=TimeoutError()
                self.assertEqual(deliver_one(self.store,self.config),'retry_or_failed')
            self.assertIsNone(self.store.claim_handoff('t'))
        with patch('approval_store.time.time',return_value=110):
            job=self.store.claim_handoff('t')
            self.assertEqual(job['attempts'],2)

    def test_terminal_failure_queues_private_free_alert_and_retries_it(self):
        with self.store.connect() as db:
            db.execute('UPDATE handoff_attempts SET attempts=9')
        with patch('handoff_delivery.send_event',return_value=False):
            self.assertEqual(deliver_one(self.store,self.config),'retry_or_failed')
            self.assertEqual(deliver_failure_alert(self.store,self.config),'failure_alert_retry_pending')
        with self.store.connect() as db:
            self.assertEqual(db.execute('SELECT delivery_state FROM handoffs').fetchone()[0],'failed')
            db.execute('UPDATE handoff_failure_alerts SET next_attempt_at=0')
        reopened=ApprovalStore(self.store.path)
        with patch('handoff_delivery.send_event',return_value=True) as send:
            self.assertEqual(deliver_failure_alert(reopened,self.config),'failure_alert_stored_in_operator')
            self.assertEqual(deliver_failure_alert(reopened,self.config),'idle')
        event=send.call_args.args[2]
        self.assertEqual(event['event_type'],'staff.handoff.delivery_failed')
        self.assertEqual(set(event['data']),{'handoff_id','error_code'})
        self.assertNotIn('Request',str(event))

    def test_manual_recovery_preserves_event_and_audits_previous_attempts(self):
        with self.store.connect() as db:
            db.execute('UPDATE handoff_attempts SET attempts=9')
        with patch('handoff_delivery.send_event',return_value=False):
            deliver_one(self.store,self.config)
        failed=self.store.failed_handoffs('t')
        self.assertEqual(len(failed),1)
        self.assertNotIn('summary',str(failed))
        identity=failed[0]['id']
        with self.assertRaises(ProposalNotFound):
            self.store.requeue_failed_handoff('other',identity,'admin')
        self.store.requeue_failed_handoff('t',identity,'admin')
        with self.assertRaises(ProposalConflict):
            self.store.requeue_failed_handoff('t',identity,'admin')
        with patch('handoff_delivery.send_event',return_value=True) as send:
            self.assertEqual(deliver_one(self.store,self.config),'stored_in_operator')
        self.assertEqual(send.call_args.args[2]['event_id'],identity)
        with self.store.connect() as db:
            event=db.execute('SELECT * FROM handoff_recovery_events').fetchone()
            self.assertEqual(event['actor'],'admin')
            self.assertEqual(event['previous_attempts'],10)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM handoffs').fetchone()[0],1)
        with self.assertRaises(ProposalConflict):
            self.store.requeue_failed_handoff('t',identity,'admin')

    def test_crashed_worker_lease_expires_without_losing_request(self):
        with patch('approval_store.time.time',return_value=100):
            first=self.store.claim_handoff('t'); self.assertIsNone(self.store.claim_handoff('t'))
        with patch('approval_store.time.time',return_value=161):
            second=self.store.claim_handoff('t')
            self.assertEqual(first['id'],second['id'])
            self.assertFalse(self.store.finish_handoff_delivery(first,accepted=True))
            self.assertTrue(self.store.finish_handoff_delivery(second,accepted=True))
