"""Stage 1 read-only evidence; run from the Medicus repository on its host.

Only dictionary data, procedure definitions, sanitized configuration and a
patient-free day projection are emitted. No patient table or clinical text is
queried. No production file is changed; all DB transactions are rolled back.
"""
import ast
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
import subprocess
import sys

root = Path.cwd()
sys.path.insert(0, str(root / 'scripts'))
import fdb
from db import _load_db_config
from business_rules import load_business_rules
from availability_search import load_search_config

def read_config(name):
    path = root / 'config' / name
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}

def project(value, keys):
    return {key: value[key] for key in keys if key in value}

api = read_config('api.local.json')
laser = read_config('laser_calendar.local.json')
search = load_search_config()
out = {
    'captured_at_utc': datetime.now(timezone.utc).isoformat(),
    'git_head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
    'api_flags': project(api, ['enable_appointment_writes','enable_appointment_cancellations','enable_staff_approval','appointment_created_by','include_related_appointments_by_default']),
    'effective_rules': load_business_rules(),
    'search_config': project(search, ['allowed_doctor_ids','system_excluded_doctor_ids','excluded_doctor_ids','slot_interval_minutes']),
    'laser_mapping': project(laser, ['enabled','database','calendar_id','workplace_id']),
    'files': {}, 'databases': {},
}
for name in ['api_server','business_rules','availability_search','availability_engine','agent_context','laser_calendar','appointment_write','patient_lookup','handoff_summary']:
    path = root/'scripts'/f'{name}.py'
    raw = path.read_bytes()
    tree = ast.parse(raw.decode('utf-8-sig'))
    out['files'][name] = {'sha256':hashlib.sha256(raw).hexdigest(), 'symbols':{
        node.name:{'line':node.lineno,'ast_sha256':hashlib.sha256(ast.dump(node).encode()).hexdigest()}
        for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))}}
base = _load_db_config()
for namespace, database in [('MAIN',base['database']),('LASER',laser['database'])]:
    con = fdb.connect(host=base['host'],port=base['port'],database=database,user=base['username'],password=base['password'],charset=base.get('charset','UTF8'))
    try:
        con.default_tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read, fdb.isc_tpb_read_committed, fdb.isc_tpb_rec_version, fdb.isc_tpb_nowait)
        cur = con.cursor()
        dbout = {'database':database}
        queries = {
            'users':'SELECT IDUZI, JMENO, PRIJMENI FROM UZIVATEL ORDER BY IDUZI',
            'activities':'SELECT ID, NAZEV, INTERVAL, IDPRAC FROM CINNOSTI ORDER BY ID',
            'schedule_workplaces':'SELECT DISTINCT IDPRAC FROM OBSPRAC ORDER BY IDPRAC',
            'workplace_relations':"SELECT TRIM(RDB$RELATION_NAME) FROM RDB$RELATIONS WHERE RDB$RELATION_NAME CONTAINING 'PRAC' AND COALESCE(RDB$SYSTEM_FLAG,0)=0",
        }
        for key, query in queries.items():
            cur.execute(query)
            dbout[key] = [[v.strip() if isinstance(v,str) else v for v in row] for row in cur.fetchall()]
        dbout['procedures'] = {}
        for proc in ['OBJOBJ_SEL','OBSDNE_PRAVODLIS_SEL']:
            cur.execute('SELECT RDB$PROCEDURE_SOURCE FROM RDB$PROCEDURES WHERE RDB$PROCEDURE_NAME=?',(proc,))
            row=cur.fetchone()
            source=row[0] if row else None
            if hasattr(source,'read'): source=source.read()
            if isinstance(source,bytes): source=source.decode('utf-8',errors='replace')
            dbout['procedures'][proc]=source
        cur.execute('SELECT IDUZI, IDPRAC, CAS, CASDO, TYP, IDCINNOSTI FROM OBJOBJ_SEL(NULL,NULL,NULL,NULL,?,?) ORDER BY IDUZI,CAS',(date(2026,10,7),date(2026,10,7)))
        dbout['day_2026_10_07']=cur.fetchall()
        out['databases'][namespace]=dbout
    finally:
        con.rollback()
        con.close()
print(json.dumps(out,ensure_ascii=True,default=str,indent=2))
