"""Bounded production-code MAIN/LASER probe; no writes or patient identifiers."""
import json
import hashlib
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_availability_release as setup

# The staged modules must still exactly match the activated production files.
manifest = json.loads(Path('C:/db_bridge/state/availability-v2/activation.json').read_text(encoding='utf-8-sig'))
for module in manifest['modules']:
    for root in (setup.candidate, setup.production):
        content = (root / 'scripts' / module['name']).read_text(encoding='utf-8').replace('\r\n', '\n')
        assert hashlib.sha256(content.encode()).hexdigest() == module['after'], 'Module drift'

def main():
    rules = setup.business_rules.load_business_rules()
    diagnostic = json.loads(json.dumps(rules))
    diagnostic['services']['dermatoscope_first']['agent_can_offer_availability'] = True
    setup.search.load_business_rules = lambda: diagnostic
    calls = {'checked': 0, 'available': 0}
    original = setup.laser_calendar.ScanCalendar.is_available
    def observed(self, day, start, end):
        calls['checked'] += 1
        result = original(self, day, start, end)
        calls['available'] += int(result)
        return result
    setup.laser_calendar.ScanCalendar.is_available = observed
    report = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'activated_modules_match': True, 'github_commit': manifest['github_commit'],
              'read_only_transactions': True, 'configuration_persisted': False,
              'diagnostic_availability_override_only': True, 'windows': []}
    connection = setup.db.connect_to_db()
    try:
        cursor = connection.cursor()
        for start, end in [('2026-10-05', '2026-10-09'),
                           ('2026-10-19', '2026-10-23'),
                           ('2026-11-02', '2026-11-06')]:
            result = setup.search.search_availability(cursor, {
                'service': 'dermatoscope_first', 'date_from': start,
                'date_to': end, 'limit': 3})
            checked = []
            with setup.laser_calendar.open_scan_calendar() as scan:
                for option in result['options']:
                    day = date.fromisoformat(option['date'])
                    cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,?,?,?,?)',
                                   (option['idprac'], option['doctor_id'], day, day))
                    assert not any(option['start_time'] < b.strftime('%H:%M') and
                                   option['end_time'] > a.strftime('%H:%M') for a,b in cursor.fetchall())
                    slot = option['scan_slot']
                    scan.cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,?,?,?,?)',
                                        (scan.workplace_id, scan.calendar_id, day, day))
                    assert not any(slot['start_time'] < b.strftime('%H:%M') and
                                   slot['end_time'] > a.strftime('%H:%M') for a,b in scan.cursor.fetchall())
                    assert slot['end_time'] <= option['start_time']
                    checked.append({'date': option['date'], 'doctor_id': option['doctor_id'],
                                    'exam_start': option['start_time'], 'exam_end': option['end_time'],
                                    'scan_start': slot['start_time'], 'scan_end': slot['end_time'],
                                    'raw_calendar_conflicts': 0})
            report['windows'].append({'from':start,'to':end,'scanned':result.get('scanned'),
                                      'options_checked': checked, 'scan_gate_counts':dict(calls)})
            if checked:
                break
    finally:
        connection.rollback()
        connection.close()
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
