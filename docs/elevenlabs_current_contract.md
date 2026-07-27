# ElevenLabs Current Contract

This is the current production-facing contract between the ElevenLabs agent and
the Medicus backend. Historical prompt exports and test runs are archive
material, not source of truth.

## Backend Base

Use the stable API base:

```text
https://medicus-api.kreli.org
```

The API exposes four agent tools:

- `doctor_availability` -> `POST /doctor-availability`
- `patient_lookup` -> `POST /patient-lookup`
- `appointment_write` -> `POST /book-appointment`
- `handoff_summary` -> `POST /handoff-summary`

## Identity

The agent must not ask for the last 4 digits of the birth number.

Identity is verified only when `patient_lookup` returns:

```json
{
  "verification": {
    "verified": true
  }
}
```

Suggested flow:

1. Use caller phone from metadata when identity is needed.
2. If not found, ask for surname and date of birth.
3. If multiple matches remain, ask for the missing next detail, typically first name.
4. Never ask the caller for `idpac`; it is internal only.

## Availability And Booking

The agent should not hold doctor/procedure business rules in the prompt. The
backend applies the current rules from `config/business_rules*.json`.

Availability options may contain two different time fields:

- `start_time` / `technical_start_time`: exact technical slot to send to `appointment_write`.
- `spoken_time_label`: time the agent should say to the caller.

For booking, always send the exact technical `start_time` returned by
`doctor_availability`, even if `spoken_time_label` is different.

Before 08:00, normal availability is hidden by the backend. Emergency slots are
returned only when the request explicitly includes `emergency=true`.

## Handoff

Use `handoff_summary` when the request is outside the supported scope or staff
must take over.

Modes:

- `live_transfer`: prepare context for immediate transfer.
- `callback`: prepare context for staff to call back later.

The tool returns `summary_for_staff`; use it as the compact handoff context.

## Source Of Truth

- Current prompt baseline: `docs/elevenlabs_agent_prompt_current_cs.md`.
- Current tool descriptions and parameters: `docs/elevenlabs_current_tools.md`.
- Current dynamic variables seed: `docs/elevenlabs_dynamic_variables_current.json`.
- Machine rules: `config/business_rules.example.json` and server-local
  `config/business_rules.local.json`.
- Human-readable generated rules: `docs/current_business_rules.md`.
- Change workflow for developers/fresh agents: `docs/business_rules_change_guide.md`.
- API behavior: `docs/local_api.md`.

Archived `archive/elevenlabs/` files are historical reference only.
