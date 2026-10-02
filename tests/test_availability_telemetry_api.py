import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fastapi.testclient import TestClient
import api_server as api
import operator_telemetry as telemetry

CONFIG={'operator_ingest_url':'https://example.test','operator_ingest_token':'test',
        'operator_tenant_key':'tenant'}
HEADERS={'Authorization':'Bearer test-token','X-Conversation-Id':'conv-test'}


def test_returned_options_are_captured_under_same_conversation():
    result={'ok':True,'options':[{'date':'2026-10-07','start_time':'13:20','doctor_name':'Test doctor'}]}
    with (patch.object(api,'API_CONFIG',CONFIG),patch.object(api,'API_TOKEN','test-token'),
          patch.object(api,'connect_to_db',return_value=MagicMock()),
          patch.object(api,'search_availability',return_value=result),
          patch.object(telemetry._EXECUTOR,'submit') as submit):
        response=TestClient(api.app).post('/doctor-availability',headers=HEADERS,
                                         json={'arbitrary_text':'private-information'})
    assert response.status_code==200
    event=submit.call_args.args[2]
    assert event['conversation_id']=='conv-test'
    assert event['tool_call']['response_safe']==result
    assert event['tool_call']['request_safe']=={}


def test_broken_telemetry_cannot_change_successful_availability():
    with (patch.object(api,'API_CONFIG',CONFIG),patch.object(api,'API_TOKEN','test-token'),
          patch.object(api,'connect_to_db',return_value=MagicMock()),
          patch.object(api,'search_availability',return_value={'ok':True,'options':[]}),
          patch.object(telemetry._EXECUTOR,'submit',side_effect=RuntimeError('pool stopped'))):
        response=TestClient(api.app).post('/doctor-availability',headers=HEADERS,json={})
    assert response.status_code==200
    assert response.json()['ok'] is True


def test_database_error_is_recorded_without_sensitive_exception():
    with (patch.object(api,'API_CONFIG',CONFIG),patch.object(api,'API_TOKEN','test-token'),
          patch.object(api,'connect_to_db',side_effect=RuntimeError('private-database-path')),
          patch.object(telemetry._EXECUTOR,'submit') as submit):
        response=TestClient(api.app).post('/doctor-availability',headers=HEADERS,json={})
    assert response.status_code==500
    assert 'private-database-path' not in response.text
    event=submit.call_args.args[2]
    assert event['event_type']=='tool.failed'
    assert event['tool_call']['error_code']=='availability_failed'
    assert 'private-database-path' not in str(event)
