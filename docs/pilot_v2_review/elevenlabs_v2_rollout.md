# Kandidát promptu a změny kontraktů ElevenLabs

## Nasazeno 5. 10. 2026 — aktuální stav

API a Operator jsou společně nasazené v režimu schvalování personálem.
Operator běží z `pilot-2026-10-05.staff-first-v1`, API z ověřeného runtime
`e0ed623`. Povolené jsou běžné kožní vyšetření a sken s následnou prohlídkou;
neověřené kategorie nadále předáváme personálu. Žádosti termíny neblokují.
Před zápisem po schválení se dostupnost znovu ověřuje.

ElevenLabs prompt je publikovaný jako `agtvrsn_2701m46xg14ze4j9fjkcpm3kp74z`.
Čtyři hlavní webhooky používají nové schéma identity/nabídky/žádosti.
U všech pěti webhooků zůstávají potřebné výsledky v odpovědi (`sanitize=false`),
protože nový prompt čte odpovědi toolů a nevkládá staré dynamické proměnné.
Transport, autentizace, přesměrování i workflow zůstaly ověřeně stejné.
JSON editor používá pole properties jako seznam, export jako mapu. Nově vkládaná
konstantní pole editor při ukládání odmítal; použita jsou běžná parametrická pole
s výslovným pokynem pro include_appointments=true, compact=true a limit=3.

Technické kontroly prošly, Supabase již byla na aktuální migraci. Nová migrace
ani změna schématu Firebirdu se neprováděla. Zachována a zálohována je existující
fronta předání. Podrobný záznam je v `production_rollout_20261005.json`.
**Hlasový průchod a vizuální kontrola produkčního Operatoru po nasazení ještě
nejsou potvrzené; celé splnění cíle se tímto neprohlašuje.** Níže uvedené starší
stavy vypnutých příznaků a nenahraných toolů jsou historické.


## Aktuální rozhodnutí pro rollout — 5. 10. 2026

Tato část má přednost před historickými záznamy níže. Důkazy a posloupnost
aktualizací jsou v `stav_cile.md`; nejde o nové živé ověření konfigurace.

| Část | Doložený stav | Další postup |
| --- | --- | --- |
| handoff_summary a odpovídající část promptu | Uživatel publikoval, živé UI ověřeno; hlasový test 5. 10. doložil trvalé doručení shrnutí do Operatoru a vyvolání transferu | Zachovat aktuální nastavení; zbývá callback a chování při obsazení/neodpovědi/chybě. Test nedokládá převzetí hovoru personálem. |
| X-Conversation-Id a autentizace pěti toolů | Potvrzeno uživatelem a dodaným exportem | Při aplikaci fragmentů zachovat transportní konfiguraci. |
| Supabase audit migrace | Tool names i paired operations aplikovány a cíleně ověřeny | Neopakovat migrace kvůli historickému textu níže. |
| Ostatní v2 tools a celý v2 prompt | Lokální kandidáti, nikoli společně publikovaná v2 | Publikovat až s odpovídajícím API a ověřeným personálním workflow. |
| Schvalovací UI | Reálný tenant_user přes Operator schválil řízené vytvoření a zrušení v MAIN/LASER; přesun navíc ověřen přes staff HTTP | Zbývá společné produkční nasazení a hlasový průchod. Identity a nabídky byly v těchto řízených testech připravené, nikoli získané hovorem. |
| Nové zápisy MAIN/LASER | Produkční příznaky vypnuté. Schválen staff-first postup bez tabulkové rezervace; živý cyklus vytvoření/přesunu/zrušení prošel a testovací řádky jsou uklizené | Při schválení znovu ověřit podklady; známý konflikt nezapisovat, případnou kolizi s ručním objednáním řeší personál. Neurčitý výsledek neopakovat. Dokončit zbývající ověření v GUI a společný rollout. |

Samostatný handoff je již nasazený; není třeba jej znovu zavádět. Nasazení pouze
karet bez dokončeného zápisového toku by nebylo dokončením schváleného pilotu.
SMS jsou mimo rozsah. Historické otázky k souběhu zůstávají v
`../stage1_mapping_audit/appointment_side_effects.md`; nebyly odeslány dodavateli
a odpověď dodavatele již není podmínkou schválené staff-first varianty.

## Historie přípravy: formát exportu a dílčí rollout

Následná aktualizace: uživatel doplňkovou Supabase migraci provedl; cílená
read-only kontrola potvrdila její view, tělo funkce, ACL a zachování wrapperu.
Čekání na migraci popsané níže je již vyřešené. Test doručení nového e-mailu
se při této kontrole neprováděl.

V `tool_patches/` je nyní všech pět fragmentů `*.current_export.patch.json`.
Čtyři zbývající fragmenty vytvořil `tools/diagnostics/prepare_elevenlabs_patches.py`
ze schválených návrhů; handoff používá předchozí samostatně ověřený fragment.
Properties jsou mapy a required je seznam na úrovni objektu. Konstanty zachovávají
textový formát dodaného exportu, včetně compact="true". Žádný fragment neobsahuje
URL, autentizaci ani celý export. Sloučení všech pěti s dodaným exportem v paměti
zachovalo transportní konfiguraci; nic nebylo odesláno do ElevenLabs.

Používat tyto aktuální fragmenty, nikoli legacy varianty bez `.current_export`.
Nahradit description, request_body_schema a pouze tam, kde fragment obsahuje
assignments, také assignments. Celé api_schema nenahrazovat.
Šest cílených testů převodu a hlasového kontraktu prošlo. Jde o lokální kontrolu,
nikoli validaci nebo publikaci na ElevenLabs. Handoff lze nasadit proti současnému
backendu; ostatní v2 kontrakty vyžadují společné nasazení odpovídajícího backendu.

Read-only kontrola Supabase 5. 10. opět potvrdila chybějící doplňkovou migraci
`20261002_write_audit_tool_names.sql`: view neobsahuje appointment_write ani
needs_reconciliation a alert funkce nezahrnuje needs_reconciliation.
Starší migrace tím nejsou zpochybněny. Novou migraci musí provést vlastník projektu.

Následující odstavce zachycují předchozí průběh; chybějící export již není blokace.

Aktuální export byl následně dodán uživatelem (verze
agtvrsn_0801m3yf865genxs8xkf2jpw361e). Všech pět webhooků má správnou
X-Conversation-Id a auth connection. Export obsahuje celé definice tools
s properties jako mapou; starší `.patch.json` s properties jako seznamem
neaplikovat přímo jako aktuální REST schema. Audit v
elevenlabs_export_audit_20261002.json neobsahuje tajemství.

Pro handoff je připraven `tool_patches/handoff_summary.current_export.patch.json`
ve skutečném formátu tohoto exportu. Nahradit pouze description a
api_schema.request_body_schema; zachovat URL, hlavičky, auth i assignments.
current_step nahrazuje recommended_next_step, přidává conversation_summary
a volitelný intent. Request_id je už v exportu správně povinné. Backend tato
pole podporuje nyní, na staff approval nečekají. Transportní zachování i
sestavení shrnutí ověřeno lokálně, změna zatím nepublikována.

`elevenlabs_prompt_v2_candidate_cs.txt` je samostatný návrh pro schvalovací
režim s explicitní větví pro backendový staff_handoff. V této větvi agent
nevolá appointment_write, nevyžaduje tokeny ani identitu pro nedostupné
schvalování; může nabídnout pouze povolenou dostupnost a předat preferenci.
Podmínkou zůstává aktuální capabilities odpověď, při neznámém režimu předává.
Není tím dokončena implementace schvalování ani celý pilot. Původní dodaný
prompt ani lokální soubor current nebyl přepsán.
Informace o pracovišti jsou převzaté ze zadání klienta; jejich aktuálnost
nebyla v tomto kroku nezávisle ověřena. Prompt není publikovaný.

Aktuální přístup znovu ověřen 2. 10.: OPERATOR_ELEVENLABS_API_KEY není
nastaven ani v lokálním .env.local, ani v produkčním C:\Operator\config\backend.env.
Ověřeny pouze booleany přítomnosti, žádné tajné hodnoty vypsány. Obě prostředí
mají jeden mapovaný agent. Browser inicializace nadále končí `failed to write
kernel assets` (os error 3). Nelze proto ověřit živý prompt nebo transportní
schémata podle současné konfigurace. K zachování Architect úprav je potřeba
aktuální export agenta a jeho připojených toolů od uživatele, případně obnovený
autorizovaný přístup. Historické backup exporty nejsou důkaz živého stavu.
Oficiální read-only API pro budoucí přístup:
https://elevenlabs.io/docs/api-reference/agents/get.

## Provázané změny nástrojů

Všechny volané webhook tools nadále používají bearer connection a musí
předat X-Conversation-Id z důvěryhodné runtime hodnoty ElevenLabs, nikoli
z pole generovaného modelem. Konkrétní runtime binding ověřit v konfiguraci
agenta před publikací. Zachovat mapování a okamžité transfer_to_number.

| Nástroj | Nový význam / nezbytné údaje |
| --- | --- |
| agent_capabilities | booking_mode=staff_review, review_services; bookable_services prázdné, agent neslibuje přímou rezervaci |
| doctor_availability | request beze změny základních polí; compact odpověď obsahuje arrival_time a offer_token, options_json zachovává celý objekt |
| patient_lookup | first_name, last_name, birth_date; záložní birth_number jako text; výstup verification.verified a patient_verification_token |
| appointment_write | endpoint /book-appointment; action create/reschedule/cancel, request_id, caller_confirmed, patient_verification_token, offer_token pro create/reschedule, appointment_ids pro reschedule/cancel |
| handoff_summary | request_id, mode, reason, intent, conversation_summary, recommended_next_step; neplést s dřívějšími názvy polí, které backend nepoužívá |

V request_id zachovat tutéž hodnotu při technickém opakování stejné žádosti.
Schválení personálem nepřidávat do veřejných toolů ani nezpřístupňovat staff
token agentovi. Response assignment nesmí nastavit write_ok nebo jiný
stav „rezervováno“ z ok=true. Úspěch je pouze committed a booking_confirmed=true.

## Podmínky společného nasazení

Konkrétní lokální fragmenty všech pěti webhook nástrojů jsou v `tool_patches/`:
appointment_write, handoff_summary, patient_lookup, doctor_availability a
agent_capabilities (soubory se zakončením `.patch.json`).
Vycházejí ze struktury uloženého exportu v backup/elevenlabs_updated; živá
konfigurace agenta ani aktuální validace ElevenLabs zatím ověřené nejsou.
Nejde o celé importovatelné definice toolů ani o JSON Patch dle RFC 6902.
Při aplikaci nahradit pouze top-level description, celý request_body_schema
uvnitř existujícího api_schema a top-level assignments. **Nenahrazovat celý
api_schema fragmentem:** chyběla by URL, hlavičky a auth connection.
Zachovat existující URL, runtime X-Conversation-Id, bearer connection a tool ID.

appointment_write nahrazuje původní pole IDPAC/patient_verified referencemi
serveru. Zůstávající proměnná write_ok čte booking_confirmed, nikoli obecné ok;
write_status čte status. Nespoléhat na výchozí hodnotu proměnné při chybě toolu,
rozhoduje aktuální odpověď. Handoff přidává request_id a plný kontext, zachovává
existující response assignments; stored/delivery_status musí agent vyhodnotit
z aktuální odpovědi. Nepředpokládat, že uložené shrnutí samo přepojilo hovor.

Patient lookup již nepovoluje phone-only ani last4 variantu; normální ověření
vyžaduje celé jméno a datum narození a explicitně volitelnou zálohu přes celé RČ.
Odstraňuje assignment patient_idpac; při společném publikování odstranit tuto
již nepoužívanou dynamickou proměnnou a odkazy v případných dalších instrukcích.
Historii lze cíleně vyžádat přes include_past_appointments, není natvrdo vypnutá.
Availability a capabilities používají review_services; emergency neodemyká
rezervace a časový filtr zahrnuje sken. Limit hlasových variant je konstantní 3.

Všech pět fragmentů bylo lokálně sloučeno s uloženými exporty pouze v paměti;
ověřeno zachování URL, hlaviček, auth connection a ostatních transportních polí.
Živý export, validace/publikace v ElevenLabs a hlasové tool-call testy stále
zbývají. Fragmenty samy nesplňují všechny následující podmínky.

- Schvalovací režim a trvalý store připravené; všechny hovory mají správný identifikátor.
- Personální schválení/zápis, stav nejistého výsledku a doručení výsledku funkční.
- Dostupnost povolit jen pro ověřené služby, MAIN/LASER mapování a jednotlivé varianty.
- Odstranit staré instrukce o phone-only ověření a přímém zápisu ze schémat tools i response assignmentů.
- Předání/callback musí mít trvalé uložení, dohledatelné doručení a admin notifikaci při chybě. Durable handoff je již nasazen a technicky ověřen; samotné ok=true však stále není důkaz doručení a živý hlasový test zbývá.
- Ověřit veřejnou tool cestu z ElevenLabs a chování přepojení při obsazení, neodpovědi a technické chybě.

Tyto podmínky dosud nejsou všechny splněny. Samostatné vložení promptu
do dnešní produkce by nespojilo dosud chybějící části řešení.

## Scénáře hlasového ověření

1. Požadavek na člověka: žádné další otázky, předání známého kontextu.
2. Nový termín: nejprve preference/dostupnost, pak celé jméno a datum narození.
3. Dva lékaři v options: nezaměnit jejich časy; 7. říjen jako regresní případ.
4. Sken/bucket: odlišit příchod, sken a prohlídku, nezkrátit požadovaný předstih.
5. pending_staff_review: výslovně nepotvrzený termín, nikoli „jste objednán“.
6. Změna dostupnosti po souhlasu: nová nabídka a nové potvrzení, bez tichého přesunu.
7. Neověřená karta: žádná historie; nulová shoda zopakování údajů, více shod volba RČ/personál.
8. Timeout návrhu/přenosu: žádné tvrzení o úspěchu, žádný nový zápis naslepo.
9. Kontrola za rok: úzké okno podle doporučení, žádný univerzální interval.
10. Služba mimo rozsah: zachovat původní požadavek, žádná náhradní nabídka kožního.
## Additional candidate contract — 2026-10-05

The local doctor_availability patches now add optional
`reschedule_appointment_id` and `patient_verification_token`. Use both only after
identity verification and explicit selection of the original MAIN appointment.
The API binds the resulting offer token to that patient/source snapshot; it may
not be used for a new booking or another source. Keep the service unchanged.
Both API and tool/prompt candidates must be deployed together before this flow
is used. This update is not published in ElevenLabs and production writes remain
gated pending live Firebird validation. The corresponding local suite passed
275 tests, including the HTTP offer issuance/submission contract.
