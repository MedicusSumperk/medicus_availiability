# Medicus Availability Engine

## Goal

This project builds support scripts for an AI receptionist integration over the Medicus Firebird database.

Core availability formula:

```text
availability = theoretical schedule slots - occupied appointment slots
```

The broader product is an integration layer for an ElevenLabs AI receptionist. The agent should have two simple and reliable tools:

1. Check availability.
2. Book a patient appointment.

The project is still a PoC/mapping effort, but the write path has moved past rollback-only testing. A committed test appointment was successfully written to `OBJOBJ` and verified with the client in the Medicus UI.

## Current Status

- Phase 1 read-only availability pipeline is implemented and validated.
- Phase 2 weekly CLI runs on the Windows server and generates usable JSON, CSV, and Markdown reports.
- Phase 3 rollback-only `OBJOBJ` insert succeeded and rollback verification passed.
- Phase 3 committed test insert succeeded and the client confirmed that the appointment appeared in the expected place in the Medicus UI.
- Direct `INSERT INTO OBJOBJ` is now considered plausible for the AI booking path, but production booking still depends on confirmed appointment type mapping and business rules.
- The current highest-priority work is read-only verification of appointment types and bookable doctor selection for a given day.

## Product Scope V1

The first product version should support booking only:

- skin examination (`kozni vysetreni`)
- plasma (`plazma`)

The first version should not book:

- standalone dermatoscope appointments
- laser appointments
- prescriptions, blood/lab requests, or test results

Requests for prescriptions, blood/lab requests, and test results should be redirected to another phone number / live person. The exact phone number is not needed for the current database mechanism work.

## Appointment Types and UI Colors

Client notes indicate that the relevant appointment types are:

- skin examination - shown as black in Medicus UI
- dermatoscope - usually shown as blue in Medicus UI
- plasma - separate appointment type/service

Additional UI colors mentioned by the client:

- yellow - reservation/blocking slot, used so another employee does not fill a slot that should stay available for follow-up dermatoscope work; for database availability purposes this must count as an occupied slot
- red - likely a pre-planned regular check / dermatoscope-related appointment; must be confirmed in DB
- green - likely another regular check variant; must be confirmed in DB

Working assumption until DB verification: red and green should be treated as dermatoscope-blocking appointment types if they represent dermatoscope usage.

Open verification: confirm whether appointment type / UI color is stored in `OBJOBJ.TYP`, and map concrete values to skin examination, dermatoscope, plasma, yellow reservation, red, and green.

## V1 Skin Examination Booking Rule

A skin examination is booked as a single appointment row in the first 15-minute slot, but booking logic must reserve capacity for the follow-up dermatoscope slot.

For a skin examination slot to be offered:

1. The selected skin examination slot must be free for the selected doctor.
2. The immediately following slot for the same doctor must be free.
3. The immediately following slot must not overlap an existing dermatoscope appointment for any other doctor, because the clinic has only one dermatoscope.
4. The last available slot in a doctor's working block must not be offered for skin examination, because there is no room for the follow-up dermatoscope slot.
5. In V1, the follow-up dermatoscope slot is not written to the database automatically. It is only checked as required free capacity.

Example:

```text
08:00 skin examination can be offered only if:
- 08:00 is free for doctor A
- 08:15 is free for doctor A
- 08:15 is not occupied by dermatoscope usage for doctor B
```

Future phase: once dermatoscope appointment type is confirmed, consider automatically writing the follow-up dermatoscope/reservation row. This is intentionally out of scope for V1.

## V1 Dermatoscope Rule

The clinic usually has two doctors working in parallel, but only one dermatoscope device.

Rules:

- The AI receptionist should not book standalone dermatoscope appointments in V1.
- Dermatoscope is a shared constrained resource.
- Existing dermatoscope appointments block only their own time interval, based on `OBJOBJ.CAS` and `OBJOBJ.CASDO`.
- For skin examination booking, only the follow-up slot is checked against shared dermatoscope usage.
- Existing red/green appointments should be treated cautiously as dermatoscope blockers until the type mapping is confirmed.

## V1 Plasma Rule

Working assumption:

- Plasma is a one-slot appointment.
- Plasma does not require a follow-up dermatoscope slot.
- Plasma should be bookable only for doctors allowed by client rules.

Client note: plasma is likely handled by Dr. Bartonova and appears to be available year-round. This must still be confirmed before production booking.

## Doctor Availability and Booking Scope

Initial assumption was that each doctor has distinct appointment types. Client clarification changed this model: most doctors can perform most relevant services, subject to exceptions.

Working model:

- For a target day, the database can show one, two, three, or more doctors with schedules.
- The clinic commonly has two doctors working in parallel, but this is not an invariant.
- If only one allowed doctor has availability, the AI may book to that doctor normally.
- If more than two doctors appear, it is not automatically an error. Possible explanations include another location/context, a technical user, a Laser grouping/user, or doctors alternating during the day.
- If a doctor works only part of the day and another doctor replaces them later, both doctors should be considered bookable during their actual free schedule blocks.
- The AI should book to any allowed doctor with availability, unless later rules introduce a preference order.

Important: database schedule rows alone are not enough to decide who is AI-bookable. A future configuration layer is expected after current open questions are answered.

Expected future configuration could be JSON or a database table and should eventually cover:

- allowed doctors / excluded users
- appointment types each doctor may receive
- manual business exceptions
- seasonal rules
- service-specific constraints

Do not implement that configuration before the current DB questions are confirmed.

## Doctor/User Open Notes

These items must be investigated and recorded before final booking rules are implemented:

1. Query `UZIVATEL` to understand the fixed user/doctor table.
2. Confirm which users are real bookable doctors.
3. Confirm whether an `Admin` user exists, what its `IDUZI` is, and whether it ever has `OBSPRAC` schedule rows.
4. Investigate the apparent `Laser` grouping/user: whether it is an `UZIVATEL` row, has an `IDUZI`, has schedule rows, or is only an organizational UI concept.
5. Determine whether AI should ever book to the `Laser` user/group. Current assumption: probably not for V1.
6. Confirm whether doctors appearing in the schedule but not intended for AI booking are tied to another office/location/service.

## Manual Business Exceptions

Client rules currently live in receptionist knowledge, not in automatic Medicus constraints. Medicus does not necessarily enforce these rules for us.

Known business-rule notes from client discussion:

- Skin examination can be done by all relevant doctors.
- Dermatoscope can be done by all relevant doctors except Dr. Bednar.
- Dr. Bednar does not do dermatoscope.
- Dr. Bednar does laser services but does not do plasma.
- Dr. Bartonova does moles, fractional laser, and plasma.
- Plasma is likely Dr. Bartonova only and year-round.
- Skin examination booking appears relevant only through September; after October, some requests may be more laser-oriented.
- Some laser services are seasonal: likely only until April or at most mid-May, then not later due to season/sun exposure. Exact service scope must be confirmed.
- Laser booking is out of V1 scope.

These notes are not final production rules. They must be converted into explicit rules after DB verification and client confirmation.

## Main Database Objects

### UZIVATEL

Contains users/doctors.

Important columns:

- `IDUZI` - doctor/user ID
- `JMENO` - first name
- `PRIJMENI` - last name

Open investigation: query all relevant columns to identify real doctors, `Admin`, possible `Laser` user/group, and any active/inactive markers.

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

Important fields identified so far:

- `IDOBJ` - primary key, generated by trigger `OBJOBJ_BI` from `GEN_IDOBJ` when omitted/null
- `IDPAC` - patient ID, foreign key to patient card table
- `IDPRAC` - workplace/schedule ID, not null
- `IDUZI` - doctor/user ID
- `DATUM` - appointment date, not null
- `CAS` - appointment start time
- `CASDO` - appointment end time
- `DATUMDO` - appointment end date, usually same as `DATUM`
- `TYP` - appointment type; exact production values must be mapped
- `PRISEL` - attendance/status flag, recent rows commonly used `N`
- `INFO` - short text field, useful for test marker
- `DATZAPIS` - write date, recent rows used current date
- `CREATEDBY` - creator user ID, recent rows showed `10`
- `CREATED` / `CHANGED` - populated by triggers
- `CEKATEL` and `ES_RESYNC_NEEDED` defaulted to `F` in rollback test

`OBJOBJ` is the current candidate direct booking/write target. A committed test row has been verified in the Medicus UI, but appointment type mapping remains a blocker for production booking.

### SP_OBJ_KALENDAR

Stored procedure returning aggregated calendar capacity indicators, used only for validation. Exact free slots are generated explicitly from schedule blocks and appointments.

## Availability Pipeline

1. Load doctors from `UZIVATEL`.
2. Select one doctor or iterate through all doctors for weekly output.
3. Input target date or selected week.
4. Compute `DENTYD` from each date, where Monday=1 and Sunday=7.
5. Query active appointment-enabled `OBSPRAC` rows:

```sql
IDUZI = doctor_id
AND OBJED = 'A'
AND DENTYD = computed_dentyd
AND PLATIOD <= target_date
AND (PLATIDO >= target_date OR PLATIDO IS NULL)
```

6. Extract `IDPRAC` and `TYPTYD`.
7. Call `OBSDNE_PRAVODLIS_SEL(target_date, TYPTYD, DENTYD, IDPRAC)`.
8. Generate theoretical slots from `CAS`, `DOBA`, and `INTERVAL`.
9. Query `OBJOBJ` for matching `IDPRAC`, `IDUZI`, `DATUM`.
10. Mark a slot occupied when:

```text
slot_time >= appointment.CAS
AND slot_time < appointment.CASDO
```

11. Free slots are theoretical slots minus occupied slots.
12. Future context output must additionally evaluate service-specific bookability, not only raw free slots.

## Validated Availability Test Case

```text
IDUZI = 1
Date = 2026-04-10
DENTYD = 5
TYPTYD = 4
IDPRAC = 1
Schedule = 08:00-12:00 and 13:00-15:00, 15-minute interval
Theoretical slots = 24
Expected free slots = 0
```

This has been checked against direct schedule block inspection, `OBJOBJ` appointments, exact slot calculation, and `SP_OBJ_KALENDAR` aggregate validation.

## Project Structure

```text
config/
  booking_insert_test.local.example.json
  booking_insert_test.local.json        # local only, created manually from example
  db_config.local.json                  # local only
data/
  availability/
    .gitkeep
docs/
  phase3_rollback_insert_test.md
scripts/
  availability_engine.py
  check_availability_cli.py
  check_week_availability_cli.py
  db.py
  tests/
    find_test_patients.py
    inspect_booking_write_path.py
    test_booking_insert_rollback.py
    test_booking_insert_commit_prompt.py
    test_obsprac.py
    test_schedule_blocks.py
    test_appointments.py
    test_calendar_capacity.py
    compute_free_slots.py
```

## Run Commands

Single-day CLI:

```powershell
C:\python\python.exe scripts\check_availability_cli.py
```

Weekly CLI:

```powershell
C:\python\python.exe scripts\check_week_availability_cli.py
```

Weekly output files are written to `data/availability/`:

```text
availability_YYYY-Www.json
availability_YYYY-Www.csv
availability_YYYY-Www.md
```

Booking write-path inspection:

```powershell
C:\python\python.exe scripts\tests\inspect_booking_write_path.py
```

Find candidate test patients:

```powershell
C:\python\python.exe scripts\tests\find_test_patients.py
```

Rollback-only booking insert test:

```powershell
C:\python\python.exe scripts\tests\test_booking_insert_rollback.py
```

Commit-prompt booking insert test:

```powershell
C:\python\python.exe scripts\tests\test_booking_insert_commit_prompt.py
```

## Local Booking Test Config

Create local config from the example:

```cmd
copy config\booking_insert_test.local.example.json config\booking_insert_test.local.json
```

Example values used during Phase 3 testing:

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

Test patient identified:

```text
IDPAC: 33411
PRIJMENI: Test
JMENO: De
RODCIS: 5656565666
DATNAR: 1956-06-06
POJ: 111
```

## Phase 3 Results

### Booking Inspection

`inspect_booking_write_path.py` confirmed:

- `IDOBJ` is generated by trigger `OBJOBJ_BI` through `GEN_IDOBJ`.
- `CREATED` and `CHANGED` are populated by triggers.
- Insert/update/delete triggers call sync/log behavior such as `COS_NEEDCALSYNC` and `sp_log`.
- Direct `INSERT INTO OBJOBJ` appears plausible for initial tests.
- Recent rows showed a practical minimal pattern with `IDPAC`, `IDPRAC`, `DATUM`, `CAS`, `TYP`, `PRISEL`, `IDUZI`, `DATUMDO`, `CASDO`, `DATZAPIS`, `CREATEDBY`.

### Rollback Insert Test

Rollback-only insert succeeded on 2026-05-05.

Inserted inside transaction:

```text
IDOBJ: 138596
IDPAC: 33411
IDPRAC: 1
DATUM: 2027-01-01
CAS: 08:00:00
CASDO: 08:15:00
TYP: 1
PRISEL: N
INFO: AI_RECEPTION_TEST_ROLLBACK
IDUZI: 1
DATUMDO: 2027-01-01
DATZAPIS: 2026-05-05
CREATEDBY: 10
CREATED: 2026-05-05 19:57:20.449000
CHANGED: 2026-05-05 19:57:20.449000
GUID: None
CEKATEL: F
ES_RESYNC_NEEDED: F
```

Rollback verification confirmed that the inserted row was gone. No commit was performed.

Detailed note: `docs/phase3_rollback_insert_test.md`.

### Committed Insert and UI Verification

After the rollback test, a client-approved committed test row was created with the commit-prompt script. The client confirmed that the database write appeared in the expected place in the Medicus UI.

This confirms that a direct `OBJOBJ` insert can be visible in the operational UI. It does not yet confirm the correct production `TYP` values for each appointment type.

## Important Rules

- Keep availability diagnostics read-only unless explicitly running controlled booking tests.
- Always check slot conflicts before insert.
- Always filter `OBSPRAC` by valid date.
- Always handle `PLATIDO IS NULL` as open-ended validity.
- Always filter by `IDUZI`.
- Always require `OBJED = 'A'` for appointment-enabled schedule rows.
- Always compute `DENTYD` correctly from the date.
- Do not rely on `SP_OBJ_KALENDAR` for exact slot generation.
- Do not expose raw free slots to the agent as final bookability without applying service-specific rules.
- For skin examination, require an immediate free follow-up slot and no shared dermatoscope conflict in that follow-up slot.
- Do not book standalone dermatoscope appointments in V1.
- Do not book laser in V1.

## Open Verification Items

### Verify Appointment Type Mapping

Highest priority.

Questions:

- Is appointment type stored in `OBJOBJ.TYP`?
- Which `TYP` value corresponds to skin examination / black UI color?
- Which `TYP` value corresponds to dermatoscope / blue UI color?
- Which values correspond to red and green regular-check variants?
- Do red and green represent dermatoscope usage and therefore block the shared dermatoscope?
- Which `TYP` value corresponds to yellow reservation/blocking slot?
- Which `TYP` value corresponds to plasma?
- Are there additional fields besides `TYP` that affect UI color or appointment behavior?

Planned approach: build/read a read-only diagnostic for a specific day that lists appointments with `IDOBJ`, `IDUZI`, `IDPRAC`, `DATUM`, `CAS`, `CASDO`, `TYP`, `INFO`, and other relevant non-null fields so the rows can be compared to what the client sees in Medicus UI.

### Verify Bookable Doctors for a Day

Questions:

- Which `UZIVATEL` rows are real bookable doctors?
- Which rows are technical users such as `Admin`?
- What is the meaning of the apparent `Laser` user/group?
- Can scheduled doctors appear because they work elsewhere or in another context?
- How should `IDPRAC` / workplace influence AI booking scope?
- How should the system explain days with fewer or more than two scheduled doctors?

Planned approach: query `UZIVATEL` and day-level `OBSPRAC` rows, then compare with client expectations for known days.

### Verify Week Type Source (`TYPTYD`)

Current implementation derives `TYPTYD` from active `OBSPRAC` rows for the selected doctor/date/day-of-week and passes it into `OBSDNE_PRAVODLIS_SEL`.

This still needs deeper read-only verification before treating Phase 2 output as final client-facing truth. The key question is whether `OBSPRAC.TYPTYD` is always the correct week type for a concrete calendar date, or whether another database table/procedure defines the actual active week type for each date.

### Convert Manual Exceptions to Explicit Rules

Current exception notes are client/receptionist knowledge, not confirmed database rules.

Need to confirm and formalize:

- allowed doctors per service
- seasonal limits for skin examination and laser/plasma services
- whether plasma is truly Dr. Bartonova only
- exact Bednar/Bartonova service exceptions
- whether any service requires longer than 15 minutes
- whether any skin examination exception requires more than the standard 30-minute capacity check

## PoC Roadmap

### Phase 1: Read-only Availability Pipeline

Status: completed.

Validated the full read-only pipeline:

```text
UZIVATEL -> OBSPRAC -> OBSDNE_PRAVODLIS_SEL -> OBJOBJ
```

### Phase 2: Extended CLI

Status: in progress.

`check_week_availability_cli.py` checks all doctors for a selected Monday-Friday week and produces console, JSON, CSV, and Markdown output. It was pulled and tested on the Windows server over SSH, and report generation works.

Next Phase 2 work should extend from raw free slots toward service-specific bookable context for the agent.

### Phase 3: SQL Write Test

Status: committed test verified.

Rollback-only insert succeeded. Commit-prompt insert also succeeded and was verified in Medicus UI with the client.

Remaining Phase 3 blocker is not whether writes appear in UI, but which appointment type values and related fields must be used for production-safe booking.

### Phase 4: Agent Booking Context

Status: planned.

Implement a mechanism that gives the AI receptionist service-specific context, not only raw availability.

Expected output should eventually answer:

- which doctors are bookable on a target day
- which slots are raw-free
- which slots are bookable for skin examination
- which slots are bookable for plasma
- why a raw-free slot is not bookable for a specific service
- which DB `TYP` should be used if a booking is created

Do not implement production booking logic until appointment type mapping and bookable doctor rules are confirmed.
