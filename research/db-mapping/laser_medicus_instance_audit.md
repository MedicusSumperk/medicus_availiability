# LASER Medicus Instance Audit

Date: 2026-07-31

## Finding

The production server has a separate LASER Medicus installation:

- Main Ordinace database: `C:/Medicus 3/data/MEDICUS.FDB`
- LASER database: `C:/Medicus 3 Laser/data/MEDICUS.FDB`
- LASER install also contains `MEDICUS_INST.FDB` and historical `.fbk` backups.

This confirms the client note that scan/LASER operations are likely managed in a
separate Medicus instance with its own users, patients, schedules, and activity
mapping.

Read-only diagnostic result:

- Core table counts:
  - `UZIVATEL`: 8
  - `OBSPRAC`: 91
  - `OBJOBJ`: 82195
  - `CINNOSTI`: 18
  - `KAR`: 30825
- First observed LASER users:
  - `IDUZI=1` Eva Bednarova
  - `IDUZI=2` Rostislav Bednar
  - `IDUZI=3` Spravce
  - `IDUZI=4` Petra Pospisilova
  - `IDUZI=5` Sken Foceni skeny
- First observed LASER activities:
  - `ID=1` Projevy znamenka/fibromy/pigment
  - `ID=5` Dodelky/kontroly
  - `ID=13` Dermatoskop potvrzeno
  - `ID=19` Frakcni laser

The LASER activity IDs differ from the main Ordinace assumptions and must not be
used interchangeably without explicit mapping.

## Runtime Status

The production backend does not depend on the LASER database in v1. Paid
dermatoscopy availability infers scan-room capacity from main Medicus
appointments with configured dermatoscopy/blocker `IDCINNOSTI` values.

Future integration can use `tools/diagnostics/audit_laser_medicus_db.py` to
inspect the LASER database read-only with the same Firebird credentials as the
main Medicus DB.

## Next Audit Questions

- Confirm LASER `UZIVATEL.IDUZI` mapping; it may differ from Ordinace.
- Confirm LASER `CINNOSTI` values and colors for scan-room reservations.
- Confirm whether scan-room schedules are represented in `OBSPRAC`/`OBJOBJ`.
- Decide whether future runtime should read LASER availability only, or also
  write generic scan-room reservations there.
