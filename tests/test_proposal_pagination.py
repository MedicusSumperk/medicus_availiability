import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_store import ApprovalStore, ProposalConflict


def test_active_pages_reach_old_requests_despite_recent_closed_cards_and_decisions(tmp_path):
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    seed = store.submit('tenant', 'seed', {}, {})
    with store.connect() as db:
        db.execute('DELETE FROM proposals')
        for number in range(230):
            state = 'pending_staff_review' if number < 110 else 'committed'
            db.execute('''INSERT INTO proposals(id,tenant,request_key,digest,payload,summary,state,created_at,expires_at)
                VALUES(?,?,?,?,?,?,?,?,?)''', (f'p{number:03d}', 'tenant', str(number), 'hash', '{}', '{}', state, 1 if number < 110 else 2, 9999999999))
    first = store.page('tenant')
    assert len(first['items']) == 100 and first['items'][0]['id'] == 'p000'
    # Reject the last displayed item before the next page. A row offset would
    # skip a request now that the active set shrank; the immutable cursor won't.
    store.decide('tenant', first['next_cursor'], 1, 'staff', approve=False)
    second = store.page('tenant', cursor=first['next_cursor'])
    ids = [r['id'] for r in first['items'] + second['items']]
    assert ids == [f'p{i:03d}' for i in range(110)]
    assert second['next_cursor'] is None
    all_ids, cursor = [], None
    while True:
        page = store.page('tenant', cursor=cursor, include_closed=True)
        all_ids.extend(r['id'] for r in page['items'])
        cursor = page['next_cursor']
        if cursor is None:
            break
    assert len(all_ids) == len(set(all_ids)) == 230


def test_cursor_from_another_tenant_is_rejected(tmp_path):
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    card = store.submit('other', 'key', {}, {})
    with pytest.raises(ProposalConflict):
        store.page('tenant', cursor=card['id'])

def test_detail_history_is_ordered_scoped_and_does_not_expose_payload(tmp_path):
    store = ApprovalStore(tmp_path / 'history.sqlite')
    card = store.submit('tenant', 'history', {'secret': 'private'}, {'action': 'create'})
    executing, _ = store.decide('tenant', card['id'], 1, 'staff-123', approve=True)
    store.finish('tenant', card['id'], executing['version'], 'needs_reconciliation', {'status': 'uncertain'})
    detail = store.detail('tenant', card['id'])
    assert detail['actor'] == 'staff-123'
    assert [e['state'] for e in detail['history']] == ['pending_staff_review', 'executing', 'needs_reconciliation']
    assert [e['actor'] for e in detail['history']] == [None, 'staff-123', 'staff-123']
    assert 'private' not in str(detail) and 'payload' not in detail
    from approval_store import ProposalNotFound
    with pytest.raises(ProposalNotFound):
        store.detail('other', card['id'])
    assert store.get('tenant', card['id'])['version'] == detail['version'] == 3


def test_expired_request_stays_in_active_queue_and_cannot_execute(tmp_path, monkeypatch):
    import approval_store
    store = ApprovalStore(tmp_path / 'expiry.sqlite')
    monkeypatch.setattr(approval_store.time, 'time', lambda: 100)
    stale = store.submit('tenant', 'stale', {}, {}, ttl_seconds=10)
    running = store.submit('tenant', 'running', {}, {}, ttl_seconds=10)
    store.decide('tenant', running['id'], 1, 'staff', approve=True)
    other = store.submit('other', 'stale', {}, {}, ttl_seconds=10)
    monkeypatch.setattr(approval_store.time, 'time', lambda: 111)
    with pytest.raises(ProposalConflict):
        store.pending_payload('tenant', stale['id'], 1)
    page = store.page('tenant')
    expired = next(c for c in page['items'] if c['id'] == stale['id'])
    assert expired['state'] == 'expired' and expired['version'] == 2
    assert store.get('tenant', running['id'])['state'] == 'executing'
    detail = store.detail('tenant', stale['id'])
    assert [e['state'] for e in detail['history']] == ['pending_staff_review', 'expired']
    assert detail['history'][-1]['actor'] is None
    with store.connect() as db:
        assert db.execute('SELECT state FROM proposals WHERE id=?', (other['id'],)).fetchone()[0] == 'pending_staff_review'
    with pytest.raises(ProposalConflict):
        store.decide('tenant', stale['id'], 2, 'staff', approve=True)
    rejected, payload = store.decide('tenant', stale['id'], 2, 'staff', approve=False)
    assert rejected['state'] == 'rejected' and payload is None
    assert stale['id'] not in [c['id'] for c in store.page('tenant')['items']]
    assert store.detail('tenant', stale['id'])['version'] == 3


def test_expired_exact_replay_keeps_identity_without_returning_pending(tmp_path, monkeypatch):
    import approval_store
    store = ApprovalStore(tmp_path / 'replay.sqlite')
    monkeypatch.setattr(approval_store.time, 'time', lambda: 100)
    payload = {'request_digest': 'same'}
    card = store.submit('tenant', 'key', payload, {}, ttl_seconds=10)
    monkeypatch.setattr(approval_store.time, 'time', lambda: 111)
    replay = store.replay_submission('tenant', 'key', 'same')
    assert replay['id'] == card['id'] and replay['state'] == 'expired'
    direct = store.submit('tenant', 'key', payload, {}, ttl_seconds=10)
    assert direct == replay
    assert len(store.page('tenant')['items']) == 1
    assert [e['state'] for e in store.detail('tenant', card['id'])['history']] == ['pending_staff_review', 'expired']
