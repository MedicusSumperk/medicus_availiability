# Activity Type Mapping

## Status

Appointment color/type mapping is not driven by `OBJOBJ.TYP` in this database.

Confirmed findings:

- `OBJOBJ.TYP` is commonly `1` and does not distinguish skin / dermatoscope / plasma.
- `OBJOBJ.COLORID` was `NULL` across inspected days and rows.
- `OBJOBJ.TYPPROH` was `NULL` across inspected days and rows.
- `OBJOBJ.CREATEDBY` is a user reference (`UZIVATEL`), not an appointment type.
- `OBJOBJ_SEL` is only a wrapper over `OBJOBJ`; it does not calculate UI colors or service types.
- The useful service-type relation is `OBJOBJ.IDCINNOSTI -> CINNOSTI.ID`.

## OBJOBJ_SEL Behavior

`OBJOBJ_SEL` selects fields directly from `OBJOBJ` and returns them. It also expands recurring appointment rows:

- normal appointments: rows where `TYP NOT IN (9, 10)`
- recurring every day in date range: `TYP = 9`
- recurring same weekday in date range: `TYP = 10`

It returns `COLORID`, `TYPPROH`, and `REZERVACE`, but those values are passed through from `OBJOBJ`. Since `COLORID` and `TYPPROH` are null in inspected data, they are not the current source of appointment color/type.

## CINNOSTI Relation

The relevant dictionary table is `CINNOSTI`.

Observed columns:

| Column | Meaning |
| --- | --- |
| `ID` | activity identifier referenced by `OBJOBJ.IDCINNOSTI` |
| `NAZEV` | activity name |
| `BARVA` | UI color value, likely Windows/Delphi `TColor` style integer |
| `INTERVAL` | activity interval, empty in inspected rows |
| `VOLNO` | free-state color/text marker, meaning still to confirm |
| `OBSAZENO` | occupied-state color/text marker, meaning still to confirm |
| `IDPRAC` | workplace/schedule relation, empty in inspected rows |
| `WEB` | web visibility flag |
| `CREATED` | created timestamp |
| `CHANGED` | changed timestamp |

Tables containing `IDCINNOSTI`:

- `CLICKDOC_CINNOSTI`
- `ES_APP`
- `ES_APPUPD`
- `OBJHIST`
- `OBJOBJ`
- `OBSODLIS`
- `OBSODLIS_CINNOST`
- `OBSPRAC`
- `OBSPRAC_CINNOST`
- `OBSSABLDOBA`
- `OBSSABLDOBA_CINNOST`

Tables containing activity-like naming:

- `CINNOSTI`
- `CINNOSTI_DETAIL`
- `CLICKDOC_CINNOSTI`
- `OBSODLIS_CINNOST`
- `OBSPRAC_CINNOST`
- `OBSSABLDOBA_CINNOST`
- `OSE_CINNOSTI`

## Observed CINNOSTI Values

```text
ID | NAZEV                   | BARVA    | VOLNO   | OBSAZENO | WEB
1  | Sken znamenek c. 1      | 4344044  | 4254956 | 4344044  | F
2  | kontrola po skenu       | 65408    |         |          | F
3  | laser vykony            | 16711935 |         |          | F
5  | Sken znamenek 2 a vyssi | 16711680 |         |          | F
6  | rezervace dermatoskop   | 65535    |         |          | F
```

Notes:

- The `BARVA` values appear to correspond to Medicus UI colors.
- These are likely stored as Windows/Delphi `TColor` integers rather than web `#RRGGBB` values.
- Example: `16711680` is often blue in BGR/TColor interpretation, even though it would be red in web RGB notation.
- `65535` corresponds to yellow in Windows/Delphi color interpretation, matching the client note for dermatoscope reservation.

## Observed Appointment Summary

For one inspected day:

```text
IDCINNOSTI | NAZEV                   | POCET | PRVNI_CAS | POSLEDNI_CAS
NULL       |                         | 29    | 07:00:00  | 17:15:00
1          | Sken znamenek c. 1      | 3     | 09:45:00  | 15:45:00
2          | kontrola po skenu       | 10    | 08:30:00  | 16:30:00
5          | Sken znamenek 2 a vyssi | 4     | 10:45:00  | 15:15:00
```

Working interpretation:

| DB condition | Working meaning | Booking impact |
| --- | --- | --- |
| `IDCINNOSTI IS NULL` | normal skin appointment / default appointment | likely skin examination candidate; requires follow-up dermatoscope capacity for V1 skin booking |
| `IDCINNOSTI = 1` | first mole scan / dermatoscope | blocks shared dermatoscope |
| `IDCINNOSTI = 2` | post-scan check | blocks shared dermatoscope unless client says otherwise |
| `IDCINNOSTI = 5` | repeated / higher-number mole scan | blocks shared dermatoscope |
| `IDCINNOSTI = 6` | dermatoscope reservation | blocks shared dermatoscope |
| `IDCINNOSTI = 3` | laser services bucket | contains plasma examples but also broader laser services |

## Plasma Finding

A search for plasma in `OBJOBJ.INFO` found rows like:

```text
IDOBJ  | DATUM      | CAS      | CASDO    | IDUZI | IDPRAC | IDCINNOSTI | NAZEV        | INFO
132752 | 2026-05-20 | 10:00:00 | 10:30:00 | 8     | 1      | 3          | laser vykony | plazma   luc
132950 | 2026-05-25 | 13:00:00 | 13:30:00 | 8     | 1      | 3          | laser vykony | plazma   luc
```

Working interpretation:

- Plasma is stored under `IDCINNOSTI = 3` (`laser vykony`).
- Plasma appears to be distinguished by `INFO` containing text like `plazma`.
- Existing plasma examples are 30 minutes long.
- It is not yet confirmed whether plasma should always be 30 minutes.
- It is not yet confirmed what exact `INFO` text should be written for production. Existing rows contain `plazma   luc`.

## V1 Booking Implications

### Skin Examination

Likely DB write shape:

- `TYP = 1`
- `IDCINNOSTI = NULL`
- standard appointment row fields as already tested in committed insert

Availability rules still apply:

- selected skin slot must be free
- immediate follow-up slot for the same doctor must be free
- follow-up slot must not overlap shared dermatoscope usage by another doctor
- last available slot in a doctor block must not be offered for skin examination

### Dermatoscope Blockers

For shared dermatoscope capacity, treat these as blockers unless client later narrows the list:

```text
IDCINNOSTI IN (1, 2, 5, 6)
```

Use `CAS` / `CASDO` for actual blocker intervals.

### Plasma

Likely DB write shape:

- `TYP = 1`
- `IDCINNOSTI = 3`
- `INFO` contains a plasma marker, exact production text still to confirm
- likely 30-minute duration, still to confirm

## Open Questions

Need client or controlled UI verification:

1. Does writing `IDCINNOSTI` propagate the expected color/activity into the Medicus calendar UI?
2. Which `IDCINNOSTI` value should be written for each controlled test type?
3. Should skin examination use `IDCINNOSTI = NULL`, or is there another activity/client workflow for skin appointments?
4. Does `IDCINNOSTI = 2` always block dermatoscope capacity, or is it a different follow-up type?
5. Should plasma always use `IDCINNOSTI = 3`?
6. Should plasma always be 30 minutes?
7. What exact `INFO` text should be written for plasma?
8. Are `VOLNO` and `OBSAZENO` meaningful for agent logic, or only UI coloring/configuration?

## Proposed Controlled Commit Test

To answer whether committed rows can propagate color/activity into the Medicus calendar, run a controlled commit-prompt test that inserts several clearly marked appointments under one approved test patient and doctor/workplace/date.

Suggested variants:

| Label | `IDCINNOSTI` | Expected UI meaning |
| --- | --- | --- |
| `skin_default` | `NULL` | default / skin appointment |
| `derm_scan_1` | `1` | first mole scan |
| `derm_followup` | `2` | post-scan check |
| `laser_plasma` | `3` | laser/plasma bucket |
| `derm_scan_repeat` | `5` | repeated mole scan |
| `derm_reservation` | `6` | dermatoscope reservation |

Important safety rules:

- Use only client-approved test data.
- Use future test slots that are verified free.
- Use obvious `INFO` markers.
- Require an explicit commit phrase before committing.
- Print all inserted `IDOBJ` values for later UI verification and cleanup.
