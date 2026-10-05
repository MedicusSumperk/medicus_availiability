import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_store import ApprovalStore
from delivery_status import inspect_store


def test_reports_only_tenant_counts_and_leaves_store_unchanged(tmp_path):
    store = ApprovalStore(tmp_path / 'cards.sqlite')
    first = store.submit('t', 'one', {'idpac': 123, 'note': 'private'}, {})
    store.decide('t', first['id'], 1, 'staff', approve=True)
    other = store.submit('other', 'two', {}, {})
    store.decide('other', other['id'], 1, 'staff', approve=True)
    with store.connect() as db:
        db.execute("UPDATE proposal_events SET at=? WHERE state='executing'", (time.time() - 601,))
        db.execute("INSERT INTO execution_outbox(proposal_id,tenant,event,attempts) VALUES('one','t','{}',3)")
        db.execute("INSERT INTO execution_outbox(proposal_id,tenant,event) VALUES('two','other','{}')")
    before = store.path.read_bytes()
    result = inspect_store(store.path, 't')
    assert result['stalled_executions'] == 1
    assert result['proposals'] == {'executing': 1}
    assert result['execution_events'] == {'total': 1, 'delivered': 0, 'pending': 1, 'due': 1, 'max_pending_attempts': 3}
    assert 'private' not in json.dumps(result) and 'idpac' not in json.dumps(result)
    assert store.path.read_bytes() == before


def test_missing_store_is_never_created(tmp_path):
    path = tmp_path / 'missing.sqlite'
    with pytest.raises(ValueError):
        inspect_store(path, 't')
    assert not path.exists()


def test_old_schema_is_reported_without_migration(tmp_path):
    import sqlite3
    path = tmp_path / 'old.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE handoffs(tenant,delivery_state)')
        db.execute("INSERT INTO handoffs VALUES ('t','pending')")
    before = path.read_bytes()
    assert inspect_store(path, 't') == {'read_only': True, 'execution_schema_ready': False, 'handoffs': {'pending': 1}}
    assert path.read_bytes() == before
