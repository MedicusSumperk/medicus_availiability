import sqlite3
import sys
from datetime import date, time
from pathlib import Path
from unittest.mock import patch

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import appointment_write as aw
from approval_execution import execution_request


class Cursor:
    def __init__(self, db):
        self.cursor = db.cursor()

    def execute(self, sql, args=()):
        self.cursor.execute(sql, tuple(str(v) if isinstance(v, (date, time)) else v for v in args))

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()


@pytest.fixture
def calendar():
    db = sqlite3.connect(':memory:', check_same_thread=False)
    db.executescript('''
      CREATE TABLE OBJOBJ (IDOBJ INTEGER PRIMARY KEY, IDPAC INTEGER, IDPRAC INTEGER,
        IDUZI INTEGER, DATUM TEXT, CAS TEXT, CASDO TEXT, TYP INTEGER, PRISEL TEXT,
        IDCINNOSTI INTEGER, INFO TEXT, IDREC INTEGER, TYPPROH TEXT, IDEXT INTEGER,
        IDCAL_EXT INTEGER, ES_UID TEXT, DATUMDO TEXT);
      CREATE TABLE OBJPROC (IDOBJ INTEGER);
      CREATE TABLE HISTORY (ACTION TEXT);
      CREATE TRIGGER deleted AFTER DELETE ON OBJOBJ BEGIN INSERT INTO HISTORY VALUES ('D'); END;
      CREATE TRIGGER updated AFTER UPDATE ON OBJOBJ BEGIN INSERT INTO HISTORY VALUES ('U'); END;
      INSERT INTO OBJOBJ VALUES (11, 1, 1, 8, '2027-01-04', '09:30', '09:40', 1, 'N',
        NULL, 'original note', NULL,NULL,NULL,NULL,NULL,'2027-01-04');
    ''')
    with patch.object(aw, '_service_followup_enabled', return_value=False):
        yield db, Cursor(db)
    db.close()


REQUEST = {'action': 'reschedule', 'service': 'skin', 'appointment_id': 11, 'idpac': 1,
           'patient_verified': True, 'include_related': False, 'date': '2027-01-05',
           'start_time': '09:20', 'doctor_id': 8, 'info': 'must not overwrite original note'}
CONFIG = {'enable_appointment_writes': True, 'enable_appointment_cancellations': True}
OPTION = {'service': 'skin', 'date': '2027-01-05', 'start_time': '09:20', 'end_time': '09:30',
          'doctor_id': 8, 'idprac': 1, 'idcinnosti': None}


def test_move_preserves_id_note_and_commits_only_update_history(calendar):
    db, cursor = calendar
    def availability(cur, request, *, exclude_main_ids):
        assert exclude_main_ids == (11,)
        cur.execute('SELECT COUNT(*) FROM OBJOBJ WHERE IDOBJ=11')
        assert cur.fetchone()[0] == 1
        return OPTION
    with patch.object(aw, '_find_exact_bookable_option', side_effect=availability):
        result = aw.write_appointment(cursor, REQUEST, CONFIG)
    db.commit()
    assert result['ok'] and result['appointment_ids'] == [11]
    assert db.execute('SELECT IDOBJ,DATUM,CAS,INFO FROM OBJOBJ').fetchall() == [(11, '2027-01-05', '09:20:00', 'original note')]
    assert db.execute('SELECT ACTION FROM HISTORY').fetchall() == [('U',)]


def test_unavailable_target_leaves_original_without_delete_history(calendar):
    db, cursor = calendar
    before = db.execute('SELECT * FROM OBJOBJ').fetchall()
    with patch.object(aw, '_find_exact_bookable_option', return_value={'error': 'slot_not_bookable'}):
        result = aw.write_appointment(cursor, REQUEST, CONFIG)
    db.commit()
    assert not result['ok']
    assert db.execute('SELECT * FROM OBJOBJ').fetchall() == before
    assert db.execute('SELECT * FROM HISTORY').fetchall() == []


def test_availability_exception_restores_savepoint(calendar):
    db, cursor = calendar
    before = db.execute('SELECT * FROM OBJOBJ').fetchall()
    with patch.object(aw, '_find_exact_bookable_option', side_effect=RuntimeError('read failed')):
        with pytest.raises(RuntimeError):
            aw.write_appointment(cursor, REQUEST, CONFIG)
    assert db.execute('SELECT * FROM OBJOBJ').fetchall() == before
    assert db.execute('SELECT * FROM HISTORY').fetchall() == []


@pytest.mark.parametrize('change', ["IDPAC=2", "IDREC=7", "IDCINNOSTI=1", "TYP=9", "PRISEL='A'"])
def test_unsupported_or_foreign_source_never_queries_target(calendar, change):
    db, cursor = calendar
    db.execute('UPDATE OBJOBJ SET '+change)
    before = db.execute('SELECT * FROM OBJOBJ').fetchall()
    with patch.object(aw, '_find_exact_bookable_option') as find:
        assert not aw.write_appointment(cursor, REQUEST, CONFIG)['ok']
    find.assert_not_called()
    assert db.execute('SELECT * FROM OBJOBJ').fetchall() == before


def test_procedure_link_is_preserved_and_requires_staff(calendar):
    db, cursor = calendar
    db.execute('INSERT INTO OBJPROC VALUES (11)')
    with patch.object(aw, '_find_exact_bookable_option') as find:
        result = aw.write_appointment(cursor, REQUEST, CONFIG)
    assert result['status'] == 'appointment_procedures_require_staff'
    find.assert_not_called()
    assert db.execute('SELECT * FROM OBJPROC').fetchall() == [(11,)]


def test_mapping_change_cannot_change_appointment_service(calendar):
    db, cursor = calendar
    before = db.execute('SELECT * FROM OBJOBJ').fetchall()
    with patch.object(aw, '_find_exact_bookable_option', return_value=dict(OPTION, idcinnosti=2)):
        result = aw.write_appointment(cursor, REQUEST, CONFIG)
    assert result['status'] == 'service_mapping_changed'
    assert db.execute('SELECT * FROM OBJOBJ').fetchall() == before


def test_staff_executor_can_build_single_move_request():
    payload = {'action': 'reschedule', 'patient': {'idpac': 1}, 'source': [{'idobj': 11}],
               'offer': dict(OPTION, technical_start_time='09:20')}
    request = execution_request(payload, 'one')
    assert request['appointment_ids'] == [11]
    assert request['service'] == 'skin' and request['include_related'] is False
