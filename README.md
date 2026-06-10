# Medicus Availability Tools

Support scripts for a Medicus / Firebird PoC that will back an AI receptionist integration.

The target agent needs two reliable tools:

1. Check doctor availability.
2. Book a patient appointment.

Current work is still PoC/mapping. Availability diagnostics are read-only. Booking test utilities should be used only with client-approved test data.

## Setup

Create a local database config at:

```text
config/db_config.local.json
```

Expected shape:

```json
{
  "host": "...",
  "port": 3050,
  "database": "...",
  "username": "...",
  "password": "...",
  "charset": "UTF8"
}
```

Run scripts from the repository root with:

```powershell
C:\python\python.exe <script-path>
```

## Availability

Single doctor / single day CLI:

```powershell
C:\python\python.exe scripts\check_availability_cli.py
```

Weekly all-doctors CLI:

```powershell
C:\python\python.exe scripts\check_week_availability_cli.py
```

The weekly CLI checks Monday-Friday availability for all doctors and writes:

```text
data/availability/availability_YYYY-Www.json
data/availability/availability_YYYY-Www.csv
data/availability/availability_YYYY-Www.md
```

Inspect doctor schedule intervals:

```powershell
C:\python\python.exe scripts\tests\inspect_schedule_intervals.py
```

Use this read-only diagnostic to confirm 10-minute vs 15-minute doctor schedules. Current findings are recorded in `docs/schedule_interval_findings.md`.

## Pre-call Agent Context

Build a compact read-only context file before a call:

```cmd
copy config\agent_context.local.example.json config\agent_context.local.json
```

```powershell
C:\python\python.exe scripts\build_agent_context_cli.py
```

Outputs are written to `data/agent_context/`:

```text
agent_context_latest.json
agent_context_latest.md
agent_context_YYYYMMDD_HHMMSS.json
agent_context_YYYYMMDD_HHMMSS.md
```

The JSON is intended for the agent. The Markdown is a quick human-readable check. Current V1 context includes service-specific options for skin examination and plasma, with skin follow-up dermatoscope checks and shared dermatoscope blockers. Slot calculations use the concrete schedule interval from the doctor/day context where available, with the config interval only as fallback.

## Local API Service

Run a small local API service for Cloudflare Tunnel / ElevenLabs tool calls:

```cmd
copy config\api.local.example.json config\api.local.json
```

```powershell
C:\python\python.exe -m pip install -r requirements.txt
C:\python\python.exe scripts\api_server.py
```

Default local URL:

```text
http://127.0.0.1:8000
```

Implemented endpoints:

```text
GET  /health
POST /doctor-availability
POST /patient-lookup       # read-only patient + future appointment lookup
POST /book-appointment     # create/cancel/reschedule behind local write flags
```

`/doctor-availability` returns a short list of bookable options. With no body it returns the first default skin options. With filters it searches a targeted date/time window and stops after the requested limit. See `docs/local_api.md`.

The availability endpoint also accepts `doctor_name` as free text. The API resolves it against Medicus users and filters by doctor only when the match is clear.
For tool callers, common aliases such as `doctor`, `preferred_doctor`, and `doctorName` are normalized to `doctor_name`.
`IDUZI=2` is excluded as a suspected inactive duplicate Bednar row.

`/patient-lookup` finds patient candidates in `KAR`, supports phone lookup through `KARKONTAKT`, supports name/date/full `RODCIS` lookup, verifies identity with the last 4 digits of `RODCIS`, and returns future plus optionally past `OBJOBJ` appointments after verification. It is read-only.

`/book-appointment` can create, cancel, or reschedule appointments when local write flags are enabled. It revalidates create/reschedule requests against live availability before writing. For `service=skin`, it writes the main skin appointment plus the immediate dermatoscope reservation in one transaction.

Quick trycloudflare test tunnel:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_trycloudflare_api.ps1
```

The script starts the local API, starts `cloudflared tunnel --url http://127.0.0.1:8000`, prints the generated `https://...trycloudflare.com` base URL, and saves it to `data/api/trycloudflare_url.txt`.

## Appointment Type Mapping

Inspect appointment rows for a date so Medicus UI colors/types can be mapped to database values:

```powershell
C:\python\python.exe scripts\tests\inspect_appointment_types.py
```

See `docs/appointment_type_mapping.md` and `docs/activity_type_mapping.md` for the verification workflow and confirmed `IDCINNOSTI -> CINNOSTI` findings.

## Booking Write Mapping

Inspect the likely booking write path:

```powershell
C:\python\python.exe scripts\tests\inspect_booking_write_path.py
```

Find candidate test patients:

```powershell
C:\python\python.exe scripts\tests\find_test_patients.py
```

A test patient identified during PoC:

```text
IDPAC: 33411
Name: Test De
```

## Booking Insert Tests

Create local test defaults:

```cmd
copy config\booking_insert_test.local.example.json config\booking_insert_test.local.json
```

Rollback-only insert test:

```powershell
C:\python\python.exe scripts\tests\test_booking_insert_rollback.py
```

Commit-prompt insert test:

```powershell
C:\python\python.exe scripts\tests\test_booking_insert_commit_prompt.py
```

This commits only if this exact phrase is typed:

```text
COMMIT TEST APPOINTMENT
```

Controlled multi-activity insert test for verifying whether `OBJOBJ.IDCINNOSTI` propagates expected activity/color into Medicus UI:

```cmd
copy config\activity_insert_test.local.example.json config\activity_insert_test.local.json
```

```powershell
C:\python\python.exe scripts\tests\test_activity_insert_commit_prompt.py
```

This commits only if this exact phrase is typed:

```text
COMMIT ACTIVITY TEST APPOINTMENTS
```

Use booking write tests only during controlled client-approved UI verification.

## Current Status

- Phase 1 read-only availability pipeline is validated.
- Phase 2 weekly CLI runs on the Windows server and generates usable reports.
- Phase 3 committed `OBJOBJ` insert and `IDCINNOSTI` activity/color propagation are verified in Medicus UI.
- Local API + trycloudflare + n8n chat agent PoC is confirmed for fast read-only availability lookup against real DB data.
- `/patient-lookup` is implemented and smoke-tested by full `RODCIS` for test patient `IDPAC=33411`; phone lookup uses `KARKONTAKT`, but the test patient has no contact row.
- Dr. Bednar active `IDUZI` is confirmed as `4`; inactive duplicate `IDUZI=2` is excluded.
- ElevenLabs voice agent availability tool test is confirmed and very fast.
- Current priority: test both read-only tools in the agent flow, then replace the temporary trycloudflare URL with a stable named Cloudflare Tunnel.

## Detailed Context

See `PROJECT_CONTEXT.md` for detailed database findings, tested values, roadmap, open questions, file map, and Phase 3/API notes.

Most relevant API files:

```text
scripts/api_server.py
scripts/availability_search.py
scripts/appointment_write.py
scripts/start_trycloudflare_api.ps1
scripts/start_named_cloudflare_tunnel.ps1
config/api.local.example.json
docs/local_api.md
```
