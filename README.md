# Medicus Backend

Production-facing backend for the Medicus / Firebird integration used by the
ElevenLabs receptionist agent.

The runtime API exposes four tool endpoints behind the stable Cloudflare Tunnel:

```text
https://medicus-api.kreli.org
```

```text
GET  /health
POST /doctor-availability
POST /patient-lookup
POST /book-appointment
POST /handoff-summary
```

## Runtime Layout

Active backend code lives in `scripts/`:

```text
api_server.py
agent_context.py
availability_engine.py
availability_search.py
appointment_write.py
business_rules.py
db.py
handoff_summary.py
load_doctors.py
patient_lookup.py
render_business_rules.py
```

Active runtime config examples live in `config/`:

```text
api.local.example.json
business_rules.example.json
db_config.example.json
settings.json
```

Server-local files such as `config/api.local.json`,
`config/db_config.local.json`, and optional `config/business_rules.local.json`
are ignored by Git.

## Source Of Truth

- API contract: `docs/local_api.md`
- ElevenLabs contract: `docs/elevenlabs_current_contract.md`
- Current machine rules: `config/business_rules.example.json`
- Generated human rules review: `docs/current_business_rules.md`
- Rule change workflow: `docs/business_rules_change_guide.md`
- Repo map: `docs/repo_inventory.md`

Diagnostics and reverse-engineering helpers live in `tools/diagnostics/`.
Database research notes live in `research/`. Historical ElevenLabs exports and
test artefacts live in ignored `archive/`.

Known deployment path typo: the repo and server folder are currently named
`medicus_availiability`. Do not rename it as part of normal cleanup or deploys;
that rename needs a separate coordinated server/GitHub migration.

## Setup

Create local config files from examples:

```cmd
copy config\db_config.example.json config\db_config.local.json
copy config\api.local.example.json config\api.local.json
```

Install dependencies:

```powershell
C:\python\python.exe -m pip install -r requirements.txt
```

Run the API locally:

```powershell
C:\python\python.exe scripts\api_server.py
```

Validate rules and tests:

```powershell
C:\python\python.exe scripts\render_business_rules.py --check
C:\python\python.exe -m unittest discover -s tests
```

Regenerate the human rules review after editing business rules:

```powershell
C:\python\python.exe scripts\render_business_rules.py
```
