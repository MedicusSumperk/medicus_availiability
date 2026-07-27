# Diagnostics

These scripts are useful for DB mapping, investigation, and one-off operational
checks. They are not part of the runtime API surface.

Run them from the repository root with the server Python:

```powershell
C:\python\python.exe tools\diagnostics\<script>.py
C:\python\python.exe tools\diagnostics\db_mapping\<script>.py
```

Config examples for diagnostics live in `tools/diagnostics/config_examples/`.
Copy a needed example into `config/*.local.json` before running a diagnostic
that asks for local defaults.

Important diagnostics:

- `check_availability_cli.py`: interactive single-day availability check
- `check_week_availability_cli.py`: weekly read-only availability report
- `build_agent_context_cli.py`: legacy pre-call context builder
- `start_trycloudflare_api.ps1`: historical temporary tunnel helper for one-off diagnostics
- `db_mapping/inspect_schedule_intervals.py`: doctor slot interval audit
- `db_mapping/inspect_appointment_types.py`: appointment/activity type mapping
- `db_mapping/inspect_booking_write_path.py`: write-shape inspection
- `db_mapping/test_booking_insert_rollback.py`: rollback-only write test
