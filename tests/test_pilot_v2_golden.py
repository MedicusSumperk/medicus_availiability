"""Business regression cases. Frozen dates, no LLM, network, or live writes.

Schedule/appointment rows are fixture inputs, not simulated evidence that
Firebird expands recurrence or applies its exception procedures correctly.
"""
import copy
import json
import sys
import unittest
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import availability_engine as engine
import availability_search as search
import laser_calendar as laser

CASES = json.loads((ROOT / 'tests/fixtures/pilot_v2_golden.json').read_text(encoding='utf-8'))['cases']
RULES = json.loads((ROOT / 'config/business_rules.example.json').read_text(encoding='utf-8-sig'))


def run_case(case):
    data = case['input']
    kind = case['kind']
    if kind == 'intervals':
        _, _, free = engine.compute_slots(data['blocks'], data['appointments'])
        return {'offers': [engine.format_time(t) for t in free]}
    if kind == 'scan':
        available = laser.interval_is_available(date.fromisoformat(data['date']), data['start'], data['end'], data['blocks'], data['appointments'])
        return {'available': available}
    if kind == 'missing_mapping':
        with patch.object(laser, 'CONFIG_PATH', ROOT / 'tests' / 'nonexistent_scan_mapping.json'):
            with laser.open_scan_calendar():
                raise AssertionError('Missing mapping must never yield a calendar')
    if kind == 'doctor':
        doctors, detail, _ = search._resolve_doctor_filter(data['doctors'], data.get('doctor_id'), data.get('doctor_name'))
        return {'doctor_ids': [d['doctor_id'] for d in doctors], 'match_type': detail['match_type']}
    if kind != 'search':
        raise AssertionError('Unimplemented golden adapter: ' + kind)

    rules = copy.deepcopy(RULES)
    for service, overrides in data.get('service_overrides', {}).items():
        rules['services'][service].update(overrides)
    doctors = data.get('doctors', [{'doctor_id': 2, 'doctor_name': 'Test Doctor'}])

    def day_availability(_cursor, doctor, target_date):
        rows = [row for row in data['calendars'] if row['doctor_id'] == doctor['doctor_id'] and row['date'] == target_date.isoformat()]
        contexts = []
        for row in rows:
            _, _, free = engine.compute_slots(row['blocks'], row.get('appointments', []))
            contexts.append({'idprac': row.get('workplace', 1),
                             'slot_interval_minutes': engine.primary_schedule_interval(row['blocks']),
                             'free_slots': [engine.format_time(t) for t in free]})
        return {'has_schedule': bool(rows), 'contexts': contexts}

    class FixtureScan:
        def is_available(self, day, start, end):
            if data.get('scan_error'):
                raise laser.ScanCalendarUnavailable('Fixture: unavailable external calendar')
            scan = data['scan']
            return laser.interval_is_available(day, start, end, scan['blocks'], scan['appointments'])

    @contextmanager
    def scan_resource():
        yield FixtureScan()

    with (patch.object(search, 'load_business_rules', return_value=rules),
          patch.object(search, '_clinic_now', return_value=datetime.fromisoformat(data.get('now', '2026-10-01T06:00:00+02:00'))),
          patch.object(search, 'load_doctors', return_value=doctors),
          patch.object(search, 'compute_day_availability', side_effect=day_availability),
          patch.object(search, 'load_dermatoscope_blockers', return_value=[]),
          patch.object(search, 'open_scan_calendar', side_effect=scan_resource)):
        response = search.search_availability(None, data['request'], base_config=search.DEFAULT_CONFIG)
    return {'offers': [{'date': o['date'], 'doctor_id': o['doctor_id'], 'time': o['start_time'],
                        'arrival': (o.get('scan_slot') or {}).get('start_time', o['spoken_time_label'])}
                       for o in response['options']]}


class PilotGoldenTests(unittest.TestCase):
    def test_fixture_contract(self):
        self.assertGreaterEqual(len(CASES), 20)
        self.assertEqual(len(CASES), len({c['id'] for c in CASES}))
        for case in CASES:
            for field in ('id', 'kind', 'input', 'expected_business_result', 'expected', 'why', 'evidence'):
                self.assertTrue(case.get(field), (case.get('id'), field))


def make_test(case):
    def test(self):
        expected = case['expected']
        error_types = {'ValueError': ValueError, 'ScanCalendarUnavailable': laser.ScanCalendarUnavailable}
        if 'error' in expected:
            with self.assertRaises(error_types[expected['error']], msg=case['why']):
                run_case(case)
        else:
            self.assertEqual(run_case(case), expected, case['why'])
    test.__doc__ = case['expected_business_result']
    return test


for case in CASES:
    setattr(PilotGoldenTests, 'test_' + case['id'], make_test(case))

if __name__ == '__main__':
    unittest.main()
