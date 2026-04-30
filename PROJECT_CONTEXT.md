PROJECT CONTEXT: MEDICUS AVAILABILITY ENGINE

Goal:
Compute exact free appointment slots for a doctor and date using Firebird database.

Core Principle:
Availability = theoretical slots (schedule) minus occupied slots (appointments)

---

DATABASE STRUCTURE

1. UZIVATEL
- Contains users/doctors
- Key column: IDUZI
- Used for doctor selection

2. OBSPRAC
- Contains scheduling rules
- Key columns:
  IDUZI (doctor)
  IDPRAC (workplace)
  TYPTYD (week type)
  DENTYD (day of week)
  CAS (start time)
  DOBA (duration in minutes)
  INTERVAL (slot size in minutes)
  PLATIOD (valid from)
  PLATIDO (valid to, can be NULL)
  OBJED = 'A' means appointment-enabled

- Important:
  Only rows valid for target date must be used:
    PLATIOD <= target_date
    AND (PLATIDO >= target_date OR PLATIDO IS NULL)

3. OBSDNE_PRAVODLIS_SEL
- Stored procedure
- Returns daily scheduling blocks for given:
  date, TYPTYD, DENTYD, IDPRAC

- Returns:
  CAS (start time)
  DOBA (duration)
  INTERVAL (slot size)
  IDUZI (doctor)

- Used to generate theoretical slots

4. OBJOBJ
- Contains real appointments
- Key columns:
  IDPRAC
  IDUZI
  DATUM
  CAS (start)
  CASDO (end)

- Used to mark occupied slots

5. SP_OBJ_KALENDAR
- Aggregated availability
- Returns:
  DOP (free capacity)
  ODP (occupied capacity)

- Used only for validation, not for slot generation

---

AVAILABILITY PIPELINE

Step 1:
Select doctor from UZIVATEL

Step 2:
Input target date

Step 3:
Compute DENTYD from date:
  Monday = 1 ... Sunday = 7

Step 4:
Query OBSPRAC:
  filter:
    IDUZI = doctor
    OBJED = 'A'
    DENTYD = computed DENTYD
    PLATIOD <= target_date
    AND (PLATIDO >= target_date OR PLATIDO IS NULL)

Step 5:
Extract:
  IDPRAC
  TYPTYD

Step 6:
Call OBSDNE_PRAVODLIS_SEL:
  (target_date, TYPTYD, DENTYD, IDPRAC)

Step 7:
Generate theoretical slots:
  for each block:
    start at CAS
    repeat every INTERVAL minutes
    until CAS + DOBA

Step 8:
Query OBJOBJ:
  IDPRAC = IDPRAC
  IDUZI = doctor
  DATUM = target_date

Step 9:
Mark occupied slots:
  slot is occupied if:
    slot_time >= CAS
    AND slot_time < CASDO

Step 10:
Free slots = theoretical slots - occupied slots

---

VALIDATED TEST CASE

Doctor:
  IDUZI = 1

Date:
  2026-04-10

Derived:
  DENTYD = 5
  TYPTYD = 4
  IDPRAC = 1

Schedule:
  08:00–12:00 (240 min, interval 15)
  13:00–15:00 (120 min, interval 15)

Theoretical slots:
  24

Appointments:
  24

Expected free slots:
  0

SP_OBJ_KALENDAR:
  DOP = 0
  ODP = 0

---

IMPORTANT RULES

- Always filter OBSPRAC by valid date
- Always compute DENTYD correctly
- Always handle PLATIDO = NULL as open-ended
- Always filter by IDUZI
- Always use OBJED = 'A'
- Do not rely on SP_OBJ_KALENDAR for slot generation
- Always compute slots explicitly

---

OUTPUT EXPECTATION

Function:
  get_free_slots(doctor_id, date)

Returns:
  list of time strings:
    ["08:00", "08:15", ...]

If none:
  return empty list

---

STATUS

Core scheduling logic is fully implemented and validated.
Next step: build user-facing interface (CLI / API / automation).
