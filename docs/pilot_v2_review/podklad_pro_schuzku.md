# Dermacentrum Šumperk

Podklad pro osobní projednání pilotu v2

Nejprve představte první verzi podle pracovních postupů R01 až R24 a vyzkoušejte společný hovor. Potom doplňte odpovědi Q01 až Q18 pro další úpravy. API, Operator a prompt jsou nasazené; hlasové přejímací testy ještě nejsou uzavřené. Zamýšlené rozšíření a neověřené chování jsou výslovně označené.

Datum schůzky: ____________________  Účastníci: ____________________

## Sken a příchod pacienta

### Q01 Je běžný sken vždy na 15 minut a lékařská návštěva na jedno políčko jeho kalendáře?

Ukažte jedno 10minutové a jedno 15minutové políčko. Jak recepce pozná požadavek, který potřebuje delší čas, a komu ho předává?

Pracovní návrh: Sken 15 minut, lékař jedno skutečné políčko. Nestandardní délku řeší personál. Prodloužení agent sám neposuzuje.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q02 Kdy přesně přicházejí první a další pacient na dermatoskopii ve společném bloku?

Příklad: lékařská políčka 11:15 a 11:30, společný příchod 11:00. Doplňte pro oba pacienty příchod, začátek skenu a prohlídku. Patří poslední políčko na hranici bloku ještě ke stejnému příchodu?

Pracovní návrh: Sken musí předcházet prohlídce a dva skeny se nesmějí překrývat. Společný příchod není automaticky společný začátek skenů. Přesné rozložení před zapnutím této nabídky ověříme.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q03 Kdo po samostatném skenu domluví chybějící lékařskou prohlídku a jak řešíte dlouhý odstup?

Domluví ji recepce na místě, nebo má pacient znovu zavolat? Kdo rozhodne o prohlídce po více než třech měsících, přesně na hranici tří měsíců a po více než šesti měsících?

Pracovní návrh: Samostatný sken jen na výslovnou žádost. Informovat o nutnosti prohlídky; nad tři měsíce předat personálu. Agent neslibuje, že pozdější termín již domluvil.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

## Co se zapisuje do kalendářů

### Q04 Kterou položku v Medicusu vybíráte pro každý ze čtyř typů návštěvy?

Ukažte běžnou prohlídku, sken s prohlídkou, prohlídku po dřívějším samotném skenu a kontrolu po vyšetření nebo zákroku. Jak odlišujete první a další sken při zápisu?

Pracovní návrh: Obsah služeb je domluvený. Potřebujeme ukázku výběru v aplikaci, nikoli nové názvy služeb. Nejasný typ zápisu nepovolíme, dokud jej technicky nepřiřadíme.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q05 Který kalendář ukazuje všechnu obsazenost jediného dermatoskopu?

Ukažte také nepřítomnost obsluhy, servis přístroje a případné jiné místnosti. Stačí volné místo v kalendáři přístroje, nebo ještě kontrolujete další kalendář?

Pracovní návrh: Volný musí být přístroj i navazující lékař. Pokud chybí informace o potřebném zdroji, agent termín nepotvrdí.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q06 Které dnešní kalendáře patří skutečně ordinujícím lékařům a které jsou pomocné?

Ukažte aktivní lékaře, duplicity a kalendáře recepce. U změny Filip Ferencz / Tamara Hrudová potvrďte, zda jde o převzetí kalendáře a zda se změnila pravidla objednání. Jaké přezdívky nebo zkrácená jména pacienti běžně používají?

Pracovní návrh: Bez preference hledat napříč skutečnými ordinujícími lékaři. Aktuální jména vycházejí z databáze; pomocný účet není lékař.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

## Výjimky a změny rozvrhu

### Q07 Jak zadáváte dovolenou, mimořádnou ordinaci a střídání týdnů?

Ukažte den s běžnou ordinací a výjimkou a den s ordinací jen výjimečně. Ruší výjimka celý den, místnost, nebo jen část práce jednoho lékaře?

Pracovní návrh: Nabídka musí odpovídat skutečnému rozvrhu včetně výjimek. O víkendech a svátcích se nenabízí ani při volném políčku.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q08 Které záznamy v kalendáři znamenají blokaci a nesmějí se nabídnout pacientovi?

Ukažte přestávku, celodenní blokaci, opakovanou událost a záznam bez běžného času konce. Jak vypadá zrušená událost? Změníte někdy jen jeden výskyt opakované události?

Pracovní návrh: Žádný výkon nesmí zasáhnout do obsazenosti ani přestávky. Nejasnou blokaci nesmíme ignorovat. Výjimky řeší personál.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q09 Jak v Medicusu přesouváte a rušíte celou návštěvu se skenem a prohlídkou?

Ukažte oba původní záznamy a postup přesunu či zrušení. Poznáte jejich spojení přímo v aplikaci? Zůstává historie a odchází pacientovi zpráva? U opakované rezervace měníte jen jednu návštěvu, nebo celou řadu?

Pracovní návrh: Agent změní sken i prohlídku jako celek. Změnu jen jedné části předá. Při neúspěšném přesunu musí zůstat původní návštěva zachovaná.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

## Pacient a termín kontroly

### Q10 Podle čeho v historii poznáte, že pacient sken nebo zákrok skutečně absolvoval?

Ukažte rozdíl mezi absolvovanou návštěvou, zrušenou návštěvou a nedostavením. Kde je doporučený odstup kontroly a kdo jej umí potvrdit?

Pracovní návrh: Historie pomáhá určit datum. Samotné staré objednání nedokazuje absolvování. Neznámý interval kontroly upřesňuje personál; agent automaticky neurčuje jeden rok.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q11 Jak postupujete, když pacient má kartu v hlavním systému, ale v kalendáři pro sken jej nenajdete?

Ukažte, jak ověříte, že jde v obou systémech o stejného pacienta, a kdo doplní chybějící kartu. Co má personál dostat v předaném požadavku?

Pracovní návrh: Agent nezakládá pacientské karty a nepoužije cizí kartu. Nejednoznačné spojení předá personálu.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q12 Vyhovuje pro kontrolu kolem doporučeného data následující krátké období?

Návrh: nejprve sedm dní před a sedm dní po cílovém datu. Pokud nic nenajdeme, nabídnout se souhlasem pacienta rozšíření nejvýše na patnáct dní před a po. Příklad: lékař doporučil kontrolu začátkem října, pacient může i koncem září.

Pracovní návrh: Jde o návrh přesného rozsahu, nikoli již potvrzenou lhůtu. Výslovné omezení pacienta vždy platí; chybějící nebo nejasné doporučení předat personálu.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

## Předání hovoru a informace

### Q13 Co přesně má agent říci při akutním požadavku a kdy má předat personálu?

Klinický garant doplní schválenou větu pro naléhavý stav a doporučení tísňové pomoci. Recepce upřesní pohotovostní příchod, případné rezervování a postup mimo tuto dobu.

Pracovní návrh: Agent nehodnotí diagnózu. Akutní požadavek klidně předá; ranní pohotovostní políčko běžně nenabízí. Konkrétní čas bez potvrzeného provozního pravidla neslibuje.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q14 Kam a v jakých hodinách se přepojuje a kdo vybírá zmeškané hovory?

Zapište cílové číslo, dostupné hodiny a zástup. Co mimo tuto dobu? Co když volající skryje číslo nebo potřebuje zpětný kontakt na jiné? U přesměrování z hlavního čísla ověříme, že se hovor nevrací k agentovi.

Pracovní návrh: Při obsazení má následovat zpětné zavolání personálu. Neslibovat přesný čas. Funkci zmeškaných hovorů a zobrazení správného čísla ověříme telefonním testem.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q15 Jsou správné informace o pracovišti, které dnes agent sděluje?

Potvrďte Zábřežská 69/41, recepci 777 177 729, sken a laser 725 708 248, výsledky 734 420 966, info@laserstudio.cz, parkování a bezhotovostní platbu. Doplňte platné hodiny obou provozů, bezbariérovost a případný schválený ceník.

Pracovní návrh: Agent sděluje jen potvrzené údaje. Ordinační hodiny nejsou nabídka volného termínu. Neznámou informaci a výsledky předá personálu.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

## Schvalování a odpovědnost personálu

### Q16 Kdo bude schvalovat žádosti o objednání, přesun a zrušení?

Zapište odpovědnou osobu nebo roli, zástup a dobu kontroly žádostí. Když se termín mezitím obsadí, kdo zavolá pacientovi pro nový výběr? Může personál žádost odmítnout s důvodem?

Pracovní návrh: Agent přijme žádost k potvrzení personálem. Teprve schválení a úspěšné provedení vytvoří, přesune nebo zruší rezervaci. Bez schválení agent sám do kalendáře nezapisuje.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q17 Kdo kontroluje frontu v Operatoru a kdo dostane technické chyby?

Určete, kdo a jak často kontroluje nové požadavky v Operatoru, včetně zástupu. Potvrďte příjemce technických upozornění e-mailem a postup při jeho nepřítomnosti.

Pracovní návrh: Požadavek se trvale uloží a zobrazí v Operatoru. SMS nejsou součástí první verze. Technické upozornění správci nenahrazuje vyřízení požadavku personálem. Rodné číslo do upozornění nepatří.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

### Q18 Jak pacient dostane konečné potvrzení a kdo řeší žádost bez výsledku?

Výchozí postup: konečný výsledek oznamuje personál telefonicky. Určete očekávanou dobu vyřízení a odpovědnou osobu. Kdo kontaktuje pacienta, pokud se požadovaný termín mezitím obsadí?

Pracovní návrh: Čekající žádost termín neblokuje. Personál má přednost; při schválení systém znovu ověří dostupnost. Při kolizi personál s pacientem vybere jiný termín. Při nejistém výsledku nejprve ověří stav zápisu, aby nevznikla duplicita.

Odpověď a odpovědná osoba:

____________________________________________________________

____________________________________________________________

# Pracovní pravidla první verze agenta

## Pracovní postup pro začátek hovoru

### R01 Zjistit skutečný požadavek

Krátce pozdravit a zjistit, co pacient potřebuje. Již sdělené údaje a preference znovu nevyžadovat. Nejasný požadavek krátce upřesnit.

Souhlas / změnit: ____________________

### R02 Předat bez přesvědčování

Při výslovné žádosti o člověka ihned přepojit bez dalšího výslechu. U služby mimo rozsah zachovat původní požadavek a nabídnout personál; nenahrazovat jej nabídkou kožního vyšetření.

Souhlas / změnit: ____________________

### R03 Rozlišit obsah návštěvy

Běžná prohlídka neobsahuje sken. Dermatoskopie běžně zahrnuje sken personálem a následnou prohlídku lékařem. Samostatná prohlídka po dřívějším skenu a kontrola po zákroku či vyšetření jsou odlišné požadavky.

Souhlas / změnit: ____________________

### R04 Dodržet rozsah služeb

První verze přijímá ke schválení běžnou prohlídku a sken s prohlídkou. Kontrolu po zákroku či vyšetření a prohlídku po dřívějším skenu předává personálu do ověření jejich zápisu. Plazmu, laser, zákroky, výsledky a zdravotní rady řeší personál. Agent nezakládá karty.

Souhlas / změnit: ____________________

### R05 Výjimečně jen sken

Samotný sken běžně nenabízet. Na výslovnou žádost jej v první verzi předat personálu. Upozornit na nutnost pozdější osobní prohlídky; neprohlašovat ji za domluvenou. Odstup nad tři měsíce posoudí personál.

Souhlas / změnit: ____________________

### R06 Objednání za jinou osobu

Lze objednat, přesunout i zrušit návštěvu za dítě, partnera či jinou osobu. Vždy pracovat s kartou a návštěvou skutečného pacienta, nikoli automaticky s kartou majitele volajícího telefonu.

Souhlas / změnit: ____________________

## Pracovní postup pro hledání termínu

### R07 Zachovat preference

Zohlednit přání pacienta z celého hovoru. Bez preference lékaře hledat nejbližší vyhovující termíny napříč ordinujícími lékaři. Původního lékaře automaticky neupřednostňovat ani při přesunu nebo kontrole.

Souhlas / změnit: ____________________

### R08 Hledat u vybraného lékaře

Nejprve hledat u požadovaného lékaře. Při neúspěchu rozšířit období nejvýše na šest měsíců, stále v mezích pacientova přání. Pokud termín není, nabídnout volbu jiného lékaře nebo personálu.

Souhlas / změnit: ____________________

### R09 Počítat skutečný příchod

Časové omezení pacienta musí splnit už příchod na sken, ne pouze pozdější prohlídka. Nový termín má mít nejméně hodinu předstihu od zavolání. Nenabízet minulý příchod ani minulý sken.

Souhlas / změnit: ____________________

### R10 Pracovní dny a svátky

Nabízet jen pondělí až pátek, mimo české svátky. Víkendový slot se nenabízí ani tehdy, když v systému vypadá volný. Běžně nenabízet ranní pohotovostní termíny před 08:00.

Souhlas / změnit: ____________________

### R11 Společné příchody

Potvrzené časy příchodů jsou Po až Pá dopoledne 11:00; Po odpoledne 15:00; Út až Čt odpoledne 16:00; Pá odpoledne 14:00. Platí ve stanovených blocích, nikoli pro všechny návštěvy dne. Přesné začlenění skenu ověříme podle Q02.

Souhlas / změnit: ____________________

### R12 Kontrola v doporučeném odstupu

V první verzi předat kontrolu personálu spolu s doporučeným odstupem sděleným pacientem. Zamýšlené hledání po ověření zápisu: krátké období kolem cílového data, i za rok a krátce před ním. Přesný rozsah určí Q12. Agent sám neurčuje roční interval.

Souhlas / změnit: ____________________

## Pracovní postup pro ověření a potvrzení

### R13 Ověřit správnou kartu

Standardně vyžádat jméno, příjmení a datum narození pacienta. Samotné telefonní číslo nestačí. Bez existující karty nelze vytvořit termín. Do ověření konkrétního výsledku nepotvrzovat, že je pacient dohledán.

Souhlas / změnit: ____________________

### R14 Nenalezená karta

Zopakovat použité jméno, příjmení a datum narození. Po opravě hledání zopakovat. Pokud volající údaje potvrdí a karta není nalezena, nabídnout volbu dohledání podle celého rodného čísla nebo předání personálu. Nezacyklit dotazování.

Souhlas / změnit: ____________________

### R15 Více shodných karet

Nabídnout volbu dohledat podle celého rodného čísla, nebo rovnou předat personálu. Rodné číslo není běžný povinný údaj. Pokud ani tato zvolená cesta nepomůže, návrh výchozího postupu je předání personálu.

Souhlas / změnit: ____________________

### R16 Vybrat konkrétní návštěvu

Při více budoucích rezervacích zjistit, které se změna týká, a výslovně ji potvrdit. Nevybírat automaticky první nebo nejbližší. Běžnou dermatoskopii přesouvat či rušit jako celek; změnu jen skenu nebo jen prohlídky předat.

Souhlas / změnit: ____________________

### R17 Stručně potvrdit požadavek

Před objednáním shrnout službu, lékaře, datum a příchod, u dermatoskopie jasně také sken. Počkat na výslovný souhlas. Při přesunu potvrdit původní i nový termín, při zrušení rušenou návštěvu.

Souhlas / změnit: ____________________

### R18 Přijmout žádost ke schválení

V první verzi platí schválení personálem. Souhlas pacienta je souhlas s předáním konkrétní žádosti. Čekající žádost termín neblokuje ani nevytváří rezervaci. Agent smí potvrdit předání až po potvrzení přijetí systémem.

Souhlas / změnit: ____________________

## Pracovní postup pro změny a potíže

### R19 Změna těsně před návštěvou

Zrušení i přesun zatím přijímat bez časové hranice před původní návštěvou. Nový termín při přesunu musí znovu splnit podmínky dostupnosti a hodinového předstihu. Prošlé návštěvy nejsou tímto pravidlem povoleny ke změně.

Souhlas / změnit: ____________________

### R20 Termín se mezitím obsadil

Personál má přednost. Při schválení systém znovu ověří dostupnost a známou kolizi nezapíše. Personál kontaktuje pacienta a domluví nový výběr; nesmí sám změnit lékaře či čas. Při neúspěšném přesunu zachovat původní rezervaci. Souběh se zápisem v Medicusu řeší personál.

Souhlas / změnit: ____________________

### R21 Potvrdit jen skutečný výsledek

Čekající žádost, schválení a dokončený zápis jsou různé stavy. Objednání, přesun nebo zrušení označit za dokončené až po potvrzeném provedení. Výchozí postup: personál oznámí výsledek pacientovi telefonicky; upřesnění odpovědností viz Q18.

Souhlas / změnit: ____________________

### R22 Technická chyba

Informovat volajícího o potížích, zaznamenat chybu i původní požadavek, upozornit správce a přesměrovat na personál. Kvůli chybě jednoduše neukončit hovor. Při nejasném výsledku změnu neoznačit za úspěšnou ani jistě neúspěšnou.

Souhlas / změnit: ____________________

### R23 Personál nezvedá

Při obsazení či nezvednutí počítat se zpětným kontaktem podle zmeškaného hovoru. Zamýšlená hláška: „Omlouváme se, ale personál je momentálně zaneprázdněn. Zavolá vám, jakmile to bude možné.“ Zda může zaznít po přepojení, ověříme testem.

Souhlas / změnit: ____________________

### R24 Selže i přesměrování

Zachovat požadavek pro personál a oznámit technickou chybu správci. Je-li agent stále na lince, omluvit se a informovat o následném kontaktu, jehož podklad se skutečně uložil. Neslibovat konkrétní čas zpětného zavolání.

Souhlas / změnit: ____________________
