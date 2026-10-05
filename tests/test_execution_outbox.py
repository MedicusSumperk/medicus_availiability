import json
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_store import ApprovalStore
from handoff_delivery import deliver_execution
from test_approval_execution import prepare, CONFIG
import approval_execution as executor
from approval_store import ProposalConflict


DELIVERY = {'operator_tenant_key': 'tenant', 'operator_ingest_url': 'https://operator.test',
            'operator_ingest_token': 'private-token'}


def queued(tmp_path):
    store, card, _ = prepare(tmp_path)
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction',
            return_value={'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [10]}):
        executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    return store, card


def test_restart_tenant_isolation_and_stale_lease(tmp_path):
    store, card = queued(tmp_path)
    restarted = ApprovalStore(store.path)
    assert restarted.claim_execution_event('other') is None
    first = restarted.claim_execution_event('tenant')
    assert first['event']['event_id'] == card['id'] + ':execution'
    assert store.claim_execution_event('tenant') is None
    with store.connect() as db:
        db.execute('UPDATE execution_outbox SET lease_until=0')
    second = store.claim_execution_event('tenant')
    assert second['event'] == first['event']
    assert second['lease_token'] != first['lease_token']
    assert store.finish_execution_event(first, True) is False
    assert store.finish_execution_event(second, True) is True
    assert restarted.claim_execution_event('tenant') is None


def test_outbox_insert_failure_rolls_back_finish(tmp_path):
    store, card, _ = prepare(tmp_path)
    with store.connect() as db:
        db.execute("CREATE TRIGGER reject_queue BEFORE INSERT ON execution_outbox BEGIN SELECT RAISE(ABORT,'test'); END")
    with patch.object(executor, 'connect_to_db', return_value=Mock()), patch.object(executor, 'write_transaction',
            return_value={'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [10]}), patch.object(executor, 'emit_tool_event'):
        with pytest.raises(Exception, match='test'):
            executor.approve(store, 'tenant', card['id'], 1, 'staff', CONFIG)
    assert store.get('tenant', card['id'])['state'] == 'executing'
    assert store.claim_execution_event('tenant') is None


def test_network_retry_sends_same_event_without_reexecuting_write(tmp_path):
    store, card = queued(tmp_path)
    opener = Mock()
    opener.open.side_effect = OSError('private-token')
    with patch('handoff_delivery.build_opener', return_value=opener), patch.object(executor, 'write_transaction') as writer:
        assert deliver_execution(store, DELIVERY) == 'execution_retry_pending'
        original = json.loads(opener.open.call_args.args[0].data)
        assert deliver_execution(store, DELIVERY) == 'execution_idle'
        with store.connect() as db:
            db.execute('UPDATE execution_outbox SET next_attempt_at=0')
        response = Mock(status=200)
        response.read.return_value = b'{"accepted":true,"duplicate":true}'
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        opener.open.side_effect = None
        opener.open.return_value = context
        assert deliver_execution(ApprovalStore(store.path), DELIVERY) == 'execution_stored_in_operator'
        assert json.loads(opener.open.call_args.args[0].data) == original
        assert deliver_execution(store, DELIVERY) == 'execution_idle'
        writer.assert_not_called()
    assert store.get('tenant', card['id'])['state'] == 'committed'


def test_stalled_alert_survives_restart_and_never_releases_claim(tmp_path):
    store, card, _ = prepare(tmp_path)
    claimed, _ = store.decide('tenant', card['id'], 1, 'staff', approve=True)
    assert store.queue_stalled_executions('tenant') == 0
    with store.connect() as db:
        db.execute("UPDATE proposal_events SET at=? WHERE state='executing'", (time.time() - 601,))
    restarted = ApprovalStore(store.path)
    assert restarted.queue_stalled_executions('other') == 0
    assert restarted.queue_stalled_executions('tenant') == 1
    assert store.queue_stalled_executions('tenant') == 0
    event = store.claim_execution_event('tenant')['event']
    assert event['tool_call']['response_safe']['status'] == 'needs_reconciliation'
    assert 'idpac' not in json.dumps(event) and 'fingerprint' not in json.dumps(event)
    assert store.get('tenant', card['id']) == claimed
    with pytest.raises(ProposalConflict):
        store.decide('tenant', card['id'], 1, 'staff', approve=True)


def test_late_finish_remains_possible_and_has_distinct_event_identity(tmp_path):
    store, card, payload = prepare(tmp_path)
    claimed, _ = store.decide('tenant', card['id'], 1, 'staff', approve=True)
    with store.connect() as db:
        db.execute("UPDATE proposal_events SET at=? WHERE state='executing'", (time.time() - 601,))
    assert store.queue_stalled_executions('tenant') == 1
    result = {'ok': True, 'status': 'created', 'booking_confirmed': True, 'appointment_ids': [10]}
    final_event = executor.durable_execution_event('tenant', payload, card['id'], 'committed', result, 0)
    store.finish('tenant', card['id'], claimed['version'], 'committed', result, event=final_event)
    assert store.queue_stalled_executions('tenant') == 0
    with store.connect() as db:
        events = [json.loads(row['event']) for row in db.execute('SELECT event FROM execution_outbox')]
    assert len({e['event_id'] for e in events}) == 2
    assert len({e['tool_call']['request_id'] for e in events}) == 2
    assert store.get('tenant', card['id'])['state'] == 'committed'


def test_completed_operation_never_generates_stalled_alert(tmp_path):
    store, _ = queued(tmp_path)
    with store.connect() as db:
        db.execute("UPDATE proposal_events SET at=? WHERE state='executing'", (time.time() - 601,))
    assert store.queue_stalled_executions('tenant') == 0
