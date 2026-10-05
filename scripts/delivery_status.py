"""Read-only local delivery diagnostics. Never initializes a store or sends data."""
import argparse
import json
from pathlib import Path
import sqlite3
import time


def inspect_store(path, tenant):
    path = Path(path)
    if not path.is_absolute() or not path.is_file() or not isinstance(tenant, str) or not tenant:
        raise ValueError('Existing absolute store path and tenant are required')
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        connection.execute('PRAGMA query_only=ON')
        connection.execute('BEGIN')
        tables = {r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('handoffs','proposals','proposal_events','execution_outbox')")}
        result = {'read_only': True, 'execution_schema_ready': 'execution_outbox' in tables}
        if 'handoffs' in tables:
            result['handoffs'] = dict(connection.execute(
                'SELECT delivery_state,COUNT(*) FROM handoffs WHERE tenant=? GROUP BY delivery_state', (tenant,)))
        if 'proposals' in tables:
            result['proposals'] = dict(connection.execute(
                'SELECT state,COUNT(*) FROM proposals WHERE tenant=? GROUP BY state', (tenant,)))
        if {'proposals', 'proposal_events'}.issubset(tables):
            result['stalled_executions'] = connection.execute('''SELECT COUNT(*) FROM proposals p
                WHERE p.tenant=? AND p.state='executing' AND
                (SELECT MAX(e.at) FROM proposal_events e WHERE e.proposal_id=p.id AND e.state='executing')<=?''',
                (tenant, time.time() - 600)).fetchone()[0]
        if 'execution_outbox' in tables:
            row = connection.execute('''SELECT COUNT(*),COALESCE(SUM(delivered),0),
                COALESCE(SUM(CASE WHEN delivered=0 AND next_attempt_at<=? AND lease_until<=? THEN 1 ELSE 0 END),0),
                COALESCE(MAX(CASE WHEN delivered=0 THEN attempts ELSE 0 END),0)
                FROM execution_outbox WHERE tenant=?''', (time.time(), time.time(), tenant)).fetchone()
            result['execution_events'] = {'total': row[0], 'delivered': row[1],
                                          'pending': row[0] - row[1], 'due': row[2], 'max_pending_attempts': row[3]}
        return result
    finally:
        connection.rollback()
        connection.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'config/api.local.json')
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding='utf-8-sig'))
        print(json.dumps(inspect_store(config.get('approval_store_path', ''), config.get('operator_tenant_key'))))
    except Exception:
        # Paths, credentials and stored clinical data must not reach diagnostics.
        print(json.dumps({'ok': False, 'error': 'delivery_status_unavailable'}))
        raise SystemExit(1) from None
