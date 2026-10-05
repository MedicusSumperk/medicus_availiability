"""Read-only incident evidence from public availability API and both DBs."""
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen, build_opener, ProxyHandler
from urllib.error import HTTPError

sys.path.insert(0, str(Path.cwd() / 'scripts'))
import fdb
from db import _load_db_config


def main():
    api = json.loads(Path('config/api.local.json').read_text(encoding='utf-8-sig'))
    token = os.environ.get('MEDICUS_API_TOKEN') or api.get('bearer_token')
    if not token:
        raise RuntimeError('API authentication is not configured')
    requests = [
        {'service': 'dermatoscope_first', 'date_from': '2026-10-02', 'limit': 3, 'compact': True},
        {'service': 'dermatoscope_first', 'date_from': '2026-10-07', 'date_to': '2026-10-07', 'doctor_id': 12, 'limit': 10, 'compact': False},
        {'service': 'skin', 'date_from': '2026-10-07', 'date_to': '2026-10-07', 'doctor_id': 12, 'limit': 10, 'compact': False},
    ]
    output = {'captured_at_utc': datetime.now(timezone.utc).isoformat(), 'api': [], 'calendars': {}}
    targets = [('public', 'https://medicus-api.kreli.org', urlopen),
               ('local', 'http://127.0.0.1:' + str(int(api.get('port', 8000))), build_opener(ProxyHandler({})).open)]
    for source, base_url, opener in targets:
      for payload in requests:
        request = Request(base_url + '/doctor-availability',
            data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with opener(request, timeout=45) as response:
                status, body = response.status, response.read()
        except HTTPError as error:
            status, body = error.code, error.read()
        try:
            parsed = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            parsed = {'non_json_response': True, 'body_bytes': len(body)}
        output['api'].append({'source': source, 'request': payload, 'status': status, 'response': parsed})
    config = _load_db_config()
    laser = json.loads(Path('config/laser_calendar.local.json').read_text(encoding='utf-8-sig'))
    for namespace, database, calendar in [('MAIN', config['database'], 12), ('LASER', laser['database'], int(laser['calendar_id']))]:
        con = fdb.connect(host=config['host'], port=config['port'], database=database,
            user=config['username'], password=config['password'], charset=config.get('charset','UTF8'))
        try:
            con.default_tpb = (fdb.isc_tpb_version3, fdb.isc_tpb_read, fdb.isc_tpb_concurrency, fdb.isc_tpb_nowait)
            cur = con.cursor()
            day = date(2026, 10, 7)
            cur.execute('SELECT IDOBJ,CAS,CASDO,IDCINNOSTI FROM OBJOBJ_SEL(NULL,NULL,1,?,?,?) ORDER BY CAS', (calendar, day, day))
            rows = cur.fetchall()
            checks = []
            for doctor_start, doctor_end, scan_start in [('15:00','15:10','14:45'),('15:10','15:20','14:55'),('15:50','16:00','15:35')]:
                start, end = (doctor_start, doctor_end) if namespace == 'MAIN' else (scan_start, doctor_start)
                conflicts = [r[0] for r in rows if start < r[2].strftime('%H:%M') and end > r[1].strftime('%H:%M')]
                checks.append({'doctor_time': doctor_start, 'tested_interval': [start,end], 'conflicting_ids': conflicts})
            output['calendars'][namespace] = {'calendar': calendar, 'date': str(day), 'workplace': 1,
                'rows': rows, 'checks': checks}
        finally:
            con.rollback()
            con.close()
    print(json.dumps(output, ensure_ascii=True, default=str, indent=2))


if __name__ == '__main__':
    main()
