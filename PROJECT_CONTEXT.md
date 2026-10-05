# Medicus Backend Context

This repository is the backend layer for the ElevenLabs receptionist agent. It
keeps DB-specific and clinic-specific business rules in backend code/config so
the voice agent can call simple tools instead of carrying operational rules in
its prompt.

## Current State

- Stable public base URL: `https://medicus-api.kreli.org`
- Server repo path: `C:\db_bridge\medicus_availiability`
- Active branch for hardening work: `feature/production-hardening-rules-cleanup`
- Runtime API endpoints: `/health`, `/doctor-availability`, `/patient-lookup`,
  `/book-appointment`, `/handoff-summary`
- Patient lookup no longer requires last-4 birth-number verification; unique
  patient match sets `verification.verified=true`
- Appointment writes and cancellations are controlled by server-local
  `config/api.local.json`

The misspelled repo/folder name `medicus_availiability` is intentionally kept
for now. Rename only through a separate coordinated GitHub/server migration.

## Runtime Source Of Truth

- `scripts/api_server.py`: FastAPI endpoint layer
- `scripts/agent_context.py`: shared service option helpers used by availability
- `scripts/availability_search.py`: targeted availability lookup for tool calls
- `scripts/appointment_write.py`: create/cancel/reschedule write helper
- `scripts/patient_lookup.py`: patient identity and appointment lookup
- `scripts/handoff_summary.py`: staff-facing handoff summary builder
- `scripts/business_rules.py`: JSON rules loader and validation
- `config/business_rules.example.json`: versioned default business rules
- `config/business_rules.local.json`: optional ignored server-local override

Human-readable rules are generated into `docs/current_business_rules.md` with:

```powershell
C:\python\python.exe scripts\render_business_rules.py
```

## Current Business Rules Highlights

- Globally excluded `IDUZI`: `4`, `10`
- Bednar uses active `IDUZI=2`; duplicate `IDUZI=4` is excluded
- Skin is an ordinary insurance-covered examination without scan or follow-up
- Dermatoscopy is a separate paid service with a 15-minute inferred scan slot
  before the doctor appointment
- Post-scan checks remain staff handoff until the 6-month scan validation is
  confirmed
- Slots before `08:00` are hidden unless availability request has
  `emergency=true`
- Afternoon skin slots from `15:00` to `16:00` may expose a shared
  `spoken_time_label=15:00` while writes still use exact technical `start_time`
- A separate LASER Medicus instance exists at
  `C:\Medicus 3 Laser\data\MEDICUS.FDB`; v1 runtime does not depend on it

## Repository Organization

- `scripts/`: active runtime backend only
- `tests/`: unit/regression tests for runtime behavior
- `config/`: runtime config examples and checked-in business rules
- `docs/`: current source-of-truth documentation only
- `tools/diagnostics/`: manually run diagnostics and DB mapping helpers
- `research/`: important DB findings and reverse-engineering notes
- `archive/`: ignored historical exports, test runs, and obsolete artefacts

See `docs/repo_inventory.md` for the detailed file map.

## Verification Commands

```powershell
C:\python\python.exe -m unittest discover -s tests
C:\python\python.exe scripts\render_business_rules.py --check
```

Server smoke checks after deploy:

```text
GET  https://medicus-api.kreli.org/health
POST https://medicus-api.kreli.org/doctor-availability
POST https://medicus-api.kreli.org/patient-lookup
POST https://medicus-api.kreli.org/book-appointment
POST https://medicus-api.kreli.org/handoff-summary
```

## Availability incident fix — 2026-10-01 (deployed)
Read-only reproduction against live Firebird found API options 2026-10-01 15:40–15:50 (IDUZI 11) overlapping an appointment starting 15:45, and 2026-10-07 15:50–16:00 (IDUZI 12) overlapping one starting 15:55. The engine checked only whether slot start was inside a booking; it now checks the entire schedule-slot interval. Slots extending past the schedule block are excluded. No patient data was modified.
Search now excludes past dates/times using Europe/Prague, including a dermatoscopy scan start before the doctor appointment. Time filtering happens before candidate limits. Existing booking validation reuses search_availability, so stale past/overlapping proposals are rejected there too. Added tzdata dependency for Windows and installed it on the server.
Validation: local unittest suite 44 passed; server suite 42 passed. Same live eight-day skin search changed from six results (two overlaps and one past time) to three results with zero overlaps or past starts. Public doctor-availability returned those three results after restart; past-day search returned zero; public health 200. Changes deployed to scripts/availability_engine.py and scripts/availability_search.py; rollback copies are in archive/availability-fix-20261001/*.before. Medicus Local API scheduled task restarted. Concrete staff-reported ElevenLabs example still pending; that may reveal additional causes. Raw tool-response visibility in Operator is a separate reported follow-up.

## Confirmed cross-calendar discrepancy — 2026-10-01
User requested full read-only day comparison for 2026-10-07 in both databases. Exported patient-free schedules and appointments to ignored archive/day-audit-20261007.json, medicus-day-20261007.html and .csv. Main: 64 direct/64 OBJOBJ_SEL expanded rows, 11 API-discovered schedule blocks. LASER: 20 direct/20 expanded rows, 9 schedule blocks. Both ordinary and recurring appointments queried through the existing OBJOBJ_SEL procedure.
Main IDUZI 12 (Marta Skolarova) has no appointment overlapping 15:00–15:20, but has 15:55–16:20 (explains the already-fixed 15:50 overlap). LASER IDUZI 5 (Sken Foceni skeny), IDPRAC 1, has activity 28 Dermatoskop at 14:45–15:00 and 15:45–16:00. Thus proposed scans 14:45–15:00 and 14:55–15:10 both overlap the first LASER reservation. Current API still ignores LASER DB; its inferred scan capacity does not establish real scan-calendar availability. Cross-database scan availability integration remains unresolved, not fixed by the interval/time patch. Do not label these two dermatoscopy options confirmed available without checking this calendar. No patient writes were performed during the comparison.

## Active recovery goal: staff approval before mutations (2026-10-01)
User requested replacing direct agent create/move/cancel with durable staff-review cards and backend execution only after approval; deterministic availability defects must be eliminated. Goal remains ACTIVE and incomplete. See docs/staff_approval_recovery.md for full contract and completion gates.
Production containment applied and verified: config/api.local.json enable_appointment_writes=false and enable_appointment_cancellations=false; all three public actions returned ok=false/writes_not_enabled. Local business rules disable all final-booking capability flags and dermatoscope_first availability (public request verified 400, no offers). Health 200. Cards/approval execution are NOT implemented yet; next work must implement that workflow and real LASER availability, not restore unsafe direct writes. Backups in config/*.before_staff_approval.local.json (sensitive, server only). Other safe reads remain available.

## Recovery progress: actual LASER reads and proposal storage (2026-10-01)
Deployed laser_calendar.py, recurrence-aware main appointment and scan-blocker reads through OBJOBJ_SEL, and a fail-closed doctor filter (unknown/ambiguous requested doctor no longer falls back to other doctors). LASER map lives server-side in config/laser_calendar.local.json: database Medicus 3 Laser, calendar 5, workplace 1; scans check entire schedule coverage and all activity types. Separate read snapshot is closed/rolled back on exit; unavailable/malformed data cannot produce a verified scan. Test run against real databases rejected both Oct 7 scan intervals and returned zero dermatoscopy options for that day. Local suite 55 passed, server targeted LASER tests 5 passed. Public unknown-doctor test returned no substitute options; write prohibitions reverified for all three actions after restart. Dermatoscopy public availability remains intentionally disabled pending proposal workflow activation, not due to missing read code now.
Local-only approval_store.py implements durable SQLite proposals, immutable request-key/digest binding, tenant-scoped projections, compare-and-swap decision/version, exclusive execution claim, reject/expiry, audit events and explicit uncertain outcome. Concurrency/restart/tenant/expiry/rejection tests pass. This is not yet connected to tool submission, staff authentication, execution, or Operator UI; never report approval cards operational. Next implement validated proposal service, staff endpoints/proxy/UI, and cross-database execution with identity/atomicity/reconciliation. Existing patient_verified is caller-supplied boolean; historical DOB-validation commit changed prompt/docs only. New service needs server-backed identity verification, not trusting that boolean.

## Recovery progress: validated proposal API (local only, 2026-10-01)
Added approval_proposals.py and feature-gated API integration (enable_staff_approval, absolute approval_store_path, fixed operator_tenant_key). Patient lookup may issue opaque conversation/tenant-bound proof only after caller DOB plus name matched uniquely without fuzzy fallback; store retains patient fingerprint for revalidation. Availability issues opaque offer references with immutable date/doctor/service/scan snapshot. book-appointment in approval mode only submits a durable card and rolls back its read transaction; it never calls the old writer. Submitted echo fields conflicting with the offer, changed patient, missing consent/reference, invalid ownership/source and expired references are rejected. Original recurring appointments require separate staff handling rather than deleting a series.
Added staff-authenticated list/detail/reject endpoints; agent bearer token cannot access them. Staff approval/actual execution and UI are still NOT implemented. New staff key must be separate from agent token. Reference tokens are redacted from telemetry, including embedded options_json; corresponding Operator sanitizer change is local and must ship before public proofs are enabled. Local Medicus suite 64 passed, including endpoint checks that no write/commit occurs, isolated staff authorization and no DB call on rejection. Production remains in containment mode with these new proposal modules NOT deployed.
Distributed Firebird transaction support confirmed in installed fdb.ConnectionGroup and official FDB docs (https://firebirdsql.org/file/documentation/drivers_documentation/python/fdb/usage-guide.html). Use group.cursor(connection), not ordinary connection.cursor, for both participants. Commit uses 2PC; an uncertain commit still requires reconciliation and must not be retried. Next steps: implement staff executor, verify cross-database patient/scan links and transaction failure recovery, add Operator proxy/UI and tool contract changes, then deploy and verify end to end.

## User scope clarification: design only for approvals (2026-10-01)
User explicitly clarified: "Zatim pouze navrh celeho schvalovani" (entire staff-approval workflow is proposal-only for now), superseding prior implementation authorization for this workflow. Stop new approval/hold implementation and do not deploy the existing local approval_store, approval_proposals, proof-token API or staff endpoints. Preserve work without deleting it. Current production containment is unchanged: direct create/move/cancel disabled; public dermatoscopy offers disabled. Previously deployed deterministic read corrections remain in place. docs/pending_slot_holds_proposal.md is a design artifact only. Future implementation needs renewed user instruction; do not infer authorization from automatic goal continuation.

## Stage 1 mapping audit requested and delivered (2026-10-01)

New user instruction requires gated stages, beginning ONLY with mapping/business-rule audit, no production behavior changes. Review package: docs/stage1_mapping_audit/README.md, inventory.md, rules.json, schema.json, observed_server.json and validation_results.json. This draft replaces no business rule until human validation. It separates code, effective server configuration, fresh dictionary/procedure observations, historical documents and staff/user reports. Forty rules: 5 confirmed facts, 8 probable interpretations, 19 unclear, 8 conflicts. Stage 2 golden dataset and Stage 3 fixes have NOT started.

Fresh read-only DB evidence captured at 2026-10-01T18:20:30Z: MAIN IDUZI15 is Tamara Hrudova, while config known still says Filip Ferencz. Other review findings include conflicting skin followup descriptions, control/repeated-scan activity names, missing explicit service-doctor eligibility, exception-only schedule discovery, TYPTYD semantics, mixed context intervals, expired spoken arrival buckets, and uncertain cross-DB patient/appointment links. No business interpretation was silently selected. Snapshot excludes patient data and credentials; database transactions were read-only and rolled back.

Offline audit integrity/current-behavior characterization passes. Existing focused tests pass: availability12, LASER5, business20, patient11 (48 total). These tests describe current code, not staff-approved business correctness. Human validation remains pending; see the package's priority questions and Stage 1 validation procedure. Do not proceed to later stages without the user's approval of their concrete scope. Existing local prototype and user prompt changes preserved, no production deployment in this stage.
