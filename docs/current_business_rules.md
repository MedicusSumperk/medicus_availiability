# Current Business Rules

<!-- Generated from config/business_rules*.json. Do not edit by hand. -->

Generated at: 2026-07-28T13:05:40
Rules version: `2026-07-production-v1`

## Validation

- OK: config is structurally valid.

## Rule Matrix

| Rule | Config path | Current value | Effect | How to change |
| --- | --- | --- | --- | --- |
| Globally allowed doctors | `doctors.globally_allowed_doctor_ids` | `[]` | Empty means all known doctors are allowed unless excluded. | Add IDs to restrict all services to a fixed global allow-list; leave empty to allow all non-excluded doctors. |
| Globally excluded doctors | `doctors.globally_excluded_doctor_ids` | `[4,10]` | These IDUZI values are never offered by availability. | Add or remove IDUZI values to globally hide or restore doctors for every backend rule. |
| Shared dermatoscope blockers | `shared_resources.dermatoscope.blocking_idcinnosti` | `[1,2,5,6]` | Appointments with these IDCINNOSTI values block shared dermatoscope capacity. | Add IDCINNOSTI values that consume dermatoscope capacity; remove values only after DB/client confirmation. |
| Shared dermatoscope capacity | `shared_resources.dermatoscope.capacity` | `1` | Current production assumption is one shared dermatoscope. | Change only if the clinic has more or fewer shared dermatoscope devices. |
| Before-time emergency gate enabled | `operational_rules.before_time_requires_emergency.enabled` | `true` | If true, ordinary availability hides slots before the configured time. | Set false to return early slots normally; keep true for production emergency-only behavior. |
| Before-time emergency cutoff | `operational_rules.before_time_requires_emergency.before` | `08:00` | Slots before this time require the emergency request flag. | Edit the HH:MM cutoff; availability before that time requires the emergency flag. |
| Emergency request flag | `operational_rules.before_time_requires_emergency.request_flag` | `emergency` | The availability request field that unlocks emergency-only slots. | Rename only if the API/tool request field is changed at the same time. |
| Afternoon bucket 1 enabled | `operational_rules.afternoon_arrival_buckets[0].enabled` | `true` | If enabled, matching technical slots get a separate spoken time label. | Set false to disable this spoken-time bucket without deleting it. |
| Afternoon bucket 1 service | `operational_rules.afternoon_arrival_buckets[0].service` | `skin` | Only this service uses the bucket; empty would mean all services. | Change the service key or leave empty/null to apply this bucket to all services. |
| Afternoon bucket 1 weekdays | `operational_rules.afternoon_arrival_buckets[0].weekdays` | `[1,2,3,4,5]` | Empty means every weekday; otherwise ISO weekdays 1=Monday through 7=Sunday. | Use ISO weekdays, e.g. [1,2,3] for Monday-Wednesday; leave empty for all days. |
| Afternoon bucket 1 technical range | `operational_rules.afternoon_arrival_buckets[0].time_from / operational_rules.afternoon_arrival_buckets[0].time_to` | `11:00 - 12:00` | Technical start_time values in this range are still used for write. | Edit the technical slot range; writes still use the exact technical start_time. |
| Afternoon bucket 1 spoken label | `operational_rules.afternoon_arrival_buckets[0].spoken_time_label` | `11:00` | This is the time the agent should say to the caller. | Edit what the agent should say to the caller for matching technical slots. |
| Afternoon bucket 2 enabled | `operational_rules.afternoon_arrival_buckets[1].enabled` | `true` | If enabled, matching technical slots get a separate spoken time label. | Set false to disable this spoken-time bucket without deleting it. |
| Afternoon bucket 2 service | `operational_rules.afternoon_arrival_buckets[1].service` | `skin` | Only this service uses the bucket; empty would mean all services. | Change the service key or leave empty/null to apply this bucket to all services. |
| Afternoon bucket 2 weekdays | `operational_rules.afternoon_arrival_buckets[1].weekdays` | `[1]` | Empty means every weekday; otherwise ISO weekdays 1=Monday through 7=Sunday. | Use ISO weekdays, e.g. [1,2,3] for Monday-Wednesday; leave empty for all days. |
| Afternoon bucket 2 technical range | `operational_rules.afternoon_arrival_buckets[1].time_from / operational_rules.afternoon_arrival_buckets[1].time_to` | `15:00 - 16:00` | Technical start_time values in this range are still used for write. | Edit the technical slot range; writes still use the exact technical start_time. |
| Afternoon bucket 2 spoken label | `operational_rules.afternoon_arrival_buckets[1].spoken_time_label` | `15:00` | This is the time the agent should say to the caller. | Edit what the agent should say to the caller for matching technical slots. |
| Afternoon bucket 3 enabled | `operational_rules.afternoon_arrival_buckets[2].enabled` | `true` | If enabled, matching technical slots get a separate spoken time label. | Set false to disable this spoken-time bucket without deleting it. |
| Afternoon bucket 3 service | `operational_rules.afternoon_arrival_buckets[2].service` | `skin` | Only this service uses the bucket; empty would mean all services. | Change the service key or leave empty/null to apply this bucket to all services. |
| Afternoon bucket 3 weekdays | `operational_rules.afternoon_arrival_buckets[2].weekdays` | `[2,3,4]` | Empty means every weekday; otherwise ISO weekdays 1=Monday through 7=Sunday. | Use ISO weekdays, e.g. [1,2,3] for Monday-Wednesday; leave empty for all days. |
| Afternoon bucket 3 technical range | `operational_rules.afternoon_arrival_buckets[2].time_from / operational_rules.afternoon_arrival_buckets[2].time_to` | `16:00 - 17:00` | Technical start_time values in this range are still used for write. | Edit the technical slot range; writes still use the exact technical start_time. |
| Afternoon bucket 3 spoken label | `operational_rules.afternoon_arrival_buckets[2].spoken_time_label` | `16:00` | This is the time the agent should say to the caller. | Edit what the agent should say to the caller for matching technical slots. |
| Afternoon bucket 4 enabled | `operational_rules.afternoon_arrival_buckets[3].enabled` | `true` | If enabled, matching technical slots get a separate spoken time label. | Set false to disable this spoken-time bucket without deleting it. |
| Afternoon bucket 4 service | `operational_rules.afternoon_arrival_buckets[3].service` | `skin` | Only this service uses the bucket; empty would mean all services. | Change the service key or leave empty/null to apply this bucket to all services. |
| Afternoon bucket 4 weekdays | `operational_rules.afternoon_arrival_buckets[3].weekdays` | `[5]` | Empty means every weekday; otherwise ISO weekdays 1=Monday through 7=Sunday. | Use ISO weekdays, e.g. [1,2,3] for Monday-Wednesday; leave empty for all days. |
| Afternoon bucket 4 technical range | `operational_rules.afternoon_arrival_buckets[3].time_from / operational_rules.afternoon_arrival_buckets[3].time_to` | `14:00 - 15:00` | Technical start_time values in this range are still used for write. | Edit the technical slot range; writes still use the exact technical start_time. |
| Afternoon bucket 4 spoken label | `operational_rules.afternoon_arrival_buckets[3].spoken_time_label` | `14:00` | This is the time the agent should say to the caller. | Edit what the agent should say to the caller for matching technical slots. |
| skin: agent may offer availability | `services.skin.agent_can_offer_availability` | `true` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| skin: agent may book | `services.skin.agent_can_book_finally` | `true` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| skin: main IDCINNOSTI | `services.skin.idcinnosti` | `null` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| skin: duration mode | `services.skin.duration.mode` | `schedule_interval` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| skin: duration minutes | `services.skin.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| skin: allowed doctors | `services.skin.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| skin: excluded doctors | `services.skin.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| skin: seasonality enabled | `services.skin.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| skin: seasonality range | `services.skin.seasonality.start / services.skin.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| skin: write strategy | `services.skin.write.strategy` | `main_row_plus_followup` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |
| skin: follow-up enabled | `services.skin.followup.create` | `true` | If true, write creates a related follow-up row. | Set false to stop creating related follow-up rows for this service. |
| skin: follow-up IDCINNOSTI | `services.skin.followup.idcinnosti` | `6` | IDCINNOSTI written into the related follow-up row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| skin: follow-up duration mode | `services.skin.followup.duration.mode` | `schedule_interval` | How the follow-up duration is computed. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| plasma: agent may offer availability | `services.plasma.agent_can_offer_availability` | `true` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| plasma: agent may book | `services.plasma.agent_can_book_finally` | `true` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| plasma: main IDCINNOSTI | `services.plasma.idcinnosti` | `3` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| plasma: duration mode | `services.plasma.duration.mode` | `fixed_minutes` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| plasma: duration minutes | `services.plasma.duration.minutes` | `30` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| plasma: allowed doctors | `services.plasma.allowed_doctor_ids` | `[8]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| plasma: excluded doctors | `services.plasma.excluded_doctor_ids` | `[2,4]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| plasma: seasonality enabled | `services.plasma.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| plasma: seasonality range | `services.plasma.seasonality.start / services.plasma.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| plasma: write strategy | `services.plasma.write.strategy` | `single_row` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |

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

| Bucket | Service | Weekdays | Technical time range | Spoken label | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | skin | 1, 2, 3, 4, 5 | 11:00 - 12:00 | 11:00 | enabled |
| 2 | skin | 1 | 15:00 - 16:00 | 15:00 | enabled |
| 3 | skin | 2, 3, 4 | 16:00 - 17:00 | 16:00 | enabled |
| 4 | skin | 5 | 14:00 - 15:00 | 14:00 | enabled |

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
