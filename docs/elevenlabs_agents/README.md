# ElevenLabs Agent JSON Artifacts

Tahle složka je připravená pro budoucí JSON exporty celého ElevenLabs agenta.

Aktuálně sem agent config neukládáme, protože export ještě nebyl předaný a mohou
v něm být hodnoty specifické pro ElevenLabs workspace. Jakmile bude export
k dispozici, zacházet s ním podobně jako s kódem:

- jeden JSON artefakt pro konkrétní agent verzi,
- změny dělat přes branch/PR,
- před commitem zkontrolovat secrets, auth connections, telefonní čísla a
  workspace-specific IDs,
- lidský popis chování držet v `../elevenlabs_agent_behavior_cs.md`,
- tool JSON artefakty držet odděleně v `../elevenlabs_tools/`.

## Co podle dokumentace potvrdit

- CLI umí držet agenty jako konfigurační soubory a pushovat je zpět do
  ElevenLabs.
- Workflows jsou součástí `conversation_config.workflow`, takže jsou také
  verzovatelné v agent JSON konfiguraci.
- Procedures jsou součástí agent konfigurace a verzují se spolu s publikovanou
  verzí agenta, ale jsou zatím Alpha.

## Doporučená budoucí struktura

```text
docs/elevenlabs_agents/
  README.md
  medicus_reception_agent_v1.json
  procedures/
    identity_verification_v1.md
    availability_lookup_v1.md
    appointment_write_v1.md
    human_handoff_v1.md
```
