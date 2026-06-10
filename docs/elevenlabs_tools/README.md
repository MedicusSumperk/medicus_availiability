# ElevenLabs Tool JSON Artifacts

Tahle složka drží samostatné JSON mode exporty ElevenLabs toolů.

Lidsky čitelný návod, popisy parametrů, pravidla použití, dynamic variables a
smoke testy jsou v `../elevenlabs_tool_config_cs.md`.

## URL policy pro MVP

Aktuálně potvrzeně prochází save v ElevenLabs s natvrdo vloženou validní
`https://...` URL.

Env variable syntaxe k ověření po získání práv:

```text
https://{{system__env_medicus_api_host}}/book-appointment
```

Název env proměnné musí začínat malým písmenem a smí obsahovat jen malá písmena,
čísla a podtržítka. URL musí začínat `https://` před env placeholderem, takže
env proměnná má nést host, ne celý base URL včetně protokolu.

## Artefakty

- `appointment_write_v1.json` - zápis, zrušení a přesun termínu přes
  `/book-appointment`.
