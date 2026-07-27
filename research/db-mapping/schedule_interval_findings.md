# Schedule Interval Findings

Last updated: 2026-07-23

Source of truth for this note: read-only DB diagnostics on the server
`medicus`, repo path `C:\db_bridge\medicus_availiability`.

## Why This Matters

Agent booking logic cannot assume a global 15-minute appointment grid. Medicus schedule blocks expose their own `INTERVAL` through `OBSDNE_PRAVODLIS_SEL`, and the same clinic week can contain both 10-minute and 15-minute doctor contexts.

The agent context therefore treats slot interval as a property of the concrete doctor/date/context, not as a doctor-hardcoded exception.

## Confirmed Server Audit, 2026-06-19

Read-only diagnostic scope:

- Server: `medicus`
- Repo: `C:\db_bridge\medicus_availiability`
- Python: `C:\python\python.exe`
- Data source: live Medicus DB through existing project scripts
- Date range: `2026-07-06` plus 84 days
- Excluded from bookable doctor conclusions in the original 2026-06-19 audit:
  - `IDUZI=2` Rostislav Bednar, then suspected old/inactive duplicate in local config
  - `IDUZI=3` Spravce, technical account
  - `IDUZI=6` Recepce, technical account
  - `IDUZI=7` Laser, technical/non-standard account for current agent flow

Doctor list returned by `scripts/load_doctors.py`:

```text
1  | Tereza Perez
2  | Rostislav Bednar
3  | Spravce
4  | Rostislav Bednar
6  | Recepce
7  | Laser
8  | Maria Bartonova
10 | Petra Pospislova
11 | Dusana Selecka
12 | Marta Skolarova
13 | Zuzana Slosarova
15 | Filip Ferencz
```

Relevant active doctors with schedule contexts in the inspected 84-day range:

```json
[
  { "doctor_id": 1, "doctor_name": "Tereza Perez", "slot_minutes": 15 },
  { "doctor_id": 8, "doctor_name": "Maria Bartonova", "slot_minutes": 10 },
  { "doctor_id": 11, "doctor_name": "Dusana Selecka", "slot_minutes": 10 },
  { "doctor_id": 12, "doctor_name": "Marta Skolarova", "slot_minutes": 10 },
  { "doctor_id": 13, "doctor_name": "Zuzana Slosarova", "slot_minutes": "mixed: 15 Mon/Tue, 10 Thu" },
  { "doctor_id": 15, "doctor_name": "Filip Ferencz", "slot_minutes": 15 }
]
```

Existing doctor/user IDs without schedule contexts in the inspected range:

```json
[
  {
    "doctor_id": 4,
    "doctor_name": "Rostislav Bednar",
    "schedule_contexts_from_2026_07_06": "none found in 84, 180, or 365 days"
  },
  {
    "doctor_id": 10,
    "doctor_name": "Petra Pospislova",
    "schedule_contexts_from_2026_07_06": "none found in 84, 180, or 365 days"
  }
]
```

Explicit ID check:

```json
[
  { "doctor_id": 4, "doctor_name": "Rostislav Bednar", "uzivatel_record": "exists" },
  { "doctor_id": 5, "doctor_name": null, "uzivatel_record": "not found" },
  { "doctor_id": 10, "doctor_name": "Petra Pospislova", "uzivatel_record": "exists" }
]
```

Detailed weekday pattern:

```text
doctor_id | doctor            | weekday   | interval_min | days | first_date | last_date  | first_start
1         | Tereza Perez      | Wednesday | 15           | 12   | 2026-07-08 | 2026-09-23 | 15:00
8         | Maria Bartonova   | Monday    | 10           | 12   | 2026-07-06 | 2026-09-21 | 08:30
8         | Maria Bartonova   | Tuesday   | 10           | 12   | 2026-07-07 | 2026-09-22 | 08:30
8         | Maria Bartonova   | Wednesday | 10           | 12   | 2026-07-08 | 2026-09-23 | 08:30
11        | Dusana Selecka    | Thursday  | 10           | 12   | 2026-07-09 | 2026-09-24 | 15:00
12        | Marta Skolarova   | Wednesday | 10           | 12   | 2026-07-08 | 2026-09-23 | 07:00
13        | Zuzana Slosarova  | Monday    | 15           | 12   | 2026-07-06 | 2026-09-21 | 15:00
13        | Zuzana Slosarova  | Tuesday   | 15           | 12   | 2026-07-07 | 2026-09-22 | 15:00
13        | Zuzana Slosarova  | Thursday  | 10           | 12   | 2026-07-09 | 2026-09-24 | 07:00
15        | Filip Ferencz     | Friday    | 15           | 12   | 2026-07-10 | 2026-09-25 | 07:00
```

Conclusion from this server audit:

- 10-minute slots are not a Bednar-only exception.
- The current active schedule includes 10-minute contexts for Bartonova, Selecka,
  Skolarova, and part of Slosarova's schedule.
- Slosarova is mixed and must be evaluated by concrete schedule context, not by
  doctor ID alone.
- Bednar `IDUZI=4` and Pospislova `IDUZI=10` exist as users/doctors, but should
  not be used for agent availability options while they have no schedule contexts
  in the tested booking window.
- No schedule context does not by itself prove that a doctor is inactive; it can
  also mean vacation, seasonal pause, missing future schedule, or a non-bookable
  configuration for the inspected period.
- Backend availability and write logic must continue using the concrete
  schedule interval returned by the schedule context.

## Bednar Follow-Up Check, 2026-07-23

Client/live testing showed the earlier Bednar duplicate interpretation was reversed for current booking behavior:

- `IDUZI=2` Rostislav Bednar has the schedule contexts used by availability.
- `IDUZI=4` Rostislav Bednar exists in `UZIVATEL` but returned no schedule contexts in the tested window.
- Server-local `config/agent_context.local.json` now excludes `IDUZI=4` through `system_excluded_doctor_ids`.
- `doctor_name="Bednar"` / `doctor_name="Bednář"` resolves to `IDUZI=2` and returns 10-minute options.
- `services.skin.followup_dermatoscope_minutes` is `null` on the server so skin duration and follow-up duration use the concrete schedule interval, including Bednar's 10-minute contexts.

Confirmed follow-up rule:

- The follow-up dermatoscope reservation length must match the main skin
  examination length.
- Reception confirmed an additional operational case: a doctor can request
  "more time" for a follow-up examination, which effectively doubles the slot to
  30 minutes.
- The "more time" / doubled follow-up slot is outside current MVP scope and
  should not be added to agent-facing behavior until it is represented explicitly
  in backend service rules.

## Earlier Diagnostic Output

Observed output from `tools/diagnostics/db_mapping/inspect_schedule_intervals.py` for 2026-05-22 through 2026-06-04:

```text
2026-05-22 | Friday    | 15 | Filip Ferencz      | 1 | 4 | 5 | 15 | 2 | 420 | 07:00
2026-05-25 | Monday    | 2  | Rostislav Bednar   | 2 | 4 | 1 | 10 | 2 | 480 | 07:00
2026-05-25 | Monday    | 8  | Maria Bartonova    | 1 | 4 | 1 | 10 | 2 | 310 | 08:30
2026-05-25 | Monday    | 13 | Zuzana Slosarova   | 1 | 4 | 1 | 15 | 1 | 120 | 15:00
2026-05-26 | Tuesday   | 8  | Maria Bartonova    | 1 | 4 | 2 | 10 | 2 | 310 | 08:30
2026-05-26 | Tuesday   | 13 | Zuzana Slosarova   | 1 | 4 | 2 | 15 | 1 | 120 | 15:00
2026-05-27 | Wednesday | 1  | Tereza Perez       | 1 | 4 | 3 | 15 | 1 | 120 | 15:00
2026-05-27 | Wednesday | 8  | Maria Bartonova    | 1 | 4 | 3 | 10 | 5 | 310 | 08:30
2026-05-27 | Wednesday | 12 | Marta Skolarova    | 1 | 4 | 3 | 10 | 5 | 700 | 07:00
2026-05-28 | Thursday  | 11 | Dusana Selecka     | 1 | 4 | 4 | 10 | 1 | 120 | 15:00
2026-05-28 | Thursday  | 13 | Zuzana Slosarova   | 1 | 4 | 4 | 10 | 2 | 405 | 07:00
2026-05-29 | Friday    | 15 | Filip Ferencz      | 1 | 4 | 5 | 15 | 2 | 420 | 07:00
2026-06-01 | Monday    | 2  | Rostislav Bednar   | 2 | 4 | 1 | 10 | 2 | 480 | 07:00
2026-06-01 | Monday    | 8  | Maria Bartonova    | 1 | 4 | 1 | 10 | 2 | 310 | 08:30
2026-06-01 | Monday    | 13 | Zuzana Slosarova   | 1 | 4 | 1 | 15 | 1 | 120 | 15:00
2026-06-02 | Tuesday   | 8  | Maria Bartonova    | 1 | 4 | 2 | 10 | 2 | 310 | 08:30
2026-06-02 | Tuesday   | 13 | Zuzana Slosarova   | 1 | 4 | 2 | 15 | 1 | 120 | 15:00
2026-06-03 | Wednesday | 1  | Tereza Perez       | 1 | 4 | 3 | 15 | 1 | 120 | 15:00
2026-06-03 | Wednesday | 8  | Maria Bartonova    | 1 | 4 | 3 | 10 | 5 | 310 | 08:30
2026-06-03 | Wednesday | 12 | Marta Skolarova    | 1 | 4 | 3 | 10 | 5 | 700 | 07:00
2026-06-04 | Thursday  | 11 | Dusana Selecka     | 1 | 4 | 4 | 10 | 1 | 120 | 15:00
2026-06-04 | Thursday  | 13 | Zuzana Slosarova   | 1 | 4 | 4 | 10 | 2 | 405 | 07:00
```

Column order from the diagnostic detail output:

```text
date | weekday | IDUZI | doctor | IDPRAC | TYPTYD | DENTYD | interval_min | blocks | minutes | first_start
```

## Interpreted Findings

- Rostislav Bednar is `IDUZI=2` in this output, not `IDUZI=6`.
- Bednar has confirmed 10-minute schedule contexts in the inspected range.
- 10-minute intervals also appear for Maria Bartonova, Marta Skolarova, Dusana Selecka, and Zuzana Slosarova.
- Zuzana Slosarova shows both 15-minute and 10-minute contexts depending on day.
- Tereza Perez and Filip Ferencz appear with 15-minute intervals in this inspected range.

## Implementation Impact

- Do not encode 10-minute logic as a Bednar-only hardcoded exception.
- Use `OBSDNE_PRAVODLIS_SEL.INTERVAL` for each concrete schedule context.
- For skin examination, default examination duration and follow-up dermatoscope duration to that context interval.
- For plasma, keep the configured service duration but validate it against consecutive free slots using that context interval.
- Shared dermatoscope checks must compare time intervals (`CAS` to `CASDO`), not only equal slot starts.

## Open Checks

- Re-run the diagnostic over a wider range before finalizing production configuration.
- Confirm whether any service should override schedule interval despite the context interval.
- Confirm final bookable doctor list and service permissions separately from schedule interval logic.
