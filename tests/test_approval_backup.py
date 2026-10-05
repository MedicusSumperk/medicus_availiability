import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from approval_backup import backup_store
from approval_store import ApprovalStore


def test_backup_includes_committed_wal_and_preserves_recovery_state(tmp_path):
    source = tmp_path / 'live.sqlite'
    store = ApprovalStore(source)
    with sqlite3.connect(source) as live:
        live.execute('PRAGMA journal_mode=WAL')
        live.execute('PRAGMA wal_autocheckpoint=0')
        live.execute("INSERT INTO call_anchors VALUES ('tenant','call',123)")
        live.execute("INSERT INTO handoffs VALUES ('id','tenant','call','request','digest','{}',123,'failed')")
        live.execute("INSERT INTO handoff_failure_alerts(handoff_id,created_at) VALUES ('id',123)")
        live.commit()
        assert Path(str(source) + '-wal').stat().st_size > 0
        destination = tmp_path / 'backup.sqlite'
        assert backup_store(source, destination)['integrity_check'] == 'ok'
        # A fresh connection reads the standalone backup with the live WAL open.
        with sqlite3.connect(destination) as restored:
            assert restored.execute('SELECT first_seen FROM call_anchors').fetchone() == (123,)
            assert restored.execute('SELECT delivery_state FROM handoffs').fetchone() == ('failed',)
            assert restored.execute('SELECT delivered FROM handoff_failure_alerts').fetchone() == (0,)
        live.execute("UPDATE handoffs SET delivery_state='pending'")
        live.commit()
        with sqlite3.connect(destination) as restored:
            assert restored.execute('SELECT delivery_state FROM handoffs').fetchone() == ('failed',)


def test_backup_never_overwrites_and_cleans_failed_new_file(tmp_path):
    source = tmp_path / 'live.sqlite'
    ApprovalStore(source)
    destination = tmp_path / 'existing.sqlite'
    destination.write_bytes(b'existing backup')
    with pytest.raises(FileExistsError):
        backup_store(source, destination)
    assert destination.read_bytes() == b'existing backup'
    with pytest.raises(ValueError):
        backup_store(source, source)
    invalid = tmp_path / 'invalid.sqlite'
    invalid.write_bytes(b'not a database')
    failed = tmp_path / 'failed.sqlite'
    with pytest.raises(sqlite3.DatabaseError):
        backup_store(invalid, failed)
    assert not failed.exists()
