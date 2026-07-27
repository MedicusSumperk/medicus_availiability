# Current Business Rules

<!-- Generated from config/business_rules*.json. Do not edit by hand. -->

Generated at: 2026-07-27T13:37:17
Rules version: `2026-07-production-v1`

## Validation

- OK: config is structurally valid.

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
