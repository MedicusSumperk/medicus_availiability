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
BASE_URL=https://DOPLNIT-AKTUALNI-URL.trycloudflare.com
```

Endpointy:

```text
GET  {BASE_URL}/health
POST {BASE_URL}/doctor-availability
POST {BASE_URL}/patient-lookup
POST {BASE_URL}/book-appointment
```

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
| `base_url` | string | static / n8n workflow | ano | Aktuální veřejná URL API. Pro trycloudflare se po restartu mění. |
| `caller_phone` | string | ElevenLabs call metadata / webhook | ne | První tichý `patient_lookup` na začátku hovoru. |
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
{{base_url}}/doctor-availability
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
- `agent_notes`
- `options`

Pravidla:

- Pokud `options` obsahuje termíny, agent nabídne nejvýše 3.
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
{{base_url}}/patient-lookup
```

Tool description:

```text
Vyhledá pacienta v Medicus kartotéce, ověří identitu pomocí posledních 4 číslic
rodného čísla a po úspěšném ověření vrátí existující objednávky. Použij tento
tool na začátku hovoru podle telefonu z call metadata, pokud je dostupný, a
potom vždy, když volající poskytne další identifikační údaj. Existující
objednávky smíš sdělit pouze pokud response obsahuje verification.verified=true.
Osobní údaje z response nikdy neříkej volajícímu; používej je jen interně pro
lookup a ověření.
```

Body description:

```text
Vyplň jen údaje, které máš z call metadata nebo které volající právě poskytl a
které jsi s ním potvrdil. Při prvním tichém lookupu použij phone z caller_phone,
pokud je dostupný. Pokud tool vrátí needs_verification, požádej o poslední
4 číslice rodného čísla a volej znovu s birth_number_last4. Pevně nastav
include_appointments=true a include_past_appointments=false, pokud volající
neřeší historii.
```

### Body parameters

| Name | Type | Required | Fixed | Description |
| --- | --- | --- | --- | --- |
| `phone` | string | ne | ne | Telefon volajícího. Při prvním lookupu použít call metadata nebo dynamic variable `caller_phone`, pokud je dostupná. |
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
- `status=multiple_matches`: požádat o doplňující údaj, ideálně datum narození
  nebo poslední 4 číslice rodného čísla.
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
{{base_url}}/book-appointment
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

1. Start hovoru s dostupným `caller_phone`: agent má zavolat `patient_lookup`.
2. Volající chce kožní vyšetření: agent zavolá `doctor_availability` se
   `service=skin`, `limit=3`, `compact=true`.
3. Volající chce Bartoňovou: agent pošle `doctor_name`.
4. Volající odmítne 3 termíny: agent zavolá dostupnost znovu a neopakuje stejné
   termíny, pokud má jiné možnosti.
5. Volající chce znát existující objednávku: agent vyžádá ověření, pokud ještě
   není `verification.verified=true`.
6. Volající řekne poslední 4 číslice rodného čísla: agent zopakuje hodnotu,
   potvrdí ji a zavolá `patient_lookup` s `birth_number_last4`.
