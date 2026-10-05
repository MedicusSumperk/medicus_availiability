"""Staff-authorized execution; never trust browser-supplied booking fields."""
import time
from datetime import datetime, timezone

from approval_store import ProposalConflict
from approval_proposals import patient_fingerprint, source_snapshot, validate_offer
from paired_appointments import write_transaction
from db import connect_to_db
from operator_telemetry import emit_tool_event


def execution_evidence(response, outcome):
    """Only verified operation metadata; never copy clinical/free-text fields."""
    if outcome != 'committed':
        return {'ok': False, 'status': outcome, 'booking_confirmed': False}
    result = public_result(response)
    for field in ('appointments', 'appointments_before_cancel'):
        if isinstance(response.get(field), list):
            result[field] = [
                {key: row[key] for key in ('database', 'idobj', 'date', 'start_time', 'end_time') if key in row}
                for row in response[field] if isinstance(row, dict)
            ]
    return result


def report_execution(config, payload, identity, outcome, response, started):
    # Best effort only: the durable proposal state remains authoritative even
    # when Operator is offline. No retry of clinical writes on delivery failure.
    try:
        offer = payload.get('offer') or {}
        emit_tool_event(
            config, conversation_id=payload.get('conversation_id'),
            tool_name='appointment_write', endpoint='/staff/proposals/{proposal_id}/approve',
            started_monotonic=started,
            request_payload={'action': payload['action'], 'request_id': 'staff:' + identity,
                             'proposal_id': identity, 'execution_source': 'staff_approval',
                             **({'date': offer['date']} if 'date' in offer else {}),
                             **({'start_time': offer['technical_start_time']} if 'technical_start_time' in offer else {})},
            response_payload=execution_evidence(response, outcome),
            http_status=200 if outcome in {'committed', 'conflict'} else 503,
            business_ok=outcome == 'committed',
            error_code=None if outcome == 'committed' else outcome,
            trace_id='staff:' + identity,
            request_id='staff:' + identity,
        )
    except Exception:
        pass


def durable_execution_event(tenant, payload, identity, outcome, response, started):
    offer = payload.get('offer') or {}
    succeeded = outcome == 'committed'
    return {
        'event_id': identity + ':execution', 'event_type': 'tool.completed' if succeeded else 'tool.failed',
        'occurred_at': datetime.now(timezone.utc).isoformat(), 'tenant_key': tenant,
        'conversation_id': payload['conversation_id'], 'source': 'medicus-api',
        'tool_call': {
            'name': 'appointment_write', 'endpoint': '/staff/proposals/{proposal_id}/approve',
            'request_id': 'staff:' + identity, 'trace_id': 'staff:' + identity,
            'sequence_no': None, 'duration_ms': max(0, round((time.perf_counter() - started) * 1000)),
            'http_status': 200 if outcome in {'committed', 'conflict'} else 503,
            'business_ok': succeeded, 'is_error': not succeeded,
            'error_code': None if succeeded else outcome,
            'request_safe': {'action': payload['action'], 'execution_source': 'staff_approval',
                             'proposal_id': identity, 'date': offer.get('date'),
                             'start_time': offer.get('technical_start_time')},
            'response_safe': execution_evidence(response, outcome),
        },
    }


def execution_request(payload, identity):
    action = payload.get('action')
    if action not in {'create', 'cancel', 'reschedule'}:
        raise ProposalConflict('Unknown operation')
    request = {'action': action, 'idpac': int(payload['patient']['idpac']),
               'patient_verified': True, 'include_related': False,
               'request_id': 'staff:' + identity}
    source = payload.get('source') or []
    offer = payload.get('offer')
    if action in {'cancel', 'reschedule'}:
        if not source:
            raise ProposalConflict('Original appointment is missing')
        request['appointment_ids'] = [int(row['idobj']) for row in source]
    elif source:
        raise ProposalConflict('Unexpected original appointment')
    if action in {'create', 'reschedule'}:
        if not offer:
            raise ProposalConflict('Selected offer is missing')
        request.update({key: offer[key] for key in ('service', 'date', 'doctor_id')})
        request['start_time'] = offer['technical_start_time']
    elif offer is not None:
        raise ProposalConflict('Unexpected replacement offer')
    return request


def validate_payload(cursor, scanner, payload):
    patient = payload['patient']
    if patient_fingerprint(cursor, patient['idpac']) != patient['fingerprint']:
        raise ProposalConflict('Patient record changed')
    if payload['action'] in {'cancel', 'reschedule'}:
        source = payload['source']
        if source_snapshot(cursor, patient['idpac'], [r['idobj'] for r in source]) != source:
            raise ProposalConflict('Original appointment changed')
    if payload.get('offer'):
        validate_offer(cursor, payload['offer'], scan_calendar=scanner,
            **({'source': payload['source'], 'idpac': patient['idpac']} if payload['action'] == 'reschedule' else {}))


def public_result(response):
    # Free text, patient identifiers, tokens and full appointment rows must not
    # be copied into the public proposal result or staff execution telemetry.
    return {k: response[k] for k in ('ok', 'status', 'booking_confirmed', 'appointment_ids',
                                    'laser_appointment_ids', 'pair_id') if k in response}


def classify_result(action, response):
    """A malformed success cannot establish which operation actually committed."""
    if not isinstance(response, dict) or response.get('status') == 'needs_reconciliation':
        return 'needs_reconciliation'
    if response.get('ok') is False:
        return 'conflict'
    expected = {'create': 'created', 'cancel': 'cancelled', 'reschedule': 'rescheduled'}
    ids = response.get('appointment_ids')
    if (response.get('ok') is True and response.get('status') == expected.get(action)
            and response.get('booking_confirmed') is True
            and isinstance(ids, list) and ids and all(type(i) is int and i > 0 for i in ids)):
        return 'committed'
    return 'needs_reconciliation'


def approve(store, tenant, identity, version, actor, config):
    if config.get('enable_staff_execution') is not True or config.get('enable_appointment_writes') is not True:
        raise ProposalConflict('Staff execution is disabled')
    # Validate structure before consuming the decision. The atomic claim checks
    # version, expiry and integrity again before returning authoritative data.
    execution_request(store.pending_payload(tenant, identity, version), identity)
    claimed, payload = store.decide(tenant, identity, version, actor, approve=True)
    started = time.perf_counter()
    connection = None
    response = {}
    entered_writer = False
    outcome, result = 'failed', {'ok': False, 'status': 'execution_not_started', 'booking_confirmed': False}
    try:
        request = execution_request(payload, identity)
        connection = connect_to_db()
        entered_writer = True
        response = write_transaction(connection, request, config,
            precondition=lambda cursor, scanner: validate_payload(cursor, scanner, payload))
        outcome = classify_result(payload['action'], response)
        result = (public_result(response) if outcome != 'needs_reconciliation'
                  else {'ok': False, 'status': outcome, 'booking_confirmed': False})
    except Exception:
        # Once execution was entered, an exception alone cannot prove rollback.
        # A lost Firebird ACK or SQLite failure must never start a second write.
        outcome = 'needs_reconciliation' if entered_writer else 'failed'
        result = {'ok': False, 'status': outcome, 'booking_confirmed': False}
    finally:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                outcome = 'needs_reconciliation'
                result = {'ok': False, 'status': outcome, 'booking_confirmed': False}
            finally:
                try:
                    connection.close()
                except Exception:
                    pass
    # If this persistence fails, the durable claim stays executing. Never retry
    # the Medicus write merely because storing or returning its result failed.
    try:
        event = durable_execution_event(tenant, payload, identity, outcome, response, started)
        finished = store.finish(tenant, identity, claimed['version'], outcome, result, event=event)
    except Exception:
        report_execution(config, payload, identity, 'needs_reconciliation', {}, started)
        raise
    return finished
