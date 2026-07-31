# ElevenLabs Current Tools

Use stable base URL:

```text
https://medicus-api.kreli.org
```

## agent_capabilities

Endpoint: `POST /agent-capabilities`

Use when the caller asks what the agent can help with, what services are
available, or mentions a service that may be outside first production scope.
Do not guess service scope from memory.

Key response fields:

- `bookable_services`: services the agent may offer and book directly
- `handoff_services`: known services that must go to staff handoff
- `voice_answer_cs`: concise Czech answer suitable for the caller

## doctor_availability

Endpoint: `POST /doctor-availability`

Use whenever the caller asks for available terms or changes service, doctor,
date, day, or time preference. Do not guess availability from memory.

Key parameters:

- `service`: use `skin` for ordinary skin examination, `dermatoscope_first` for
  paid dermatoscopy with scan 15 minutes before doctor time. Other known
  services should use handoff unless returned in `bookable_services`.
- `doctor_name`: optional free-text doctor preference
- `date_from`, `date_to`: optional `YYYY-MM-DD` search window
- `time_from`, `time_to`: optional `HH:MM` search window
- `weekdays`: optional list of ISO weekdays
- `limit`: use `3` for voice
- `compact`: use `true` for voice
- `emergency`: set `true` only for emergency/pohotovost requests

For "nearest available" requests, do not set `date_to` to a short artificial
window. Send `date_from` plus service/time/doctor filters and let the backend
extend the search until it finds the nearest matching slot.

Key response fields:

- `options[].start_time`: exact technical slot for booking writes
- `options[].technical_start_time`: same exact technical slot when present
- `options[].spoken_time_label`: time to say to the caller
- `options[].scan_start_time`: for dermatoscopy, when the patient should arrive for scan
- `options[].weekday_cs`: day name to say to the caller

If `spoken_time_label` differs from `start_time`, say `spoken_time_label` to the
caller but keep the technical `start_time` for `appointment_write`.
For `dermatoscope_first`, tell the caller both times naturally: the scan arrival
time from `scan_start_time`, and the doctor appointment time from `start_time`.

The backend may deduplicate multiple technical slots that share the same
`spoken_time_label` for the same doctor/date/service. The returned option still
contains the exact technical slot to use for booking.

## patient_lookup

Endpoint: `POST /patient-lookup`

Use only when identity is needed for existing appointments, cancellation,
reschedule, or final booking.

Key parameters:

- `phone`: caller phone from metadata or confirmed digits; useful as a lookup hint, but not sufficient by itself for final new booking
- `surname`: confirmed surname
- `birth_date`: confirmed date of birth
- `first_name`: confirmed first name when needed to narrow multiple matches
- `include_appointments`: normally `true`
- `include_past_appointments`: normally `false`
- `birth_number_last4`: deprecated optional compatibility field; do not ask for it
- `birth_number`: full birth number only if explicitly provided in testing or by caller

Verification succeeds only when response contains:

```json
{"verification": {"verified": true}}
```

For final creation of a new appointment, verify the patient being booked with at least confirmed surname and date of birth. Do not rely on caller-phone-only verification before `appointment_write`.

Never ask the caller for `idpac`; it is internal only.

## appointment_write

Endpoint: `POST /book-appointment`

Use only after `patient_lookup` verified identity and the caller explicitly
confirmed the concrete action.

Key parameters:

- `action`: `create`, `cancel`, or `reschedule`
- `idpac`: internal patient ID from verified lookup
- `patient_verified`: `true`
- `service`: selected service
- `doctor_name`: selected doctor from availability
- `date`: selected date from availability
- `time` or `start_time`: exact technical slot from availability
- `appointment_id`: required for cancel/reschedule

For create/reschedule, send the technical slot from `doctor_availability`, not
the spoken label.

First production scope permits final booking for `skin` and
`dermatoscope_first`. Post-scan check, laser, plasma/PRP and procedures should
use `handoff_summary`.

## handoff_summary

Endpoint: `POST /handoff-summary`

Use when the caller needs staff or the request is outside supported automation.

Key parameters:

- `mode`: `live_transfer` or `callback`
- `caller_phone`: caller phone when available
- `reason`: short handoff reason
- `patient`: verified patient context when available
- `selected_slot`: selected slot context when available
- `appointments`: relevant appointment context when available

Use `summary_for_staff` as the compact context for staff.
