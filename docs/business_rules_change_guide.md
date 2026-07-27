# Business Rules Change Guide

This guide is for developers and fresh Codex agents changing production booking
rules.

## Source Of Truth

- Edit `config/business_rules.example.json` for repo defaults.
- Edit server-local `config/business_rules.local.json` for production overrides.
- Do not hand-edit `docs/current_business_rules.md`; regenerate it.

## Change Workflow

1. Find the requested behavior in `docs/current_business_rules.md`.
2. Use the `Config path` column to locate the JSON value.
3. Use the `How to change` column to understand the intended edit and required code/test implications.
4. Change the JSON config or, if the rule shape is new, add backend support first.
5. Regenerate the readable view:

```powershell
python scripts\render_business_rules.py
```

6. Validate and test:

```powershell
python scripts\render_business_rules.py --check
python -m unittest discover -s tests
```

## When Config Is Enough

Config-only edits are acceptable for existing rule paths, for example:

- adding or removing a doctor from `globally_excluded_doctor_ids`,
- changing a service `allowed_doctor_ids` list,
- changing the pre-08:00 cutoff,
- changing an afternoon bucket spoken label,
- enabling an already-modeled seasonality window.

## When Code Is Also Required

Code changes are required when the requested rule does not already have a config
path in the matrix, for example:

- a new type of capacity dependency,
- a new write strategy,
- a new API request field,
- a new service behavior that cannot be expressed by existing service fields,
- a new handoff side effect beyond summary generation.

For these changes, add or update:

- `config/business_rules.example.json`,
- `scripts/business_rules.py` validation/translation,
- backend behavior in availability/write/handoff,
- `scripts/render_business_rules.py` matrix rows,
- focused unit tests.

## Review Checklist

- `docs/current_business_rules.md` clearly explains the changed rule.
- The matrix has a row mapping the human rule to the config path.
- The API still returns technical `start_time` for writes.
- The agent-facing contract does not duplicate backend business rules.
- Tests cover both the enabled and disabled/negative path when practical.
