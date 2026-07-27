# ElevenLabs Agent Artifacts

Tahle složka drží verzovatelné artefakty pro ElevenLabs agenta Dermatologického
střediska Šumperk.

Aktuální cíl:

- nahrát nový state-first branch do ElevenLabs,
- ověřit tool calls proti Medicus API,
- ověřit decision tree v hlasovém testu,
- ověřit, jestli critical state bezpečně drží dynamic variables, nebo jestli ho
  musí řídit n8n.

## Aktuální Upload Artefakt

```text
branches/sumper_recepcni_v3_state_first_upload.json
```

Poznámky k uploadu:

```text
branches/sumper_recepcni_v3_state_first_upload_notes.md
```

V upload JSONu jsou zachované aktuální tooly:

- `doctor_availability`
- `patient_lookup`
- `appointment_write`
- `end_call`

Upload JSON má:

- kratší state-first prompt,
- explicitní tool rules,
- first message pro Dermatologické středisko Šumperk,
- flattened dynamic variable placeholders podle
  `../elevenlabs_flat_dynamic_variables_v1.json`,
- zachované hardcoded `https://...trycloudflare.com` tool URL ze zdrojového
  exportu.

## Procedures

Procedures jsou zatím drženy jako markdown artefakty, protože ElevenLabs
Procedures jsou alpha feature a export/import schema chceme ověřit živě v UI.

Import pack:

```text
procedures/medicus_procedures_import_v1.md
```

Jednotlivé návrhy:

- `procedures/intent_triage_v1.md`
- `procedures/patient_card_gate_v1.md`
- `procedures/availability_lookup_v1.md`
- `procedures/identity_verification_v1.md`
- `procedures/appointment_write_v1.md`
- `procedures/handoff_v1.md`

## Testovací Dokumentace

Hlavní plán:

```text
../elevenlabs_agent_test_plan_v1_cs.md
```

Krátký checklist pro den živého testu:

```text
../elevenlabs_live_test_run_sheet_v1_cs.md
```

Vyplnitelný log pro konkrétní test běh:

```text
../elevenlabs_live_test_log_template_v1_cs.md
```

State a assignment matice:

```text
../elevenlabs_state_assignment_test_matrix_v1_cs.md
```

Decision tree:

```text
../elevenlabs_agent_decision_tree_v1_cs.md
```

## Co Je Potvrzené

- Medicus API endpointy a jejich kontrakt jsou popsané v `../local_api.md`.
- Upload JSON obsahuje 3 Medicus tooly a `end_call`.
- Prompt v upload JSONu říká agentovi, kdy použít `doctor_availability`,
  `patient_lookup` a `appointment_write`.
- Testovací dokumentace pokrývá API smoke, ElevenLabs tool payloady, dynamic
  variables, decision tree, write flow a safety/privacy.

## Co Není Potvrzené

- Jestli ElevenLabs dynamic variables v našem workspace bezpečně podporují nested
  object state.
- Jestli assignments umí ukládat array/object hodnoty s `preserve_native_type`.
- Jestli flattened dynamic variables půjdou během hovoru spolehlivě aktualizovat
  přes tool assignments, nebo bude potřeba n8n-managed state.
- Jestli Procedures import v UI vytvoří použitelnou a exportovatelnou konfiguraci.
- Jestli agent v živém hlasovém testu udrží decision tree i po odbočkách,
  odmítnutých termínech a opakovaných lookupech.

## Doporučený Další Postup

1. Nahrát `branches/sumper_recepcni_v3_state_first_upload.json` do nového
   ElevenLabs branche.
2. Zkontrolovat a případně aktualizovat aktuální tool URL.
3. Importovat nebo ručně přepsat Procedures z import packu.
4. Nastavit canary dynamic variables podle
   `../elevenlabs_state_assignment_test_matrix_v1_cs.md`.
5. Projít `../elevenlabs_live_test_run_sheet_v1_cs.md`.
6. Výsledky zapsat do kopie
   `../elevenlabs_live_test_log_template_v1_cs.md`.

Bez potvrzeného state mechanismu není splněný cíl, že agent nedrží kritické
informace jen v paměti modelu.
