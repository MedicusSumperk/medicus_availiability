# Read-only availability rollout candidate

Candidate over deployed handoff1, prepared 2026-10-02. Not deployed yet.
Preserves the live LASER reader and handoff worker. Never enable appointment
writes, cancellations or staff approval as part of this rollout.

Changes: schedule exceptions, per-cell duration on mixed 10/15-minute days,
complete overlap rejection, invalid-interval failure, weekdays/Czech holidays,
arrival preference and lead time including scan, six-calendar-month horizon.
The available capabilities now honor the API write switch: disabled writes
yield no bookable services and a staff-handoff explanation.

Appointment validation's search filter uses technical_start_time, not the
patient arrival preference window. No Firebird INSERT/UPDATE/DELETE or schema
logic is changed by that adjustment; the write path remains disabled.

87 focused tests passed locally. Before activation, compare the candidate
read-only against actual MAIN/LASER data (including 7 October) and verify
production business/laser config without copying credentials to the repository.
Protect all live dirty changes; replace only inspected and backed-up modules.
Do not enable currently disabled service types on guessed activity mapping.
The API currently defaults lead time to request-processing time; durable
first-call anchoring across all tools belongs to the later complete v2 rollout.
GUI create/move/cancel verification and final approval execution remain pending.

Live read-only probe on 2 October: both returned skin options for doctor 12 on
7 October have no overlap against OBJOBJ_SEL. Saturday 3 October and holiday
28 October return no options. The historical incident's 15:00/15:10 exam times
are MAIN-free but their scans overlap LASER; 15:50 overlaps both calendars.
All three are excluded by the candidate. This verifies current occupancy,
not a reconstruction of the original call's database snapshot.

Dermatoscope availability remains disabled in production configuration. The
probe overrides that flag only in process memory for diagnostic calculation;
it neither changes config nor enables writes. No combined free option was
found for this doctor in the additional 8–16 October window, so a positive
real combined-booking case is not established by this sample. Synthetic
positive cases are covered by regression tests. Evidence: docs/availability_v2_live_probe.json.
