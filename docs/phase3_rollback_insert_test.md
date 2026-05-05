# Phase 3 Rollback Insert Test

Date: 2026-05-05

## Status

Successful rollback-only insert test against `OBJOBJ`.

## Test Data

```text
IDPAC: 33411
IDPRAC: 1
IDUZI: 1
DATUM: 2027-01-01
CAS: 08:00:00
CASDO: 08:15:00
TYP: 1
PRISEL: N
INFO: AI_RECEPTION_TEST_ROLLBACK
DATUMDO: 2027-01-01
DATZAPIS: 2026-05-05
CREATEDBY: 10
```

## Observed Result

The insert succeeded inside the active transaction and returned:

```text
IDOBJ: 138596
```

The inserted row was readable in the same transaction.

Triggers/defaults populated:

```text
CREATED: 2026-05-05 19:57:20.449000
CHANGED: 2026-05-05 19:57:20.449000
CEKATEL: F
ES_RESYNC_NEEDED: F
```

`GUID` remained `NULL`.

## Rollback Verification

The script called `rollback()` after reading the row back. Follow-up verification confirmed that the inserted row was gone.

```text
Rollback verification: inserted row is gone.
Done. No commit was performed.
```

## Conclusion

The database accepts a minimal direct `INSERT` into `OBJOBJ` with the tested fields, `IDOBJ` generation works, relevant timestamp/default triggers fire, and rollback behavior is confirmed.

Next step is a client-approved committed test appointment to verify visibility in the Medicus UI.
