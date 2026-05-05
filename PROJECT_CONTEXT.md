# Medicus Availability Engine

## Goal

This project computes exact free appointment slots for a selected doctor and date using the Medicus Firebird database.

Core formula:

```text
availability = theoretical schedule slots - occupied appointment slots
```

The verified core logic is read-only. Scripts query the database and print inspection or availability output; they do not write back to the database.

## Product Context

The broader project is an integration layer for an AI receptionist. The client wants an ElevenLabs voice agent that can answer patient calls, reason over current appointment availability, and eventually book patients into the Medicus system.

The agent should have two simple, reliable tools:

1. Check availability.
2. Book a patient appointment.

The availability tool should provide fresh context for the agent before or during a call. If the requested appointment date/time is outside the cached context window, the agent should call the availability tool again and verify current availability.

The booking tool should write an appointment to the database only after the write path is mapped, tested, and confirmed with the client.

A supporting procedure/reason dictionary will be needed so the agent can map patient intent to required appointment duration. Example concept:

```json
{
  "kontrola": {
    "duration_minutes": 15,
    "required_slots": 1
  },
  "vstupni_vysetreni": {
    "duration_minutes": 30,
    "required_slots": 2
  }
}
```

The script should calculate whether a doctor has enough consecutive free slots for the requested procedure. The agent should not have to infer this from raw slot lists.

## Main Database Objects

### UZIVATEL

Contains users/doctors.

Important columns:

- `IDUZI` - doctor/user ID
- `JMENO` - first name
- `PRIJMENI` - last name

Used by the CLI to list and select doctors.

### OBSPRAC

Contains scheduling rules.

Important columns:

- `IDUZI` - doctor/user ID
- `IDPRAC` - workplace/schedule ID
- `TYPTYD` - week type
- `DENTYD` - day of week, Monday=1 through Sunday=7
- `CAS` - block start time
- `DOBA` - block duration in minutes
- `INTERVAL` - appointment slot size in minutes
- `PLATIOD` - valid from date
- `PLATIDO` - valid to date, nullable/open-ended
- `OBJED` - `A` means appointment-enabled

Only rows valid for the target date are considered:

```sql
PLATIOD <= target_date
AND (PLATIDO >= target_date OR PLATIDO IS NULL)
```

### OBSDNE_PRAVODLIS_SEL

Stored procedure returning daily schedule blocks for a date, week type, day of week, and workplace.

Called with:

```text
(target_date, TYPTYD, DENTYD, IDPRAC)
```

Used to generate theoretical appointment slots from `CAS`, `DOBA`, and `INTERVAL`.

### OBJOBJ

Contains real appointments.

Important columns:

- `IDPRAC` - workplace/schedule ID
- `IDUZI` - doctor/user ID
- `DATUM` - appointment date
- `CAS` - appointment start time
- `CASDO` - appointment end time

Used to mark generated theoretical slots as occupied. This is also a likely booking/write target, but Phase 3 must verify the correct write path, required fields, defaults, generated IDs, and UI visibility before any production booking script is created.

### SP_OBJ_KALENDAR

Stored procedure returning aggregated calendar capacity indicators.

Important output columns:

- `DOP`
- `ODP`

Used for validation only. Exact free slots are generated explicitly from schedule blocks and appointments, not from this aggregate procedure.

## Availability Pipeline

1. Load doctors from `UZIVATEL`.
2. Select a doctor (`IDUZI`) or iterate through all doctors for the weekly CLI.
3. Input the target date or selected week.
4. Compute `DENTYD` from each target date, where Monday=1 and Sunday=7.
5. Query `OBSPRAC` for active appointment-enabled schedule rows:

```sql
IDUZI = doctor_id
AND OBJED = 'A'
AND DENTYD = computed_dentyd
AND PLATIOD <= target_date
AND (PLATIDO >= target_date OR PLATIDO IS NULL)
```

6. Extract the schedule context, especially `IDPRAC` and `TYPTYD`.
7. Call `OBSDNE_PRAVODLIS_SEL(target_date, TYPTYD, DENTYD, IDPRAC)`.
8. Generate theoretical slots for each returned block:

```text
start at CAS
repeat every INTERVAL minutes
stop before CAS + DOBA
```

9. Query `OBJOBJ` for appointments matching `IDPRAC`, `IDUZI`, and `DATUM`.
10. Mark a generated slot as occupied when:

```text
slot_time >= appointment.CAS
AND slot_time < appointment.CASDO
```

11. Return free slots as theoretical slots minus occupied slots.

## Validated Test Case

Doctor:

```text
IDUZI = 1
```

Date:

```text
2026-04-10
```

Derived context:

```text
DENTYD = 5
TYPTYD = 4
IDPRAC = 1
```

Schedule:

```text
08:00-12:00, 240 minutes, interval 15
13:00-15:00, 120 minutes, interval 15
```

Expected result:

```text
Theoretical slots: 24
Expected free slots: 0
```

This has been checked against direct schedule block inspection, `OBJOBJ` appointments, exact slot calculation, and `SP_OBJ_KALENDAR` aggregate validation.

## Project Structure

```text
data/
  availability/
    .gitkeep
scripts/
  availability_engine.py
  check_availability_cli.py
  check_week_availability_cli.py
  db.py
  tests/
    inspect_booking_write_path.py
    test_obsprac.py
    test_schedule_blocks.py
    test_appointments.py
    test_calendar_capacity.py
    compute_free_slots.py
```

`availability_engine.py` contains reusable read-only calculation helpers.

`check_availability_cli.py` is the original interactive single-doctor/single-day CLI entry point.

`check_week_availability_cli.py` is the Phase 2 weekly CLI. It checks Monday-Friday availability for all doctors and writes JSON, CSV, and Markdown output files.

`scripts/tests/` contains read-only validation and inspection scripts used to verify the database pipeline.

## Run the Single-Day CLI

From the repository root:

```powershell
C:\python\python.exe scripts\check_availability_cli.py
```

The CLI lists doctors from `UZIVATEL`, prompts for a doctor number, prompts for a target date in `YYYY-MM-DD` format, and prints total, occupied, and free slot counts plus free slot times.

## Run the Weekly CLI

From the repository root:

```powershell
C:\python\python.exe scripts\check_week_availability_cli.py
```

The weekly CLI prompts for one of these options:

- current Monday-Friday week
- next Monday-Friday week
- following Monday-Friday week
- custom date, using the Monday-Friday week containing that date

It computes availability for all doctors and includes doctors even when they have no free slots or no schedule for a day.

Output files are written to `data/availability/`:

```text
availability_YYYY-Www.json
availability_YYYY-Www.csv
availability_YYYY-Www.md
```

The Markdown report is intended as the easiest output to show to a client. JSON is for downstream automation/API use, and CSV is for spreadsheet review.

## Run Validation Scripts

Run all validation scripts from the repository root so their imports resolve consistently:

```powershell
C:\python\python.exe scripts\tests\test_obsprac.py
C:\python\python.exe scripts\tests\test_schedule_blocks.py
C:\python\python.exe scripts\tests\test_appointments.py
C:\python\python.exe scripts\tests\test_calendar_capacity.py
C:\python\python.exe scripts\tests\compute_free_slots.py
```

Each validation script adds the parent `scripts` directory to `sys.path`, then imports `db.py` from `scripts/db.py`.

## Run Phase 3 Booking Inspection

From the repository root:

```powershell
C:\python\python.exe scripts\tests\inspect_booking_write_path.py
```

This script is read-only. It inspects `OBJOBJ` columns, constraints, indexes, triggers, likely generators/sequences, and potentially related procedures. At the end it asks whether to print recent `OBJOBJ` rows; answer `YES` only when patient-data exposure is acceptable for the current debugging session.

## Important Rules

- Keep database interactions read-only until Phase 3.
- Phase 3 write tests should start inside a database transaction and use rollback by default.
- Do not commit any test appointment until the target table/procedure, fields, and UI visibility are confirmed with the client.
- Always filter `OBSPRAC` by valid date.
- Always handle `PLATIDO IS NULL` as open-ended validity.
- Always filter by `IDUZI`.
- Always require `OBJED = 'A'` for appointment-enabled schedule rows.
- Always compute `DENTYD` correctly from the date.
- Do not rely on `SP_OBJ_KALENDAR` for exact slot generation.
- Generate exact free slots explicitly from schedule blocks and appointments.

## Open Verification Items

### Verify Week Type Source (`TYPTYD`)

Current implementation derives `TYPTYD` from active `OBSPRAC` rows for the selected doctor/date/day-of-week and passes it into `OBSDNE_PRAVODLIS_SEL`.

This needs deeper read-only verification before treating Phase 2 output as final client-facing truth. The key question is whether `OBSPRAC.TYPTYD` is always the correct week type for a concrete calendar date, or whether another database table/procedure defines the actual active week type for each date.

Suggested verification path:

1. Search the database schema for tables/procedures containing week type/calendar mapping data.
2. Compare that source with `OBSPRAC.TYPTYD` across several consecutive weeks.
3. Test at least one doctor with known alternating week schedules, if available.
4. Update `availability_engine.py` if a separate source of truth for calendar week type is found.

### Map Booking Write Path

Before creating a production booking script, Phase 3 must determine how Medicus expects appointments to be written.

Open questions:

- Is direct `INSERT` into `OBJOBJ` sufficient, or should booking use a stored procedure?
- Which fields are required beyond `IDPRAC`, `IDUZI`, `DATUM`, `CAS`, and `CASDO`?
- How are appointment IDs generated?
- Which patient identifier fields are required?
- Which appointment type/status/source fields are required for the appointment to appear correctly in the Medicus UI?
- Is there a safe way to mark test records, such as a note value like `AI_RECEPTION_TEST`?
- Is there a supported cancellation/delete path for test cleanup?

## Phase 3 Write-Test Approach

Firebird writes are transactional. A Phase 3 script can open a connection, start or use a transaction, perform a test write, query the same transaction to inspect the inserted data, and then call `rollback()` so the database is not permanently changed.

Initial write-test script should be deliberately conservative:

1. Inspect `OBJOBJ` metadata and nearby real appointment rows.
2. Identify required/non-null columns and likely defaults.
3. Build a candidate test insert using a clearly recognizable marker such as `AI_RECEPTION_TEST`.
4. Run the insert inside a transaction.
5. Query the inserted row back in the same session.
6. Roll back by default.
7. Only after client confirmation, optionally run a controlled commit test for one known safe appointment slot.

This phase is for mapping and confidence building with the client. Production booking behavior comes later, after Phase 2 availability and Phase 3 write behavior are confirmed.

## PoC Roadmap

### Phase 1: Read-only Availability Pipeline

Status: completed.

Validated the full read-only pipeline for computing exact free appointment slots from Firebird:

```text
UZIVATEL -> OBSPRAC -> OBSDNE_PRAVODLIS_SEL -> OBJOBJ
```

`SP_OBJ_KALENDAR` is used as an aggregate validation reference.

### Phase 2: Extended CLI

Status: in progress.

Build a more capable CLI around the verified availability engine. The first implementation is `scripts/check_week_availability_cli.py`, which checks all doctors for a selected Monday-Friday week and produces console, JSON, CSV, and Markdown output.

Test status:

- Pulled and tested on the Windows server over SSH.
- Weekly CLI runs successfully.
- Console output is visible.
- Report generation works and creates files under `data/availability/`.
- Generated Markdown/CSV files can be opened or transferred from the server for review.

### Phase 3: SQL Write Test

Status: planned.

Create a minimal controlled SQL write test to confirm that writing into the client database works, understand exactly which table and fields are affected, and verify that the written data is visible in the expected place on the client side.

The first implementation should default to rollback. A committed test should happen only after the write path and test data are explicitly agreed with the client.

First mapping script:

```powershell
C:\python\python.exe scripts\tests\inspect_booking_write_path.py
```

## Current Status

The core scheduling logic is implemented and validated. Phase 2 weekly CLI was tested on the Windows server and generates usable report files while keeping database operations read-only. The main remaining Phase 2 validation item is confirming the correct source of truth for `TYPTYD`; the next major workstream is Phase 3 mapping of safe appointment writes.
