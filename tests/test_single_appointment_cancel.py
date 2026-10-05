from unittest.mock import patch

import pytest
from test_single_appointment_move import calendar, REQUEST, CONFIG, aw


CANCEL = dict(REQUEST, action='cancel')


@pytest.mark.parametrize('change', ["IDREC=7", "TYPPROH='x'", "IDEXT=3", "IDCAL_EXT=3",
                                     "ES_UID='external'", "DATUMDO='2027-01-05'", "TYP=9",
                                     "PRISEL='A'", "IDCINNOSTI=5", "IDPAC=2"])
def test_nonstandard_cancel_keeps_row_and_history(calendar, change):
    db, cursor = calendar
    db.execute('UPDATE OBJOBJ SET ' + change)
    before = db.execute('SELECT * FROM OBJOBJ').fetchall()
    history = db.execute('SELECT * FROM HISTORY').fetchall()
    assert aw.write_appointment(cursor, CANCEL, CONFIG)['ok'] is False
    assert db.execute('SELECT * FROM OBJOBJ').fetchall() == before
    assert db.execute('SELECT * FROM HISTORY').fetchall() == history


def test_all_requested_cells_validated_before_first_delete(calendar):
    db, cursor = calendar
    db.execute('INSERT INTO OBJOBJ SELECT 12,IDPAC,IDPRAC,IDUZI,DATUM,CAS,CASDO,TYP,PRISEL,IDCINNOSTI,INFO,IDREC,TYPPROH,IDEXT,IDCAL_EXT,ES_UID,DATUMDO FROM OBJOBJ')
    db.execute('INSERT INTO OBJPROC VALUES (12)')
    request = dict(CANCEL, appointment_ids=[11, 12])
    request.pop('appointment_id')
    result = aw.write_appointment(cursor, request, CONFIG)
    assert result['status'] == 'appointment_procedures_require_staff'
    assert db.execute('SELECT COUNT(*) FROM OBJOBJ').fetchone()[0] == 2
    assert db.execute('SELECT * FROM HISTORY').fetchall() == []


def test_default_cancellation_never_infers_related_cells(calendar):
    db, cursor = calendar
    request = dict(CANCEL)
    request.pop('include_related')
    with patch.object(aw, '_expand_related_appointment_ids') as expand:
        result = aw.write_appointment(cursor, request, CONFIG)
    expand.assert_not_called()
    assert result['ok'] is True and result['appointment_ids'] == [11]
    assert db.execute('SELECT * FROM HISTORY').fetchall() == [('D',)]


def test_explicit_inferred_related_cancel_requires_staff(calendar):
    db, cursor = calendar
    assert aw.write_appointment(cursor, dict(CANCEL, include_related=True), CONFIG)['status'] == 'related_appointments_require_staff'
    assert db.execute('SELECT COUNT(*) FROM OBJOBJ').fetchone()[0] == 1
