# Procedure: identity_verification_v1

Trigger: agent needs to work with existing appointments or write an appointment.

Task:

1. Use `patient_lookup`.
2. If caller phone is available, use it for the first lookup.
3. If `status=not_found`, ask for surname and date of birth, then call lookup again.
4. If `status=multiple_matches`, ask for the missing next identifying detail, typically date of birth first, then first name.
5. If `verification.verified=true`, identity is verified and existing appointments may be used.
6. Do not ask for the last 4 digits of the birth number. Last-4 verification is deprecated.
7. Repeat caller-provided personal data for confirmation before sending it to the tool.

Privacy:

Never read personal data from the database back to the caller. `patients` is only internal lookup state. Existing appointments may be discussed only after `verification.verified=true`.
