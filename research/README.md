# Research

This directory keeps important reverse-engineering notes that inform runtime
behavior but should not sit in the active API documentation path.

Current groups:

```text
research/db-mapping/
  Medicus / Firebird table mapping, appointment type mapping, write-path
  findings, and schedule interval findings.

research/agent_context.md
  Legacy pre-call context notes for the diagnostic context builder.
```

When a research finding becomes an active backend rule, encode it in
`config/business_rules.example.json`, regenerate `docs/current_business_rules.md`,
and update tests.
