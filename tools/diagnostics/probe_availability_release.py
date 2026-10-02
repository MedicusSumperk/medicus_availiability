"""Bounded MAIN/LASER read-only check; no patient fields or production changes."""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

candidate = Path('C:/db_bridge/staging/medicus-availability-v2')
production = Path('C:/db_bridge/medicus_availiability')
sys.path.insert(0, str(candidate / 'scripts'))
import fdb
import db
import business_rules
import availability_search as search
import laser_calendar

db.CONFIG_PATH = production / 'config/db_config.local.json'
business_rules.LOCAL_RULES_PATH = production / 'config/business_rules.local.json'
search.LOCAL_CONFIG_PATH = production / 'config/agent_context.local.json'
laser_calendar.CONFIG_PATH = production / 'config/laser_calendar.local.json'

original_connect = fdb.connect


def read_only_connect(*args, **kwargs):
    connection = original_connect(*args, **kwargs)
    connection.default_tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read,
                              fdb.isc_tpb_concurrency, fdb.isc_tpb_nowait)
    return connection


fdb.connect = read_only_connect


def main():
    rules = business_rules.load_business_rules()
    output = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'read_only_transactions': True, 'production_config_changed': False,
              'checks': []}
    connection = db.connect_to_db()
    try:
        cursor = connection.cursor()
        for day in ('2026-10-07', '2026-10-03', '2026-10-28'):
            result = search.search_availability(cursor, {'service': 'skin',
                'date_from': day, 'date_to': day, 'doctor_id': 12, 'limit': 10})
            options = result['options']
            for option in options:
                target = date.fromisoformat(day)
                cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,?,?,?,?)',
                               (option['idprac'], option['doctor_id'], target, target))
                assert not any(option['start_time'] < b.strftime('%H:%M')
                               and option['end_time'] > a.strftime('%H:%M') for a, b in cursor.fetchall())
            if day != '2026-10-07':
                assert not options, 'Weekend/holiday was offered'
            output['checks'].append({'service': 'skin', 'date': day,
                                    'option_count': len(options), 'raw_conflicts_checked': True})

        enabled = business_rules.service_enabled_for_availability(rules, 'dermatoscope_first')
        output['production_dermatoscope_availability_enabled'] = enabled
        # Diagnostic-only: examine combined capacity even if this service is
        # disabled for the live agent. Never persist rules or enable booking.
        diagnostic_rules = json.loads(json.dumps(rules))
        diagnostic_rules['services']['dermatoscope_first']['agent_can_offer_availability'] = True
        search.load_business_rules = lambda: diagnostic_rules
        result = search.search_availability(cursor, {'service': 'dermatoscope_first',
            'date_from': '2026-10-07', 'date_to': '2026-10-07',
            'doctor_id': 12, 'limit': 100, 'max_limit': 100})
        offered = {item['start_time'] for item in result['options']}
        candidates = [('15:00', '15:10', '14:45'), ('15:10', '15:20', '14:55'),
                      ('15:50', '16:00', '15:35')]
        day = date(2026, 10, 7)
        cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,1,?,?,?)', (12, day, day))
        main_intervals = [(a.strftime('%H:%M'), b.strftime('%H:%M')) for a, b in cursor.fetchall()]
        with laser_calendar.open_scan_calendar() as scan:
            scan.cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,?,?,?,?)',
                                (scan.workplace_id, scan.calendar_id, day, day))
            scan_intervals = [(a.strftime('%H:%M'), b.strftime('%H:%M')) for a, b in scan.cursor.fetchall()]
        incident = []
        for start, end, scan_start in candidates:
            main_conflicts = sum(start < b and end > a for a, b in main_intervals)
            scan_conflicts = sum(scan_start < b and start > a for a, b in scan_intervals)
            if main_conflicts or scan_conflicts:
                assert start not in offered, 'Occupied combined appointment was offered'
            incident.append({'exam_start': start, 'main_conflicts': main_conflicts,
                             'scan_conflicts': scan_conflicts, 'offered': start in offered})
        output['diagnostic_combined_capacity'] = {'date': str(day), 'option_count': len(offered),
            'all_conflicting_incident_options_excluded': True, 'incident': incident}
        positive = search.search_availability(cursor, {'service': 'dermatoscope_first',
            'date_from': '2026-10-08', 'date_to': '2026-10-16',
            'doctor_id': 12, 'limit': 3})
        checked = []
        with laser_calendar.open_scan_calendar() as scan:
            for option in positive['options']:
                target = date.fromisoformat(option['date'])
                cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,?,?,?,?)',
                               (option['idprac'], option['doctor_id'], target, target))
                busy = cursor.fetchall()
                assert not any(option['start_time'] < b.strftime('%H:%M')
                               and option['end_time'] > a.strftime('%H:%M') for a, b in busy)
                scan_slot = option['scan_slot']
                scan.cursor.execute('SELECT CAS,CASDO FROM OBJOBJ_SEL(NULL,NULL,?,?,?,?)',
                                    (scan.workplace_id, scan.calendar_id, target, target))
                assert not any(scan_slot['start_time'] < b.strftime('%H:%M')
                               and scan_slot['end_time'] > a.strftime('%H:%M') for a, b in scan.cursor.fetchall())
                checked.append({'date': option['date'], 'exam_start': option['start_time'],
                                'raw_calendar_conflicts': 0})
        output['diagnostic_future_options_checked'] = checked
    finally:
        connection.rollback()
        connection.close()
    print(json.dumps(output, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
