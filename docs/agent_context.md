# Pre-call Agent Context

## Goal

Build a compact read-only context before an AI receptionist call so the agent knows where it can safely offer appointments.

The context is intentionally not a production booking API yet. It is a pre-call snapshot for testing agent behavior against real reception scenarios.

## Command

Create local config:

```cmd
copy config\agent_context.local.example.json config\agent_context.local.json
```

Run:

```powershell
C:\python\python.exe scripts\build_agent_context_cli.py
```

Outputs:

```text
data/agent_context/agent_context_latest.json
data/agent_context/agent_context_latest.md
data/agent_context/agent_context_YYYYMMDD_HHMMSS.json
data/agent_context/agent_context_YYYYMMDD_HHMMSS.md
```

The JSON is intended for the agent. The Markdown is a short human-readable check.

## Default Window

The default config currently uses:

- start date: today
- days ahead: 14 included business days
- weekends: excluded
- unscheduled doctors: excluded
- max options per service / doctor / day: 6
- fallback slot interval: 15 minutes

The fallback slot interval is used only when the database schedule context does not expose an `INTERVAL`. Normal planning should use `OBSDNE_PRAVODLIS_SEL.INTERVAL` for the concrete doctor/date/context.

These values are placeholders until the needed pre-call context range and size are confirmed.

## Included Services

V1 context includes:

### Skin Examination

Booking shape:

- `TYP = 1`
- `IDCINNOSTI = NULL`

Bookability rules:

- selected skin slot must be free
- skin duration defaults to the schedule interval for that doctor/context
- immediate follow-up dermatoscope duration defaults to the same schedule interval
- immediate follow-up slot for the same doctor must be free
- follow-up interval must not overlap shared dermatoscope usage anywhere else
- follow-up slot is not written automatically in V1

This handles doctors with non-15-minute schedules. Confirmed business finding: Rostislav Bednar should use 10-minute skin and follow-up dermatoscope intervals; verify `IDUZI` and whether other doctors also have 10-minute intervals with `scripts/tests/inspect_schedule_intervals.py`.

### Plasma

Booking shape:

- `TYP = 1`
- `IDCINNOSTI = 3`
- `INFO` should contain a plasma marker

Bookability rules:

- configured appointment duration must fit into consecutive free slots
- consecutive slot checks use the schedule interval for that doctor/context
- no follow-up dermatoscope slot is required

Current default duration is 30 minutes, based on observed rows. Confirm before production booking.

## Dermatoscope Blockers

The context treats these as shared dermatoscope blockers:

```text
IDCINNOSTI IN (1, 2, 5, 6)
```

Actual blocker intervals are read from `OBJOBJ.CAS` / `OBJOBJ.CASDO` and compared as time intervals, not just equal slot starts. This matters when one doctor has 10-minute slots and another has 15-minute slots.

## Doctor Filtering

The config supports:

```json
"allowed_doctor_ids": [],
"excluded_doctor_ids": [],
"include_unscheduled_doctors": false
```

Current default is to consider all doctors returned by `UZIVATEL`, then include only doctors who have a schedule for each day. This keeps the agent context compact and avoids returning a full matrix of non-ordinating doctors.

For diagnostics, set `include_unscheduled_doctors` to `true` to include doctors without a schedule.

## Schedule Interval Diagnostic

Run this read-only script to verify doctor slot intervals:

```powershell
C:\python\python.exe scripts\tests\inspect_schedule_intervals.py
```

Use it to confirm:

- whether Rostislav Bednar is `IDUZI=6`
- which doctors have 10-minute intervals
- whether any doctor/date/context has mixed intervals
- which `IDPRAC` / `TYPTYD` context produced the interval

## Output Shape

The JSON contains:

- generated timestamp
- included date range
- rule summary
- days
- scheduled doctors per day
- raw free-slot count
- bookable skin options
- bookable plasma options
- option `duration_minutes`
- option `slot_interval_minutes`
- limited rejection reasons for debugging

The agent should use `services.skin` and `services.plasma` options, not raw free slots.

## Known Limitations

- Bookable doctor filtering is not final.
- Manual exceptions are not yet encoded.
- Plasma exact `INFO` text and fixed duration are still to confirm.
- Skin seasonal rules are not yet encoded.
- Week-type source (`TYPTYD`) still needs deeper verification.
- Context size/window should be tuned after real reception scenario mapping.

## Safety

This context builder is read-only. It does not write appointments.
