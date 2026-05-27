# Local API Service

## Purpose

The local API is intended to run on the Medicus server behind Cloudflare Tunnel. It exposes small HTTP endpoints for ElevenLabs tools while keeping Medicus and Firebird unavailable from the public internet.

Initial implementation is read-only for availability. Patient lookup and booking endpoints are reserved stubs.

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

Reserved:

- `/patient-lookup`
- `/book-appointment`

The reserved endpoints return `not_implemented` and do not read or write appointment data.

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

For PoC testing without creating a named Cloudflare tunnel, install `cloudflared` and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_trycloudflare_api.ps1
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

## Authentication

If `bearer_token` is set to anything other than `CHANGE_ME`, requests must include:

```http
Authorization: Bearer <token>
```

For real deployment, keep the token out of source control. Use `config/api.local.json` or `MEDICUS_API_TOKEN`.

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
- `limit`: defaults to API config, capped by `max_limit`
- `compact`: return a shorter voice-agent payload

## Compact Response

With `"compact": true`:

```json
{
  "ok": true,
  "service": "skin",
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
    "doctor_id": null
  },
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
