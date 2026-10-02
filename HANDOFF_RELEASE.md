# Incremental durable handoff release

Based on server commit c767598. Only api_server.py and the new handoff/store/
backup/recovery modules are deployment inputs. Do not replace the full server
checkout: it contains separate LASER availability changes and local config.
This release exposes no proposal approval endpoints or execution path.
Appointment write/cancel flags must remain false.

Before applying: capture hashes and backup of existing api_server.py and config;
compare API source with the expected base. Refuse an unexpected source change.
Archive and test new modules without switching the API. Keep existing bearer,
handoff target and availability settings. No Firebird DDL or data changes.

Create a protected SQLite directory for SYSTEM and host Administrators only;
configure an absolute approval_store_path, fixed operator_tenant_key and the
existing Operator ingest URL/token. Initialize via handoff_config.handoff_store
using the same service config. Do not print credentials or handoff payloads.
The store schema is local SQLite, not Firebird or Supabase.

Enable enable_durable_handoff only when ElevenLabs sends X-Conversation-Id
from actual conversation metadata and a stable request_id in each request.
Missing identifiers are rejected rather than associating a request with a
guessed call. Until binding is ready, keep the switch false; the legacy endpoint
returns stored=false/not_queued and must not promise delivery.

After configuration, scripts/register_handoff_worker.ps1 registers only the
new SYSTEM startup task Medicus Handoff Delivery (refuses an existing task).
Restart only the API task after verifying its owning process/port. Never restart
the computer or Medicus application. Verify health, authorization and a marked
synthetic request end to end in Operator, including deduplicated retry and
follow-up resolution. Stored does not imply SMS or staff contact.

Rollback: stop the new worker, stop only the verified API process, restore its
previous file/config and restart its existing task. Retain the protected store
and queued requests; reconcile delivery before retries. Never delete the queue
as part of rollback. Disable (do not delete) the new task if no longer used.

Current status: deployed on 2026-10-02 after user confirmation of ElevenLabs
tool changes. SYSTEM API and handoff delivery tasks are running. Live
API/store/scheduled-worker/Operator test passed, including retry deduplication
and preservation of resolved follow-up. Test requests contain no patient data
and were marked resolved. Actual provider voice test and SMS remain pending.

Embedded server Python ignores PYTHONPATH and does not automatically add the
script directory. Worker/recovery explicitly add their own directory before
importing local modules. The fix is verified by the live scheduled process.

Backup helper `scripts/backup_handoff_store.ps1` writes unique SQLite snapshots
using the backup API, including WAL, and validates integrity. Its `backups`
directory must already exist beside the protected store. It writes a safe
last-success marker after success; task failure is nonzero. No pilot backup
is automatically deleted. These are same-host snapshots, not off-host disaster
recovery; retention and an off-host destination remain deployment follow-ups.
