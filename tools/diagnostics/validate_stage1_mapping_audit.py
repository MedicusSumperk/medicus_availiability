"""Offline Stage 1 evidence/characterization checks; not business acceptance.

Run from repo root. No network, writes, real patient lookup or DB connection.
"""
import ast
from collections import Counter
from datetime import date, datetime, time
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
from zoneinfo import ZoneInfo

root=Path(__file__).resolve().parents[2]
folder=root/'docs/stage1_mapping_audit'
data=json.loads((folder/'rules.json').read_text(encoding='utf-8-sig'))
schema=json.loads((folder/'schema.json').read_text(encoding='utf-8-sig'))
live=json.loads((folder/'observed_server.json').read_text(encoding='utf-8-sig'))
assert set(data)==set(schema['required'])
assert data['status']=='DRAFT_FOR_HUMAN_VALIDATION'
assert data['schema_version']==schema['properties']['schema_version']['const']
fields=set(schema['properties']['rules']['items']['required'])
statuses={'CONFIRMED','PROBABLE','UNCLEAR','CONFLICT'}
ids=[r['rule_id'] for r in data['rules']]
assert len(ids)==len(set(ids))==40
sources={}
for name,remote in live['files'].items():
    raw=(root/'scripts'/f'{name}.py').read_bytes()
    tree=ast.parse(raw.decode('utf-8-sig'))
    symbols={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    sources[name]={'same_file':hashlib.sha256(raw).hexdigest()==remote['sha256'], 'changed_symbols':[
        name for name,node in symbols.items() if name not in remote['symbols'] or
        hashlib.sha256(ast.dump(node).encode()).hexdigest()!=remote['symbols'][name]['ast_sha256']]}
for r in data['rules']:
    assert set(r)==fields,r['rule_id']
    assert all(isinstance(v,str) and v.strip() for v in r.values()),r['rule_id']
    assert r['confidence'] in statuses
    for location in r['implementation_location'].split('; '):
        clean=location.split(' (')[0].split('#')[0]
        path,*symbol=clean.split('::')
        assert (root/path).is_file(),location
        if symbol:
            tree=ast.parse((root/path).read_text(encoding='utf-8-sig'))
            assert any(getattr(n,'name',None)==symbol[0] for n in tree.body),location
assert live['api_flags']['enable_appointment_writes'] is False
assert live['api_flags']['enable_appointment_cancellations'] is False
actual15=next(x for x in live['databases']['MAIN']['users'] if x[0]==15)
declared15=next(x for x in live['effective_rules']['doctors']['known'] if x['id']==15)
assert ' '.join(actual15[1:])!=declared15['name']
assert live['databases']['MAIN']['procedures']['OBSDNE_PRAVODLIS_SEL']

sys.path.insert(0,str(root/'scripts'))
from availability_engine import compute_slots, compute_day_availability
from agent_context import build_skin_options
from laser_calendar import interval_is_available, ScanCalendarUnavailable
from availability_search import _resolve_doctor_filter, _apply_spoken_time, _option_is_future
from business_rules import afternoon_bucket_for_time
rules=live['effective_rules']
# Characterize existing behavior, not the desired business answer.
assert afternoon_bucket_for_time(rules,'skin','16:00',1)['spoken_time_label']=='15:00'
now=datetime(2026,10,1,11,10,tzinfo=ZoneInfo('Europe/Prague'))
option={'start_time':'11:30'}
assert _option_is_future(option,now.date(),now)
assert _apply_spoken_time(option,'skin',rules,4)['spoken_time_label']=='11:00'
with patch('availability_engine.find_schedule_contexts',return_value=[]), patch('availability_engine.load_schedule_blocks') as blocks:
    result=compute_day_availability(None,{'doctor_id':12},date(2026,10,7))
    assert result['has_schedule'] is False
    blocks.assert_not_called()
doctors=[{'doctor_id':11,'doctor_name':'Dušana Selecká'},{'doctor_id':13,'doctor_name':'Zuzana Šlosárová'}]
matched,detail,_=_resolve_doctor_filter(doctors,11,'Zuzana Šlosárová')
assert matched[0]['doctor_id']==11 and detail['match_type']=='doctor_id'
assert compute_slots([(time(9),10,10)],[(time(9),time(9))])[2]==[time(9)]
try:
    interval_is_available(date(2026,10,7),'09:00','09:10',[(time(9),10,10)],[(time(9),time(9))])
except ScanCalendarUnavailable:
    pass
else:
    raise AssertionError('Expected LASER invalid interval rejection')
context={'idprac':1,'slot_interval_minutes':10,'free_slots':['09:00','09:15','10:00','10:10']}
offers,_=build_skin_options(context,[],{'use_schedule_interval':True,'create_followup_dermatoscope':False},15,10)
assert next(o for o in offers if o['start_time']=='09:00')['end_time']=='09:10'
assert compute_slots([(time(9),30,15),(time(10),20,10)],[])[2]==[time(9),time(9,15),time(10),time(10,10)]
main=live['databases']['MAIN']['day_2026_10_07']
laser=live['databases']['LASER']['day_2026_10_07']
assert any(r[0]==12 and r[2]=='15:55:00' and r[3]=='16:20:00' for r in main)
assert any(r[0]==5 and r[1]==1 and r[2]=='14:45:00' and r[3]=='15:00:00' for r in laser)
print(json.dumps({'result':'PASS: inventory integrity and current-behavior characterization only',
    'rule_count':len(ids),'confidence_counts':dict(Counter(r['confidence'] for r in data['rules'])),
    'source_comparison':sources,'human_business_validation':'NOT DONE'},ensure_ascii=False,indent=2))
