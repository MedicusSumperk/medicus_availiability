"""Handoff can run while both proposal and direct appointment writes are disabled."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fastapi.testclient import TestClient
import api_server as api
from handoff_config import durable_handoff_enabled, handoff_store
from handoff_delivery import deliver_one


class IndependentHandoffTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.config = {
            'enable_durable_handoff': True, 'enable_staff_approval': False,
            'enable_appointment_writes': False, 'enable_appointment_cancellations': False,
            'approval_store_path': str(Path(tmp.name) / 'handoff.sqlite'),
            'operator_tenant_key': 'tenant', 'staff_approval_token': 's' * 40,
            'operator_ingest_url': 'http://127.0.0.1:8100', 'operator_ingest_token': 'test',
        }
        for name, value in [('API_CONFIG', self.config), ('API_TOKEN', 'agent-token')]:
            patcher = patch.object(api, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = TestClient(api.app)
        self.headers = {'Authorization': 'Bearer agent-token', 'X-Conversation-Id': 'call'}
        self.payload = {'mode': 'callback', 'request_id': 'one', 'conversation_summary': 'Staff needed'}

    def test_store_deliver_and_replay_without_medicus_or_staff_review(self):
        handoff_store(self.config)  # Deployment provisions the protected store.
        with patch.object(api, 'connect_to_db') as connect, patch.object(api, 'emit_tool_event'):
            first = self.client.post('/handoff-summary', headers=self.headers, json=self.payload)
            self.assertEqual(first.status_code, 200)
            self.assertTrue(first.json()['stored'])
            store = handoff_store(self.config, existing=True)
            with patch('handoff_delivery.send_event', return_value=True) as send:
                self.assertEqual(deliver_one(store, self.config), 'stored_in_operator')
                self.assertEqual(send.call_args.args[2]['conversation_id'], 'call')
            replay = self.client.post('/handoff-summary', headers=self.headers, json=self.payload)
            self.assertEqual(replay.json()['handoff_id'], first.json()['handoff_id'])
            self.assertEqual(deliver_one(store, self.config), 'idle')
            staff = self.client.get('/staff/proposals', headers={'X-Staff-Token': 's' * 40})
            self.assertEqual(staff.status_code, 503)
            connect.assert_not_called()

    def test_direct_writes_remain_disabled_for_all_actions(self):
        handoff_store(self.config)
        for action in ('create', 'cancel', 'reschedule'):
            with self.subTest(action=action):
                connection = Mock()
                with patch.object(api, 'connect_to_db', return_value=connection), patch.object(api, 'emit_tool_event'):
                    response = self.client.post('/book-appointment', headers=self.headers, json={'action': action})
                self.assertEqual(response.json()['status'], 'writes_not_enabled')
                connection.cursor.return_value.execute.assert_not_called()
                connection.commit.assert_not_called()
                connection.rollback.assert_called_once()

    def test_missing_provisioned_store_fails_without_creating_replacement(self):
        with patch.object(api, 'connect_to_db') as connect:
            response = self.client.post('/handoff-summary', headers=self.headers, json=self.payload)
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Path(self.config['approval_store_path']).exists())
        connect.assert_not_called()

    def test_unauthenticated_request_does_not_create_store(self):
        response = self.client.post('/handoff-summary', json=self.payload)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Path(self.config['approval_store_path']).exists())

    def test_disabled_mode_does_not_claim_storage(self):
        self.config['enable_durable_handoff'] = False
        with patch.object(api, 'emit_tool_event'):
            response = self.client.post('/handoff-summary', headers=self.headers, json=self.payload)
        self.assertFalse(response.json()['stored'])
        self.assertEqual(response.json()['delivery_status'], 'not_queued')
        self.assertFalse(Path(self.config['approval_store_path']).exists())

    def test_worker_requires_existing_store_and_strict_flags(self):
        with self.assertRaises(ValueError):
            handoff_store(self.config, existing=True)
        for value in ('true', 1, False, None):
            self.assertFalse(durable_handoff_enabled({'enable_durable_handoff': value}))
        self.assertTrue(durable_handoff_enabled({'enable_staff_approval': True}))
        for override in ({'approval_store_path': 'relative.sqlite'}, {'operator_tenant_key': ''}):
            with self.assertRaises(ValueError):
                handoff_store({**self.config, **override})


if __name__ == '__main__':
    unittest.main()
