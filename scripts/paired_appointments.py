"""MAIN physician + anonymous LASER scanner bookings, without schema changes.

Only pairs created here can be moved/cancelled automatically. Firebird 2PC
owns both writes; the local journal prevents blind retries after uncertain
commits. An interrupted/uncertain attempt requires operator reconciliation.

Staff-first policy: revalidate in a fresh snapshot, without reserving OBJOBJ
against the Medicus GUI. Concurrent inserts after that snapshot can still
collide; staff resolve those collisions. Existing-row update conflicts and 2PC
remain enforced by Firebird. This is not a guarantee of exclusive slot ownership.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

import fdb
import appointment_write as aw
import laser_calendar as laser
from db import _load_db_config
from approval_store import ProposalConflict

PAIR = re.compile(r'^AI_PAIR_V1:([0-9a-f]{32}):(MAIN|LASER)\|')


class PairUnavailable(ValueError):
    """A safe public error, without SQL/credentials/patient details."""


def failure(status):
    return {'ok': False, 'status': status, 'booking_confirmed': False}


def staff_write_tpb():
    """Fresh, nonblocking snapshot; deliberately no table-wide reservation."""
    tpb = fdb.TPB()
    tpb.isolation_level = fdb.isc_tpb_concurrency
    tpb.lock_resolution = fdb.isc_tpb_nowait
    return tpb


class Journal:
    def __init__(self, path):
        if not path or not Path(path).is_absolute() or not Path(path).parent.is_dir():
            raise PairUnavailable('paired_journal_not_configured')
        self.path = str(path)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS attempts (key TEXT PRIMARY KEY, digest TEXT NOT NULL, state TEXT NOT NULL, result TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db:
                yield db
        finally:
            db.close()

    def claim(self, key, request):
        digest = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT digest,state,result FROM attempts WHERE key=?', (key,)).fetchone()
            if old:
                if old[0] != digest:
                    raise PairUnavailable('request_id_payload_conflict')
                if old[1] in ('committed', 'rejected'):
                    return json.loads(old[2])
                raise PairUnavailable('paired_write_requires_reconciliation')
            if db.execute("SELECT 1 FROM attempts WHERE state NOT IN ('committed','rejected') LIMIT 1").fetchone():
                raise PairUnavailable('paired_write_requires_reconciliation')
            db.execute('INSERT INTO attempts VALUES (?,?,?,NULL)', (key, digest, 'started'))
        return None

    def state(self, key, state, result=None):
        with self.connect() as db:
            db.execute('UPDATE attempts SET state=?,result=? WHERE key=?',
                       (state, json.dumps(result) if result is not None else None, key))


def marker(token, role):
    return f'AI_PAIR_V1:{token}:{role}|'


def pair_token(info, role):
    match = PAIR.match(info or '')
    if match is None or match[2] != role:
        raise PairUnavailable('unmanaged_or_modified_pair_contact_staff')
    return match[1]


def is_pair_request(cursor, request):
    if str(request.get('service', '')).lower() == 'dermatoscope_first':
        return True
    if request.get('action', 'create') in ('cancel', 'reschedule'):
        rows = aw._fetch_appointment_rows(cursor, aw._appointment_ids(request))
        return any(row['idcinnosti'] == 1 or 'AI_PAIR_V1:' in row['info'] for row in rows)
    return False


def mapping():
    cfg = json.loads(laser.CONFIG_PATH.read_text(encoding='utf-8-sig'))
    base = _load_db_config()
    if cfg.get('enabled') is not True or cfg.get('write_enabled') is not True:
        raise PairUnavailable('laser_writes_not_enabled')
    # Explicit, empirically verified mapping; never send a MAIN IDPAC to LASER.
    if (int(cfg.get('calendar_id', 0)), int(cfg.get('workplace_id', 0)), int(cfg.get('booking_activity_id', 0))) != (5, 1, 28):
        raise PairUnavailable('laser_write_mapping_not_verified')
    if str(cfg['database']).replace('\\', '/').casefold() == str(base['database']).replace('\\', '/').casefold():
        raise PairUnavailable('databases_must_differ')
    return cfg, base


def load_pair(main, scan, request, cfg):
    ids = aw._appointment_ids(request)
    if len(ids) != 1:
        raise PairUnavailable('exactly_one_managed_pair_required')
    rows = aw._fetch_appointment_rows(main, ids)
    if len(rows) != 1 or rows[0]['idpac'] != int(request['idpac']):
        raise PairUnavailable('appointment_not_found_or_patient_mismatch')
    physician = rows[0]
    token = pair_token(physician['info'], 'MAIN')
    main.execute('SELECT IDOBJ FROM OBJOBJ WHERE INFO STARTING WITH ?', (marker(token, 'MAIN'),))
    if [row[0] for row in main.fetchall()] != [physician['idobj']]:
        raise PairUnavailable('paired_physician_missing_or_ambiguous')
    scan.execute('SELECT IDOBJ FROM OBJOBJ WHERE INFO STARTING WITH ?', (marker(token, 'LASER'),))
    scan_ids = [r[0] for r in scan.fetchall()]
    if len(scan_ids) != 1:
        raise PairUnavailable('paired_scan_missing_or_ambiguous')
    scanner = aw._fetch_appointment_rows(scan, scan_ids)[0]
    pair_token(scanner['info'], 'LASER')
    expected_end = datetime.fromisoformat(physician['date'] + 'T' + physician['start_time'])
    expected_start = expected_end - timedelta(minutes=15)
    if (physician['idcinnosti'] != 1 or scanner['idpac'] is not None or
        scanner['idcinnosti'] != cfg['booking_activity_id'] or
        scanner['doctor_id'] != cfg['calendar_id'] or scanner['idprac'] != cfg['workplace_id'] or
        scanner['date'] != physician['date'] or scanner['end_time'] != expected_end.strftime('%H:%M') or
        scanner['start_time'] != expected_start.strftime('%H:%M')):
        raise PairUnavailable('paired_rows_modified_contact_staff')
    # Do not silently discard recurrence, external links, procedures or arrived visits.
    for cursor, row in ((main, physician), (scan, scanner)):
        cursor.execute('SELECT IDREC,TYPPROH,IDEXT,IDCAL_EXT,ES_UID,DATUMDO FROM OBJOBJ WHERE IDOBJ=?', (row['idobj'],))
        extra = cursor.fetchone()
        if any(v is not None for v in extra[:5]) or str(extra[5]) != row['date'] or row['typ'] != 1 or row['prisel'] != 'N':
            raise PairUnavailable('paired_rows_modified_contact_staff')
        cursor.execute('SELECT COUNT(*) FROM OBJPROC WHERE IDOBJ=?', (row['idobj'],))
        if cursor.fetchone()[0]:
            raise PairUnavailable('paired_rows_have_procedures_contact_staff')
    return physician, scanner, token


def info_text(request, token, role):
    text = aw._clean(request.get('info')) or 'AI_RECEPTION dermatoscope_first'
    if 'AI_PAIR_V1:' in text:
        raise PairUnavailable('reserved_pair_marker')
    prefix = marker(token, role)
    return prefix + text[:80 - len(prefix)]


def validate_info(cursor, text):
    cursor.execute("SELECT F.RDB$CHARACTER_LENGTH FROM RDB$RELATION_FIELDS RF JOIN RDB$FIELDS F ON F.RDB$FIELD_NAME=RF.RDB$FIELD_SOURCE WHERE RF.RDB$RELATION_NAME='OBJOBJ' AND RF.RDB$FIELD_NAME='INFO'")
    row = cursor.fetchone()
    if not row or row[0] is None or len(text) > int(row[0]):
        raise PairUnavailable('paired_note_too_long')


def option_for_pair(main, scan, request, cfg, *, exclude_main_ids=(), exclude_scan_ids=()):
    option = aw._find_exact_bookable_option(main, dict(request, service='dermatoscope_first'),
        scan_calendar=laser.ScanCalendar(scan, cfg['calendar_id'], cfg['workplace_id'], exclude_ids=exclude_scan_ids),
        **({'exclude_main_ids': exclude_main_ids} if exclude_main_ids else {}))
    if option.get('error'):
        raise PairUnavailable(option['error'])
    slot = option.get('scan_slot') or {}
    end = datetime.fromisoformat(option['date'] + 'T' + option['start_time'])
    if option.get('idcinnosti') != 1 or slot.get('start_time') != (end - timedelta(minutes=15)).strftime('%H:%M') or slot.get('end_time') != end.strftime('%H:%M'):
        raise PairUnavailable('combined_service_mapping_not_verified')
    return option


def insert_pair(main, scan, request, config, cfg):
    option = option_for_pair(main, scan, request, cfg)
    token = uuid.uuid4().hex
    main_info, scan_info = info_text(request, token, 'MAIN'), info_text(request, token, 'LASER')
    validate_info(main, main_info)
    validate_info(scan, scan_info)
    common = {'target_date': aw._parse_date(option['date'], 'date'), 'created_by': aw._created_by(config)}
    physician = aw._insert_appointment(main, idpac=int(request['idpac']), idprac=option['idprac'], doctor_id=option['doctor_id'],
        start_time=aw._parse_time(option['start_time'], 'start'), end_time=aw._parse_time(option['end_time'], 'end'),
        idcinnosti=1, info=main_info, **common)
    scanner = aw._insert_appointment(scan, idpac=None, idprac=cfg['workplace_id'], doctor_id=cfg['calendar_id'],
        start_time=aw._parse_time(option['scan_slot']['start_time'], 'start'), end_time=aw._parse_time(option['scan_slot']['end_time'], 'end'),
        idcinnosti=cfg['booking_activity_id'], info=scan_info, **dict(common, created_by=int(cfg['created_by'])))
    return result('created', physician, scanner, token, option)


def result(status, physician, scanner, token, option=None):
    value = {'ok': True, 'status': status, 'booking_confirmed': True,
             'service': 'dermatoscope_first', 'pair_id': token,
             'appointment_ids': [physician['idobj']], 'laser_appointment_ids': [scanner['idobj']],
             'appointments': [dict(physician, database='MAIN'), dict(scanner, database='LASER')]}
    if option is not None:
        value['availability_option'] = option
    return value


def change_pair(group, main, scan, request, cfg):
    physician, scanner, token = load_pair(main, scan, request, cfg)
    if request['action'] == 'cancel':
        main.execute('DELETE FROM OBJOBJ WHERE IDOBJ=?', (physician['idobj'],))
        scan.execute('DELETE FROM OBJOBJ WHERE IDOBJ=?', (scanner['idobj'],))
        return result('cancelled', physician, scanner, token)
    if request.get('service', 'dermatoscope_first') != 'dermatoscope_first':
        raise PairUnavailable('service_change_requires_staff')
    # Both reads remain in the write transaction; load_pair verified these
    # exact ordinary rows and their explicit cross-database marker before use.
    option = option_for_pair(main, scan, request, cfg,
                             exclude_main_ids=(physician['idobj'],), exclude_scan_ids=(scanner['idobj'],))
    day = aw._parse_date(option['date'], 'date')
    for cursor, row, workplace, doctor, start, end in (
        (main, physician, option['idprac'], option['doctor_id'], option['start_time'], option['end_time']),
        (scan, scanner, cfg['workplace_id'], cfg['calendar_id'], option['scan_slot']['start_time'], option['scan_slot']['end_time'])):
        cursor.execute('UPDATE OBJOBJ SET IDPRAC=?,IDUZI=?,DATUM=?,DATUMDO=?,CAS=?,CASDO=? WHERE IDOBJ=?',
                       (workplace, doctor, day, day, aw._parse_time(start, 'start'), aw._parse_time(end, 'end'), row['idobj']))
        row.update(idprac=workplace, doctor_id=doctor, date=option['date'], start_time=start, end_time=end)
    return result('rescheduled', physician, scanner, token, option)


def execute_pair(connection, request, config, *, precondition=None):
    if config.get('enable_paired_appointment_writes') is not True:
        return failure('paired_writes_not_enabled')
    aw._require_patient_verified(request)
    action = request.get('action', 'create')
    if action not in aw.SUPPORTED_ACTIONS:
        raise PairUnavailable('unsupported_action')
    if action != 'create' and not aw._cancel_enabled(config):
        return failure('cancel_not_enabled')
    key = str(request.get('request_id') or '').strip()
    if not key or len(key) > 200:
        raise PairUnavailable('request_id_required')
    cfg, base = mapping()
    journal = Journal(config.get('paired_write_journal_path'))
    replay = journal.claim(key, request)
    if replay is not None:
        return replay
    scan_connection = group = None
    commit_started = False
    try:
        connection.rollback()
        scan_connection = fdb.connect(host=base['host'], port=base['port'], database=cfg['database'],
            user=base['username'], password=base['password'], charset=base.get('charset', 'UTF8'))
        # Prevent aliases of the same database entering a distributed group.
        paths = []
        for con in (connection, scan_connection):
            cur = con.cursor()
            cur.execute('SELECT MON$DATABASE_NAME FROM MON$DATABASE')
            paths.append(str(cur.fetchone()[0]).replace('\\', '/').casefold())
            con.rollback()
        if paths[0] == paths[1]:
            raise PairUnavailable('databases_must_differ')
        group = fdb.ConnectionGroup([connection, scan_connection])
        group.begin(staff_write_tpb())
        main, scan = group.cursor(connection), group.cursor(scan_connection)
        if precondition is not None:
            precondition(main, laser.ScanCalendar(scan, cfg['calendar_id'], cfg['workplace_id']))
        for cursor, creator in ((main, aw._created_by(config)), (scan, int(cfg['created_by']))):
            cursor.execute('SELECT IDUZI FROM UZIVATEL WHERE IDUZI=?', (creator,))
            if cursor.fetchone() is None:
                raise PairUnavailable('appointment_author_not_mapped')
        response = insert_pair(main, scan, request, config, cfg) if action == 'create' else change_pair(group, main, scan, request, cfg)
        # Persist intended result BEFORE asking Firebird to prepare/commit.
        journal.state(key, 'commit_started', response)
        commit_started = True
        group.commit()  # FDB performs distributed two-phase commit.
        journal.state(key, 'committed', response)
        return response
    except Exception as exc:
        if commit_started:
            # A lost ACK is not proof of rollback. Keep journal unresolved and
            # block all further paired writes until both DBs are reconciled.
            raise PairUnavailable('paired_commit_uncertain_contact_admin') from exc
        try:
            if group is not None:
                group.rollback()
        except Exception as rollback_error:
            raise PairUnavailable('paired_rollback_uncertain_contact_admin') from rollback_error
        status = str(exc) if isinstance(exc, PairUnavailable) else 'paired_write_failed_contact_staff'
        if isinstance(exc, ProposalConflict):
            status = 'proposal_changed_contact_staff'
        if isinstance(exc, fdb.DatabaseError) and 335544345 in exc.args:
            status = 'calendar_busy_retry_later'
        response = failure(status)
        journal.state(key, 'rejected', response)
        return response
    finally:
        try:
            if group is not None:
                group.disband()
        finally:
            if scan_connection is not None:
                scan_connection.close()


def write_transaction(connection, request, config, legacy_writer=aw.write_appointment, *, precondition=None):
    cursor = connection.cursor()
    replay = False
    path = config.get('paired_write_journal_path')
    if config.get('enable_paired_appointment_writes') is True and path and Path(path).is_file() and request.get('request_id'):
        with Journal(path).connect() as db:
            replay = db.execute('SELECT 1 FROM attempts WHERE key=?', (str(request['request_id']).strip(),)).fetchone() is not None
    if aw._write_enabled(config) and (replay or is_pair_request(cursor, request)):
        return execute_pair(connection, request, config, **({'precondition': precondition} if precondition is not None else {}))
    if aw._write_enabled(config):
        connection.rollback()
        connection.begin(staff_write_tpb())
        cursor = connection.cursor()
        if precondition is not None:
            try:
                precondition(cursor, None)
            except ProposalConflict:
                # This callback is read-only and precedes the writer. Only a
                # successful rollback establishes a definite rejection; a lost
                # rollback ACK must still propagate to reconciliation.
                connection.rollback()
                return failure('proposal_changed_contact_staff')
    response = legacy_writer(cursor, request, config)
    if response.get('ok'):
        connection.commit()
    else:
        connection.rollback()
    return response
