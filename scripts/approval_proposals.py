"""Read-only proposal validation. This module cannot commit to Medicus."""
import hashlib
import json
from copy import deepcopy
from contextlib import contextmanager, ExitStack
from datetime import date, datetime
from zoneinfo import ZoneInfo

from approval_store import ProposalConflict
from appointment_write import _fetch_appointment_rows
from availability_search import search_availability
from business_rules import load_business_rules
from patient_lookup import verified_identity_method


def patient_fingerprint(cursor, idpac):
    cursor.execute('SELECT IDPAC,JMENO,PRIJMENI,DATNAR FROM KAR WHERE IDPAC=?',(idpac,))
    row=cursor.fetchone()
    if row is None:
        raise ProposalConflict('Patient no longer exists')
    return hashlib.sha256(json.dumps(list(row),default=str,ensure_ascii=False).encode()).hexdigest()


def issue_patient_reference(store, cursor, tenant, conversation, request, response):
    # A unique name-only/id-only lookup and the agent's patient_verified flag
    # are not proof of caller-provided DOB validation.
    patients=response.get('patients',[])
    if not conversation or verified_identity_method(request, response) is None:
        return None
    idpac=int(patients[0]['idpac'])
    return store.issue_grant(tenant,conversation,'patient',
                            {'idpac':idpac,'fingerprint':patient_fingerprint(cursor,idpac)})


def offer_snapshot(option):
    fields=('service','date','start_time','end_time','doctor_id','doctor_name','idprac','idcinnosti','scan_slot',
            'duration_minutes','slot_interval_minutes','communication_note')
    snapshot=deepcopy({k:option.get(k) for k in fields})
    snapshot['technical_start_time']=option.get('technical_start_time') or option['start_time']
    snapshot['spoken_time_label']=option.get('spoken_time_label') or option['start_time']
    arrivals=[snapshot['spoken_time_label']]
    if snapshot['scan_slot']:
        arrivals.append(snapshot['scan_slot']['start_time'])
    snapshot['arrival_time']=min(arrivals)
    snapshot['schema_version']=2
    snapshot['call_started_at']=option.get('call_started_at')
    snapshot['rules_sha256']=hashlib.sha256(json.dumps(load_business_rules(),sort_keys=True,
        ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return snapshot


def source_snapshot(cursor, idpac, ids):
    ids=sorted(set(int(i) for i in ids))
    if not ids or len(ids)>10:
        raise ProposalConflict('Specify the original appointment')
    rows=_fetch_appointment_rows(cursor,ids)
    if len(rows)!=len(ids) or any(r['idpac']!=idpac for r in rows):
        raise ProposalConflict('Original appointment does not belong to verified patient')
    now=datetime.now(ZoneInfo('Europe/Prague'))
    for row in rows:
        if row['typ'] in (9,10):
            raise ProposalConflict('Recurring appointments require individual staff handling')
        if datetime.fromisoformat(row['date']+'T'+row['start_time']).replace(tzinfo=now.tzinfo)<=now:
            raise ProposalConflict('Original appointment is already in the past')
    fields=('idobj','idpac','idprac','doctor_id','date','start_time','end_time','typ','idcinnosti')
    return sorted([{k:r.get(k) for k in fields} for r in rows],key=lambda r:r['idobj'])


def staff_original_summary(cursor, idpac, source):
    """Display verified source details without widening the execution snapshot."""
    from laser_calendar import open_scan_calendar
    from paired_appointments import load_pair
    summaries = []
    for row in source:
        cursor.execute('SELECT JMENO,PRIJMENI FROM UZIVATEL WHERE IDUZI=?', (row['doctor_id'],))
        doctor = cursor.fetchone()
        name = ' '.join(str(part).strip() for part in doctor if part and str(part).strip()) if doctor else None
        item = {k: row.get(k) for k in ('date', 'start_time', 'end_time', 'doctor_id')}
        item.update(doctor_name=name or None, service=None, scan_slot=None,
                    arrival_time=None, communication_note=None)
        if row.get('idcinnosti') == 1:
            with open_scan_calendar() as calendar:
                if (calendar.calendar_id, calendar.workplace_id) != (5, 1):
                    raise ProposalConflict('Unverified scan calendar mapping')
                physician, scanner, _ = load_pair(cursor, calendar.cursor,
                    {'appointment_ids': [row['idobj']], 'idpac': idpac},
                    {'calendar_id': 5, 'workplace_id': 1, 'booking_activity_id': 28})
                if any(physician.get(k) != v for k, v in row.items()):
                    raise ProposalConflict('Original appointment changed during summary')
                item.update(service='dermatoscope_first', scan_slot={
                    'start_time': scanner['start_time'], 'end_time': scanner['end_time']},
                    communication_note='Změna se týká prohlídky i navázaného skenu.')
        elif row.get('idcinnosti') is None:
            item['service'] = 'skin'
        # Historic arrival/bucket information is not persisted in OBJOBJ.
        # Do not invent a prior communicated arrival from today's rules.
        summaries.append(item)
    return summaries


@contextmanager
def verified_move_availability(cursor, idpac, source, *, scan_calendar=None):
    """Exclude only the unchanged verified source, never arbitrary caller IDs."""
    from appointment_write import _single_change_guard
    from laser_calendar import ScanCalendar, open_scan_calendar
    from paired_appointments import load_pair
    with ExitStack() as resources:
        arguments = {'scan_calendar': scan_calendar} if scan_calendar is not None else {}
        if source:
            ids = [row['idobj'] for row in source]
            if len(ids) != 1 or source_snapshot(cursor, idpac, ids) != source:
                raise ProposalConflict('Original appointment changed or requires staff handling')
            row = _fetch_appointment_rows(cursor, ids)[0]
            if row['idcinnosti'] == 1 or 'AI_PAIR_V1:' in row['info']:
                calendar = scan_calendar or resources.enter_context(open_scan_calendar())
                cfg = {'calendar_id': calendar.calendar_id, 'workplace_id': calendar.workplace_id,
                       'booking_activity_id': 28}
                if (cfg['calendar_id'], cfg['workplace_id']) != (5, 1):
                    raise ProposalConflict('Unverified scan calendar mapping')
                _, scanner, _ = load_pair(cursor, calendar.cursor,
                    {'appointment_ids': ids, 'idpac': idpac}, cfg)
                arguments['scan_calendar'] = ScanCalendar(calendar.cursor, calendar.calendar_id,
                    calendar.workplace_id, exclude_ids=(scanner['idobj'],))
            else:
                issue = _single_change_guard(cursor, row)
                if issue:
                    raise ProposalConflict(issue)
            arguments['exclude_main_ids'] = tuple(ids)
        yield arguments


def validate_offer(cursor, offer, *, scan_calendar=None, source=(), idpac=None):
    anchor=datetime.fromisoformat(offer['call_started_at']) if offer.get('call_started_at') else None
    with verified_move_availability(cursor, idpac, source, scan_calendar=scan_calendar) as exclusions:
        response=search_availability(cursor,{'service':offer['service'],'doctor_id':offer['doctor_id'],
            'date_from':offer['date'],'date_to':offer['date'],
            'technical_start_time':offer['start_time'],'limit':10}, call_started_at=anchor, **exclusions)
    for option in response['options']:
        option['call_started_at']=offer.get('call_started_at')
    if not any(offer_snapshot(o)==offer for o in response['options']):
        raise ProposalConflict('The selected offer is no longer available or has changed')


def resolve_move_search(store, cursor, tenant, conversation, request):
    identity = request.get('reschedule_appointment_id')
    if type(identity) is not int or identity <= 0:
        raise ProposalConflict('A single original appointment ID is required')
    patient = store.resolve_grant(tenant, conversation, 'patient', request.get('patient_verification_token'))
    if patient_fingerprint(cursor, patient['idpac']) != patient['fingerprint']:
        raise ProposalConflict('Patient record changed; repeat verification')
    source = source_snapshot(cursor, patient['idpac'], [identity])
    service = {None: 'skin', 1: 'dermatoscope_first', 2: 'dermatoscope_followup'}.get(source[0]['idcinnosti'])
    if not service or request.get('service', 'skin') != service:
        raise ProposalConflict('Changing the appointment service requires staff')
    return {'patient': patient, 'source': source}


def proposal_response(card):
    return {'ok':True,'status':card['state'],'booking_confirmed':card['state']=='committed','proposal_id':card['id'],
            'message':'Request status: '+card['state']+'. Only committed means a completed Medicus change.'}


def revalidate_proposal(store, cursor, tenant, identity, version):
    """Check current data without granting permission to write or holding a slot."""
    payload = store.pending_payload(tenant, identity, version)
    action = payload.get('action')
    if action not in {'create', 'reschedule', 'cancel'}:
        raise ProposalConflict('Unknown operation')
    patient = payload['patient']
    if patient_fingerprint(cursor, patient['idpac']) != patient['fingerprint']:
        raise ProposalConflict('Patient record changed; repeat verification')
    source = payload.get('source') or []
    if action in {'reschedule', 'cancel'}:
        if source_snapshot(cursor, patient['idpac'], [row['idobj'] for row in source]) != source:
            raise ProposalConflict('Original appointment changed; create a new request')
    elif source:
        raise ProposalConflict('Unexpected original appointment')
    offer = payload.get('offer')
    if action in {'create', 'reschedule'}:
        if not offer:
            raise ProposalConflict('Selected offer is missing')
        validate_offer(cursor, offer, **({'source': source, 'idpac': patient['idpac']} if action == 'reschedule' else {}))
    elif offer is not None:
        raise ProposalConflict('Unexpected replacement offer')
    # A staff decision may have occurred while the database was being queried.
    if store.pending_payload(tenant, identity, version) != payload:
        raise ProposalConflict('Proposal changed during validation')
    return {'ok': True, 'status': 'validated', 'proposal_id': identity, 'version': version,
            'booking_confirmed': False, 'execution_enabled': False,
            'checked_at': datetime.now(ZoneInfo('Europe/Prague')).isoformat()}


def submission_identity(conversation, request):
    if not conversation or len(conversation)>160:
        raise ProposalConflict('Conversation reference is required')
    action=request.get('action','create')
    if action not in {'create','reschedule','cancel'}:
        raise ProposalConflict('Unknown operation')
    if request.get('caller_confirmed') is not True:
        raise ProposalConflict('Caller confirmation of this request is required')
    request_key=request.get('request_id')
    if not isinstance(request_key,str) or not 1<=len(request_key)<=160:
        raise ProposalConflict('Stable request_id is required')
    # JSON tuple avoids collisions between conversation/request keys containing ':'.
    storage_key=json.dumps([conversation, request_key], ensure_ascii=True, separators=(',',':'))
    request_digest=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=True,
        separators=(',',':')).encode()).hexdigest()
    return storage_key, request_digest


def replay_proposal(store, tenant, conversation, request):
    storage_key, request_digest = submission_identity(conversation, request)
    existing=store.replay_submission(tenant,storage_key,request_digest)
    if existing is None:
        # Pre-v2 local cards have no request digest. Fail closed rather than
        # silently creating a second card under the new unambiguous key.
        existing=store.replay_submission(tenant,conversation+':'+request['request_id'],request_digest)
    if existing is not None:
        return proposal_response(existing)
    return None


def submit_proposal(store, cursor, tenant, conversation, request):
    existing = replay_proposal(store, tenant, conversation, request)
    if existing is not None:
        return existing
    storage_key, request_digest = submission_identity(conversation, request)
    action = request.get('action', 'create')
    patient=store.resolve_grant(tenant,conversation,'patient',request.get('patient_verification_token'))
    if patient_fingerprint(cursor,patient['idpac'])!=patient['fingerprint']:
        raise ProposalConflict('Patient record changed; repeat verification')
    source=[]
    if action in {'reschedule','cancel'}:
        ids=request.get('appointment_ids') or ([request['appointment_id']] if request.get('appointment_id') else [])
        source=source_snapshot(cursor,patient['idpac'],ids)
    offer=None
    if action in {'create','reschedule'}:
        offer=store.resolve_grant(tenant,conversation,'offer',request.get('offer_token'))
        if 'move_binding' in offer:
            binding = offer['move_binding']
            if action != 'reschedule' or binding.get('patient') != patient or binding.get('source') != source:
                raise ProposalConflict('Offer belongs to a different original appointment or patient')
            offer = offer['offer']
        # Reject conflicting echoed fields instead of silently choosing a token
        # over a different date/time/doctor voiced by the model.
        for key in ('date','start_time','end_time','doctor_id','doctor_name','service',
                    'technical_start_time','spoken_time_label','arrival_time','scan_slot'):
            if request.get(key) is not None and request[key]!=offer.get(key):
                raise ProposalConflict('Submitted fields do not match the selected offer')
        validate_offer(cursor,offer, **({'source': source, 'idpac': patient['idpac']} if action == 'reschedule' else {}))
    payload={'action':action,'patient':patient,'source':source,'offer':offer,'conversation_id':conversation,
             'request_digest':request_digest}
    def staff_appointment(row):
        return {k:row.get(k) for k in ('date','start_time','end_time','doctor_id','doctor_name','service','scan_slot',
                                     'technical_start_time','spoken_time_label','arrival_time','communication_note')}
    summary={'action':action,'conversation_id':conversation,'original':staff_original_summary(cursor,patient['idpac'],source),
             'requested':staff_appointment(offer) if offer else None}
    card=store.submit(tenant,storage_key,payload,summary)
    return proposal_response(card)
