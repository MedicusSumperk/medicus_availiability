"""MAIN GUI projection: zero-length row occupies its real calendar cell."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from availability_engine import CalendarDataUnavailable, compute_slots
import laser_calendar


def test_zero_duration_arriving_after_offer_blocks_staff_validation_and_writer():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import availability_engine as engine
    import availability_search as search
    import appointment_write as writer
    import approval_execution as execution
    from approval_proposals import offer_snapshot
    from approval_store import ProposalConflict

    request = dict(service='skin', date='2026-10-09', start_time='11:15',
                   doctor_id=15, idpac=1, patient_verified=True)
    cursor = Mock()
    with patch.object(search, '_clinic_now', return_value=datetime(2026, 10, 5, 10, tzinfo=ZoneInfo('Europe/Prague'))), \
         patch.object(search, 'load_doctors', return_value=[{'doctor_id':15, 'doctor_name':'Test doctor'}]), \
         patch.object(search, 'load_dermatoscope_blockers', return_value=[]), \
         patch.object(engine, 'find_schedule_contexts', return_value=[{'idprac':1, 'typtyd':4, 'dentyd':5}]), \
         patch.object(engine, 'load_schedule_blocks', return_value=[('11:15',30,15)]), \
         patch.object(engine, 'load_appointments', return_value=[]) as appointments, \
         patch.object(execution, 'patient_fingerprint', return_value='verified'), \
         patch.object(writer, '_insert_appointment') as insert:
        # Positive control: real search and slot calculation produce a valid
        # offer and the staff precondition accepts it before occupancy changes.
        option = writer._find_exact_bookable_option(cursor, request)
        assert option.get('error') is None
        assert option['start_time'] == '11:15'
        payload = {'action':'create', 'patient':{'idpac':1, 'fingerprint':'verified'},
                   'source':[], 'offer':offer_snapshot(option)}
        execution.validate_payload(cursor, None, payload)

        # Only the data-loader output changes; no availability/search/approval
        # result is mocked. Both production callers must now reject the slot.
        appointments.return_value = [('11:15','11:15')]
        with pytest.raises(ProposalConflict, match='no longer available'):
            execution.validate_payload(cursor, None, payload)
        result = writer._create_appointments(cursor, request, {})
        assert result['ok'] is False
        assert result['status'] == 'slot_not_bookable'
        insert.assert_not_called()


@pytest.mark.parametrize('minutes,end', [(10, '11:25'), (15, '11:30')])
def test_zero_duration_blocks_actual_cell_and_keeps_next_cell(minutes, end):
    _, occupied, free = compute_slots([('11:15', minutes * 2, minutes)], [('11:15', '11:15')])
    assert [x.strftime('%H:%M') for x in occupied] == ['11:15']
    assert [x.strftime('%H:%M') for x in free] == [end]


def test_mixed_duration_uses_cell_at_appointment_time():
    _, occupied, free = compute_slots([('09:00', 20, 10), ('11:15', 30, 15)], [('11:15', '11:15')])
    assert [x.strftime('%H:%M') for x in occupied] == ['11:15']
    assert [x.strftime('%H:%M') for x in free] == ['09:00', '09:10', '11:30']


@pytest.mark.parametrize('overlapping_reservation_present', [True, False])
@pytest.mark.parametrize('reverse_order', [True, False])
def test_oct9_overlap_does_not_hide_original_zero_duration_occupancy(
        overlapping_reservation_present, reverse_order):
    # Sanitized Oct 9 MAIN observation: original zero-length row, a later
    # overlapping booking, and the next booked cell. Removing the later
    # overlap must not release the original GUI appointment's cell.
    appointments = [('11:15', '11:15'), ('11:30', '11:45')]
    if overlapping_reservation_present:
        appointments.append(('11:15', '11:30'))
    if reverse_order:
        appointments.reverse()
    _, occupied, free = compute_slots([('11:15', 45, 15)], appointments)
    assert [x.strftime('%H:%M') for x in occupied] == ['11:15', '11:30']
    assert [x.strftime('%H:%M') for x in free] == ['11:45']


@pytest.mark.parametrize('booking', [
    ('11:16', '11:16'), ('12:00', '12:00'), ('11:30', '11:15'),
    (None, '11:30'), ('11:15', None), ('invalid', '11:30'),
])
def test_ambiguous_intervals_still_fail_closed(booking):
    with pytest.raises(CalendarDataUnavailable):
        compute_slots([('11:15', 30, 15)], [booking])


def test_main_data_error_is_not_relabelled_as_laser_failure(tmp_path):
    config = tmp_path / 'laser.json'
    config.write_text(json.dumps(dict(enabled=True, calendar_id=5, workplace_id=1, database='LASER')))
    connection = Mock()
    connection.cursor.return_value.fetchone.return_value = (5,)
    failure = CalendarDataUnavailable('Invalid MAIN appointment interval')
    with patch.object(laser_calendar, 'CONFIG_PATH', config), \
         patch.dict(sys.modules, {'fdb': SimpleNamespace(connect=Mock(return_value=connection))}), \
         patch('db._load_db_config', return_value=dict(host='test', port=3050, database='MAIN', username='test', password='test')):
        with pytest.raises(CalendarDataUnavailable) as raised:
            with laser_calendar.open_scan_calendar():
                raise failure
    assert raised.value is failure
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
