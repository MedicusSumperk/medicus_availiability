from unittest.mock import Mock, patch

import pytest
from test_single_appointment_move import calendar
from approval_proposals import source_snapshot, verified_move_availability
from approval_store import ProposalConflict
from laser_calendar import ScanCalendar


def test_verified_single_source_is_excluded_without_mutation(calendar):
    db, cursor = calendar
    source = source_snapshot(cursor, 1, [11])
    before = db.execute('SELECT * FROM OBJOBJ').fetchall()
    with verified_move_availability(cursor, 1, source) as arguments:
        assert arguments == {'exclude_main_ids': (11,)}
    assert db.execute('SELECT * FROM OBJOBJ').fetchall() == before
    assert db.execute('SELECT * FROM HISTORY').fetchall() == []


@pytest.mark.parametrize('change', ['IDPAC=2', "CAS='09:35'", 'IDREC=7'])
def test_foreign_changed_or_linked_source_cannot_be_excluded(calendar, change):
    db, cursor = calendar
    source = source_snapshot(cursor, 1, [11])
    db.execute('UPDATE OBJOBJ SET ' + change)
    with pytest.raises(ProposalConflict):
        with verified_move_availability(cursor, 1, source):
            pytest.fail('Invalid source accepted')


def test_pair_exclusion_uses_verified_counterpart_in_same_transaction(calendar):
    db, cursor = calendar
    db.execute('UPDATE OBJOBJ SET IDCINNOSTI=1')
    source = source_snapshot(cursor, 1, [11])
    scan_cursor = Mock()
    scanner = ScanCalendar(scan_cursor, 5, 1)
    with patch('paired_appointments.load_pair', return_value=({}, {'idobj': 22}, 'pair')) as verify:
        with verified_move_availability(cursor, 1, source, scan_calendar=scanner) as arguments:
            assert arguments['exclude_main_ids'] == (11,)
            assert arguments['scan_calendar'].exclude_ids == (22,)
            assert arguments['scan_calendar'].cursor is scan_cursor
    assert verify.call_args.args[2] == {'appointment_ids': [11], 'idpac': 1}


def test_unverified_pair_never_yields_exclusions(calendar):
    db, cursor = calendar
    db.execute('UPDATE OBJOBJ SET IDCINNOSTI=1')
    source = source_snapshot(cursor, 1, [11])
    with patch('paired_appointments.load_pair', side_effect=ValueError('unmanaged pair')):
        with pytest.raises(ValueError, match='unmanaged'):
            with verified_move_availability(cursor, 1, source, scan_calendar=ScanCalendar(Mock(), 5, 1)):
                pytest.fail('Unverified pair accepted')
