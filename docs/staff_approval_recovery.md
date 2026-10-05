# Recovery: validated offers and staff-approved Medicus changes

Status: DESIGN ONLY, 2026-10-01. User clarified that the entire approval workflow
must remain a proposal for now. Do not implement further or deploy the existing
local prototype without a new user instruction. This is a proposed acceptance
contract, not a claim that the approval workflow is available. See also
pending_slot_holds_proposal.md for proposed concurrency/hold behavior.

## Closing audit of the currently authorized scope (2026-10-01)

- Mapping evidence is indexed below; the reported October 7 mismatch is
  explained by actual LASER occupancy and the main-calendar partial overlap.
- Previously verified corrections cover full interval overlap, past starts,
  recurrence-aware reads, actual LASER occupancy and unresolved doctor filters.
  This is evidence for the identified defects, not a guarantee against every
  possible scheduling or spoken-response defect.
- Fresh host inspection confirmed LASER enabled, direct writes/cancellations
  disabled and staff approval disabled. Deployed engine, agent-context and LASER
  module SHA256 hashes match the reviewed local files. Local search also has
  undeployed proposal-token changes, so its full-file hash is not expected to match.
- Running loopback API returned health 200, writes_not_enabled for all three
  actions, and HTTP 400 for disabled dermatoscopy availability. Public requests
  from the workstation also returned writes_not_enabled for all three actions.
  Python public requests originating on the server returned HTTP 403; this does
  not establish its cause or demonstrate an application write-policy failure.
- Create/move/cancel review, immutable offer binding, identity proof, staff
  authorization, idempotency, uncertainty handling and caller confirmation are
  specified here. Resource holds, expiry, concurrency and manual-writer limits
  are specified in pending_slot_holds_proposal.md. These remain proposals under
  the user's explicit design-only instruction, not unfinished deployment work
  authorized by an automatic continuation.
- Provider support and a proposed calibration/test handoff are recorded below.
  No live agent configuration or telephony change was made in this audit.

The requested diagnostic/safety work and design handoff are complete at this
scope. Future implementation and activation require a new instruction and the
acceptance evidence below. Approval cards and holds are not operational, and
end-to-end booking correctness must not be described as certified.

## Production containment verified

- Direct `create`, `cancel`, and `reschedule` return `ok=false`,
  `status=writes_not_enabled` at the public API. No write flag from a tool may
  override server configuration.
- Final-booking capability flags are disabled for all services.
- Dermatoscopy availability remains disabled. Real LASER calendar validation was
  subsequently deployed and the October 7 collision was reproduced and rejected;
  this does not activate public dermatoscopy offers or staff-approved booking.
- Public health remains 200. These restrictions are temporary; cards are not
  implemented yet. Existing agent prompt must not equate a received request or
  tool HTTP 200 with a confirmed booking.
- Previous local configuration is saved on the Medicus host in
  `config/api.before_staff_approval.local.json` and, if it existed,
  `config/business_rules.before_staff_approval.local.json`. Do not restore direct
  agent writes as a shortcut to deploying staff approvals.

## Evidence and mapping artifacts

- `research/db-mapping/schedule_interval_findings.md`: schedule intervals and
  calendar identities; validate exceptions/recurrence in the actual DB.
- `research/db-mapping/activity_type_mapping.md`: `IDCINNOSTI -> CINNOSTI`,
  activity colors and `OBJOBJ_SEL` recurrence expansion. TYP 9/10 must not be
  treated as ordinary date-equal bookings.
- `research/db-mapping/appointment_type_mapping.md`: appointment row fields.
- `research/db-mapping/phase3_rollback_insert_test.md`: rollback write evidence.
- `research/db-mapping/laser_medicus_instance_audit.md`: second DB discovery;
  explicitly not runtime integration. Main and LASER IDs are separate namespaces.
- `archive/day-audit-20261007.json` and corresponding HTML/CSV: patient-free
  current snapshot. Main doctor 12 has no booking 15:00–15:20; LASER calendar 5,
  workplace 1, activity 28 has 14:45–15:00 occupied. Both offered scan windows
  overlap this reservation. Snapshot does not prove historical call-time state.

Confirmed deterministic defects: slot-start-only overlap check (fixed), past
options (fixed), absent LASER read (subsequently fixed), absent LASER reservation write
(unfixed and blocked by disabled writes). Recurrence-aware reads and rejection of
unknown/ambiguous doctor filters were also deployed. Spoken mixing of returned objects is separately observed; no claim
that prompting alone prevents it.

## Intended workflow

1. Backend produces validated offers with an opaque, expiring offer ID bound to
   tenant, conversation, service, doctor, workplace, date and exact doctor/scan
   intervals. Reordering speech must not change that binding.
2. Agent collects caller consent to submit the specific request. It submits a
   proposal, not a Medicus mutation. Agent response distinguishes
   `pending_staff_review` from `committed`; caller is told confirmation is pending.
3. Durable card appears in Operator, even before the post-call webhook arrives.
   Card displays operation, original appointment for cancel/move, proposed target,
   caller contact, validation state and a link to the conversation when available.
   Sensitive execution payload stays on the protected Medicus host; it is not
   copied into telemetry or browser responses. Staff can identify the request
   through existing authorized conversation data.
4. Authenticated, tenant-authorized staff approve or reject the immutable proposal.
   Browser cannot choose actor/tenant or rewrite the execution payload. Rejection
   performs no Medicus mutation. Changing a target creates a new proposal version.
5. Approval takes an exclusive claim, checks expiry, patient identity, ownership
   and unchanged source appointment, rechecks both calendars and all business
   rules, then executes. Approval is not an unconditional write authorization.
6. Conflict/expiry results in an actionable card, not a substituted time or doctor.
   Successful commit becomes `committed`. Uncertain commit becomes
   `needs_reconciliation` and MUST NOT be blindly retried. Record actor, time,
   proposal version and technical result. Notify caller only through an explicitly
   configured confirmation workflow; never claim an unsent notification occurred.

## Persistence and security decisions

- Use a protected on-host durable request store for execution payloads, separate
  from Firebird. Keep browser-facing projections tenant-scoped and allowlisted.
- Public agent token can submit/read its result, never approve or execute.
  Approval uses a distinct server-only credential through the authenticated
  Operator backend/proxy. An `approved=true` tool argument is never trusted.
- Deduplicate delivery by a validated request key and canonical payload digest.
  Duplicate key with altered payload fails. Repeated staff clicks execute once.
- Persist execution intent before starting a Firebird transaction. If process
  dies after possible commit, retain uncertainty and reconcile from authoritative
  records; do not reset to pending automatically.
- Main and LASER patient IDs must never be copied between databases. Establish
  verified mapping or stop for staff resolution. Define scan activity/calendar
  mapping explicitly rather than inferring it from display names.
- Cross-database create/move/cancel requires an explicit atomicity/recovery design
  and linked record receipts before enabling staff execution for dermatoscopy.
  A main-only booking is not a completed dermatoscopy booking.

## Design decisions required before future implementation

- Staff coverage and review deadline determine the pending hold lifetime. The
  proposed 30 minutes is not an agreed service level. On expiry the card must
  visibly require a new offer; it cannot remain apparently actionable.
- Define who can review each clinic and how staff receive new-card and delayed
  review notifications. Notification failure must not delete the durable card.
- Agree how callers receive final confirmation or rejection and which contact
  data is verified. Successful database commit and successful message delivery
  are separate outcomes; failed delivery must never retry the booking itself.
- Confirm main/LASER patient identity mapping and linked appointment identities
  for create, move and cancel. Unmapped or ambiguous records require staff
  resolution; a name match alone is not a safe cross-database identity key.
- Choose a supported concurrency mechanism shared with manual Medicus writers
  before claiming protection against their simultaneous writes. Local holds
  guarantee exclusivity only among cooperating API proposals.
- Establish an authorized reconciliation procedure for uncertain commits:
  inspect both databases and transaction outcome, identify linked records,
  record the evidence and reviewer, and only then resolve quarantine. Neither
  timeout nor absence of an immediate response proves rollback.

These are implementation gates, not requests to enable or deploy the prototype.

## Future implementation acceptance evidence required

- Real calendar reads cover normal/recurring bookings, schedule exceptions,
  block boundaries, all scan activities, unavailable LASER and unknown mappings.
- Fresh API no longer offers either colliding scan from the October 7 example.
- Create/cancel/move each persist a review card without touching Medicus.
- Unauthorized actor/other tenant/public tool token cannot approve.
- Reject leaves both DBs unchanged; approval writes expected linked records once.
- Stale slot, expired offer, changed original appointment, concurrency, repeated
  click, timeout and restart cannot cause duplicate or partial silent success.
- Staff UI rendered and exercised for pending, rejected, committed, conflict and
  uncertain states; controls do not promise success before backend confirmation.
- Deployment checks cover live public submission, staff auth, worker/store
  restart durability and rollback. Controlled write tests use the designated test
  patient and clearly specified reversible records, never real patient mutations.
- Known UI/tool-response visibility issue is tracked separately from provider
  speech: inspect actual stored sanitized tool evidence and role stripping.

## Execution candidate, 2026-10-05

The local API now has a staff-authenticated `/staff/proposals/{id}/approve`
endpoint. It requires both `enable_staff_execution` and
`enable_appointment_writes`; the example defaults to disabled. It is not
deployed or enabled on the production server. The agent token cannot approve.
The trusted staff gateway must supply the authenticated staff actor; do not
expose the staff token to the browser or accept a browser-selected actor.

Execution uses the stored payload, an atomic version/expiry/integrity claim,
and a stable journal key derived from the proposal ID. The immutable patient,
source and offer snapshots are revalidated inside the protected write
transaction. Pair validation receives the transaction's LASER cursor rather
than opening an unrelated calendar snapshot. Repeated approval cannot claim
an executing or completed card. Public results exclude full booking rows,
patient identity, free text and tokens.

A known negative writer result becomes conflict; failure before entering the
writer becomes failed. Exceptions after entering the writer become
needs_reconciliation. Failure to persist the outcome leaves executing and
never retries the Firebird operation. A rejected or ambiguous decision is
not a confirmed booking. A separate recovery workflow must reconcile an
executing card after a process crash; that workflow is still incomplete.

Single-calendar rescheduling now uses an UPDATE candidate preserving IDOBJ and
notes, based on the observed GUI move. It supports ordinary skin cells and
mapped post-scan checks, rejecting service changes, recurrence, arrived visits,
external links and OBJPROC pending further mapping. A savepoint excludes only
the original row for availability checking; temporary delete effects are rolled
back before UPDATE. SQLite transaction tests cover restoration and history,
but they do not prove Firebird trigger behavior. A live API move is still required.
The same live table-lock limitation applies to staff execution as to direct
paired writes. Normal concurrent staff activity, complete side-effect checks,
Operator proxy/UI wiring, execution failure notifications and production
rollout remain to be verified before enablement.

Local verification: `python -m pytest tests -q`, 213 passed. The earlier
187-test unittest run did not collect pytest-style functions; use pytest for
the full suite. Eight new executor tests cover disabled configuration, duplicate
approval, immutable payload use, sanitization, connection failure, lost ACK,
outcome-persistence failure, claim integrity and endpoint authorization.

## Later calibration (not a blocker to implementing safeguards)

Review early hangups, introduction latency, interruption/turn-taking, unmet intent,
and requests for a human using a bounded sample with timestamps. Human-request
intent should trigger offered handoff without repeated resistance. Verify current
ElevenLabs support before relying on frustration signals; an analysis label after
the call is not evidence of an actionable live signal. Do not promise automatic
frustration escalation until tool/prompt behavior is exercised.

### Provider documentation checked 2026-10-01 (proposal only)

ElevenLabs [sentiment analysis](https://elevenlabs.io/docs/eleven-agents/customization/agent-analysis/sentiment-analysis)
is computed from completed conversation transcripts. This feature is not itself
a live frustration trigger. The specific frustration label observed by staff has
not been identified, so do not assume it is this metric or an available live API.

[Transfer to number](https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number)
supports natural-language transfer conditions, including an explicit request for
a human. Proposed behavior: honor that request immediately; offer transfer when
the caller expresses frustration or repeated attempts fail. Do not require a
numeric sentiment threshold. Actual transfer destination, availability and failure
handling still require a controlled call; this documentation check does not prove
the deployed agent is configured correctly. Telephony remains user-managed.

Suggested Architect instruction (not applied):

> If the caller explicitly asks for a human, acknowledge briefly and use the
> configured human transfer tool without continuing the booking interview. If
> repeated misunderstandings occur or the caller expresses frustration, offer
> human assistance. Never claim a transfer succeeded before its result confirms
> it. If transfer fails, explain that clearly and offer only an actually available
> callback workflow. Never describe a pending request as a confirmed booking.

[Agent Testing](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing)
supports next-response, tool-call and conversation simulation tests. Proposed
cases: explicit human request during interruption; repeated misunderstanding;
transfer failure; no callback workflow; booking pending versus committed; and
the supplied doctor/time mixing example. Verify exact offer fields in tool tests
and spoken content in response tests. Use a controlled transfer destination:
system tools are not mocked. For mocked webhook tools, use error fallback instead
of calling the real tool on an unmatched fixture. Audio timing/interruptions also
need real controlled phone tests; text tests cannot establish their quality.
