# Stage 1 — mapování Medicus / LASER k ověření personálem
## Stav přílohy vydání — 5. 10. 2026

Následující původní registr zachycuje stav k 1. 10. a historii upřesňování.
Jeho tehdejší zákaz zahájení dalších etap není aktuální pokyn: uživatel následně
schválil konsolidovaný návrh a staff-first variantu. Aktuální stav implementace
a nasazení popisuje `../pilot_v2_review/stav_cile.md` a backend `CURRENT_STATE.md`.
Odpovědi klienta mají následovat po představení první verze; dosud neověřené
významy databázových vazeb tím nejsou automaticky potvrzené.

Tato příloha obsahuje sanitizované kopie důkazů. Testovací IDPAC jsou odstraněna;
identifikátory testovacích rezervací zůstávají pro dohledání omezených snímků.
`publication_manifest.json` zaznamenává otisky originálu a vydané kopie.
Originály a podrobné snímky zůstávají v dosavadním lokálním úložišti a chráněném
adresáři serveru. Export souborů sám není novým testem databáze.

| Důkaz | Co prokazuje | Co neprokazuje |
| --- | --- | --- |
| gui_skin_cycle_20261005.json | Vytvoření, přesun se zachováním ID a zrušení běžné prohlídky přes GUI; následný úklid | Správnost všech ostatních kategorií |
| gui_scan_pair_20261005.json | Samostatnou anonymní rezervaci LASER, oddělenou rezervaci lékaře a správné čtení obsazenosti | Kanonickou kategorii okamžité prohlídky po skenu ani automatickou vazbu obou GUI rezervací |
| api_gui_tests_20261005.json | GUI zobrazení tehdejších API zápisů včetně barev; historickou chybu chybějícího LASER zápisu | Úspěch pozdější opravené párové implementace |
| staff_first_pair_cycle2_20261005.json | Opravený živý API cyklus vytvoření/přesunu/zrušení obou částí a úklid | Hlasový tok ani GUI zobrazení nového páru |
| staff_approval_move_cycle_20261005.json | Živý cyklus přes staff HTTP, stejné identifikátory při přesunu, obohacený souhrn a úklid | Ověření identity hovorem, nejistý commit ani nové GUI ověření |

Historické neúspěchy ponecháváme pro dohledání příčiny. Aktuální úspěšný test
nenahrazuje chybějící druh důkazu; původní omezení jednotlivých zpráv zůstávají.

## Původní registr a historie
**Stav: DRAFT_FOR_HUMAN_VALIDATION. Datum 1. 10. 2026.**

Tento balíček je navržený jediný registr mapování pro další revizi. Není schválenou
business specifikací a nesmí se bez potvrzení použít pro změnu chování. Stage 2–7
nebyly zahájeny. Produkční chování, konfigurace, prompt, schvalování ani rezervace
nebyly v rámci tohoto auditu změněny.

## Co předkládáme ke kontrole

- [Nový tiskový podklad a konsolidovaný návrh pilotu v2](../pilot_v2_review/README.md):
  18 otázek pro klienta, 24 pracovních pravidel, formulář zpětné vazby a plán
  implementace ke schválení. Navazuje na společnou revizi USER-REVIEW-01 až45.

- [Inventář všech 40 pravidel](inventory.md): každé má ID, doménu, význam, DB
  reprezentaci, implementaci, důkazy, jistotu, dopad, reprodukci a otevřenou otázku.
- [Strojově čitelný registr](rules.json) a jeho [navržené schéma](schema.json).
- [Aktuální serverový snímek](observed_server.json): efektivní business pravidla,
  povolené příznaky API, slovníky obou DB, definice procedur, anonymní časové
  intervaly 7. 10. a otisky zdrojového kódu. Neobsahuje pacientská jména, IDPAC,
  telefony, klinické poznámky ani přístupové klíče. Jména personálu jsou potřebná
  k validaci mapování lékařů.
- [Výsledky reprodukovatelných kontrol](validation_results.json).

## Aktuální revize dodaného promptu

- [Porovnání s dohodnutými pravidly a krátké otázky pro personál](prompt_comparison_2026-10-01.md).
- [Přesná kopie promptu dodaného uživatelem](production_prompt_supplied_2026-10-01.txt); zdroj, nikoli upravený návrh nebo živě ověřená konfigurace.

## Jak číst jistotu

**CONFIRMED** znamená potvrzený přesně popsaný fakt, například dva odlišné
databázové namespace. Neznamená, že personál schválil všechna navazující pravidla.
**PROBABLE** je podložený výklad bez dostatečného nezávislého potvrzení provozu.
**UNCLEAR** znamená, že nelze určit správný business výsledek. **CONFLICT** znamená
konkrétní rozpor mezi zdroji. Počty po USER-REVIEW-10: 7 CONFIRMED, 8 PROBABLE, 18 UNCLEAR, 7 CONFLICT.

Uživatel v USER-REVIEW-01 potvrdil rozlišení služeb a skin bez automatického scanu. Nejde o přímé potvrzení recepčními ani o schválení technického DB mapování. Podrobnosti jsou v [záznamu společné revize](review_log.md). Starší dokument,
který používá slovo „confirmed“, je historický zdroj, nikoli automatické dnešní
potvrzení. Funkční test starého pravidla prokazuje implementaci, nikoli jeho
klinickou/provozní správnost. UNCLEAR/CONFLICT se v další implementaci nesmějí
proměnit v automatickou nabídku/zápis; bezpečné odmítnutí či předání musí mít
samostatně schválený rozsah.

## Zdrojový registr a časová platnost

| Klíč | Typ důkazu a přesný zdroj | Omezení |
| --- | --- | --- |
| LIVE | observed_server.json, zachyceno 2026-10-01 18:20:30 UTC / 20:20:30 Praha | Dvě postupně čtené read-only transakce, nikoli atomický snímek obou DB ani historie hovoru. |
| CODE | Konkrétní soubor a symbol u každého MAP; serverové řádky/AST hashe v LIVE.files | Lokální a produkční kód se liší; rozdíly níže. |
| DOC-ACT | research/db-mapping/activity_type_mapping.md | Historická interpretace, mj. původní skin followup a širší blocker list. |
| DOC-SCHEDULE | research/db-mapping/schedule_interval_findings.md | Audit staršího časového okna; nelze jím potvrdit dnešní personální role. |
| DOC-LASER | research/db-mapping/laser_medicus_instance_audit.md, 2026-07-31 | Zjištění oddělené instance; tehdejší „runtime nečte LASER“ už neplatí. |
| DOC-ROLLBACK | research/db-mapping/phase3_rollback_insert_test.md, 2026-05-05 | Ověření technického insert/rollback, nikoli kompletní dnešní business pravidlo. Testovací IDPAC do auditu nekopírujeme. |
| CONTRACT | docs/elevenlabs_current_contract.md | Verzovaný text, nikoli export skutečného aktuálního agenta; přímý booking scope už neodpovídá containment konfiguraci. |
| USER-OCT7 | Uživatelem vložený request dermatoscope_first od 2.10. a response s 7.10.15:00/15:10/15:50 u Marty Školařové; sdělení o obsazenosti personálem | Dokládá nabídku a hlášení personálu. Chybí časově shodný historický snapshot DB. |
| USER-OCT1 | Uživatelem vložená odpověď s Šlosárovou13:20 a výrokem agenta Selecká13:20 | Dokládá míchání řeči; neprokazuje, že se tato kombinace zapsala. |
| HISTORY-ARRIVAL | [Audit historie commitů](arrival_history.md), git fetch + log --all a offline reprodukce | Dokládá kódovou sémantiku, nikoli schválení provozních pravidel. |
| USER-REVIEW-45 | Uživatel1.10.2026: kontrolu lze nabídnout i krátce před doporučeným datem | V krátkém hledacím okně a v mezích požadavku pacienta; přesný počet dní otevřen. Pouze návrh. |
| USER-REVIEW-44 | Uživatel1.10.2026: kontrolu v budoucím odstupu hledat explicitně v krátkém okně dvou týdnů nebo měsíce podle zátěže | Lze i za rok; šest měsíců není maximální vzdálenost objednání. Přesná délka a poloha okna otevřené. |
| USER-REVIEW-43 | Uživatel1.10.2026: obecné preference lékaře platí i pro oba typy kontrol | Bez preference napříč lékaři, původního automaticky neupřednostňovat. Pouze návrh. |
| USER-REVIEW-42 | Uživatel1.10.2026: followup = vyšetření po skenu bez následné prohlídky; regular_check = kontrola po zákroku/vyšetření | Význam potvrzen, DB rozpor regular_check trvá. Interval dle sděleného doporučení, jinak personál. Pouze návrh. |
| USER-REVIEW-41 | Uživatel1.10.2026: prohlídka / s dermatoskopem / navazující kontrola; kontrolu na výslovnou žádost lze v návrhu objednat | Historie jako podklad; rok od zákroku pouze nejistý předpoklad. Konflikt kategorií v lokální dokumentaci přetrvává. |
| USER-REVIEW-40 | Uživatel1.10.2026 předběžně: opakovaná dermatoskopie patrně stejná služba, minulá objednání jako kontext | Výslovná nejistota; význam kontroly versus nového skenu a DB mapování neuzavřeny. |
| USER-REVIEW-39 | Uživatel1.10.2026: před novým objednáním stručně shrnout službu, lékaře, datum a příchod a získat výslovné potvrzení | Kompaktní formulace; potvrzení volajícího není důkaz zápisu. Pouze návrh. |
| USER-REVIEW-38 | Uživatel1.10.2026: technická chyba -> informovat volajícího, zaznamenat, notifikovat admina a přesměrovat personálu; hovor prostě neukončovat | Nejistý výsledek operace nepotvrzovat jako úspěch; při selhání transferu platí dřívější fallback. Pouze návrh. |
| USER-REVIEW-37 | Uživatel1.10.2026: po obsazení nabídnutého termínu nové hledání a nový výběr; původní rezervaci zachovat do úspěšného přesunu | Business požadavek, nikoli ověřená transakční implementace; pouze návrh. |
| USER-REVIEW-36 | Uživatel1.10.2026: při více budoucích rezervacích zjistit požadovanou návštěvu a před změnou ji výslovně potvrdit | Žádný automatický výběr první/nejbližší rezervace; pouze návrh. |
| USER-REVIEW-35 | Uživatel1.10.2026: pro dobrovolné krajní dohledání použít celé rodné číslo | Navazuje na volbu RČ/personál při více shodných kartách; standardní lookup beze změny. Pouze návrh. |
| USER-REVIEW-34 | Uživatel1.10.2026: při více shodných kartách nabídnout dohledání podle RČ nebo přímé předání personálu | Dobrovolný fallback, nikoli rutinní last4; pouze návrh. |
| USER-REVIEW-33 | Uživatel1.10.2026: při nenalezené kartě zopakovat jméno, příjmení a datum narození; při potvrzení původních údajů nabídnout personál | Opravené údaje znovu vyhledat; bez automatického požadavku na RČ. Pouze návrh. |
| USER-REVIEW-32 | Uživatel1.10.2026: standard jméno + datum narození; rutinní last4 odstraněno na požadavek klienta, RČ pouze krajní možnost | Historie commitů v této revizi neověřena; přesný fallback zbývá upřesnit. Pouze návrh. |
| USER-REVIEW-31 | Uživatel1.10.2026: za jinou osobu lze návštěvu také přesunout nebo zrušit | Pracovat s kartou a rezervací cílového pacienta; postup ověření samostatně. Pouze návrh. |
| USER-REVIEW-30 | Uživatel1.10.2026: lze objednat jinou osobu s dohledanou existující kartou pacienta | Použít IDPAC cílového pacienta, ne automaticky volajícího; ověření identity a změny za jinou osobu samostatně. |
| USER-REVIEW-29 | Uživatel1.10.2026: agent nezakládá pacientské karty; pro termín je nutné IDPAC existující karty | Při nedohledání předat personálu podle pravidla mimo scope; pouze návrh. |
| USER-REVIEW-28 | Uživatel1.10.2026: prozatím umožnit zrušení/přesun i těsně před návštěvou, bez časové hranice | Případné omezení ověří s klientem; pravidla nového termínu zůstávají. Pouze návrh. |
| USER-REVIEW-27 | Uživatel1.10.2026: běžnou dermatoskopii přesouvat/rušit jako celek, sken i prohlídku; změnu jedné části předat personálu | MAP-29/30/31, technické párování a provedení zůstávají otevřené; pouze návrh. |
| USER-REVIEW-26 | Uživatel1.10.2026: při přesunu stejné preference jako při objednání, včetně preference zmíněné dříve v hovoru | Bez preference hledat napříč lékaři; původního automaticky nezachovávat. Pouze návrh. |
| USER-REVIEW-25 | Uživatel1.10.2026: bez preference lékaře nejbližší vyhovující termíny napříč všemi ordinujícími lékaři | Potvrzený návrh; řazení nesmí zvýhodnit ID lékaře. Bez runtime změn. |
| USER-REVIEW-24 | Uživatel1.10.2026: samostatný roční seznam svátků defaultně blokující dostupnost nezávisle na rozvrhu DB | České svátky a všechny roky hledání jsou návrhový výklad; konkrétní data budou ověřena při implementaci. |
| USER-REVIEW-23 | Uživatel1.10.2026: pouze pondělí až pátek, víkendový slot nenabízet ani jako výjimku | Podezření na chybu rozvrhu, příčina neověřena. Svátky v týdnu samostatný bod; pouze návrh. |
| USER-REVIEW-22 | Uživatel1.10.2026: časové omezení platí pro požadovaný příchod včetně skenu před prohlídkou | MAP-25/27, potvrzený návrh; bez změny runtime. |
| USER-REVIEW-21 | Uživatel1.10.2026: preferovaný lékař, rozšíření hledání nejvýše na 6 měsíců při respektování omezení volajícího; poté volba jiného lékaře/personálu | Potvrzený návrh. Test přepojení odložen po implementaci. Bez produkčních změn. |
| USER-REVIEW-20 | Uživatel1.10.2026: callback ze zmeškaného hovoru při nedostupnosti; při technické chybě admin alert a zachování požadavku pro personál | Oficiální ElevenLabs/Twilio dokumentace ověřena; skutečný telefonní fallback a caller ID vyžadují test. Bez změn produkce. |
| USER-REVIEW-19 | Uživatel1.10.2026: plazma/PRP, laser a další zákroky mimo první scope; obecně předat původní požadavek personálu bez náhradní nabídky kožního | Plazma kandidát pozdějšího rozšíření. Produkční dataset při této revizi znovu nečten; prompt beze změny. |
| USER-REVIEW-18 | Uživatel1.10.2026: před08:00 jen pohotovost, běžně nenabízet; návrh emergency tagu a okamžitého předání | Rezervování a doporučení konkrétního času ověří klient; tag není oprávnění API emergency=true. |
| USER-REVIEW-17 | Uživatel1.10.2026 určil pevný prozatímní default minimálně1 hodina od zavolání | Hodnota schválena pro návrh; klientské výjimky později. Vazba na příchod a technický zdroj času jsou rozlišené od explicitního výroku. |
| USER-REVIEW-16 | Uživatel1.10.2026 výslovně potvrdil dle poznámek klienta příchody Po–Pá11:00, Po15:00, Út–Čt16:00, Pá14:00 | Časy potvrzené; koncové hranice technických bloků a dermatoskopická transformace zatím ne. |
| USER-REVIEW-15 | Uživatel1.10.2026 zadal pracovní návrh bucketu příchodu také pro dermatoskopii při zachování skenu před prohlídkou | Detail prvního/dalších příchodů upřesní personál, větší buffer zatím nepožadován; bez implementace. |
| USER-REVIEW-14 | Uživatel1.10.2026: předpoklad11:15→scan11:00, žádost ověřit historii | Propojení se společným příchodem si uživatel ještě upřesní. |
| USER-REVIEW-13 | Uživatel1.10.2026 předpokládá bucket i pro dermatoskopii, sken T−15 pro pacienta na začátku bloku | Rozlišení společného příchodu a individuální rezervace skeneru pro další pacienty neuzavřeno. |
| USER-REVIEW-12 | Uživatel1.10.2026 potvrdil společný čas příchodu a postupné zvaní pacientů z čekárny | Princip potvrzen, rozsah služeb/hodin a postup při uplynulém příchodu ještě otevřené. |
| USER-REVIEW-11 | Uživatel1.10.2026: databáze je rozhodující pro aktuální personální/kalendářová data; nahrazení Ferencze Hrudovou si ověří | Priorita DB jména potvrzena, historie změny a individuální pravidla otevřené. |
| USER-REVIEW-10 | Uživatel1.10.2026: prohlídky všichni ordinující lékaři; jeden společný přístroj a scan kalendář | Počet dvou lékařů je předpoklad; přesná DB identita zdroje a dostupnost obsluhy nejsou potvrzeny. |
| USER-REVIEW-09 | Uživatel1.10.2026 předpokládá stejný průběh opakované a první dermatoskopie včetně možnosti odložené prohlídky | Předpoklad k potvrzení, nikoli uzavřené DB mapování nebo obecný klinický závěr. |
| USER-REVIEW-08 | Uživatel1.10.2026: běžná prohlídka jedno políčko; více políček pouze po posouzení personálem | Business pravidlo potvrzeno, technická vazba na konkrétní rozvrhový blok ještě otevřená. |
| USER-REVIEW-07 | Uživatel1.10.2026: délka prohlídky podle lékaře;10min běžně předpokládá jen u Bednáře, připouští jiné nálezy | Historický DB audit obsahuje více10min lékařů; délka výkonu vs rozteč a dnešní rozvrh zůstávají otevřené. |
| USER-REVIEW-06 | Uživatel1.10.2026 předpokládá pevný15min sken; krajně může být delší, agent to pravděpodobně neumí posoudit | Výslovně nejistá délka, zůstává k potvrzení. |
| USER-REVIEW-05 | Uživatel1.10.2026 souhlasí: agent prohlídku po více než3 měsících automaticky nenabízí a předává personálu | Objednání na místě je očekávání, nikoli zaručený krok; role schvalující výjimku zůstává otevřená. |
| USER-REVIEW-04 | Uživatel1.10.2026: po samotném skenu osobní prohlídka jindy, běžně nejpozději do3 měsíců, krajně do6; po3 měsících může sken ztrácet relevanci | Klinické/provozní pravidlo sdělené uživatelem; oprávnění výjimky, přesné hranice a DB mapování neuzavřeny. |
| USER-REVIEW-03 | Uživatel1.10.2026: agent má umožnit samotný sken na výslovnou žádost, ale běžně jej nenavrhovat | Schválený business požadavek; bez schválení implementace, DB mapování nebo přímých zápisů. |
| USER-REVIEW-02 | Uživatelské upřesnění1.10.2026: po scanu běžně ihned osobní prohlídka; výjimečně lze jen scan | Nepotvrzuje délky, DB aktivity ani oprávnění agenta objednávat výjimku. |
| USER-REVIEW-01 | Uživatelské vysvětlení 1.10.2026: kožní prohlídka hrazená pojišťovnou; placený dermatoskop samostatně, sken personálem a následné posouzení lékařem | Potvrzuje business rozlišení, nikoli délku, DB aktivity ani způsob předání výsledků. |
| USER-SCOPE | Uživatel: celé schvalování zatím návrh; nové zadání: pouze Stage1 bez změny produkce | Aktuální hranice oprávnění. |
| DESIGN | docs/staff_approval_recovery.md a docs/pending_slot_holds_proposal.md | Návrhy; nejsou důkazem provozní funkcionality. |
| TEST-SAFETY | tests/test_availability_safety.py | Jednotkové příklady intervalu, času a lékaře. |
| TEST-LASER | tests/test_laser_calendar.py | Mj. fixture kolize7.10.; procedura opakování je v části testů mockována. |
| TEST-FILTERS | tests/test_availability_search_filters.py | Tvar dotazu a odpovědi; ne všechny provozní hranice. |
| TEST-BUSINESS | tests/test_business_rules.py | Výchozí pravidla a mockované zápisy, nikoli schválení významu služeb. |
| TEST-PATIENT | tests/test_patient_lookup_name_matching.py | Syntetické identity; neověřuje reálné oprávnění volajícího. |

Všechny relativní cesty v registru zdrojů jsou od kořene repozitáře, cesty k
artefaktům v tomto dokumentu od adresáře tohoto balíčku.

## Aktuální implementační vrstvy

Lokální HEAD: `5dab343a75e2df3060b679c988f777d928078765` s existujícími změnami.
Serverový HEAD: `c767598749d8b02aa8912eff1ed2990151ce040f` s manuálně nasazenými
opravami. Samotný Git commit tedy nepopisuje celý nasazený stav.

Engine, agent_context a laser_calendar mají shodný SHA256 lokálně i na serveru.
U business_rules, appointment_write, patient_lookup a handoff_summary se liší
souborové otisky, ale kontrolované funkce mají shodné AST. To samo neprokazuje
shodu importů/globálních konstant ani celého procesu. Search se funkčně liší
v compact_options kvůli lokálnímu offer_tokenu. API se liší v několika funkcích
kvůli lokálním prototypům/telemetrii. Úplný seznam je ve validation_results.json.

Efektivní serverová pravidla vznikají hlubokým překrytím example konfigurace
server-local souborem; následně se aplikují na agent_context konfiguraci.
Aktuálně je z nabídek povolené jen `skin`, všechny finální booking příznaky jsou
false, globální writes/cancellations jsou false a LASER read je enabled.
Chybějící enable_staff_approval v serverové konfiguraci není důkaz spuštěných
schvalovacích karet; prototyp není nasazen. Hodnota rules.version zůstává
2026-07-production-v1, a proto sama neidentifikuje dnešní override.

## Souhrnný inventář služeb

Hodnoty v tabulce jsou pozorovaná konfigurace, nikoli potvrzená provozní pravidla.
Číselné aktivity jsou vždy v MAIN, pokud je výslovně neuvedeno jinak.

| Interní služba | Aktivita | Délka v kódu | Nabídka nyní | Rozhodnutí |
| --- | --- | --- | --- | --- |
| skin | NULL | interval rozvrhu | ano | MAP-02: uživatel potvrdil bez automatického scanu; starší followup výklad pro tuto službu překonán. |
| dermatoscope_first | 1 | interval lékaře + scan15min před ním | ne | MAP-03: chybí schválený úplný write mapping LASER. |
| dermatoscope_followup | 2 kontrola po skenu | interval | ne | MAP-04: upřesnit terminologii a zdroje. |
| regular_check | 5 Sken znamének2 a vyšší | interval | ne | MAP-05: label Kontrola po scanu je v rozporu s názvem aktivity. |
| plasma | 3 laser výkony + marker | 30min | ne | MAP-06: délka/lékař/marker potřebují potvrzení. |
| laser | 3 | fixed, ale minutes=NULL | ne | MAP-07: nedostatečná specifikace jednotlivých výkonů. |
| dermatoscope_reservation | 6 | interval | ne | MAP-08: technická blokace, nezaměnit s LASER6. |

## Lékaři, kalendáře a pracoviště

| MAIN IDUZI | Aktuální jméno v DB | Poznámka k auditovaným pravidlům |
| --- | --- | --- |
| 1 | Tereza Pérez | Config říká active, poznámka současně „not part of first production scope“; prázdný allowlist ji nevyřazuje. |
| 2 | Rostislav Bednář | Aktivní varianta podle pozdějšího historického auditu. |
| 4 | Rostislav Bednář | Globálně vyřazen; samotná shoda jména není identita kalendáře. |
| 3 / 6 / 7 | Správce / Recepce / Laser | Technické názvy, ale role není v runtime explicitně filtrována. |
| 8 | Mária Bartoňová | Jediná povolená u plasma v configu, klinickou způsobilost to nedokazuje. |
| 10 | Petra Pospíšlová | Globálně vyřazena; absence rozvrhu není důkaz ukončení činnosti. |
| 11 | Dušana Selecká | Služby nemají individuální schválenou matici eligibility. |
| 12 | Marta Školařová | Kalendář v doloženém příkladu7.10. |
| 13 | Zuzana Šlosárová | Historicky různé intervaly podle konkrétního dne/kontextu. |
| 15 | Tamara Hrudová | KONFLIKT: config known i starší dokument mají Filip Ferencz. |

LASER IDUZI: 1 Eva Bednářová; 2 Rostislav Bednář; 3 Správce; 4 Petra Pospíšilová;
5 Sken Focení skeny; 6 Jitka Horká; 8 Iveta Hojgrová; 15 Mária Bartoňová.
Podobná jména nejsou potvrzené cross-DB mapování. Pro runtime scan je nastaveno
LASER kalendář5/pracoviště1. V rozvrzích jsou MAIN pracoviště1,2 a LASER1,2,9,12;
jejich provozní názvy, místnosti a sdílené zdroje zůstávají neověřené.

Úplný číselník LASER aktivit je ve snapshotu. Zvlášť relevantní jsou 13
„Dermatoskop potvrzeno“ a 28 „Dermatoskop“; z názvu nelze odvodit povolený stavový
přechod nebo cílový typ nové rezervace. V tomto auditu jsme nečetli karty pacientů.

## Podezřelé nekonzistence a otevřená pravidla

1. **MAP-10/12: personální identita a eligibility.** ID15 změnilo jméno oproti
   configu, Tereza má rozpornou scope poznámku a technické účty nemají explicitní
   filtr podle role. Potřebujeme schválenou matici, ne odhad z existence rozvrhu.
2. **MAP-02/05/22: druh služby a scan.** Skin followup byl vyřešen USER-REVIEW-01 (bez scanu). Kontrola vs opakovaný scan
   a seznam sdílených blockerů si odporují v různých zdrojích.
3. **MAP-20/21: výjimky a týdenní rozvrh.** Procedura umí výjimky, vstupní objevování
   kontextů je ale závislé na pravidelném rozvrhu. Význam TYPTYD není potvrzen.
4. **MAP-15/16/17/40: délka a hranice.** Nejmenší interval kontextu není automaticky
   správná délka každého výkonu; chybějí schválené buffery a speciální intervaly.
5. **MAP-24/25: pacientský příjezd.** Budoucí technický termín může dostat již
   uplynulý společný čas příjezdu. Konce bucketů jsou zahrnuté; dopolední příchod11:00 byl potvrzen USER-REVIEW-16, přestože historická poznámka obsahuje Draft.
6. **MAP-28–33: zápisové významy.** Derm create jen v MAIN, přesun delete+create,
   fyzické smazání, odhad vazby podle sousedního času a caller-supplied verification
   nejsou dostatečná business specifikace. Zápisy zůstávají vypnuté.
7. **MAP-34/35/38/39: potvrzení a předání.** HTTP200, handoff summary, pending návrh
   ani lokální hold samy neznamenají potvrzenou rezervaci/převzetí personálem.

## Otázky pro personál — připravené k jednomu společnému průchodu

| Priorita | Co potvrdit | Způsob odpovědi / vlastník |
| --- | --- | --- |
| P0 | Skin bez scanu již potvrzen uživatelem. Zbývá význam prvního/opakovaného scanu, kontroly a přesné aktivity v MAIN i LASER. | Vedoucí recepce + klinický garant: vyplnit tabulku služeb, u každé ano/ne scan a konkrétní UI typ. |
| P0 | Kdo je MAIN15 a od kdy, scope MAIN1, aktivní Bednář, povolené služby každého lékaře? | Správce Medicusu + personál: ID, současná osoba, aliasy, platnost, služby a pracoviště. |
| P0 | Je LASER5/1 jediný scan zdroj? Co znamená aktivita13 vs28? | Pracovník scanu: zdroj, počet souběhů, čekající/potvrzený stav. |
| P0 | Pracoviště1/2 a LASER1/2/9/12: místnosti, provoz a sdílení lidí/přístrojů? | Správce + personál, odděleně podle databáze. |
| P0 | Délka návštěvy vs krok rozvrhu, scan offset/délka, mezera, konec bloku? | Klinický garant: konkrétní minuty pro každou službu, ne obecné „podle kalendáře“. |
| P0 | Jak UI vyhodnocuje OBSODLIS, zavřený den, TYPTYD a nulovou blokaci? | Správce Medicusu: konkrétní dva dny a jejich rozvrh; bez nutnosti sdílet pacienty. |
| P0 | Časy příchodů potvrzené USER-REVIEW-16. Zbývá zahrnutí konce, minimální předstih a kdo určuje emergency. | Vedoucí recepce: příklad16:00→15:00 a11:30 při aktuálním11:10. |
| P0 před zápisy | Identita pro čtení a změny, dítě/zástupce, nový pacient; cross-DB klíč a založení chybějící karty? | Klinický/provozní garant a správce, každá operace zvlášť. |
| P0 před zápisy | Přesun zachovává ID? Storno maže řádek? Jak propojit doctor+scan a upravovat sérii? | Správce porovná podporovaný postup v UI a DB vazby, nikoli pouze to, zda INSERT projde. |
| P1 před schvalováním | Kdo schvaluje, do kdy, jaká notifikace pacientovi a jak řešit manuální souběh? | Vedoucí recepce; konkrétní SLA/kanál, holdTTL zatím bez schválené hodnoty. |

Otázky jsou podklad pro review; žádná odpověď nebyla předpokládána ani nahrazena
stávajícím kódem. Neodesílali jsme je personálu za vás.

## Navržené schéma a pravidla schvalování specifikace

`rules.json` používá požadovaných deset polí z [schema.json](schema.json).
`implementation_location` zapisuje soubor a symbol (`::`) nebo JSON cestu (`#/`).
Řádek na aktuálním serveru lze dohledat v `observed_server.json → files → symbols`.
`evidence` odkazuje na zdrojový registr výše a konkrétní část LIVE.

Pro lidskou validaci navrhuji samostatný approval záznam, který zatím **není**
produkční databázovou tabulkou: rule_id, revision, rozhodnutí
(accept/reject/needs_evidence), schválený business výrok, reviewer/role,
reviewed_at, effective_from/to, reference na UI příklad a důvod. Odlišovat
schválení významu pravidla od povolení implementace a nasazení. Evidence z kódu
nesmí sama přepnout pravidlo na business-approved. Změna podkladů zneplatní
dotčené schválení, nikoli automaticky celou specifikaci.

## Doporučená validace Stage 1 a brána do další fáze

1. Personál se správcem projde inventář po doménách, nejdřív P0 otázky. Každé
   pravidlo dostane konkrétní odpověď, odpovědnou roli a datum platnosti.
2. V Medicus UI porovnat stejný den/čas s oběma DB: normální den, výjimku,
   opakovaný výskyt a příklad7.10. Pro každý záznam použít namespace, kalendář,
   pracoviště, aktivitu a interval. Neposílat do tohoto registru údaje pacientů.
3. Zvlášť projít syntetické hraniční příklady z inventáře: překryv, sousední konec,
   proměnlivý interval, společný příjezd, neznámý lékař a špatná kombinace služby.
   U nejasného pravidla personál nejdřív stanoví očekávaný výsledek.
4. Upravit pouze review registr podle odpovědí. Rozpor nezahladit; uchovat oba
   zdroje a explicitní rozhodnutí. Podle potřeby zopakovat pouze cílené read-only
   čtení. Žádné testovací zápisy v této fázi.
5. Znovu spustit kontrolu struktury/zdrojů, připojit výsledky a zbývající rizika.
   Human validation, zejména rozvrhové výjimky a write mapping, dnes **neproběhla**.
6. Před Stage2 předložit konkrétní návrh golden fixtures pouze ze schválených
   pravidel. Výslovný souhlas s další etapou je brána; tento audit jej nenahrazuje.

Konkrétní další implementace v rámci Stage1 je pouze zpřesnění dokumentace a
opakování čtecích/charakterizačních kontrol po review. Neopravujeme zde ani nově
zjištěné behaviorální nedostatky a neaktivujeme local-only approval prototyp.

## Ověření provedená nyní a praktické limity

- Read-only snapshot z obou DB, s databázově read-only transakcemi a rollbackem.
- Validace40 záznamů: všechna požadovaná pole, jedinečné ID, známé stavy,
  existující implementační soubory/symboly, porovnání serverových otisků.
- Offline charakterizace: koncový bucket, uplynulý spoken příjezd, absence
  exception-only kontextu, rozpor ID/jméno, nulový interval MAIN vs LASER,
  minimální interval v kontextu, konkrétní kolizní řádky7.10.
- **48 existujících testů prošlo:** availability12, LASER5, business20,
  patient lookup11. Testy neprovedly reálné pacientské zápisy a necertifikují
  správnost podnikových pravidel. Nový golden regression dataset Stage2 nevznikl.
- Ostatní reprodukční scénáře u pravidel jsou návrhy ke společnému ověření,
  nikoli tvrzení, že všechny byly spuštěny. Live ElevenLabs agent, audio a
  end-to-end booking nebyly v Stage1 ověřovány.

Reprodukce z kořene repozitáře (lokálně zvolený Python má závislosti projektu):

```powershell
../operator_backend/.venv/Scripts/python.exe tools/diagnostics/validate_stage1_mapping_audit.py
../operator_backend/.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_availability*.py'
../operator_backend/.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_laser_calendar.py'
../operator_backend/.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_business_rules.py'
../operator_backend/.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_patient_lookup_name_matching.py'
```

Nové read-only zachycení: spustit obsah
`tools/diagnostics/stage1_mapping_snapshot.py` na hostu Medicus přes Python se
správným pracovním adresářem `C:\db_bridge\medicus_availiability`. Výstup uchovat
jako novou revizi, nepřepsat historický snapshot bez aktualizace auditu.
