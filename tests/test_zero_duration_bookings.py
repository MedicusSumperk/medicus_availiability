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


@pytest.mark.parametrize('minutes,end', [(10, '11:25'), (15, '11:30')])
def test_zero_duration_blocks_actual_cell_and_keeps_next_cell(minutes, end):
    _, occupied, free = compute_slots([('11:15', minutes * 2, minutes)], [('11:15', '11:15')])
    assert [x.strftime('%H:%M') for x in occupied] == ['11:15']
    assert [x.strftime('%H:%M') for x in free] == [end]


def test_mixed_duration_uses_cell_at_appointment_time():
    _, occupied, free = compute_slots([('09:00', 20, 10), ('11:15', 30, 15)], [('11:15', '11:15')])
    assert [x.strftime('%H:%M') for x in occupied] == ['11:15']
    assert [x.strftime('%H:%M') for x in free] == ['09:00', '09:10', '11:30']


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
