from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from test_single_appointment_move import calendar
from approval_store import ApprovalStore, ProposalConflict
import approval_proposals as proposals
import api_server as api


def test_http_move_search_binds_offer_and_rejects_reuse_for_create(calendar, tmp_path):
    db, cursor = calendar
    db.execute('CREATE TABLE UZIVATEL (IDUZI INTEGER, JMENO TEXT, PRIJMENI TEXT)')
    db.execute('INSERT INTO UZIVATEL VALUES (8, ?, ?)', ('Test', 'Doctor'))
    db.commit()
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    patient = {'idpac': 1, 'fingerprint': 'verified'}
    proof = store.issue_grant('tenant', 'call', 'patient', patient)
    config = {'enable_staff_approval': True, 'operator_tenant_key': 'tenant',
              'approval_store_path': str(store.path)}
    connection = Mock()
    connection.cursor.return_value = cursor
    option = {'service': 'skin', 'date': '2027-01-04', 'start_time': '09:30',
              'end_time': '09:40', 'doctor_id': 8, 'idprac': 1, 'idcinnosti': None}
    with patch.object(api, 'API_CONFIG', config), patch.object(api, 'API_TOKEN', 'test'), \
         patch.object(api, 'connect_to_db', return_value=connection), \
         patch.object(api, 'call_anchor', return_value=datetime(2026, 10, 5, tzinfo=timezone.utc)), \
         patch.object(proposals, 'patient_fingerprint', return_value='verified'), \
         patch.object(api, 'search_availability', return_value={'ok': True, 'options': [option]}) as search:
        response = TestClient(api.app).post('/doctor-availability',
            headers={'Authorization': 'Bearer test', 'X-Conversation-Id': 'call'},
            json={'service': 'skin', 'reschedule_appointment_id': 11, 'patient_verification_token': proof})
        assert response.status_code == 200, response.text
        assert search.call_args.kwargs['exclude_main_ids'] == (11,)
        result = response.json()
        token = result['options'][0]['offer_token']
        grant = store.resolve_grant('tenant', 'call', 'offer', token)
        assert grant['move_binding']['source'][0]['idobj'] == 11
        assert 'move_binding' not in response.text and 'idpac' not in response.text
        request = {'action': 'reschedule', 'request_id': 'move', 'caller_confirmed': True,
                   'appointment_id': 11, 'patient_verification_token': proof, 'offer_token': token}
        with patch.object(proposals, 'validate_offer') as validate:
            assert proposals.submit_proposal(store, cursor, 'tenant', 'call', request)['status'] == 'pending_staff_review'
            assert validate.call_args.kwargs['source'] == grant['move_binding']['source']
            with pytest.raises(ProposalConflict, match='different original'):
                proposals.submit_proposal(store, cursor, 'tenant', 'call', dict(request, action='create', request_id='new'))
        db.execute("UPDATE OBJOBJ SET CAS='09:35'")
        with pytest.raises(ProposalConflict, match='different original'):
            proposals.submit_proposal(store, cursor, 'tenant', 'call', dict(request, request_id='changed'))


@pytest.mark.parametrize('change', [
    {'reschedule_appointment_id': True}, {'reschedule_appointment_id': '11'},
    {'patient_verification_token': None}, {'service': 'dermatoscope_first'},
])
def test_move_search_requires_patient_proof_exact_source_and_same_service(calendar, tmp_path, change):
    _, cursor = calendar
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    proof = store.issue_grant('tenant', 'call', 'patient', {'idpac': 1, 'fingerprint': 'verified'})
    request = {'service': 'skin', 'reschedule_appointment_id': 11, 'patient_verification_token': proof, **change}
    with patch.object(proposals, 'patient_fingerprint', return_value='verified'):
        with pytest.raises(ProposalConflict):
            proposals.resolve_move_search(store, cursor, 'tenant', 'call', request)
