import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_store import ApprovalStore, ProposalConflict
import approval_execution as executor
import paired_appointments as paired
import api_server as api
from fastapi.testclient import TestClient


def prepare(tmp_path):
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    payload = {'action': 'create', 'patient': {'idpac': 1, 'fingerprint': 'verified'},
               'conversation_id': 'conv_test',
               'source': [], 'offer': {'service': 'skin', 'date': '2027-01-04',
                                      'doctor_id': 8, 'technical_start_time': '09:30'}}
    card = store.submit('tenant', 'one', payload, {'action': 'create'})
    return store, card, payload


CONFIG = {'enable_staff_execution': True, 'enable_appointment_writes': True}


@pytest.mark.parametrize('rollback_fails', [False, True])
def test_real_single_transaction_validation_rejection(tmp_path, rollback_fails):
    store, card, _ = prepare(tmp_path)
    connection, writer = Mock(), Mock()
    if rollback_fails:
        # First rollback starts a fresh transaction, second handles rejection,
        # third is the executor's cleanup. A later successful cleanup cannot
        # retroactively turn a failed rollback acknowledgement into certainty.
        connection.rollback.side_effect = [None, OSError('lost rollback ACK'), None]
    def transact(con, request, cfg, *, precondition):
        return paired.write_transaction(con, request, cfg, writer, precondition=precondition)
    with patch.object(executor, 'connect_to_db', return_value=connection), \
         patch.object(executor, 'validate_payload', side_effect=ProposalConflict('private patient context')), \
         patch.object(paired, 'is_pair_request', return_value=False), \
         patch.object(executor, 'write_transaction', side_effect=transact):
        result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    assert result['state'] == ('needs_reconciliation' if rollback_fails else 'conflict')
    assert result['result']['booking_confirmed'] is False
    assert 'private patient context' not in str(result)
    writer.assert_not_called()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_disabled_execution_leaves_pending_card_and_never_connects(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db') as connect:
        with pytest.raises(ProposalConflict):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', {})
    connect.assert_not_called()
    assert store.get('tenant', card['id']) == card


def test_commit_once_and_public_result_drops_private_data(tmp_path):
    store, card, _ = prepare(tmp_path)
    connection = Mock()
    with patch.object(executor, 'connect_to_db', return_value=connection), patch.object(executor, 'validate_payload') as validate:
        def write(con, request, cfg, *, precondition):
            assert request['idpac'] == 1 and request['request_id'] == 'staff:' + card['id']
            precondition('locked-main', 'locked-laser')
            return {'ok': True, 'status': 'created', 'appointment_ids': [10], 'booking_confirmed': True,
                    'appointments': [{'idpac': 1, 'info': 'private'}], 'token': 'secret'}
        with patch.object(executor, 'write_transaction', side_effect=write) as writer:
            result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
            with pytest.raises(ProposalConflict):
                executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
            writer.assert_called_once()
    assert result['state'] == 'committed'
    assert result['result'] == {'ok': True, 'status': 'created', 'appointment_ids': [10], 'booking_confirmed': True}
    assert 'private' not in str(result) and 'secret' not in str(result)
    assert validate.call_args.args[:2] == ('locked-main', 'locked-laser')


def test_database_unavailable_before_writer_is_failed_without_retry(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', side_effect=OSError('private path')), patch.object(executor, 'write_transaction') as writer:
        result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    assert result['state'] == 'failed'
    writer.assert_not_called()
    assert 'private' not in str(result)


def test_lost_commit_ack_requires_reconciliation(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction', side_effect=OSError('lost ACK')) as writer:
        result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
        with pytest.raises(ProposalConflict):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    assert result['state'] == 'needs_reconciliation'
    writer.assert_called_once()


def test_failure_to_persist_success_leaves_executing_not_retryable(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction', return_value={'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [10]}) as writer, patch.object(store, 'finish', side_effect=OSError('disk full')):
        with pytest.raises(OSError):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
        assert store.get('tenant', card['id'])['state'] == 'executing'
        with pytest.raises(ProposalConflict):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    writer.assert_called_once()


def test_definite_rejection_is_conflict(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction', return_value={'ok': False, 'status': 'calendar_busy_retry_later'}):
        result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    assert result['state'] == 'conflict'


def test_atomic_claim_rechecks_integrity(tmp_path):
    store, card, _ = prepare(tmp_path)
    with store.connect() as db:
        db.execute('UPDATE proposals SET payload=? WHERE id=?', ('{}', card['id']))
    with pytest.raises(ProposalConflict, match='integrity'):
        store.decide('tenant', card['id'], 1, 'staff', approve=True)
    assert store.get('tenant', card['id'])['state'] == 'pending_staff_review'


def test_approve_endpoint_rejects_agent_token_and_disabled_staff_execution(tmp_path):
    store, card, _ = prepare(tmp_path)
    cfg = {'enable_staff_approval': True, 'approval_store_path': str(store.path),
           'operator_tenant_key': 'tenant', 'staff_approval_token': 's'*40}
    with patch.object(api, 'API_CONFIG', cfg), patch.object(api, 'API_TOKEN', 'agent-token'), patch.object(executor, 'connect_to_db') as connect:
        client = TestClient(api.app)
        path = '/staff/proposals/' + card['id'] + '/approve'
        body = {'version': 1, 'actor_user_id': 'verified-staff'}
        assert client.post(path, headers={'Authorization': 'Bearer agent-token'}, json=body).status_code == 401
        assert client.post(path, headers={'X-Staff-Token': 's'*40}, json=body).status_code == 409
    connect.assert_not_called()
    assert store.get('tenant', card['id']) == card


def test_execution_telemetry_correlates_call_and_excludes_private_fields(tmp_path):
    store, card, _ = prepare(tmp_path)
    response = {'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [22],
                'appointments': [{'database': 'LASER', 'idobj': 22, 'date': '2027-01-04',
                                  'start_time': '09:15', 'idpac': 1, 'info': 'private note'}]}
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction', return_value=response), patch.object(executor, 'emit_tool_event') as emit:
        executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
        with pytest.raises(ProposalConflict):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    emit.assert_not_called()
    event = store.claim_execution_event('tenant')['event']
    assert event['conversation_id'] == 'conv_test'
    tool = event['tool_call']
    assert tool['name'] == 'appointment_write'
    assert tool['request_id'] == 'staff:' + card['id']
    assert tool['response_safe']['appointments'][0]['database'] == 'LASER'
    assert tool['business_ok'] is True
    assert 'idpac' not in str(event) and 'private note' not in str(event)


@pytest.mark.parametrize('failure', ['connect', 'write', 'persist', 'uncertain_result'])
def test_execution_failures_emit_no_confirmed_rows(tmp_path, failure):
    store, card, _ = prepare(tmp_path)
    connect = Mock(return_value=Mock())
    write = Mock(return_value={'ok': True, 'status': 'created', 'appointments': [{'idobj': 22}]})
    finish = store.finish
    if failure == 'connect':
        connect.side_effect = OSError('private')
    elif failure == 'write':
        write.side_effect = OSError('private')
    elif failure == 'persist':
        finish = Mock(side_effect=OSError('private'))
    else:
        write.return_value = {'ok': False, 'status': 'needs_reconciliation', 'appointments': [{'idobj': 22}]}
    with patch.object(executor, 'connect_to_db', connect), patch.object(executor, 'write_transaction', write), patch.object(store, 'finish', finish), patch.object(executor, 'emit_tool_event') as emit:
        if failure == 'persist':
            with pytest.raises(OSError):
                executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
        else:
            result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
            assert result['state'] == ('failed' if failure == 'connect' else 'needs_reconciliation')
    if failure == 'persist':
        event = emit.call_args.kwargs
    else:
        emit.assert_not_called()
        event = store.claim_execution_event('tenant')['event']['tool_call']
        event['response_payload'] = event['response_safe']
    assert event['business_ok'] is False and event['http_status'] == 503
    assert event['response_payload']['booking_confirmed'] is False
    assert 'appointments' not in event['response_payload'] and 'private' not in str(event)


def test_telemetry_failure_cannot_change_committed_operation(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction', return_value={'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [10]}), patch.object(executor, 'emit_tool_event', side_effect=OSError('offline')):
        result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    assert result['state'] == 'committed'


@pytest.mark.parametrize('response', [None, {}, {'ok': True},
    {'ok': True, 'status': 'created', 'booking_confirmed': False, 'appointment_ids': [10]},
    {'ok': True, 'status': 'cancelled', 'booking_confirmed': True, 'appointment_ids': [10]},
    {'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': []},
    {'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [True]},
    {'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': ['10']}])
def test_malformed_success_is_durable_uncertainty_not_committed(tmp_path, response):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction', return_value=response) as writer:
        result = executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
        with pytest.raises(ProposalConflict):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    writer.assert_called_once()
    assert result['state'] == 'needs_reconciliation'
    assert result['result'] == {'ok': False, 'status': 'needs_reconciliation', 'booking_confirmed': False}
    event = store.claim_execution_event('tenant')['event']['tool_call']
    assert event['is_error'] is True
    assert 'appointments' not in event['response_safe']
