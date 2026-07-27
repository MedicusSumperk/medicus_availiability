# Repository Inventory

Status labels:

- `runtime`: active API/backend code
- `runtime_config`: versioned runtime config or example
- `generated_review`: generated human-readable output
- `current_docs`: active source of truth
- `diagnostic`: manually run helper outside runtime
- `research`: important DB/reverse-engineering notes
- `archive`: historical artefact, not active source of truth
- `ignored_local`: local config/output/log, not committed

| Path | Status | Used by | Notes |
| --- | --- | --- | --- |
| `scripts/api_server.py` | runtime | FastAPI service | Defines `/health`, `/doctor-availability`, `/patient-lookup`, `/book-appointment`, `/handoff-summary`. |
| `scripts/agent_context.py` | runtime | availability search | Shared service option helpers retained because runtime availability imports them. |
| `scripts/availability_search.py` | runtime | `/doctor-availability`, write revalidation | Applies business rules and returns technical/spoken time fields. |
| `scripts/availability_engine.py` | runtime | availability search, diagnostics | Firebird schedule/appointment availability calculation. |
| `scripts/appointment_write.py` | runtime | `/book-appointment` | Creates, cancels, or reschedules behind local write flags. |
| `scripts/patient_lookup.py` | runtime | `/patient-lookup` | Verifies identity by unique match; no last4 gate. |
| `scripts/handoff_summary.py` | runtime | `/handoff-summary` | Builds staff-facing live-transfer/callback context. |
| `scripts/business_rules.py` | runtime | availability/write/rules renderer | Loads and validates machine business rules. |
| `scripts/db.py` | runtime | all DB-backed runtime and diagnostics | Firebird connection helper. |
| `scripts/load_doctors.py` | runtime | doctor directory helpers | Doctor metadata lookup helper. |
| `scripts/render_business_rules.py` | runtime | docs generation/checks | Generates `docs/current_business_rules.md`. |
| `config/api.local.example.json` | runtime_config | API setup | Example for ignored `config/api.local.json`. |
| `config/db_config.example.json` | runtime_config | DB setup | Example for ignored `config/db_config.local.json`. |
| `config/business_rules.example.json` | runtime_config | backend rules | Versioned default business rules. |
| `config/business_rules.local.json` | ignored_local | server override | Optional ignored local overlay when present. |
| `docs/local_api.md` | current_docs | backend/API implementers | API behavior and request/response notes. |
| `docs/elevenlabs_current_contract.md` | current_docs | ElevenLabs setup | Current agent/tool contract. |
| `docs/elevenlabs_current_tools.md` | current_docs | ElevenLabs setup | Copy-ready current tool descriptions and params. |
| `docs/elevenlabs_agent_prompt_current_cs.md` | current_docs | ElevenLabs setup | Current prompt baseline. |
| `docs/elevenlabs_dynamic_variables_current.json` | current_docs | ElevenLabs setup | Minimal current dynamic-variable state. |
| `docs/current_business_rules.md` | generated_review | rule review | Generated from business rules; do not edit by hand. |
| `docs/business_rules_change_guide.md` | current_docs | dev/fresh agents | How to add or change rules. |
| `tools/diagnostics/` | diagnostic | manual operators/devs | DB mapping, legacy context builder, and availability diagnostics. |
| `tools/diagnostics/start_trycloudflare_api.ps1` | diagnostic | one-off tunnel tests | Temporary tunnel helper; production uses the stable named tunnel. |
| `research/db-mapping/` | research | dev/fresh agents | Important DB findings and mapping notes. |
| `archive/elevenlabs/` | archive | historical reference only | Old prompts, exports, dynamic variables, and tool configs. |
| `logs/`, `outputs/`, `data/api/`, `docs/test_runs/` | ignored_local | generated output | Local/server generated artefacts. |

Known typo: repo and server path currently use `medicus_availiability`; do not
rename during normal cleanup or deployment.
