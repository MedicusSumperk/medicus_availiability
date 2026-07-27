# Local API Service

## Purpose

The local API is intended to run on the Medicus server behind Cloudflare Tunnel. It exposes small HTTP endpoints for ElevenLabs tools while keeping Medicus and Firebird unavailable from the public internet.

Availability and patient lookup are read-only. Appointment writes are available
behind explicit local config flags and must be used only after patient
verification and a final caller confirmation.

## Endpoints

```text
GET  /health
POST /doctor-availability
POST /patient-lookup
POST /book-appointment
```

Currently implemented:

- `/health`
- `/doctor-availability`
- `/patient-lookup`
- `/book-appointment`

`/patient-lookup` reads patient card and future appointment data but performs no
writes. `/book-appointment` can create, cancel, or reschedule appointments only
when `enable_appointment_writes` is enabled in local config.

## Agent Tool Contract

Target beta behavior:

1. Use `/doctor-availability` whenever the caller asks for available appointment terms, changes doctor/date/time/service preference, or asks for a specific doctor.
2. Use `/patient-lookup` only when identity is needed for existing appointments, changes, cancellations, or final booking.
3. Start with caller phone when available; if it is not enough, ask for surname and date of birth, then first name if needed.
4. Treat `verification.verified=true` as the only gate for existing appointments and write actions. The backend sets it after a unique patient match; last-4 birth-number verification is no longer required.
5. After successful verification, use `appointments` for future bookings and `past_appointments` when `include_past_appointments` was requested.
6. Never discuss existing appointments before verification succeeds.
7. Use `/book-appointment` only after the caller has selected a concrete term
   and the agent has repeated the selected date, time, doctor, and service back
   to the caller for confirmation.
8. Treat `/book-appointment` response as authoritative. If it returns `ok:false`,
   do not claim that the appointment was changed.

## File Locations

Core API files:

```text
scripts/api_server.py
scripts/availability_search.py
scripts/patient_lookup.py
scripts/start_trycloudflare_api.ps1
scripts/start_named_cloudflare_tunnel.ps1
config/api.local.example.json
config/api.local.json              # local only, ignored
docs/local_api.md
data/api/trycloudflare_url.txt     # generated, ignored
```

Shared availability/rule files used by the API:

```text
scripts/agent_context.py
scripts/availability_engine.py
scripts/db.py
config/agent_context.local.example.json
config/agent_context.local.json    # local only, ignored
config/db_config.local.json        # local only, ignored
```

Relevant docs:

```text
PROJECT_CONTEXT.md
docs/agent_context.md
docs/schedule_interval_findings.md
docs/activity_type_mapping.md
```

## Setup

Install dependencies:

```powershell
C:\python\python.exe -m pip install -r requirements.txt
```

Create API config:

```cmd
copy config\api.local.example.json config\api.local.json
```

Set a strong token in `config/api.local.json` or set environment variable:

```powershell
setx MEDICUS_API_TOKEN "strong-random-token"
```

Run locally:

```powershell
C:\python\python.exe scripts\api_server.py
```

Default local URL:

```text
http://127.0.0.1:8000
```

For production-like use, run the API as a background process or Windows service and expose it through Cloudflare Tunnel:

```text
https://medicus-api.kreli.org -> http://127.0.0.1:8000
```

No inbound firewall port is needed on the Medicus server when Cloudflare Tunnel is used.

## Quick Trycloudflare Test

For PoC testing without creating a named Cloudflare tunnel, download `cloudflared.exe` and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_trycloudflare_api.ps1
```

The helper tries to find `cloudflared.exe` in:

```text
<repo>\cloudflared.exe
<repo>\tools\cloudflared.exe
C:\tools\cloudflared\cloudflared.exe
C:\cloudflared\cloudflared.exe
PATH
```

If needed, pass the path explicitly:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_trycloudflare_api.ps1 -CloudflaredPath "C:\tools\cloudflared\cloudflared.exe"
```

The script:

- starts the local API on `http://127.0.0.1:8000`
- starts `cloudflared tunnel --url http://127.0.0.1:8000`
- watches the `cloudflared` output for `https://...trycloudflare.com`
- prints the generated base URL and endpoint URLs
- writes the base URL to `data/api/trycloudflare_url.txt`

Example output:

```text
trycloudflare base URL:
https://example-random-name.trycloudflare.com

Webhook endpoints:
https://example-random-name.trycloudflare.com/doctor-availability
https://example-random-name.trycloudflare.com/patient-lookup
https://example-random-name.trycloudflare.com/book-appointment
```

If the API is already running, use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_trycloudflare_api.ps1 -SkipApiStart
```

`trycloudflare` URLs are temporary and can change after restart. For production, use a named Cloudflare Tunnel and stable hostname.

## Stable Named Cloudflare Tunnel

The current stable beta hostname is:

```text
https://medicus-api.kreli.org -> http://127.0.0.1:8000
```

Historical `https://...trycloudflare.com` URLs in local exports are stale unless a temporary tunnel was explicitly restarted for a one-off test.

One-time Cloudflare setup outline:

```powershell
C:\tools\cloudflared\cloudflared.exe tunnel login
C:\tools\cloudflared\cloudflared.exe tunnel create medicus-api
C:\tools\cloudflared\cloudflared.exe tunnel route dns medicus-api medicus-api.kreli.org
```

Create a local `cloudflared` config file on the server. Exact path can vary by installation, but a common service-friendly location is:

```text
C:\Windows\System32\config\systemprofile\.cloudflared\config.yml
```

Example config:

```yaml
tunnel: medicus-api
credentials-file: C:\Windows\System32\config\systemprofile\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: medicus-api.kreli.org
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Manual run for testing:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_named_cloudflare_tunnel.ps1 -TunnelName medicus-api
```

If API is already running manually:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_named_cloudflare_tunnel.ps1 -TunnelName medicus-api -SkipApiStart
```

For beta/production, install `cloudflared` as a Windows Service after the named tunnel works manually:

```powershell
C:\tools\cloudflared\cloudflared.exe service install
```

Keep the local API as a separate service/process. Do not expose the API directly to the public interface; keep it bound to `127.0.0.1`.

## PoC Verification

Status: confirmed for the current beta test phase.

Verified flow:

```text
n8n / ElevenLabs tool
-> stable Cloudflare Tunnel URL
-> cloudflared on Medicus server
-> local FastAPI service
-> Firebird DB availability logic
-> compact JSON response
-> n8n chat agent
```

Confirmed findings:

- The local API starts and responds on `/health`.
- `/doctor-availability` returns real DB-derived availability, not dummy data.
- The endpoint remains fast enough for chat/voice-agent tool use through Cloudflare Tunnel.
- The response can be kept compact enough for a conversational agent.
- n8n can call the endpoint as an HTTP Request tool.
- ElevenLabs voice agent can call the availability webhook/tool successfully.
- Voice-agent latency was observed as very fast, practically without noticeable delay.
- Stable tunnel smoke tests pass through `https://medicus-api.kreli.org`.
- The server-local API config currently has appointment writes and cancellations enabled for controlled client testing.

Current tested request shape:

```json
{
  "service": "skin",
  "limit": 3,
  "compact": true
}
```

Targeted request shape also works when n8n maps fields explicitly:

```json
{
  "service": "skin",
  "date_from": "2026-08-08",
  "date_to": "2026-09-08",
  "time_from": "14:00",
  "limit": 3,
  "compact": true
}
```

Agent/tool-schema note:

- The backend supports `weekdays` as a list, e.g. `[4]`.
- The tested agent initially mapped parameters incorrectly when it was allowed to infer too many fields.
- For the next tests, keep `limit` and `compact` fixed in the n8n/ElevenLabs tool definition.
- Prefer simple scalar fields for agent input where possible, e.g. `weekday: 4`, then map that to `weekdays: [4]` in the workflow.
- Later backend hardening can make the API accept `weekday`, single-value `weekdays`, or empty strings more gracefully.

Operational note:

- For the PoC, two foreground processes are acceptable: one terminal for `scripts/api_server.py` and one terminal for `cloudflared`.
- `scripts/start_trycloudflare_api.ps1 -SkipApiStart` is useful when the API is already running manually.
- If `cloudflared` is not in `PATH`, pass `-CloudflaredPath "C:\path\to\cloudflared.exe"`.
- For current beta tests, prefer the stable base URL `https://medicus-api.kreli.org` over any saved temporary tunnel URL.

## Authentication

If `bearer_token` is set to anything other than `CHANGE_ME`, requests must include:

```http
Authorization: Bearer <token>
```

For real deployment, keep the token out of source control. Use `config/api.local.json` or `MEDICUS_API_TOKEN`.

Appointment writes are disabled unless local config explicitly enables them:

```json
{
  "enable_appointment_writes": true,
  "enable_appointment_cancellations": true,
  "appointment_created_by": 10,
  "appointment_info_prefix": "AI_RECEPTION",
  "include_related_appointments_by_default": true,
  "skin_followup_idcinnosti": 6,
  "skin_followup_info": "AI_DERMATOSCOPE_RESERVATION",
  "plasma_info_marker": "plazma"
}
```

## Patient Lookup Request

`POST /patient-lookup`

Purpose:

- Find a patient in `KAR` from caller/tool data.
- Verify identity when the provided data narrows the lookup to one unique patient.
- After verification, return future `OBJOBJ` appointments for that patient.
- Stay read-only.

Supported request fields:

- `phone`, `phone_number`, or `caller_phone`: caller phone number, normalized by digits and matched through `KARKONTAKT.TELEFON_ADJ` / `KARKONTAKT.KONTAKT`.
- `idpac`: internal direct patient ID if already known from system state; never ask the caller for this value.
- `birth_number`, `rodne_cislo`, or `rodcis`: full birth number, matched exactly against `KAR.RODCIS`; kept as a strong technical anchor if explicitly available.
- `first_name` / `name`
- `last_name` / `surname`
- `birth_date`: `YYYY-MM-DD`, matched against `KAR.DATNAR`.
- `birth_number_last4` or `rodne_cislo_last4`: deprecated compatibility input; accepted but no longer required or used as the verification gate.
- `include_appointments`: defaults to `true`.
- `appointment_days_ahead`: defaults to `365`, capped at `730`.
- `include_past_appointments`: defaults to `false`.
- `past_appointment_days`: defaults to `365`, capped at `1825`.
- `limit`: max patient candidates, defaults to `5`, capped at `20`.

Current behavior:

- A unique patient match returns `status: "found"` and `verification.verified=true`.
- Last-4 birth-number verification is deprecated and is no longer required before returning appointments.
- Start with phone when available. If phone is not enough, ask for surname and date of birth, then first name if needed.
- Fuzzy/accent-insensitive name matching is used only when the request also has a stable anchor such as phone, birth date, internal `idpac`, or full birth number.

Name matching first uses the database text filters. If that returns no rows and
the request also contains a stable identifying anchor such as `birth_date`,
`phone`, internal `idpac`, or full birth number, the backend retries without the name
filters and applies an accent-insensitive Python name match to the narrowed
candidate set. This lets inputs such as `Vladimir` match `Vladimír` without
making name-only lookups overly broad.

Example first lookup from a phone number:

```json
{
  "phone": "+420 777 123 456",
  "limit": 5
}
```

If exactly one patient is found, the response is verified by unique match. The API does not ask the agent to collect last-4 birth-number verification.

Example verified lookup:

```json
{
  "phone": "+420 777 123 456",
  "include_appointments": true
}
```

Example lookup with full birth number:

```json
{
  "birth_number": "5656565666",
  "include_appointments": true,
  "include_past_appointments": true
}
```

After unique-match verification, `appointments` contains future `OBJOBJ` rows with date, time, doctor, activity, and info fields.
If `include_past_appointments` is true, `past_appointments` contains recent past rows ordered newest first.
The response also includes `appointments_json` and `past_appointments_json` as
stringified JSON arrays for ElevenLabs flattened dynamic variable assignments.

## Appointment Write Request

`POST /book-appointment`

Purpose:

- Create, cancel, or reschedule appointment rows in `OBJOBJ`.
- Revalidate create/reschedule requests against live `/doctor-availability`
  logic before writing.
- For `service=skin`, create both the main skin appointment and the immediate
  follow-up dermatoscope reservation in one transaction.
- Keep cancellation/reschedule transactional: if any step fails, the API rolls
  back the whole request.

Supported actions:

- `create`
- `cancel`
- `reschedule`

Common required fields:

- `action`: `create`, `cancel`, or `reschedule`; defaults to `create`
- `idpac`: verified patient ID
- `patient_verified`: must be `true`; the agent sets this only after
  `patient_lookup` returned `verification.verified=true`

Create/reschedule fields:

- `service`: `skin` or `plasma`
- `date`: appointment date, `YYYY-MM-DD`
- `time` or `start_time`: selected start time, `HH:MM`
- `doctor_name`: natural-language doctor name, or `doctor_id` when the caller is
  using a DB-facing full availability option
- `info`: optional explicit `OBJOBJ.INFO`; if omitted, API uses configured
  markers

Cancel/reschedule fields:

- `appointment_id` or `appointment_ids`: existing `OBJOBJ.IDOBJ` row(s)
- `include_related`: defaults to `true`; when cancelling/moving a skin main row,
  API tries to include the immediate dermatoscope reservation row as well

Example create skin appointment:

```json
{
  "action": "create",
  "idpac": 33411,
  "patient_verified": true,
  "service": "skin",
  "doctor_name": "Bartonova",
  "date": "2026-08-08",
  "time": "14:00"
}
```

Successful skin response returns two IDs:

```json
{
  "ok": true,
  "status": "created",
  "service": "skin",
  "appointment_ids": [140001, 140002],
  "appointments": [
    {
      "idobj": 140001,
      "idcinnosti": null
    },
    {
      "idobj": 140002,
      "idcinnosti": 6
    }
  ]
}
```

Example create plasma appointment:

```json
{
  "action": "create",
  "idpac": 33411,
  "patient_verified": true,
  "service": "plasma",
  "doctor_name": "Bartonova",
  "date": "2026-08-08",
  "time": "14:00"
}
```

Example cancel appointment:

```json
{
  "action": "cancel",
  "idpac": 33411,
  "patient_verified": true,
  "appointment_id": 140001,
  "include_related": true
}
```

Example reschedule appointment:

```json
{
  "action": "reschedule",
  "idpac": 33411,
  "patient_verified": true,
  "appointment_id": 140001,
  "include_related": true,
  "service": "skin",
  "doctor_name": "Bartonova",
  "date": "2026-08-15",
  "time": "10:00"
}
```

Important write behavior:

- Writes are disabled by default in `config/api.local.example.json`.
- Create and reschedule re-run live availability for the exact date/time/service
  before insert.
- Skin writes create two rows in one transaction:
  - main skin appointment with `IDCINNOSTI=NULL`
  - follow-up dermatoscope reservation with configured `skin_followup_idcinnosti`
    defaulting to `6`
- Plasma writes create one row with `IDCINNOSTI=3` and configured plasma marker
  in `INFO`.
- Cancel currently uses `DELETE FROM OBJOBJ` for the selected row(s) when
  `enable_appointment_cancellations=true`.
- If the selected slot is no longer bookable, response status is
  `slot_not_bookable` and no write is committed.
- If `doctor_name` cannot be resolved clearly, response status is
  `doctor_not_resolved` and no write is committed.

## Availability Request

No body, or an empty body, returns the first default options:

```http
POST /doctor-availability
```

Filtered request:

```json
{
  "service": "skin",
  "date_from": "2026-07-01",
  "date_to": "2026-08-31",
  "doctor_name": "Bartonova",
  "weekdays": [4],
  "time_from": "14:00",
  "limit": 3,
  "compact": true
}
```

Weekdays use ISO numbering:

```text
1 = Monday
2 = Tuesday
3 = Wednesday
4 = Thursday
5 = Friday
6 = Saturday
7 = Sunday
```

Supported filters:

- `service`: `skin` or `plasma`; defaults to `skin`
- `date_from`: ISO date; defaults to today
- `date_to`: ISO date; optional
- `days_ahead`: used when `date_to` is omitted; default from API config
- `include_weekends`: default `false`
- `weekdays`: explicit ISO weekday filter from the request
- `weekday`: optional scalar alias; normalized to `weekdays: [weekday]`
- `effective_weekdays`: ISO weekday numbers effectively scanned by the backend;
  when `include_weekends=false` and no explicit `weekdays` are provided, this is
  `[1, 2, 3, 4, 5]`
- `time_from`: `HH:MM`
- `time_to`: `HH:MM`
- `doctor_id`: optional `IDUZI`
- `doctor_name`: optional free-text doctor name from the caller; API resolves it against `UZIVATEL`
- Doctor-name aliases accepted by the API include `doctor`, `preferred_doctor`, `doctorName`, `doctor_text`, `physician`, and `lekar`.
- `system_excluded_doctor_ids` in config marks database users that must never be offered by the API.
- Current server finding/config: Bednar availability is on `IDUZI=2`; `IDUZI=4` is excluded because it exists in `UZIVATEL` but has no schedule contexts in the tested window.
- `limit`: defaults to API config, capped by `max_limit`
- `compact`: return a shorter voice-agent payload

`limit` is the response limit. When a `time_from` or `time_to` filter is present, the backend scans a larger internal candidate set before applying the time filter so afternoon/evening results are not accidentally cut off by early-day candidates.

Doctor-name behavior:

- If `doctor_id` is supplied and found, it wins.
- If `doctor_name` uniquely matches a known doctor, the API filters to that doctor.
- Matching is case-insensitive and accent-insensitive; partial surname-like input should work.
- If `doctor_name` is unknown or ambiguous, the API returns general availability and includes an `agent_notes` message explaining that the doctor filter was not applied.

Example with doctor preference:

```json
{
  "service": "skin",
  "doctor_name": "Bartonova",
  "date_from": "2026-07-01",
  "limit": 3,
  "compact": true
}
```

Example note when the doctor was not found:

```json
{
  "agent_notes": [
    "Doctor name 'Novak' was not found; returning general availability."
  ]
}
```

## Compact Response

With `"compact": true`:

```json
{
  "ok": true,
  "service": "skin",
  "filters": {
    "weekdays": [],
    "effective_weekdays": [1, 2, 3, 4, 5],
    "include_weekends": false,
    "doctor": {
      "doctor_id": 8,
      "doctor_name": "Maria Bartonova",
      "requested_doctor_name": "Bartonova",
      "match_type": "partial"
    }
  },
  "agent_notes": [],
  "options": [
    {
      "date": "2026-07-24",
      "weekday": "Friday",
      "weekday_iso": 5,
      "weekday_cs": "pátek",
      "time": "14:00",
      "doctor_name": "Maria Bartonova"
    }
  ],
  "options_json": "[{\"date\":\"2026-07-24\",\"weekday\":\"Friday\",\"weekday_iso\":5,\"weekday_cs\":\"pátek\",\"time\":\"14:00\",\"doctor_name\":\"Maria Bartonova\"}]"
}
```

`options_json` is intentionally included as a string for ElevenLabs dynamic
variable assignments, because the beta agent uses flattened string/number/boolean
runtime variables instead of a nested state object.

## Full Response

Without `"compact": true`, the response includes DB-facing fields needed for later booking:

```json
{
  "ok": true,
  "service": "skin",
  "date_range": {
    "date_from": "2026-07-01",
    "date_to": "2026-08-31"
  },
  "filters": {
    "weekdays": [4],
    "time_from": "14:00",
    "time_to": null,
    "doctor": {
      "doctor_id": 8,
      "doctor_name": "Maria Bartonova",
      "requested_doctor_name": "Bartonova",
      "match_type": "partial"
    }
  },
  "agent_notes": [],
  "options": [
    {
      "date": "2026-07-02",
      "weekday": "Thursday",
      "weekday_iso": 4,
      "weekday_cs": "čtvrtek",
      "service": "skin",
      "start_time": "14:10",
      "end_time": "14:20",
      "duration_minutes": 10,
      "slot_interval_minutes": 10,
      "doctor_id": 8,
      "doctor_name": "Maria Bartonova",
      "idprac": 1,
      "idcinnosti": null,
      "followup_dermatoscope_slot": {
        "start_time": "14:20",
        "end_time": "14:30",
        "duration_minutes": 10,
        "written_in_v1": true
      }
    }
  ],
  "scanned": {
    "days": 1,
    "contexts": 2
  }
}
```

## Cloudflare Tunnel Shape

Target mapping:

```text
Cloudflare public HTTPS URL
  -> cloudflared on Medicus server
  -> http://127.0.0.1:8000
  -> scripts/api_server.py
  -> Firebird DB / existing availability modules
```

The API should bind to `127.0.0.1`, not a public interface, when used behind Cloudflare Tunnel.
