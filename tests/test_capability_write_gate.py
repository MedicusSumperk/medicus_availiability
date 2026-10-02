import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fastapi.testclient import TestClient
import api_server as api


def test_capabilities_never_advertise_booking_when_runtime_writes_are_off():
    for setting in (False, None, 'true'):
        with patch.object(api, 'API_CONFIG', {'enable_appointment_writes': setting}), patch.object(api, 'API_TOKEN', 'test-token'):
            response = TestClient(api.app).post('/agent-capabilities', headers={'Authorization': 'Bearer test-token'}, json={})
        assert response.status_code == 200
        body = response.json()
        assert body['booking_mode'] == 'staff_handoff'
        assert body['bookable_services'] == []
        assert all(not service['agent_can_book_finally'] for service in body['handoff_services'])
        assert 'personál' in body['voice_answer_cs']


def test_enabled_runtime_still_respects_service_rules():
    with patch.object(api, 'API_CONFIG', {'enable_appointment_writes': True}), patch.object(api, 'API_TOKEN', 'test-token'):
        response = TestClient(api.app).get('/agent-capabilities', headers={'Authorization': 'Bearer test-token'})
    body = response.json()
    assert body['booking_mode'] == 'direct'
    assert body['bookable_services']
    assert all(service['agent_can_book_finally'] for service in body['bookable_services'])
    assert any(not service['agent_can_book_finally'] for service in body['handoff_services'])
