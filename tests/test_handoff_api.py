import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fastapi.testclient import TestClient
import api_server as api


class HandoffApiTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.config = {'enable_durable_handoff': True,
                       'approval_store_path': str(Path(tmp.name) / 'queue.sqlite'),
                       'operator_tenant_key': 'test', 'enable_appointment_writes': False}
        for name, value in [('API_CONFIG', self.config), ('API_TOKEN', 'test-token')]:
            patcher = patch.object(api, name, value)
            patcher.start(); self.addCleanup(patcher.stop)
        self.client = TestClient(api.app)
        self.headers = {'Authorization': 'Bearer test-token', 'X-Conversation-Id': 'test-call'}
        self.body = {'request_id': 'request', 'mode': 'callback', 'summary': 'Staff request'}

    def test_store_and_retry_without_database_connection(self):
        api.handoff_store(self.config)  # Deployment provisions the protected store.
        with patch.object(api, 'connect_to_db') as connect:
            first = self.client.post('/handoff-summary', headers=self.headers, json=self.body)
            retry = self.client.post('/handoff-summary', headers=self.headers, json=self.body)
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()['stored'])
        self.assertEqual(first.json()['handoff_id'], retry.json()['handoff_id'])
        connect.assert_not_called()

    def test_missing_identity_and_changed_request_are_rejected(self):
        response = self.client.post('/handoff-summary', headers={'Authorization': 'Bearer test-token'}, json=self.body)
        self.assertEqual(response.status_code, 400)
        api.handoff_store(self.config)
        self.client.post('/handoff-summary', headers=self.headers, json=self.body)
        response = self.client.post('/handoff-summary', headers=self.headers, json={**self.body, 'summary': 'Other request'})
        self.assertEqual(response.status_code, 400)

    def test_disabled_mode_never_claims_persistence(self):
        self.config['enable_durable_handoff'] = False
        response = self.client.post('/handoff-summary', headers=self.headers, json={'mode': 'callback'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['stored'])
        self.assertFalse(Path(self.config['approval_store_path']).exists())

    def test_authentication_fails_closed(self):
        for token in ('', 'CHANGE_ME'):
            with patch.object(api, 'API_TOKEN', token):
                self.assertEqual(self.client.post('/handoff-summary', json=self.body).status_code, 503)
        self.assertEqual(self.client.post('/handoff-summary', json=self.body).status_code, 401)
        self.assertFalse(Path(self.config['approval_store_path']).exists())

    def test_disk_failure_does_not_claim_success_or_disclose_path(self):
        api.handoff_store(self.config)
        with patch.object(api, 'handoff_store', side_effect=OSError('private path')):
            response = self.client.post('/handoff-summary', headers=self.headers, json=self.body)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private path', response.text)


if __name__ == '__main__':
    unittest.main()
