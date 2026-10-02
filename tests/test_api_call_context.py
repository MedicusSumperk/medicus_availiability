import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fastapi.testclient import TestClient
from approval_store import ApprovalStore
import api_server as api


def test_all_authenticated_tools_anchor_call_without_enabling_writes(tmp_path):
    path = tmp_path / 'requests.sqlite'
    ApprovalStore(path)
    config = {'enable_durable_handoff': True, 'approval_store_path': str(path),
              'operator_tenant_key': 'test', 'enable_appointment_writes': False}
    headers = {'Authorization': 'Bearer test-token', 'X-Conversation-Id': 'conv-test'}
    with patch.object(api, 'API_CONFIG', config), patch.object(api, 'API_TOKEN', 'test-token'):
        client = TestClient(api.app)
        with patch('approval_store.time.time', return_value=100):
            assert client.get('/agent-capabilities', headers=headers).status_code == 200
        with (patch('approval_store.time.time', return_value=400),
              patch.object(api, 'connect_to_db', return_value=MagicMock()),
              patch.object(api, 'search_availability', return_value={'ok':True,'options':[]}) as search):
            response = client.post('/doctor-availability', headers=headers,
                                   json={'call_started_at':'1900-01-01T00:00:00Z'})
            assert response.status_code == 200
            assert search.call_args.kwargs['call_started_at'].timestamp() == 100
        assert ApprovalStore(path).first_seen('test', 'conv-test') == 100
        assert client.get('/agent-capabilities', headers=headers).json()['bookable_services'] == []


def test_unauthorized_request_never_creates_anchor(tmp_path):
    config = {'enable_durable_handoff':True, 'approval_store_path':str(tmp_path/'missing.sqlite'),
              'operator_tenant_key':'test'}
    with patch.object(api,'API_CONFIG',config), patch.object(api,'API_TOKEN','test-token'):
        response = TestClient(api.app).get('/agent-capabilities',headers={'X-Conversation-Id':'conv-test'})
        assert response.status_code == 401
    assert not (tmp_path/'missing.sqlite').exists()


def test_unresolved_runtime_headers_are_rejected():
    with patch.object(api,'API_CONFIG',{}), patch.object(api,'API_TOKEN','test-token'):
        for value in ('{{system__conversation_id}}', 'system__conversation_id', ' ', 'a b', 'x'*161):
            response = TestClient(api.app).get('/agent-capabilities',headers={
                'Authorization':'Bearer test-token','X-Conversation-Id':value})
            assert response.status_code == 400


def test_missing_durable_store_fails_closed_without_exposing_path(tmp_path):
    config={'enable_durable_handoff':True,'approval_store_path':str(tmp_path/'missing.sqlite'),
            'operator_tenant_key':'test'}
    with patch.object(api,'API_CONFIG',config), patch.object(api,'API_TOKEN','test-token'):
        response=TestClient(api.app).get('/agent-capabilities',headers={
            'Authorization':'Bearer test-token','X-Conversation-Id':'conv-test'})
        assert response.status_code == 503
        assert str(tmp_path) not in response.text
    assert not (tmp_path/'missing.sqlite').exists()


def test_legacy_missing_header_uses_current_request_time():
    with (patch.object(api,'API_CONFIG',{}), patch.object(api,'API_TOKEN','test-token'),
          patch.object(api,'connect_to_db',return_value=MagicMock()),
          patch.object(api,'search_availability',return_value={'ok':True,'options':[]}) as search):
        response=TestClient(api.app).post('/doctor-availability',headers={'Authorization':'Bearer test-token'},json={})
        assert response.status_code == 200
        assert search.call_args.kwargs['call_started_at'].tzinfo is not None
