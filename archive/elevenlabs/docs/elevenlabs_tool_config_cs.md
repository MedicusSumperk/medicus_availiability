# ElevenLabs Tool Configuration CS

Verze: 1.1
Datum: 2026-06-18
Stav: pracovnĂ­ verze pro nastavenĂ­ ElevenLabs toolĹŻ vÄŤetnÄ› v4 kalibrace

Tento dokument shrnuje informace potĹ™ebnĂ© pro nastavenĂ­ toolĹŻ pĹ™Ă­mo v
ElevenLabs. ChovĂˇnĂ­ agenta a pravidla vyhodnocovĂˇnĂ­ jsou podrobnÄ›ji popsanĂ©
v `docs/elevenlabs_agent_behavior_cs.md`.

KompaktnĂ­ copy-ready seed pro dynamic variables je v
`docs/elevenlabs_dynamic_variables_compact_v0.json`. DetailnĂ­ referenÄŤnĂ­ katalog
pro n8n, prompt design a audit je v `docs/elevenlabs_dynamic_variables_v0.json`.
NavrĹľenĂ˝ state-first objekt pro dalĹˇĂ­ iteraci je v
`docs/elevenlabs_dynamic_state_v1.json`.
NĂˇvrh konkrĂ©tnĂ­ch dynamic variable assignments je v
`docs/elevenlabs_dynamic_assignments_v1_cs.md`.
AktuĂˇlnĂ­ beta-pragmatickĂ˝ flattened state seed je v
`docs/elevenlabs_flat_dynamic_variables_v1.json`.
PraktickĂˇ assignment matice pro ĹľivĂ© ovÄ›Ĺ™enĂ­ response paths, canary variables a
fallbacku pĹ™es n8n je v `docs/elevenlabs_state_assignment_test_matrix_v1_cs.md`.
JSON mode export aktuĂˇlnÄ› nastavenĂ©ho toolu `appointment_write` je v
`docs/elevenlabs_tools/appointment_write_v1.json`.
AktuĂˇlnĂ­ upload-ready agent JSON a souvisejĂ­cĂ­ branch artefakty jsou v
`docs/elevenlabs_agents/`.

Ĺ˝ivĂ˝ test po nastavenĂ­ toolĹŻ vĂ©st podle:

```text
docs/elevenlabs_agent_test_plan_v1_cs.md
docs/elevenlabs_live_test_run_sheet_v1_cs.md
docs/elevenlabs_live_test_log_template_v1_cs.md
```

## SpoleÄŤnĂ© nastavenĂ­

AktuĂˇlnĂ­ testovacĂ­ architektura:

```text
ElevenLabs agent
-> webhook tool
-> trycloudflare nebo named Cloudflare Tunnel URL
-> lokĂˇlnĂ­ FastAPI
-> Firebird / Medicus read-only logika
```

PĹ™ed testem doplnit:

```text
medicus_base_url=https://DOPLNIT-AKTUALNI-URL.trycloudflare.com
```

Endpointy:

```text
GET  {medicus_base_url}/health
POST {medicus_base_url}/doctor-availability
POST {medicus_base_url}/patient-lookup
POST {medicus_base_url}/book-appointment
```

PoznĂˇmka k ElevenLabs URL fields:

- Save aktuĂˇlnÄ› potvrzenÄ› prochĂˇzĂ­ s natvrdo vloĹľenou validnĂ­ `https://...`
  URL.
- Env variable syntaxe mĂˇ obecnĂ˝ tvar `{{system__env_<label>}}`.
- NĂˇzev env promÄ›nnĂ© musĂ­ zaÄŤĂ­nat malĂ˝m pĂ­smenem a smĂ­ obsahovat jen malĂˇ
  pĂ­smena, ÄŤĂ­sla a podtrĹľĂ­tka.
- URL musĂ­ zaÄŤĂ­nat `https://` jeĹˇtÄ› pĹ™ed env promÄ›nnou. Env promÄ›nnĂˇ tedy nemĂˇ
  Ĺ™Ă­dit protokol. Pro server tool URL je vhodnÄ›jĹˇĂ­ host-only promÄ›nnĂˇ, napĹ™Ă­klad
  `medicus_api_host`, a URL `https://{{system__env_medicus_api_host}}/...`.
- PouĹľitĂ­ env promÄ›nnĂ© pĹ™Ă­mo v naĹˇem workspace zatĂ­m nenĂ­ potvrzenĂ©, protoĹľe
  editace env variables vyĹľaduje prĂˇva.
- Pro MVP tedy v JSON artefaktech drĹľet save-ready hardcoded tunnel URL a env
  variantu ovÄ›Ĺ™it samostatnÄ›, aĹľ budou prĂˇva.

AktuĂˇlnÄ› pouĹľĂ­vat jen dva read-only tooly:

- `doctor_availability`
- `patient_lookup`

ZapisovacĂ­ tool pouĹľĂ­vat aĹľ po explicitnĂ­m zapnutĂ­ v lokĂˇlnĂ­m API configu:

- `appointment_write`

`appointment_write` volĂˇ endpoint `/book-appointment` a podporuje akce
`create`, `cancel` a `reschedule`.

Pokud je v API nastaven bearer token, kaĹľdĂ˝ webhook request musĂ­ posĂ­lat:

```http
Authorization: Bearer <token>
```

## Dynamic variables v0

Dynamic variables mohou bĂ˝t statickĂ© v agentovi, pĹ™edanĂ© z n8n workflow,
zĂ­skanĂ© z ElevenLabs call metadata nebo naÄŤtenĂ© dynamicky pĹ™es webhook.

| NĂˇzev | Typ | Zdroj | PovinnĂ© | PouĹľitĂ­ |
| --- | --- | --- | --- | --- |
| `medicus_base_url` | string | static / n8n workflow | ano | AktuĂˇlnĂ­ veĹ™ejnĂˇ URL API pro textovĂ© nastavenĂ­ a handoff. Pro trycloudflare se po restartu mÄ›nĂ­. |
| `medicus_api_host` | string | environment | volitelnĂ© | Host-only varianta pro ElevenLabs env URL, napĹ™Ă­klad `abc.trycloudflare.com`. PouĹľĂ­t jako `https://{{system__env_medicus_api_host}}/...`, aĹľ budou prĂˇva k env variables. |
| `caller_phone` | string | ElevenLabs call metadata / webhook / n8n trigger | ne | Telefon z triggeru hovoru. NepouĹľĂ­vat pro turn-0 lookup; pouĹľĂ­t aĹľ jako prvnĂ­ Ăşdaj v identity gate pĹ™i rezervaci, zmÄ›nÄ›, zruĹˇenĂ­ nebo dotazu na existujĂ­cĂ­ termĂ­ny. |
| `patient_lookup_status` | string | tool assignment | ano | PoslednĂ­ `patient_lookup.status`, napĹ™Ă­klad `not_started`, `needs_verification`, `verified`, `not_found`. |
| `patient_verified` | boolean | tool assignment | ano | HlavnĂ­ gate pro sdÄ›lenĂ­ appointments a write tool. |
| `patient_idpac` | number | tool assignment | ano | TechnickĂ© ID ovÄ›Ĺ™ovanĂ©ho pacienta pro write tool; pouĹľĂ­t jen pĹ™i `patient_verified=true`. |
| `patient_appointments_json` | string | tool assignment | doporuÄŤeno | JSON string budoucĂ­ch appointments po ovÄ›Ĺ™enĂ­ pacienta. |
| `availability_options_json` | string | tool assignment | doporuÄŤeno | JSON string poslednĂ­ch nabĂ­dnutĂ˝ch availability options. |
| `availability_doctor_match_type` | string | tool assignment | doporuÄŤeno | `exact`, `partial`, `not_found`, `ambiguous` atd.; hlĂ­dĂˇ tvrzenĂ­ o konkrĂ©tnĂ­m lĂ©kaĹ™i. |
| `write_ok` | boolean | tool assignment | ano | HlavnĂ­ gate pro potvrzenĂ­ write akce. |
| `write_status` | string | tool assignment | ano | `created`, `cancelled`, `rescheduled`, nebo dĹŻvod selhĂˇnĂ­. |
| `handoff_required` | boolean | prompt / workflow | doporuÄŤeno | Stav, Ĺľe mĂˇ bĂ˝t hovor pĹ™edĂˇn ĹľivĂ© osobÄ›. |
| `handoff_reason` | string | prompt / workflow | doporuÄŤeno | DĹŻvod handoffu. |
| `medicus_state` | object | legacy / budoucĂ­ n8n workflow | ne | StarĹˇĂ­ nĂˇvrh jednoho objektu pro decision tree. Pro beta preferovat flattened variables. |
| `caller_state` | object | legacy nĂˇvrh | ne | StarĹˇĂ­ rozdÄ›lenĂ˝ stav volajĂ­cĂ­ho. Pro dalĹˇĂ­ iteraci preferovat sjednocenĂ˝ `medicus_state`. |
| `availability_state` | object | legacy nĂˇvrh | ne | StarĹˇĂ­ rozdÄ›lenĂ˝ stav dostupnosti. Pro dalĹˇĂ­ iteraci preferovat sjednocenĂ˝ `medicus_state`. |
| `clinic_name` | string | static | ano | PĹ™edstavenĂ­ agenta. VĂ˝chozĂ­: DermatologickĂ© stĹ™edisko Ĺ umperk. |
| `clinic_address` | string | static | ne | OdpovÄ›di na zĂˇkladnĂ­ dotazy o adrese. Hodnota zatĂ­m doplnit. |
| `clinic_opening_hours` | string/object | static | ne | OdpovÄ›di na dotazy k otevĂ­racĂ­ dobÄ›. Hodnota zatĂ­m doplnit. |
| `clinic_phone` | string | static | ne | Kontakt na stĹ™edisko nebo Ĺľivou recepci. Hodnota zatĂ­m doplnit. |
| `handoff_phone` | string | static | ne | Telefon pro pĹ™esmÄ›rovĂˇnĂ­ vybranĂ˝ch poĹľadavkĹŻ, pokud bude potĹ™eba. |
| `doctor_list` | array/object | static / n8n workflow / webhook | doporuÄŤeno | Seznam lĂ©kaĹ™ĹŻ pro obecnou znalost agenta; pro API stĂˇle posĂ­lat `doctor_name`, ne `doctor_id`. |
| `procedure_list` | array/object | static / n8n workflow / webhook | doporuÄŤeno | Seznam podporovanĂ˝ch a nepodporovanĂ˝ch sluĹľeb, aby agent zbyteÄŤnÄ› nevolal tool. |
| `transfer_reasons` | array | static | doporuÄŤeno | DĹŻvody pro pĹ™edĂˇnĂ­ ĹľivĂ© osobÄ›. |
| `agent_version` | string | static | ne | Identifikace testovanĂ© verze promptu/tool nastavenĂ­. |

PracovnĂ­ doporuÄŤenĂ­:

- `doctor_list` a `procedure_list` zatĂ­m drĹľet jako static nebo n8n-managed
  dynamic variables.
- `medicus_base_url` pro MVP zatĂ­m drĹľet jako hardcoded `https://...` URL v
  kaĹľdĂ©m toolu.
- Env variantu ovÄ›Ĺ™it jako `medicus_api_host`, ne jako full base URL, protoĹľe
  ElevenLabs URL validĂˇtor vyĹľaduje `https://` pĹ™ed placeholderem.
- Pro beta preferovat flattened variables, protoĹľe odpovĂ­dajĂ­ potvrzenĂ˝m typĹŻm
  dynamic variables v ElevenLabs.
- Jeden sjednocenĂ˝ objekt `medicus_state` drĹľet jako budoucĂ­/n8n variantu, ne jako
  prvnĂ­ dashboard implementaci.
- `caller_state` a `availability_state` brĂˇt jako starĹˇĂ­ rozdÄ›lenĂ˝ nĂˇvrh, ne jako
  cĂ­lovĂ˝ state-first model.
- NedÄ›lat pro nÄ› samostatnĂ˝ API tool, pokud nejde o data, kterĂˇ se ÄŤasto mÄ›nĂ­
  bÄ›hem dne.
- API dostupnosti mĂˇ stĂˇle rozhodovat podle reĂˇlnĂ© DB dostupnosti, ne podle
  statickĂ©ho seznamu v promptu.
- Pro reĂˇlnĂ© ElevenLabs dynamic variables pouĹľĂ­t hlavnÄ› kompaktnĂ­ enum soubor
  `docs/elevenlabs_dynamic_variables_compact_v0.json`.
- DetailnĂ­ katalog `docs/elevenlabs_dynamic_variables_v0.json` je spĂ­Ĺˇ pro n8n
  orkestraci, internĂ­ pravidla a audit, ne pro celĂ˝ prompt context.
- NĂ­Ĺľe uvedenĂ© `procedure_list` a `doctor_list` jsou jen zkrĂˇcenĂ© orientaÄŤnĂ­
  ukĂˇzky.

## ZkrĂˇcenĂˇ ukĂˇzka `procedure_list` v0

```json
[
  {
    "key": "skin",
    "spoken_names": ["koĹľnĂ­ vyĹˇetĹ™enĂ­", "vyĹˇetĹ™enĂ­ kĹŻĹľe", "kontrola kĹŻĹľe"],
    "availability_service": "skin",
    "agent_can_offer_availability": true,
    "agent_can_book_finally": true,
    "notes": "V1 podporuje hledĂˇnĂ­ dostupnosti i zĂˇpis pĹ™es appointment_write po ovÄ›Ĺ™enĂ­ pacienta a potvrzenĂ­ termĂ­nu."
  },
  {
    "key": "plasma",
    "spoken_names": ["plazma", "plazmovĂ© oĹˇetĹ™enĂ­"],
    "availability_service": "plasma",
    "agent_can_offer_availability": true,
    "agent_can_book_finally": true,
    "notes": "PouĹľĂ­t pouze kdyĹľ pacient vĂ˝slovnÄ› poĹľaduje plazmu."
  },
  {
    "key": "dermatoscope",
    "spoken_names": ["dermatoskop", "sken znamĂ©nek", "vyĹˇetĹ™enĂ­ znamĂ©nek"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "notes": "SamostatnĂ˝ dermatoskop nenĂ­ ve V1 podporovanĂ˝ jako bookovatelnĂˇ sluĹľba."
  },
  {
    "key": "test_results",
    "spoken_names": ["vĂ˝sledky", "vĂ˝sledky testĹŻ", "laboratornĂ­ vĂ˝sledky"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "transfer_to_human": true
  },
  {
    "key": "prescription",
    "spoken_names": ["recept", "pĹ™edpis", "lĂ©ky"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "transfer_to_human": true
  },
  {
    "key": "personal_data_change",
    "spoken_names": ["zmÄ›na ĂşdajĹŻ", "zmÄ›nit telefon", "zmÄ›nit adresu"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "transfer_to_human": true
  }
]
```

## ZkrĂˇcenĂˇ ukĂˇzka `doctor_list` v0

Tento seznam je pro orientaci agenta a pĹ™Ă­padnou vĂ˝slovnost. API mĂˇ pro
dostupnost stĂˇle dostat pĹ™irozenĂ˝ text v `doctor_name`.

```json
[
  {
    "display_name": "doktorka BartoĹovĂˇ",
    "doctor_name_for_api": "Bartonova",
    "known_services": ["skin", "plasma"],
    "notes": "Plazma u BartoĹovĂ© je pracovnĂ­ pravidlo k dalĹˇĂ­mu ovÄ›Ĺ™enĂ­."
  },
  {
    "display_name": "doktor BednĂˇĹ™",
    "doctor_name_for_api": "Bednar",
    "known_services": ["skin"],
    "notes": "BednĂˇĹ™ nedÄ›lĂˇ dermatoskop; duplicitnĂ­ DB ID je Ĺ™eĹˇenĂ© lokĂˇlnĂ­m configem. Agent neposĂ­lĂˇ doctor_id."
  }
]
```

Seznam doplnit podle potvrzenĂ˝ch lĂ©kaĹ™ĹŻ a provoznĂ­ch pravidel. NepouĹľĂ­vat jako
nĂˇhradu za dostupnost z API.

## Tool `doctor_availability`

### ZĂˇklad

Name:

```text
doctor_availability
```

Method:

```text
POST
```

URL:

```text
https://DOPLNIT-AKTUALNI-URL.trycloudflare.com/doctor-availability
```

Tool description:

```text
VyhledĂˇ reĂˇlnĂ© dostupnĂ© termĂ­ny v Medicus databĂˇzi. PouĹľij tento tool vĹľdy,
kdyĹľ volajĂ­cĂ­ hledĂˇ termĂ­n nebo zmÄ›nĂ­ lĂ©kaĹ™e, sluĹľbu, datum, obdobĂ­, den v
tĂ˝dnu nebo preferovanĂ˝ ÄŤas. Dostupnost neodhaduj z pamÄ›ti ani ze starĹˇĂ­ho
vĂ˝sledku. Pokud volajĂ­cĂ­ uvede konkrĂ©tnĂ­ho lĂ©kaĹ™e, poĹˇli jeho jmĂ©no jako
doctor_name a neurÄŤuj doctor_id. KdyĹľ volajĂ­cĂ­ odmĂ­tne vĹˇechny vrĂˇcenĂ© termĂ­ny,
dalĹˇĂ­ volĂˇnĂ­ nesmĂ­ bĂ˝t stejnĂ© jako pĹ™edchozĂ­. Nevracej odmĂ­tnutĂ© sloty jako novĂ©
moĹľnosti. Pokud volajĂ­cĂ­ chce dalĹˇĂ­ termĂ­ny bez upĹ™esnÄ›nĂ­, nastav date_from na
den po nejpozdÄ›jĹˇĂ­m odmĂ­tnutĂ©m datu, nebo zmÄ›Ĺ ÄŤasovĂ˝ filtr podle novĂ©
preference.
```

Body description:

```text
VyplĹ pouze parametry, kterĂ© vyplĂ˝vajĂ­ z aktuĂˇlnĂ­ konverzace nebo jsou pevnÄ›
nastavenĂ©. SluĹľbu nastav na skin pro koĹľnĂ­ vyĹˇetĹ™enĂ­ a na plasma pouze pokud
volajĂ­cĂ­ vĂ˝slovnÄ› poĹľaduje plazmu. LĂ©kaĹ™e pĹ™edĂˇvej jako pĹ™irozenÄ› Ĺ™eÄŤenĂ© jmĂ©no
nebo pĹ™Ă­jmenĂ­ v doctor_name. Datum posĂ­lej ve formĂˇtu YYYY-MM-DD, ÄŤas ve formĂˇtu
HH:MM. NevyplĹuj doctor_id. PevnÄ› nastav limit=3 a compact=true. PĹ™i opakovanĂ©m
hledĂˇnĂ­ po odmĂ­tnutĂ­ vĹˇech nabĂ­dnutĂ˝ch slotĹŻ neposĂ­lej stejnĂ˝ request. Pokud
volajĂ­cĂ­ neupĹ™esnĂ­ preference, pouĹľij date_from jako den po nejpozdÄ›jĹˇĂ­m
odmĂ­tnutĂ©m datu. Pokud odmĂ­tl rannĂ­ termĂ­ny a chce nÄ›co jinĂ©ho, odstraĹ pĹŻvodnĂ­
time_from/time_to filtr, nebo se krĂˇtce zeptej na dopoledne ÄŤi odpoledne.
```

### Body parameters

| Name | Type | Required | Fixed | Description |
| --- | --- | --- | --- | --- |
| `service` | string | ano | ne | Typ sluĹľby. PouĹľij `skin` pro koĹľnĂ­ vyĹˇetĹ™enĂ­. PouĹľij `plasma` pouze pokud pacient vĂ˝slovnÄ› poĹľaduje plazmu. |
| `doctor_name` | string | ne | ne | JmĂ©no nebo pĹ™Ă­jmenĂ­ lĂ©kaĹ™e tak, jak ho Ĺ™ekl pacient, napĹ™Ă­klad Bednar nebo Bartonova. NepouĹľĂ­vej `doctor_id`. |
| `date_from` | string | ne | ne | PoÄŤĂˇteÄŤnĂ­ datum hledĂˇnĂ­ ve formĂˇtu `YYYY-MM-DD`. Vyplnit jen pokud pacient uvede datum nebo obdobĂ­. |
| `date_to` | string | ne | ne | KoncovĂ© datum hledĂˇnĂ­ ve formĂˇtu `YYYY-MM-DD`. Vyplnit jen pokud pacient uvede rozsah. |
| `days_ahead` | integer | ne | ne | PoÄŤet dnĂ­ dopĹ™edu. PouĹľĂ­t pro rozĹˇĂ­Ĺ™enĂ­ hledĂˇnĂ­, hlavnÄ› pĹ™i opakovanĂ©m lookupu. |
| `weekdays` | integer[] | ne | ne | ISO dny v tĂ˝dnu: pondÄ›lĂ­=1 aĹľ nedÄ›le=7. |
| `time_from` | string | ne | ne | NejbliĹľĹˇĂ­ pĹ™ijatelnĂ˝ ÄŤas ve formĂˇtu `HH:MM`. |
| `time_to` | string | ne | ne | NejpozdÄ›jĹˇĂ­ pĹ™ijatelnĂ˝ ÄŤas ve formĂˇtu `HH:MM`. |
| `limit` | integer | ano | `3` | PoÄŤet vrĂˇcenĂ˝ch variant. Pro hlasovĂ©ho agenta drĹľet na 3. |
| `compact` | boolean | ano | `true` | KrĂˇtkĂˇ odpovÄ›ÄŹ vhodnĂˇ pro hlasovĂ©ho agenta. |

### Interpretace response

Agent ÄŤte hlavnÄ›:

- `ok`
- `service`
- `filters.doctor`
- `filters.effective_weekdays`
- `agent_notes`
- `options`

Pravidla:

- Pokud `options` obsahuje termĂ­ny, agent nabĂ­dne nejvĂ˝Ĺˇe 3.
- Pro den v tĂ˝dnu agent pouĹľĂ­vĂˇ `options[].weekday_cs`. Den tĂ˝dne neodvozuje z
  data vlastnĂ­ Ăşvahou.
- ÄŚas agent ÄŤte pĹ™esnÄ› z `options[].time` ve formĂˇtu `HH:MM`. PrvnĂ­ dvÄ› ÄŤĂ­slice
  jsou hodina a poslednĂ­ dvÄ› ÄŤĂ­slice jsou minuty. `07:20` Ĺ™Ă­kĂˇ jako "sedm
  dvacet", nikdy jako "osm dvacet". `08:20` Ĺ™Ă­kĂˇ jako "osm dvacet".
- Pokud `filters.effective_weekdays` obsahuje jen `[1,2,3,4,5]`, backend hledal
  pouze pracovnĂ­ dny, i kdyĹľ `filters.weekdays` je prĂˇzdnĂ©.
- Pokud `agent_notes` Ĺ™Ă­kĂˇ, Ĺľe lĂ©kaĹ™ nebyl nalezen nebo byl nejednoznaÄŤnĂ˝,
  agent nesmĂ­ tvrdit, Ĺľe termĂ­ny jsou u poĹľadovanĂ©ho lĂ©kaĹ™e.
- Pokud `options` je prĂˇzdnĂ©, agent se zeptĂˇ na rozĹˇĂ­Ĺ™enĂ­ hledĂˇnĂ­ nebo zmÄ›nu
  preferencĂ­ a zavolĂˇ tool znovu.
- PĹ™i opakovanĂ©m hledĂˇnĂ­ agent nenabĂ­zĂ­ znovu stejnĂ© termĂ­ny, pokud mĂˇ jinĂ©
  moĹľnosti.
- Pokud opakovanĂ˝ lookup vrĂˇtĂ­ jen sloty, kterĂ© uĹľ volajĂ­cĂ­ odmĂ­tl, agent je
  nepĹ™edstavuje jako novĂ©. Ĺekne, Ĺľe podle aktuĂˇlnĂ­ho zadĂˇnĂ­ jinĂ© moĹľnosti
  nevidĂ­, a nabĂ­dne zmÄ›nu preference nebo pĹ™edĂˇnĂ­ personĂˇlu.

### TestovacĂ­ vÄ›ty

- "ChtÄ›l bych se objednat na koĹľnĂ­."
- "MĂˇte nÄ›co u doktorky BartoĹovĂ©?"
- "A co doktor BednĂˇĹ™?"
- "PotĹ™ebuju spĂ­Ĺˇ odpoledne."
- "Tyhle termĂ­ny se mi nehodĂ­, mĂˇte nÄ›co dalĹˇĂ­ho?"
- "Chci plazmu."

## Tool `patient_lookup`

Aktualizace 2026-07-23: `patient_lookup` uĹľ nevyĹľaduje poslednĂ­ 4 ÄŤĂ­slice
rodnĂ©ho ÄŤĂ­sla. Identita je ovÄ›Ĺ™enĂˇ, pokud poskytnutĂ© Ăşdaje zĂşĹľĂ­ vĂ˝sledek na
jednoho pacienta a response obsahuje `verification.verified=true`. Agent mĂˇ
postupovat po krocĂ­ch: telefon, potom pĹ™Ă­jmenĂ­ + datum narozenĂ­, potom kĹ™estnĂ­
jmĂ©no pĹ™i vĂ­ce shodĂˇch. Pole `birth_number_last4` je jen deprecated
kompatibilita a agent ho nemĂˇ aktivnÄ› vyĹľadovat.

### ZĂˇklad

Name:

```text
patient_lookup
```

Method:

```text
POST
```

URL:

```text
https://DOPLNIT-AKTUALNI-URL.trycloudflare.com/patient-lookup
```

Tool description:

```text
VyhledĂˇ pacienta v Medicus kartotĂ©ce, ovÄ›Ĺ™Ă­ identitu pomocĂ­ poslednĂ­ch 4 ÄŤĂ­slic
rodnĂ©ho ÄŤĂ­sla a po ĂşspÄ›ĹˇnĂ©m ovÄ›Ĺ™enĂ­ vrĂˇtĂ­ existujĂ­cĂ­ objednĂˇvky. Pokud je
caller_phone dostupnĂ˝ z triggeru nebo call metadata, pouĹľij ho jako prvnĂ­ Ăşdaj aĹľ
v identity gate; nevolej tool v turnu 0 na zaÄŤĂˇtku hovoru. Tool pouĹľĂ­vej
pro prĂˇci s existujĂ­cĂ­m termĂ­nem, zmÄ›nu termĂ­nu, zruĹˇenĂ­ termĂ­nu nebo finĂˇlnĂ­
rezervaci novĂ©ho termĂ­nu po tom, co si volajĂ­cĂ­ vybral konkrĂ©tnĂ­ slot. V identity
gate s caller_phone nejdĹ™Ă­v zavolej lookup jen s phone. NeĹ™Ă­kej, Ĺľe jsi naĹˇla
odpovĂ­dajĂ­cĂ­ kartu, dokud verification.verified=true nebo patient_verified=true.
Pokud lookup vrĂˇtĂ­ patients=[], not_found nebo patient_verified=false, pouĹľĂ­vej
neutrĂˇlnĂ­ formulace a nepokraÄŤuj jako pĹ™i nalezenĂ© kartÄ›. Pokud lookup podle
telefonu vrĂˇtĂ­ multiple_matches, poĹľĂˇdej nejdĹ™Ă­v o datum narozenĂ­, ne hned o
poslednĂ­ 4 ÄŤĂ­slice rodnĂ©ho ÄŤĂ­sla. Pokud lookup vrĂˇtĂ­ needs_verification, poĹľĂˇdej
o poslednĂ­ 4 ÄŤĂ­slice rodnĂ©ho ÄŤĂ­sla. NepouĹľĂ­vej aktivnĂ­ lookup jen proto, Ĺľe
volajĂ­cĂ­ Ĺ™ekl, Ĺľe uĹľ u nĂˇs byl. PĹ™i novĂ©m objednĂˇnĂ­ nejdĹ™Ă­v
ovÄ›Ĺ™ dostupnost pĹ™es doctor_availability a nabĂ­dni termĂ­ny; identitu Ĺ™eĹˇ aĹľ pĹ™ed
rezervacĂ­ vybranĂ©ho termĂ­nu. ExistujĂ­cĂ­ objednĂˇvky smĂ­Ĺˇ sdÄ›lit pouze pokud
response obsahuje verification.verified=true.
OsobnĂ­ Ăşdaje z response nikdy neĹ™Ă­kej volajĂ­cĂ­mu; pouĹľĂ­vej je jen internÄ› pro
lookup a ovÄ›Ĺ™enĂ­.
```

Body description:

```text
VyplĹ jen Ăşdaje, kterĂ© mĂˇĹˇ z call metadata nebo kterĂ© volajĂ­cĂ­ poskytl a potvrdil
po kontrolnĂ­ otĂˇzce. Pokud jsi Ăşdaj prĂˇvÄ› zopakoval a zeptal ses â€žJe to
sprĂˇvnÄ›?â€ś, jeĹˇtÄ› ho neposĂ­lej do toolu; poÄŤkej na odpovÄ›ÄŹ volajĂ­cĂ­ho. Pokud je
caller_phone dostupnĂ˝ z triggeru nebo call metadata, pouĹľij ho aĹľ ve chvĂ­li, kdy
je potĹ™eba identity gate. Nevolej patient_lookup v turnu 0. V identity gate s
caller_phone nejdĹ™Ă­v poĹˇli jen phone, include_appointments=true a
include_past_appointments=false. Pokud lookup podle telefonu vrĂˇtĂ­
multiple_matches, dalĹˇĂ­ lookup zpĹ™esni nejdĹ™Ă­v datem narozenĂ­. `birth_number_last4` neposílej; je jen deprecated compatibility pole.
Telefon posĂ­lej jen jako pĹ™esnÄ›
potvrzenou sekvenci ÄŤĂ­slic bez mezer. ÄŚeskĂ© mobilnĂ­ ÄŤĂ­slo bez
pĹ™edvolby mĂˇ obvykle 9 ÄŤĂ­slic; pokud volajĂ­cĂ­ potvrdil 9 ÄŤĂ­slic, neposĂ­lej
10 ÄŤĂ­slic. Nikdy nepĹ™idĂˇvej nulu ani jinou ÄŤĂ­slici, kterou volajĂ­cĂ­ neĹ™ekl a
nepotvrdil. Pokud lookup podle caller_phone vrĂˇtĂ­ jednu pravdÄ›podobnou shodu
nebo needs_verification, neĹ™Ă­kej jmĂ©no z databĂˇze; poĹľĂˇdej neutrĂˇlnÄ› o poslednĂ­
4 ÄŤĂ­slice rodnĂ©ho ÄŤĂ­sla. PevnÄ› nastav
include_appointments=true a include_past_appointments=false, pokud volajĂ­cĂ­
neĹ™eĹˇĂ­ historii.
```

### Body parameters

| Name | Type | Required | Fixed | Description |
| --- | --- | --- | --- | --- |
| `phone` | string | ne | ne | Telefon volajĂ­cĂ­ho jako pĹ™esnÄ› potvrzenĂ© ÄŤĂ­slice bez mezer. PouĹľĂ­t call metadata nebo dynamic variable `caller_phone`, pokud je dostupnĂˇ a agent je prĂˇvÄ› v identity gate. NepouĹľĂ­vat v turnu 0. Pokud ÄŤĂ­slo diktuje volajĂ­cĂ­, poslat ho aĹľ po vĂ˝slovnĂ©m potvrzenĂ­. NepĹ™idĂˇvat ÄŤĂ­slice, neodhadovat pĹ™edvolbu ani nulu; u ÄŤeskĂ©ho mobilu bez pĹ™edvolby typicky oÄŤekĂˇvat 9 ÄŤĂ­slic. |
| `first_name` | string | ne | ne | KĹ™estnĂ­ jmĂ©no pacienta, aĹľ kdyĹľ ho volajĂ­cĂ­ poskytne a agent ho potvrdĂ­. |
| `last_name` | string | ne | ne | PĹ™Ă­jmenĂ­ pacienta, aĹľ kdyĹľ ho volajĂ­cĂ­ poskytne a agent ho potvrdĂ­. |
| `birth_date` | string | ne | ne | Datum narozenĂ­ ve formĂˇtu `YYYY-MM-DD`, aĹľ kdyĹľ ho volajĂ­cĂ­ poskytne a agent ho potvrdĂ­. |
| `birth_number_last4` | string | ne | ne | Deprecated compatibility input. Agent ho nemá vyžadovat ani posílat jako běžný ověřovací údaj. |
| `birth_number` | string | ne | ne | CelĂ© rodnĂ© ÄŤĂ­slo. PouĹľĂ­t hlavnÄ› pro test nebo pokud ho pacient vĂ˝slovnÄ› poskytne. NevyĹľadovat bÄ›ĹľnÄ› jako prvnĂ­ volbu. |
| `include_appointments` | boolean | ano | `true` | Po ovÄ›Ĺ™enĂ­ vrĂˇtit budoucĂ­ objednĂˇvky. |
| `include_past_appointments` | boolean | ano | `false` | Pro bÄ›ĹľnĂ˝ lookup vypnout. Zapnout jen pokud volajĂ­cĂ­ Ĺ™eĹˇĂ­ historii objednĂˇvek. |

### Interpretace response

Agent ÄŤte hlavnÄ›:

- `status`
- `verification.required`
- `verification.verified`
- `patients`
- `appointments`
- `past_appointments`
- `agent_next_step`

Pravidla:

- `status=not_found`: poĹľĂˇdat o jmĂ©no, pĹ™Ă­jmenĂ­ a datum narozenĂ­, potom lookup
  zopakovat.
- `status=multiple_matches` po lookupu podle telefonu: poĹľĂˇdat nejdĹ™Ă­v o datum narozenĂ­.
  PoslednĂ­ 4 ÄŤĂ­slice rodnĂ©ho ÄŤĂ­sla pouĹľĂ­t aĹľ po `needs_verification` nebo pokud
  datum narozenĂ­ nestaÄŤĂ­.
  neĂşspÄ›chu pĹ™edat ĹľivĂ© osobÄ›.
- `verification.verified=true`: teprve potom smĂ­ agent sdÄ›lit existujĂ­cĂ­
  objednanĂ© termĂ­ny z `appointments` nebo `past_appointments`.

Agent nikdy nesdÄ›luje osobnĂ­ Ăşdaje z `patients`, ani ovÄ›Ĺ™enĂ©mu volajĂ­cĂ­mu.
`patients` slouĹľĂ­ jen k internĂ­mu dohledĂˇnĂ­ a rozhodnutĂ­ o dalĹˇĂ­m ovÄ›Ĺ™enĂ­.
Pokud `patients` je prĂˇzdnĂ© nebo `verification.verified=false`, agent nesmĂ­ Ĺ™Ă­ct
"naĹˇla jsem kartu" ani "mĂˇte u nĂˇs kartu". SamotnĂ© `patient_idpac` z dynamic
variables nesmĂ­ pouĹľĂ­t jako identitu, dokud `patient_verified=true`, protoĹľe pĹ™i
`multiple_matches` mĹŻĹľe obsahovat prvnĂ­ho kandidĂˇta.
JedinĂˇ aktuĂˇlnĂ­ vĂ˝jimka pro sdÄ›lovĂˇnĂ­ dat jsou objednanĂ© termĂ­ny ovÄ›Ĺ™enĂ©ho
pacienta z `appointments` nebo `past_appointments`.

### TestovacĂ­ vÄ›ty

- "VolĂˇm z ÄŤĂ­sla, na kterĂ© jsem objednanĂ˝."
- "MĂˇm uĹľ u vĂˇs nÄ›jakĂ˝ termĂ­n?"
- "Jmenuji se Jana NovĂˇkovĂˇ."
- "Datum narozenĂ­ je 6. ÄŤervna 1956."
- "PoslednĂ­ ÄŤtyĹ™i ÄŤĂ­slice jsou 5666."
- "Chci zmÄ›nit termĂ­n."

## NejÄŤastÄ›jĹˇĂ­ chyby nastavenĂ­

- Tool se jmenuje `doctor_availiability` mĂ­sto `doctor_availability`.
- Agent vyplĹuje `doctor_id` mĂ­sto `doctor_name`.
- `limit` a `compact` nejsou fixed a agent je zapomĂ­nĂˇ posĂ­lat.
- Agent ignoruje `agent_notes`.
- Agent sdÄ›lĂ­ existujĂ­cĂ­ objednĂˇvku pĹ™ed `verification.verified=true`.
- Agent pĹ™eĹ™Ă­kĂˇ osobnĂ­ Ăşdaje z `patients` mĂ­sto toho, aby je pouĹľil jen internÄ›.
- Agent se ptĂˇ na celĂ© rodnĂ© ÄŤĂ­slo mĂ­sto poslednĂ­ch 4 ÄŤĂ­slic.
- Agent posĂ­lĂˇ prĂˇzdnĂ© stringy jako parametry.
- Agent po zmÄ›nÄ› preference nevolĂˇ `doctor_availability` znovu.
- Agent opakuje stejnĂ© 3 termĂ­ny, kdyĹľ volajĂ­cĂ­ Ĺ™ekne, Ĺľe nevyhovujĂ­.
- Body object nemĂˇ vlastnĂ­ description a agent nevĂ­, odkud parametry brĂˇt.
- JednotlivĂ© parametry nemajĂ­ description a agent je ĹˇpatnÄ› mapuje.

## Tool `appointment_write`

### ZĂˇklad

Name:

```text
appointment_write
```

Method:

```text
POST
```

URL:

```text
https://DOPLNIT-AKTUALNI-URL.trycloudflare.com/book-appointment
```

Copy-ready JSON mode export:

```text
docs/elevenlabs_tools/appointment_write_v1.json
```

Save-ready varianta pro aktuĂˇlnĂ­ MVP je stejnĂˇ hardcoded `https://...` URL v
JSON artefaktu. Env varianta k ovÄ›Ĺ™enĂ­ po zĂ­skĂˇnĂ­ prĂˇv:

```text
https://{{system__env_medicus_api_host}}/book-appointment
```

Tool description:

```text
VytvoĹ™Ă­, zruĹˇĂ­ nebo pĹ™esune objednanĂ˝ termĂ­n v Medicus databĂˇzi. Tool pouĹľij
pouze po ĂşspÄ›ĹˇnĂ©m ovÄ›Ĺ™enĂ­ pacienta pĹ™es patient_lookup, tedy kdyĹľ
verification.verified=true, a aĹľ potĂ©, co volajĂ­cĂ­ vĂ˝slovnÄ› potvrdil konkrĂ©tnĂ­
termĂ­n nebo zmÄ›nu. Pro koĹľnĂ­ vyĹˇetĹ™enĂ­ backend automaticky vytvoĹ™Ă­ nebo zruĹˇĂ­
takĂ© navazujĂ­cĂ­ dermatoskopickou rezervaci. Pokud tool vrĂˇtĂ­ ok=false, termĂ­n
nebyl vytvoĹ™en, zruĹˇen ani pĹ™esunut.
```

Body description:

```text
VyplĹ pouze Ăşdaje nutnĂ© pro zvolenou akci. action nastav na create, cancel nebo
reschedule. idpac vezmi pouze z ovÄ›Ĺ™enĂ©ho patient_lookup vĂ˝sledku.
patient_verified nastav na true pouze pokud patient_lookup vrĂˇtil
verification.verified=true. Pro create a reschedule poĹˇli service, doctor_name,
date a time podle termĂ­nu, kterĂ˝ volajĂ­cĂ­ potvrdil. Pro cancel a reschedule
poĹˇli appointment_id z ovÄ›Ĺ™enĂ˝ch appointments. NeposĂ­lej osobnĂ­ Ăşdaje pacienta
kromÄ› idpac. NeposĂ­lej doctor_id; lĂ©kaĹ™e posĂ­lej jako doctor_name.
```

### Body parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `action` | string | ano | Akce, kterou mĂˇ backend provĂ©st. PouĹľij pĹ™esnÄ› `create`, `cancel`, nebo `reschedule`. |
| `idpac` | integer | ano | ID ovÄ›Ĺ™enĂ©ho pacienta z `patient_lookup`. PouĹľĂ­t pouze po ĂşspÄ›ĹˇnĂ©m ovÄ›Ĺ™enĂ­ identity. |
| `patient_verified` | boolean | ano | Nastav na `true` pouze pokud `patient_lookup` vrĂˇtil `verification.verified=true`. Jinak tool nevolej. |
| `service` | string | ne | PovinnĂ© pro `create` a `reschedule`. PouĹľij `skin` pro koĹľnĂ­ vyĹˇetĹ™enĂ­ nebo `plasma` pro plazmu. |
| `doctor_name` | string | ne | PovinnĂ© pro `create` a `reschedule`. JmĂ©no nebo pĹ™Ă­jmenĂ­ lĂ©kaĹ™e potvrzenĂ© volajĂ­cĂ­m, napĹ™. `Bartonova` nebo `Bednar`. NeposĂ­lej `doctor_id`. |
| `date` | string | ne | PovinnĂ© pro `create` a `reschedule`. Datum novĂ©ho termĂ­nu ve formĂˇtu `YYYY-MM-DD`. |
| `time` | string | ne | PovinnĂ© pro `create` a `reschedule`. ZaÄŤĂˇtek novĂ©ho termĂ­nu ve formĂˇtu `HH:MM`. |
| `appointment_id` | integer | ne | PovinnĂ© pro `cancel` a `reschedule`. ID existujĂ­cĂ­ho termĂ­nu z ovÄ›Ĺ™enĂ©ho pole `appointments`. |
| `include_related` | boolean | ne | Nastav na `true`. PĹ™i zruĹˇenĂ­ nebo pĹ™esunu koĹľnĂ­ho termĂ­nu backend zahrne i navazujĂ­cĂ­ dermatoskopickou rezervaci. |

### Recommended fixed value

Pokud ElevenLabs dovolĂ­ fixed body parameter, nastav:

```json
{
  "include_related": true
}
```

V aktuĂˇlnĂ­m JSON exportu je `include_related` nastaven jako constant parameter:

```json
{
  "id": "include_related",
  "type": "boolean",
  "value_type": "constant",
  "constant_value": "true"
}
```

### Dynamic variable assignments

AktuĂˇlnĂ­ export mĂˇ zatĂ­m:

```json
"assignments": []
```

DalĹˇĂ­ iterace by mÄ›la pĹ™idat assignments pro flattened variables podle
`docs/elevenlabs_flat_dynamic_variables_v1.json`.

KandidĂˇtnĂ­ `value_path` pro aktuĂˇlnĂ­ response objekty API a minimĂˇlnĂ­ canary
variables pro ĹľivĂ˝ test jsou v
`docs/elevenlabs_state_assignment_test_matrix_v1_cs.md`.

- `patient_lookup` aktualizuje `patient_lookup_status`, `patient_verified`,
  `patient_idpac` a `patient_appointments_json`.
- `doctor_availability` aktualizuje `availability_options_json` a
  `availability_doctor_match_type`.
- `appointment_write` aktualizuje `write_ok` a `write_status`.
- Handoff vÄ›tve aktualizujĂ­ `handoff_required` a `handoff_reason`.

Agent stĂˇle nesmĂ­ hodnoty z dynamic variables pĹ™eĹ™Ă­kĂˇvat jako osobnĂ­ Ăşdaje. SlouĹľĂ­
jen pro rozhodovĂˇnĂ­, ovÄ›Ĺ™enĂ­ a bezpeÄŤnĂ© pokraÄŤovĂˇnĂ­ flow.

## Agent JSON, Workflows a Procedures

ElevenLabs agent nastavenĂ­ lze chĂˇpat jako verzovatelnou konfiguraci. SamostatnĂ©
artefakty pro celĂ˝ agent JSON budou patĹ™it do `docs/elevenlabs_agents/`.

PotvrzenĂ© z dokumentace:

- ElevenLabs CLI podporuje sprĂˇvu agentĹŻ jako konfiguraÄŤnĂ­ch souborĹŻ a push zpÄ›t
  do platformy.
- Workflows jsou uloĹľenĂ© v `conversation_config.workflow`, takĹľe je lze verzovat
  spolu s agent configem.
- Dynamic variables lze pouĹľĂ­t v system promptu, first message a tool
  parametrech. System dynamic variables majĂ­ prefix `system__`; vlastnĂ­ custom
  dynamic variables tento prefix pouĹľĂ­vat nesmĂ­.
- UĹľiteÄŤnĂ© system variables pro audit a ladÄ›nĂ­ mohou bĂ˝t napĹ™Ă­klad
  `system__conversation_id`, `system__caller_id`, `system__agent_turns` a
  `system__conversation_history`.
- Tool calls mohou aktualizovat dynamic variables pĹ™es assignments z JSON
  response pomocĂ­ dot notation.
- Procedures jsou task-specific instrukce s triggerem a markdown contentem.
  Jsou vhodnĂ© pro oddÄ›lenĂ­ modelovĂ˝ch situacĂ­, ale jsou aktuĂˇlnÄ› Alpha.

DoporuÄŤenĂ­ pro nĂˇĹˇ agent:

- System prompt drĹľet pro globĂˇlnĂ­ identitu, bezpeÄŤnostnĂ­ pravidla a privacy
  guardrails.
- Procedures zvaĹľovat pro opakovanĂ© situace: ovÄ›Ĺ™enĂ­ identity, opakovanĂ˝ lookup
  termĂ­nĹŻ, zmÄ›na termĂ­nu, zruĹˇenĂ­ termĂ­nu a pĹ™edĂˇnĂ­ ĹľivĂ© osobÄ›.
- Procedures zatĂ­m nebrat jako stabilnĂ­ produkÄŤnĂ­ zĂˇklad bez testu, protoĹľe
  Alpha feature mĹŻĹľe mÄ›nit schema i dashboard chovĂˇnĂ­.

### NepĹ™idĂˇvat agentovi jako bÄ›ĹľnĂ© parametry

```text
doctor_id
appointment_ids
info
availability_limit
availability_max_limit
```

Tyhle parametry jsou backendovĂ© nebo pokroÄŤilĂ©. Pro prvnĂ­ agent test drĹľet jen
scalar `appointment_id`, ne array `appointment_ids`.

### Interpretace response

- `ok=true`, `status=created`: termĂ­n byl vytvoĹ™en. U `skin` oÄŤekĂˇvej dvÄ› ID.
- `ok=true`, `status=cancelled`: termĂ­n byl zruĹˇen.
- `ok=true`, `status=rescheduled`: pĹŻvodnĂ­ termĂ­n byl zruĹˇen a novĂ˝ vytvoĹ™en.
- `ok=false`, `status=writes_not_enabled`: zapisovĂˇnĂ­ nenĂ­ zapnutĂ© v lokĂˇlnĂ­m configu.
- `ok=false`, `status=slot_not_bookable`: vybranĂ˝ termĂ­n uĹľ nenĂ­ dostupnĂ˝; agent mĂˇ nabĂ­dnout novĂ˝ lookup.
- `ok=false`, `status=doctor_not_resolved`: lĂ©kaĹ™ nebyl jednoznaÄŤnÄ› rozpoznĂˇn; agent mĂˇ upĹ™esnit lĂ©kaĹ™e nebo znovu vyhledat dostupnost.
- `ok=false`: agent nesmĂ­ tvrdit, Ĺľe zmÄ›na probÄ›hla.

## MinimĂˇlnĂ­ smoke test po zmÄ›nÄ› konfigurace

DetailnĂ­ provedenĂ­ a logovĂˇnĂ­ testu:

```text
docs/elevenlabs_agent_test_plan_v1_cs.md
docs/elevenlabs_live_test_run_sheet_v1_cs.md
docs/elevenlabs_live_test_log_template_v1_cs.md
```

1. NovĂ© objednĂˇnĂ­ s dostupnĂ˝m `caller_phone`: agent nemĂˇ volat `patient_lookup`
   v turnu 0 ani pĹ™ed nabĂ­dkou dostupnosti. `caller_phone` pouĹľije aĹľ pĹ™i
   rezervaci vybranĂ©ho termĂ­nu.
2. VolajĂ­cĂ­ chce koĹľnĂ­ vyĹˇetĹ™enĂ­: agent zavolĂˇ `doctor_availability` se
   `service=skin`, `limit=3`, `compact=true`.
3. VolajĂ­cĂ­ chce BartoĹovou: agent poĹˇle `doctor_name`.
4. VolajĂ­cĂ­ odmĂ­tne 3 termĂ­ny: agent zavolĂˇ dostupnost znovu a neopakuje stejnĂ©
   termĂ­ny, pokud mĂˇ jinĂ© moĹľnosti.
5. VolajĂ­cĂ­ chce znĂˇt existujĂ­cĂ­ objednĂˇvku: agent vyĹľĂˇdĂˇ ovÄ›Ĺ™enĂ­, pokud jeĹˇtÄ›
   nenĂ­ `verification.verified=true`.
6. Pokud `patient_lookup` vrati `multiple_matches`, agent pozada o chybejici
   dalsi udaj podle `agent_next_step` a lookup zopakuje.


### Aktualni override patient_lookup 2026-07-23

patient_lookup uz nevyzaduje posledni 4 cislice rodneho cisla. Agent ma nejdrive pouzit telefon z call metadata, potom prijmeni + datum narozeni, a pri vice shodach krestni jmeno nebo dalsi udaj podle agent_next_step. birth_number_last4 zustava jen deprecated compatibility input a nema se vyzadovat. Objednavky lze sdelit pouze pri verification.verified=true.
