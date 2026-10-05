# Zapojení handoff_summary v ElevenLabs

Aktualizace 5. 10. 2026: uživatel potvrdil uložení toolu a publikování promptu.
Browser kontrola potvrdila správná povinná pole toolu (a opravila popis shrnutí),
nový handoff blok v promptu bez current_step a disabled Publish po publikaci.
Níže uvedené kroky jsou nyní hotové; zbývá hlasový test aktuální verze.

Pouze handoff; ostatní v2 schémata a celý kandidát promptu zatím nezapínat.
Operator inbox i Medicus durable handoff jsou nasazené; uživatel potvrdil
hlavičku a request_id u handoff_summary. Skutečný hlasový test ještě zbývá.

## Zbývající změna podle dodaného exportu

Export verze agtvrsn_0801m3yf865genxs8xkf2jpw361e již potvrzuje hlavičky
všech pěti toolů i request_id. Tyto hotové kroky znovu neprovádět.
V handoff_summary ale stále obsahuje current_step, který backend nečte.
Pro tuto etapu použít `tool_patches/handoff_summary.current_export.patch.json`:

- Odstranit current_step.
- Přidat povinný string conversation_summary, zdroj LLM prompt, s popisem
  z fragmentu: pouze dostupný kontext, bez dalších otázek před přepojením,
  bez RČ, data narození, IDPAC a ověřovacích tokenů.
- Přidat povinný string recommended_next_step, zdroj LLM prompt, s popisem
  z fragmentu: další krok personálu bez slibu rezervace nebo úspěšného přepojení.
- Volitelně přidat string intent podle fragmentu.
- Nahradit popis toolu a těla podle fragmentu; zachovat mode, reason,
  request_id, caller_phone, URL, autentizaci, hlavičky a response assignments.

Fragment není celá definice toolu: nenahradit jím celý tool ani api_schema.
Současný nasazený backend tato pole podporuje. Ostatní čtyři v2 kontrakty
vyžadují společné nasazení; tento krok je neaktivuje.
Po změně ověřit nový export a skutečný hovor s dohledatelným shrnutím v Operatoru.

### Současně opravit jednu instrukci produkčního promptu

Dodané znění promptu má v sekci `# HANDOFF` stále větu
„Do current_step napiš, kde hovor skončil a co má personál udělat dál.“
Nahradit ji následujícím blokem; ostatní instrukce k okamžitému předání zachovat:

```text
Do conversation_summary stručně napiš původní požadavek, známé preference a dosavadní průběh hovoru.
Do recommended_next_step napiš, co má personál udělat dál.
Použij pouze již známé informace; kvůli shrnutí nepokládej před přepojením další otázky. Neuváděj RČ, datum narození, IDPAC ani ověřovací tokeny.
Každému novému požadavku přiděl request_id; při technickém opakování stejného požadavku zachovej přesně stejné request_id i obsah.
stored=true potvrzuje pouze uložení požadavku, nikoli převzetí personálem nebo úspěšné přepojení. Samotné ok=true nestačí jako potvrzení uložení.
Pokud uložení selže nebo stored=false, neslibuj, že je zpětné zavolání zajištěné; pokus se o živé přepojení. Chyba shrnutí nesmí zabránit požadovanému přepojení na člověka.
```

Celý v2 prompt se v tomto kroku nepublikuje. Výše je pouze oprava konkrétního
handoff kontraktu proti skutečně dodanému znění; dostupnost a rezervace mají
samostatné dosud nedokončené podmínky nasazení.

Následující část zachycuje i již dokončené historické kroky.

## Navazující hlavičky pro časový kontext

Uživatel 2. 10. potvrdil, že X-Conversation-Id má zatím pouze handoff_summary.
Stejnou hlavičku je třeba přidat také do agent_capabilities,
doctor_availability, patient_lookup a appointment_write. Zdroj Dynamic variable,
hodnota system__conversation_id, stejným postupem níže. Ostatní pole, URL,
Bearer connection a response assignments při tomto kroku neměnit.

Backendový kandidát nyní zaznamenává první autentizovaný požadavek hovoru do
existujícího chráněného SQLite store i při vypnutém staff approval. Dostupnost
pak počítá hodinový předstih od tohoto serverového času, ne od každého hledání
znovu. Není to přesný okamžik přijetí telefonního hovoru. Bez hlavičky zůstává
konzervativní výpočet od aktuálního požadavku. Nevyřešené šablony v hlavičce
odmítá; chybějící již zřízený store automaticky nenahrazuje novým.
Nasazeno 2. 10. z release/call-context-v2, f7c7c28; 26 cílených testů prošlo
lokálně i na serveru. Živá dvojice capabilities/availability zachovala first_seen,
fallback bez hlavičky funguje. Důkazy v chráněném state/call-context-v2.
Uživatel následně potvrdil „hotovo, přidáno u všech toolů“. Read-only kontrola
call_anchors za poslední hodinu zatím neobsahuje žádný nesyntetický hovor;
živý hlasový test tedy ještě není doložen. Tyto hlavičky samy
neaktivují schvalování, zápisy ani nové v2 schéma těla nástrojů.

## Nastavení handoff_summary

1. Otevřít existující tool `handoff_summary` a zachovat jeho URL, ID a Bearer
   auth connection. Do request headers přidat `X-Conversation-Id`; jako zdroj
   vybrat **Dynamic variable**, hodnotu `system__conversation_id`.
   Nepoužívat statický text `{{system__conversation_id}}`.
2. Do JSON body přidat povinný string `request_id`, zdroj LLM prompt:
   `Stable unique ID for this staff request within this call, without spaces.
   Reuse exactly the same ID and request content for technical retries.
   Use a new ID only for a genuinely new staff request.`
3. Zachovat/použít `mode` (live_transfer nebo callback), `reason`,
   `conversation_summary`, `recommended_next_step`; ostatní známý kontext je
   volitelný. Aktuální pole jsou v tool_patches/handoff_summary.current_export.patch.json.
   Nepřidávat interní IDPAC ani RČ do volného textu.
4. Při úpravě přes REST API je hodnota této hlavičky objekt:

   ```json
   {"X-Conversation-Id": {"variable_name": "system__conversation_id"}}
   ```

   Jde jen o položku mapy `api_schema.request_headers`, nikoli náhradu celého
   toolu. Starší UI export v backup používá jinou strukturu; nepřevádět ho
   naslepo do aktuálního REST API a neodstraňovat existující autentizaci.
5. Uložit změnu a respektovat případnou výzvu ElevenLabs k publikování.
   Teprve živý test prokáže použitou konfiguraci, samotné uložení nestačí.
6. Po připravení backendu ověřit kontrolovaným hovorem: backend dostane
   skutečné ID stejného hovoru v ElevenLabs a vrátí `stored=true`;
   v Operatoru vznikne shrnutí u tohoto hovoru. Opakování stejného požadavku
   zachová handoff_id. Ověřit také zpětné volání a okamžitý transfer odděleně.

Instrukce agentovi pro tento dílčí rollout:

> When staff assistance is needed, call handoff_summary with the available
> context and a stable request_id. Reuse the same ID and identical content on
> technical retries. stored=true confirms that the request was saved, not that
> staff have read it, received an SMS, or answered a transfer. If persistence
> fails or stored=false, do not promise a callback has been arranged; attempt
> live transfer. When the caller asks for a person, do not ask extra questions
> before transferring. The summary tool does not itself transfer the call.

Ověřeno v dokumentaci 2. 10. 2026:
- [Systémové dynamické proměnné](https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables)
- [Oficiální SDK: reference dynamické proměnné](https://github.com/elevenlabs/elevenlabs-python/blob/main/src/elevenlabs/types/conv_ai_dynamic_variable.py)
- [Oficiální Architect: typované hlavičky](https://github.com/elevenlabs/plugin/blob/main/architect/skills/architect-migrate-from-competitor/SKILL.md)

Živá konfigurace tohoto agenta zatím nebyla ověřena. Browser tool selhává při
inicializaci (chybějící kernel assets), ElevenLabs connector není dostupný.
