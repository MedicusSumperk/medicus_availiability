"""Durable on-host proposals. Execution payloads never leave this store's API.

Caller authentication and validation belong to the endpoint/service layer.
The deployment must restrict the store directory to the service and host admins.
An executing request is never automatically retried after a process failure.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid
import secrets
from datetime import datetime, timezone


class ProposalConflict(ValueError):
    pass


class ProposalNotFound(ValueError):
    pass


class ApprovalStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS proposals (
                  id TEXT PRIMARY KEY, tenant TEXT NOT NULL, request_key TEXT NOT NULL,
                  digest TEXT NOT NULL, payload TEXT NOT NULL, summary TEXT NOT NULL,
                  state TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
                  created_at REAL NOT NULL, expires_at REAL NOT NULL,
                  actor TEXT, result TEXT, UNIQUE(tenant,request_key));
                CREATE TABLE IF NOT EXISTS proposal_events (
                  id INTEGER PRIMARY KEY, proposal_id TEXT NOT NULL,
                  state TEXT NOT NULL, actor TEXT, at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS execution_outbox (
                  proposal_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, event TEXT NOT NULL,
                  delivered INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
                  next_attempt_at REAL NOT NULL DEFAULT 0, lease_until REAL NOT NULL DEFAULT 0,
                  lease_token TEXT);
                CREATE TABLE IF NOT EXISTS grants (
                  token_hash TEXT PRIMARY KEY, tenant TEXT NOT NULL,
                  conversation TEXT NOT NULL, purpose TEXT NOT NULL,
                  payload TEXT NOT NULL, expires_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS call_anchors (
                  tenant TEXT NOT NULL, conversation TEXT NOT NULL,
                  first_seen REAL NOT NULL, PRIMARY KEY(tenant,conversation));
                CREATE TABLE IF NOT EXISTS handoffs (
                  id TEXT PRIMARY KEY, tenant TEXT NOT NULL, conversation TEXT NOT NULL,
                  request_key TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL,
                  created_at REAL NOT NULL, delivery_state TEXT NOT NULL DEFAULT 'pending',
                  UNIQUE(tenant,conversation,request_key));
                CREATE TABLE IF NOT EXISTS handoff_attempts (
                  handoff_id TEXT PRIMARY KEY, attempts INTEGER NOT NULL DEFAULT 0,
                  next_attempt_at REAL NOT NULL DEFAULT 0, lease_until REAL NOT NULL DEFAULT 0,
                  lease_token TEXT, last_error_code TEXT);
                CREATE TABLE IF NOT EXISTS handoff_failure_alerts (
                  handoff_id TEXT PRIMARY KEY, created_at REAL NOT NULL,
                  delivered INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
                  next_attempt_at REAL NOT NULL DEFAULT 0, lease_until REAL NOT NULL DEFAULT 0,
                  lease_token TEXT);
                CREATE TABLE IF NOT EXISTS handoff_recovery_events (
                  id INTEGER PRIMARY KEY, handoff_id TEXT NOT NULL, tenant TEXT NOT NULL,
                  actor TEXT NOT NULL, at REAL NOT NULL, previous_attempts INTEGER NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def public(row):
        return {**{k:row[k] for k in ('id','state','version','created_at','expires_at')},
                'summary':json.loads(row['summary']),
                'result':json.loads(row['result']) if row['result'] else None}

    def first_seen(self, tenant, conversation):
        if not tenant or not isinstance(conversation, str) or not 1 <= len(conversation) <= 160:
            raise ProposalConflict('Valid conversation reference is required')
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO call_anchors VALUES(?,?,?)', (tenant,conversation,time.time()))
            return db.execute('SELECT first_seen FROM call_anchors WHERE tenant=? AND conversation=?',
                              (tenant,conversation)).fetchone()[0]

    def store_handoff(self, tenant, conversation, request_key, payload):
        if (not tenant or not isinstance(conversation, str) or not 1 <= len(conversation) <= 160
                or not isinstance(request_key, str) or not 1 <= len(request_key) <= 160
                or any(char.isspace() for char in conversation + request_key)
                or any(marker in conversation + request_key for marker in ('{', '}'))
                or conversation.startswith('system__')):
            raise ProposalConflict('Conversation and stable request_id are required')
        # Creation timestamp changes on transport retry, but not the request.
        content={key:value for key,value in payload.items() if key not in {'created_at','ok'}}
        encoded=json.dumps(content,sort_keys=True,ensure_ascii=False,separators=(',',':'))
        if len(encoded.encode('utf-8')) > 32000:
            raise ProposalConflict('Handoff context is too large')
        digest=hashlib.sha256(encoded.encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT id,digest,delivery_state FROM handoffs WHERE tenant=? AND conversation=? AND request_key=?',
                           (tenant,conversation,request_key)).fetchone()
            if row:
                if row['digest'] != digest:
                    raise ProposalConflict('Handoff request_id already used for different context')
                return {'handoff_id':row['id'],'stored':True,'delivery_status':row['delivery_state']}
            identity='handoff_'+uuid.uuid4().hex
            db.execute('INSERT INTO handoffs(id,tenant,conversation,request_key,digest,payload,created_at) VALUES(?,?,?,?,?,?,?)',
                       (identity,tenant,conversation,request_key,digest,encoded,time.time()))
            db.execute('INSERT INTO handoff_attempts(handoff_id) VALUES(?)',(identity,))
            return {'handoff_id':identity,'stored':True,'delivery_status':'pending'}

    def claim_handoff(self, tenant):
        now=time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # Populate delivery metadata for records created before worker rollout.
            db.execute('INSERT OR IGNORE INTO handoff_attempts(handoff_id) SELECT id FROM handoffs WHERE tenant=?',(tenant,))
            row=db.execute('SELECT h.*,a.attempts FROM handoffs h JOIN handoff_attempts a ON a.handoff_id=h.id '
                "WHERE h.tenant=? AND h.delivery_state='pending' AND a.next_attempt_at<=? AND a.lease_until<=? ORDER BY h.created_at LIMIT 1",
                (tenant,now,now)).fetchone()
            if row is None:
                return None
            lease=uuid.uuid4().hex
            db.execute('UPDATE handoff_attempts SET lease_until=?,lease_token=?,attempts=attempts+1 WHERE handoff_id=?',
                       (now+60,lease,row['id']))
            return {'id':row['id'],'tenant':tenant,'conversation':row['conversation'],
                    'created_at':row['created_at'],'payload':json.loads(row['payload']),
                    'lease':lease,'attempts':row['attempts']+1}

    def finish_handoff_delivery(self, job, *, accepted):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT attempts FROM handoff_attempts WHERE handoff_id=? AND lease_token=?',
                           (job['id'],job['lease'])).fetchone()
            if row is None:
                return False
            state='stored_in_operator' if accepted else ('failed' if row['attempts'] >= 10 else 'pending')
            db.execute('UPDATE handoffs SET delivery_state=? WHERE id=? AND tenant=?',(state,job['id'],job['tenant']))
            if state == 'failed':
                db.execute('INSERT OR IGNORE INTO handoff_failure_alerts(handoff_id,created_at) VALUES(?,?)',
                           (job['id'],time.time()))
            db.execute('UPDATE handoff_attempts SET lease_until=0,lease_token=NULL,next_attempt_at=?,last_error_code=? WHERE handoff_id=?',
                       (time.time()+min(1800,2**min(row['attempts'],10)),None if accepted else 'operator_delivery_failed',job['id']))
            return True

    def failed_handoffs(self, tenant):
        with self.connect() as db:
            return [dict(row) for row in db.execute(
                'SELECT h.id,h.conversation,h.created_at,a.attempts,a.last_error_code '
                'FROM handoffs h JOIN handoff_attempts a ON a.handoff_id=h.id '
                "WHERE h.tenant=? AND h.delivery_state='failed' ORDER BY h.created_at", (tenant,))]

    def requeue_failed_handoff(self, tenant, identity, actor):
        if not isinstance(actor,str) or not actor.strip() or len(actor)>160:
            raise ValueError('Recovery actor is required')
        now=time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT h.delivery_state,a.attempts,a.lease_until FROM handoffs h '
                'JOIN handoff_attempts a ON a.handoff_id=h.id WHERE h.tenant=? AND h.id=?',
                (tenant,identity)).fetchone()
            if row is None:
                raise ProposalNotFound('Handoff not found')
            if row['delivery_state']!='failed' or row['lease_until']>now:
                raise ProposalConflict('Only failed handoffs without an active lease can be requeued')
            db.execute('INSERT INTO handoff_recovery_events(handoff_id,tenant,actor,at,previous_attempts) VALUES(?,?,?,?,?)',
                       (identity,tenant,actor.strip(),now,row['attempts']))
            db.execute("UPDATE handoffs SET delivery_state='pending' WHERE id=? AND tenant=?",(identity,tenant))
            db.execute('UPDATE handoff_attempts SET attempts=0,next_attempt_at=0,lease_until=0,lease_token=NULL '
                       'WHERE handoff_id=?',(identity,))
            return {'handoff_id':identity,'delivery_status':'pending'}

    def claim_handoff_failure_alert(self, tenant):
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("INSERT OR IGNORE INTO handoff_failure_alerts(handoff_id,created_at) "
                       "SELECT id,? FROM handoffs WHERE tenant=? AND delivery_state='failed'", (now,tenant))
            row = db.execute('SELECT a.*,h.conversation FROM handoff_failure_alerts a '
                'JOIN handoffs h ON h.id=a.handoff_id WHERE h.tenant=? AND a.delivered=0 '
                'AND a.next_attempt_at<=? AND a.lease_until<=? ORDER BY a.created_at LIMIT 1',
                (tenant,now,now)).fetchone()
            if row is None:
                return None
            lease = uuid.uuid4().hex
            db.execute('UPDATE handoff_failure_alerts SET lease_token=?,lease_until=?,attempts=attempts+1 WHERE handoff_id=?',
                       (lease,now+60,row['handoff_id']))
            return {**dict(row),'tenant':tenant,'lease':lease}

    def finish_handoff_failure_alert(self, job, accepted):
        with self.connect() as db:
            result = db.execute('UPDATE handoff_failure_alerts SET delivered=?,lease_token=NULL,lease_until=0,'
                'next_attempt_at=? WHERE handoff_id=? AND lease_token=?',
                (int(accepted),time.time()+300,job['handoff_id'],job['lease']))
            return result.rowcount == 1

    def issue_grant(self, tenant, conversation, purpose, payload, ttl_seconds=1800):
        if not tenant or not conversation or purpose not in {'patient','offer'} or ttl_seconds <= 0:
            raise ValueError('Invalid grant scope')
        token=secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('INSERT INTO grants VALUES(?,?,?,?,?,?)',
                       (hashlib.sha256(token.encode()).hexdigest(),tenant,conversation,purpose,
                        json.dumps(payload,sort_keys=True),time.time()+ttl_seconds))
        return token

    def resolve_grant(self, tenant, conversation, purpose, token):
        if not isinstance(token,str) or len(token)>200:
            raise ProposalConflict('Verification reference is invalid or expired')
        with self.connect() as db:
            row=db.execute('SELECT payload FROM grants WHERE token_hash=? AND tenant=? AND conversation=? AND purpose=? AND expires_at>?',
                           (hashlib.sha256(token.encode()).hexdigest(),tenant,conversation,purpose,time.time())).fetchone()
            if row is None:
                raise ProposalConflict('Verification reference is invalid or expired')
            return json.loads(row['payload'])

    def get(self, tenant, identity):
        self.expire_pending(tenant, identity)
        with self.connect() as db:
            row=db.execute('SELECT * FROM proposals WHERE tenant=? AND id=?',(tenant,identity)).fetchone()
            if row is None:
                raise ProposalNotFound('Proposal not found')
            return self.public(row)

    def detail(self, tenant, identity):
        """Tenant-scoped snapshot of state and audit; no execution payload."""
        self.expire_pending(tenant, identity)
        with self.connect() as db:
            db.execute('BEGIN')
            row = db.execute('SELECT * FROM proposals WHERE tenant=? AND id=?',
                             (tenant, identity)).fetchone()
            if row is None:
                raise ProposalNotFound('Proposal not found')
            history = [dict(event) for event in db.execute(
                'SELECT state,actor,at FROM proposal_events WHERE proposal_id=? ORDER BY id',
                (identity,))]
            return {**self.public(row), 'actor': row['actor'], 'history': history}

    def replay_submission(self, tenant, request_key, request_digest):
        """Return a previously accepted exact request without resolving old grants."""
        with self.connect() as db:
            row = db.execute('SELECT * FROM proposals WHERE tenant=? AND request_key=?',
                             (tenant, request_key)).fetchone()
            if row is None:
                return None
            if json.loads(row['payload']).get('request_digest') != request_digest:
                raise ProposalConflict('Request key already used for different request')
            identity = row['id']
        # Replays retain the original request ID but report its current lifetime.
        return self.get(tenant, identity)

    def pending_payload(self, tenant, identity, version):
        """Expire stale requests, then read the private execution payload."""
        self.expire_pending(tenant, identity)
        with self.connect() as db:
            row = db.execute('SELECT * FROM proposals WHERE tenant=? AND id=?',
                             (tenant, identity)).fetchone()
            if row is None:
                raise ProposalNotFound('Proposal not found')
            if row['state'] != 'pending_staff_review' or row['version'] != version:
                raise ProposalConflict('Proposal is no longer awaiting this decision')
            if row['expires_at'] <= time.time():
                raise ProposalConflict('Proposal has expired')
            if hashlib.sha256(row['payload'].encode()).hexdigest() != row['digest']:
                raise ProposalConflict('Stored proposal integrity check failed')
            return json.loads(row['payload'])

    def submit(self, tenant, request_key, payload, summary, *, ttl_seconds=86400):
        if not tenant or not request_key or ttl_seconds <= 0:
            raise ValueError('Invalid proposal identity or lifetime')
        self.expire_pending(tenant)
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(',',':'))
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM proposals WHERE tenant=? AND request_key=?',(tenant,request_key)).fetchone()
            if row:
                # A racing exact retry may have derived a newer DB snapshot.
                # The first accepted request remains authoritative.
                if payload.get('request_digest') and json.loads(row['payload']).get('request_digest') == payload['request_digest']:
                    return self.public(row)
                if row['digest'] != digest:
                    raise ProposalConflict('Request key already used for different payload')
                return self.public(row)
            identity = 'proposal_' + uuid.uuid4().hex
            db.execute('INSERT INTO proposals(id,tenant,request_key,digest,payload,summary,state,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?)',
                       (identity,tenant,request_key,digest,encoded,json.dumps(summary,ensure_ascii=False),'pending_staff_review',now,now+ttl_seconds))
            db.execute('INSERT INTO proposal_events(proposal_id,state,at) VALUES(?,?,?)',(identity,'pending_staff_review',now))
            return self.public(db.execute('SELECT * FROM proposals WHERE id=?',(identity,)).fetchone())

    def expire_pending(self, tenant, identity=None):
        """Expire only unclaimed requests; retain them for staff follow-up."""
        now = time.time()
        where = "tenant=? AND state='pending_staff_review' AND expires_at<=?"
        params = [tenant, now]
        if identity is not None:
            where += ' AND id=?'
            params.append(identity)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("INSERT INTO proposal_events(proposal_id,state,actor,at) "
                       "SELECT id,'expired',NULL,? FROM proposals WHERE " + where,
                       [now, *params])
            db.execute("UPDATE proposals SET state='expired',version=version+1 WHERE " + where, params)

    def list(self, tenant, limit=100):
        self.expire_pending(tenant)
        with self.connect() as db:
            return [self.public(r) for r in db.execute('SELECT * FROM proposals WHERE tenant=? ORDER BY created_at DESC LIMIT ?', (tenant,min(max(limit,1),100)))]

    def page(self, tenant, *, cursor=None, include_closed=False):
        self.expire_pending(tenant)
        with self.connect() as db:
            parameters = [tenant]
            filters = ['tenant=?']
            if not include_closed:
                filters.append("state NOT IN ('committed','rejected')")
            if cursor is not None:
                if not isinstance(cursor, str) or not 1 <= len(cursor) <= 160:
                    raise ProposalConflict('Invalid list cursor')
                anchor = db.execute('SELECT created_at,id FROM proposals WHERE tenant=? AND id=?',
                                    (tenant, cursor)).fetchone()
                if anchor is None:
                    raise ProposalConflict('Invalid list cursor; refresh the list')
                filters.append('(created_at>? OR (created_at=? AND id>?))')
                parameters.extend([anchor['created_at'], anchor['created_at'], anchor['id']])
            rows = db.execute('SELECT * FROM proposals WHERE ' + ' AND '.join(filters) +
                              ' ORDER BY created_at,id LIMIT 101', parameters).fetchall()
            return {'items': [self.public(r) for r in rows[:100]],
                    'next_cursor': rows[99]['id'] if len(rows) > 100 else None}

    def decide(self, tenant, identity, version, actor, *, approve):
        if not actor:
            raise ValueError('Verified staff actor is required')
        self.expire_pending(tenant, identity)
        expired = False
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM proposals WHERE tenant=? AND id=?',(tenant,identity)).fetchone()
            if row is None:
                raise ProposalNotFound('Proposal not found')
            allowed = {'pending_staff_review'} if approve else {'pending_staff_review', 'expired'}
            if row['state'] not in allowed or row['version'] != version:
                raise ProposalConflict('Proposal is no longer awaiting this decision')
            if approve and hashlib.sha256(row['payload'].encode()).hexdigest() != row['digest']:
                raise ProposalConflict('Stored proposal integrity check failed')
            expired = approve and row['expires_at'] <= time.time()
            state = 'expired' if expired else ('executing' if approve else 'rejected')
            db.execute('UPDATE proposals SET state=?,version=version+1,actor=? WHERE id=?',(state,actor,identity))
            db.execute('INSERT INTO proposal_events(proposal_id,state,actor,at) VALUES(?,?,?,?)',(identity,state,actor,time.time()))
            updated = db.execute('SELECT * FROM proposals WHERE id=?',(identity,)).fetchone()
            result = self.public(updated)
            # Payload returned only to the internal execution service; never
            # serialize this tuple as a browser/agent response.
            payload = json.loads(row['payload']) if approve and not expired else None
        if expired:
            raise ProposalConflict('Proposal has expired; no write was authorized')
        return result, payload

    def finish(self, tenant, identity, version, state, result, *, event=None):
        if state not in {'committed','conflict','failed','needs_reconciliation'}:
            raise ValueError('Invalid execution outcome')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM proposals WHERE tenant=? AND id=?',(tenant,identity)).fetchone()
            if row is None:
                raise ProposalNotFound('Proposal not found')
            if row['state']!='executing' or row['version']!=version:
                raise ProposalConflict('Execution is not held by this claim')
            db.execute('UPDATE proposals SET state=?,version=version+1,result=? WHERE id=?',(state,json.dumps(result),identity))
            db.execute('INSERT INTO proposal_events(proposal_id,state,actor,at) VALUES(?,?,?,?)',(identity,state,row['actor'],time.time()))
            if event is not None:
                if event.get('tenant_key') != tenant or event.get('event_id') != identity + ':execution':
                    raise ValueError('Execution event identity mismatch')
                db.execute('INSERT INTO execution_outbox(proposal_id,tenant,event) VALUES(?,?,?)',
                           (identity, tenant, json.dumps(event, ensure_ascii=False)))
            return self.public(db.execute('SELECT * FROM proposals WHERE id=?',(identity,)).fetchone())

    def claim_execution_event(self, tenant):
        now = time.time()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM execution_outbox WHERE tenant=? AND delivered=0 '
                             'AND next_attempt_at<=? AND lease_until<=? ORDER BY next_attempt_at,proposal_id LIMIT 1',
                             (tenant, now, now)).fetchone()
            if row is None:
                return None
            token = secrets.token_hex(24)
            db.execute('UPDATE execution_outbox SET lease_until=?,lease_token=?,attempts=attempts+1 WHERE proposal_id=?',
                       (now + 60, token, row['proposal_id']))
            return {'proposal_id': row['proposal_id'], 'tenant': tenant, 'lease_token': token,
                    'event': json.loads(row['event'])}

    def queue_stalled_executions(self, tenant):
        """Alert once after ten minutes; never infer rollback or release a claim."""
        now = time.time()
        queued = 0
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('''SELECT p.id,p.payload FROM proposals p
                WHERE p.tenant=? AND p.state='executing'
                AND (SELECT MAX(e.at) FROM proposal_events e
                     WHERE e.proposal_id=p.id AND e.state='executing') <= ?
                AND NOT EXISTS(SELECT 1 FROM execution_outbox o WHERE o.proposal_id=p.id || ':stalled')
                ORDER BY p.created_at LIMIT 50''', (tenant, now - 600)).fetchall()
            for row in rows:
                payload = json.loads(row['payload'])
                conversation = payload.get('conversation_id')
                if not isinstance(conversation, str) or not conversation:
                    continue
                identity = row['id']
                event = {
                    'event_id': identity + ':execution_stalled', 'event_type': 'tool.failed',
                    'occurred_at': datetime.fromtimestamp(now, timezone.utc).isoformat(),
                    'tenant_key': tenant, 'conversation_id': conversation, 'source': 'medicus-api',
                    'tool_call': {
                        'name': 'appointment_write', 'endpoint': '/staff/proposals/{proposal_id}/approve',
                        'request_id': 'staff:' + identity + ':stalled', 'sequence_no': None,
                        'trace_id': 'staff:' + identity, 'http_status': 503,
                        'business_ok': False, 'is_error': True, 'error_code': 'execution_stalled',
                        'request_safe': {'action': payload.get('action'), 'proposal_id': identity,
                                         'execution_source': 'staff_approval'},
                        'response_safe': {'ok': False, 'status': 'needs_reconciliation',
                                          'booking_confirmed': False, 'reason': 'execution_stalled'},
                    },
                }
                db.execute('INSERT INTO execution_outbox(proposal_id,tenant,event) VALUES(?,?,?)',
                           (identity + ':stalled', tenant, json.dumps(event)))
                queued += 1
        return queued

    def finish_execution_event(self, job, accepted):
        with self.connect() as db:
            row = db.execute('SELECT attempts FROM execution_outbox WHERE tenant=? AND proposal_id=? '
                             'AND lease_token=? AND delivered=0',
                             (job['tenant'], job['proposal_id'], job['lease_token'])).fetchone()
            if row is None:
                return False
            delay = min(3600, 2 ** min(row['attempts'], 12))
            return db.execute('UPDATE execution_outbox SET delivered=?,next_attempt_at=?,lease_until=0,lease_token=NULL '
                              'WHERE tenant=? AND proposal_id=? AND lease_token=? AND delivered=0',
                              (int(accepted), time.time() + delay, job['tenant'], job['proposal_id'], job['lease_token'])).rowcount == 1
