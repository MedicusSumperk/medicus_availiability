# Stav celého cíle pilotu v2

Aktivní cíl se nezúžil na dokumentaci. Požadovaný konečný stav je ověřený
a nasazený pilot v2 včetně Medicus API, infrastruktury, ElevenLabs promptu
a nástrojů, Operator backendu i frontendu a klientského testování.

| Požadavek | Stav | Důkaz nebo zbývající práce |
| --- | --- | --- |
| Konkrétní otázky pro klienta | Připraveno | PDF strany1–6, 18 otázek s místem na odpovědi |
| Srozumitelná pravidla jako pracovní kroky | Připraveno | PDF strany7–10, R01–R24, odlišeny pracovní defaulty a skutečné nasazení |
| Tisknutelný podklad a přesný feedback | Připraveno | 11stránkové PDF vizuálně zkontrolováno, list hovoru strana11 |
| Odpovědi klienta na zbývající otázky | Po představení první verze | Pokyn 5. 10.: nyní implementovat nejlepší dosavadní pochopení a domluvené defaulty; Q01–Q18 slouží pro následnou revizi. Faktické DB rozpory neřešit odhadem. |
| Konsolidace návrhu | Schváleno | konsolidovany_navrh.md, včetně etap a navazujících závislostí |
| Schválení návrhu před změnami | Doloženo | Uživatel výslovně odpověděl „Schvaluji“; autorizována postupná implementace návrhu |
| API a infrastrukturní změny | Nasazeno; přejímka pokračuje | Runtime e0ed623 + oprava nulových intervalů 862c138 (dva moduly); staff_review pro skin a dermatoscope_first; ostatní zápisové cesty předává personálu |
| Prompt a schémata ElevenLabs tools | Publikováno; hlasový test zbývá | Verze agtvrsn_2701m46xg14ze4j9fjkcpm3kp74z, pět toolů se zachovanou autentizací a viditelnými výsledky |
| Operator backend a frontend | Nasazeno; produkční UI přejímka zbývá | Backend 4c949dd, dashboard 725fb06; předchozí řízené staff testy prošly, ovládání browseru nyní selhává |
| Technické notifikace | Konfigurace a plán ověřeny | Owner SQL výstup 5. 10. 21:43 UTC: zapnuto, správný příjemce, minutový plán, pět úspěšných běhů, jeden sent záznam, žádné čekající. Endpoint 200/idle s klíčem a 401 bez klíče. Nové doručení do schránky netestováno; dřívější uživatel potvrdil. SMS mimo rozsah. |
| Prezentovatelná verze pro klientský test | Nasazena; závěrečné ověření pokračuje | Aktualizovaný tiskový podklad, pravidla staff-first; je třeba skutečný hlasový průchod |
| Řízený test s klientem a opravy | Nedokončeno | T01–T15, záznam skutečné řeči, toolů a DB výsledku, ne jen unit test |
| Nasazení a ověření pilotu v2 | Nasazeno; cíl není uzavřen | Pět služeb Running při nasazení, zdravotní sondy a API kontrakty prošly; zbývá hlasový průchod, produkční UI a dosud nedoložené části mapování. Veřejné autentizované hledání z PowerShellu vrací 200, Python urllib ze serveru i pracovní stanice 403. Přesná příčina odmítnutí a dostupnost z ElevenLabs nejsou tím doložené. |

## Aktuální podmínky dokončení

Doplnění 5. 10., po 21:50 UTC: omezené čtení potvrdilo v MAIN 9. října
u lékaře 15 původní nulový záznam 141243 (červenec) a překryv 144588
z 1. října s příznakem AI_RECEPTION. Následující 11:30 je srpnový záznam
142198; žádný z nich není dnešní testovací zápis. Nic nebylo změněno.
Anonymizovaná regrese potvrzuje zachování obsazenosti původního nulového
intervalu i při odstranění pozdějšího překryvu; všech 14 cílených testů prošlo.
Veřejná cesta byla ověřena autentizovaným POST přes PowerShell (200 a tři
nabídky), Python urllib je odmítán 403. Viz oct9_overlap_20261005.json
a public_client_comparison_20261005.json v ../stage1_mapping_audit/.

Doplnění 5. 10. večer: široké lokální hledání po opravě nulového MAIN
intervalu vrací HTTP 200; regrese má 309 úspěšných testů. GUI LASERu pro
7. října ukázalo obsazená pole kolem 14:45 a 15:45, konzistentní s databázovými
kolizemi. Přesné hranice ani ID nebyly samostatně přečtené v GUI detailu;
viz ../stage1_mapping_audit/incident_laser_gui_20261005.json. Kontrola skončila
po zaznamenání uživatelského vstupu do relace, bez změny dat. Tato dílčí
shoda nenahrazuje původní rozsah empirického mapování.

Nejnovější stav 5. 10. 2026: produkční nasazení je dokončené. Podrobný záznam
verzí a ověření je v production_rollout_20261005.json. Supabase migrace je
ověřená, opakovaně se nespouštěla. Firebird objekty se neměnily. Nasazené
schvalování žádné sloty nedrží; personál rozhoduje a systém před provedením
znovu ověřuje dostupnost. Známý konflikt zastaví zápis, vzácný souběh s GUI
řeší personál kontaktem s pacientem. Živý hovor po publikaci dosud není
doložen. Ostatní níže uvedené zápisy jsou historické a jejich starší stav
produkčních příznaků ani tehdejší překážky nepopisují současné nasazení.

Před nasazením staff-first varianta prošla skutečným řízeným
vytvořením, přesunem a zrušením MAIN/LASER přes staff HTTP. Vytvoření a zrušení
navíc prošly přes Operator s přihlášeným tenant_user. Nové řádky jsou uklizené,
původní testovací termín zůstal nezměněný. Kompletní lokální regrese:
Medicus 295, Operator 56 a dashboard 8 policy testů; lint prošel.
Párové vytvoření, přesun a zrušení nasazeného API byly také zkontrolované
v obou GUI; testovací řádky jsou uklizené. Žádný z těchto řízených testů
nenahrazuje ověření identity v hovoru ani plné doložení všech původně
plánovaných GUI postupů. Historické důkazy a zbývající omezení zachováváme.

5. 10. 2026, po schválení „personál má přednost“: lokální writer odstranil
celotabulkovou rezervaci OBJOBJ při zachování nové SNAPSHOT/NOWAIT transakce,
revalidace, idempotence a 2PC. Odmítnutí při kontrole před jednoduchým zápisem
se po úspěšném rollbacku vrací jako konflikt; chyba rollbacku zůstává nejistá.
59 cílených testů prošlo. Živá transakční sonda MAIN i LASER úspěšně provedla
begin, čtení nejvýše jednoho ID a rollback, bez DML či commitu. Původní problém
se zahájením chráněné transakce proto neblokuje tuto schválenou variantu.
Skutečný zápisový cyklus, párová obnova a společné nasazení tím nejsou ověřeny.
Nové instrukce personálu jsou zatím pouze ve zdroji Operatoru.

5. 10. 2026: uživatel upřesnil pořadí. Nejprve dokončit ucelenou první verzi
refaktoru po launchi, interně ověřit a předložit klientovi; až potom získat
upřesnění a provést další změny. Obchodní otázky neblokují přípravu první verze.
Technický souběh zápisů zůstává samostatný problém k vyřešení, nikoli důvod
automaticky zastavit všechny ostatní části. Nezaměnit hotovou verzi za demo
se syntetickými zápisy nebo za zúžený tok bez schválení a skutečného výsledku.

5. 10. 2026: opravena diagnostika paired_recovery — chyba rollback/close v jedné
DB již nepřeskočí úklid druhého spojení. Zachována původní chyba inspekce,
samostatná chyba úklidu nevrátí úspěch. Deset cílených testů prošlo. Změna
je lokální; nemění journal, neřeší limbo a nenahrazuje provozní řešení souběhu.

5. 10. 2026: dokončen průchod schvalovacími kartami přes skutečný účet personálu
(tenant_user), reálnou Supabase relaci a lokální produkční build dashboardu.
Ověřeny příchod/sken/vyšetření, otevřená expirace, nejistý výsledek bez retry,
vypnuté schválení, potvrzení zamítnutí, přesun do uzavřených a historie s autorem.
Žádosti byly výslovně umělé v dočasném SQLite; PostgreSQL read-only, Firebird
zakázán, žádný produkční zápis. Fixture PID25348 vypnut; obnoven read-only
Operator PID10316 (health200), port8102 uzavřen. Překážka staff UI přihlášení
je odstraněna. Živá úspěšná revalidace/schválení, souběh zápisů MAIN/LASER,
zbývající mapování a nasazení celého pilotu tím nejsou uzavřeny.

5. 10. 2026: aktuální dashboard úspěšně sestaven a lokálně spuštěn přes next start
na 127.0.0.1:3000. Reálná admin relace zachována, 50 hovorů načteno; anonymní
auth/me a seznam žádostí vracejí 401. Lokální backend nadále read-only,
syntetické schvalovací API vypnuté. Jde o lokální produkční build, nikoli nasazení
na server klienta. Tenant-user průchod a živé zápisové testy zůstávají otevřené.

5. 10. 2026: dokončen admin UI test neúspěšné revalidace při zakázaném Firebirdu
a obnovení seznamu. Žádné falešné potvrzení, po refresh návrat ovládání, nejistý
výsledek stále bez retry. Izolovaný fixture proces PID17356 zastaven, port8102
uzavřen. Lokální read-only Operator obnoven (PID21448, health200), dashboard
zůstává přihlášený na přehledu. Produkce beze změny. Test nenahrazuje tenant-user
ověření ani úspěšnou živou revalidaci a zápis.

5. 10. 2026: uživatel se přihlásil do lokálního Operatoru; překážka přihlášení
odstraněna. Přes skutečný admin účet ověřen seznam karet, příchod/sken/lékař,
expirace, nejistý výsledek bez retry, historie, potvrzení zamítnutí a autor,
otevřený/uzavřený filtr i chybějící původní hovor. Čtyři označené umělé žádosti
byly pouze v dočasném lokálním SQLite store; reálné Medicus staff API/Operator
proxy, PostgreSQL read-only, Firebird connect zakázán a zápisy vypnuté.
Vizuální kontrola prošla; opraven indikátor nesouvisejícího ověřování během
otevírání hovoru, potvrzen browserem, ESLintem a TypeScriptem. Nejde o důkaz
tenant-user role, živého zápisu ani produkčního nasazení. Testovací proces
PID17356 (8100/8102) a dashboard zůstávají pro další UI ověření.

5. 10. 2026: celý lint dashboardu a celá Operator sada (56 testů) prošly.
Integrační test handoff byl aktualizován na explicitní inicializaci úložiště;
nejprve ověřuje 503 a nevytvoření náhradního souboru při chybějícím store.
Nasazovací skript nyní vynucuje skutečný tag odpovídající checkoutu. Ověřeny
lightweight/annotated tagy, odmítnutí větve i jiného commitu a PowerShell syntaxe.
Lokální příprava; žádný tag/push, nasazení či změna produkčního procesu.

5. 10. 2026: celá lokální Medicus sada prošla (283 testů). Následně opraven
zastaralý pending stav při přesném opakování již vypršelé žádosti: původní ID
zůstává, TTL se neprodlužuje, stav odpovídá expiraci, nevzniká nová žádost.
Po této změně prošlo 21 cílených store/pagination/API testů včetně nové regrese.
Nejde o důkaz živého Firebird/GUI zápisu ani o nasazení aplikace.

5. 10. 2026: schvalovací karta propojena s existujícím detailem původního hovoru,
kontaktem a přepisem. Přímé načtení podle conversation_id není omezené seznamem
50 hovorů ani datovým filtrem; používá stávající autorizovanou tenantovou cestu.
Chybějící hovor ponechá žádost viditelnou a zobrazí samostatnou chybu. ESLint,
TypeScript a diff kontrola prošly. Lokální změna; autentizovaný UI průchod zbývá.

5. 10. 2026: opraven životní cyklus vypršelých žádostí. Při čtení/kontrole
rozhodnutí se pouze nevyřízené žádosti daného tenanta atomicky označí expired,
zvýší se verze a jednou uloží systémová událost. Běžící zápisy se nemění.
Expired zůstává ve výchozí frontě; nelze schválit, lze výslovně zamítnout.
UI vysvětluje další postup. Dřívější filtr skrývající expired je překonaný.
Prošlo 48 existujících cílených testů, následně nová lifecycle kontrola se
všemi 4 pagination/history testy, ESLint a TypeScript. Zatím lokálně.

5. 10. 2026: doplněn detail historie schvalovací žádosti přes Medicus → Operator
→ dashboard: pořadí stavů, čas, identifikátor rozhodujícího účtu. SQLite čtení
má společný snapshot a kontrolu tenanta; Operator propouští explicitně povolená
pole. Přidány pokyny pro probíhající/neúspěšný/konfliktní zápis. Nejde o funkci
ručního uzavření nejasného výsledku ani opakování zápisu. Prošlo 9 store testů,
10 Medicus HTTP testů, 15 Operator bridge testů, ESLint a TypeScript. Lokální
kandidát, bez nasazení; autentizovaný UI test stále čeká na přihlášení uživatele.

5. 10. 2026: cíl obnoven. Lokální dashboard (127.0.0.1:3000) běží se skutečným
Supabase přihlášením, nikoli auth stubem; čeká na přihlášení uživatele.
Lokální Operator (127.0.0.1:8100) má každou PostgreSQL transakci vynuceně
read-only, vypnuté vytvoření schématu a schvalovací zápisy, bez připojení
na Medicus review. Čtyři HTTP kontroly bez session (list/approve/reject/
revalidate) správně vrátily 401. Není to zatím autentizovaný UI důkaz.
Opravena zavádějící indikace dostupnosti dashboardu; ESLint a TypeScript prošly.
Změna je lokální, žádné produkční služby ani konfigurace se neměnily.

### Bod pro navázání po pauze — 5. 10. 2026

Uživatel požádal dokončit dílčí úkol a pozastavit cíl. Dílčí úkol auditní
Supabase migrace je dokončený, nasazený a ověřený; znovu jej neprovádět.
Po obnovení navázat autentizovaným ověřením schvalovacího UI a přípravou
společného nasazení Medicus API, Operator backendu a dashboardu. Lokální
kandidáti včetně stránkování nejsou produkční release. Nové zápisové cesty
nepovolovat, dokud nebude vyřešen a živě ověřen souběh s Medicus GUI.
Neověřené mapování, řízené zápisové/GUI testy, ElevenLabs kandidáti a klientský
akceptační test zůstávají v rozsahu celého cíle. SMS zůstává mimo rozsah;
zákaz změn Firebird schémat/procedur a restartu serveru zůstává zachovaný.

5. 10. 2026: doplňková Supabase migrace
20261005_write_audit_paired_operations.sql nasazena přes přihlášený SQL Editor.
UI potvrdilo Success; nezávislé SQL čtení runtime rolí ověřilo 29 sloupců,
nový database_name, updated projekci přesunů a podporu párového rušení.
ACL i security_invoker/security_barrier zůstaly stejné. Dřívější požadavek
na ruční spuštění už je vyřešený. Bez změny Firebirdu, restartu či odeslání
alertu. Nasazení aplikačních kandidátů a živé ověření souběhu stále zbývá.

5. 10. 2026: opraven limit fronty na 100 nejnovějších karet, který mohl skrýt
starší nevyřízené žádosti. Server filtruje otevřené stavy před limitem, řadí
od nejstarších a vrací tenantový cursor podle immutable created_at/id. Operator
a dashboard podporují další stránky a samostatné zahrnutí uzavřených žádostí.
2 store testy (230 žádostí, stejné timestampy, změna stavu mezi stránkami,
cizí tenant), 14 bridge testů, ESLint a produkční build prošly. Zatím lokálně;
všechny tři komponenty nasadit společně, autentizovaný UI průchod ještě ověřit.

5. 10. 2026: aktuální skripty kopírovány pouze do privátního read-candidate na
serveru. Izolovaný skutečný HTTP test použil read-only Firebird TPB, všechny
write/execution flags false, vlastní SQLite store a vypnutou telemetrii.
Původní termín testovací karty 141976 má IDCINNOSTI=6; nepodporovaný zdroj
reschedule search správně odmítnut HTTP400 (staff required), nevydána nabídka.
Termín beze změny, localhost test server korektně zastaven, žádné události/mail.
Nejde o úspěšný test validního překrývajícího přesunu; ten dále chybí, stejně
jako živý writer kvůli zámkům. Aktivitu6 nepřemapovávat odhadem na skin/followup.
Důkaz: ../stage1_mapping_audit/live_move_http_readonly_20261005.json.
Embedded Python nemá httpx; použito existující uvicorn + urllib, nic neinstalováno.

5. 10. 2026: ověřena plánovaná úloha Medicus Handoff Delivery: Running, boot
trigger, 20 restartů po minutě, IgnoreNew. Bez restartu nebo změny konfigurace.
Nový delivery_status.py s mode=ro, tenantovými agregacemi a bez inicializace
store prošel 9 cílenými testy a samostatně na serveru z privátní testovací cesty.
Produkční store: 3 stored_in_operator, žádné proposals/stalled; execution_outbox
zatím chybí (očekávaný důkaz, že nová verze není nasazená). Nic neodesláno.
Upozornění na selhání celého hostu/disku tato lokální diagnostika nenahrazuje.

5. 10. 2026: cílený MON přehled našel dlouhé transakce Medicus GUI v obou DB;
nejde o identifikaci konkrétního držitele konfliktu. Uloženy agregace bez jmen
pacientů, uživatelů či stanic v live_transaction_groups_20261005.json.
Technická dokumentace appointment_side_effects.md doplněna o bránu souběhu
a čtyři přesné otázky pro integrátora Medicusu: sdílený zámkový kontrakt GUI/API,
podporovaný atomický booking, provoz dlouhých transakcí a explicitní vazba párů.
Nic neposláno externě. PROTECTED WRITE má dle Firebird dokumentace rozsah celé
tabulky, nikoli termínu; klidový test sám neprokáže bezpečný běžný provoz.
Původní zákaz změn Firebird objektů a vypnuté produkční zápisy zachovány.

5. 10. 2026: cílená živá read-only kontrola projekce OBJOBJ_SEL pro 7.10.2026
a 4.1.2027 v MAIN kalendáři8 a LASER kalendáři5 prošla. Parametrizované vynechání
IDOBJ přesně odpovídá odebrání zvoleného řádku z původní projekce, ostatní
intervaly zachovány: počty 17→16, 1→0, 10→9, 1→0. Není to test zápisu/API/GUI.
Nová lock-only NOWAIT sonda opět hlásí v obou DB konflikt 335544345 (-901)
při protected OBJOBJ reservation, před DML. Žádné relace ukončeny, žádný restart.
Důkaz: ../stage1_mapping_audit/live_projection_lock_check_20261005.json.
Provozní použitelnost writeru zůstává zásadní otevřená brána; neoslabovat ochrany
a nepovolovat zápisy jen proto, aby test prošel. Samotné klidové okno neprokazuje
bezpečný souběh s běžným provozem Medicusu. Celý původní rozsah cíle zachován.

5. 10. 2026: veřejná doctor-availability cesta pro přesun napojena. Volitelný
reschedule_appointment_id vyžaduje staff-review režim, conversation ID a platný
patient_verification_token. Ověří fingerprint, vlastnictví/snapshot, stejnou
službu a standardní zdroj/pár; teprve pak vylučuje přesná MAIN/LASER ID.
Vydaný offer grant ukládá neveřejnou vazbu na pacienta a původní snapshot.
Submit odmítne jeho použití pro create, jinou nebo mezitím změněnou rezervaci.
Aktualizovány oba kandidátní doctor_availability patch formáty a český prompt;
v ElevenLabs nic nepublikováno. HTTP kontrakt + negativní případy ověřeny,
celá lokální sada: 275 passed. Produkční nasazení, aktuální Firebird projekce,
zámky a živý překrývající přesun ještě ověřit. Nejde o uzavření celého pilotu.

5. 10. 2026: single/pair writer již nepoužívá dočasné DELETE/SAVEPOINT pro
ověřování přesunu; po ověření původních řádků používá explicitní read projection
exclusions a následné UPDATE se zachováním ID. Stejný ověřený kontext napojen
do validate_offer při submit, revalidate i executor precondition. Ověří vlastníka,
shodu snapshotu, standardní vazby, u páru explicitní marker a konkrétní scan ID;
nevylučuje cizí, změněné ani neprokázaně propojené rezervace. 45 cílených writer
testů, celá dosavadní sada 264 a 6 následně přidaných testů kontextu prošly.
Stále chybí veřejná availability cesta: ověřený patient grant + výslovně vybraný
původní appointment -> stejný read-only kontext -> offer token vázaný na zdroj.
Bez toho agent překrývající nabídku zatím nezíská. Žádné nasazení ani živý zápis.

5. 10. 2026: připraven read-only základ přesunové dostupnosti: load_appointments
umí interní parametr exclude_ids, předaný explicitně do MAIN engine/search
a ScanCalendar. Filtr používá IDOBJ z procedury, zachová jiné záznamy ve stejném
čase i NULL ID, nevytváří DML. Není napojen na veřejný request ani schvalování;
nejde zatím o dokončenou opravu překrývajícího přesunu. 14 cílených testů prošlo.
Další krok: po ověření vlastníka/snapshotu a standardních vazeb sestavit přesná
MAIN/LASER vyloučení, použít je v nabídce, submit/revalidate i executor validaci;
pak odstranit dočasné DELETE kontroly uvnitř writerů. Živé SQL/procedury ověřit.

5. 10. 2026: executor přijme committed pouze pro shodnou operaci, ok=true,
booking_confirmed=true a neprázdný seznam kladných celočíselných appointment_ids.
Legacy single create/cancel vracejí výslovné potvrzení. Chybná/neúplná odpověď
včetně None vede k trvalému needs_reconciliation a outbox alertu bez opakování.
68 cílených testů prošlo včetně osmi nových chybných odpovědí. Jen lokální změny.
Další potvrzená funkční mezera: validate_payload volá validate_offer ještě před
dočasným vyloučením původního termínu uvnitř writeru. Překrývající přesun může
selhat na vlastní rezervaci. Nestačí odstranit ověření nabídky; nutno zachovat
kontrolu immutable offer/rules v transakci a vyloučit pouze ověřený zdroj/pár,
a řešit konzistentně také získání nabídky a read-only revalidaci návrhu.

5. 10. 2026: rušení samostatných termínů nově sdílí ochrany přesunu pro externí
vazby, opakování, OBJPROC, vícedenní/již navštívené a nemapované aktivity.
Celá dávka se kontroluje před prvním DELETE. Automatické přibrání sousedního
termínu podle času odstraněno; explicitní include_related vyžaduje personál,
spravované dvojice dál obsluhuje párový writer. 40 cílených testů prošlo.
Jen lokální změny; nenahrazuje živé ověření Firebird triggerů a zámků.
Cílené produkční čtení Supabase potvrdilo, že database_name ve view zatím chybí
a dostupná role není vlastníkem; migration connection není nastavena.
Uživateli otevřen otestovaný soubor 20261005_write_audit_paired_operations.sql
a požádán o spuštění v SQL editoru. Produkční schema beze změny.
Po těchto změnách prošla celá lokální sada Medicus: 251 pytest testů.
Jde o regresní testy, nikoli produkční Firebird nebo klientský acceptance test.

5. 10. 2026: delivery worker doplněn o detekci executing starších než 10 minut
podle času atomického převzetí. V jedné SQLite transakci zařadí nejvýše jednou
trvalé upozornění needs_reconciliation; stav žádosti ani oprávnění zápisu nemění.
Případné pozdní dokončení má samostatné event/request ID a zůstává možné.
25 cílených Medicus testů a 12 Operator testů prošlo. Nový integrační test
používá skutečné Medicus události proti lokálnímu Operator endpointu/databázi:
stalled a pozdní úspěch se nezamění, duplicity nepřibývají, párový přesun má
MAIN/LASER a updated. Žádné produkční nasazení ani e-mail. Výpadek disku/celého
hostu stále vyžaduje nezávislý monitoring; worker oznámí uvázlou žádost po obnově.
Další zásadní brány: Supabase migrace a alert doručení, provozní Firebird zámky,
živý ověřený writer a sjednocený rollout celého pilotu.

5. 10. 2026: trvalá fronta execution_outbox v lokálním SQLite approval store.
Dokončení návrhu a vložení redigované události nyní tvoří jednu transakci.
Existující handoff delivery worker obsluhuje také /v1/events/tool, s pevným
event/request ID, tenant filtrem, lease tokenem a opakováním pouze doručení.
28 cílených testů prošlo včetně restartu store, stale lease, rollbacku při
selhání vložení fronty, síťového retry a potvrzení duplicity. Žádné nasazení;
nejde o změnu Firebirdu. Zbývá crash gap: pád procesu nebo disku po zápisu
před dokončením store ponechá executing a zatím vyžaduje ruční reconciliation;
nutno doplnit trvalé upozornění na takto uvázlé žádosti a provozní monitoring.
End-to-end Operator/Resend doručení a novou migraci stále ověřit před rolloutem.

5. 10. 2026: připravena Supabase migrace 20261005_write_audit_paired_operations.sql
pro in-place přesuny a párová zrušení, s doplněným database_name. Skutečné SQL
nahrazení view a syntetické případy ověřeny na PostgreSQL pouze v dočasných
objektech s rollbackem; produkční objekty nedotčeny. Nasazení/ACL/alert ještě
ověřit. Staff telemetrie používá trvalý request_id namísto lokální sekvence,
aby po restartu nekolidovala s dřívějším tool eventem; 21 cílených testů prošlo.
Migrace ani nové aplikace zatím nenasazeny. Další práce: trvalé doručení
execution událostí, provozní zámky a živé zápisy, sjednocení release kandidátů.

5. 10. 2026: staff executor nyní odesílá výsledek přes existující appointment_write
telemetrii, přiřazený původnímu hovoru a proposal/request ID. Záznam obsahuje
pouze technické údaje termínu včetně MAIN/LASER, nikoli IDPAC ani poznámky.
Nejistý výsledek writeru zůstává needs_reconciliation (dříve byl chybně conflict).
Chyba uložení výsledku vyvolá nepotvrzenou diagnostiku bez opakování zápisu;
selhání telemetrie nesmí změnit výsledek operace. 20 cílených testů executoru
a telemetrie prošlo. Změny pouze lokální, bez nasazení či zapnutí zápisů.
Doručení je zatím best effort: doplnit trvalou frontu/recovery pro výpadek
Operatoru a otestovat alert end-to-end. Supabase view ještě nerozbalí nový
in-place reschedule a párový cancel kontrakt; vyžaduje doplňkovou migraci.

5. 10. 2026: propojení schvalovacího endpointu přes Operator do dashboardu
lokálně implementováno. Identita pracovníka pochází ze serverově ověřeného
přihlášení, požadavek nese pouze verzi a ID karty. Samostatný Operator příznak
schvalování zůstává defaultně vypnutý; backend odmítne nepotvrzené či chybně
přiřazené upstream výsledky. UI nabízí potvrzení, nereprodukuje timeoutovaný
zápis a zobrazí úspěch pouze pro committed. 13 cílených backend testů,
TypeScript/build a cílený ESLint prošly. Žádné nasazení ani živý zápis.
Další krok: provázat staff execution s hypercare/auditem a ověřit aktuální
Supabase view proti novému response kontraktu; poté sjednotit release kandidáty.
Autentizovaný browser průchod i provozní test Medicusu stále chybějí.

5. 10. 2026, navazující krok: samostatný přesun nyní aktualizuje původní IDOBJ
a zachovává poznámku; odmítá cizí kartu, neověřené vazby, opakování a změnu
služby. Jedenáct nových testovacích případů včetně skutečného SQLite SAVEPOINT
a rollbacku historie prošlo. Po doplnění redakce poznámek prošla kompletní
sada pytest: 225 testů. Nejde o živý Firebird důkaz.
Operator má podporu nového rescheduled kontraktu (operation=updated), rozlišení
MAIN/LASER a párového zrušení. 11 cílených backend testů, TypeScript, ESLint
upravené stránky a Next.js produkční build prošly. Změny pouze lokální,
bez nasazení či zapnutí zápisů. Zbývá proxy/UI samotného schvalování,
Supabase audit kontrakt, notifikace, recovery a živé ověření zámků i zápisů.

5. 10. 2026, další implementace: připraven staff approve endpoint a executor
s atomickým převzetím žádosti, kontrolou integrity, opětovným ověřením
uložených údajů uvnitř zápisové transakce a stavem needs_reconciliation při
nejistém výsledku. Výchozí enable_staff_execution=false, žádné nasazení.
Osm nových testů, kompletní běh pytest: 213 passed. Původní číslo 187 se
týkalo unittest discovery a nezahrnovalo pytest funkce; není úplným počtem.
Zbývá in-place přesun samostatné prohlídky (executor zatím odmítá legacy
DELETE+INSERT), napojení Operatoru/notifikací, recovery a živé ověření.
Zámky Medicusu dále omezují použitelnost zápisů; nenahrazovat tuto otázku
pouhým úspěchem mockovaných testů. Celý pilot zůstává nedokončený.

5. 10. 2026, po obnovení cíle: doplněna read-only diagnostika párového journalu
`scripts/paired_recovery.py`. Sedm nových testů; celá sada 187 testů prošla.
Ověřeno také spuštění na serveru nad odmítnutým testovacím request_id:
rejected/no_recorded_commit_intent, bez změny journalu a bez DB zápisu.
Diagnostika není automatický recovery executor ani důkaz dokončené transakce.
Další nezávislá práce: napojení schvalovacího executoru na validaci a journal;
živé párové zápisy a provozní použitelnost zámků zůstávají neověřené.
Pokračování respektuje celý původní rozsah cíle; produkční zápisy nezapnuté.

5. 10. 2026, 15:11: připraven kandidát párového create/reschedule/cancel
Ordinace/Laser, zachování ID při přesunu, ověřování vazby, 2PC a trvalý
request_id journal. Celá lokální sada 180 testů prošla (16 nových testů).
Izolované HTTP pokusy na serveru se zastavily PŘED zápisem na zámku OBJOBJ
v aktivním Medicusu; nejde o úspěšný živý test nové dvojice. Snapshot B0–B1
potvrdil beze změny OBJOBJ, OBJHIST i OBJPROC v obou DB pro sledované dny.
Testovací server zastaven, produkční procesy/config/schema beze změny.
Zbývá klidové okno pro živé ověření i posouzení provozní použitelnosti
konzervativního PROTECTED WRITE/NOWAIT zamykání. Zápisy nezapínat pouze
na základě unit testů; schvalovací executor/recovery zůstávají otevřené.
Důkazy: ../stage1_mapping_audit/paired_write_candidate_20261005.json;
technický postup v appointment_side_effects.md. Uživatel dostal otázku
na možné klidové okno; časování zatím není potvrzené.

5. 10. 2026, 14:49: dokončena série skutečných HTTP zápisů přes izolovanou
lokální instanci serverového API se zapnutím pouze testovacího rozsahu.
Produkční zápisy zůstávají vypnuté. MAIN karta 41738, lékař 8, leden 2027:
běžná prohlídka 144759 (černá), kontrola po skenu 144760 (zelená, aktivita 2),
dermatoskopie 144761 (červená, aktivita 1) odpovídají GUI. Svátek, víkend
a duplicitní termín odmítnuty. Přesun běžné prohlídky vytvořil nový IDOBJ
144762; oproti přesunu v GUI API mění ID. Zrušení prošlo, všechny testovací
ID globálně nepřítomné, sledované OBJOBJ odpovídají výchozímu stavu;
zůstaly čtyři očekávané záznamy D v historii. Testovací proces zastaven.
**Potvrzený nedostatek:** dermatoscope_first vrací created a scan_slot
09:15–09:30, ale vytvoří jen MAIN prohlídku v 09:30. LASER zůstává beze
změny a sken není rezervovaný. Před zapnutím kombinovaného objednávání je
nutné doplnit rezervaci skenu a konzistentní přesun/zrušení obou částí.
Test potvrdil technické typy/barvy, nikoli klinické přiřazení aktivit.
Důkaz: ../stage1_mapping_audit/api_gui_tests_20261005.json.
Žádná změna schémat ani procedur Firebirdu, žádný restart produkce.

5. 10. 2026, 14:32: dokončen technický GUI test dvou navazujících rezervací:
LASER IDOBJ 100051, 4. 1. 2027 08:15–08:30, aktivita 28 Dermatoskop bez
IDPAC; MAIN IDOBJ 144756, 08:30–08:40, karta 41738, lékař 8. Čtení
obsazenosti obou zdrojů správně reagovalo na vytvoření i zrušení. Smazání
prohlídky sken automaticky nezrušilo; oba testovací záznamy následně uklizeny
a jejich globální počet je 0. Aktuální objednávky ve sledovaných dnech
odpovídají výchozímu snímku, historie zachována. Zmapovány barvy aktivit
Laseru 28/13 a Ordinace 1/2/5/6. Důkazy a meze:
../stage1_mapping_audit/gui_scan_pair_20261005.json.
Nejde o potvrzení kanonického postupu kombinované služby: MAIN prohlídka
měla běžnou prázdnou aktivitu a oba záznamy byly vytvořeny samostatně.
Personál má potvrdit konkrétní MAIN aktivitu pro prohlídku ihned po skenu
a zda běžně zadává obě rezervace zvlášť. Kombinovaná služba zůstává pro
agenta vypnutá, HTTP/hlasový zápis ani společný přesun nejsou tímto ověřeny.

5. 10. 2026, pozdější aktualizace: uživatel schválil aktivní MAIN kartu IDPAC
41738. GUI test běžného kožního vyšetření prošel: vytvoření IDOBJ 144753
na 4. 1. 2027 08:30–08:40 u lékaře 8, přesun stejného ID na 5. 1.
09:20–09:30 a zrušení. Produkční modul dostupnosti v každé fázi odpovídal
obsazenosti; po úklidu oba sloty opět volné. Existující objednávka 141976
nezměněna. OBJOBJ pro sledované dny odpovídá výchozímu snímku, MAIN historie
obsahuje dvě očekávané změny U/D; Laser beze změny. Automatická poznámka
o testovací objednávce po zrušení v GUI zmizela, v DEKURS nenalezen testovací
marker ani data testu. Podrobnosti a omezení:
../stage1_mapping_audit/gui_skin_cycle_20261005.json.
Tím je odstraněna blokace aktivní kartou popsaná níže; původní neaktivní
karta 33411 nebyla upravena. Zbývají GUI mapování ostatních typů služeb,
zejména kombinace Ordinace/Laser, a následný API/hlasový zápisový test.
Tento dílčí úspěch nezapíná produkční zápisy ani neuzavírá celý cíl.

5. 10. 2026: příprava GUI testu na leden 2027 narazila na vyřazenou testovací
kartu MAIN IDPAC 33411 (VYRAZEN=A). GUI ji zobrazí po zahrnutí vyřazených,
ale tlačítko Vybrat je neaktivní a dvojklik ji nevybere. Žádná objednávka
nebyla uložena. Uživatel požádán o aktivaci karty nebo jinou aktivní testovací
kartu. API a GUI potvrzují volný slot 4. 1. 2027 08:30–08:40, lékař 8;
API správně vyřadí 1. leden a sobotu 2. ledna. Výchozí read-only snapshot
obou DB uložen na serveru s omezenými ACL, před pozdějším zápisem obnovit.
Podrobnosti: ../stage1_mapping_audit/gui_test_20261005.json.

5. 10. 2026: uživatel zpřístupnil přihlášené GUI Ordinace i Laser v RDP;
okna byla skutečně otevřena přes computer-use. První empirické GUI/DB porovnání
7. října je v ../stage1_mapping_audit/gui_observation_20261005.json.
LASER detail skenu 14:45–15:00 potvrzuje 15 minut a popisek Dermatoskop,
odpovídající IDCINNOSTI=28. Dva kontrolované LASER řádky nemají IDPAC vazbu.
Dokumentovaná testovací karta existuje v MAIN a má testovací označení, ale
v LASER není pod stejným ID ani přesnou shodou jména/příjmení/data narození.
Nevytvářet novou kartu ani nekopírovat ID automaticky. GUI create/move/cancel
zatím neprovedeny; pouze navigace a náhled existujícího termínu, zavřen bez uložení.
Hlavní kalendář má nyní obsazené 15:00 a 15:10; dnešní stav není důkazem stavu
při původním incidentu. Původní blokace chybějícím GUI přístupem je odstraněna.

5. 10. 2026: první skutečný hlasový test nové handoff konfigurace doložen.
Hovor conv_2601m45pwgtyfdnb90pv2ykxva47 začal 11:38:58 Europe/Prague, trval
18 sekund. ElevenLabs tool pořadí: handoff_summary (ok=true, stored=true,
mode=live_transfer, všechna nová pole i request_id přítomna), poté
transfer_to_number (business_ok=true, is_error=false). Termination reason:
Call was transferred to number. Trvalý store na serveru má právě jeden
handoff, stored_in_operator, attempts=1, bez error_code, shrnutí i další krok
neprázdné. Jde o důkaz vyvolání transferu a doručení shrnutí, nikoli důkaz,
že personál telefon zvedl nebo co slyšel při obsazení/neodpovědi.
Test callbacku, chybového transferu a GUI zápisů stále zbývá.

5. 10. 2026: uživatel potvrdil úpravu toolu i promptu a publikování.
Následná živá kontrola stejného agenta v ElevenLabs potvrzuje nový blok
conversation_summary/recommended_next_step, stabilní request_id a význam
stored=true. Původní instrukce Do current_step chybí, Publish je disabled
(žádná čekající změna v zobrazeném editoru). Tool byl předtím uložen a ověřen.
Blokace úpravou handoff konfigurace odstraněna; hlasové doručení této verze
ještě není prokázáno. Další krok: řízený test callbacku označeného jako TEST,
kontrola konkrétního hovoru a shrnutí v Operatoru; telefonní transfer testovat
samostatně. Toto není publikace celého v2 ani aktivace zápisů/staff_review.

5. 10. 2026: skutečná UI kontrola nasazeného operator.kreli.org v přihlášeném
Chrome profilu potvrdila plná telefonní čísla u novějších záznamů a zachování
maskování starších. Pole Celé číslo volajícího otestováno číslem již viditelným
v seznamu; serverové hledání doběhlo a zobrazilo odpovídající jediný hovor.
Žádná čísla nejsou uložena v tomto důkazu. Testovací filtr zrušen; žádný stav
hovoru ani personální požadavek nebyl změněn. V administračním seznamu je také
viditelný rozcestník Medicus audit (počet API výsledků a potvrzených záznamů),
což samo o sobě nepotvrzuje skutečné zápisy ve Firebirdu.

5. 10. 2026: browser přístup obnoven, Chrome tab 728999354 otevřen na správném
agentovi/toolu. Živé UI potvrzuje conversation_summary a recommended_next_step
jako povinné string LLM Prompt, current_step odstraněn, request_id a hlavička
zachovány. conversation_summary mělo omylem popis dalšího kroku; agent tento
jediný popis opravil a uložil. Po dokončení Save zmizel stav unsaved changes
a UI zobrazilo správný text. Tool popis a popis těla zůstávají původní.
Uživatel mezitím přešel do full-screen Plain editoru promptu; obsah stále měl
větu s current_step. Kvůli souběžné úpravě agent prompt nepřepsal ani nepublikoval.
Editor ponechán pro uživatele; skutečný hlasový test zbývá. Předchozí tvrzení
o nedostupném browseru již není aktuální.

5. 10. 2026: cílená kontrola dodaného produkčního promptu odhalila v sekci
HANDOFF výslovnou instrukci posílat current_step. Vedle změny parametrů toolu
je nutné nahradit tuto větu instrukcemi pro conversation_summary a
recommended_next_step, stabilní request_id a skutečný význam stored=true.
Přesný omezený blok připraven v handoff_elevenlabs_setup.md; zachovává okamžité
předání bez dalších otázek a nesmí být zaměněn s publikací celého v2 promptu.
Změna v ElevenLabs uživatelem zatím není potvrzená.

5. 10. 2026 11:28 Europe/Prague: cílená kontrola produkce přes SSH potvrzuje
Running pro Medicus API, handoff delivery, Operator API/dashboard/worker;
lokální health API na portech 8000/8100 vrací 200. Veřejné health obou API
a /login dashboardu vrací 200 s běžným browser User-Agent (výchozí urllib
User-Agent byl HTTP odmítnut; nešlo o doložený výpadek backendu).
enable_appointment_writes/cancellations/staff_approval=false, durable_handoff=true.
Poslední plánovaná záloha má LastTaskResult=0; tím se znovu netestovala obnova.
Nasazený handoff_summary.py obsahuje obě podporovaná pole. Nebyly spuštěny
žádné restartovací úlohy ani provedeny zápisy. Čeká se na uživatelovo potvrzení
úpravy toolu, poté nový export nebo reálný hlasový test.

5. 10. 2026: společná cílená sada identity, approval store, návrhů, revalidace,
HTTP API a hlasových regresí prošla (81 testů). Není tím ověřen skutečný hlasový
hovor ani Medicus GUI zápis. Deployment dokumentace opravena podle skutečně
aplikované Supabase migrace a dodaného exportu. Další bezprostřední externí krok
je aplikace hotového handoff_summary fragmentu v ElevenLabs; uživateli položen
dotaz na dostupnost editoru. Staff_review zatím nezapínat bez dokončeného
schvalovacího executor/workflow a navazujícího ověření zápisů.

5. 10. 2026, audit schvalovacího API: opraveny čtyři předčasné návraty z
/book-appointment ve staff_review režimu, které obcházely emit_tool_event.
Nová žádost, replay, konflikt při replay a konflikt při vytvoření nyní emitují
skutečný stav, booking_confirmed a proposal_id; žádné tokeny, identita ani
volný text. Replay nadále neotevírá Medicus, nová žádost provede pouze rollback.
20 cílených testů prošlo, včetně všech čtyř HTTP větví. Jde o lokální přípravu
full-v2, nikoli nasazenou změnu ani důkaz doručení události/e-mailu v produkci.
Diagnostika zůstává best effort; nenahrazuje durable schvalovací store.

5. 10. 2026: uživatel provedl doplňkovou Supabase migraci
20261002_write_audit_tool_names.sql. Následná cílená read-only kontrola potvrzuje
nové aliasy toolů, needs_reconciliation, vazbu podle tenant_id, bezpečnost view
a oprávnění. Tělo claim funkce odpovídá souboru po normalizaci konců řádků;
existující e-mailový wrapper ji nadále volá. Blokace touto migrací odstraněna.
Kontrola neposílala e-mail ani neprováděla Firebird operace. Níže uvedené čekání
na tuto migraci je historické; skutečný hlasový test a GUI důkaz zápisů zbývají.

5. 10. 2026, navazující kontrola backendu: porovnání full-v2 API s nasazenou
release větví odhalilo regresi v diagnostice dostupnosti. Lokální full-v2 nyní
opět vynechává libovolný request text z availability telemetrie, používá bezpečné
chybové kódy a nevydává interní výjimky při chybě dostupnosti. Také lookup a
capabilities vracejí při interní chybě obecnou zprávu. Nové HTTP fault testy
ověřují zachování vrácených slotů, uzavření spojení a absenci commitu.
28 cílených testů prošlo. Dva starší handoff testy potřebovaly skutečné předchozí
vytvoření testovacího store podle nynějšího deployment kontraktu; přidán test,
že ztracený store znamená 503 bez automatického vytvoření náhrady.
Tato změna je lokální, produkce nebyla měněna. Na aplikaci doplňkové Supabase
migrace uživatelem a její následné ověření se stále čeká.

5. 10. 2026: cíl obnoven a aktivní. Všech pět tool fragmentů je připraveno ve
formátu dodaného aktuálního exportu (`*.current_export.patch.json`), sloučení
ověřeno v paměti se zachováním transportu/auth/hlaviček. Šest cílených testů
prošlo; do ElevenLabs nic nepublikováno. Doplňková Supabase migrace
20261002_write_audit_tool_names.sql podle nové read-only kontroly stále chybí.
Uživatel má přístup k SQL editoru a požádal otevřít soubor pro ruční aplikaci;
ověření výsledku následuje po jeho provedení. Firebird beze změn.

NOVÝ PODKLAD OD UŽIVATELE: export Sumper_Recepcni, verze
agtvrsn_0801m3yf865genxs8xkf2jpw361e, doručen a zkontrolován. Blokace chybějícím
exportem je odstraněná; přímý přístup k účtu a živý hlasový test tím doložené
nejsou. Všech pět webhooků má správnou dynamickou X-Conversation-Id i auth
connection. Handoff má povinné request_id, ale current_step backend nečte;
chybí conversation_summary/recommended_next_step. Připraven fragment podle
aktuálního dictionary formátu exportu, se zachováním veškerého transportu a
assignments; syntetický průchod skutečným build_handoff_summary prošel.
Soubor: tool_patches/handoff_summary.current_export.patch.json. Není to celý
importovatelný tool; mění pouze description a request_body_schema.

Prompt v exportu stále předpokládá přímé zápisy, potvrzuje podle ok=true,
obsahuje phone-first identitu a last4 zůstává ve schématu patient_lookup.
Popis appointment_write nesprávně přidává dermatoskop k běžnému kožnímu.
Tyto staré kontrakty nepřenášet do v2; nepovolovat zápisy kvůli shodě s nimi.
Kandidát zachovává Architect pravidla pro nesměšování slotů, okamžité předání,
časové preference a nově přesný blok výslovnosti časů. Audit bez tajemství:
elevenlabs_export_audit_20261002.json. Žádné změny v ElevenLabs nepublikovány.

BLOKACE DALŠÍHO POSTUPU (2. 10.): stejné externí závislosti přetrvaly během
tří navazujících goal turnů. Poslední read-only kontrola potvrzuje chybějící
appointment_write/needs_reconciliation v Supabase view a alert funkci,
nenastavený ElevenLabs API klíč a nula nesyntetických call anchors za hodinu.
Živý export ani přístup do Medicus GUI nebyl dodán. Bez těchto podkladů nelze
dokončit společné kontrakty, ověřenou zápisovou cestu a klientský pilot.
Nejde o dokončení cíle; schvalovací executor, jeho zotavení a celý rollout
zůstávají v rozsahu. Nezastavovat produkční služby, nevytvářet duplicitní cíl.
Navázat na existující rozpracované změny, jakmile přijde export/přístup,
potvrzení migrace či čas skutečného testu. GUI zápis nenahrazovat SQL pokusem.

Živá konfigurace ElevenLabs zůstává nedostupná: nově konkrétně ověřeno,
že lokální i produkční Operator backend nemají ElevenLabs API klíč; browser
znovu selhal při inicializaci (kernel assets, os error 3). Uživatel potvrzuje
hlavičky všech toolů, ale aktuální prompt/ostatní schémata nelze nezávisle
porovnat. Vyžádán aktuální export pro zachování Architect změn. Nevytvářet
nového agenta a nepřepisovat živý prompt podle historického backupu.

Full-v2 pracovní implementace: doplněn staff-only POST
/staff/proposals/{id}/revalidate s verzí žádosti. Tenantově oddělený interní
snapshot ověřuje pending stav, expiraci a digest před DB čtením; následně
znovu porovnává pacienta, původní rezervaci a dostupnost nabídky. Po čtení
ověří, že mezitím nevzniklo jiné rozhodnutí. Vrací pouze bezpečný výsledek,
booking_confirmed=false a execution_enabled=false; nevytváří blokaci ani
schválení. Firebird transakce se rollbackuje, write_appointment se nevolá.
33 cílených testů revalidace/proposals/API/store prošlo. Žádné produkční
nasazení této části. Personální kontrola je nyní lokálně propojena do Operatoru:
backend tenant-bound bridge, striktní kontrola ID/verze/booking_confirmed=false,
dashboard autorizovaná proxy a tlačítko Ověřit aktuální stav. Výsledek ukazuje
čas kontroly a výslovně neznamená rezervaci. Osm backend testů, TypeScript,
ESLint změněných souborů i produkční Next.js build prošly. Připravit společný rollout;
skutečný approve executor a GUI důkazy zápisového mapování nadále zbývají.

Poslední cílená read-only kontrola Supabase znovu potvrdila nepřítomnost
20261002_write_audit_tool_names.sql: appointment_write i needs_reconciliation
chybí ve view a claim funkci. Soubor otevřen uživateli k provedení v SQL Editoru
vlastníkem projektu; runtime role nemá potřebná DDL oprávnění. Předchozí migrace
nenahrazuje tuto doplňující migraci. Žádné Firebird SQL změny nejsou součástí.

Kandidát ElevenLabs promptu nyní rozlišuje staff_review a staff_handoff podle
aktuálních capabilities; při handoff nevyžaduje identitu/tokeny a nepředstírá
schvalovací žádost. Služby filtruje dle skutečné availability schopnosti,
plazma/laser zůstávají mimo pilot. Rozpor nulové shody pacienta opraven podle
výslovného zadání uživatele: po kontrole údajů volba celého RČ nebo personálu,
shodně s existujícím patient_lookup tool patchem. Produkční prompt NEMĚNĚN;
aktuální Architect úpravy je nutné při živé publikaci zachovat.

CÍL OBNOVEN, DOSTUPNOST NASAZENA 2. 10. 2026: osm modulů z GitHub
release/availability-v2, commit 41ee4e1 (strom 4aa5935 shodný s lokálním
87e96aa), aktivováno po kontrole hashů kandidáta i původních souborů.
87 testů prošlo lokálně i v serverovém Pythonu před nasazením. Následný živý
API test vrátil tři skin termíny na 7. 10.; všechny tři byly read-only
porovnány s OBJOBJ_SEL, bez kolize. Sobota 3. 10. a svátek 28. 10. bez nabídky.
Bez tokenu API vrací 401; capabilities správně hlásí staff_handoff a prázdné
bookable_services. Zápisy, rušení, schvalování i dostupnost dermatoscope_first
zůstávají vypnuté. Produkční konfigurace se nezměnila; žádné Firebird DML/DDL.
Restartována pouze služba Medicus Local API, nikoli počítač nebo Medicus.
Rollback soubory, activation.json a live-smoke.json jsou v chráněném
C:\db_bridge\state\availability-v2. Operator API/dashboard/worker i Medicus
handoff worker běží; zálohovací a health úlohy připravené, poslední výsledek 0.
Starší zmínky o nenasazeném kandidátu níže jsou historické.

Dále zbývají hlasový handoff test, doplňující Supabase audit migrace,
GUI mapování, schvalovací executor, úplné ElevenLabs
kontrakty/prompt a klientský pilot. Hodinový předstih je v této izolované verzi
vztažen k času požadavku; společné ukotvení na začátek hovoru ještě není zapojené.
SMS jsou mimo současný rozsah. Stávající cíl je aktivní; nový nezakládat.

Call context NASAZEN 2. 10.: shared call_context.py a zapojení autentizovaných
tools, first_seen v existujícím chráněném SQLite i s vypnutým staff approval.
26 cílených testů (API, časový předstih, capabilities, handoff uložení/doručení)
prošlo lokálně i na serveru. Publikováno release/call-context-v2, f7c7c28,
strom 3446555 přesně odpovídá lokálnímu 87a54b4. Před nasazením ověřeny hashe
měněných modulů i čtyř závislostí a existence chráněného store. Živý test přes
capabilities a availability ověřil stejný first_seen, fallback bez hlavičky,
HTTP 400 pro nevyřešenou šablonu a 401 bez tokenu. Konfigurace nezměněna,
zápisy vypnuté, žádné Firebird DML/DDL; restartováno pouze API. Rollback a důkazy
jsou v C:\db_bridge\state\call-context-v2 (activation.json, live-smoke.json).
Uživatel následně potvrdil X-Conversation-Id u všech toolů. Následná read-only
kontrola call_anchors za poslední hodinu našla nula nesyntetických hovorů;
celkový hlasový tok tedy ještě není ověřen. Další potřebný důkaz je skutečný
kontrolovaný hovor s opakovaným hledáním a předáním požadavku do Operatoru.
Oprava je i ve full-v2 pracovním stromu; osm auth/lead-time testů zde prošlo.

Diagnostika dostupnosti NASAZENA 2. 10.: v izolovaném release stromu doplněno
odesílání skutečně vrácených options i bezpečného kódu chyby do Operatoru pod
stejným conversation ID. Arbitrární text requestu se neodesílá. Odesílač
nově zachytí i chybu konfigurace/zařazení do fronty, aby nezměnila výsledek
API; výjimky se nevypisují do logu, identity/tokeny se redigují včetně JSON
řetězců. 18 cílených testů prošlo (telemetrie, availability endpoint, call
context, handoff), také všech 18 na serveru. Publikováno jako
release/availability-telemetry bb9429f (strom 2cf0452 odpovídá lokálnímu
057d243). Nasazeny jen api_server.py a operator_telemetry.py; původní hashe
ověřeny, config nezměněn, zápisy vypnuté. Živý technický dotaz na 7. 10.
vrátil tři skin termíny; přes tenant-scoped detail Operatoru dohledána přesně
jedna událost medicus-api se stejnými daty, časy a lékaři. Bez pacientských
údajů, bez Firebird zápisů. Rollback i activation/live-smoke.json uloženy
v C:\db_bridge\state\availability-telemetry. Restartováno pouze API.
Veřejné health Medicus/Operator a login dashboardu HTTP 200. Best-effort
diagnostika nenahrazuje trvalé doručení technického alertu administrátorovi.

Pozitivní kombinovaná dostupnost doložena 2. 10. v 13:58 UTC: kandidát se
hashově shoduje s osmi nasazenými moduly. Read-only diagnostika napříč lékaři
našla 5. 10. u ID 8 vyšetření 10:40–10:50 a 10:50–11:00 se skeny
10:25–10:40 a 10:35–10:50, dále 7. 10. u ID 12 vyšetření 13:20–13:30
se skenem 13:05–13:20. Každá alternativa zvlášť porovnána s OBJOBJ_SEL
v obou DB, bez kolize; nejde o tři současně rezervovatelné termíny (skeny
prvních dvou alternativ se překrývají). Šest kandidátů prošlo kontrolou LASER,
tři odmítnuty a tři přijaty. Povolení availability pouze v paměti diagnostiky,
produkční konfigurace ani data nezměněny. Neprokazuje zápisové mapování ani
GUI chování. Evidence: medicus-availability-release/docs/
availability_v2_combined_positive.json; skript tools/diagnostics/
probe_combined_positive.py. Starší nulové výsledky níže platí pro dřívější
dotazy a okamžik snímku; nejsou trvalým tvrzením o obsazenosti.

Kandidát dostupnosti ověřen read-only na MAIN/LASER 2. 10.: 7. 10. dva
vrácené skin termíny bez kolize oproti OBJOBJ_SEL, sobota 3. 10. a svátek
28. 10. bez nabídky. Incident 15:00/15:10 koliduje skenem v LASER, 15:50
v obou kalendářích; kandidát všechny tři vylučuje. Jde o aktuální stav,
ne historickou rekonstrukci hovoru. Produkční dermatoscope availability je
stále false; diagnostické dočasné povolení existovalo jen v paměti procesu.
Pozitivní kombinovaný slot pro lékaře 12 ve vzorku 8.–16. 10. nenalezen,
nelze tím doložit pozitivní živý kombinovaný případ. Data ani config nezměněny.
Evidence v medicus-availability-release/docs/availability_v2_live_probe.json.

Read-only dostupnost: vytvořen izolovaný `../medicus-availability-release`,
branch release/availability-v2 nad handoff1. Proti skutečnému serverovému
snapshotu chybí výjimky rozvrhu, smíšené délky buněk, svátky/časové filtry.
Přeneseny připravené opravy; 87 cílených testů prošlo. Opraven navíc rozpor
agent-capabilities, který ignoroval vypnutý API write switch a mohl slibovat
objednání. Kandidát zatím nenasazen; další krok je cílené read-only srovnání
se skutečnými MAIN/LASER daty a produkční konfigurací před aktivací.

ZMĚNA ROZSAHU OD UŽIVATELE: SMS nyní neimplementovat ani nezapínat kvůli
dalším nákladům. SMS již nejsou podmínkou dokončení aktuálního pilotu.
Rozpracovaný, nezapojený transport odstraněn; žádný Twilio request ani SMS
neproběhly. Trvalé požadavky v Operatoru a admin e-mailové alerty zůstávají
v rozsahu. Historické zmínky o chybějících SMS níže jsou tímto překonané.

Medicus handoff publikován na GitHubu release/handoff1 commit 75761c8
(strom 40bf310 shodný s lokálním a2e6fb2). Přidán denní SYSTEM task
Medicus Handoff Backup, 03:10 podle času serveru, StartWhenAvailable.
První záloha vytvořena SQLite backup API, samostatně otevřena read-only,
integrita OK a oba známé technické handoffy zachovány. Ukládá se do chráněného
state/handoff1/backups; pilotní kopie se automaticky nemažou. Je to záloha
na stejném hostu; off-host uložení a retenční politika zůstávají otevřené.
Skutečné výsledky na hostu: backup-verification.json a last-success.json;
activation.json nově obsahuje publikovaný commit/strom.

AKTUÁLNĚ: po potvrzení uživatele, že upravil handoff_summary, aktivován
Medicus durable handoff. Nasazené soubory odpovídají izolované větvi
medicus-handoff-release c66c9af; produkční dirty LASER soubory zachovány.
SYSTEM task Medicus Handoff Delivery i Medicus Local API běží; oba health OK.
Živý test přes API → SQLite → scheduled worker → Operator prošel, dvě odlišné
technické žádosti bez pacientských údajů, retry bez duplicit a bez znovuotevření
vyřešeného testu. Test označen resolved. Evidence v chráněném state/handoff1:
activation.json (včetně hashů), live_smoke.json, smoke_identity.json.
Embedded Python vyžadoval explicitní sys.path při spuštění workeru; opraveno
a doručení ověřeno skutečným scheduled procesem. Recovery CLI vrací [] selhání.
Zápisy/cancellations/staff approval zůstávají false. Restartováno pouze API,
nikoli Medicus/počítač. Skutečný hlasový test a SMS stále chybějí.
Starší přípravné/čekací poznámky níže jsou historie.

Handoff aktivace připravena: `C:\db_bridge\state\handoff1` má chráněné ACL
pouze SYSTEM + Administrators. Obsahuje prázdný ověřený requests.sqlite,
zálohu původního API/configu, api.local.prepared.json a preparation.json.
Připravený config obsahuje tajemství, nezveřejňovat ani kopírovat do Git.
Autorizované čtení Operatoru přes loopback a fixed tenant prošlo. Produkční
config/API porovnány byte-for-byte beze změny. Před aktivací porovnat jejich
SHA256 s preparation.json; neobnovovat slepě starý snapshot, pokud se mezitím
změní. Worker neregistrován, na potvrzení toolu ElevenLabs stále čekáme.
Opakovaná cílená read-only kontrola Supabase potvrdila, že doplňující migrace
20261002_write_audit_tool_names.sql stále chybí (appointment_write a
needs_reconciliation nejsou v audit view, uncertain alert není ve funkci).

Medicus handoff balíček 1ddee07 připraven na serveru v
`C:\db_bridge\staging\medicus-handoff1`; SHA256 archivu
D4F88BCE230C7653A491325BD69E8227412E34CF404FA2DB2EDF17FCCE3D8148.
V produkčním Pythonu/FastAPI prošlo 17 cílených testů s testovacími závislostmi
izolovanými v staging/.testdeps (embedded Python ignoruje PYTHONPATH, proto
runner doplňuje sys.path přímo). Důkaz na serveru verification.json.
Produkční API soubor hash odpovídá očekávanému c767598; writes/cancel/review/
durable handoff jsou false. Operator ingest URL/token/tenant v Medicus configu
zatím chybějí; doplnit na hostu bez výpisu tajemství při aktivaci.
Uživatel právě upravuje ElevenLabs handoff_summary dle zaslaného postupu;
potvrzení uložení dosud nepřišlo. Produkční API ani worker nebyly přepnuty.

Medicus handoff release připraven v `../medicus-handoff-release`, branch
release/handoff1, založený na skutečném serverovém c767598. Server má vedle toho
dirty LASER úpravy; nepřepisovat celý checkout. Izolovaná API změna a worker
mají 16 lokálních testů, instalační PowerShell syntakticky ověřen.
API běží přes SYSTEM task `Medicus Local API`, pracovní adresář
C:\db_bridge\medicus_availiability. Nový worker dosud není registrovaný.
Před zapnutím ověřit ElevenLabs X-Conversation-Id a request_id; jinak endpoint
záměrně odmítá neidentifikovatelné handoffy. Postup v HANDOFF_RELEASE.md.

Nejnovější nasazení: Operator `pilot-2026-10-02.handoff1` aktivní. GitHub
release/handoff1: backend fbce634, dashboard 65867dd; stromy shodné s lokálně
testovanými f7ef629 / 3ef1187. Na serveru prošlo 14 backend testů, 5 proxy
testů a build. Autorizované čtení 10 hovorů a detailu ověřilo nový kontrakt
staff_requests i zachování hypercare. API/dashboard/worker běží, health task
obnoven. Rollback: hypercare1. Medicus doručovací worker zatím není nasazen;
živé doručení z agenta ani SMS tím není potvrzeno. Žádné DB migrace ani
Firebird změny při tomto nasazení.

Operator handoff inbox a personální zobrazení připraveny v izolovaných
release worktrees nad hypercare1. Ověřeno 17 cílených backend testů (včetně
propojení Medicus–Operator, ztraceného ACK, pozdního post-call a tenant izolace),
5 dashboard proxy testů a produkční build. Nová DB migrace pro inbox není
potřeba. Nasazení inboxu a workeru dosud neproběhlo; produkce zůstává hypercare1.

Samostatný durable handoff: lokálně oddělen příznak `enable_durable_handoff`
od schvalování rezervací. API, worker a recovery sdílejí stejnou podmínku;
worker/recovery vyžadují existující store. Cílené testy ověřují předání při
vypnutých rezervacích, deduplikaci a odmítnutí staff endpointu. Produkční
instalace workeru a Operator inboxu dosud neproběhla.

Novější stav po obnovení: admin přehled nasazen jako hypercare1 (backend 5aaf00d,
dashboard 0c6cdd1 se shodným stromem jako lokální b4f7801). Serverové testy 10+5,
build a živá konzistence seznam/detail prošly. Operator procesy běží, veřejné
health/login 200, neautorizované čtení 401. Supabase forward migrace stále chybí;
Firebird beze změn. Předchozí pauza a prepared-only poznámky níže jsou historické.

Poslední krok před druhou pauzou: admin hypercare přehled připraven v lokálních
commitech backend 5aaf00d / dashboard b4f7801. Testy 10+5, TypeScript, build a
cílený lint prošly. Není nasazeno. Produkce je search1. Nová Supabase migrace
20261002_write_audit_tool_names.sql zatím dle read-only kontroly chybí.
Uživatel výslovně požádal dokončit tuto dílčí přípravu a znovu pozastavit cíl.
Rozsah celého cíle zachován; pokračovat až po dalším pokynu.

Aktualizace 2. 10.: telefonní filtr nasazen ve vydání Operator search1
(backend c81fefd, dashboard 9128bdb). Serverové testy 12+4 a build prošly.
Živé autorizované hledání podle existujícího čísla našlo očekávaný hovor;
neautorizované hledání odmítnuto 401. Všechny tři Operator procesy běží.
Vizuální kontrola a nový hlasový hovor zůstávají otevřené. Bez Firebird změn.

Původní údaj o 98 testech popisoval začátek práce. Jednotlivé aktuální běhy
jsou doložené v implementace.md; počet testů není důkaz hotového pilotu.

| Oblast | Lokálně doloženo | Zbývá |
| --- | --- | --- |
| Dostupnost | Intervaly, výjimky rozvrhu, LASER, svátky, časové filtry, čtení živého Firebirdu | Srovnání s Medicus UI a klientem |
| Zápisové mapování | Triggery, historie, kaskádový OBJPROC a capture před/po | Řízené GUI create/move/cancel, vazba pacienta a dvojice MAIN/LASER, synchronizační tabulky |
| Žádosti | Tokeny, trvalost, idempotence včetně výpadku DB, list/detail/reject a UI | Approve executor, konzistence a souběh s ručním Medicusem; nevycházet z odhadnutých vazeb |
| Handoff | Trvalé uložení, worker, inbox, retry, ruční obnova a propojené testy | Servisní instalace, živá síťová cesta, skutečný transfer/callback |
| Telefon | Oprava přepisování kontaktu pozdním webhookem, tenant-scoped čtení/hledání | Nasazení a nový reálný hovor |
| E-mail | Failure outbox; PostgreSQL 16 testy a read-only ověření aplikované Supabase migrace 2. 10. 2026 | Živý řízený Resend test a nasazení workeru |
| SMS | Zamýšlený příjemce: číslo pro živé přesměrování | Twilio odesílatel/capability/přístup; implementace a ověření |
| ElevenLabs | Celý kandidát promptu, všech pět webhook fragmentů | Živá konfigurace, runtime binding, provider validace, publikace a hlasové testy |
| Celý pilot | Schválený návrh, tisknutelné otázky/pravidla, scénáře a deployment podklady | Chybějící funkce výše, klientské testy, rollout/rollback a doložené produkční verze |

## Pokračování po obnovení cíle (2. 10. 2026)

Nejnovější pokyn uživatele: pokračovat od aktuálního stavu. Práce obnovena bez
duplikování dokončených kroků. Phone2 zůstává posledním ověřeným nasazením;
připravuje se oddělené vydání hledání celého čísla (backend c81fefd, 12 cílených
testů). Dashboard kandidát je v operator-dashboard-phone-release. Dřívější
poznámka o pauze níže je historická. Celý pilot a původní podmínky zůstávají.

Pozdější stav: na výslovnou žádost uživatele po dokončení dílčího nasazení
pozastavit cíl. Operator phone2 (87db8c9) nasazen, 10 testů prošlo i na serveru,
API/worker běží, veřejné endpointy a autorizované čtení HTTP 200. Bez restartu
serveru/Medicusu a bez DB změn. Nový skutečný hovor není ověřen. Níže uvedený
aktivní stav popisuje předchozí obnovení; během pauzy automaticky nepokračovat.

Cíl je aktivní, původní rozsah zachován. Uživatel aplikoval Supabase migraci;
živý read-only dotaz ověřil shodu nové i přejmenované původní funkce a ACL.
Důkaz je v operator_backend/tests/sql/live_handoff_migration_verification.json.
Nová větev e-mailu zatím nemá důkaz skutečného doručení. Runtime role nemá
přístup k privátní konfiguraci/outboxu ani schématu cron; oprávnění nerozšiřovat.

Uživatel nemá přihlašovací údaje do frontendu Medicusu. GUI experiment se
odkládá; pokračovat v nezávislé backendové práci. Přímý SQL zápis není důkaz
správného chování frontendu. Ve Firebirdu jsou výslovně zakázány změny schématu,
procedur, triggerů i dalších databázových objektů. Případné datové zápisy pouze
do konkrétních ověřených tabulek ověřeným postupem. Neověřené cesty nezapínat.

ElevenLabs/Twilio živý přístup, klientské testy a koordinované nasazení zůstávají
nedokončené. Dřívější blokace nástrojů pro UI je historické zjištění, nikoli důkaz
nemožnosti pokračovat v backendu. Dočasné blokace termínů zůstávají návrhem;
uložená pending karta nezaručuje držený termín.
