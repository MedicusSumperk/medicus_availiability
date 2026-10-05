import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_store import ApprovalStore, ProposalConflict, ProposalNotFound
import approval_proposals as proposals
import api_server as api
from fastapi.testclient import TestClient


def prepare(tmp_path, action='create'):
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    payload = {'action': action, 'patient': {'idpac': 123, 'fingerprint': 'fingerprint'},
               'source': [] if action == 'create' else [{'idobj': 7}],
               'offer': None if action == 'cancel' else {'service': 'skin'}}
    card = store.submit('tenant', 'request', payload, {'action': action})
    return store, card, payload


def test_success_does_not_approve_or_expose_patient(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(proposals, 'patient_fingerprint', return_value='fingerprint'), patch.object(proposals, 'validate_offer'):
        result = proposals.revalidate_proposal(store, Mock(), 'tenant', card['id'], 1)
    assert result['status'] == 'validated' and result['booking_confirmed'] is False
    assert result['execution_enabled'] is False
    assert 'idpac' not in str(result) and 'fingerprint' not in str(result)
    assert store.get('tenant', card['id']) == card


def test_changed_patient_stops_before_availability(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(proposals, 'patient_fingerprint', return_value='changed'), patch.object(proposals, 'validate_offer') as offer:
        with pytest.raises(ProposalConflict):
            proposals.revalidate_proposal(store, Mock(), 'tenant', card['id'], 1)
        offer.assert_not_called()


@pytest.mark.parametrize('action', ['cancel', 'reschedule'])
def test_changed_source_is_rejected(tmp_path, action):
    store, card, _ = prepare(tmp_path, action)
    with patch.object(proposals, 'patient_fingerprint', return_value='fingerprint'), patch.object(proposals, 'source_snapshot', return_value=[{'idobj':8}]):
        with pytest.raises(ProposalConflict):
            proposals.revalidate_proposal(store, Mock(), 'tenant', card['id'], 1)


def test_decision_during_validation_is_not_reported_valid(tmp_path):
    store, card, _ = prepare(tmp_path)
    def reject(_cursor, _offer):
        store.decide('tenant', card['id'], 1, 'staff', approve=False)
    with patch.object(proposals, 'patient_fingerprint', return_value='fingerprint'), patch.object(proposals, 'validate_offer', side_effect=reject):
        with pytest.raises(ProposalConflict):
            proposals.revalidate_proposal(store, Mock(), 'tenant', card['id'], 1)


def test_expiry_version_tenant_and_corruption_are_rejected(tmp_path):
    store, card, _ = prepare(tmp_path)
    with pytest.raises(ProposalNotFound): store.pending_payload('other', card['id'], 1)
    with pytest.raises(ProposalConflict): store.pending_payload('tenant', card['id'], 2)
    with patch('approval_store.time.time', return_value=card['expires_at']):
        with pytest.raises(ProposalConflict): store.pending_payload('tenant', card['id'], 1)
    with store.connect() as db:
        db.execute('UPDATE proposals SET payload=? WHERE id=?', ('{}', card['id']))
    with pytest.raises(ProposalConflict): store.pending_payload('tenant', card['id'], 1)


def test_staff_endpoint_rolls_back_and_never_calls_writer(tmp_path):
    store, card, _ = prepare(tmp_path)
    connection = Mock()
    config = {'enable_staff_approval':True, 'approval_store_path':str(store.path),
              'operator_tenant_key':'tenant', 'staff_approval_token':'s'*40}
    with (patch.object(api,'API_CONFIG',config), patch.object(api,'API_TOKEN','agent-token'),
          patch.object(api,'connect_to_db',return_value=connection) as connect,
          patch.object(api,'write_appointment') as write,
          patch.object(proposals,'patient_fingerprint',return_value='fingerprint'),
          patch.object(proposals,'validate_offer')):
        client = TestClient(api.app)
        path='/staff/proposals/'+card['id']+'/revalidate'
        assert client.post(path,headers={'Authorization':'Bearer agent-token'},json={'version':1}).status_code==401
        connect.assert_not_called()
        result=client.post(path,headers={'X-Staff-Token':'s'*40},json={'version':1})
        assert result.status_code==200
        assert result.json()['booking_confirmed'] is False
        write.assert_not_called()
        connection.commit.assert_not_called()
        connection.rollback.assert_called_once()
        connection.close.assert_called_once()
