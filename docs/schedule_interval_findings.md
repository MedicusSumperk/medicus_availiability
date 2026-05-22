# Schedule Interval Findings

## Why This Matters

Agent booking logic cannot assume a global 15-minute appointment grid. Medicus schedule blocks expose their own `INTERVAL` through `OBSDNE_PRAVODLIS_SEL`, and the same clinic week can contain both 10-minute and 15-minute doctor contexts.

The agent context therefore treats slot interval as a property of the concrete doctor/date/context, not as a doctor-hardcoded exception.

## Confirmed Diagnostic Output

Observed output from `scripts/tests/inspect_schedule_intervals.py` for 2026-05-22 through 2026-06-04:

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
