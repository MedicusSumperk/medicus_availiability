import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fastapi.testclient import TestClient
import api_server as api


class ApiAuthTests(unittest.TestCase):
    routes = ['/agent-capabilities', '/doctor-availability', '/patient-lookup',
              '/book-appointment', '/handoff-summary']

    def test_missing_or_placeholder_config_never_opens_tools(self):
        client = TestClient(api.app)
        with (patch.object(api, 'connect_to_db') as connect,
              patch.object(api, 'call_anchor') as anchor,
              patch.object(api, 'API_CONFIG', {'enable_staff_approval': True})):
            for token in [None, '', ' ', 'CHANGE_ME', ' CHANGE_ME ', ' secret ', 123]:
                with patch.object(api, 'API_TOKEN', token):
                    for route in self.routes:
                        response = client.post(route, json={}, headers={'X-Conversation-Id': 'c'})
                        self.assertEqual(response.status_code, 503, (token, route))
            connect.assert_not_called()
            anchor.assert_not_called()

    def test_bad_credentials_never_reach_database_or_call_store(self):
        client = TestClient(api.app)
        with (patch.object(api, 'API_TOKEN', 'valid-token'),
              patch.object(api, 'connect_to_db') as connect,
              patch.object(api, 'call_anchor') as anchor,
              patch.object(api, 'API_CONFIG', {'enable_staff_approval': True})):
            for value in ['', 'Bearer wrong', 'Basic valid-token', 'Bearer valid-token extra']:
                for route in self.routes:
                    response = client.post(route, json={}, headers={
                        'Authorization': value, 'X-Conversation-Id': 'c'})
                    self.assertEqual(response.status_code, 401)
            connect.assert_not_called()
            anchor.assert_not_called()

    def test_valid_case_insensitive_bearer_still_works(self):
        with patch.object(api, 'API_TOKEN', 'valid-token'), patch.object(api, 'API_CONFIG', {}):
            response = TestClient(api.app).get('/agent-capabilities',
                headers={'Authorization': 'bearer valid-token'})
        self.assertEqual(response.status_code, 200)

    def test_non_ascii_staff_input_is_rejected_without_type_error(self):
        with patch.object(api, 'API_CONFIG', {'staff_approval_token': 's' * 40}):
            with self.assertRaises(api.HTTPException) as caught:
                api.require_staff_auth('neplatný')
        self.assertEqual(caught.exception.status_code, 401)


if __name__ == '__main__':
    unittest.main()
