# Current Business Rules

<!-- Generated from config/business_rules*.json. Do not edit by hand. -->

Generated at: 2026-07-27T13:46:26
Rules version: `2026-07-production-v1`

## Validation

- OK: config is structurally valid.

## Rule Matrix

| Rule | Config path | Current value | Effect |
| --- | --- | --- | --- |
| Globally allowed doctors | `doctors.globally_allowed_doctor_ids` | `[]` | Empty means all known doctors are allowed unless excluded. |
| Globally excluded doctors | `doctors.globally_excluded_doctor_ids` | `[4,10]` | These IDUZI values are never offered by availability. |
| Shared dermatoscope blockers | `shared_resources.dermatoscope.blocking_idcinnosti` | `[1,2,5,6]` | Appointments with these IDCINNOSTI values block shared dermatoscope capacity. |
| Shared dermatoscope capacity | `shared_resources.dermatoscope.capacity` | `1` | Current production assumption is one shared dermatoscope. |
| Before-time emergency gate enabled | `operational_rules.before_time_requires_emergency.enabled` | `true` | If true, ordinary availability hides slots before the configured time. |
| Before-time emergency cutoff | `operational_rules.before_time_requires_emergency.before` | `08:00` | Slots before this time require the emergency request flag. |
| Emergency request flag | `operational_rules.before_time_requires_emergency.request_flag` | `emergency` | The availability request field that unlocks emergency-only slots. |
| Afternoon bucket 1 enabled | `operational_rules.afternoon_arrival_buckets[0].enabled` | `true` | If enabled, matching technical slots get a separate spoken time label. |
| Afternoon bucket 1 service | `operational_rules.afternoon_arrival_buckets[0].service` | `skin` | Only this service uses the bucket; empty would mean all services. |
| Afternoon bucket 1 technical range | `operational_rules.afternoon_arrival_buckets[0].time_from / operational_rules.afternoon_arrival_buckets[0].time_to` | `15:00 - 16:00` | Technical start_time values in this range are still used for write. |
| Afternoon bucket 1 spoken label | `operational_rules.afternoon_arrival_buckets[0].spoken_time_label` | `15:00` | This is the time the agent should say to the caller. |
| skin: agent may offer availability | `services.skin.agent_can_offer_availability` | `true` | If false, the service is not accepted by doctor_availability. |
| skin: agent may book | `services.skin.agent_can_book_finally` | `true` | If false, appointment_write rejects this service. |
| skin: main IDCINNOSTI | `services.skin.idcinnosti` | `null` | Value written into the main appointment row; null means default skin row. |
| skin: duration mode | `services.skin.duration.mode` | `schedule_interval` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. |
| skin: duration minutes | `services.skin.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. |
| skin: allowed doctors | `services.skin.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. |
| skin: excluded doctors | `services.skin.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. |
| skin: seasonality enabled | `services.skin.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. |
| skin: seasonality range | `services.skin.seasonality.start / services.skin.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. |
| skin: write strategy | `services.skin.write.strategy` | `main_row_plus_followup` | Controls whether write creates one row or related rows. |
| skin: follow-up enabled | `services.skin.followup.create` | `true` | If true, write creates a related follow-up row. |
| skin: follow-up IDCINNOSTI | `services.skin.followup.idcinnosti` | `6` | IDCINNOSTI written into the related follow-up row. |
| skin: follow-up duration mode | `services.skin.followup.duration.mode` | `schedule_interval` | How the follow-up duration is computed. |
| plasma: agent may offer availability | `services.plasma.agent_can_offer_availability` | `true` | If false, the service is not accepted by doctor_availability. |
| plasma: agent may book | `services.plasma.agent_can_book_finally` | `true` | If false, appointment_write rejects this service. |
| plasma: main IDCINNOSTI | `services.plasma.idcinnosti` | `3` | Value written into the main appointment row; null means default skin row. |
| plasma: duration mode | `services.plasma.duration.mode` | `fixed_minutes` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. |
| plasma: duration minutes | `services.plasma.duration.minutes` | `30` | Used only when duration mode needs a fixed minute value. |
| plasma: allowed doctors | `services.plasma.allowed_doctor_ids` | `[8]` | Empty means all globally allowed doctors unless service-excluded. |
| plasma: excluded doctors | `services.plasma.excluded_doctor_ids` | `[2,4]` | Doctor IDs excluded only for this service. |
| plasma: seasonality enabled | `services.plasma.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. |
| plasma: seasonality range | `services.plasma.seasonality.start / services.plasma.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. |
| plasma: write strategy | `services.plasma.write.strategy` | `single_row` | Controls whether write creates one row or related rows. |

## Doctors

- Globally allowed doctor IDs: `all unless excluded`
- Globally excluded doctor IDs: `4, 10`

| IDUZI | Name | Status | Note |
| --- | --- | --- | --- |
| 1 | Marta Skolarova | active |  |
| 2 | Rostislav Bednar | active | Active Bednar row used by availability/write revalidation. |
| 4 | Rostislav Bednar | excluded | Duplicate row without schedule contexts in tested window. |
| 8 | Maria Bartonova | active |  |
| 10 | Petra Pospisilova | excluded | No schedule contexts in tested window. |
| 11 | Zuzana Slosarova | active |  |
| 12 | Filip Ferencz | active |  |
| 13 | Doctor 13 | active | Schedule interval may vary by day/context. |

## Operational Rules

- Dermatoscope blocking IDCINNOSTI: `1, 2, 5, 6`
- Dermatoscope shared capacity: `1`
- Before-time emergency gate: `enabled` before `08:00` using request flag `emergency`

| Bucket | Service | Technical time range | Spoken label | Status |
| --- | --- | --- | --- | --- |
| 1 | skin | 15:00 - 16:00 | 15:00 | enabled |

## Services

### skin

- Label: Kozni vysetreni
- Agent may offer availability: `True`
- Agent may book finally: `True`
- Main IDCINNOSTI: `None`
- Duration: `schedule_interval`
- Allowed doctor IDs: `all unless excluded`
- Excluded doctor IDs: `all unless excluded`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `main_row_plus_followup`
- Follow-up: `dermatoscope_reservation` with IDCINNOSTI `6`
- Follow-up duration: `schedule_interval`
- Requires shared dermatoscope capacity: `true`

### plasma

- Label: Plazma
- Agent may offer availability: `True`
- Agent may book finally: `True`
- Main IDCINNOSTI: `3`
- Duration: `fixed_minutes` / `30` minutes
- Allowed doctor IDs: `8`
- Excluded doctor IDs: `2, 4`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `single_row`
