# Inventář mapování — návrh k lidské validaci

Zdroj: [rules.json](rules.json). Kontext, legenda zdrojů a postup schválení: [README](README.md).

CONFIRMED potvrzuje konkrétní uvedený fakt, nikoli automatické schválení celého procesu. Reprodukční případy jsou návrhy; provedené kontroly jsou výslovně uvedeny v README.

## MAP-01 — database_identity

**Doména:** database_identity

**Business význam / současná interpretace:** Identita každého záznamu musí obsahovat databázový namespace; stejné číslo ve dvou DB neznamená stejný objekt.

**DB reprezentace:** MAIN=C:/Medicus 3/data/MEDICUS.FDB; LASER=C:/Medicus 3 Laser/data/MEDICUS.FDB; IDUZI/IDPAC/IDOBJ/IDCINNOSTI jsou lokální.

**Implementace:** scripts/db.py::connect_to_db; scripts/laser_calendar.py::open_scan_calendar

**Důkazy:** LIVE.databases; DOC-LASER

**Jistota:** CONFIRMED

**Dopad chyby:** Záměna pacienta, lékaře nebo aktivity při zápisu.

**Reprodukovatelný případ:** Porovnat MAIN.IDUZI=1 (Tereza Pérez) s LASER.IDUZI=1 (Eva Bednářová); nesloučit.

**Otázka k potvrzení:** Jaký stabilní identifikátor fyzického zdroje/personálu je společný napříč instancemi?


## MAP-02 — service_skin

**Doména:** service_skin

**Business význam / současná interpretace:** Uživatel potvrdil: běžné kožní vyšetření je samostatná lékařská prohlídka hrazená pojišťovnou. Nezahrnuje automatický sken ani navazující rezervaci dermatoskopu. Placená dermatoskopie je oddělená služba.

**DB reprezentace:** MAIN.OBJOBJ.IDCINNOSTI=NULL; followup.create=false; dřívější dokument požaduje další řádek IDCINNOSTI=6.

**Implementace:** config/business_rules.example.json#/services/skin; scripts/agent_context.py::build_skin_options

**Důkazy:** LIVE.effective_rules; DOC-ACT; CONTRACT; USER-REVIEW-01

**Jistota:** CONFIRMED

**Dopad chyby:** Neoprávněně nabídnutý termín nebo zbytečná blokace/skener.

**Reprodukovatelný případ:** Samotný požadavek skin nesmí vyžadovat ani vytvářet scan/followup rezervaci. Poslední slot smí projít bez navazujícího scanu, pokud vyhoví ostatním pravidlům délky a dostupnosti. Business očekávání potvrzeno uživatelem; nejde o povolení produkčního zápisu.

**Otázka k potvrzení:** Rozlišení služeb a absence automatického scanu vyřešeny uživatelem. Přesné mapování IDCINNOSTI=NULL, délka návštěvy a další pravidla se ověřují samostatně; nebyly touto odpovědí schváleny.


## MAP-03 — service_dermatoscope_first

**Doména:** service_dermatoscope_first

**Business význam / současná interpretace:** Uživatel potvrdil standard placené dermatoskopie: sken personálem a hned navazující osobní lékařská prohlídka při stejné návštěvě. Výjimečně lze objednat pouze sken, například pokud pacient nemá čas na prohlídku. Uživatel potvrdil, že agent má umožnit samostatný sken na výslovnou žádost pacienta, ale nemá jej běžně navrhovat. Jde o schválený požadavek na budoucí chování, nikoli o povolení přímých zápisů nebo nasazení. Kód předpokládá sken15min před lékařem; konkrétní délky ani DB mapování tím nejsou schváleny. Veřejná nabídka je zakázaná. Podle uživatele po samostatném skenu musí následovat osobní návštěva lékaře jindy; běžně nejpozději do3 měsíců od skenu, v krajních případech do6 měsíců. Již po3 měsících může sken ztrácet relevanci. Informování pacienta a případné domluvení termínu personálem po skenu uživatel navrhl; konkrétní odpovědnost a postup zatím nejsou uzavřeny. Uživatel schválil: agent termín prohlídky více než3 měsíce po skenu automaticky nenabízí, ale předá požadavek personálu k posouzení výjimky. Objednání přímo na místě po skenu je očekávané, nikoli zaručené. USER-REVIEW-06: uživatel předpokládá standardní sken15 minut, ale výslovně si není jistý. Delší trvání může být krajní výjimkou, kterou agent pravděpodobně neumí posoudit. Délka proto zůstává předběžná, nikoli nově CONFIRMED. USER-REVIEW-40 (předběžné): Uživatel navrhuje orientaci podle minulých návštěv, ale není si jistý rolí opakované dermatoskopie. Domnívá se, že jde o stejnou službu na vyžádání, případně opakovanou preventivní prohlídku po čase, nikoli samostatně rozlišovanou službu. Není tím potvrzeno sloučení service keys/aktivit, totožnost opakovaného skenu a kontroly bez skenu ani časový interval opakování. Záznam minulého objednání sám nedokazuje absolvovaný sken. USER-REVIEW-41: Uživatel upřesňuje pracovní členění na prohlídku, prohlídku s dermatoskopem a navazující kontrolu po vyšetření/zákroku; opakovaná či preventivní dermatoskopie podle něj není samostatná procedura. Na výslovný požadavek pacienta může agent navazující kontrolu objednat v budoucím návrhu. Uživatel navrhuje ověřit související datum v minulých návštěvách a odvodit doporučený termín; obvyklý rok od zákroku uvádí nejistě, nikoli jako potvrzenou univerzální či nejzazší lhůtu. Rozlišení skutečně absolvovaného relevantního výkonu od pouhé rezervace a zdroj doporučeného intervalu zůstávají k vyřešení. Neměnit tím samostatné pravidlo odložené prohlídky po skenu (3/6 měsíců).

**DB reprezentace:** MAIN aktivita 1; LASER calendar 5/workplace 1 čtení; cílová aktivita zápisu LASER není specifikována.

**Implementace:** config/business_rules.example.json#/services/dermatoscope_first; scripts/agent_context.py::build_dermatoscope_options; scripts/laser_calendar.py::ScanCalendar

**Důkazy:** LIVE.effective_rules; LIVE.laser_mapping; DOC-LASER; USER-OCT7; USER-REVIEW-01; USER-REVIEW-02; USER-REVIEW-03; USER-REVIEW-04; USER-REVIEW-05; USER-REVIEW-06; USER-REVIEW-40; USER-REVIEW-41; docs/current_business_rules.md

**Jistota:** PROBABLE

**Dopad chyby:** Chybějící kapacita skeneru nebo chybný typ výkonu.

**Reprodukovatelný případ:** Standardní požadavek dermatoskopie potřebuje volný scan a hned navazující lékařskou prohlídku. Obsazený scan14:45–15:00 znemožní tuto kombinaci s lékařem15:00. Bez výslovného požadavku agent samostatný sken běžně nenavrhuje. Na výslovnou žádost umožní tuto variantu a nesmí ji zaměnit za kombinaci s prohlídkou. Konkrétní zápisová sémantika varianty zatím není schválená. Pro samostatný sken zdokumentovat potřebu další osobní návštěvy; rozlišit běžnou lhůtu do3 měsíců a krajní výjimku do6 měsíců. Nepovažovat automaticky šest měsíců za standardní platnost. Přesné hraniční případy čekají na potvrzení. Požadavek na prohlídku4 měsíce po skenu: agent nenabízí automatický termín, předá personálu; netvrdí, že návštěva je domluvena.

**Otázka k potvrzení:** Agent předává prohlídku po více než3 měsících personálu; zbývá určit oprávněnou roli k povolení výjimky, přesné hraniční datum a postup po6 měsících. Kdo zajistí skutečné domluvení pozdější návštěvy? Přesné délky, DB aktivity a vazby nadále otevřené. USER-REVIEW-40: Konkrétní otázka pro personál: při další preventivní návštěvě se znovu provádí sken i navazující prohlídka, nebo může jít pouze o kontrolu lékařem bez nového skenu; liší se způsob objednání? Následně přiřadit skutečné DB aktivity/service keys. Minulá objednání jsou uživatelem navržený zdroj kontextu, ne potvrzené automatické klasifikační pravidlo. USER-REVIEW-41: Ověřit mapování konkrétní navazující kontroly; lokální dokumentace rozlišuje dermatoscope_followup -> MAIN aktivita2 kontrola po skenu a regular_check -> aktivita5 Sken znamének2 a vyšší, ačkoli label je Kontrola po scanu. Tyto kategorie neprokazují univerzální kontrolu po libovolném zákroku. Roční interval není potvrzen; upřesnit zdroj a význam doporučené lhůty před automatickým doporučováním nejzazšího termínu.


## MAP-04 — service_followup

**Doména:** service_followup

**Business význam / současná interpretace:** dermatoscope_followup je označena Dermatoskopie kontrola a mapována na kontrolu po skenu; obchodní odlišení od regular_check není uzavřené. Uživatel nově popsal odloženou osobní prohlídku po samostatném skenu (běžně do3 měsíců, krajně do6); tato odpověď sama nepotvrzuje, že jí odpovídá tento service key nebo aktivita2. Uživatel schválil: agent termín prohlídky více než3 měsíce po skenu automaticky nenabízí, ale předá požadavek personálu k posouzení výjimky. Objednání přímo na místě po skenu je očekávané, nikoli zaručené. Nový opakovaný sken je podle předpokladu uživatele jiný požadavek než prohlídka k již existujícímu skenu; přiřazení technických služeb/aktivit zůstává neuzavřené. USER-REVIEW-40 (předběžné): Uživatel navrhuje orientaci podle minulých návštěv, ale není si jistý rolí opakované dermatoskopie. Domnívá se, že jde o stejnou službu na vyžádání, případně opakovanou preventivní prohlídku po čase, nikoli samostatně rozlišovanou službu. Není tím potvrzeno sloučení service keys/aktivit, totožnost opakovaného skenu a kontroly bez skenu ani časový interval opakování. Záznam minulého objednání sám nedokazuje absolvovaný sken. USER-REVIEW-41: Uživatel upřesňuje pracovní členění na prohlídku, prohlídku s dermatoskopem a navazující kontrolu po vyšetření/zákroku; opakovaná či preventivní dermatoskopie podle něj není samostatná procedura. Na výslovný požadavek pacienta může agent navazující kontrolu objednat v budoucím návrhu. Uživatel navrhuje ověřit související datum v minulých návštěvách a odvodit doporučený termín; obvyklý rok od zákroku uvádí nejistě, nikoli jako potvrzenou univerzální či nejzazší lhůtu. Rozlišení skutečně absolvovaného relevantního výkonu od pouhé rezervace a zdroj doporučeného intervalu zůstávají k vyřešení. Neměnit tím samostatné pravidlo odložené prohlídky po skenu (3/6 měsíců). USER-REVIEW-42: Uživatel výslovně potvrzuje: dermatoscope_followup je samostatná prohlídka po dříve absolvovaném skenu, po kterém pacient nebyl následně vyšetřen lékařem; nejde o automatické opakování skenu. Souhlasí také s pracovním postupem pro doporučený interval kontroly: pokud pacient sdělí například doporučení lékaře za rok, hledat kolem odpovídajícího data; pokud interval nezná, předat upřesnění personálu. Automatický univerzální roční interval ani nejzazší lhůta nejsou potvrzeny. Dřívější samostatná pravidla odložené prohlídky po skenu zůstávají zachována. USER-REVIEW-43: Obecné pravidlo výběru lékaře platí i pro dermatoscope_followup a regular_check: bez preference pacienta hledat napříč ordinujícími lékaři, při zmíněné preferenci ji respektovat. Původního lékaře automaticky neupřednostňovat. Uživatel následně potvrdil tento výklad.

**DB reprezentace:** MAIN.CINNOSTI 2 = kontrola po skenu; nabídka/zápis false.

**Implementace:** config/business_rules.example.json#/services/dermatoscope_followup

**Důkazy:** LIVE.effective_rules; LIVE.databases.MAIN.activities; CONTRACT; USER-REVIEW-04; USER-REVIEW-05; USER-REVIEW-09; USER-REVIEW-40; USER-REVIEW-41; docs/current_business_rules.md; USER-REVIEW-42; USER-REVIEW-43

**Jistota:** UNCLEAR

**Dopad chyby:** Záměna opakovaného skenu a kontroly, nesprávné zdroje.

**Reprodukovatelný případ:** Vstup kontrola po skenu: zapsat očekávanou službu a nutnost skeneru podle personálu; současné API odmítá tuto službu. Požadavek na prohlídku4 měsíce po skenu: agent nenabízí automatický termín, předá personálu; netvrdí, že návštěva je domluvena. USER-REVIEW-42, návrhové případy: dřívější sken bez vyšetření -> dermatoscope_followup; kontrola po zákroku/vyšetření -> regular_check; pacientem sdělený interval určuje cílové období, neznámý interval -> personál bez automatického doporučení jednoho roku. U regular_check nevyvozovat správnost aktivity5 jen z názvu service key. Test zde neproveden.

**Otázka k potvrzení:** Business význam service key potvrzen USER-REVIEW-42: prohlídka po skenu bez následného vyšetření. Technicky ověřit spolehlivé dohledání relevantního absolvovaného skenu a absenci následné prohlídky, správné DB mapování a zápis. Zachovat dřívější pravidla odložené prohlídky po skenu. Zdroj intervalu: doporučení sdělené pacientem; pokud interval nezná, upřesnění personálem. Přesná tolerance kolem doporučeného data a doklad skutečně absolvované relevantní návštěvy zůstávají k návrhu.


## MAP-05 — service_regular_check

**Doména:** service_regular_check

**Business význam / současná interpretace:** regular_check má label Kontrola po scanu, ale přiřazená DB aktivita5 se jmenuje Sken znamének2 a vyšší. Uživatel předpokládá, že opakovaná dermatoskopie stejně jako první zahrnuje nový sken a navazující lékařskou prohlídku, případně odloženou prohlídku obdobně jako po prvním skenu. Toto je předběžný výklad uživatele, nikoli nezávisle potvrzené pravidlo nebo potvrzení service key/DB aktivity. USER-REVIEW-40 (předběžné): Uživatel navrhuje orientaci podle minulých návštěv, ale není si jistý rolí opakované dermatoskopie. Domnívá se, že jde o stejnou službu na vyžádání, případně opakovanou preventivní prohlídku po čase, nikoli samostatně rozlišovanou službu. Není tím potvrzeno sloučení service keys/aktivit, totožnost opakovaného skenu a kontroly bez skenu ani časový interval opakování. Záznam minulého objednání sám nedokazuje absolvovaný sken. USER-REVIEW-41: Uživatel upřesňuje pracovní členění na prohlídku, prohlídku s dermatoskopem a navazující kontrolu po vyšetření/zákroku; opakovaná či preventivní dermatoskopie podle něj není samostatná procedura. Na výslovný požadavek pacienta může agent navazující kontrolu objednat v budoucím návrhu. Uživatel navrhuje ověřit související datum v minulých návštěvách a odvodit doporučený termín; obvyklý rok od zákroku uvádí nejistě, nikoli jako potvrzenou univerzální či nejzazší lhůtu. Rozlišení skutečně absolvovaného relevantního výkonu od pouhé rezervace a zdroj doporučeného intervalu zůstávají k vyřešení. Neměnit tím samostatné pravidlo odložené prohlídky po skenu (3/6 měsíců). USER-REVIEW-42: Uživatel výslovně potvrzuje: regular_check je navazující kontrola po zákroku nebo předchozím vyšetření; nejde o samostatnou proceduru opakované dermatoskopie. Potvrzený business význam dosud neřeší rozpor současného mapování na MAIN aktivitu5 (Sken znamének2 a vyšší). Souhlasí také s pracovním postupem pro doporučený interval kontroly: pokud pacient sdělí například doporučení lékaře za rok, hledat kolem odpovídajícího data; pokud interval nezná, předat upřesnění personálu. Automatický univerzální roční interval ani nejzazší lhůta nejsou potvrzeny. Dřívější samostatná pravidla odložené prohlídky po skenu zůstávají zachována. USER-REVIEW-43: Obecné pravidlo výběru lékaře platí i pro dermatoscope_followup a regular_check: bez preference pacienta hledat napříč ordinujícími lékaři, při zmíněné preferenci ji respektovat. Původního lékaře automaticky neupřednostňovat. Uživatel následně potvrdil tento výklad. USER-REVIEW-44: Pro kontrolu v definovaném budoucím odstupu (například za rok) lze hledat i za hranicí šesti měsíců od dneška. Hledání má mít explicitní krátký datumový filtr u cílového data, přibližně dva týdny nebo měsíc podle technické zátěže; přesná délka zatím není zvolena. Neprohledávat automaticky celé období od dneška do cílového data. Dřívější šestiměsíční rozšíření při preferovaném lékaři není zákaz objednat vzdálenější datum ani oprávnění překročit pacientem určené období či doporučený interval kontroly. USER-REVIEW-45: Krátké vyhledávací okno pro doporučenou kontrolu může zahrnovat také termíny krátce před cílovým datem, nikoli pouze od něj dál. Přesný počet dní před/po ani symetrie okna nejsou určeny. Nadále respektovat výslovné časové omezení pacienta; souhlas neznamená posun před jím stanovené nejdřívější datum.

**DB reprezentace:** MAIN.CINNOSTI 5 = Sken znamének 2 a vyšší; služby regular_check.idcinnosti=5.

**Implementace:** config/business_rules.example.json#/services/regular_check

**Důkazy:** LIVE.effective_rules; LIVE.databases.MAIN.activities; DOC-ACT; USER-REVIEW-09; USER-REVIEW-40; USER-REVIEW-41; docs/current_business_rules.md; USER-REVIEW-42; USER-REVIEW-43; USER-REVIEW-44; USER-REVIEW-45

**Jistota:** CONFLICT

**Dopad chyby:** Špatný výkon, délka a potřebná kapacita.

**Reprodukovatelný případ:** Připravit k potvrzení dva odlišné scénáře: nový opakovaný sken s lékařem versus návštěva pouze k vyhodnocení dřívějšího skenu. U prvního předběžně očekáváme obě kapacity a případnou výslovnou výjimku odkladu; konkrétní aktivity a lhůty musí být potvrzeny před implementací. USER-REVIEW-42, návrhové případy: dřívější sken bez vyšetření -> dermatoscope_followup; kontrola po zákroku/vyšetření -> regular_check; pacientem sdělený interval určuje cílové období, neznámý interval -> personál bez automatického doporučení jednoho roku. U regular_check nevyvozovat správnost aktivity5 jen z názvu service key. Test zde neproveden. USER-REVIEW-44, návrhový případ: pacient uvádí doporučenou kontrolu za rok -> datumové filtry pouze pro krátké okno v daném odstupu, nikoli sken celého roku nebo odmítnutí kvůli vzdálenosti nad šest měsíců. Zkontrolovat obě hranice filtru a respektování pacientova požadavku. Test zatím neproveden. USER-REVIEW-45, návrhový případ: kontrola přibližně na začátek října může zahrnout konec září, pokud spadá do zvoleného krátkého okna a neporušuje výslovné omezení pacienta. Test zde neproveden.

**Otázka k potvrzení:** Business význam service key potvrzen USER-REVIEW-42: kontrola po zákroku nebo vyšetření. Vyřešit technický rozpor: současná aktivita5 je označena Sken znamének2 a vyšší, současný label Kontrola po scanu neodpovídá potvrzenému významu. Potvrzení významu není schválení tohoto DB mapování. Zdroj intervalu: doporučení sdělené pacientem; pokud interval nezná, upřesnění personálem. Přesná tolerance kolem doporučeného data a doklad skutečně absolvované relevantní návštěvy zůstávají k návrhu. USER-REVIEW-44: Při implementaci ověřit zátěž cíleného hledání a vybrat dva týdny nebo měsíc; USER-REVIEW-45 dovoluje i krátce před cílovým datem; přesný počet dní před/po a případná symetrie okna zůstávají k návrhu. Nenalezený termín nesmí automaticky vést k rozšíření za hranice požadovaného období. Šest měsíců neinterpretovat jako maximální vzdálenost objednání od dneška.


## MAP-06 — service_plasma

**Doména:** service_plasma

**Business význam / současná interpretace:** Plazma je v kódu pod laser aktivitou, s markerem plazma, 30 minut a lékařem MAIN 8; zatím handoff. Uživatel potvrdil plazmu/PRP zatím mimo první scope, s předáním personálu. Plazmu označuje za safe případ klientského objednání pro budoucí rozšíření; toto označení není ověřením klinické bezpečnosti, konkrétní délky nebo DB mapování.

**DB reprezentace:** MAIN.IDCINNOSTI=3; INFO marker; fixed_minutes=30; allowed=[8], excluded=[2,4].

**Implementace:** config/business_rules.example.json#/services/plasma; scripts/appointment_write.py::_service_info

**Důkazy:** LIVE.effective_rules; DOC-ACT; USER-REVIEW-19

**Jistota:** PROBABLE

**Dopad chyby:** Špatná délka, lékař, případně záměna PRP a jiné plazmy.

**Reprodukovatelný případ:** Personál porovná dva různě pojmenované výkony plazma/PRP; API plasma dnes musí odmítnout.

**Otázka k potvrzení:** Je 30 minut univerzální, pouze lékař 8, a jaký přesně marker?


## MAP-07 — service_laser

**Doména:** service_laser

**Business význam / současná interpretace:** Obecný laser není dostatečně specifická automaticky objednatelná služba; dnes zakázán. Uživatel výslovně potvrdil laserové výkony a ostatní zákroky zatím předávat personálu, bez nabídky termínů agentem.

**DB reprezentace:** MAIN aktivita 3; duration fixed_minutes s minutes=NULL; LASER má více odlišných aktivit.

**Implementace:** config/business_rules.example.json#/services/laser; scripts/agent_context.py::build_simple_service_options

**Důkazy:** LIVE.effective_rules; LIVE.databases.LASER.activities; USER-REVIEW-19

**Jistota:** UNCLEAR

**Dopad chyby:** Při pouhém povolení služby by neznámá délka mohla použít fallback intervalu.

**Reprodukovatelný případ:** Požadavek laser: handoff; před budoucím povolením každý výkon musí mít schválenou délku/zdroj.

**Otázka k potvrzení:** Rozdělit laser na které výkony a do které DB se každý objednává?


## MAP-08 — service_reservation

**Doména:** service_reservation

**Business význam / současná interpretace:** dermatoscope_reservation je technická blokace, nikoli veřejně nabízený výkon.

**DB reprezentace:** MAIN.IDCINNOSTI=6; LASER.ID=6 naopak Laserová gelová maska.

**Implementace:** config/business_rules.example.json#/services/dermatoscope_reservation; scripts/appointment_write.py::_skin_followup_idcinnosti

**Důkazy:** LIVE.effective_rules; LIVE.databases; DOC-ACT

**Jistota:** PROBABLE

**Dopad chyby:** Přenesení čísla aktivity do jiné DB vytvoří jiný výkon.

**Reprodukovatelný případ:** Porovnat oba číselníky pro ID=6, ověřit zákaz veřejného objednání.

**Otázka k potvrzení:** Jak se technické rezervace používají dnes a co je bezpečně označuje za související řádek?


## MAP-09 — activity_and_type

**Doména:** activity_and_type

**Business význam / současná interpretace:** Aktivitu určuje IDCINNOSTI→CINNOSTI; TYP používá též opakování, není číselníkem lékařských služeb.

**DB reprezentace:** MAIN aktivity 1/2/3/5/6; běžný insert TYP=1; opakování TYP=9/10.

**Implementace:** scripts/appointment_write.py::_insert_appointment; scripts/availability_engine.py::load_appointments

**Důkazy:** LIVE.databases.MAIN.activities; LIVE.databases.MAIN.procedures; DOC-ACT

**Jistota:** CONFIRMED

**Dopad chyby:** Chybné typy a ztráta opakování.

**Reprodukovatelný případ:** Číst názvy CINNOSTI a definici OBJOBJ_SEL; v UI zvlášť potvrdit význam/barvu, neodvozovat z TYP.

**Otázka k potvrzení:** Mají další hodnoty TYP zvláštní blokovací význam? Aktuální UI barvy v tomto auditu znovu nepotvrzeny.


## MAP-10 — doctor_identity

**Doména:** doctor_identity

**Business význam / současná interpretace:** MAIN ID15 je v živé DB Tamara Hrudová, ale config known uvádí Filip Ferencz. Uživatel určil databázi jako rozhodující zdroj aktuálních personálních/kalendářových údajů; nabídky proto mají respektovat aktuální DB jméno, ne historickou konfiguraci. Zda došlo k nahrazení osoby/převzetí kalendáře si uživatel ještě potvrdí. Stejné ID samo nepotvrzuje trvalou osobní identitu nebo přenos historických individuálních pravidel.

**DB reprezentace:** UZIVATEL.IDUZI=15; config.doctors.known[id=15].

**Implementace:** scripts/availability_engine.py::load_doctors; config/business_rules.example.json#/doctors/known

**Důkazy:** LIVE.databases.MAIN.users; LIVE.effective_rules; DOC-SCHEDULE; USER-REVIEW-11

**Jistota:** CONFLICT

**Dopad chyby:** Pravidlo pro jednoho lékaře se aplikuje jinému; nesprávné nabídky a jméno.

**Reprodukovatelný případ:** MAIN.UZIVATEL ID15 vrací Tamara Hrudová, config known Filip Ferencz: současné nabídky mají použít DB jméno. Nepřevzít bez důkazu historická pravidla Ferencze ani automaticky vytvořit alias Ferencz→Hrudová.

**Otázka k potvrzení:** Priorita aktuálního DB jména před starší konfigurací vyřešena uživatelem. Uživatel potvrdí historii změny osoby/kalendáře a případnou platnost historických individuálních pravidel. Rozpor v uložené konfiguraci trvá, v Stage1 se neopravuje.


## MAP-11 — doctor_aliases

**Doména:** doctor_aliases

**Business význam / současná interpretace:** Jména se normalizují bez diakritiky/titulů, dále exact/partial match. Neexistuje schválený slovník aliasů; ID má přednost před jménem.

**DB reprezentace:** UZIVATEL.JMENO/PRIJMENI; explicitní doctor_id; žádná alias tabulka v této cestě.

**Implementace:** scripts/availability_search.py::_normalize_name; scripts/availability_search.py::_resolve_doctor_filter

**Důkazy:** CODE; LIVE.databases.MAIN.users; DOC-SCHEDULE

**Jistota:** PROBABLE

**Dopad chyby:** Nesprávný lékař při kolizi jmen nebo rozporném ID a jménu.

**Reprodukovatelný případ:** Bednář→2 po vyloučení 4; neznámý/ambiguous→[]; doctor_id=11 se jménem jiné lékařky: zaznamenat přednost ID.

**Otázka k potvrzení:** Má se rozpor doctor_id/jméno vždy odmítnout? Jaké aliasy personál schvaluje?


## MAP-12 — doctor_eligibility

**Doména:** doctor_eligibility

**Business význam / současná interpretace:** Uživatel potvrdil, že prohlídky po dermatoskopii provádějí všichni lékaři centra, vždy podle toho, kdo právě ordinuje. Podle jeho pochopení bývají přítomni dva ordinující lékaři; nejde o potvrzený pevný počet ani algoritmický limit. Toto nepotvrzuje způsobilost technických účtů v UZIVATEL ani pravidla jiných výkonů jako plasma. Kód používá allow/exclude seznamy, nikoli known.status jako filtr.

**DB reprezentace:** Globálně excluded [4,10], allowed []; skin/derm allowed []; plasma [8]. Technické účty MAIN 3/6/7 jsou v UZIVATEL.

**Implementace:** scripts/agent_context.py::filter_doctors; scripts/business_rules.py::filter_doctors_for_service

**Důkazy:** LIVE.search_config; LIVE.effective_rules; LIVE.databases.MAIN.users; USER-REVIEW-10

**Jistota:** UNCLEAR

**Dopad chyby:** Technický či nezpůsobilý kalendář může být nabízen, pokud získá rozvrh.

**Reprodukovatelný případ:** Dva skuteční ordinující lékaři mohou být kandidáti na prohlídku, ale nabídka musí ověřit sdílený sken. Technický účet s rozvrhem není tímto pravidlem oprávněným lékařem. Pokud v rozvrhu jsou tři skuteční lékaři, nesmí se třetí vyřadit jen na základě nepodloženého limitu dva.

**Otázka k potvrzení:** Způsobilost všech právě ordinujících skutečných lékařů pro prohlídku po dermatoskopii potvrzena. Technicky zbývá ověřit aktivní personální identity a odlišit technické/duplicitní účty; nepovažovat každý UZIVATEL za lékaře ani omezit počet na dva. Eligibility ostatních služeb zůstává samostatná.


## MAP-13 — workplaces

**Doména:** workplaces

**Business význam / současná interpretace:** Pracoviště je součást kontextu a rezervace, ale fyzický význam jednotlivých ID není doložen.

**DB reprezentace:** MAIN OBSPRAC.IDPRAC obsahuje 1,2; LASER 1,2,9,12. Žádná rovnost významu mezi DB není potvrzena.

**Implementace:** scripts/availability_engine.py::find_schedule_contexts; scripts/availability_engine.py::load_appointments

**Důkazy:** LIVE.databases.*.schedule_workplaces; LIVE.laser_mapping

**Jistota:** UNCLEAR

**Dopad chyby:** Kolize kapacity napříč pracovišti nebo nabídka jiné lokality.

**Reprodukovatelný případ:** Pro každé ID personál přiřadí název/místnost a screenshot rozvrhu bez pacienta.

**Otázka k potvrzení:** Co znamenají tato pracoviště a sdílejí stejného lékaře nebo přístroj?


## MAP-14 — scan_calendar

**Doména:** scan_calendar

**Business význam / současná interpretace:** Čtecí implementace používá LASER IDUZI5, IDPRAC1 jako jediný scan kalendář. Uživatel potvrdil jeden fyzický dermatoskop a sdílený kalendář skenu pro ordinující lékaře; přesné přiřazení tohoto kalendáře k LASER5/1 tím nepotvrdil.

**DB reprezentace:** LASER.UZIVATEL5=Sken Focení skeny; config laser_calendar.local.json.

**Implementace:** scripts/laser_calendar.py::open_scan_calendar; scripts/laser_calendar.py::ScanCalendar

**Důkazy:** LIVE.laser_mapping; LIVE.databases.LASER.users; USER-OCT7; USER-REVIEW-10

**Jistota:** PROBABLE

**Dopad chyby:** Jiný/neúplný kalendář nezachytí skutečnou obsazenost.

**Reprodukovatelný případ:** 7.10. číst kalendář5/pracoviště1; porovnat 14:45–15:00 s personálem.

**Otázka k potvrzení:** Je LASER5/pracoviště1 kompletním sdíleným kalendářem skenu, který uživatel popsal? Jeden přístroj je potvrzen; potřebujeme ještě ověřit případná samostatná omezení obsluhy.


## MAP-15 — duration

**Doména:** duration

**Business význam / současná interpretace:** Uživatel potvrdil: běžná prohlídka zabírá jedno políčko kalendáře konkrétního lékaře. Více políček je krajní případ, který musí posoudit personál; agent nemá potřebné prodloužení sám odhadovat. Standardní délka tedy není univerzálních15 minut ani natvrdo podle jména lékaře. Přesné technické přiřazení UI políčka k rozvrhovému bloku a INTERVAL je stále k ověření. Historický audit našel10min kontexty u více lékařů, přestože uživatel původně předpokládal běžně10 minut jen u Bednáře.

**DB reprezentace:** OBSDNE_PRAVODLIS_SEL.INTERVAL; engine vybírá nejmenší kladný interval v kontextu; fallback15.

**Implementace:** scripts/availability_engine.py::schedule_interval_values; scripts/availability_engine.py::compute_day_availability; scripts/agent_context.py::context_slot_interval

**Důkazy:** CODE; DOC-SCHEDULE; USER-REVIEW-07; USER-REVIEW-08

**Jistota:** UNCLEAR

**Dopad chyby:** Při různých intervalech v témže kontextu může mít nabídka špatný konec/délku.

**Reprodukovatelný případ:** Pro běžnou prohlídku rezervovat právě jedno políčko daného kalendáře. V syntetickém dni s blokem09:00/30min/15 a10:00/20min/10 musí délka odpovídat konkrétnímu políčku, nikoli minimu celého kontextu, až bude vazba políčko–INTERVAL ověřena. Požadavek na více políček vyžaduje posouzení personálem; agent délku neurčuje.

**Otázka k potvrzení:** Business pravidlo jedno políčko / prodloužení posuzuje personál je potvrzeno. Zbývá technicky ověřit UI políčko→konkrétní blok/INTERVAL, zejména při různých intervalech v jednom dni. Aktuální10min kalendáře a případné změny podle dne není vhodné odvozovat natvrdo ze jména.


## MAP-16 — scan_intervals_buffers

**Doména:** scan_intervals_buffers

**Business význam / současná interpretace:** Ve standardním průběhu uživatel potvrdil bezprostředně navazující prohlídku po skenu. Předpokládá standardní délku skenu15 minut, s výslovnou nejistotou; delší sken může být krajní výjimkou, kterou agent pravděpodobně nedokáže posoudit. Současný kód používá15 minut. Technicky nulový buffer ani postup pro delší sken nejsou potvrzené. Uživatel předběžně popsal T−15 také vůči začátku společného bloku pro pacienta na jeho začátku. Způsob časování dalších scanů/příchodů ve stejném bloku není potvrzen. Historie ověřena:194c52f definuje buckety jen pro skin; cc846e7 přidává scan15 minut před technickým časem lékaře; c767598 požaduje sdělit oba časy. Příklad lékař11:15→scan11:00 odpovídá tomuto kódu. Implementace společného bucketu pro dermatoskopii nebyla v dostupné historii nalezena. USER-REVIEW-15: pracovní návrh má zachovat sken před prohlídkou i při společném příchodu; větší buffer nyní není požadován, případná změna až po upřesnění provozu. Nejde o potvrzení technického nulového bufferu pro všechny případy.

**DB reprezentace:** scan_before_minutes=15, scan_duration_minutes=15; žádné obecné buffer pole.

**Implementace:** scripts/agent_context.py::build_dermatoscope_options; scripts/agent_context.py::inferred_scan_conflict

**Důkazy:** LIVE.effective_rules; CODE; USER-REVIEW-02; USER-REVIEW-06; USER-REVIEW-13; HISTORY-ARRIVAL; USER-REVIEW-14; USER-REVIEW-15

**Jistota:** UNCLEAR

**Dopad chyby:** Scan může zasahovat do lékaře či nedat čas na přesun.

**Reprodukovatelný případ:** Doctor15:00: při offset15/duration10 kód 14:50–15:00; při offset15/duration20 14:45–15:05. Očekávání vyžaduje schválení.

**Otázka k potvrzení:** Personálu zbývá potvrdit standardních15 minut a jak poznat/předat požadavek na delší sken bez klinického odhadu agentem. Jaká je délka navazující prohlídky a přesný odstup?


## MAP-17 — schedule_boundaries

**Doména:** schedule_boundaries

**Business význam / současná interpretace:** Celý interval musí být uvnitř dostupného rozvrhu; částečný závěrečný slot je v enginu vyřazen. LASER kontroluje souvislé pokrytí.

**DB reprezentace:** CAS+DOBA interval rozvrhu; LASER sjednocuje navazující bloky.

**Implementace:** scripts/availability_engine.py::compute_slots; scripts/laser_calendar.py::interval_is_available

**Důkazy:** CODE; TEST-SAFETY; TEST-LASER

**Jistota:** PROBABLE

**Dopad chyby:** Přesah za ordinační dobu.

**Reprodukovatelný případ:** Blok09:00–09:15 krok10→pouze09:00; sken15:50–16:05 proti konci16:00→zamítnout.

**Otázka k potvrzení:** Může výkon překročit hranici bloku/přestávku a kdo může dát výjimku?


## MAP-18 — overlap

**Doména:** overlap

**Business význam / současná interpretace:** Současná kontrola používá polootevřené intervaly: sousední konce neblokují, libovolný kladný překryv blokuje.

**DB reprezentace:** startA<endB AND endA>startB; CAS/CASDO.

**Implementace:** scripts/availability_engine.py::compute_slots; scripts/agent_context.py::time_interval_overlaps; scripts/laser_calendar.py::interval_is_available

**Důkazy:** CODE; TEST-SAFETY; TEST-LASER; USER-OCT7

**Jistota:** PROBABLE

**Dopad chyby:** Nabídka obsazeného času nebo zbytečné blokování sousedního času.

**Reprodukovatelný případ:** 15:40–15:50 proti15:45–15:55→obsazeno; 15:00–15:10 proti15:10–15:20→bez překryvu, pokud nejsou buffery.

**Otázka k potvrzení:** Schválit nulový odstup mezi návštěvami a jednotku přesnosti (sekundy/minuty).


## MAP-19 — recurrence

**Doména:** recurrence

**Business význam / současná interpretace:** Dostupnost čte expandované výskyty TYP9/10; seznam pacientových rezervací je naopak vylučuje; zápisový konflikt používá přímou tabulku.

**DB reprezentace:** OBJOBJ_SEL: denně/stejný den týdne DATUM…DATUMDO; lookup TYP NOT IN(9,10); writer DATUM=? přímo.

**Implementace:** scripts/availability_engine.py::load_appointments; scripts/patient_lookup.py::_load_appointments; scripts/appointment_write.py::_find_conflicts

**Důkazy:** LIVE.databases.MAIN.procedures; CODE; DOC-ACT

**Jistota:** CONFLICT

**Dopad chyby:** Výskyt může blokovat nabídku, ale není vidět/bezpečně identifikován pro přesun či zrušení.

**Reprodukovatelný případ:** Denní/týdenní série s počátkem před dotazovaným dnem: porovnat expanded dostupnost vs lookup; žádné mutace.

**Otázka k potvrzení:** Smí personál upravit jeden výskyt, nebo celou sérii? Jak Medicus reprezentuje výjimku série?


## MAP-20 — schedule_exceptions

**Doména:** schedule_exceptions

**Business význam / současná interpretace:** Procedura preferuje OBSODLIS pro celé pracoviště/den. API však objeví kontext jen přes pravidelné OBSPRAC, takže mimořádný den bez pravidelného kontextu může být neviditelný.

**DB reprezentace:** OBSDNE_PRAVODLIS_SEL nejprve OBSODLIS OBJED=A a při nálezu EXIT; potom OBSPRAC.

**Implementace:** scripts/availability_engine.py::find_schedule_contexts; scripts/availability_engine.py::load_schedule_blocks

**Důkazy:** LIVE.databases.MAIN.procedures; CODE

**Jistota:** UNCLEAR

**Dopad chyby:** Mimořádná ordinace může zmizet; částečná výjimka může potlačit jiné lékaře.

**Reprodukovatelný případ:** Syntetický den bez OBSPRAC kontextu, ale s OBSODLIS: současný compute_day nenavštíví proceduru. UI musí potvrdit správnou prioritu.

**Otázka k potvrzení:** Nahrazuje výjimka rozvrh celého pracoviště nebo jen lékaře? Jak se značí úplné zavření?


## MAP-21 — schedule_week_type

**Doména:** schedule_week_type

**Business význam / současná interpretace:** Kontexty se vybírají podle DENTYD/platnosti, ale kód explicitně neodvozuje lichý/sudý týden z data.

**DB reprezentace:** OBSPRAC.TYPTYD; procedura TYPTYD=:TYPTYD OR TYPTYD=4.

**Implementace:** scripts/availability_engine.py::find_schedule_contexts; scripts/availability_engine.py::load_schedule_blocks

**Důkazy:** LIVE.databases.MAIN.procedures; CODE

**Jistota:** UNCLEAR

**Dopad chyby:** Nabídnutí pravidelného rozvrhu z nesprávného týdne.

**Reprodukovatelný případ:** Syntetické dvě TYPTYD ve stejný den týdne; porovnat skutečné dva po sobě jdoucí týdny v UI.

**Otázka k potvrzení:** Co přesně znamenají hodnoty TYPTYD a jak se určují z data?


## MAP-22 — blocking_activities

**Doména:** blocking_activities

**Business význam / současná interpretace:** MAIN sdílený scan blocker list je [1,6], starší dokument [1,2,5,6]. LASER na vybraném kalendáři blokuje každá aktivita.

**DB reprezentace:** MAIN1→inferred interval před návštěvou; MAIN6→CAS/CASDO; LASER libovolné IDCINNOSTI i NULL.

**Implementace:** scripts/agent_context.py::load_dermatoscope_blockers; scripts/agent_context.py::inferred_scan_conflict; scripts/laser_calendar.py::ScanCalendar

**Důkazy:** LIVE.effective_rules; DOC-ACT; CODE

**Jistota:** CONFLICT

**Dopad chyby:** Ignorovaný skutečný blocker nebo dvojí/příliš konzervativní omezení.

**Reprodukovatelný případ:** Samostatně fixture MAIN2, MAIN5, MAIN6 a LASER28; business očekávání musí personál potvrdit.

**Otázka k potvrzení:** Jsou MAIN2/5 scanner blockers? Má MAIN dál odvozovat scan, když je LASER autoritativní?


## MAP-23 — resource_capacity

**Doména:** resource_capacity

**Business význam / současná interpretace:** Uživatel potvrdil jeden fyzický dermatoskop společný všem právě ordinujícím lékařům. Skeny pacientů různých lékařů se musí vejít do stejného sdíleného kalendáře; fyzická kapacita skeneru je1. Dvě ordinace tedy neznamenají dva souběžné skeny. Implementace používá binární kontrolu překryvu.

**DB reprezentace:** config shared_resources.dermatoscope.capacity=1; overlap vrací první konflikt.

**Implementace:** scripts/agent_context.py::inferred_scan_conflict; scripts/laser_calendar.py::interval_is_available

**Důkazy:** LIVE.effective_rules; CODE; USER-REVIEW-10

**Jistota:** CONFIRMED

**Dopad chyby:** Při chybném rozdělení kapacity podle lékaře by dva pacienti dostali současně jediný přístroj.

**Reprodukovatelný případ:** Sken pacienta lékařeA14:45–15:00 blokuje tentýž interval i pro pacienta lékařeB, i když je B volný. Prohlídka již oskenovaného pacienta uA a následný nepřekrývající se sken jiného pacienta používají odlišné zdroje; potvrzená kapacita přístroje sama neurčuje dostupnost personálu.

**Otázka k potvrzení:** Počet přístrojů a sdílení mezi lékaři vyřešeny uživatelem. Samostatná dostupnost obsluhy a přesná identita DB kalendáře zůstávají k ověření; dva ordinující lékaři jsou dosavadní pochopení provozu, nikoli pevný invariant.


## MAP-24 — time_past

**Doména:** time_past

**Business význam / současná interpretace:** Současný kód vylučuje začátky <= nyní Europe/Prague včetně scanu, ale neimplementuje hodinový předstih. Uživatel v USER-REVIEW-17 určil prozatímní pevný default: nejdříve1 hodinu od zavolání; konkrétní krajní případy ověří později s klientem. Pro návrh interpretujeme tuto lhůtu vůči skutečně požadovanému příchodu pacienta (bucket nebo sken), nikoli jen internímu času lékaře. Tato technická interpretace je odlišená od explicitně schválené hodnoty60 minut. Nelze posunout pacientovi příjezd svévolně tak, aby se obešlo pravidlo společného příchodu.

**DB reprezentace:** Datetime v API; DATUM/CAS v DB bez timezone; spoken bucket může být dříve než technický čas.

**Implementace:** scripts/availability_search.py::_clinic_now; scripts/availability_search.py::_option_is_future; scripts/availability_search.py::_apply_spoken_time

**Důkazy:** CODE; TEST-SAFETY; LIVE.effective_rules; USER-REVIEW-12; USER-REVIEW-17

**Jistota:** UNCLEAR

**Dopad chyby:** Agent může říci již uplynulý společný příjezd, přestože technický čas je budoucí.

**Reprodukovatelný případ:** Návrhové případy s počátkem hovoru10:00: příchod10:59 odmítnout,11:00 splňuje60min minimum, pokud ostatní pravidla dovolí nabídku. Lékař11:00 a povinný sken10:45 minimum nesplní. Volání11:10 a bucket11:00 odmítnout bez ohledu na pozdější volné technické políčko. Toto jsou případy pro pozdější implementaci, nikoli tvrzení o současném kódu.

**Otázka k potvrzení:** Hodnota60 minut od zavolání je schválený prozatímní default. Technicky ještě určit autoritativní čas začátku hovoru, postup při chybějícím údaji a přehodnocení při dlouhém hovoru či pozdějším schvalování. Vazba na skutečný příchod je navržený výklad; klientské výjimky pro budoucí úpravu ověří uživatel.


## MAP-25 — arrival_buckets

**Doména:** arrival_buckets

**Business význam / současná interpretace:** Uživatel potvrdil záměr společného příchodu: pacienti čekají a lékař je postupně zve. V USER-REVIEW-15 určil jako pracovní návrh bucket pro příchod také u dermatoskopie podle předchozího výkladu. Musí zůstat zachováno pořadí sken před prohlídkou, bez kolize jediného přístroje. Větší časový buffer lze řešit později; nyní jej uživatel nepožaduje. Přesné časování příchodu vůči jednotlivým scanům je konkrétní otázka pro personál. Historie kódu194c52f definuje buckety pouze pro skin, cc846e7/c767598 pro dermatoskopii individuální scan15 minut před termínem lékaře; pracovní návrh tedy není popisem aktuální implementace. USER-REVIEW-16: uživatel podle poznámek klienta výslovně potvrdil společné příchody Po–Pá11:00, Po15:00, Út–Čt16:00, Pá14:00. Příznak Draft v historické poznámce proto již neznamená neověřený čas dopoledního příchodu. Potvrzení se nevztahuje automaticky na konce technických intervalů ani přesnou transformaci dermatoskopického příchodu. USER-REVIEW-22: Časové omezení volajícího se vztahuje k požadovanému příchodu, u dermatoskopie již se započtením skenu před prohlídkou. Nestačí, aby omezení splňoval pouze čas lékaře.

**DB reprezentace:** Po–Pá11–12→11; Po15–16→15; Út–Čt16–17→16; Pá14–15→14; technický čas zůstává.

**Implementace:** scripts/business_rules.py::afternoon_bucket_for_time; scripts/availability_search.py::_apply_spoken_time; config/business_rules.example.json#/operational_rules/afternoon_arrival_buckets

**Důkazy:** LIVE.effective_rules; CONTRACT; USER-REVIEW-12; USER-REVIEW-13; HISTORY-ARRIVAL; USER-REVIEW-14; USER-REVIEW-15; USER-REVIEW-16; USER-REVIEW-17; USER-REVIEW-22

**Jistota:** UNCLEAR

**Dopad chyby:** Personál očekává jiný příjezd než pacient; hraniční čas chybně zařazen.

**Reprodukovatelný případ:** Ve schváleném společném bloku může technické políčko11:30 odpovídat příchodu11:00; agent nemá toto pravidlo svévolně nahradit přesným časem políčka. Pro pondělní16:00→15:00 ještě ověřit zahrnutí konce. Příchod nesmí být interpretován jako garance okamžitého zahájení prohlídky. Synteticky blok11:00, technické prohlídky11:00 a11:30: scan10:45–11:00 a11:15–11:30 se nepřekrývají. Automatické odvození obou scan rezervací z bucketu11:00 by je naopak položilo na10:45–11:00 a porušilo kapacitu1. Společný příchod obou pacientů10:45 není totéž co dvě současné scan rezervace; správné komunikační pravidlo čeká na potvrzení. Návrhový případ: pacient může až po 14:00; lékař 14:10 se skenem/příchodem 13:55 není vyhovující nabídka. Stejně vyřadit termín, jehož společný příchod je před pacientovým omezením, i když technické políčko lékaře omezení splňuje. Test dosud neproveden.

**Otázka k potvrzení:** Konkrétní časy příchodů potvrzeny USER-REVIEW-16; pro blízké termíny uživatel určil pracovní default60 minut od zavolání (MAP-24). Zbývají koncová technická políčka a přesná vazba příchodu/scanu/prohlídky u dermatoskopie. Neodvozovat univerzálně bucket−15 pro všechny scan rezervace.


## MAP-26 — emergency

**Doména:** emergency

**Business význam / současná interpretace:** Uživatel potvrdil, že termíny před08:00 jsou pro pohotovost a běžně se nenabízejí. Pravidla jejich rezervování ověří s klientem. Navrhuje emergency tag při zmínce akutního případu: uklidňující reakce, doporučení pohotovostního času a návrh okamžitého přesměrování na personál. Tag a doporučení času jsou zatím návrh, nikoli schválená rezervace nebo klinická triáž. Současný API parametr emergency=true naproti tomu odemyká časový filtr; tuto existující technickou možnost nelze zaměnit za oprávnění navrženého tagu.

**DB reprezentace:** API request flag, žádné prokázané DB oprávnění emergency.

**Implementace:** scripts/availability_search.py::_option_allowed_by_operational_rules; config/business_rules.example.json#/operational_rules/before_time_requires_emergency

**Důkazy:** LIVE.effective_rules; TEST-BUSINESS; CONTRACT; USER-REVIEW-18

**Jistota:** UNCLEAR

**Dopad chyby:** Model si může sám odemknout časy určené jiné skupině.

**Reprodukovatelný případ:** Běžný požadavek: čas07:50 nenabízet. Volající výslovně zmiňuje akutní případ: návrh označí požadavek k rychlému předání personálu, bez samostatného posouzení diagnózy či potvrzení pohotovostní rezervace. Ve starém kódu emergency=true propustí před08:00 časový filtr; budoucí tag nesmí tuto pravomoc získat jen shodným názvem. Konkrétní sdělovaný čas a neúspěšné předání čekají na schválený postup.

**Otázka k potvrzení:** Klient potvrdí, zda a jak se pohotovostní sloty rezervují a jaký čas/instrukci smí agent doporučit. Jak postupovat mimo pohotovostní dobu a při nedostupnosti personálu? Má být výjimka z60min předstihu? Taková výjimka není tímto návrhem schválena. Tag/transfer workflow zůstává návrhem pro pozdější etapu.


## MAP-27 — search_window

**Doména:** search_window

**Business význam / současná interpretace:** Výchozí hledání může rozšířit30 na180 dní, bez víkendů; explicitní date_to rozšíření omezí. Pořadí je den→lékař→kontext, ne globální čas dne. USER-REVIEW-21: Pro požadovaného lékaře nejprve hledat v základním rozsahu a při neúspěchu rozšířit hledání nejvýše na 6 měsíců, stále u stejného lékaře a vždy respektovat časová i další omezení volajícího. Nenajde-li se termín ani potom, nabídnout volbu hledat u jiného lékaře nebo předat personálu; lékaře neměnit automaticky. Jde o potvrzený návrh chování, nikoli změnu runtime. USER-REVIEW-22: Časové omezení volajícího se vztahuje k požadovanému příchodu, u dermatoskopie již se započtením skenu před prohlídkou. Nestačí, aby omezení splňoval pouze čas lékaře. USER-REVIEW-23: Agent smí nabízet pouze pondělí až pátek. Víkendový slot považovat za podezření na chybu zpracování rozvrhu, nikoli za povolenou výjimku; nenabízet jej ani na výslovný požadavek pacienta nebo při rozšíření hledání. Toto potvrzené business pravidlo je přísnější než současný parametr include_weekends. USER-REVIEW-24: Uživatel požaduje samostatný seznam svátků pro daný rok, který defaultně blokuje dostupnost i při volném slotu vráceném databází. Není potvrzeno, zda databázový rozvrh svátky správně zohledňuje. Návrhový výklad asistenta: české svátky, pokrytí všech roků dotčených hledáním včetně přelomu roku; blokace ve výpočtu dostupnosti, nikoli automatické zápisy rezervací do Medicusu. Konkrétní seznam a jeho zdroj se ověří při implementaci. USER-REVIEW-25: Pokud pacient neurčí lékaře, agent hledá napříč všemi skutečně ordinujícími lékaři a nabízí nejbližší dostupné termíny splňující ostatní pravidla a požadavky pacienta. Pořadí lékařů v databázi nesmí samo určovat přednost nabídky. USER-REVIEW-26: Při přesunu platí stejný výběr lékaře jako při novém objednání. Respektovat preferenci lékaře a další omezení, pokud je pacient v hovoru zmínil, i když je při samotné žádosti o přesun neopakuje. Bez preference hledat napříč ordinujícími lékaři; původní lékař není automaticky preferencí pacienta. Při preferovaném lékaři platí rozšíření hledání nejvýše na 6 měsíců v mezích požadavku a při neúspěchu volba jiného lékaře nebo personálu. USER-REVIEW-43: Obecné pravidlo výběru lékaře platí i pro dermatoscope_followup a regular_check: bez preference pacienta hledat napříč ordinujícími lékaři, při zmíněné preferenci ji respektovat. Původního lékaře automaticky neupřednostňovat. Uživatel následně potvrdil tento výklad. USER-REVIEW-44: Pro kontrolu v definovaném budoucím odstupu (například za rok) lze hledat i za hranicí šesti měsíců od dneška. Hledání má mít explicitní krátký datumový filtr u cílového data, přibližně dva týdny nebo měsíc podle technické zátěže; přesná délka zatím není zvolena. Neprohledávat automaticky celé období od dneška do cílového data. Dřívější šestiměsíční rozšíření při preferovaném lékaři není zákaz objednat vzdálenější datum ani oprávnění překročit pacientem určené období či doporučený interval kontroly. USER-REVIEW-45: Krátké vyhledávací okno pro doporučenou kontrolu může zahrnovat také termíny krátce před cílovým datem, nikoli pouze od něj dál. Přesný počet dní před/po ani symetrie okna nejsou určeny. Nadále respektovat výslovné časové omezení pacienta; souhlas neznamená posun před jím stanovené nejdřívější datum.

**DB reprezentace:** request date_from/date_to/days_ahead/ensure_first_available; UZIVATEL ORDER BY IDUZI.

**Implementace:** scripts/availability_search.py::_search_availability; scripts/availability_search.py::_iter_dates

**Důkazy:** CODE; TEST-FILTERS; TEST-BUSINESS; USER-REVIEW-21; USER-REVIEW-22; USER-REVIEW-23; USER-REVIEW-24; USER-REVIEW-25; USER-REVIEW-26; USER-REVIEW-43; USER-REVIEW-44; USER-REVIEW-45

**Jistota:** UNCLEAR

**Dopad chyby:** Nejbližší může znamenat nejbližší den, nikoli čas; preference mohou být porušeny.

**Reprodukovatelný případ:** Dva lékaři téhož dne s15:00 a09:00: ověřit pořadí a limit3; Současný kód umožňuje sobotu přes include_weekends; podle USER-REVIEW-23 má budoucí agentní cesta sobotu i neděli vždy vyloučit. Návrhové případy: u požadovaného lékaře bez výsledku v základním rozsahu, ale s výsledkem v rozšířeném; bez výsledku do 6 měsíců -> nabídka jiného lékaře nebo personálu; omezení volajícího na kratší období/konkrétní dny a časy zůstávají zachována při rozšíření. Neprováděno proti produkci. Návrhový případ: pacient může až po 14:00; lékař 14:10 se skenem/příchodem 13:55 není vyhovující nabídka. Stejně vyřadit termín, jehož společný příchod je před pacientovým omezením, i když technické políčko lékaře omezení splňuje. Test dosud neproveden. Návrhový případ: databáze vrátí platný sobotní/nedělní slot; nesmí být nabídnut ani při include_weekends=true či rozšířeném hledání u konkrétního lékaře. Tato změna zatím neimplementována ani netestována. Návrhové případy pro svátky: svátek ve všední den s volným DB slotem je vyloučen; běžný všední den zůstává způsobilý podle ostatních pravidel; hledání přes prosinec/leden načte svátky obou roků; seznam zahrnuje i pohyblivé svátky podle ověřeného zdroje. Zatím bez implementace či provedení testů. USER-REVIEW-25, návrhový případ bez preference lékaře: při vyhovujících příchodech 09:00 a 15:00 téhož dne musí být dřívější nabídka vybrána před pozdější bez ohledu na ID lékaře; řazení napříč lékaři před aplikací limitu. Respektovat skutečný příchod včetně skenu/bucketu a všechna omezení pacienta. Zatím bez implementace. Návrhové případy přesunu: bez preference lze nabídnout jiného ordinujícího lékaře; s preferencí zmíněnou dříve v hovoru ji zachovat i bez opakování při žádosti o přesun; původního lékaře neodvozovat jako preferenci pouze ze staré rezervace. Zatím bez implementace a provedení testů. USER-REVIEW-44, návrhový případ: pacient uvádí doporučenou kontrolu za rok -> datumové filtry pouze pro krátké okno v daném odstupu, nikoli sken celého roku nebo odmítnutí kvůli vzdálenosti nad šest měsíců. Zkontrolovat obě hranice filtru a respektování pacientova požadavku. Test zatím neproveden. USER-REVIEW-45, návrhový případ: kontrola přibližně na začátek října může zahrnout konec září, pokud spadá do zvoleného krátkého okna a neporušuje výslovné omezení pacienta. Test zde neproveden.

**Otázka k potvrzení:** Horizont při hledání konkrétního lékaře potvrzen: nejvýše 6 měsíců v mezích požadavku volajícího. Technicky vyjasnit kalendářních 6 měsíců versus současných 180 dní a ukotvení horizontu pro budoucí date_from; bez automatického ztotožnění. Časové omezení na příchod včetně předcházejícího skenu potvrzeno USER-REVIEW-22. Víkendy vyloučeny USER-REVIEW-23; USER-REVIEW-25 potvrzuje nabídku nejbližších vyhovujících termínů napříč ordinujícími lékaři bez pacientovy preference; zbývá technicky stanovit řazení při shodném příchodu a rozdílném technickém čase prohlídky. USER-REVIEW-24 potvrzuje výchozí blokaci svátků samostatným seznamem nezávisle na rozvrhu DB; konkrétní zdroj seznamu a případné oprávnění k provozním výjimkám zbývají k návrhu. Nezaměnit požadavek na čas příchodu s výslovným požadavkem odejít do určité hodiny. Zátěž rozšířeného hledání ověřit při implementaci. USER-REVIEW-44: Při implementaci ověřit zátěž cíleného hledání a vybrat dva týdny nebo měsíc; USER-REVIEW-45 dovoluje i krátce před cílovým datem; přesný počet dní před/po a případná symetrie okna zůstávají k návrhu. Nenalezený termín nesmí automaticky vést k rozšíření za hranice požadovaného období. Šest měsíců neinterpretovat jako maximální vzdálenost objednání od dneška.


## MAP-28 — create_semantics

**Doména:** create_semantics

**Business význam / současná interpretace:** Legacy create znovu hledá přesný termín a zapisuje hlavní řádek; pro derm nevytvoří LASER řádek. Nyní je tento zápis zakázaný. USER-REVIEW-29: Zakládání nové pacientské karty je mimo aktuální scope agenta. Pro založení termínu je nutná existující pacientská karta a její IDPAC; bez IDPAC termín nevytvářet. Pokud kartu nelze dohledat, předat původní požadavek personálu podle pravidla mimo-scope. Nedohledání samo nedokazuje, že pacient kartu nemá. Samotná znalost IDPAC nenahrazuje potřebné ověření identity ani řešení namespace napříč databázemi. USER-REVIEW-30: Agent smí přijmout objednání za jinou osobu (například rodič za dítě nebo partner za partnerku), pokud dohledá existující kartu cílového pacienta. Rezervace musí použít IDPAC pacienta, pro kterého se návštěva domlouvá, nikoli automaticky IDPAC volajícího podle telefonního čísla. USER-REVIEW-30 se týká objednání; přesun a zrušení za jinou osobu následně potvrzuje USER-REVIEW-31. Údaje pro ověření identity a rozsah sdělovaných údajů zůstávají samostatnými otázkami. USER-REVIEW-37: Pokud vybraný termín mezitím obsadí někdo jiný, agent vyhledá nové vyhovující možnosti a nechá pacienta znovu vybrat; nenahradí termín automaticky. Při přesunu musí původní rezervace zůstat zachovaná, dokud se přesun úspěšně nedokončí. Jde o požadovaný výsledek, nikoli důkaz současné transakční bezpečnosti či oprávnění implementovat dočasné blokace. USER-REVIEW-38: Obecně jakákoli technická chyba nesmí být důvodem, aby agent prostě ukončil hovor. Má volajícího informovat o technických potížích, chybu a původní požadavek zaznamenat, notifikovat admina a přesměrovat na personál. Při neověřeném výsledku objednání/přesunu/zrušení nepotvrdit úspěch ani neodvozovat jisté selhání; personálu předat i informaci o nejistém výsledku k ověření. Pokud selže samotné přesměrování, platí fallback USER-REVIEW-20: zachovat požadavek pro následný kontakt personálu a upozornění adminovi. USER-REVIEW-39: Před každým novým objednáním agent stručně shrne službu, lékaře, datum a požadovaný čas příchodu a vyžádá si výslovné potvrzení volajícího. Shrnutí může být kompaktní, ale nesmí vynechat uvedené údaje. U dermatoskopie příchod zahrnuje sken před prohlídkou; technický čas lékaře nesmí nahradit správný čas příchodu. Potvrzení volajícího není důkaz úspěšného zápisu ani náhrada případného samostatného schvalovacího workflow.

**DB reprezentace:** MAIN INSERT OBJOBJ, TYP1, PRISEL=N, DATUMDO=DATUM, CREATEDBY config10; IDCINNOSTI z nabídky.

**Implementace:** scripts/appointment_write.py::_create_appointments; scripts/appointment_write.py::_insert_appointment

**Důkazy:** CODE; TEST-BUSINESS; LIVE.api_flags; DOC-ROLLBACK; USER-REVIEW-29; USER-REVIEW-30; USER-REVIEW-37; USER-REVIEW-38; USER-REVIEW-39

**Jistota:** CONFLICT

**Dopad chyby:** Main-only derm objednání není kompletní rezervace obou zdrojů.

**Reprodukovatelný případ:** Existující test_dermatoscope_write_creates_single_main_row dokládá pouze současný kód, ne správné business chování. Návrhové případy: chybějící IDPAC nebo nenalezená karta -> žádné vytvoření karty ani termínu, předání personálu; nevymýšlet náhradní IDPAC ani nepoužít kartu jiného pacienta. Zatím návrh, test zde neproveden. Návrhový případ: rodič nebo partner volá ze svého čísla a objednává jiného pacienta s existující kartou; dohledat cílového pacienta a nepoužít automaticky kartu majitele čísla. Nejednoznačná identita neznamená oprávnění vybrat libovolnou kartu. Test zatím neproveden. USER-REVIEW-37, návrhový případ: termín po nabídce obsadí jiný uživatel; agent znovu vyhledá možnosti a vyžádá nový výběr pacienta, bez automatické náhrady. Při neúspěšném přesunu zůstává původní rezervace včetně souvisejících částí zachovaná. Test zde neproveden. USER-REVIEW-38, návrhové případy: technické selhání čtení nebo zápisu -> vysvětlení volajícímu, záznam chyby a požadavku, admin alert a pokus o přesměrování; timeout s neznámým výsledkem zápisu -> bez tvrzení úspěchu a bez slepého opakování mutace, předat nejistý stav personálu; selhání transferu -> zachovat callback požadavek podle USER-REVIEW-20. Testy zde neprovedeny. USER-REVIEW-39, návrhové případy: před novým objednáním zazní stručné shrnutí služby/lékaře/data/příchodu a následuje výslovné potvrzení; při opravě některého údaje znovu potvrdit opravenou nabídku před objednáním; bez potvrzení nevytvářet rezervaci. Test zde neproveden.

**Otázka k potvrzení:** Jaké oba řádky, aktivity, stav a vazba tvoří kompletní objednání? CREATEDBY=10 je technický účet nebo osoba?


## MAP-29 — reschedule_semantics

**Doména:** reschedule_semantics

**Business význam / současná interpretace:** Legacy přesun je delete+create v jedné MAIN transakci; při známém neúspěchu endpoint rollbackuje. Neřeší LASER pár ani změnu zdroje od posledního čtení. USER-REVIEW-26: Při přesunu platí stejný výběr lékaře jako při novém objednání. Respektovat preferenci lékaře a další omezení, pokud je pacient v hovoru zmínil, i když je při samotné žádosti o přesun neopakuje. Bez preference hledat napříč ordinujícími lékaři; původní lékař není automaticky preferencí pacienta. Při preferovaném lékaři platí rozšíření hledání nejvýše na 6 měsíců v mezích požadavku a při neúspěchu volba jiného lékaře nebo personálu. USER-REVIEW-27: U běžné dermatoskopie se sken a navazující prohlídka přesouvají nebo ruší jako jeden celek. Požadavek změnit pouze jednu část agent předá personálu. Potvrzení neřeší technické párování záznamů ani transakční provedení napříč databázemi a neruší dříve povolený výjimečný scan-only scénář. USER-REVIEW-28: Prozatímní default umožňuje přijmout přesun nebo zrušení i těsně před původní návštěvou, bez časové hranice vyžadující předání personálu. Uživatel ověří případné budoucí omezení s klientem. Toto neuděluje oprávnění měnit již proběhlé návštěvy; pro nový termín při přesunu nadále platí dosavadní pravidla dostupnosti a minimálního předstihu. USER-REVIEW-31: Možnost jednat za jinou osobu platí také pro přesun a zrušení návštěvy. Pracovat s kartou cílového pacienta a jeho konkrétní rezervací, nikoli automaticky s kartou volajícího. Postup ověření identity a identifikace rezervace zůstává samostatným bodem. USER-REVIEW-36: Pokud má pacient více budoucích rezervací, agent před přesunem nebo zrušením nejprve zjistí, které návštěvy se požadavek týká, a před změnou nechá konkrétní návštěvu výslovně potvrdit volajícím. Nesmí automaticky vybrat první či nejbližší rezervaci. U běžné dermatoskopie nadále platí změna skenu a navazující prohlídky jako celku. USER-REVIEW-37: Pokud vybraný termín mezitím obsadí někdo jiný, agent vyhledá nové vyhovující možnosti a nechá pacienta znovu vybrat; nenahradí termín automaticky. Při přesunu musí původní rezervace zůstat zachovaná, dokud se přesun úspěšně nedokončí. Jde o požadovaný výsledek, nikoli důkaz současné transakční bezpečnosti či oprávnění implementovat dočasné blokace. USER-REVIEW-38: Obecně jakákoli technická chyba nesmí být důvodem, aby agent prostě ukončil hovor. Má volajícího informovat o technických potížích, chybu a původní požadavek zaznamenat, notifikovat admina a přesměrovat na personál. Při neověřeném výsledku objednání/přesunu/zrušení nepotvrdit úspěch ani neodvozovat jisté selhání; personálu předat i informaci o nejistém výsledku k ověření. Pokud selže samotné přesměrování, platí fallback USER-REVIEW-20: zachovat požadavek pro následný kontakt personálu a upozornění adminovi.

**DB reprezentace:** MAIN stará IDOBJ smazána, nová IDOBJ vytvořena; stejná connection.

**Implementace:** scripts/appointment_write.py::write_appointment; scripts/api_server.py::book_appointment

**Důkazy:** CODE; LIVE.api_flags; USER-REVIEW-26; USER-REVIEW-27; USER-REVIEW-28; USER-REVIEW-31; USER-REVIEW-36; USER-REVIEW-37; USER-REVIEW-38

**Jistota:** UNCLEAR

**Dopad chyby:** Ztráta vazeb/historie nebo částečný přesun dvou DB při budoucím zapnutí.

**Reprodukovatelný případ:** Fake connection: create vrací ok=false po cancel→endpoint rollback; není důkaz crash recovery. Návrhové případy přesunu: bez preference lze nabídnout jiného ordinujícího lékaře; s preferencí zmíněnou dříve v hovoru ji zachovat i bez opakování při žádosti o přesun; původního lékaře neodvozovat jako preferenci pouze ze staré rezervace. Zatím bez implementace a provedení testů. Návrhové případy: přesun/zrušení běžné dermatoskopie zahrne prokazatelně související sken i prohlídku; požadavek na změnu jedné části skončí předáním personálu bez částečné mutace. Při nejednoznačné vazbě nesmí dojít k odhadnutému spojení ani zrušení cizí návštěvy. Testy zde pouze navrženy. Návrhový případ: původní budoucí návštěva začíná za několik minut; samotná blízkost jejího začátku nesmí vynutit předání personálu při zrušení/přesunu. Nový termín přesunu musí nezávisle splnit dostupnost a pravidlo předstihu. Test zatím neproveden. Návrhový případ: volající přesouvá nebo ruší návštěvu jiné osoby; vybrat správného pacienta i jeho rezervaci a nezasáhnout návštěvu volajícího. Samotné odlišné telefonní číslo není důvodem zákaz zastoupení vynutit. Test zde neproveden. USER-REVIEW-36, návrhový případ: pacient má více budoucích návštěv a obecně žádá přesun/zrušení; agent si nechá určit návštěvu a před změnou ji výslovně potvrdit. Bez rozlišení a potvrzení žádnou rezervaci neměnit. Test zde neproveden. USER-REVIEW-37, návrhový případ: termín po nabídce obsadí jiný uživatel; agent znovu vyhledá možnosti a vyžádá nový výběr pacienta, bez automatické náhrady. Při neúspěšném přesunu zůstává původní rezervace včetně souvisejících částí zachovaná. Test zde neproveden. USER-REVIEW-38, návrhové případy: technické selhání čtení nebo zápisu -> vysvětlení volajícímu, záznam chyby a požadavku, admin alert a pokus o přesměrování; timeout s neznámým výsledkem zápisu -> bez tvrzení úspěchu a bez slepého opakování mutace, předat nejistý stav personálu; selhání transferu -> zachovat callback požadavek podle USER-REVIEW-20. Testy zde neprovedeny.

**Otázka k potvrzení:** Má přesun zachovat IDOBJ? Jaké návaznosti (SMS, dokumentace, LASER) musí zůstat?


## MAP-30 — cancel_semantics

**Doména:** cancel_semantics

**Business význam / současná interpretace:** Legacy zrušení fyzicky maže OBJOBJ po kontrole IDPAC; nezná samostatný stav stornováno ani zákaz historické/recurring rezervace. USER-REVIEW-27: U běžné dermatoskopie se sken a navazující prohlídka přesouvají nebo ruší jako jeden celek. Požadavek změnit pouze jednu část agent předá personálu. Potvrzení neřeší technické párování záznamů ani transakční provedení napříč databázemi a neruší dříve povolený výjimečný scan-only scénář. USER-REVIEW-28: Prozatímní default umožňuje přijmout přesun nebo zrušení i těsně před původní návštěvou, bez časové hranice vyžadující předání personálu. Uživatel ověří případné budoucí omezení s klientem. Toto neuděluje oprávnění měnit již proběhlé návštěvy; pro nový termín při přesunu nadále platí dosavadní pravidla dostupnosti a minimálního předstihu. USER-REVIEW-31: Možnost jednat za jinou osobu platí také pro přesun a zrušení návštěvy. Pracovat s kartou cílového pacienta a jeho konkrétní rezervací, nikoli automaticky s kartou volajícího. Postup ověření identity a identifikace rezervace zůstává samostatným bodem. USER-REVIEW-36: Pokud má pacient více budoucích rezervací, agent před přesunem nebo zrušením nejprve zjistí, které návštěvy se požadavek týká, a před změnou nechá konkrétní návštěvu výslovně potvrdit volajícím. Nesmí automaticky vybrat první či nejbližší rezervaci. U běžné dermatoskopie nadále platí změna skenu a navazující prohlídky jako celku. USER-REVIEW-38: Obecně jakákoli technická chyba nesmí být důvodem, aby agent prostě ukončil hovor. Má volajícího informovat o technických potížích, chybu a původní požadavek zaznamenat, notifikovat admina a přesměrovat na personál. Při neověřeném výsledku objednání/přesunu/zrušení nepotvrdit úspěch ani neodvozovat jisté selhání; personálu předat i informaci o nejistém výsledku k ověření. Pokud selže samotné přesměrování, platí fallback USER-REVIEW-20: zachovat požadavek pro následný kontakt personálu a upozornění adminovi.

**DB reprezentace:** DELETE FROM OBJOBJ WHERE IDOBJ IN(...); config enable_appointment_cancellations=false.

**Implementace:** scripts/appointment_write.py::_cancel_appointments; scripts/appointment_write.py::_fetch_appointment_rows

**Důkazy:** CODE; LIVE.api_flags; USER-REVIEW-27; USER-REVIEW-28; USER-REVIEW-31; USER-REVIEW-36; USER-REVIEW-38

**Jistota:** UNCLEAR

**Dopad chyby:** Smazání série/historie místo jednoho výkonu; nejasná auditní stopa.

**Reprodukovatelný případ:** Syntetické TYP9 a minulá rezervace: doložit chybějící specifickou validaci bez provedení DB DELETE. Návrhové případy: přesun/zrušení běžné dermatoskopie zahrne prokazatelně související sken i prohlídku; požadavek na změnu jedné části skončí předáním personálu bez částečné mutace. Při nejednoznačné vazbě nesmí dojít k odhadnutému spojení ani zrušení cizí návštěvy. Testy zde pouze navrženy. Návrhový případ: původní budoucí návštěva začíná za několik minut; samotná blízkost jejího začátku nesmí vynutit předání personálu při zrušení/přesunu. Nový termín přesunu musí nezávisle splnit dostupnost a pravidlo předstihu. Test zatím neproveden. Návrhový případ: volající přesouvá nebo ruší návštěvu jiné osoby; vybrat správného pacienta i jeho rezervaci a nezasáhnout návštěvu volajícího. Samotné odlišné telefonní číslo není důvodem zákaz zastoupení vynutit. Test zde neproveden. USER-REVIEW-36, návrhový případ: pacient má více budoucích návštěv a obecně žádá přesun/zrušení; agent si nechá určit návštěvu a před změnou ji výslovně potvrdit. Bez rozlišení a potvrzení žádnou rezervaci neměnit. Test zde neproveden. USER-REVIEW-38, návrhové případy: technické selhání čtení nebo zápisu -> vysvětlení volajícímu, záznam chyby a požadavku, admin alert a pokus o přesměrování; timeout s neznámým výsledkem zápisu -> bez tvrzení úspěchu a bez slepého opakování mutace, předat nejistý stav personálu; selhání transferu -> zachovat callback požadavek podle USER-REVIEW-20. Testy zde neprovedeny.

**Otázka k potvrzení:** Používá UI fyzické smazání, změnu stavu, nebo proceduru? Jak se zachová historie?


## MAP-31 — original_appointment

**Doména:** original_appointment

**Business význam / současná interpretace:** Originální rezervace je MAIN.IDOBJ+IDPAC. Související skin blokaci kód odhaduje podle návazného času, osoby, lékaře, pracoviště a aktivity6, nikoli explicitní vazby. USER-REVIEW-27: U běžné dermatoskopie se sken a navazující prohlídka přesouvají nebo ruší jako jeden celek. Požadavek změnit pouze jednu část agent předá personálu. Potvrzení neřeší technické párování záznamů ani transakční provedení napříč databázemi a neruší dříve povolený výjimečný scan-only scénář. USER-REVIEW-36: Pokud má pacient více budoucích rezervací, agent před přesunem nebo zrušením nejprve zjistí, které návštěvy se požadavek týká, a před změnou nechá konkrétní návštěvu výslovně potvrdit volajícím. Nesmí automaticky vybrat první či nejbližší rezervaci. U běžné dermatoskopie nadále platí změna skenu a navazující prohlídky jako celku.

**DB reprezentace:** FIRST1 následný OBJOBJ; include_related default true; bez invariantní skupiny rezervací.

**Implementace:** scripts/appointment_write.py::_appointment_ids; scripts/appointment_write.py::_expand_related_appointment_ids

**Důkazy:** CODE; LIVE.api_flags; DOC-ACT; USER-REVIEW-27; USER-REVIEW-36

**Jistota:** UNCLEAR

**Dopad chyby:** Zrušení samostatné návazné rezervace jiného účelu.

**Reprodukovatelný případ:** Dvě návazné aktivity6 se stejným pacientem: kód vybere první IDOBJ; staff musí určit skutečnou vazbu. Návrhové případy: přesun/zrušení běžné dermatoskopie zahrne prokazatelně související sken i prohlídku; požadavek na změnu jedné části skončí předáním personálu bez částečné mutace. Při nejednoznačné vazbě nesmí dojít k odhadnutému spojení ani zrušení cizí návštěvy. Testy zde pouze navrženy. USER-REVIEW-36, návrhový případ: pacient má více budoucích návštěv a obecně žádá přesun/zrušení; agent si nechá určit návštěvu a před změnou ji výslovně potvrdit. Bez rozlišení a potvrzení žádnou rezervaci neměnit. Test zde neproveden.

**Otázka k potvrzení:** Existuje stabilní link/group/GUID? Smí se vazba odvozovat pouze z času?


## MAP-32 — patient_identity

**Doména:** patient_identity

**Business význam / současná interpretace:** Lookup prohlašuje jediný výsledek za verified i pro telefon či fuzzy jméno. Dokument vyžaduje pro novou rezervaci příjmení+datum narození; legacy writer důvěřuje booleanu. USER-REVIEW-29: Zakládání nové pacientské karty je mimo aktuální scope agenta. Pro založení termínu je nutná existující pacientská karta a její IDPAC; bez IDPAC termín nevytvářet. Pokud kartu nelze dohledat, předat původní požadavek personálu podle pravidla mimo-scope. Nedohledání samo nedokazuje, že pacient kartu nemá. Samotná znalost IDPAC nenahrazuje potřebné ověření identity ani řešení namespace napříč databázemi. USER-REVIEW-30: Agent smí přijmout objednání za jinou osobu (například rodič za dítě nebo partner za partnerku), pokud dohledá existující kartu cílového pacienta. Rezervace musí použít IDPAC pacienta, pro kterého se návštěva domlouvá, nikoli automaticky IDPAC volajícího podle telefonního čísla. USER-REVIEW-30 se týká objednání; přesun a zrušení za jinou osobu následně potvrzuje USER-REVIEW-31. Údaje pro ověření identity a rozsah sdělovaných údajů zůstávají samostatnými otázkami. USER-REVIEW-31: Možnost jednat za jinou osobu platí také pro přesun a zrušení návštěvy. Pracovat s kartou cílového pacienta a jeho konkrétní rezervací, nikoli automaticky s kartou volajícího. Postup ověření identity a identifikace rezervace zůstává samostatným bodem. USER-REVIEW-32: Standardem podle uživatele je jméno a datum narození pacienta. Dřívější běžný požadavek na poslední čtyři číslice rodného čísla byl dle uživatele v posledních commitech odstraněn na výslovný požadavek klienta; toto tvrzení o historii nebylo při této revizi nezávisle ověřeno. Rodné číslo je pouze krajní možnost, nikoli rutinní či povinný další krok. Přesné podmínky a rozsah této krajní možnosti zbývají k upřesnění. Pro zastupování jde o údaje cílového pacienta. USER-REVIEW-33: Při nedohledání karty agent výslovně sdělí, že ji nenašel pod použitým jménem, příjmením a datem narození, a tyto údaje zopakuje k ověření. Pokud je volající opraví, hledání zopakuje s opravenými údaji; pokud na původních údajích trvá, nabídne předání personálu bez dalšího komplikování a bez automatického dotazu na RČ. Tím je pro tento běžný neúspěšný lookup určena přednost předání před dříve neurčeným last-resort RČ. USER-REVIEW-34: Pokud je více karet se shodným jménem a datem narození, nabídnout volajícímu volbu: zkusit dohledání podle rodného čísla, nebo rovnou předat personálu. RČ je v této větvi dobrovolná krajní možnost, nikoli povinný krok; neobnovuje se rutinní last4. Potvrzení se vztahuje k nejednoznačné shodě, nemění postup při nulové shodě z USER-REVIEW-33. USER-REVIEW-35 určuje pro tento dobrovolný krajní lookup celé rodné číslo, nikoli pouze last4. USER-REVIEW-35: Pokud si volající při více shodných kartách zvolí dohledání podle RČ, agent požádá o celé rodné číslo. Standardní jméno, příjmení a datum narození ani možnost přímého předání personálu se nemění.

**DB reprezentace:** KAR.IDPAC/JMENO/PRIJMENI/DATNAR; KARKONTAKT; patient_verified request.

**Implementace:** scripts/patient_lookup.py::lookup_patient; scripts/patient_lookup.py::_build_patient_query; scripts/appointment_write.py::_require_patient_verified

**Důkazy:** CODE; CONTRACT; TEST-PATIENT; USER-REVIEW-29; USER-REVIEW-30; USER-REVIEW-31; USER-REVIEW-32; USER-REVIEW-33; USER-REVIEW-34; USER-REVIEW-35

**Jistota:** CONFLICT

**Dopad chyby:** Zápis či zpřístupnění rezervace nesprávnému pacientovi.

**Reprodukovatelný případ:** Syntetický unique phone→verified; limit1 u více možných výsledků musí být zvlášť přezkoumán; žádná skutečná pacientská data. Návrhové případy: chybějící IDPAC nebo nenalezená karta -> žádné vytvoření karty ani termínu, předání personálu; nevymýšlet náhradní IDPAC ani nepoužít kartu jiného pacienta. Zatím návrh, test zde neproveden. Návrhový případ: rodič nebo partner volá ze svého čísla a objednává jiného pacienta s existující kartou; dohledat cílového pacienta a nepoužít automaticky kartu majitele čísla. Nejednoznačná identita neznamená oprávnění vybrat libovolnou kartu. Test zatím neproveden. Návrhový případ: volající přesouvá nebo ruší návštěvu jiné osoby; vybrat správného pacienta i jeho rezervaci a nezasáhnout návštěvu volajícího. Samotné odlišné telefonní číslo není důvodem zákaz zastoupení vynutit. Test zde neproveden. Návrhové případy: jednoznačná shoda jména a data narození nevyžaduje rutinně last4 ani celé rodné číslo; při nulové či nejednoznačné shodě nevybrat libovolnou kartu a neoznačit ji automaticky za ověřenou. Přesný fallback čeká na upřesnění. Test zde neproveden. USER-REVIEW-33, návrhové případy: nulová shoda -> zopakovat jen údaje dodané volajícím; oprava data či jména -> opakovat lookup s opravou; potvrzení původních údajů -> nabídnout předání personálu, nevyžadovat RČ ani cyklit stejné hledání. Neříkat, že pacient kartu určitě nemá. Test zde neproveden. USER-REVIEW-34, návrhové případy: více karet se shodným jménem a datem narození -> nabídnout lookup podle RČ nebo personál; zvolí-li volající personál, RČ nevyžadovat. Bez jednoznačného výsledku nevybrat libovolnou kartu. Test zde neproveden. USER-REVIEW-35, návrhový případ: při více shodných kartách a zvolené možnosti RČ použít celé RČ pro dohledání; neomezit jej na last4. V běžném jednoznačném dohledání RČ nevyžadovat. Pouze návrh, test neproveden.

**Otázka k potvrzení:** Standard jméno + příjmení + datum narození a fallback při nenalezené kartě potvrzen USER-REVIEW-32/33: zopakovat použité údaje, při opravě nové hledání, při potvrzení původních údajů nabídnout personál. Automatický přechod na RČ v této větvi není požadován; případné jiné použití RČ jako krajní možnosti není specifikováno. USER-REVIEW-34 řeší více shodných karet volbou dobrovolného dohledání podle RČ nebo přímého předání personálu; USER-REVIEW-35 stanoví celé RČ; postup při neúspěchu tohoto krajního dohledání zbývá k upřesnění; technicky porovnat lookup/verified a historii odstranění povinného last4 s potvrzenými pravidly. Samotný telefon ani IDPAC nenahrazují potvrzené údaje.


## MAP-33 — patient_cross_database

**Doména:** patient_cross_database

**Business význam / současná interpretace:** Není nalezena implementovaná ověřená vazba MAIN.KAR↔LASER.KAR. Shoda ID ani jména nesmí být interpretována jako vazba.

**DB reprezentace:** Dvě samostatné KAR.IDPAC; žádný ověřený crosswalk v prohlédnuté API cestě.

**Implementace:** scripts/db.py::connect_to_db; scripts/appointment_write.py::_create_appointments; scripts/approval_proposals.py::patient_fingerprint (local-only)

**Důkazy:** CODE; DOC-LASER; DESIGN

**Jistota:** UNCLEAR

**Dopad chyby:** Zápis scanu jinému pacientovi.

**Reprodukovatelný případ:** Syntetický MAIN.IDPAC100 a LASER.IDPAC100 s různými osobami→budoucí bezpečné odmítnutí, nikdy slepé kopírování.

**Otázka k potvrzení:** Existuje společný stabilní klíč, integrační tabulka či personální ověření? Kdo zakládá chybějící kartu?


## MAP-34 — confirmation

**Doména:** confirmation

**Business význam / současná interpretace:** HTTP200 není potvrzení rezervace. V produkci writes_not_enabled. Budoucí pending návrh také není rezervace. USER-REVIEW-36: Pokud má pacient více budoucích rezervací, agent před přesunem nebo zrušením nejprve zjistí, které návštěvy se požadavek týká, a před změnou nechá konkrétní návštěvu výslovně potvrdit volajícím. Nesmí automaticky vybrat první či nejbližší rezervaci. U běžné dermatoskopie nadále platí změna skenu a navazující prohlídky jako celku. USER-REVIEW-38: Obecně jakákoli technická chyba nesmí být důvodem, aby agent prostě ukončil hovor. Má volajícího informovat o technických potížích, chybu a původní požadavek zaznamenat, notifikovat admina a přesměrovat na personál. Při neověřeném výsledku objednání/přesunu/zrušení nepotvrdit úspěch ani neodvozovat jisté selhání; personálu předat i informaci o nejistém výsledku k ověření. Pokud selže samotné přesměrování, platí fallback USER-REVIEW-20: zachovat požadavek pro následný kontakt personálu a upozornění adminovi. USER-REVIEW-39: Před každým novým objednáním agent stručně shrne službu, lékaře, datum a požadovaný čas příchodu a vyžádá si výslovné potvrzení volajícího. Shrnutí může být kompaktní, ale nesmí vynechat uvedené údaje. U dermatoskopie příchod zahrnuje sken před prohlídkou; technický čas lékaře nesmí nahradit správný čas příchodu. Potvrzení volajícího není důkaz úspěšného zápisu ani náhrada případného samostatného schvalovacího workflow.

**DB reprezentace:** API ok/status a transaction commit; local-only proposal.state není produkční workflow.

**Implementace:** scripts/api_server.py::book_appointment; scripts/appointment_write.py::write_appointment; scripts/approval_store.py (local-only)

**Důkazy:** LIVE.api_flags; USER-SCOPE; DESIGN; CODE; USER-REVIEW-36; USER-REVIEW-38; USER-REVIEW-39

**Jistota:** CONFIRMED

**Dopad chyby:** Falešné ujištění pacienta, že je objednán.

**Reprodukovatelný případ:** ok=false/status=writes_not_enabled přiHTTP200→nepotvrzovat; pending_staff_review→pouze přijetí žádosti. USER-REVIEW-36, návrhový případ: pacient má více budoucích návštěv a obecně žádá přesun/zrušení; agent si nechá určit návštěvu a před změnou ji výslovně potvrdit. Bez rozlišení a potvrzení žádnou rezervaci neměnit. Test zde neproveden. USER-REVIEW-38, návrhové případy: technické selhání čtení nebo zápisu -> vysvětlení volajícímu, záznam chyby a požadavku, admin alert a pokus o přesměrování; timeout s neznámým výsledkem zápisu -> bez tvrzení úspěchu a bez slepého opakování mutace, předat nejistý stav personálu; selhání transferu -> zachovat callback požadavek podle USER-REVIEW-20. Testy zde neprovedeny. USER-REVIEW-39, návrhové případy: před novým objednáním zazní stručné shrnutí služby/lékaře/data/příchodu a následuje výslovné potvrzení; při opravě některého údaje znovu potvrdit opravenou nabídku před objednáním; bez potvrzení nevytvářet rezervaci. Test zde neproveden.

**Otázka k potvrzení:** Jakým kanálem a kým se pacient dozví finální výsledek?


## MAP-35 — staff_intervention

**Doména:** staff_intervention

**Business význam / současná interpretace:** Nejasná identita, neznámá služba/lékař, konflikt, chybějící mapping a nejistý zápis vyžadují vyjasnění/personál; souhrn sám nezaručuje doručení ani transfer. Uživatel navrhl akutní požadavek označit emergency tagem a nabídnout okamžité přesměrování na personál s klidnou reakcí, místo pokračování běžného objednávacího rozhovoru. Nejde o potvrzení technické dostupnosti přesměrování ani oprávnění rezervovat pohotovost. USER-REVIEW-19: jasný požadavek mimo vymezený agent scope má vést k nabídce předání původního požadavku personálu. Agent jej nesmí nahrazovat nesouvisející nabídkou podporované služby, například kožního vyšetření. Uživatel popsal nežádoucí současnou odpověď s takovou náhradní nabídkou; původní produkční hovor nebyl v této revizi nezávisle načten. USER-REVIEW-20: Obsazeno/nezvednuto je provozní nedostupnost; personál má provést callback podle zmeškaného hovoru. Požadovaná hláška: Omlouváme se, ale personál je momentálně zaneprázdněn. Zavolá Vám, jakmile to bude možné. Technická chyba přepojení musí mít záznam pokusu a původního požadavku pro personál i upozornění adminovi; pokud hovor pokračuje, omluva a informace o následném kontaktu. Uživatelský cíl je neztratit požadavek, nikoli tvrdit neověřené doručení. USER-REVIEW-38: Obecně jakákoli technická chyba nesmí být důvodem, aby agent prostě ukončil hovor. Má volajícího informovat o technických potížích, chybu a původní požadavek zaznamenat, notifikovat admina a přesměrovat na personál. Při neověřeném výsledku objednání/přesunu/zrušení nepotvrdit úspěch ani neodvozovat jisté selhání; personálu předat i informaci o nejistém výsledku k ověření. Pokud selže samotné přesměrování, platí fallback USER-REVIEW-20: zachovat požadavek pro následný kontakt personálu a upozornění adminovi.

**DB reprezentace:** handoff_summary vrací strukturu; standalone potvrzení doručení/telefonního přenosu v tomto helperu není.

**Implementace:** scripts/handoff_summary.py::build_handoff_summary; scripts/business_rules.py::agent_capabilities; docs/staff_approval_recovery.md

**Důkazy:** CODE; CONTRACT; USER-SCOPE; DESIGN; USER-REVIEW-18; USER-REVIEW-19; USER-REVIEW-20; https://elevenlabs.io/docs/eleven-agents/customization/tools/system-tools/transfer-to-number; https://www.twilio.com/docs/voice/twiml/dial; USER-REVIEW-38

**Jistota:** PROBABLE

**Dopad chyby:** Požadavek je označen za předaný, ale personál jej nedostane.

**Reprodukovatelný případ:** Vygenerovat callback summary: ověřit pouze strukturu, zvlášť ověřit skutečné doručení v pozdější fázi. Požadavek na plazmu/laser/zákrok mimo scope: nabídnout personál a zachovat původní intent v souhrnu, nenabízet kožní jako náhradu. Návrh testu pro pozdější etapu: nejasný požadavek krátce vyjasnit, neslibovat předání či callback jako hotový bez skutečného výsledku. Konverzační testy zde nebyly spuštěny. Budoucí řízené testy: vyzvednuto, obsazeno, nezvednuto, technické selhání; zjistit návrat do konverzace či možnost hlášky, zobrazení původního caller ID a zmeškaného hovoru na cílovém telefonu; při technické chybě ověřit trvalý záznam požadavku a admin alert. Tyto telefonní testy zatím neprovedeny. USER-REVIEW-38, návrhové případy: technické selhání čtení nebo zápisu -> vysvětlení volajícímu, záznam chyby a požadavku, admin alert a pokus o přesměrování; timeout s neznámým výsledkem zápisu -> bez tvrzení úspěchu a bez slepého opakování mutace, předat nejistý stav personálu; selhání transferu -> zachovat callback požadavek podle USER-REVIEW-20. Testy zde neprovedeny.

**Otázka k potvrzení:** Kdo řeší které případy, SLA, nedostupný personál, chybu doručení a neúspěšný transfer? Ověřit skutečný transfer_type a integraci produkčního agenta; dokumentace nezaručuje návrat agenta po busy/no-answer ani zmeškaný hovor na cílovém přístroji. Callback podle zmeškaného hovoru závisí na dostupném správném čísle. Zvolit doručovací cestu a potvrzení uložení požadavku při technickém selhání. Aktuální prompt dodá uživatel na konci review; zachovat již provedené úpravy ElevenLabs architecta.


## MAP-36 — october7_evidence

**Doména:** october7_evidence

**Business význam / současná interpretace:** Ukázka7.10. pro MAIN12 15:00/15:10 koliduje scanem s LASER5 14:45–15:00;15:50 koliduje MAIN15:55–16:20 i LASER15:45–16:00.

**DB reprezentace:** Read-only day projection obou OBJOBJ_SEL; bez IDPAC/INFO.

**Implementace:** scripts/laser_calendar.py::interval_is_available; scripts/availability_engine.py::compute_slots

**Důkazy:** LIVE.databases.*.day_2026_10_07; USER-OCT7; TEST-LASER; TEST-SAFETY

**Jistota:** CONFIRMED

**Dopad chyby:** Konkrétní falešně dostupné nabídky.

**Reprodukovatelný případ:** Porovnat intervaly v uloženém snapshotu; první dva lékařské intervaly mají volný MAIN, ale obsazený scan.

**Otázka k potvrzení:** Personál musí potvrdit UI pro stejný čas snapshotu; snapshot nedokazuje historický stav v okamžiku původního hovoru.


## MAP-37 — source_precedence

**Doména:** source_precedence

**Business význam / současná interpretace:** Efektivní pravidla jsou example+server-local override, dále overlay do agent_context. Lokální prototyp není produkce; verze v JSON sama nezachycuje všechny overrides. Uživatel schválil prioritu DB pro aktuální jména a kalendářové identity před historickými seznamy. Toto není univerzální schválení business pravidel odvozených z DB ani ignorování známých výjimek a konfigurace.

**DB reprezentace:** business_rules.local.json hluboký merge; agent_context.local.json; API_CONFIG načtené při startu.

**Implementace:** scripts/business_rules.py::load_business_rules; scripts/availability_search.py::load_search_config; scripts/api_server.py

**Důkazy:** LIVE.effective_rules; LIVE.files; CODE; USER-REVIEW-11

**Jistota:** CONFIRMED

**Dopad chyby:** Audit výchozího configu je zaměněn za skutečný produkční stav.

**Reprodukovatelný případ:** Porovnat default skin booking=true vs effective=false; AST/hash serveru vs lokální soubory.

**Otázka k potvrzení:** Kdo schvaluje změny pravidel a jak se verzují nezávisle na deployi kódu?


## MAP-38 — offer_binding

**Doména:** offer_binding

**Business význam / současná interpretace:** Produkční compact nabídka nese jméno a časy, nikoli autoritativní immutable offer reference. Lokální proof-token prototyp není aktivován. USER-REVIEW-37: Pokud vybraný termín mezitím obsadí někdo jiný, agent vyhledá nové vyhovující možnosti a nechá pacienta znovu vybrat; nenahradí termín automaticky. Při přesunu musí původní rezervace zůstat zachovaná, dokud se přesun úspěšně nedokončí. Jde o požadovaný výsledek, nikoli důkaz současné transakční bezpečnosti či oprávnění implementovat dočasné blokace.

**DB reprezentace:** options/options_json; compact vynechává doctor_id,idprac,end_time; prod writer znovu sestavuje požadavek.

**Implementace:** scripts/availability_search.py::compact_options; scripts/appointment_write.py::_find_exact_bookable_option; scripts/approval_proposals.py (local-only)

**Důkazy:** CODE; LIVE.files; USER-OCT1; DESIGN; USER-REVIEW-37

**Jistota:** CONFLICT

**Dopad chyby:** Agent spojí hodnoty z různých nabídek; dnes zabráněno mutation globálním zákazem, ne produkční vazbou nabídky.

**Reprodukovatelný případ:** Použít dodaný příklad Šlosárová13:20 vs Selecká15:30 a odlišit textovou chybu od stavu API. USER-REVIEW-37, návrhový případ: termín po nabídce obsadí jiný uživatel; agent znovu vyhledá možnosti a vyžádá nový výběr pacienta, bez automatické náhrady. Při neúspěšném přesunu zůstává původní rezervace včetně souvisejících částí zachovaná. Test zde neproveden.

**Otázka k potvrzení:** Budoucí Stage4: potvrdit úplný objekt nabídky; zatím neimplementovat.


## MAP-39 — manual_concurrency_and_holds

**Doména:** manual_concurrency_and_holds

**Business význam / současná interpretace:** Dočasné holdy nejsou v produkci. Read-then-write není důkaz exkluzivity vůči současné práci personálu v Medicusu. USER-REVIEW-37: Pokud vybraný termín mezitím obsadí někdo jiný, agent vyhledá nové vyhovující možnosti a nechá pacienta znovu vybrat; nenahradí termín automaticky. Při přesunu musí původní rezervace zůstat zachovaná, dokud se přesun úspěšně nedokončí. Jde o požadovaný výsledek, nikoli důkaz současné transakční bezpečnosti či oprávnění implementovat dočasné blokace.

**DB reprezentace:** Dva Firebird DB; žádný aktivovaný společný rezervační zámek; local proposal store není externí Medicus rezervace.

**Implementace:** scripts/appointment_write.py::_find_conflicts; docs/pending_slot_holds_proposal.md

**Důkazy:** CODE; LIVE.api_flags; DESIGN; USER-SCOPE; USER-REVIEW-37

**Jistota:** UNCLEAR

**Dopad chyby:** Dvě rezervace téhož zdroje nebo nevyřešený částečný commit.

**Reprodukovatelný případ:** Budoucí test: manuální rezervace mezi načtením a schválením; očekávání musí zahrnout podporovaný společný mechanismus. USER-REVIEW-37, návrhový případ: termín po nabídce obsadí jiný uživatel; agent znovu vyhledá možnosti a vyžádá nový výběr pacienta, bez automatické náhrady. Při neúspěšném přesunu zůstává původní rezervace včetně souvisejících částí zachovaná. Test zde neproveden.

**Otázka k potvrzení:** Podporuje Medicus provizorní rezervaci/zámek? Jaký holdTTL a staff SLA?


## MAP-40 — invalid_intervals

**Doména:** invalid_intervals

**Business význam / současná interpretace:** LASER odmítá neplatný konec rezervace; main engine nevaliduje end<=start explicitně. Politika celodenních/nulových blokací není doložená.

**DB reprezentace:** OBJOBJ.CAS/CASDO; OBSODLIS.DOBA může být0; chybějící či obrácené časy.

**Implementace:** scripts/availability_engine.py::compute_slots; scripts/laser_calendar.py::interval_is_available

**Důkazy:** CODE; TEST-LASER

**Jistota:** UNCLEAR

**Dopad chyby:** Nulová či speciální blokace může být ignorována; různé chování obou DB.

**Reprodukovatelný případ:** Syntetická booking09:00–09:00: main ji neblokuje, LASER vyhodí ScanCalendarUnavailable.

**Otázka k potvrzení:** Co znamenají nula/NULL/přes-půlnoc/celodenní záznamy v Medicus UI a jak je bezpečně zpracovat?
