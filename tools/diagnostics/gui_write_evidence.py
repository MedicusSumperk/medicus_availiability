"""Read-only OBJOBJ before/after evidence; never performs a Medicus write.

Run capture on the DB host. Use the same private MEDICUS_AUDIT_KEY for all
snapshots in a session. Output omits patient fields and free text, retaining
keyed field fingerprints to detect changes. It remains restricted audit data.
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

VISIBLE = {'IDOBJ', 'IDOBJPROC', 'DATUM', 'DATUMDO', 'CAS', 'CASDO', 'IDUZI', 'IDPRAC',
           'TYP', 'IDCINNOSTI', 'REZERVACE', 'COLORID', 'AKCE'}


def fingerprint(value, key):
    if hasattr(value, 'read'):
        value = value.read()
    if isinstance(value, bytes):
        value = {'bytes': value.hex()}
    encoded = json.dumps(value, default=str, sort_keys=True, ensure_ascii=True).encode()
    return hmac.new(key, encoded, hashlib.sha256).hexdigest()


def protect_row(row, key):
    return {'values': {k: v for k, v in row.items() if k in VISIBLE},
            'fingerprints': {k: fingerprint(v, key) for k, v in row.items()}}


def related_delta(before, after):
    if set(before) != set(after):
        raise ValueError('Related table coverage differs')
    result = {}
    for table, left in before.items():
        right = after[table]
        if left['columns'] != right['columns']:
            raise ValueError('Related table schema changed')
        signature = lambda row: json.dumps(row['fingerprints'], sort_keys=True)
        old = Counter(map(signature, left['rows']))
        new = Counter(map(signature, right['rows']))
        lookup = {signature(row): row['values'] for row in left['rows'] + right['rows']}
        result[table] = {
            'added': [{'values': lookup[key], 'count': count} for key, count in (new-old).items()],
            'removed': [{'values': lookup[key], 'count': count} for key, count in (old-new).items()],
        }
    return result


def compare(before, after):
    for field in ('schema_version', 'key_id', 'dates'):
        if before[field] != after[field]:
            raise ValueError('Snapshots differ in ' + field)
    if set(before['databases']) != set(after['databases']):
        raise ValueError('Database coverage differs')
    changes = {}
    for namespace, left in before['databases'].items():
        right = after['databases'][namespace]
        if left['columns'] != right['columns']:
            raise ValueError('Database schema changed')
        old, new = left['rows'], right['rows']
        changed = []
        for identifier in sorted(old.keys() & new.keys()):
            fields = [k for k in left['columns']
                      if old[identifier]['fingerprints'][k] != new[identifier]['fingerprints'][k]]
            if fields:
                changed.append({'idobj': identifier, 'fields': fields,
                                'before': old[identifier]['values'],
                                'after': new[identifier]['values']})
        changes[namespace] = {
            'added_to_scope': [new[k]['values'] for k in sorted(new.keys() - old.keys())],
            'removed_from_scope': [old[k]['values'] for k in sorted(old.keys() - new.keys())],
            'changed': changed,
            'related': related_delta(left.get('related', {}), right.get('related', {})),
        }
    return {'before': before['captured_at_utc'], 'after': after['captured_at_utc'],
            'databases': changes,
            'limits': ['Date-scoped OBJOBJ/OBJHIST and linked OBJPROC; absence is not proof of deletion.',
                       'MAIN and LASER snapshots are not atomic together.',
                       'Concurrent staff changes require reconciliation in the GUI.',
                       'Fingerprints do not establish patient identity or cross-DB links.']}


def capture(days, key):
    # Deferred imports allow offline comparison without a Firebird installation.
    sys.path.insert(0, str(Path.cwd() / 'scripts'))
    import fdb
    from db import _load_db_config
    config = _load_db_config()
    laser = json.loads(Path('config/laser_calendar.local.json').read_text(encoding='utf-8-sig'))
    output = {'schema_version': 2, 'key_id': fingerprint('audit-session', key),
              'dates': sorted(set(days)), 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
              'databases': {}}
    for namespace, database in [('MAIN', config['database']), ('LASER', laser['database'])]:
        con = fdb.connect(host=config['host'], port=config['port'], database=database,
                          user=config['username'], password=config['password'],
                          charset=config.get('charset', 'UTF8'))
        try:
            con.default_tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read,
                               fdb.isc_tpb_concurrency, fdb.isc_tpb_nowait)
            cursor = con.cursor()
            rows = {}
            columns = []
            for day in output['dates']:
                cursor.execute('SELECT * FROM OBJOBJ WHERE DATUM=? OR '
                               '(TYP IN (9,10) AND DATUM<=? AND DATUMDO>=?)',
                               (day, day, day))
                columns = [c[0].strip().upper() for c in cursor.description]
                for values in cursor.fetchall():
                    row = dict(zip(columns, values))
                    rows[str(row['IDOBJ'])] = protect_row(row, key)
            related = {}
            marks = ','.join('?' for _ in output['dates'])
            appointment_ids = [int(identifier) for identifier in rows]
            live_predicate = 'IDOBJ IN (' + ','.join('?' for _ in appointment_ids) + ')' if appointment_ids else '1=0'
            queries = {
                'OBJHIST': (f'SELECT * FROM OBJHIST WHERE DATUM IN ({marks})', output['dates']),
                'OBJPROC': (f'SELECT * FROM OBJPROC WHERE ({live_predicate}) OR IDOBJ IN ('
                            f'SELECT IDOBJ FROM OBJHIST WHERE DATUM IN ({marks}))', appointment_ids+output['dates']),
            }
            for table, (query, parameters) in queries.items():
                cursor.execute(query, parameters)
                fields = [c[0].strip().upper() for c in cursor.description]
                protected = [protect_row(dict(zip(fields, values)), key) for values in cursor.fetchall()]
                related[table] = {'columns': fields, 'rows': protected}
            output['databases'][namespace] = {'columns': columns, 'rows': rows, 'related': related}
        finally:
            con.rollback()
            con.close()
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    read = commands.add_parser('capture')
    read.add_argument('--date', action='append', required=True, type=date.fromisoformat)
    diff = commands.add_parser('compare')
    diff.add_argument('before', type=Path)
    diff.add_argument('after', type=Path)
    args = parser.parse_args()
    if args.command == 'capture':
        key = os.environ.get('MEDICUS_AUDIT_KEY', '').encode()
        if len(key) < 32:
            parser.error('Set a private random MEDICUS_AUDIT_KEY of at least 32 bytes')
        result = capture(args.date, key)
    else:
        result = compare(json.loads(args.before.read_text(encoding='utf-8-sig')),
                         json.loads(args.after.read_text(encoding='utf-8-sig')))
    print(json.dumps(result, default=str, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
