"""Durable at-least-once delivery to the idempotent Operator inbox."""
import sys
from pathlib import Path

# Embedded Windows Python does not add the script directory automatically.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import re
from datetime import datetime, timezone
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def delivery_config(config):
    tenant=config.get('operator_tenant_key')
    base=str(config.get('operator_ingest_url') or '').rstrip('/')
    token=config.get('operator_ingest_token')
    parsed=urlsplit(base)
    if not tenant or not token or not (parsed.scheme=='https' or (parsed.scheme=='http' and parsed.hostname in {'localhost','127.0.0.1','::1'})):
        raise ValueError('Operator delivery configuration is incomplete')
    return tenant, base, token


def send_event(base, token, event):
    try:
        request=Request(base+'/v1/events/workflow',data=json.dumps(event).encode(),
            headers={'Content-Type':'application/json','X-Operator-Token':token})
        with build_opener(NoRedirect()).open(request,timeout=10) as response:
            return response.status==200 and json.loads(response.read()).get('accepted') is True
    except Exception:
        return False


def deliver_failure_alert(store, config):
    tenant, base, token = delivery_config(config)
    job = store.claim_handoff_failure_alert(tenant)
    if job is None:
        return 'idle'
    event = {'event_id':job['handoff_id']+':delivery_failed',
             'event_type':'staff.handoff.delivery_failed','source':'medicus-api',
             'occurred_at':datetime.fromtimestamp(job['created_at'],timezone.utc).isoformat(),
             'tenant_key':tenant,'conversation_id':job['conversation'],
             'data':{'handoff_id':job['handoff_id'],'error_code':'operator_delivery_failed'}}
    accepted = send_event(base, token, event)
    store.finish_handoff_failure_alert(job, accepted)
    return 'failure_alert_stored_in_operator' if accepted else 'failure_alert_retry_pending'


def deliver_one(store, config):
    tenant, base, token = delivery_config(config)
    job=store.claim_handoff(tenant)
    if job is None:
        return 'idle'
    payload=job['payload']
    summary=str(payload.get('summary_for_staff') or '')
    if payload.get('caller_phone'):
        summary=summary.replace(str(payload['caller_phone']), '[kontakt u hovoru]')
    summary=re.sub(r'internal idpac:\s*\d+', 'internal patient reference withheld', summary, flags=re.I)
    summary=re.sub(r'(?<!\d)\d{6}/?\d{3,4}(?!\d)', '[citlivý údaj]', summary)
    event={'event_id':job['id'],'event_type':'staff.handoff.requested','source':'medicus-api',
           'occurred_at':datetime.fromtimestamp(job['created_at'],timezone.utc).isoformat(),
           'tenant_key':tenant,'conversation_id':job['conversation'],
           'data':{key:payload.get(key) for key in ('mode','reason','caller_phone','summary_for_staff','recommended_next_step')}}
    event['data']['summary_for_staff']=summary
    accepted=send_event(base, token, event)
    store.finish_handoff_delivery(job,accepted=accepted)
    return 'stored_in_operator' if accepted else 'retry_or_failed'


def deliver_execution(store, config):
    tenant, base, token = delivery_config(config)
    store.queue_stalled_executions(tenant)
    job = store.claim_execution_event(tenant)
    if job is None:
        return 'execution_idle'
    try:
        request = Request(base + '/v1/events/tool', data=json.dumps(job['event']).encode(),
                          headers={'Content-Type': 'application/json', 'X-Operator-Token': token})
        with build_opener(NoRedirect()).open(request, timeout=10) as response:
            accepted = response.status == 200 and json.loads(response.read()).get('accepted') is True
    except Exception:
        accepted = False
    store.finish_execution_event(job, accepted)
    return 'execution_stored_in_operator' if accepted else 'execution_retry_pending'


if __name__=='__main__':
    import argparse
    import time
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    config=json.loads((Path(__file__).resolve().parents[1]/'config/api.local.json').read_text(encoding='utf-8-sig'))
    from handoff_config import handoff_store
    try:
        store=handoff_store(config, existing=True)
        delivery_config(config)
    except ValueError as error:
        raise SystemExit(str(error)) from None
    while True:
        outcome=deliver_one(store,config)
        print(outcome,flush=True)
        print(deliver_failure_alert(store,config),flush=True)
        print(deliver_execution(store,config),flush=True)
        if args.once:
            break
        time.sleep(2)
