import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import api_server as api


@pytest.fixture
def client():
    with patch.object(api, 'API_TOKEN', 'test-token'), patch.object(api, 'API_CONFIG', {}), patch.object(
        api, 'call_anchor', return_value=datetime(2026, 10, 5, 9, tzinfo=ZoneInfo('Europe/Prague'))
    ):
        yield TestClient(api.app)


HEADERS = {'Authorization': 'Bearer test-token', 'X-Conversation-Id': 'synthetic-diagnostics'}


@pytest.mark.parametrize('failure,status,code', [
    (ValueError('private caller input'), 400, 'validation_error'),
    (OSError('private database path'), 500, 'availability_failed'),
])
def test_availability_diagnostics_do_not_copy_input_or_exception(client, failure, status, code):
    connection = Mock()
    with patch.object(api, 'connect_to_db', return_value=connection), patch.object(
        api, 'search_availability', side_effect=failure
    ), patch.object(api, 'emit_tool_event') as emit:
        response = client.post('/doctor-availability', headers=HEADERS,
                               json={'service': 'skin', 'doctor_name': 'private caller input'})
    assert response.status_code == status
    event = emit.call_args.kwargs
    assert event['request_payload'] == {}
    assert event['response_payload'] == {'ok': False, 'error_code': code}
    assert 'private' not in str(event)
    if status == 500:
        assert 'private' not in response.text
    connection.close.assert_called_once()
    connection.commit.assert_not_called()


def test_success_keeps_returned_slots_but_not_arbitrary_request_text(client):
    result = {'ok': True, 'options': [{'date': '2026-10-07', 'start_time': '15:00', 'doctor_name': 'Test doctor'}]}
    with patch.object(api, 'connect_to_db', return_value=Mock()), patch.object(
        api, 'search_availability', return_value=result
    ), patch.object(api, 'emit_tool_event') as emit:
        response = client.post('/doctor-availability', headers=HEADERS,
                               json={'service': 'skin', 'free_text': 'private caller input'})
    assert response.status_code == 200
    event = emit.call_args.kwargs
    assert event['request_payload'] == {}
    assert event['response_payload']['options'] == response.json()['options']
    assert 'private caller input' not in str(event)


@pytest.mark.parametrize('endpoint,target', [
    ('/patient-lookup', 'connect_to_db'),
    ('/agent-capabilities', 'agent_capabilities'),
])
def test_read_tools_do_not_expose_internal_errors(client, endpoint, target):
    with patch.object(api, target, side_effect=OSError('private database path')), patch.object(api, 'emit_tool_event'):
        response = client.post(endpoint, headers=HEADERS, json={})
    assert response.status_code == 500
    assert 'private database path' not in response.text
