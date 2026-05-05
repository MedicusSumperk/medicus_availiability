# Medicus Availability Engine

## Goal

This project computes exact free appointment slots for a selected doctor and date using the Medicus Firebird database.

Core formula:

```text
availability = theoretical schedule slots - occupied appointment slots
```

The verified core logic is read-only. Scripts query the database and print inspection or availability output; they do not write back to the database.

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

Used to mark generated theoretical slots as occupied.

### SP_OBJ_KALENDAR

Stored procedure returning aggregated calendar capacity indicators.

Important output columns:

- `DOP`
- `ODP`

Used for validation only. Exact free slots are generated explicitly from schedule blocks and appointments, not from this aggregate procedure.

## Availability Pipeline

1. Load doctors from `UZIVATEL`.
2. Select a doctor (`IDUZI`).
3. Input the target date.
4. Compute `DENTYD` from the target date, where Monday=1 and Sunday=7.
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
scripts/
  check_availability_cli.py
  db.py
  tests/
    test_obsprac.py
    test_schedule_blocks.py
    test_appointments.py
    test_calendar_capacity.py
    compute_free_slots.py
```

`check_availability_cli.py` is the main interactive CLI entry point.

`scripts/tests/` contains read-only validation and inspection scripts used to verify the database pipeline.

## Run the CLI

From the repository root:

```powershell
C:\python\python.exe scripts\check_availability_cli.py
```

The CLI lists doctors from `UZIVATEL`, prompts for a doctor number, prompts for a target date in `YYYY-MM-DD` format, and prints total, occupied, and free slot counts plus free slot times.

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

## Important Rules

- Keep scripts read-only against the database.
- Always filter `OBSPRAC` by valid date.
- Always handle `PLATIDO IS NULL` as open-ended validity.
- Always filter by `IDUZI`.
- Always require `OBJED = 'A'` for appointment-enabled schedule rows.
- Always compute `DENTYD` correctly from the date.
- Do not rely on `SP_OBJ_KALENDAR` for exact slot generation.
- Generate exact free slots explicitly from schedule blocks and appointments.

## PoC Roadmap

### Phase 1: Read-only Availability Pipeline

Status: completed.

Validated the full read-only pipeline for computing exact free appointment slots from Firebird:

```text
UZIVATEL -> OBSPRAC -> OBSDNE_PRAVODLIS_SEL -> OBJOBJ
```

`SP_OBJ_KALENDAR` is used as an aggregate validation reference.

### Phase 2: Extended CLI

Status: planned.

Build a more capable CLI around the verified availability engine. It should support practical testing flows, broader inputs, clearer output, and reusable functions for later API or automation layers.

### Phase 3: SQL Write Test

Status: planned.

Create a minimal controlled SQL write test to confirm that writing into the client database works, understand exactly which table and fields are affected, and verify that the written data is visible in the expected place on the client side.

## Current Status

The core scheduling logic is implemented and validated. The repository now separates the main interactive CLI from read-only validation scripts under `scripts/tests/`. Next planned work is Phase 2: an extended CLI for broader PoC testing.
