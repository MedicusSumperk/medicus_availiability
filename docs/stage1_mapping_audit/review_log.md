# Společná revize pravidel

## USER-REVIEW-01 — 2026-10-01, rozlišení služeb

Zdroj: přímé vysvětlení uživatele v této konverzaci; ne samostatné potvrzení recepce.

Potvrzený význam:

- Běžné kožní vyšetření je samostatná lékařská prohlídka hrazená pojišťovnou.
- Dermatoskopie je oddělená placená služba. Personál provede sken přístrojem,
  předá výsledky lékaři a lékař je následně posuzuje.
- Z objednání běžného kožního vyšetření nevyplývá automatický scan ani rezervace
  přístroje. Starší opačný popis není platným pravidlem pro službu skin.

Rozhodnutí: MAP-02 business význam potvrzen; MAP-03 potvrzen pouze sled činností
a oddělení placené služby. MAP-03 zůstává PROBABLE jako celek, protože obsahuje
dosud neověřené technické a časové předpoklady.

Touto odpovědí nebyly potvrzeny: konkrétní DB aktivity, délka scanu/návštěvy,
15min offset, nutnost bezprostřední osobní návštěvy lékaře ve stejný den,
pravidla opakovaných scanů a kontrol, cena ani cross-DB vazby.

Navazující otázka: co přesně pro pacienta znamená následné posouzení lékařem —
osobní návštěva hned po scanu, osobní návštěva jindy, nebo vyhodnocení bez návštěvy?

Změněna pouze auditní dokumentace. Bez povolení implementace či nasazení.

## USER-REVIEW-02 — 2026-10-01, návaznost prohlídky a výjimka

Zdroj: přímé upřesnění uživatele v konverzaci.

- Standardně po scanu hned následuje osobní lékařská prohlídka při téže návštěvě.
- Výjimečně lze objednat pouze dermatoskopický scan, například při nedostatku
  času pacienta na následnou prohlídku. Výjimka není běžný postup.
- Pro standardní kombinaci tedy potřebujeme obě navazující kapacity.

Tím je zodpovězena navazující otázka z USER-REVIEW-01. Není potvrzeno, že agent
smí samostatný scan nabídnout/objednat; toto je další otázka. Neodvozujeme ani,
že výjimka znamená konkrétní variantu service key, odpadnutí lékařského posouzení
výsledků nebo konkrétní postup jejich pozdějšího vyhodnocení.

MAP-03 a MAP-16 aktualizovány; konkrétní délky, buffery a DB aktivity zůstávají
otevřené. Výrok „hned navazuje“ není sám potvrzením přesného nulového bufferu.
Změněna pouze dokumentace, bez implementace a nasazení.

## USER-REVIEW-03 — 2026-10-01, agent a samostatný sken

Uživatel potvrdil: možnost samotného skenu má existovat i pro agenta, pokud
o ni pacient výslovně požádá. Agent ji nemá běžně navrhovat. Výchozí průběh
zůstává sken a ihned navazující prohlídka.

Tím je vyřešena otázka oprávnění agenta z USER-REVIEW-02 na úrovni business
požadavku. Nevzniká oprávnění změnit produkci, zapnout přímé zápisy ani obejít
budoucí schvalování. Konkrétní service key a DB mapování samostatného skenu
zůstávají otevřené. Bez navazující návštěvy nelze automaticky dovodit, že odpadá
lékařské vyhodnocení výsledků; způsob jeho zajištění je další otázka.

MAP-03 aktualizován pouze v dokumentaci. Celková jistota PROBABLE zůstává kvůli
nepotvrzeným technickým a časovým částem; pravidlo výslovné žádosti je potvrzené.

## USER-REVIEW-04 — 2026-10-01, odložená prohlídka po skenu

Uživatel uvedl: po samotném skenu je nutné domluvit osobní návštěvu lékaře na
jindy. Běžně nejpozději do 3 měsíců od skenu, krajně do 6 měsíců; již po 3
měsících může sken ztrácet relevanci. Toto je provozní pravidlo sdělené uživatelem,
nikoli nezávisle ověřený obecný klinický závěr. Šest měsíců není standardní
zaručená platnost skenu.

Uživatel navrhl pacienta informovat a případně domluvit další návštěvu přes
personál bezprostředně po skenu. Odpovědnost za tento krok není definitivně
určená. Neznamená to, že nelékařský personál provede lékařské vyhodnocení.

Otevřeno: kdo povolí výjimku 3–6 měsíců a zda ji smí nabídnout agent, přesný
výpočet hraničních dat, doložení data skenu, postup po 6 měsících a odpovědnost
za domluvení návštěvy. Neodvozujeme automatické opakování skenu ani konkrétní
service key či DB aktivitu.

MAP-03 a MAP-04 aktualizovány pouze v dokumentaci, bez změny chování.


## USER-REVIEW-05 — 2026-10-01, předání výjimky personálu

Uživatel souhlasí: agent termín více než 3 měsíce po skenu automaticky
nenabízí a požadavek předá personálu k posouzení výjimky. Předání není
potvrzením rezervace ani automatickým povolením krajní lhůty do 6 měsíců.

Uživatel očekává, že se další návštěva většinou domluví na místě po skenu.
Toto očekávání neznamená, že je pro konkrétního pacienta návštěva domluvená;
agent ji nesmí za domluvenou prohlásit bez potvrzení. Zůstává otevřená role
rozhodující o výjimce, hraniční data a technické mapování.

Aktualizovány MAP-03 a MAP-04 pouze v dokumentaci, bez implementace.

## USER-REVIEW-06 — 2026-10-01, délka skenu

Uživatel předpokládá pevně 15 minut, ale dodává „pokud se nemýlím“.
Krajně může sken trvat déle a agent to podle uživatele pravděpodobně nemůže
posoudit. Standardních 15 minut tedy zůstává předběžným pravidlem k potvrzení
recepcí, nikoli nezávisle potvrzeným faktem jen proto, že shodnou délku používá
kód. Není určena delší délka ani automatický mechanismus jejího výběru.

MAP-03 a MAP-16 aktualizovány; jistoty beze změny. Další bod společné revize:
délka navazující lékařské prohlídky. Pouze dokumentace, bez implementace.

## USER-REVIEW-07 — 2026-10-01, délka prohlídky podle lékaře

Uživatel potvrdil závislost na konkrétním lékaři. Výhradně10min sloty u
Bednáře uvedl jako předpoklad, současně připomněl jiné DB nálezy. Starší
schedule_interval_findings.md v okně červenec–září2026 uvádí10min kontexty
u Bartoňové, Selecké, Školařové a Šlosárové (ta má i15min kontexty).
Záznam nepřepisujeme na pravidlo pouze Bednář10 / ostatní15 a historickou
DB hodnotu nezaměňujeme za potvrzenou délku výkonu nebo současný rozvrh.

MAP-15 zůstává UNCLEAR jako celek. Konkrétní otázka k vyřešení: rezervuje
recepce pro běžnou prohlídku jedno políčko podle kalendáře daného lékaře,
nebo i více políček? Změna pouze dokumentace, bez zásahu do produkce.

## USER-REVIEW-08 — 2026-10-01, jedno políčko pro prohlídku

Uživatel potvrdil, že běžná prohlídka zabírá jedno políčko kalendáře.
Více políček se používá v krajních případech, které musí posoudit personál.
Agent proto nemá sám určovat potřebné prodloužení. Tím je zodpovězena otázka
z USER-REVIEW-07; nevyžadujeme od recepce znovu potvrdit toto obecné pravidlo.

Technické mapování políčka na konkrétní rozvrhový blok/INTERVAL musí teprve
prokázat audit, zejména v dni s více intervaly. Nepotvrzuje se tím dnešní
implementace používající nejmenší interval kontextu ani pravidlo pouze
Bednář10 / ostatní15. MAP-15 má potvrzenou business část, jako celek zůstává
UNCLEAR kvůli technické vazbě. Změněna pouze dokumentace.

## USER-REVIEW-09 — 2026-10-01, opakovaná dermatoskopie

Uživatel předpokládá stejný průběh jako u první dermatoskopie: nový sken
a prohlídka, případně odložená obdobně jako po prvním skenu. Výslovné
„předpokládám“ zachováváme jako nejistotu; nepřevádíme je na definitivní
klinické pravidlo, nové potvrzení lhůt nebo přiřazení DB aktivity.

Krátký dotaz pro personál: Má opakovaná dermatoskopie stejný průběh
sken+lékař a stejné možnosti a lhůty odkladu jako první?

MAP-04/05 aktualizovány; technický konflikt regular_check→aktivita5
zůstává otevřený. Nebyla změněna produkce ani zahájena další etapa.

## USER-REVIEW-10 — 2026-10-01, lékaři a sdílený přístroj

Uživatel potvrdil, že prohlídku po skenu provádějí všichni právě ordinující
lékaři. Přístroj je jediný a skeny se musí vejít do společného kalendáře,
nezávisle na lékaři následné prohlídky. MAP-23: kapacita1 potvrzena.

Počet dvou přítomných lékařů uživatel označil za své pochopení pravidel;
nepřevádíme jej na pevný limit. MAP-12/14: potvrzen význam, nikoli technické
identity účtů, LASER5/1 či samostatná dostupnost obsluhy. Neodvozujeme
klinickou způsobilost technických účtů ani pravidla jiných služeb.

Pouze dokumentace, bez změny produkce.

## USER-REVIEW-11 — 2026-10-01, autorita aktuální databázové identity

Uživatel bere databázi jako pevná data; historii Hrudová/Ferencz si potvrdí.
V kontextu této otázky je tedy pro aktuální jméno a kalendářové ID rozhodující
DB, nikoli starší konfigurace. Neodvozujeme nahrazení osoby, zpětné přejmenování
historických záznamů, alias ani platnost starých individuálních pravidel.

MAP-10 zachovává CONFLICT pro nesoulad uložených zdrojů, ale volba zdroje
aktuálního jména je vyřešena. MAP-37 doplněn. Toto není plošné schválení
všech business interpretací DB. Pouze dokumentace, žádná změna konfigurace.

## USER-REVIEW-12 — 2026-10-01, společné příchody

Uživatel potvrdil záměr bucketů: pacienti přijdou na společný čas, čekají
v čekárně a lékař je postupně podle potřeby zve. Rozdíl mezi technickým
políčkem a sděleným příchodem není sám chybou. Nesmí se automaticky
„opravit“ odstraněním společného příchodu nebo slibem přesného zahájení.

Nejsou dosud jednotlivě potvrzeny konkrétní časy a konce bloků, rozsah
služeb a lékařů ani objednání po již uplynulém společném příchodu.
MAP-25 má potvrzen princip, jako celek zůstává UNCLEAR pro tyto otázky;
MAP-24 doplněn. Pouze dokumentace, bez změny produkce.

## USER-REVIEW-13 — 2026-10-01, dermatoskopie a společný příchod

Uživatel předpokládá platnost společného příchodu také pro dermatoskopii.
Sken má předcházet prohlídce o15 minut; pacient na začátku společného
bloku má být v čase prohlídky již oskenován. Formulaci „takto to chápu já“
zachováváme jako předběžný výklad.

Neurčeno: T pro ostatní pacienty v bloku, společný versus individuální
příchod a vztah k reálné scan rezervaci. Jeden přístroj nesmí získat
překrývající se rezervace pouhým odečtením15 od společného bucketu.
Společný příchod s čekáním je odlišný od současného použití skeneru.
Konkrétní příklad k vyjasnění je v MAP-25; aktualizován také MAP-16.
Pouze dokumentace, bez změny chování nebo volby neověřeného výkladu.

## USER-REVIEW-14 — 2026-10-01, ověření historie arrival bucket

Uživatel si provozní detail upřesní; předpokládá11:15→rezervace/příchod11:00
a požádal o ověření historie. Proveden fetch a audit dostupných commitů.
Nalezeno oddělené skin bucket mapování a dermatoskopický offset před
technickým časem lékaře. Podrobný důkaz a omezení v [arrival_history.md](arrival_history.md).
Offline transformace11:15→scan11:00 potvrzena, bez testu živé dostupnosti.
MAP-16/25 doplněny; žádné provozní rozhodnutí ani změna implementace.

## USER-REVIEW-15 — 2026-10-01, pracovní návrh příchodu na dermatoskopii

Uživatel určil prozatímní návrh: společný bucket příchodu i pro dermatoskopii
podle předchozího vysvětlení. Podstatné je zachovat sken před prohlídkou.
Konkrétní dotaz na personál ohledně prvního a dalších pacientů už je dostatečně
přesný; další časový buffer se případně upraví později.

Tím je vybrán pracovní směr, nikoli schválena kompletní časová transformace
nebo implementace. Jeden přístroj stále vyžaduje nepřekrývající se scan
rezervace. Nevytváříme bez důkazu společnou scan rezervaci bucket−15 pro více
pacientů, větší buffer ani pravidlo, že čekání nemůže nastat.

MAP-16/25 aktualizovány, technické detaily zůstávají otevřené. Pouze Stage1
dokumentace, žádná změna runtime ani produkce.

## USER-REVIEW-16 — 2026-10-01, potvrzené časy společných příchodů

Uživatel výslovně potvrdil shodu s poznámkami klienta:
- pondělí až pátek dopoledne11:00,
- pondělí odpoledne15:00,
- úterý až čtvrtek odpoledne16:00,
- pátek odpoledne14:00.

Tyto časy jsou potvrzené, nebudeme se na ně znovu dotazovat personálu.
Zatím není schváleno zahrnutí koncových technických políček do bucketu
ani přesné odvození příchodu/scanu u dermatoskopie. MAP-25 zůstává jako
celek UNCLEAR pro tyto konkrétní části, nikoli pro samotné časy.
Bez změny konfigurace, promptu či produkčního chování.

## USER-REVIEW-17 — 2026-10-01, minimální předstih

Uživatel zvolil prozatímní pevný default minimálně1 hodina od zavolání.
Krajní provozní případy ověří s klientem pro budoucí úpravu. Toto není
pokyn implementovat nyní ani ponechat minulý příchod při pozdějším slotu.

Výklad pro návrh sdělený asistentem: minimum se vztahuje k požadovanému
příchodu (společný bucket nebo sken), nikoli pouze k termínu lékaře. Tuto
interpretaci vedeme odděleně od výslovně zvolené hodnoty60 minut. Od zavolání
nenahrazujeme bez rozhodnutí časem každého API dotazu ani neposouváme anchor
při retry. Autoritativní timestamp, chybějící metadata a pozdější revalidace
zůstávají technicky otevřené. Příklady v MAP-24 jsou návrhové, ne nové testy
produkčního chování. MAP-24/25 aktualizovány pouze v dokumentaci.

## USER-REVIEW-18 — 2026-10-01, pohotovost a návrh emergency tagu

Potvrzeno uživatelem: termíny před08:00 jsou skutečně pro pohotovost a běžně
je nenabízet. Rezervování těchto slotů uživatel ověří s klientem.

Návrh uživatele: při zmínce akutního případu emergency tag, doporučení tohoto
času a návrh okamžitého přesměrování na personál. Cílem je klidná, vstřícná
reakce na rozrušeného volajícího. Zaznamenáno jako návrh, ne implementace.

Oddělujeme navržené označení požadavku od stávajícího API emergency=true,
které odemyká časový filtr. Tag není diagnóza, oprávnění rezervovat ani
potvrzení dostupného termínu. Před doporučováním konkrétního příchodu musí
klient upřesnit režim pohotovosti. Otevřen je postup při nedostupnosti
personálu/mimo dané hodiny a případná výjimka z60min předstihu; nevytváříme
ji automaticky. MAP-26/35 aktualizovány pouze v auditní dokumentaci.

## USER-REVIEW-19 — 2026-10-01, mimo scope předávat původní požadavek

Uživatel potvrzuje: plazma/PRP, laserové výkony a další zákroky zatím mimo
první scope, bez nabídky termínů agentem. Plazmu označuje za safe kandidáta
klientského objednání pro pozdější rozšíření; neověřujeme tím klinické
předpoklady ani její technická pravidla.

Obecný požadavek: co je jasně mimo scope, nabídnout k předání personálu.
Neodpovídat náhradní nabídkou kožního nebo jiné podporované služby. Zachovat
původní požadavek pacienta. Uživatel popsal současnou nežádoucí reakci;
produkční dataset jsme při této revizi nezávisle neprohlíželi.

Navržená formulace: „S tímto vám pomůže personál. Mohu vás na něj přepojit?“
Při již výslovném požadavku na člověka neopakovat přesvědčování o službách
agenta. Technické provedení a fallback při neúspěšném předání se ověřují
samostatně; samotné shrnutí není důkaz doručení. Toto jsou podklady pro
pozdější prompt/test etapu, nikoli změna produkčního agenta.

MAP-06/07/35 doplněny pouze v auditní dokumentaci.

## USER-REVIEW-20 — 2026-10-01, nedostupnost personálu a technická chyba přepojení

Uživatel očekává při obsazení/nezvednutí zmeškaný hovor na cílovém telefonu a callback personálu. Požadovaná hláška, pokud ji lze po selhání přehrát: „Omlouváme se, ale personál je momentálně zaneprázdněn. Zavolá Vám, jakmile to bude možné.“ U jiné technické chyby má vzniknout admin upozornění i záznam původního požadavku a nemožnosti přepojení pro personál. Volajícímu omluva a ujištění o předání a následném kontaktu; návrh musí zajistit skutečné uložení/předání před jeho potvrzením.

Read-only ověření oficiální dokumentace: ElevenLabs rozlišuje conference (přidá příjemce, odebere AI), blind (přímé předání, zachování původního caller ID, pouze native Twilio) a SIP REFER. Dokumentace neposkytuje záruku návratu AI po busy/no-answer. Twilio Dial rozlišuje busy/no-answer/failed a umožňuje navazující call flow, což samo nedokazuje podporu v managed ElevenLabs transferu. Zmeškaný hovor se správným číslem na fyzickém telefonu je nutné ověřit v reálné konfiguraci, nikoli odvodit z API statusu.

Zdroje: https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number a https://www.twilio.com/docs/voice/twiml/dial . Produkční nastavení nebylo při této revizi načteno; nebyl proveden zkušební hovor ani změna konfigurace. Otevřen technický test vyzvednuto/obsazeno/nezvednuto/selhání.

Uživatel dodá aktuální prompt až po review pravidel. Zohlednit změny ElevenLabs architecta, zejména okamžité předání na výslovnou žádost. Pouze návrhová dokumentace; MAP-35 aktualizován.

## USER-REVIEW-21 — 2026-10-01, preferovaný lékař a rozšířené hledání

Uživatel potvrdil maximální rozsah 6 měsíců pro rozšířené hledání u požadovaného lékaře. Vždy respektovat požadavky volajícího; při neúspěchu nabídnout volbu jiného lékaře nebo předání personálu, nikoli lékaře změnit bez souhlasu. Výkon filtru je předpoklad k technickému ověření. Šest měsíců nezaměňujeme bez rozhodnutí za současných 180 dní. MAP-27 aktualizován, zbývající nevyřešené části pravidla zachovány.

Uživatel rovněž rozhodl ponechat praktické ověření přepojení z USER-REVIEW-20 až na konkrétní test po implementaci. Není to blokace dokončení business review. Žádné runtime, prompt ani produkční změny.

## USER-REVIEW-22 — 2026-10-01, časové omezení platí již pro příchod na sken

Uživatel potvrdil, že při požadavku typu „mohu až po 14. hodině“ je nutné počítat i s předcházejícím skenem. Omezení tedy musí splňovat požadovaný příchod, nikoli pouze následný čas prohlídky; platí i při použití společného příchodu. Příklad lékař14:10 / sken13:55 nesplňuje příchod po14:00. Potvrzení neřeší přesný konec návštěvy ani neuzavírá otevřenou technickou transformaci bucketů. MAP-25/27 aktualizovány pouze v návrhu, žádná změna runtime nebo produkčního promptu.

## USER-REVIEW-23 — 2026-10-01, víkendy vždy mimo nabídku

Uživatel výslovně odmítl víkendové objednávání: případný víkendový slot je pravděpodobně chyba nespracovaného rozvrhu. Agent má nabízet pouze pondělí až pátek, bez víkendové výjimky při požadavku volajícího či rozšíření hledání. Příčinu případného slotu tím technicky nepotvrzujeme. Současný include_weekends není oprávnění výjimku povolit. Režim státních svátků v týdnu zůstává samostatným bodem. MAP-27 a inventář aktualizovány pouze v dokumentaci, runtime beze změny.

## USER-REVIEW-24 — 2026-10-01, samostatné blokace svátků

Uživatel si není jistý, zda databáze/rozvrh zohledňuje svátky, a požaduje samostatný seznam pro daný rok, který defaultně blokuje dostupnost. Nejde o ověřené tvrzení o chybě databáze. Návrhový výklad asistenta: české svátky včetně pohyblivých, seznam pro každý rok dotčený hledáním, blokace ve výpočtu dostupnosti bez vytváření umělých rezervací v Medicusu. Konkrétní zdroj a data budou ověřeny při implementaci. Případné výjimky vyžadují samostatné pravidlo; nelze je odvodit pouze z volného DB slotu. MAP-27 doplněn, žádná změna runtime/produkce, kalendář svátků zatím nevytvořen.

## USER-REVIEW-25 — 2026-10-01, nejbližší nabídka bez preference lékaře

Uživatel potvrdil: pokud pacient neurčí lékaře, nabídnout nejbližší dostupné termíny napříč všemi ordinujícími lékaři. Nadále platí omezení pacienta a předchozí pravidla dostupnosti. Návrhový technický důsledek: porovnat výsledky napříč lékaři před omezením počtu nabídek, nikoli preferovat pořadí ID lékařů. Neřeší tím samostatně shodné společné příchody a různé technické časy prohlídek. MAP-27 aktualizován pouze v dokumentaci, produkce a prompt beze změny.

## USER-REVIEW-26 — 2026-10-01, preference lékaře při přesunu

Uživatel stanoví stejný postup jako při objednání: hledat podle preference, pokud byla zmíněna, jinak napříč lékaři. Preference dříve uvedená v hovoru platí i bez opakování při žádosti o přesun; původní lékař rezervace není automatickou preferencí. Ostatní potvrzená pravidla hledání zůstávají. MAP-27/29 aktualizovány pouze v návrhu; nejde o oprávnění měnit rezervace, implementovat přesuny ani nasazovat změny.

## USER-REVIEW-27 — 2026-10-01, přesun a zrušení celé dermatoskopie

Uživatel potvrdil: při přesunu nebo zrušení běžné dermatoskopie pracovat se skenem a navazující prohlídkou jako jedním celkem. Změnu pouze jedné části předat personálu. Potvrzení business pravidla neřeší spolehlivé technické párování ani konzistenci dvou databází a nemění dřívější scan-only výjimku. MAP-29/30/31 doplněny; žádné runtime změny, rezervace ani nasazení.

## USER-REVIEW-28 — 2026-10-01, změna těsně před návštěvou

Uživatel ponechává jako prozatímní default možnost zrušit nebo přesunout návštěvu i těsně před začátkem. Případnou časovou hranici ověří s klientem pro pozdější úpravu. Nejde o výjimku z pravidel výběru nového termínu ani o schválení změn již proběhlých návštěv. MAP-29/30 aktualizovány pouze v návrhu; žádná změna runtime či produkce.

## USER-REVIEW-29 — 2026-10-01, existující karta a IDPAC

Uživatel potvrdil, že zakládání pacientské karty je mimo aktuální scope. Bez IDPAC existující karty není možné založit termín. Při nedohledané kartě platí obecné předání požadavku personálu; neodvozovat z neúspěšného hledání jistotu, že karta neexistuje. Požadavek IDPAC neuzavírá samostatné otázky ověření identity a propojení pacientů mezi databázemi. MAP-28/32 aktualizovány pouze v dokumentaci, žádná změna runtime, karet ani rezervací.

## USER-REVIEW-30 — 2026-10-01, objednání za jiného pacienta

Uživatel potvrdil možnost objednání za jinou osobu, například rodičem za dítě nebo partnerem za partnerku, pokud agent dohledá kartu pacienta. Rezervace patří cílovému pacientovi a jeho IDPAC; telefon volajícího nesmí automaticky určit pacienta. Toto potvrzení samo neřeší postup ověření identity ani přesun/zrušení cizí rezervace. MAP-28/32 doplněny pouze v návrhu, bez runtime a produkčních změn.

## USER-REVIEW-31 — 2026-10-01, přesun a zrušení za jinou osobu

Uživatel potvrdil, že zastoupení jiné osoby je dovoleno i při přesunu a zrušení návštěvy. Pracovat s kartou skutečného pacienta a jeho konkrétní rezervací, nikoli automaticky s identitou volajícího podle telefonu. Tím se uzavírá otevřená otázka rozsahu operací z USER-REVIEW-30; konkrétní postup ověření identity zůstává samostatný. Aktualizována pouze návrhová dokumentace, žádné runtime změny nebo změny rezervací.

## USER-REVIEW-32 — 2026-10-01, standard jméno a datum narození

Uživatel potvrdil standardní údaje: jméno a datum narození pacienta. Dřívější požadavek last4 rodného čísla byl podle uživatele odstraněn v posledních commitech na výslovný požadavek klienta. Historii jsme v této revizi nezávisle neověřovali. Rodné číslo ponechat pouze jako last resort; přesný spouštěč a požadovaný rozsah zatím nejsou potvrzeny. Neobnovovat rutinní last4. MAP-32 aktualizován, technický konflikt lookup/verified zůstává otevřený. Pouze návrh, bez změn runtime či produkčního promptu.

## USER-REVIEW-33 — 2026-10-01, nenalezená karta: kontrola údajů a personál

Uživatel zvolil při nedohledání karty výslovné zopakování použitých údajů: jméno, příjmení, datum narození. Agent sdělí, že s nimi kartu nedohledal. Pokud volající na údajích trvá, nekomplikovat a nabídnout předání personálu. Výklad návrhu: opravené údaje použít pro nové hledání; potvrzené původní údaje nevedou k automatickému dotazu na RČ ani nekonečnému opakování. Pro tuto větev tak předání nahrazuje dříve neupřesněný last-resort postup s RČ. Jiné případné použití RČ není specifikováno. MAP-32 doplněn pouze v dokumentaci; žádné runtime či produkční změny.

## USER-REVIEW-34 — 2026-10-01, více shodných karet: volitelně RČ nebo personál

V odpovědi na otázku k více kartám se shodným jménem a datem narození uživatel určil volbu pro volajícího: zkusit dohledání podle rodného čísla, nebo rovnou předat personálu. Nejde o rutinní povinnost last4 ani změnu potvrzeného postupu při nulové shodě. Přesný rozsah RČ potřebný k dohledání nebyl touto odpovědí určen. MAP-32 a inventář aktualizovány pouze v dokumentaci, bez runtime či produkčních změn.

## USER-REVIEW-35 — 2026-10-01, celé RČ pro dobrovolné krajní dohledání

Uživatel zvolil celé rodné číslo, pokud se využije krajní možnost dohledání podle RČ. V kontextu USER-REVIEW-34 jde o dobrovolnou volbu při více shodných kartách, s alternativou přímého předání personálu. Standard jméno, příjmení a datum narození ani postup při nulové shodě z USER-REVIEW-33 se nemění. MAP-32 aktualizován pouze v návrhové dokumentaci, žádná změna runtime, promptu či produkce.

## USER-REVIEW-36 — 2026-10-01, výběr a potvrzení návštěvy při více rezervacích

Uživatel výslovně potvrdil, že při více budoucích rezervacích musí agent nejprve zjistit, které návštěvy se požadavek na přesun nebo zrušení týká, a před změnou ji nechat výslovně potvrdit. Automatický výběr první či nejbližší rezervace není přípustný. U běžné dermatoskopie platí dříve potvrzená práce se skenem a prohlídkou jako celkem. MAP-29/30/31/34 doplněny pouze v návrhové dokumentaci, bez změn runtime či rezervací.

## USER-REVIEW-37 — 2026-10-01, termín obsazený po nabídce a zachování původní rezervace

Uživatel potvrdil nové hledání a nový výběr pacienta, pokud vybraný termín mezitím obsadí někdo jiný. Při přesunu zůstává původní rezervace zachovaná až do úspěšného dokončení přesunu. Potvrzen je požadovaný business výsledek, nikoli technická realizace nebo ověření současného chování napříč databázemi. Neopravňuje implementaci holds či schvalování. MAP-28/29/38/39 doplněny pouze v návrhu, runtime a produkce beze změny.

## USER-REVIEW-38 — 2026-10-01, obecný postup při technické chybě

Uživatel výslovně požaduje, aby jakákoli technická chyba nevedla k prostému ukončení hovoru agentem. Informovat volajícího o technických potížích, zaznamenat chybu i požadavek, notifikovat admina a přesměrovat personálu. Souhlasí s tím, že při neověřeném výsledku objednání/přesunu/zrušení agent nepotvrdí úspěch a předá ověření personálu. Návrhový technický důsledek: nejistý výsledek nezaměnit za jisté selhání ani zápis slepě neopakovat. Pro selhání samotného transferu nadále platí USER-REVIEW-20; praktické chování telefonu se ověří po implementaci. Toto je požadované chování systému, nikoli záruka pokračování hovoru při úplném výpadku telefonní infrastruktury. MAP-28/29/30/34/35 aktualizovány pouze v návrhu, bez změn runtime či produkce.

## USER-REVIEW-39 — 2026-10-01, kompaktní potvrzení před novým objednáním

Uživatel potvrdil povinné výslovné potvrzení před každým novým objednáním po stručném shrnutí služby, lékaře, data a času příchodu. Formulace má být kompaktní. U dermatoskopie respektovat již potvrzený příchod včetně skenu; neplést jej s technickým časem lékaře. Potvrzení pacienta není potvrzením dokončeného zápisu ani rozhodnutím o samostatném schvalování. MAP-28/34 doplněny pouze v návrhové dokumentaci, runtime a produkční prompt beze změny.

## USER-REVIEW-40 — 2026-10-01, význam opakované dermatoskopie neuzavřen

Uživatel předběžně navrhuje minulá objednání jako podklad, ale výslovně si není jistý rolí opakované dermatoskopie. Předpokládá stejnou službu na vyžádání, opakovanou preventivní prohlídku po čase, nikoli oddělenou službu. Toto není potvrzení automatické klasifikace, sloučení service keys/DB aktivit ani rozlišení nového skenu a kontroly bez něj. Historické objednání samo nedokazuje absolvování. Konkrétní otázka pro personál: zda další preventivní návštěva zahrnuje nový sken i lékaře, nebo jen kontrolu bez skenu, a zda se jinak objednává. MAP-03/04/05 doplněny jako předběžné, beze změny confidence, runtime nebo produkce.

## USER-REVIEW-41 — 2026-10-01, členění služeb a navazující kontrola na žádost

Uživatel koriguje předchozí pracovní členění: prohlídka, prohlídka s dermatoskopem, navazující kontrola po vyšetření nebo zákroku. Opakovanou/preventivní dermatoskopii nepovažuje za samostatnou proceduru. Navazující kontrolu může agent podle návrhu objednávat na výslovnou žádost pacienta. Datum může ověřit v minulých návštěvách. Obvyklý rok od zákroku uživatel uvádí jako nejistý předpoklad, nikoli potvrzený maximální interval. Neodvozovat z pouhé rezervace absolvovaný výkon ani automatickou klinickou lhůtu.

Read-only kontrola lokální dokumentace current_business_rules.md a auditního README potvrzuje existenci technických kategorií, ale také konflikt: dermatoscope_followup má aktivitu2 (kontrola po skenu); regular_check má label Kontrola po scanu a aktivitu5 (Sken znamének2 a vyšší). Neprokazuje to správné mapování obecné kontroly po zákroku. Historická dokumentace má obě služby zakázané pro nabídku/zápis; současný souhlas mění návrh, nikoli produkční přepínače. Dřívější lhůty odložené prohlídky po skenu zůstávají oddělené. MAP-03/04/05 aktualizovány pouze v návrhu.

## USER-REVIEW-42 — 2026-10-01, potvrzené významy kontrol a zdroj intervalu

Uživatel výslovně potvrzuje dermatoscope_followup jako samostatnou prohlídku po skenu, po kterém pacient nebyl následně vyšetřen. regular_check je kontrola po zákroku nebo předchozím vyšetření. Toto řeší význam service keys, nikoli technický rozpor regular_check -> aktivita5 Sken znamének2 a vyšší. Dřívější pravidla odložené prohlídky po skenu tím nejsou nahrazena ročním intervalem.

Uživatel souhlasí: při sděleném doporučení lékaře (například za rok) hledat kolem odpovídajícího data; při neznámém intervalu předat upřesnění personálu. Univerzální rok ani nejzazší klinická lhůta nebyly potvrzeny. MAP-04/05 doplněny, technické otázky zachovány. Pouze návrh, bez změny runtime, promptu či produkce.

## USER-REVIEW-43 — 2026-10-01, preference lékaře i u kontrol

Uživatel souhlasil s obecným pravidlem a následně potvrdil výklad: pro dermatoscope_followup i regular_check bez preference hledat napříč ordinujícími lékaři, zmíněnou preferenci respektovat, původního lékaře automaticky neupřednostňovat. MAP-04/05/27 doplněny pouze v návrhu. Bez změn runtime či produkce.

## USER-REVIEW-44 — 2026-10-01, krátké hledání v budoucím odstupu

Uživatel potvrzuje hledání kontroly i například za rok; požaduje explicitní krátký filtr na dva týdny nebo měsíc v definovaném odstupu podle zátěže. Přesná délka není zvolena a poloha okna před/po/kolem cílového data není určena. Neprohledávat celý rok od dneška. Šestiměsíční rozšíření pro preferovaného lékaře není maximální vzdálenost objednání a nepřebíjí požadovaný interval pacienta. Zátěž se změří při implementaci; žádná nová runtime změna nebo měření nebyly provedeny. MAP-05/27 doplněny pouze v návrhu.

## USER-REVIEW-45 — 2026-10-01, kontrola i krátce před cílovým datem

Uživatel potvrzuje, že krátké hledací okno může zahrnout také termíny krátce před doporučeným datem (například konec září pro kontrolu začátkem října). Přesná délka okna, počet dní před/po a symetrie nebyly určeny. Dřívější pravidlo respektovat výslovná omezení pacienta zůstává. MAP-05/27 aktualizovány pouze v návrhové dokumentaci, bez změn runtime nebo produkce.

## PROMPT-REVIEW-01 — 2026-10-01, porovnání uživatelem dodaného aktuálního promptu

Přijata přesná kopie promptu z přílohy e11c7e43-85b7-4025-b6a8-bb3d789a6ecb. Porovnáno s USER-REVIEW-01 až45; vznikl prompt_comparison_2026-10-01.md s18 položkami a krátkými otázkami pro personál. Zachovat okamžitý transfer, integritu nabídky, recheck a potvrzování. Rozpory zejména mimo-scope náhradní nabídka, ověřování existujících rezervací, neznámý výsledek zápisu, služby/capabilities, chybějící nové časové a chybové postupy. Živá konfigurace nebyla načtena, produkční ani místní pracovní prompt nepřepsán, Stage2–7 nezahájeny.
