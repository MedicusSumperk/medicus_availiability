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

The JSON is intended for the agent. The Markdown is a quick human-readable check. Current V1 context includes service-specific options for skin examination and plasma, with skin follow-up dermatoscope checks and shared dermatoscope blockers.

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
- Current priority: generate compact pre-call context for the agent and refine business rules from real reception call mapping.

## Detailed Context

See `PROJECT_CONTEXT.md` for detailed database findings, tested values, roadmap, open questions, and Phase 3 notes.
