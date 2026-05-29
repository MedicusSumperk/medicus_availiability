# Local API Service

## Purpose

The local API is intended to run on the Medicus server behind Cloudflare Tunnel. It exposes small HTTP endpoints for ElevenLabs tools while keeping Medicus and Firebird unavailable from the public internet.

Initial implementation is read-only for availability and patient lookup. Booking is still a reserved stub.

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

Reserved:

- `/book-appointment`

`/patient-lookup` reads patient card and future appointment data but performs no writes. `/book-appointment` returns `not_implemented` and does not write appointment data.

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
https://medicus-api.example.cz -> http://127.0.0.1:8000
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

Next beta step: replace temporary `trycloudflare` URLs with a named Cloudflare Tunnel and stable hostname, for example:

```text
https://medicus-api.example.cz -> http://127.0.0.1:8000
```

One-time Cloudflare setup outline:

```powershell
C:\tools\cloudflared\cloudflared.exe tunnel login
C:\tools\cloudflared\cloudflared.exe tunnel create medicus-api
C:\tools\cloudflared\cloudflared.exe tunnel route dns medicus-api medicus-api.example.cz
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
  - hostname: medicus-api.example.cz
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

Status: confirmed for the current PoC phase.

Verified flow:

```text
n8n chat agent tool
-> trycloudflare public URL
-> cloudflared on Medicus server
-> local FastAPI service
-> Firebird DB availability logic
-> compact JSON response
-> n8n chat agent
```

Confirmed findings:

- The local API starts and responds on `/health`.
- `/doctor-availability` returns real DB-derived availability, not dummy data.
- The endpoint remains fast enough for chat-agent tool use through trycloudflare.
- The response can be kept compact enough for a conversational agent.
- n8n can call the endpoint as an HTTP Request tool.
- ElevenLabs voice agent can call the availability webhook/tool successfully.
- Voice-agent latency was observed as very fast, practically without noticeable delay.
- The current implementation is sufficient as a PoC; the next infrastructure step is a stable named Cloudflare Tunnel.

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

## Authentication

If `bearer_token` is set to anything other than `CHANGE_ME`, requests must include:

```http
Authorization: Bearer <token>
```

For real deployment, keep the token out of source control. Use `config/api.local.json` or `MEDICUS_API_TOKEN`.

## Patient Lookup Request

`POST /patient-lookup`

Purpose:

- Find a patient in `KAR` from caller/tool data.
- Validate identity using the last 4 digits of `KAR.RODCIS`.
- After verification, return future `OBJOBJ` appointments for that patient.
- Stay read-only.

Supported request fields:

- `phone`, `phone_number`, or `caller_phone`: caller phone number, normalized by digits and matched through `KARKONTAKT.TELEFON_ADJ` / `KARKONTAKT.KONTAKT`.
- `idpac`: direct patient ID if already known.
- `birth_number`, `rodne_cislo`, or `rodcis`: full birth number, matched exactly against `KAR.RODCIS`; also satisfies the last-4 verification check.
- `first_name` / `name`
- `last_name` / `surname`
- `birth_date`: `YYYY-MM-DD`, matched against `KAR.DATNAR`.
- `birth_number_last4` or `rodne_cislo_last4`: verification value.
- `include_appointments`: defaults to `true`.
- `appointment_days_ahead`: defaults to `365`, capped at `730`.
- `include_past_appointments`: defaults to `false`.
- `past_appointment_days`: defaults to `365`, capped at `1825`.
- `limit`: max patient candidates, defaults to `5`, capped at `20`.

Example first lookup from a phone number:

```json
{
  "phone": "+420 777 123 456",
  "limit": 5
}
```

If exactly one patient is found but no verification value is provided, response status is `needs_verification`; the agent should ask for the last 4 digits of the birth number before discussing existing appointments.

The API uses `KAR.RODCIS` internally for verification but does not return the expected last 4 digits to the agent.

Example verified lookup:

```json
{
  "phone": "+420 777 123 456",
  "birth_number_last4": "5666",
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

After verification, `appointments` contains future `OBJOBJ` rows with date, time, doctor, activity, and info fields.
If `include_past_appointments` is true, `past_appointments` contains recent past rows ordered newest first.

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
- `weekdays`: ISO weekday numbers
- `time_from`: `HH:MM`
- `time_to`: `HH:MM`
- `doctor_id`: optional `IDUZI`
- `doctor_name`: optional free-text doctor name from the caller; API resolves it against `UZIVATEL`
- Doctor-name aliases accepted by the API include `doctor`, `preferred_doctor`, `doctorName`, `doctor_text`, `physician`, and `lekar`.
- `system_excluded_doctor_ids` in config marks database users that must never be offered by the API; currently `IDUZI=2` is excluded as an inactive duplicate Bednar row.
- `limit`: defaults to API config, capped by `max_limit`
- `compact`: return a shorter voice-agent payload

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
      "time": "14:00",
      "doctor_name": "Maria Bartonova"
    }
  ]
}
```

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
        "written_in_v1": false
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
