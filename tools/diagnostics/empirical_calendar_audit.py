"""Read-only, patient-free comparison of raw calendars and OBJOBJ_SEL.

Run on the database host from the repository root. Emits technical appointment
IDs for local UI reconciliation, never patient IDs, names or free text.
No clinical interpretation is inferred from type/activity IDs.
"""
import hashlib
import json
import random
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'scripts'))
import fdb
from db import _load_db_config
from availability_engine import find_schedule_contexts

START, END = date(2026, 9, 1), date(2026, 11, 30)
SEED = 20261007
FIELDS = 'IDOBJ, DATUM, DATUMDO, CAS, CASDO, IDUZI, IDPRAC, TYP, IDCINNOSTI, REZERVACE, COLORID'


def records(cursor, sql, args=()):
    cursor.execute(sql, args)
    names = [col[0].strip().lower() for col in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def expected_occurrences(rows, day):
    result = []
    for row in rows:
        start, end, typ = row['datum'], row['datumdo'], row['typ']
        if typ not in (9, 10):
            matches = typ is not None and start == day
        else:
            matches = start <= day and end is not None and day <= end
            if matches and typ == 10:
                matches = (day - start).days % 7 == 0
        if matches:
            occurrence = dict(row)
            occurrence['datum'] = day
            result.append(occurrence)
    return result


def signature(row):
    return tuple(str(row[name.strip().lower()]) for name in FIELDS.split(','))


def main():
    config = _load_db_config()
    laser = json.loads((Path('config') / 'laser_calendar.local.json').read_text(encoding='utf-8-sig'))
    random_days = sorted(random.Random(SEED).sample(
        [START + timedelta(days=n) for n in range((END - START).days + 1)], 12))
    output = {'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'range': [str(START), str(END)], 'seed': SEED,
              'random_days': list(map(str, random_days)), 'databases': {}}
    for namespace, database in [('MAIN', config['database']), ('LASER', laser['database'])]:
        con = fdb.connect(host=config['host'], port=config['port'], database=database,
                          user=config['username'], password=config['password'],
                          charset=config.get('charset', 'UTF8'))
        try:
            # Stable snapshot within each DB; no claim of cross-DB atomicity.
            con.default_tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read,
                               fdb.isc_tpb_concurrency, fdb.isc_tpb_nowait)
            cur = con.cursor()
            rows = records(cur, f'SELECT {FIELDS} FROM OBJOBJ WHERE '
                '(DATUM BETWEEN ? AND ?) OR (TYP IN (9,10) AND DATUM<=? AND DATUMDO>=?)',
                (START, END, END, START))
            dbout = {'raw_row_count': len(rows), 'type_activity_counts': [], 'days': {}}
            dbout['recurrence_inventory'] = records(cur,
                'SELECT TYP, COUNT(*) AS N, MIN(DATUM) AS FIRST_DATE, MAX(DATUMDO) AS LAST_DATE '
                'FROM OBJOBJ WHERE TYP IN (9,10) GROUP BY TYP')
            dbout['exception_inventory'] = records(cur,
                'SELECT COUNT(*) AS N, MIN(DATUM) AS FIRST_DATE, MAX(DATUM) AS LAST_DATE FROM OBSODLIS')
            dbout['historical_exception_checks'] = []
            exception_days = records(cur,
                'SELECT DISTINCT DATUM, IDPRAC FROM OBSODLIS ORDER BY DATUM DESC, IDPRAC')
            for item in exception_days:
                day, workplace = item['datum'], item['idprac']
                exception_rows = records(cur,
                    'SELECT IDUZI, CAS, DOBA, INTERVAL, OBJED FROM OBSODLIS WHERE DATUM=? AND IDPRAC=?',
                    (day, workplace))
                effective = records(cur,
                    'SELECT IDUZI, CAS, DOBA, INTERVAL FROM OBSDNE_PRAVODLIS_SEL(?,4,?,?)',
                    (day, day.isoweekday(), workplace))
                enabled = [r for r in exception_rows if r['objed'] == 'A']
                comparable = lambda r: tuple(str(r[k]) for k in ('iduzi','cas','doba','interval'))
                missed = []
                for doctor in sorted({r['iduzi'] for r in effective}):
                    contexts = find_schedule_contexts(cur, doctor, day)
                    if not any(c['idprac'] == workplace for c in contexts):
                        missed.append(doctor)
                dbout['historical_exception_checks'].append({
                    'date': day, 'workplace': workplace, 'exception_rows': exception_rows,
                    'procedure_rows': effective,
                    'enabled_exception_matches': Counter(map(comparable, enabled)) == Counter(map(comparable, effective)) if enabled else None,
                    'effective_doctors_missing_api_context': missed,
                    'week_type_parameter': 4})
            dbout['schedule_patterns'] = records(cur,
                'SELECT IDUZI, IDPRAC, TYPTYD, DENTYD, CAS, DOBA, INTERVAL, OBJED '
                'FROM OBSPRAC WHERE PLATIOD<=? AND (PLATIDO IS NULL OR PLATIDO>=?) '
                'ORDER BY IDUZI, IDPRAC, DENTYD, CAS', (END, START))
            counts = Counter((r['typ'], r['idcinnosti']) for r in rows)
            for (typ, activity), count in sorted(counts.items(), key=lambda item: str(item[0])):
                dbout['type_activity_counts'].append({'typ': typ, 'activity': activity, 'count': count})
            # Target one example of each observed type/activity alongside random days.
            targeted = {}
            for row in sorted(rows, key=lambda r: (r['datum'], r['idobj'])):
                if START <= row['datum'] <= END:
                    targeted.setdefault(str((row['typ'], row['idcinnosti'])), row['datum'])
            exceptions = records(cur, 'SELECT DATUM, IDPRAC, IDUZI, CAS, DOBA, INTERVAL, OBJED '
                                  'FROM OBSODLIS WHERE DATUM BETWEEN ? AND ? ORDER BY DATUM, IDPRAC, IDUZI, CAS', (START, END))
            dbout['schedule_exceptions'] = exceptions
            dbout['targeted_type_days'] = targeted
            days = set(random_days) | set(targeted.values()) | {date(2026, 10, 7), date(2026, 10, 2)}
            days.update(r['datum'] for r in exceptions[:10])
            for day in sorted(days):
                actual = records(cur, f'SELECT {FIELDS} FROM OBJOBJ_SEL(NULL,NULL,NULL,NULL,?,?)', (day, day))
                expected = expected_occurrences(rows, day)
                left, right = Counter(map(signature, expected)), Counter(map(signature, actual))
                dbout['days'][str(day)] = {'raw_expanded_count': len(expected),
                    'procedure_count': len(actual), 'match': left == right,
                    'missing_from_procedure': list((left - right).elements()),
                    'unexpected_in_procedure': list((right - left).elements()),
                    'procedure_rows': actual}
            cur.execute('SELECT RDB$PROCEDURE_SOURCE FROM RDB$PROCEDURES WHERE RDB$PROCEDURE_NAME=?', ('OBJOBJ_SEL',))
            source = cur.fetchone()[0]
            if hasattr(source, 'read'):
                source = source.read()
            if isinstance(source, str):
                source = source.encode('utf-8')
            dbout['procedure_sha256'] = hashlib.sha256(source).hexdigest()
            output['databases'][namespace] = dbout
        finally:
            con.rollback()
            con.close()
    print(json.dumps(output, ensure_ascii=True, default=str, indent=2))


if __name__ == '__main__':
    main()
