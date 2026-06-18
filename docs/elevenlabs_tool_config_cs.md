# ElevenLabs Tool Configuration CS

Verze: 1
Datum: 2026-06-10
Stav: pracovní verze pro nastavení ElevenLabs toolů včetně appointment_write

Tento dokument shrnuje informace potřebné pro nastavení toolů přímo v
ElevenLabs. Chování agenta a pravidla vyhodnocování jsou podrobněji popsané
v `docs/elevenlabs_agent_behavior_cs.md`.

Kompaktní copy-ready seed pro dynamic variables je v
`docs/elevenlabs_dynamic_variables_compact_v0.json`. Detailní referenční katalog
pro n8n, prompt design a audit je v `docs/elevenlabs_dynamic_variables_v0.json`.
Navržený state-first objekt pro další iteraci je v
`docs/elevenlabs_dynamic_state_v1.json`.
Návrh konkrétních dynamic variable assignments je v
`docs/elevenlabs_dynamic_assignments_v1_cs.md`.
Aktuální beta-pragmatický flattened state seed je v
`docs/elevenlabs_flat_dynamic_variables_v1.json`.
Praktická assignment matice pro živé ověření response paths, canary variables a
fallbacku přes n8n je v `docs/elevenlabs_state_assignment_test_matrix_v1_cs.md`.
JSON mode export aktuálně nastaveného toolu `appointment_write` je v
`docs/elevenlabs_tools/appointment_write_v1.json`.
Aktuální upload-ready agent JSON a související branch artefakty jsou v
`docs/elevenlabs_agents/`.

Živý test po nastavení toolů vést podle:

```text
docs/elevenlabs_agent_test_plan_v1_cs.md
docs/elevenlabs_live_test_run_sheet_v1_cs.md
docs/elevenlabs_live_test_log_template_v1_cs.md
```

## Společné nastavení

Aktuální testovací architektura:

```text
ElevenLabs agent
-> webhook tool
-> trycloudflare nebo named Cloudflare Tunnel URL
-> lokální FastAPI
-> Firebird / Medicus read-only logika
```

Před testem doplnit:

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

Poznámka k ElevenLabs URL fields:

- Save aktuálně potvrzeně prochází s natvrdo vloženou validní `https://...`
  URL.
- Env variable syntaxe má obecný tvar `{{system__env_<label>}}`.
- Název env proměnné musí začínat malým písmenem a smí obsahovat jen malá
  písmena, čísla a podtržítka.
- URL musí začínat `https://` ještě před env proměnnou. Env proměnná tedy nemá
  řídit protokol. Pro server tool URL je vhodnější host-only proměnná, například
  `medicus_api_host`, a URL `https://{{system__env_medicus_api_host}}/...`.
- Použití env proměnné přímo v našem workspace zatím není potvrzené, protože
  editace env variables vyžaduje práva.
- Pro MVP tedy v JSON artefaktech držet save-ready hardcoded tunnel URL a env
  variantu ověřit samostatně, až budou práva.

Aktuálně používat jen dva read-only tooly:

- `doctor_availability`
- `patient_lookup`

Zapisovací tool používat až po explicitním zapnutí v lokálním API configu:

- `appointment_write`

`appointment_write` volá endpoint `/book-appointment` a podporuje akce
`create`, `cancel` a `reschedule`.

Pokud je v API nastaven bearer token, každý webhook request musí posílat:

```http
Authorization: Bearer <token>
```

## Dynamic variables v0

Dynamic variables mohou být statické v agentovi, předané z n8n workflow,
získané z ElevenLabs call metadata nebo načtené dynamicky přes webhook.

| Název | Typ | Zdroj | Povinné | Použití |
| --- | --- | --- | --- | --- |
| `medicus_base_url` | string | static / n8n workflow | ano | Aktuální veřejná URL API pro textové nastavení a handoff. Pro trycloudflare se po restartu mění. |
| `medicus_api_host` | string | environment | volitelné | Host-only varianta pro ElevenLabs env URL, například `abc.trycloudflare.com`. Použít jako `https://{{system__env_medicus_api_host}}/...`, až budou práva k env variables. |
| `caller_phone` | string | ElevenLabs call metadata / webhook / n8n trigger | ne | Telefon z triggeru hovoru. Nepoužívat pro turn-0 lookup; použít až jako první údaj v identity gate při rezervaci, změně, zrušení nebo dotazu na existující termíny. |
| `patient_lookup_status` | string | tool assignment | ano | Poslední `patient_lookup.status`, například `not_started`, `needs_verification`, `verified`, `not_found`. |
| `patient_verified` | boolean | tool assignment | ano | Hlavní gate pro sdělení appointments a write tool. |
| `patient_idpac` | number | tool assignment | ano | Technické ID ověřovaného pacienta pro write tool; použít jen při `patient_verified=true`. |
| `patient_appointments_json` | string | tool assignment | doporučeno | JSON string budoucích appointments po ověření pacienta. |
| `availability_options_json` | string | tool assignment | doporučeno | JSON string posledních nabídnutých availability options. |
| `availability_doctor_match_type` | string | tool assignment | doporučeno | `exact`, `partial`, `not_found`, `ambiguous` atd.; hlídá tvrzení o konkrétním lékaři. |
| `write_ok` | boolean | tool assignment | ano | Hlavní gate pro potvrzení write akce. |
| `write_status` | string | tool assignment | ano | `created`, `cancelled`, `rescheduled`, nebo důvod selhání. |
| `handoff_required` | boolean | prompt / workflow | doporučeno | Stav, že má být hovor předán živé osobě. |
| `handoff_reason` | string | prompt / workflow | doporučeno | Důvod handoffu. |
| `medicus_state` | object | legacy / budoucí n8n workflow | ne | Starší návrh jednoho objektu pro decision tree. Pro beta preferovat flattened variables. |
| `caller_state` | object | legacy návrh | ne | Starší rozdělený stav volajícího. Pro další iteraci preferovat sjednocený `medicus_state`. |
| `availability_state` | object | legacy návrh | ne | Starší rozdělený stav dostupnosti. Pro další iteraci preferovat sjednocený `medicus_state`. |
| `clinic_name` | string | static | ano | Představení agenta. Výchozí: Dermatologické středisko Šumperk. |
| `clinic_address` | string | static | ne | Odpovědi na základní dotazy o adrese. Hodnota zatím doplnit. |
| `clinic_opening_hours` | string/object | static | ne | Odpovědi na dotazy k otevírací době. Hodnota zatím doplnit. |
| `clinic_phone` | string | static | ne | Kontakt na středisko nebo živou recepci. Hodnota zatím doplnit. |
| `handoff_phone` | string | static | ne | Telefon pro přesměrování vybraných požadavků, pokud bude potřeba. |
| `doctor_list` | array/object | static / n8n workflow / webhook | doporučeno | Seznam lékařů pro obecnou znalost agenta; pro API stále posílat `doctor_name`, ne `doctor_id`. |
| `procedure_list` | array/object | static / n8n workflow / webhook | doporučeno | Seznam podporovaných a nepodporovaných služeb, aby agent zbytečně nevolal tool. |
| `transfer_reasons` | array | static | doporučeno | Důvody pro předání živé osobě. |
| `agent_version` | string | static | ne | Identifikace testované verze promptu/tool nastavení. |

Pracovní doporučení:

- `doctor_list` a `procedure_list` zatím držet jako static nebo n8n-managed
  dynamic variables.
- `medicus_base_url` pro MVP zatím držet jako hardcoded `https://...` URL v
  každém toolu.
- Env variantu ověřit jako `medicus_api_host`, ne jako full base URL, protože
  ElevenLabs URL validátor vyžaduje `https://` před placeholderem.
- Pro beta preferovat flattened variables, protože odpovídají potvrzeným typům
  dynamic variables v ElevenLabs.
- Jeden sjednocený objekt `medicus_state` držet jako budoucí/n8n variantu, ne jako
  první dashboard implementaci.
- `caller_state` a `availability_state` brát jako starší rozdělený návrh, ne jako
  cílový state-first model.
- Nedělat pro ně samostatný API tool, pokud nejde o data, která se často mění
  během dne.
- API dostupnosti má stále rozhodovat podle reálné DB dostupnosti, ne podle
  statického seznamu v promptu.
- Pro reálné ElevenLabs dynamic variables použít hlavně kompaktní enum soubor
  `docs/elevenlabs_dynamic_variables_compact_v0.json`.
- Detailní katalog `docs/elevenlabs_dynamic_variables_v0.json` je spíš pro n8n
  orkestraci, interní pravidla a audit, ne pro celý prompt context.
- Níže uvedené `procedure_list` a `doctor_list` jsou jen zkrácené orientační
  ukázky.

## Zkrácená ukázka `procedure_list` v0

```json
[
  {
    "key": "skin",
    "spoken_names": ["kožní vyšetření", "vyšetření kůže", "kontrola kůže"],
    "availability_service": "skin",
    "agent_can_offer_availability": true,
    "agent_can_book_finally": true,
    "notes": "V1 podporuje hledání dostupnosti i zápis přes appointment_write po ověření pacienta a potvrzení termínu."
  },
  {
    "key": "plasma",
    "spoken_names": ["plazma", "plazmové ošetření"],
    "availability_service": "plasma",
    "agent_can_offer_availability": true,
    "agent_can_book_finally": true,
    "notes": "Použít pouze když pacient výslovně požaduje plazmu."
  },
  {
    "key": "dermatoscope",
    "spoken_names": ["dermatoskop", "sken znamének", "vyšetření znamének"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "notes": "Samostatný dermatoskop není ve V1 podporovaný jako bookovatelná služba."
  },
  {
    "key": "test_results",
    "spoken_names": ["výsledky", "výsledky testů", "laboratorní výsledky"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "transfer_to_human": true
  },
  {
    "key": "prescription",
    "spoken_names": ["recept", "předpis", "léky"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "transfer_to_human": true
  },
  {
    "key": "personal_data_change",
    "spoken_names": ["změna údajů", "změnit telefon", "změnit adresu"],
    "availability_service": null,
    "agent_can_offer_availability": false,
    "agent_can_book_finally": false,
    "transfer_to_human": true
  }
]
```

## Zkrácená ukázka `doctor_list` v0

Tento seznam je pro orientaci agenta a případnou výslovnost. API má pro
dostupnost stále dostat přirozený text v `doctor_name`.

```json
[
  {
    "display_name": "doktorka Bartoňová",
    "doctor_name_for_api": "Bartonova",
    "known_services": ["skin", "plasma"],
    "notes": "Plazma u Bartoňové je pracovní pravidlo k dalšímu ověření."
  },
  {
    "display_name": "doktor Bednář",
    "doctor_name_for_api": "Bednar",
    "known_services": ["skin"],
    "notes": "Bednář nedělá dermatoskop; duplicitní DB ID je řešené lokálním configem. Agent neposílá doctor_id."
  }
]
```

Seznam doplnit podle potvrzených lékařů a provozních pravidel. Nepoužívat jako
náhradu za dostupnost z API.

## Tool `doctor_availability`

### Základ

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
Vyhledá reálné dostupné termíny v Medicus databázi. Použij tento tool vždy,
když volající hledá termín nebo změní lékaře, službu, datum, období, den v
týdnu nebo preferovaný čas. Dostupnost neodhaduj z paměti ani ze staršího
výsledku. Pokud volající uvede konkrétního lékaře, pošli jeho jméno jako
doctor_name a neurčuj doctor_id.
```

Body description:

```text
Vyplň pouze parametry, které vyplývají z aktuální konverzace nebo jsou pevně
nastavené. Službu nastav na skin pro kožní vyšetření a na plasma pouze pokud
volající výslovně požaduje plazmu. Lékaře předávej jako přirozeně řečené jméno
nebo příjmení v doctor_name. Datum posílej ve formátu YYYY-MM-DD, čas ve formátu
HH:MM. Nevyplňuj doctor_id. Pevně nastav limit=3 a compact=true.
```

### Body parameters

| Name | Type | Required | Fixed | Description |
| --- | --- | --- | --- | --- |
| `service` | string | ano | ne | Typ služby. Použij `skin` pro kožní vyšetření. Použij `plasma` pouze pokud pacient výslovně požaduje plazmu. |
| `doctor_name` | string | ne | ne | Jméno nebo příjmení lékaře tak, jak ho řekl pacient, například Bednar nebo Bartonova. Nepoužívej `doctor_id`. |
| `date_from` | string | ne | ne | Počáteční datum hledání ve formátu `YYYY-MM-DD`. Vyplnit jen pokud pacient uvede datum nebo období. |
| `date_to` | string | ne | ne | Koncové datum hledání ve formátu `YYYY-MM-DD`. Vyplnit jen pokud pacient uvede rozsah. |
| `days_ahead` | integer | ne | ne | Počet dní dopředu. Použít pro rozšíření hledání, hlavně při opakovaném lookupu. |
| `weekdays` | integer[] | ne | ne | ISO dny v týdnu: pondělí=1 až neděle=7. |
| `time_from` | string | ne | ne | Nejbližší přijatelný čas ve formátu `HH:MM`. |
| `time_to` | string | ne | ne | Nejpozdější přijatelný čas ve formátu `HH:MM`. |
| `limit` | integer | ano | `3` | Počet vrácených variant. Pro hlasového agenta držet na 3. |
| `compact` | boolean | ano | `true` | Krátká odpověď vhodná pro hlasového agenta. |

### Interpretace response

Agent čte hlavně:

- `ok`
- `service`
- `filters.doctor`
- `filters.effective_weekdays`
- `agent_notes`
- `options`

Pravidla:

- Pokud `options` obsahuje termíny, agent nabídne nejvýše 3.
- Pro den v týdnu agent používá `options[].weekday_cs`. Den týdne neodvozuje z
  data vlastní úvahou.
- Pokud `filters.effective_weekdays` obsahuje jen `[1,2,3,4,5]`, backend hledal
  pouze pracovní dny, i když `filters.weekdays` je prázdné.
- Pokud `agent_notes` říká, že lékař nebyl nalezen nebo byl nejednoznačný,
  agent nesmí tvrdit, že termíny jsou u požadovaného lékaře.
- Pokud `options` je prázdné, agent se zeptá na rozšíření hledání nebo změnu
  preferencí a zavolá tool znovu.
- Při opakovaném hledání agent nenabízí znovu stejné termíny, pokud má jiné
  možnosti.

### Testovací věty

- "Chtěl bych se objednat na kožní."
- "Máte něco u doktorky Bartoňové?"
- "A co doktor Bednář?"
- "Potřebuju spíš odpoledne."
- "Tyhle termíny se mi nehodí, máte něco dalšího?"
- "Chci plazmu."

## Tool `patient_lookup`

### Základ

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
Vyhledá pacienta v Medicus kartotéce, ověří identitu pomocí posledních 4 číslic
rodného čísla a po úspěšném ověření vrátí existující objednávky. Pokud je
caller_phone dostupný z triggeru nebo call metadata, použij ho jako první údaj až
v identity gate; nevolej tool v turnu 0 na začátku hovoru. Tool používej
pro práci s existujícím termínem, změnu termínu, zrušení termínu nebo finální
rezervaci nového termínu po tom, co si volající vybral konkrétní slot. V identity
gate s caller_phone nejdřív zavolej lookup jen s phone. Neříkej, že jsi našla
odpovídající kartu, dokud lookup skutečně neproběhl. Pokud lookup podle telefonu
vrátí multiple_matches, požádej nejdřív o datum narození, ne hned o poslední
4 číslice rodného čísla. Pokud lookup vrátí needs_verification, požádej o
poslední 4 číslice rodného čísla. Nepoužívej aktivní lookup jen proto, že
volající řekl, že už u nás byl. Při novém objednání nejdřív
ověř dostupnost přes doctor_availability a nabídni termíny; identitu řeš až před
rezervací vybraného termínu. Existující objednávky smíš sdělit pouze pokud
response obsahuje verification.verified=true.
Osobní údaje z response nikdy neříkej volajícímu; používej je jen interně pro
lookup a ověření.
```

Body description:

```text
Vyplň jen údaje, které máš z call metadata nebo které volající poskytl a potvrdil
po kontrolní otázce. Pokud jsi údaj právě zopakoval a zeptal ses „Je to
správně?“, ještě ho neposílej do toolu; počkej na odpověď volajícího. Pokud je
caller_phone dostupný z triggeru nebo call metadata, použij ho až ve chvíli, kdy
je potřeba identity gate. Nevolej patient_lookup v turnu 0. V identity gate s
caller_phone nejdřív pošli jen phone, include_appointments=true a
include_past_appointments=false. Pokud lookup podle telefonu vrátí
multiple_matches, další lookup zpřesni nejdřív datem narození. Birth_number_last4
posílej hlavně až po status=needs_verification nebo pokud datum narození nestačí.
Telefon posílej jen jako přesně
potvrzenou sekvenci číslic bez mezer. České mobilní číslo bez
předvolby má obvykle 9 číslic; pokud volající potvrdil 9 číslic, neposílej
10 číslic. Nikdy nepřidávej nulu ani jinou číslici, kterou volající neřekl a
nepotvrdil. Pokud lookup podle caller_phone vrátí jednu pravděpodobnou shodu
nebo needs_verification, neříkej jméno z databáze; požádej neutrálně o poslední
4 číslice rodného čísla. Pevně nastav
include_appointments=true a include_past_appointments=false, pokud volající
neřeší historii.
```

### Body parameters

| Name | Type | Required | Fixed | Description |
| --- | --- | --- | --- | --- |
| `phone` | string | ne | ne | Telefon volajícího jako přesně potvrzené číslice bez mezer. Použít call metadata nebo dynamic variable `caller_phone`, pokud je dostupná a agent je právě v identity gate. Nepoužívat v turnu 0. Pokud číslo diktuje volající, poslat ho až po výslovném potvrzení. Nepřidávat číslice, neodhadovat předvolbu ani nulu; u českého mobilu bez předvolby typicky očekávat 9 číslic. |
| `first_name` | string | ne | ne | Křestní jméno pacienta, až když ho volající poskytne a agent ho potvrdí. |
| `last_name` | string | ne | ne | Příjmení pacienta, až když ho volající poskytne a agent ho potvrdí. |
| `birth_date` | string | ne | ne | Datum narození ve formátu `YYYY-MM-DD`, až když ho volající poskytne a agent ho potvrdí. |
| `birth_number_last4` | string | ne | ne | Poslední 4 číslice rodného čísla pro ověření totožnosti. Použít hlavně po `needs_verification`. |
| `birth_number` | string | ne | ne | Celé rodné číslo. Použít hlavně pro test nebo pokud ho pacient výslovně poskytne. Nevyžadovat běžně jako první volbu. |
| `include_appointments` | boolean | ano | `true` | Po ověření vrátit budoucí objednávky. |
| `include_past_appointments` | boolean | ano | `false` | Pro běžný lookup vypnout. Zapnout jen pokud volající řeší historii objednávek. |

### Interpretace response

Agent čte hlavně:

- `status`
- `verification.required`
- `verification.verified`
- `patients`
- `appointments`
- `past_appointments`
- `agent_next_step`

Pravidla:

- `status=not_found`: požádat o jméno, příjmení a datum narození, potom lookup
  zopakovat.
- `status=multiple_matches` po lookupu podle telefonu: požádat nejdřív o datum narození.
  Poslední 4 číslice rodného čísla použít až po `needs_verification` nebo pokud
  datum narození nestačí.
- `status=needs_verification`: požádat o poslední 4 číslice rodného čísla.
- `status=verification_failed`: požádat o zopakování údaje; při opakovaném
  neúspěchu předat živé osobě.
- `verification.verified=true`: teprve potom smí agent sdělit existující
  objednané termíny z `appointments` nebo `past_appointments`.

Agent nikdy nesděluje osobní údaje z `patients`, ani ověřenému volajícímu.
`patients` slouží jen k internímu dohledání a rozhodnutí o dalším ověření.
Jediná aktuální výjimka pro sdělování dat jsou objednané termíny ověřeného
pacienta z `appointments` nebo `past_appointments`.

### Testovací věty

- "Volám z čísla, na které jsem objednaný."
- "Mám už u vás nějaký termín?"
- "Jmenuji se Jana Nováková."
- "Datum narození je 6. června 1956."
- "Poslední čtyři číslice jsou 5666."
- "Chci změnit termín."

## Nejčastější chyby nastavení

- Tool se jmenuje `doctor_availiability` místo `doctor_availability`.
- Agent vyplňuje `doctor_id` místo `doctor_name`.
- `limit` a `compact` nejsou fixed a agent je zapomíná posílat.
- Agent ignoruje `agent_notes`.
- Agent sdělí existující objednávku před `verification.verified=true`.
- Agent přeříká osobní údaje z `patients` místo toho, aby je použil jen interně.
- Agent se ptá na celé rodné číslo místo posledních 4 číslic.
- Agent posílá prázdné stringy jako parametry.
- Agent po změně preference nevolá `doctor_availability` znovu.
- Agent opakuje stejné 3 termíny, když volající řekne, že nevyhovují.
- Body object nemá vlastní description a agent neví, odkud parametry brát.
- Jednotlivé parametry nemají description a agent je špatně mapuje.

## Tool `appointment_write`

### Základ

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

Save-ready varianta pro aktuální MVP je stejná hardcoded `https://...` URL v
JSON artefaktu. Env varianta k ověření po získání práv:

```text
https://{{system__env_medicus_api_host}}/book-appointment
```

Tool description:

```text
Vytvoří, zruší nebo přesune objednaný termín v Medicus databázi. Tool použij
pouze po úspěšném ověření pacienta přes patient_lookup, tedy když
verification.verified=true, a až poté, co volající výslovně potvrdil konkrétní
termín nebo změnu. Pro kožní vyšetření backend automaticky vytvoří nebo zruší
také navazující dermatoskopickou rezervaci. Pokud tool vrátí ok=false, termín
nebyl vytvořen, zrušen ani přesunut.
```

Body description:

```text
Vyplň pouze údaje nutné pro zvolenou akci. action nastav na create, cancel nebo
reschedule. idpac vezmi pouze z ověřeného patient_lookup výsledku.
patient_verified nastav na true pouze pokud patient_lookup vrátil
verification.verified=true. Pro create a reschedule pošli service, doctor_name,
date a time podle termínu, který volající potvrdil. Pro cancel a reschedule
pošli appointment_id z ověřených appointments. Neposílej osobní údaje pacienta
kromě idpac. Neposílej doctor_id; lékaře posílej jako doctor_name.
```

### Body parameters

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `action` | string | ano | Akce, kterou má backend provést. Použij přesně `create`, `cancel`, nebo `reschedule`. |
| `idpac` | integer | ano | ID ověřeného pacienta z `patient_lookup`. Použít pouze po úspěšném ověření identity. |
| `patient_verified` | boolean | ano | Nastav na `true` pouze pokud `patient_lookup` vrátil `verification.verified=true`. Jinak tool nevolej. |
| `service` | string | ne | Povinné pro `create` a `reschedule`. Použij `skin` pro kožní vyšetření nebo `plasma` pro plazmu. |
| `doctor_name` | string | ne | Povinné pro `create` a `reschedule`. Jméno nebo příjmení lékaře potvrzené volajícím, např. `Bartonova` nebo `Bednar`. Neposílej `doctor_id`. |
| `date` | string | ne | Povinné pro `create` a `reschedule`. Datum nového termínu ve formátu `YYYY-MM-DD`. |
| `time` | string | ne | Povinné pro `create` a `reschedule`. Začátek nového termínu ve formátu `HH:MM`. |
| `appointment_id` | integer | ne | Povinné pro `cancel` a `reschedule`. ID existujícího termínu z ověřeného pole `appointments`. |
| `include_related` | boolean | ne | Nastav na `true`. Při zrušení nebo přesunu kožního termínu backend zahrne i navazující dermatoskopickou rezervaci. |

### Recommended fixed value

Pokud ElevenLabs dovolí fixed body parameter, nastav:

```json
{
  "include_related": true
}
```

V aktuálním JSON exportu je `include_related` nastaven jako constant parameter:

```json
{
  "id": "include_related",
  "type": "boolean",
  "value_type": "constant",
  "constant_value": "true"
}
```

### Dynamic variable assignments

Aktuální export má zatím:

```json
"assignments": []
```

Další iterace by měla přidat assignments pro flattened variables podle
`docs/elevenlabs_flat_dynamic_variables_v1.json`.

Kandidátní `value_path` pro aktuální response objekty API a minimální canary
variables pro živý test jsou v
`docs/elevenlabs_state_assignment_test_matrix_v1_cs.md`.

- `patient_lookup` aktualizuje `patient_lookup_status`, `patient_verified`,
  `patient_idpac` a `patient_appointments_json`.
- `doctor_availability` aktualizuje `availability_options_json` a
  `availability_doctor_match_type`.
- `appointment_write` aktualizuje `write_ok` a `write_status`.
- Handoff větve aktualizují `handoff_required` a `handoff_reason`.

Agent stále nesmí hodnoty z dynamic variables přeříkávat jako osobní údaje. Slouží
jen pro rozhodování, ověření a bezpečné pokračování flow.

## Agent JSON, Workflows a Procedures

ElevenLabs agent nastavení lze chápat jako verzovatelnou konfiguraci. Samostatné
artefakty pro celý agent JSON budou patřit do `docs/elevenlabs_agents/`.

Potvrzené z dokumentace:

- ElevenLabs CLI podporuje správu agentů jako konfiguračních souborů a push zpět
  do platformy.
- Workflows jsou uložené v `conversation_config.workflow`, takže je lze verzovat
  spolu s agent configem.
- Dynamic variables lze použít v system promptu, first message a tool
  parametrech. System dynamic variables mají prefix `system__`; vlastní custom
  dynamic variables tento prefix používat nesmí.
- Užitečné system variables pro audit a ladění mohou být například
  `system__conversation_id`, `system__caller_id`, `system__agent_turns` a
  `system__conversation_history`.
- Tool calls mohou aktualizovat dynamic variables přes assignments z JSON
  response pomocí dot notation.
- Procedures jsou task-specific instrukce s triggerem a markdown contentem.
  Jsou vhodné pro oddělení modelových situací, ale jsou aktuálně Alpha.

Doporučení pro náš agent:

- System prompt držet pro globální identitu, bezpečnostní pravidla a privacy
  guardrails.
- Procedures zvažovat pro opakované situace: ověření identity, opakovaný lookup
  termínů, změna termínu, zrušení termínu a předání živé osobě.
- Procedures zatím nebrat jako stabilní produkční základ bez testu, protože
  Alpha feature může měnit schema i dashboard chování.

### Nepřidávat agentovi jako běžné parametry

```text
doctor_id
appointment_ids
info
availability_limit
availability_max_limit
```

Tyhle parametry jsou backendové nebo pokročilé. Pro první agent test držet jen
scalar `appointment_id`, ne array `appointment_ids`.

### Interpretace response

- `ok=true`, `status=created`: termín byl vytvořen. U `skin` očekávej dvě ID.
- `ok=true`, `status=cancelled`: termín byl zrušen.
- `ok=true`, `status=rescheduled`: původní termín byl zrušen a nový vytvořen.
- `ok=false`, `status=writes_not_enabled`: zapisování není zapnuté v lokálním configu.
- `ok=false`, `status=slot_not_bookable`: vybraný termín už není dostupný; agent má nabídnout nový lookup.
- `ok=false`, `status=doctor_not_resolved`: lékař nebyl jednoznačně rozpoznán; agent má upřesnit lékaře nebo znovu vyhledat dostupnost.
- `ok=false`: agent nesmí tvrdit, že změna proběhla.

## Minimální smoke test po změně konfigurace

Detailní provedení a logování testu:

```text
docs/elevenlabs_agent_test_plan_v1_cs.md
docs/elevenlabs_live_test_run_sheet_v1_cs.md
docs/elevenlabs_live_test_log_template_v1_cs.md
```

1. Nové objednání s dostupným `caller_phone`: agent nemá volat `patient_lookup`
   v turnu 0 ani před nabídkou dostupnosti. `caller_phone` použije až při
   rezervaci vybraného termínu.
2. Volající chce kožní vyšetření: agent zavolá `doctor_availability` se
   `service=skin`, `limit=3`, `compact=true`.
3. Volající chce Bartoňovou: agent pošle `doctor_name`.
4. Volající odmítne 3 termíny: agent zavolá dostupnost znovu a neopakuje stejné
   termíny, pokud má jiné možnosti.
5. Volající chce znát existující objednávku: agent vyžádá ověření, pokud ještě
   není `verification.verified=true`.
6. Volající řekne poslední 4 číslice rodného čísla: agent zopakuje hodnotu,
   potvrdí ji a zavolá `patient_lookup` s `birth_number_last4`.
