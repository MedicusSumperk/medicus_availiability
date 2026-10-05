# Konfigurace společného nasazení v2

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


Toto je podklad pro připravenou implementaci, nikoli potvrzení připravenosti
pilotu. Dokončení schvalovacího zápisu, zbývající empirické GUI ověření a
hlasové testy celého v2 toku zůstávají podmínkami finálního nasazení. Stávající lokální
produkční konfigurační soubory nepřepisovat celým příkladem.

## Již aktivní části — stav ověřený 2. 10. 2026

Medicus běží s durable handoff a dostupností, nikoli se staff approval.
Aktivační záznamy potvrzují postupně availability-v2 (41ee4e1), call-context-v2
(f7c7c28) a availability-telemetry (bb9429f), vždy bez změny produkční konfigurace.
API má tedy konkrétní postupně nasazené moduly, nikoli celý full-v2 pracovní strom.
Zálohy před jednotlivými změnami a důkazy jsou v příslušných podadresářích
`C:\db_bridge\state`. Nevytvářet novou prázdnou frontu pro další etapu.

Existující store je `C:\db_bridge\state\handoff1\requests.sqlite`; ACL chrání
SYSTEM a Administrators. `Medicus Handoff Delivery` je systémová úloha při
startu, `Medicus Handoff Backup` denně v 03:10 podle serverového času.
První záloha má ověřenou integritu i obsah. Worker a API používají stejný store.
Operator aktivní release je `pilot-2026-10-02.handoff1`.

ElevenLabs hlavičky všech toolů jsou potvrzené uživatelem i dodaným exportem;
prompt a celé definice toolů byly z exportu zkontrolovány. Aktualizace 5. 10.:
handoff tool a odpovídající prompt publikovány; skutečný hovor doložil vyvolání
transferu a trvalé doručení shrnutí do Operatoru. Převzetí personálem ani chování
při obsazení/neodpovědi tím ověřené není. Návrhy identity, tokenů,
staff review a opakované kontroly žádostí nejsou společně nasazené.
Aktualizace 5. 10.: uživatel schválil staff-first postup. Žádosti nedrží termín;
při schválení se znovu ověří dostupnost a známý konflikt zastaví zápis. Případnou
kolizi s ručním objednáním řeší personál a domluví s pacientem náhradu. Kandidát
nepoužívá tabulkové PROTECTED WRITE rezervace; zachovává ochranu opakování,
konfliktů aktualizace a konzistenci párové transakce.
Řízené živé vytvoření, přesun a zrušení MAIN/LASER přes staff HTTP prošly;
vytvoření a zrušení prošly také přes Operator s přihlášeným tenant_user.
Všechny testovací rezervace byly uklizeny. To nedokládá hlasové ověření identity
ani další GUI mapování. GUI cyklus běžného kožního vyšetření je doložen, nikoli
veškeré mapování. Společné vydání dosud není nasazené. Podrobnosti v
`stav_cile.md` a `elevenlabs_v2_rollout.md`.
SMS jsou mimo aktuální rozsah; nevyžadovat ani neaktivovat Twilio SMS.

## Medicus API: config/api.local.json

### Samostatné nasazení předávání personálu

`enable_durable_handoff: true` umožňuje trvale ukládat a doručovat handoff,
zatímco `enable_staff_approval`, `enable_appointment_writes` a
`enable_appointment_cancellations` zůstávají `false`. Příznak nijak nepovoluje
rezervace ani schvalovací endpointy. Dosavadní `enable_staff_approval: true`
nadále zapíná i trvalý handoff kvůli kompatibilitě rozpracované v2.

API, worker i recovery CLI musí používat stejný `approval_store_path`
(absolutní cesta v chráněném adresáři) a `operator_tenant_key`.
Worker a recovery vyžadují existující SQLite soubor; při překlepu nesmí založit
prázdnou náhradní frontu. Před startem workeru inicializovat store pomocí stejné
konfigurace a `handoff_config.handoff_store(config)` pod servisním účtem.
Worker také předem ověří nastavení cílového Operatoru.

Pořadí: nasadit Operator inbox s deduplikací, připravit chráněný store,
nasadit API a worker, ověřit autorizované uložení a skutečné doručení,
teprve potom připojit nový kontrakt ElevenLabs. `stored=true` znamená uložení
do fronty; není potvrzením SMS ani převzetí personálem. Samostatný příznak je
otestovaný a nasazený, skutečné doručení do Operatoru ověřené i hlasovým testem
5. 10. Zbývají callback a chybové scénáře transferu.

| Položka | Hodnota a účel |
| --- | --- |
| host | 127.0.0.1; veřejný přístup přes stávající tunel |
| bearer_token | Existující tajemství pro ElevenLabs. CHANGE_ME ani prázdná hodnota nejsou funkční konfigurace. |
| enable_staff_approval | Zapnout až společně s v2 tools, personálním workflow a workerem. |
| approval_store_path | Zachovat existující C:\db_bridge\state\handoff1\requests.sqlite pro API i worker. Adresář musí být přístupný jen servisnímu účtu a správcům. |
| staff_approval_token | Samostatné náhodné tajemství alespoň 32 znaků; nesmí být stejné jako bearer_token. Nikdy nevkládat do ElevenLabs. |
| enable_appointment_writes | Ponechat false; neověřené přímé zápisy nejsou náhradou staff review. |
| enable_appointment_cancellations | Ponechat false do dokončení ověřené zápisové cesty. |
| operator_ingest_url | Základní URL backendu Operatoru bez /v1/events/workflow. HTTPS, nebo HTTP pouze přes loopback. |
| operator_ingest_token | Stávající interní ingest token Operatoru; pouze na serveru. |
| operator_tenant_key | laser_medicus; musí odpovídat konfiguraci review bridge. |

SQLite soubor obsahuje citlivý kontext a ověřovací reference. Konzistentní
zálohu vytváří `scripts/approval_backup.py --destination ABSOLUTNI_CESTA`.
Používá SQLite backup API a kontrolu integrity; zahrne potvrzená WAL data,
nikdy nepřepíše existující zálohu a neúspěšný nový soubor odstraní.
Adresář předem omezit ACL na servisní účet a správce, stejně jako živý store.
Nekopírovat pouze hlavní soubor během aktivních zápisů. Test samostatného
otevření zálohy prošel lokálně i na hostu; denní úloha je již instalovaná.
Retence, off-host kopie a řízené přepnutí produkce na obnovený store zůstávají
otevřené. Existující zálohy automaticky nemažou historické snapshoty.

Při obnově zastavit pouze Medicus API a jeho handoff worker, zachovat původní
store včetně jeho sidecar souborů pro vyšetření a připravit ověřenou zálohu
na nové chráněné cestě. Nepřepisovat aktivní databázi ani nekombinovat obnovený
soubor se starými WAL/SHM. Změnit approval_store_path pro oba procesy na tutéž
obnovenou cestu. Před jejich spuštěním porovnat stav s Operatorem a skutečnými
zápisy v Medicusu: záloha nemusí obsahovat novější požadavky ani potvrzení.
Stavy executing/needs_reconciliation nevracet automaticky do pending.
Obnova není důvod opakovat Firebird zápis. Stabilní event ID chrání opakované
doručení existujícího handoffu; neobnoví požadavek, který vznikl až po záloze.
Ověření tohoto postupu na hostu naplánovat v servisním okně, nikoli restartem
počítače. Žádný produkční proces nebyl v rámci lokálního testu zastaven.

## Operator: serverové prostředí

| Proměnná | Vazba |
| --- | --- |
| OPERATOR_MEDICUS_REVIEW_URL | Základní interní URL Medicus API, dostupná z procesu Operatoru. |
| OPERATOR_MEDICUS_REVIEW_TOKEN | Stejná hodnota jako staff_approval_token. |
| OPERATOR_MEDICUS_REVIEW_TENANT | laser_medicus. |

Existující OPERATOR_INGEST_TOKEN musí odpovídat operator_ingest_token v Medicusu.
Žádné z těchto tajemství nepatří do NEXT_PUBLIC proměnných nebo browserového
request body. Dashboard dál ověřuje session a členství; personální identitu
pro zamítnutí odvozuje server z přihlášení.

## Doručovací worker

Bez odeslání nebo inicializace databáze lze zkontrolovat stav:

```powershell
C:\python\python.exe scripts/delivery_status.py --config config/api.local.json
```

Diagnostika používá existující SQLite soubor v mode=ro, vrací pouze tenantové
počty předání/návrhů, uvázlé executing starší 10 minut a stav execution fronty.
Nevytváří chybějící store ani tabulky. execution_schema_ready=false znamená,
že na daném store ještě není nasazená nová fronta výsledků. Provozní kontrola
5.10.: 3 stored_in_operator, žádné návrhy/stalled, execution schema zatím chybí.
Úloha Medicus Handoff Delivery: Running, boot trigger, RestartCount=20,
RestartInterval=PT1M, MultipleInstances=IgnoreNew. Jde o čtení nastavení,
nikoli provedený restart/recovery test; proces stále používá původní release.

Z kořene Medicus repozitáře lze po konfiguraci provést jeden skutečný průchod:

```powershell
C:\python\python.exe scripts/handoff_delivery.py --once
```

Tento příkaz **není dry-run**: může doručit čekající handoff i technický alert.
Pro trvalý provoz spouštět stejný příkaz bez --once pomocí servisního správce
klientského hosta, pod účtem s přístupem k témuž SQLite store. Instalace
služby/autostartu je provedena úlohou Medicus Handoff Delivery. Nevytvářet
druhou paralelní instanci. Nepoužívat nezajištěné interaktivní
okno jako produkční worker. Ověřit automatický start po restartu a dohled.

Význam výstupů: stored_in_operator potvrzuje přijetí backendem, nikoli přečtení
personálem; failure_alert_stored_in_operator nepotvrzuje doručení e-mailu.
Postup ruční obnovy je v handoff_recovery.md.

## Supabase a ElevenLabs

Po původní hypercare migraci aplikovat jednou
operator_backend/supabase/20261002_handoff_failure_alerts.sql. Použije stávající
příjemce a Resend tajemství. Uživatel migraci aplikoval a 2. 10. 2026 byla
read-only ověřena shoda obou funkcí i jejich oprávnění. Znovu neaplikovat.
Ověřit následně jediný řízený technický test, nikoli sérii produkčních selhání.

Dodatečná migrace `operator_backend/supabase/20261002_write_audit_tool_names.sql`
byla aplikována vlastníkem a ověřena 5. 10. 2026. Obsahuje appointment_write
a needs_reconciliation; definice, ACL a vazba e-mailového wrapperu ověřeny.
Žádnou z již aplikovaných migrací znovu nespouštět kvůli této etapě.

ElevenLabs musí posílat stabilní skutečné X-Conversation-Id a request_id,
respektovat pending_staff_review a nové tokeny. Konkrétní změny tools a promptu
jsou v elevenlabs_v2_rollout.md. Pouhé zapnutí enable_staff_approval bez těchto
vazeb není nasazení pilotu v2. Staff schválení se agentovi nezpřístupňuje.
