# Current Business Rules

<!-- Generated from config/business_rules*.json. Do not edit by hand. -->

Generated at: 2026-07-28T13:25:20
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
| plasma: agent may offer availability | `services.plasma.agent_can_offer_availability` | `false` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| plasma: agent may book | `services.plasma.agent_can_book_finally` | `false` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| plasma: main IDCINNOSTI | `services.plasma.idcinnosti` | `3` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| plasma: duration mode | `services.plasma.duration.mode` | `fixed_minutes` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| plasma: duration minutes | `services.plasma.duration.minutes` | `30` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| plasma: allowed doctors | `services.plasma.allowed_doctor_ids` | `[8]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| plasma: excluded doctors | `services.plasma.excluded_doctor_ids` | `[2,4]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| plasma: seasonality enabled | `services.plasma.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| plasma: seasonality range | `services.plasma.seasonality.start / services.plasma.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| plasma: write strategy | `services.plasma.write.strategy` | `single_row` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |
| dermatoscope_first: agent may offer availability | `services.dermatoscope_first.agent_can_offer_availability` | `false` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| dermatoscope_first: agent may book | `services.dermatoscope_first.agent_can_book_finally` | `false` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| dermatoscope_first: main IDCINNOSTI | `services.dermatoscope_first.idcinnosti` | `1` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| dermatoscope_first: duration mode | `services.dermatoscope_first.duration.mode` | `schedule_interval` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| dermatoscope_first: duration minutes | `services.dermatoscope_first.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| dermatoscope_first: allowed doctors | `services.dermatoscope_first.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| dermatoscope_first: excluded doctors | `services.dermatoscope_first.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| dermatoscope_first: seasonality enabled | `services.dermatoscope_first.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| dermatoscope_first: seasonality range | `services.dermatoscope_first.seasonality.start / services.dermatoscope_first.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| dermatoscope_first: write strategy | `services.dermatoscope_first.write.strategy` | `disabled_not_in_first_scope` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |
| dermatoscope_followup: agent may offer availability | `services.dermatoscope_followup.agent_can_offer_availability` | `false` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| dermatoscope_followup: agent may book | `services.dermatoscope_followup.agent_can_book_finally` | `false` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| dermatoscope_followup: main IDCINNOSTI | `services.dermatoscope_followup.idcinnosti` | `2` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| dermatoscope_followup: duration mode | `services.dermatoscope_followup.duration.mode` | `schedule_interval` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| dermatoscope_followup: duration minutes | `services.dermatoscope_followup.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| dermatoscope_followup: allowed doctors | `services.dermatoscope_followup.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| dermatoscope_followup: excluded doctors | `services.dermatoscope_followup.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| dermatoscope_followup: seasonality enabled | `services.dermatoscope_followup.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| dermatoscope_followup: seasonality range | `services.dermatoscope_followup.seasonality.start / services.dermatoscope_followup.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| dermatoscope_followup: write strategy | `services.dermatoscope_followup.write.strategy` | `disabled_not_in_first_scope` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |
| laser: agent may offer availability | `services.laser.agent_can_offer_availability` | `false` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| laser: agent may book | `services.laser.agent_can_book_finally` | `false` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| laser: main IDCINNOSTI | `services.laser.idcinnosti` | `3` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| laser: duration mode | `services.laser.duration.mode` | `fixed_minutes` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| laser: duration minutes | `services.laser.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| laser: allowed doctors | `services.laser.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| laser: excluded doctors | `services.laser.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| laser: seasonality enabled | `services.laser.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| laser: seasonality range | `services.laser.seasonality.start / services.laser.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| laser: write strategy | `services.laser.write.strategy` | `disabled_not_in_first_scope` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |
| regular_check: agent may offer availability | `services.regular_check.agent_can_offer_availability` | `false` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| regular_check: agent may book | `services.regular_check.agent_can_book_finally` | `false` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| regular_check: main IDCINNOSTI | `services.regular_check.idcinnosti` | `5` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| regular_check: duration mode | `services.regular_check.duration.mode` | `schedule_interval` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| regular_check: duration minutes | `services.regular_check.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| regular_check: allowed doctors | `services.regular_check.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| regular_check: excluded doctors | `services.regular_check.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| regular_check: seasonality enabled | `services.regular_check.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| regular_check: seasonality range | `services.regular_check.seasonality.start / services.regular_check.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| regular_check: write strategy | `services.regular_check.write.strategy` | `disabled_not_in_first_scope` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |
| dermatoscope_reservation: agent may offer availability | `services.dermatoscope_reservation.agent_can_offer_availability` | `false` | If false, the service is not accepted by doctor_availability. | Set false to make doctor_availability reject this service. |
| dermatoscope_reservation: agent may book | `services.dermatoscope_reservation.agent_can_book_finally` | `false` | If false, appointment_write rejects this service. | Set false to make appointment_write reject final booking for this service. |
| dermatoscope_reservation: main IDCINNOSTI | `services.dermatoscope_reservation.idcinnosti` | `6` | Value written into the main appointment row; null means default skin row. | Change only after confirming the Medicus IDCINNOSTI mapping and write shape. |
| dermatoscope_reservation: duration mode | `services.dermatoscope_reservation.duration.mode` | `schedule_interval` | schedule_interval follows the concrete Medicus schedule interval; fixed_minutes uses minutes. | Use schedule_interval to follow Medicus schedule blocks; use fixed_minutes with duration.minutes. |
| dermatoscope_reservation: duration minutes | `services.dermatoscope_reservation.duration.minutes` | `null` | Used only when duration mode needs a fixed minute value. | Set the fixed duration in minutes; ignored when mode follows schedule_interval. |
| dermatoscope_reservation: allowed doctors | `services.dermatoscope_reservation.allowed_doctor_ids` | `[]` | Empty means all globally allowed doctors unless service-excluded. | Add IDs to restrict this service to specific doctors; leave empty for all globally allowed doctors. |
| dermatoscope_reservation: excluded doctors | `services.dermatoscope_reservation.excluded_doctor_ids` | `[]` | Doctor IDs excluded only for this service. | Add IDs to block doctors only for this service. |
| dermatoscope_reservation: seasonality enabled | `services.dermatoscope_reservation.seasonality.enabled` | `false` | If true, availability outside the date range is hidden. | Set true to enforce the configured month-day range. |
| dermatoscope_reservation: seasonality range | `services.dermatoscope_reservation.seasonality.start / services.dermatoscope_reservation.seasonality.end` | `01-01 - 12-31` | Month-day range when the service is bookable. | Edit the MM-DD range and add/adjust tests for in-season and out-of-season availability. |
| dermatoscope_reservation: write strategy | `services.dermatoscope_reservation.write.strategy` | `disabled_not_in_first_scope` | Controls whether write creates one row or related rows. | Change only with matching appointment_write implementation and tests. |

## Doctors

- Globally allowed doctor IDs: `all unless excluded`
- Globally excluded doctor IDs: `4, 10`

| IDUZI | Name | Status | Note |
| --- | --- | --- | --- |
| 1 | Tereza Perez | active | Observed in DB schedule reports; not part of first production booking scope. |
| 2 | Rostislav Bednar | active | Active Bednar row used by availability/write revalidation. |
| 4 | Rostislav Bednar | excluded | Duplicate row without schedule contexts in tested window. |
| 8 | Maria Bartonova | active |  |
| 10 | Petra Pospisilova | excluded | No schedule contexts in tested window. |
| 11 | Dusana Selecka | active |  |
| 12 | Marta Skolarova | active |  |
| 13 | Zuzana Slosarova | active | Schedule interval may vary by day/context. |
| 15 | Filip Ferencz | active |  |

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
- Agent may offer availability: `False`
- Agent may book finally: `False`
- Main IDCINNOSTI: `3`
- Duration: `fixed_minutes` / `30` minutes
- Allowed doctor IDs: `8`
- Excluded doctor IDs: `2, 4`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `single_row`

### dermatoscope_first

- Label: Dermatoskopie prvni
- Agent may offer availability: `False`
- Agent may book finally: `False`
- Main IDCINNOSTI: `1`
- Duration: `schedule_interval`
- Allowed doctor IDs: `all unless excluded`
- Excluded doctor IDs: `all unless excluded`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `disabled_not_in_first_scope`

### dermatoscope_followup

- Label: Dermatoskopie kontrola
- Agent may offer availability: `False`
- Agent may book finally: `False`
- Main IDCINNOSTI: `2`
- Duration: `schedule_interval`
- Allowed doctor IDs: `all unless excluded`
- Excluded doctor IDs: `all unless excluded`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `disabled_not_in_first_scope`

### laser

- Label: Laserove vykony
- Agent may offer availability: `False`
- Agent may book finally: `False`
- Main IDCINNOSTI: `3`
- Duration: `fixed_minutes`
- Allowed doctor IDs: `all unless excluded`
- Excluded doctor IDs: `all unless excluded`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `disabled_not_in_first_scope`

### regular_check

- Label: Kontrola
- Agent may offer availability: `False`
- Agent may book finally: `False`
- Main IDCINNOSTI: `5`
- Duration: `schedule_interval`
- Allowed doctor IDs: `all unless excluded`
- Excluded doctor IDs: `all unless excluded`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `disabled_not_in_first_scope`

### dermatoscope_reservation

- Label: Rezervace dermatoskopu
- Agent may offer availability: `False`
- Agent may book finally: `False`
- Main IDCINNOSTI: `6`
- Duration: `schedule_interval`
- Allowed doctor IDs: `all unless excluded`
- Excluded doctor IDs: `all unless excluded`
- Seasonality: `disabled` `01-01` to `12-31`
- Write strategy: `disabled_not_in_first_scope`
