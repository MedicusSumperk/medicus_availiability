# Konsolidovaný návrh pilotu v2

Verze v2-review-1, připraveno 1. 10. 2026. **Schváleno uživatelem zprávou „Schvaluji“. Probíhá postupná implementace; schválení není potvrzením nasazení.**

## Výsledek a pořadí práce

Cílem je agent, který nabízí správné dostupné termíny, přiměřeně stručně ověřuje
pacienta, respektuje jeho preference a předává požadavky personálu bez ztráty
kontextu. Operator umožní personálu schvalovat žádosti a správci ověřit jejich
skutečný výsledek. Potom proběhne řízené ověření s klientem a nasazení pilotu v2.

Tento dokument sjednocuje USER-REVIEW-01 až 45, původní zadání sedmi etap,
dodaný produkční prompt a nové zadání tiskového podkladu. Pozdější potvrzené
významy služeb nahrazují starší nejisté interpretace, nikoli technické důkazy.
Aktuální produkční stav se před implementací a nasazením znovu ověří. Snímek
z 1. 10. a místní rozpracované soubory nejsou důkazem dnešního nasazení.

Pořadí upřesněné uživatelem 5. 10.: schválený návrh a dosavadní mapování →
ucelená první verze úprav po launchi podle nejlepšího dosavadního pochopení →
interní ověření → představení klientovi a konkrétní otázky → následné úpravy
podle zpětné vazby. Odpovědi na obchodní otázky nejsou předpokladem přípravy
první verze; použijí se již dohodnuté pracovní defaulty a evidované předpoklady.
Schválení
návrhu neznamená automatické potvrzení neznámého databázového mapování.
Původní etapové kontroly zůstávají; po každé se předkládají důkazy před pokračováním.

„První verze“ zde znamená první ucelené vydání tohoto refaktoru; historické
označení pilot v2 zůstává v názvech souborů. Není tím schváleno nahrazení
personálního schválení ručním přepisováním termínů ani prezentování simulace
jako funkčního živého zápisu. Technické vady řešit samostatně: neověřený zápis
do Medicusu nezapínat a nevyřešený souběh neskrývat mezi otázky na recepci.

## Přiložené podklady

- [PDF pro tisk](../../output/pdf/Dermacentrum_pilot_v2_podklad_pro_schuzku.pdf):
  šest stran otázek, čtyři strany pracovních pravidel, list pro zpětnou vazbu.
- [Upravitelný text schůzky](podklad_pro_schuzku.md) a [zdroj obsahu](meeting_content.json).
- [Porovnání dodaného promptu](../stage1_mapping_audit/prompt_comparison_2026-10-01.md).
- [Historie rozhodnutí](../stage1_mapping_audit/review_log.md),
  [technický inventář](../stage1_mapping_audit/rules.json).
- [Původní návrh schvalování](../staff_approval_recovery.md) a
  [návrh dočasných blokací](../pending_slot_holds_proposal.md).

Otázky jsou konkrétní ukázky práce recepce. SQL identifikátory, transakce,
časová pásma a izolaci tenantů ověří technik, ne recepční. Pracovní pravidla
popisují připravované chování; nejsou tvrzením, že už tak produkce funguje.

## Služby a správná karta

| Požadavek | Cílové chování | Stav mapování |
| --- | --- | --- |
| Běžná kožní prohlídka | Lékař, bez automatického skenu | Význam potvrzen; ověřit zápis a konkrétní interval |
| Prohlídka s dermatoskopem | Sken a bezprostředně navazující prohlídka | Ověřit společné příchody, dvojici zápisů a zdroje |
| Samotný sken | Jen na výslovnou žádost, informace o pozdější prohlídce | Varianta musí mít vlastní jednoznačný kontrakt; nezaměnit se spojenou návštěvou |
| `dermatoscope_followup` | Lékařská prohlídka po dřívějším skenu bez následného vyšetření | Význam potvrzen, ověřit příslušnou aktivitu a historický sken |
| `regular_check` | Kontrola po vyšetření nebo zákroku na výslovnou žádost | Význam potvrzen; aktivita 5 má rozporný název a nesmí být schválena odhadem |
| Plazma, laser, jiné zákroky | Personál, zachovat původní požadavek | Mimo první rozsah; plazma kandidát dalšího rozšíření |

Opakovaná či preventivní dermatoskopie není na základě dosavadního rozhovoru
samostatná pacientská služba. Technické aktivity první/další sken se nesmějí
bez důkazu sloučit nebo použít jako obecná kontrola.

Standard identity je jméno, příjmení a datum narození cílového pacienta, i když
volá někdo jiný. IDPAC je vždy v namespace konkrétní databáze. Agent nevytváří
kartu a neodvozuje jinou identitu z telefonního čísla. Telefon může pomoci
hledání, nikdy sám nestačí k ověření. Po nulové shodě zopakovat použité údaje;
opravené vyhledat, při potvrzených nenalezených údajích nabídnout volbu celého
RČ nebo personálu (výslovné upřesnění uživatele). Stejná volba platí po více
shodách. Návrhový default po neúspěchu zvoleného RČ: personál, bez
dalších cyklů. Rodné číslo nevystavovat v běžných logách, SMS ani Operator UI.

## Dostupnost a časy

Celý lékařský interval a celý interval skenu musejí být v dostupném rozvrhu,
bez kolizí, s jedním sdíleným přístrojem. Číst MAIN i LASER, opakování,
výjimky a všechny relevantní blokace; při nedostupnosti potřebného zdroje
nevrátit falešné volno. Personální kalendáře odlišit od technických účtů.

Pondělí až pátek, bez svátků všech dotčených roků. Víkend není povolená výjimka.
Před 08:00 běžně nenabízet; emergency označení nesmí samo odemknout rezervování
pohotovosti. Svátky se blokují ve výpočtu, nikoli umělými rezervacemi v Medicusu.

Časové preference i budoucnost posuzovat podle skutečného příchodu, včetně
skenu a společného bloku. Default předstihu je hodina od zavolání. Návrhová
technická pojistka: zároveň nepřijmout termín, jehož příchod již nastal při
pozdějším schválení. Čas začátku hovoru musí být ověřený; při absenci použít
čas prvního serverového zpracování jako konzervativní náhradní hodnotu a označit
jej v diagnostice. Tato náhradní hodnota je návrh, nikoli dřívější potvrzené pravidlo.

Společné příchody: Po–Pá 11:00, Po odpoledne 15:00, Út–Čt 16:00, Pá 14:00,
jen v příslušných blocích. Jeden pacient má běžně jedno lékařské políčko,
jeho délku určuje konkrétní rozvrh. Sken má předběžně 15 minut. Neodvozovat
10 minut pouze ze jména lékaře a nevytvářet několik skenů ve stejném intervalu
jen proto, že je společný příchod. Dokud není Q02 vyřešeno, neprohlašovat
přesnou transformaci dermatoskopie za potvrzenou.

Bez preference lékaře řadit vyhovující nabídky napříč ordinujícími lékaři
před omezením počtu výsledků. Při shodném příchodu navrhujeme sekundárně
čas prohlídky a stabilní identifikátor, nikoli střídání výsledků mezi dotazy.
S preferencí rozšiřovat u téhož lékaře nejvýše na šest kalendářních měsíců
od počátku požadovaného období a nikdy za pacientovo omezení. Tato přesná
interpretace kalendářních měsíců je návrhový default. Po neúspěchu volba
jiného lékaře nebo personálu, ne automatická změna.

Kontrola podle doporučení sděleného pacientem může být i za rok. Automatický
univerzální rok ani nejzazší klinická lhůta nejsou pravidlem. Návrh krátkého
filtru: cílové datum ±7 dní; při souhlasu pacienta s širším obdobím až ±15 dní,
jen pokud to doporučení a pacientovo omezení dovolují. Výkon porovnat na
reálných read-only dotazech. Neznámý interval předat personálu. Historické
objednání samo neprokazuje absolvování výkonu. Pro odloženou prohlídku po
samotném skenu nadále platí samostatná hranice tří měsíců a posouzení výjimky
personálem; nesmí se zaměnit za kontrolu v ročním odstupu.

## Potvrzení a schvalovací tok

**Zachovává se původně požadované schvalování personálem, nikoli přímé veřejné zápisy agenta.**

1. Backend vrátí ověřenou nabídku s neprůhledným identifikátorem, úplnými
   intervaly, službou, zdroji, verzí pravidel, hovorem a expirací.
2. Agent stručně sdělí službu, lékaře, datum a příchod. Pacient výslovně
   potvrdí konkrétní požadavek. Nový výběr vyžaduje nové potvrzení.
3. Ověřená identita a nabídka se spojí v trvale uložené žádosti.
   Agent řekne: „Žádost jsem předala personálu k potvrzení.“ Pouze pokud
   přijetí skutečně uspělo; neřekne „jste objednán“.
4. Operator ukáže žádost před přijetím post-call webhooku. Oprávněný personál
   ji schválí nebo odmítne. Změna obsahu znamená novou verzi a případně nový
   souhlas pacienta, nikoli tichou výměnu času při schválení.
5. Před zápisem backend znovu ověří identitu, původní rezervaci, dostupnost
   obou kalendářů a pravidla. Více kliknutí nebo opakovaný webhook provede
   logicky stejnou operaci jen jednou.
6. Teprve potvrzený úplný zápis změní stav na dokončeno. Návrh výchozího
   oznámení pacientovi: personál zavolá a označí kontakt jako vyřízený.
   Konečný kanál, odpovědnost a doba vyřízení čekají na Q16–Q18.

Při více návštěvách zvolit a potvrdit konkrétní původní návštěvu. Běžná
dermatoskopie se přesouvá/ruší jako celek. Částečnou změnu předat. Změna těsně
před původním termínem není zakázaná; nový termín musí splnit všechny podmínky.
Při konfliktu nabídnout nový výběr a zachovat původní rezervaci. Při nejistém
commitu neslibovat ani úspěch, ani jisté selhání, nezkoušet zápis naslepo znovu.

Dočasné blokace zůstávají návrhem. 30 minut je kandidát podle doby vyřízení,
ne dohodnutá garance a ne současná schopnost systému. Lokální blokace chrání
jen spolupracující procesy API; nemůže se vydávat za zámek pro ruční zápisy
Medicus. Uživatel 5. 10. schválil variantu „personál má přednost“: žádost slot
neblokuje, schválení ověří aktuální dostupnost v nové transakci. Obsazenost
zjištěná při kontrole znamená konflikt bez zápisu a domluvení náhrady personálem.
Vzácný souběžný insert po této kontrole může vytvořit kolizi; toto riziko je
přijaté a rozhodnutí o přesunu provede personál, nikoli automatický přepis
cizí rezervace. Celotabulková rezervace OBJOBJ se proto nepoužije. Zůstává
ochrana proti opakovanému provedení téže žádosti, konfliktům změny existujícího
řádku a požadavek na konzistenci obou databází. Technické ověření zápisů
a nejistého výsledku je nadále podmínkou aktivace.
Nejasný výsledek má samostatný stav k ověření, ne automatické uvolnění a retry.

## Předání a notifikace

Výslovná žádost o člověka vede přímo k předání bez dalšího vysvětlování.
Mimo rozsah zachovat původní požadavek. Při technické chybě vysvětlit potíže,
trvale zaznamenat kontext a chybu, upozornit admina a pokusit se přesměrovat.
Selhání zápisu shrnutí nemá samo zabránit telefonnímu předání. Opačně,
úspěšný transfer nenahrazuje záznam nevyřešené technické nejistoty.

Obsazeno/nezvednuto je provozní nedostupnost s následným callbackem. Selhání
telefonního přenosu je technická chyba. Hlášku po neúspěšném přepojení, návrat
agenta, skutečné zmeškané hovory a původní caller ID ověřit po implementaci
na konkrétním typu transferu. Úplný výpadek telefonu nelze překonat samotným promptem.

Požadavek pro personál musí přežít chybu SMS. Navrhujeme trvalý záznam
plus oddělené doručování s bezpečným opakováním, ne opakování booking operace.
Aktualizace rozsahu 2. 10. 2026: uživatel SMS odložil kvůli nákladům.
Aktuální pilot používá trvalý požadavek v Operatoru a admin e-mailové alerty;
SMS se neimplementují, nezapínají a nejsou podmínkou dokončení pilotu.
Následující původní SMS návrh platí pouze pro případné budoucí rozšíření.

SMS na číslo živého předání obsahuje jen potřebný důvod, callback kontakt a
chráněný odkaz; detailní obsah a příjemce potvrdí Q17. SMS schopnost přijímacího
Twilio čísla a schválený odesílatel dosud nejsou prokázané. Admin e-mail má
navázat na existující Resend/hypercare cestu po ověření aktuálního stavu,
bez duplicitních upozornění a bez citlivých payloadů. Stav doručení a rezervace
jsou oddělené; čekající zpráva není doručená zpráva.

## Operator a hypercare

- Plné číslo volajícího pro oprávněný personál, přesné hledání celého čísla
  po normalizaci formátu, bez obnovování umělých historických čísel. Skryté
  nebo chybějící číslo označit, nevymýšlet kontakt.
- Karta požadavku: pacientský kontext v nezbytném oprávněném rozsahu, služba,
  původní a nový příchod, lékař, sken, stav ověření, čeká/schváleno/dokončeno/
  odmítnuto/konflikt/expirováno/vyžaduje ověření, odpovědná osoba, historie.
- Viditelné tlačítko schválit/odmítnout pouze pro oprávněnou roli a tenant;
  disabled/busy stav není sám ochranou proti souběhu, tu zajistí backend.
- Zřetelně odlišit žádost pro personál, výsledek změny a stav kontaktování
  pacienta. U chyby možnost převzít případ; neprovádět skrytý automatický retry.
- Admin detail: konkrétní sanitizované vstupy a výstupy toolů, čas, korelace
  hovoru/nabídky/žádosti/operace, namespace DB, typ operace, datum návštěvy,
  skutečný stav a označení zasažených objektů. Plné RČ, tokeny a celé zdravotní
  payloady neukládat do obecné telemetrie. Interní pacientské identifikátory
  nevystavit v klientském UI; použít chráněnou korelaci a serverový audit.
- Hypercare přehled a čitelný Supabase view sladit s novými stavy, včetně
  schváleno bez commitu, nejistého výsledku a selhání notifikace. Ověřit granty
  a izolaci tenantů, nikoli pouze vzhled tabulky.

## Implementační etapy po schválení

| Etapa | Rozsah | Důkaz před pokračováním |
| --- | --- | --- |
| 1 dokončení | Odpovědi Q01–Q18, mapování, odsouhlasení tohoto návrhu | Schválené rozhodnutí nebo explicitně přijatý default, ne automatické překlopení UNCLEAR na CONFIRMED |
| 2 regresní případy | Deterministická data včetně incidentu 7.10., hranic, opakování, výjimek, neznámého lékaře, LASER a identity | Každý případ má vstup, business výsledek, nabídku/odmítnutí a důvod; bez LLM |
| 3 dostupnost | MAIN/LASER, časy a filtry, svátky, předstih, řazení, nové varianty služeb | Test známé chyby před/s fixem; porovnání konkrétního dne s Medicus UI; měření krátkého okna |
| 4 nabídky a identita | Neměnné offer ID, ověřovací důkaz, verze, expirace, identita hovoru | Smíchané údaje nevytvoří vykonatelnou nabídku; samostatný test chybných slovních kombinací |
| 5 schvalování | Trvalá žádost, příjem do Operator backendu, staff autorizace, revalidace | Create/move/cancel bez veřejných přímých zápisů; odmítnutí bez mutace; cizí tenant/role nedostane práva |
| 6 zápisy a zotavení | Idempotence, původní rezervace, dvě DB, souběh, restart, nejistý commit | Opakované kliknutí, timeout po commitu a pád mezi kroky nevyvolají duplicitu nebo tichý částečný úspěch |
| 7 prompt a nástroje | Sladit se skutečnými kontrakty, zachovat Architect opravy, zkrátit hovory a předání | ElevenLabs testy plus řízené hovory; žádná promptová náhrada chybných dat |
| UI a pilot | Dokončit Operator, diagnostiku a doručování; provést celý uživatelský tok | Personál schválí i odmítne; admin dohledá výsledek; pacient nedostane nepravdivé potvrzení |
| nasazení | Verzované release všech součástí, migrace, flags, konfigurace tools, rollback | Verze/hash, zdraví, řízený skutečný hovor, DB výsledek a UI; aktivace po důkazech |

Průběžně se implementují smlouvy Operator backendu potřebné pro schválení;
finální úpravy frontendového chování navazují na stabilní API. Nasazení pilotu
zahrnuje i asistované nastavení ElevenLabs tools, pokud bude potřebné. Nejde
jen o odevzdání nového textu promptu.

Pracovní oblasti: `scripts/availability_*`, `business_rules.py`,
`agent_context.py`, `patient_lookup.py`, `laser_calendar.py`, `appointment_write.py`,
`api_server.py`, lokální `approval_*`; dále související Operator API/worker,
migrace a tenantově oddělené projekce; dashboard `app` a `lib`. Lokální prototyp
se před použitím znovu posoudí. Před změnami každého repozitáře číst jeho AGENTS
a aktuální stav; nesmí se přepsat uživatelské rozpracované soubory.

## Přijímací scénáře pro klienta

| ID | Hovor nebo situace | Očekávání |
| --- | --- | --- |
| T01 | Nejbližší běžné kožní bez lékaře | Nejbližší vyhovující nabídky napříč lékaři, bez skenu |
| T02 | Konkrétní lékař a krátké časové omezení | Zachování preference, rozšíření nepřekročí omezení |
| T03 | Dermatoskopie a obsazený LASER | Žádná nabídka kolidujícího skenu; srovnání se skutečným kalendářem |
| T04 | Pacient může až po 14:00 | Žádný příchod na sken před 14:00; správný společný příchod |
| T05 | Dnes, víkend nebo svátek | Předstih a zákazy fungují v API i řeči |
| T06 | Kontrola za rok | Krátké cílené okno, správná služba, žádné automatické klinické datum |
| T07 | Chybně vyslovené jméno, nulová nebo více shod | Jedna smysluplná oprava; volba RČ/personál, bez zveřejnění cizích údajů |
| T08 | Rodič objedná dítě, pak mění jeho návštěvu | Cílový pacient a rezervace správné, ne karta volajícího |
| T09 | Více rezervací nebo změna jedné části dermatoskopie | Výslovný výběr, částečný požadavek personálu |
| T10 | Nabídnutý termín mezitím obsazen | Nový výběr, původní rezervace při přesunu zachována |
| T11 | Chci člověka nebo chci plazmu | Předání bez výslechu či náhradní nabídky kožního |
| T12 | API selže nebo je výsledek zápisu nejistý | Omluva, požadavek uložen, admin upozorněn, žádný falešný úspěch |
| T13 | Personál obsazen / nezvedá / transfer selže | Ověřený telefonní výsledek, správný kontakt, žádný ztracený požadavek |
| T14 | Souhlas pacienta a následné staff schválení/odmítnutí | Čekající žádost není rezervace; skutečný DB výsledek a oznámení oddělené |
| T15 | Doručení do Operatoru selže nebo se zopakuje kliknutí na schválení | Požadavek přežije, zápis se neduplikuje, stav je viditelný; SMS mimo rozsah |

Jde o plán scénářů, nikoli hotovou regresní sadu nebo výsledky testů.
Testovací zápisy použijí určenou testovací kartu a evidované vratné změny.
Klientský feedback zaznamená scénář, očekávání, skutečný výsledek, čas hovoru,
korelaci a konkrétní opravu. Nepoužívat reálné pacienty pro neřízené pokusy.

## Nasazení a hranice dokončení

Před deployem znovu zkontrolovat efektivní flags, verze služeb, databázové
schéma, agent tools a cílové číslo přesměrování. Uchovat návratový release
a rozlišit rollback aplikace od řešení již provedených DB změn. Migrace nejprve
kompatibilní, spouštění workeru a doručování ověřit včetně restartu. Tajemství
nepatří do promptu ani dokumentů. Resend/Vault se ověřují bez vypisování hodnot.

Po nasazení ověřit veřejný příjem hovoru a webhook, aktuální možnosti API,
staff autorizaci, schválení, DB readback, zobrazení v Operatoru, notifikace
a předání. Veřejný agent nemá cestu obejít schvalování. Izolované zdraví
endpointu nebo zelený unit test nejsou důkazem správného celého pilotu.

Celý cíl zůstává otevřený do skutečně ověřeného nasazení pilotu v2. Návrh je
schválený; dostupnost, durable handoff a diagnostika jsou částečně nasazené.
Aktuální důkazy i zbývající implementace a testy jsou ve stav_cile.md.
Žádná dílčí etapa nenahrazuje celý pilot, skutečné GUI mapování ani řízené hovory.
