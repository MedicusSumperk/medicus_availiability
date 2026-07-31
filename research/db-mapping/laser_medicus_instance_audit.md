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
