"""Read actual scan-calendar occupancy; never infer availability on read failure."""
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import json
from pathlib import Path

from availability_engine import find_schedule_contexts, load_schedule_blocks, load_appointments, to_time

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config' / 'laser_calendar.local.json'


class ScanCalendarUnavailable(RuntimeError):
    pass


def interval_is_available(day, start, end, schedules, bookings):
    begin = datetime.combine(day, to_time(start))
    finish = datetime.combine(day, to_time(end))
    if finish <= begin:
        return False
    spans = []
    for raw_start, duration, _interval in schedules:
        if duration is None or int(duration) < 0:
            raise ScanCalendarUnavailable('Invalid scan schedule')
        a = datetime.combine(day, to_time(raw_start))
        spans.append((a, a + timedelta(minutes=int(duration))))
    covered = begin
    for a, b in sorted(spans):
        if a > covered:
            break
        if b > covered:
            covered = b
        if covered >= finish:
            break
    if covered < finish:
        return False
    for a, b in bookings:
        if a is None or b is None or to_time(b) <= to_time(a):
            raise ScanCalendarUnavailable('Invalid scan reservation interval')
        if begin.time() < to_time(b) and finish.time() > to_time(a):
            return False
    return True


class ScanCalendar:
    def __init__(self, cursor, calendar_id, workplace_id, *, exclude_ids=()):
        self.cursor = cursor
        self.calendar_id = calendar_id
        self.workplace_id = workplace_id
        self.exclude_ids = tuple(exclude_ids)
        self.days = {}

    def is_available(self, day, start, end):
        if day not in self.days:
            contexts = find_schedule_contexts(self.cursor, self.calendar_id, day)
            blocks = []
            for ctx in contexts:
                if ctx['idprac'] == self.workplace_id:
                    blocks.extend(load_schedule_blocks(self.cursor, day, ctx['typtyd'], ctx['dentyd'], self.workplace_id, self.calendar_id))
            # Every appointment in this physical calendar blocks capacity,
            # regardless of activity/color. The DB procedure expands recurrence.
            appointments = load_appointments(self.cursor, self.workplace_id, self.calendar_id, day,
                **({'exclude_ids': self.exclude_ids} if self.exclude_ids else {}))
            self.days[day] = blocks, appointments
        return interval_is_available(day, start, end, *self.days[day])


@contextmanager
def open_scan_calendar():
    connection = None
    try:
        import fdb
        from db import _load_db_config
        config = json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig'))
        if config.get('enabled') is not True:
            raise ScanCalendarUnavailable('Scan calendar is not enabled')
        calendar_id = int(config['calendar_id'])
        workplace_id = int(config['workplace_id'])
        database = str(config['database'])
        base = _load_db_config()
        if calendar_id <= 0 or workplace_id <= 0 or not database or database == base['database']:
            raise ScanCalendarUnavailable('Invalid scan calendar mapping')
        connection = fdb.connect(host=base['host'], port=base['port'], database=database,
                                 user=base['username'], password=base['password'], charset=base.get('charset', 'UTF8'))
        cursor = connection.cursor()
        cursor.execute('SELECT IDUZI FROM UZIVATEL WHERE IDUZI=?', (calendar_id,))
        if cursor.fetchone() is None:
            raise ScanCalendarUnavailable('Unknown scan calendar')
        yield ScanCalendar(cursor, calendar_id, workplace_id)
    except ScanCalendarUnavailable:
        raise
    except Exception as exc:
        # Never expose credentials, SQL parameters or connection details.
        raise ScanCalendarUnavailable('Scan calendar cannot be verified') from exc
    finally:
        if connection is not None:
            try:
                connection.rollback()
            finally:
                connection.close()
