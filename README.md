# Medicus Availability Tools

Support scripts for a Medicus / Firebird PoC that will back an AI receptionist integration.

The target agent needs two reliable tools:

1. Check doctor availability.
2. Book a patient appointment.

Current work is still PoC/mapping. Availability scripts are read-only. Booking scripts are Phase 3 test utilities and should be used only with client-approved test data.

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

The Markdown report is the easiest output to show to a client. JSON is for downstream automation/API work, and CSV is for spreadsheet review.

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

Example config:

```json
{
  "idpac": 33411,
  "idprac": 1,
  "iduzi": 1,
  "date": "2027-01-01",
  "start_time": "08:00",
  "duration_minutes": 15,
  "typ": 1,
  "created_by": 10
}
```

Rollback-only insert test:

```powershell
C:\python\python.exe scripts\tests\test_booking_insert_rollback.py
```

This inserts `INFO = AI_RECEPTION_TEST_ROLLBACK`, reads the row back inside the transaction, then always rolls back.

Commit-prompt insert test:

```powershell
C:\python\python.exe scripts\tests\test_booking_insert_commit_prompt.py
```

This inserts `INFO = AI_RECEPTION_TEST_COMMIT`, reads the row back, then commits only if this exact phrase is typed:

```text
COMMIT TEST APPOINTMENT
```

Any other input rolls back.

## Current Status

- Phase 1 read-only availability pipeline is validated.
- Phase 2 weekly CLI runs on the Windows server and generates usable reports.
- Phase 3 rollback-only `OBJOBJ` insert succeeded and rollback verification passed.
- Next checkpoint: client-approved committed test row and verification in Medicus UI.

## Detailed Context

See `PROJECT_CONTEXT.md` for detailed database findings, tested values, roadmap, open questions, and Phase 3 notes.
