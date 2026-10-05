"""Read-only reconciliation evidence for interrupted paired writes.

This command never updates the journal, resolves limbo transactions, or writes
to Medicus. Matching visible rows is evidence for an administrator, not an
automatic authorization to retry an uncertain operation.
"""
import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fdb
from appointment_write import _fetch_appointment_rows
from paired_appointments import pair_token


def read_attempt(path, request_id):
    source = Path(path)
    if not source.is_absolute() or not source.is_file():
        raise ValueError('Existing absolute journal path required')
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute('SELECT state,result FROM attempts WHERE key=?', (request_id,)).fetchone()
    if row is None:
        raise ValueError('Request not found')
    return {'state': row[0], 'result': json.loads(row[1]) if row[1] else None}


def inspect_attempt(attempt, main_cursor, laser_cursor):
    report = {'journal_state': attempt['state'], 'journal_changed': False,
              'safe_to_retry': False, 'automatic_resolution': False}
    result = attempt.get('result')
    if not result or result.get('ok') is not True:
        return dict(report, observation='no_recorded_commit_intent')
    operation = result.get('status')
    if operation not in ('created', 'rescheduled', 'cancelled'):
        raise ValueError('Unknown recorded operation')
    expected = result.get('appointments') or []
    if len(expected) != 2 or {r.get('database') for r in expected} != {'MAIN', 'LASER'}:
        raise ValueError('Incomplete recorded pair')
    token = result.get('pair_id')
    if not token:
        raise ValueError('Missing pair identity')
    checks = []
    fields = ('idobj', 'idpac', 'idprac', 'doctor_id', 'date', 'start_time', 'end_time', 'typ', 'prisel', 'idcinnosti')
    for role, cursor in (('MAIN', main_cursor), ('LASER', laser_cursor)):
        wanted = next(row for row in expected if row['database'] == role)
        if pair_token(wanted.get('info'), role) != token:
            raise ValueError('Recorded pair identity mismatch')
        rows = _fetch_appointment_rows(cursor, [int(wanted['idobj'])])
        check = {'database': role, 'idobj': int(wanted['idobj']), 'present': len(rows) == 1,
                 'matches_recorded_result': False}
        if len(rows) == 1:
            row = rows[0]
            try:
                identity_matches = pair_token(row.get('info'), role) == token
            except ValueError:
                identity_matches = False
            check['matches_recorded_result'] = identity_matches and all(row.get(f) == wanted.get(f) for f in fields)
        checks.append(check)
    if operation == 'cancelled':
        # Absence could mean rollback, another deletion, an in-doubt transaction,
        # or incomplete evidence. Never turn it into a replayable success here.
        observation = 'both_rows_absent' if all(not c['present'] for c in checks) else 'cancellation_not_fully_visible'
    elif all(c['matches_recorded_result'] for c in checks):
        observation = 'both_expected_rows_visible'
    elif any(c['present'] for c in checks):
        observation = 'partial_or_modified_pair'
    else:
        observation = 'neither_expected_row_visible'
    return dict(report, operation=operation, observation=observation, checks=checks)


def inspect_live(path, request_id):
    from db import connect_to_db, _load_db_config
    from laser_calendar import CONFIG_PATH
    attempt = read_attempt(path, request_id)
    if not attempt.get('result') or attempt['result'].get('ok') is not True:
        return inspect_attempt(attempt, None, None)
    cfg = json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig'))
    if cfg.get('enabled') is not True:
        raise ValueError('Laser read mapping is disabled')
    base = _load_db_config()
    main = scan = None
    try:
        main = connect_to_db()
        scan = fdb.connect(host=base['host'], port=base['port'], database=cfg['database'],
                           user=base['username'], password=base['password'], charset=base.get('charset', 'UTF8'))
        tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read, fdb.isc_tpb_concurrency, fdb.isc_tpb_nowait)
        for connection in (main, scan):
            connection.begin(tpb)
        report = inspect_attempt(attempt, main.cursor(), scan.cursor())
        report['limits'] = ['Separate read-only snapshots; not an atomic cross-database observation',
                            'No limbo resolution or historical ownership proof; administrator must reconcile before retry']
        return report
    finally:
        # A failed rollback/close on one database must not skip the other.
        # Preserve the original inspection failure; otherwise surface cleanup
        # failure so the CLI cannot report an unqualified successful check.
        inspection_failed = sys.exc_info()[0] is not None
        cleanup_error = None
        for connection in (scan, main):
            if connection is not None:
                try:
                    connection.rollback()
                except Exception as exc:
                    cleanup_error = cleanup_error or exc
                finally:
                    try:
                        connection.close()
                    except Exception as exc:
                        cleanup_error = cleanup_error or exc
        if cleanup_error is not None and not inspection_failed:
            raise cleanup_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', required=True)
    parser.add_argument('--request-id', required=True)
    args = parser.parse_args()
    try:
        report = inspect_live(args.journal, args.request_id)
    except Exception as exc:
        print(json.dumps({'observation': 'unavailable', 'safe_to_retry': False,
                          'journal_changed': False, 'error_type': type(exc).__name__}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
