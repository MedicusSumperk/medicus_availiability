# Medicus Backend Context

This repository is the backend layer for the ElevenLabs receptionist agent. It
keeps DB-specific and clinic-specific business rules in backend code/config so
the voice agent can call simple tools instead of carrying operational rules in
its prompt.

## Current State

- Stable public base URL: `https://medicus-api.kreli.org`
- Server repo path: `C:\db_bridge\medicus_availiability`
- Active branch for hardening work: `feature/production-hardening-rules-cleanup`
- Runtime API endpoints: `/health`, `/doctor-availability`, `/patient-lookup`,
  `/book-appointment`, `/handoff-summary`
- Patient lookup no longer requires last-4 birth-number verification; unique
  patient match sets `verification.verified=true`
- Appointment writes and cancellations are controlled by server-local
  `config/api.local.json`

The misspelled repo/folder name `medicus_availiability` is intentionally kept
for now. Rename only through a separate coordinated GitHub/server migration.

## Runtime Source Of Truth

- `scripts/api_server.py`: FastAPI endpoint layer
- `scripts/agent_context.py`: shared service option helpers used by availability
- `scripts/availability_search.py`: targeted availability lookup for tool calls
- `scripts/appointment_write.py`: create/cancel/reschedule write helper
- `scripts/patient_lookup.py`: patient identity and appointment lookup
- `scripts/handoff_summary.py`: staff-facing handoff summary builder
- `scripts/business_rules.py`: JSON rules loader and validation
- `config/business_rules.example.json`: versioned default business rules
- `config/business_rules.local.json`: optional ignored server-local override

Human-readable rules are generated into `docs/current_business_rules.md` with:

```powershell
C:\python\python.exe scripts\render_business_rules.py
```

## Current Business Rules Highlights

- Globally excluded `IDUZI`: `4`, `10`
- Bednar uses active `IDUZI=2`; duplicate `IDUZI=4` is excluded
- Skin uses concrete schedule interval and creates a follow-up dermatoscope row
- Plasma uses fixed 30-minute duration and is limited to `IDUZI=8`
- Slots before `08:00` are hidden unless availability request has
  `emergency=true`
- Afternoon skin slots from `15:00` to `16:00` may expose a shared
  `spoken_time_label=15:00` while writes still use exact technical `start_time`

## Repository Organization

- `scripts/`: active runtime backend only
- `tests/`: unit/regression tests for runtime behavior
- `config/`: runtime config examples and checked-in business rules
- `docs/`: current source-of-truth documentation only
- `tools/diagnostics/`: manually run diagnostics and DB mapping helpers
- `research/`: important DB findings and reverse-engineering notes
- `archive/`: ignored historical exports, test runs, and obsolete artefacts

See `docs/repo_inventory.md` for the detailed file map.

## Verification Commands

```powershell
C:\python\python.exe -m unittest discover -s tests
C:\python\python.exe scripts\render_business_rules.py --check
```

Server smoke checks after deploy:

```text
GET  https://medicus-api.kreli.org/health
POST https://medicus-api.kreli.org/doctor-availability
POST https://medicus-api.kreli.org/patient-lookup
POST https://medicus-api.kreli.org/book-appointment
POST https://medicus-api.kreli.org/handoff-summary
```
