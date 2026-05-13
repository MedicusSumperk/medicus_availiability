# Appointment Type Mapping Workflow

## Goal

Map Medicus UI appointment colors/types to database values before production booking logic uses `OBJOBJ.TYP`.

This is the current highest-priority verification item because booking must write the correct appointment type for:

- skin examination
- dermatoscope
- plasma

## Read-only Diagnostic

Run from the repository root on the Windows server:

```powershell
C:\python\python.exe scripts\tests\inspect_appointment_types.py
```

Enter a target date that the client can also inspect in the Medicus UI.

Choose a date that ideally contains examples of:

- black skin examination
- blue dermatoscope
- red regular check / possible dermatoscope variant
- green regular check / possible dermatoscope variant
- yellow reservation / blocking slot
- plasma

The script prints:

- appointment rows for the selected date
- `OBJOBJ.TYP` summary
- durations from `CAS` to `CASDO`
- doctor names from `UZIVATEL`
- non-empty inspected fields
- candidate lookup tables/procedures whose names may contain appointment type metadata

No database writes are performed.

## What to Compare in Medicus UI

For each visible appointment type/color in the Medicus UI, identify the matching row in the script output using:

- doctor
- time (`CAS` / `CASDO`)
- date
- patient or visible appointment text if safe to use
- appointment duration

Then record the mapping:

| UI meaning | UI color | DB field | DB value | Blocks dermatoscope? | Notes |
| --- | --- | --- | --- | --- | --- |
| Skin examination | black | `OBJOBJ.TYP`? | TBD | No, but requires follow-up slot | TBD |
| Dermatoscope | blue | `OBJOBJ.TYP`? | TBD | Yes | TBD |
| Regular check | red | `OBJOBJ.TYP`? | TBD | TBD, likely yes | TBD |
| Regular check | green | `OBJOBJ.TYP`? | TBD | TBD, likely yes | TBD |
| Reservation | yellow | `OBJOBJ.TYP`? | TBD | If reserving dermatoscope capacity, yes | TBD |
| Plasma | TBD | `OBJOBJ.TYP`? | TBD | No | TBD |

## V1 Booking Implications

V1 should book only:

- skin examination
- plasma

V1 should not book standalone dermatoscope appointments.

However, skin examination bookability depends on dermatoscope capacity:

- skin slot must be free
- immediately following slot for the same doctor must be free
- immediately following slot must not overlap dermatoscope use by another doctor

Therefore the mapping must identify all appointment types that block dermatoscope usage, including possible red/green variants.

## Open Questions

- Is `OBJOBJ.TYP` the only field controlling UI color/type?
- Which `TYP` value should be used when writing a skin examination booking?
- Which `TYP` value should be used when writing a plasma booking?
- Which existing appointment types should block shared dermatoscope capacity?
- Does yellow reservation always mean an occupied slot for our availability logic?
- Is there a type lookup table in the database that gives names/descriptions for `TYP` values?
