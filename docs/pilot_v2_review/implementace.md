# Průběh schválené implementace

## 2. 10. 2026: Operator handoff1 nasazen

Na server aktivováno `pilot-2026-10-02.handoff1` po ověření SHA256 archivů,
14 backend testech, 5 dashboard proxy testech a produkčním buildu.
GitHub branch `release/handoff1` v obou repozitářích; backend fbce634,
dashboard 65867dd, stromy přesně odpovídají lokálním f7ef629 / 3ef1187.
Autorizovaný smoke ověřil 10 hovorů a detail: staff_requests a hypercare
kontrakt zachovány. API, dashboard i worker jsou Running; health task obnoven.
Veřejný smoke s browser User-Agent: health 200, login 200, anonymní API 401.
Výchozí Python User-Agent blokuje Cloudflare 403 před aplikací.
Rollback připraven na hypercare1. Žádná DB migrace, Firebird změna ani restart
Medicusu/počítače. Medicus doručovací worker není tímto nasazením zapojen;
živý handoff, SMS a hlasový test zůstávají následujícími kroky.

## 2. 10. 2026: samostatné předávání personálu

Přidán `enable_durable_handoff` (default false), nezávislý na povolení
schvalování a zápisů rezervací. Společný helper používá endpoint, worker
i recovery CLI; worker/recovery odmítají neexistující store. Původní režim
staff approval zachovává trvalé předávání. Dokumentace popisuje pořadí
nasazení a rozdíl mezi uložením, doručením a převzetím personálem.

Ověření: 10 testů `test_handoff*.py`, 8 approval API, 4 durable handoff
a 4 autentizační testy prošly (26 celkem), `git diff --check` bez chyb.
Nové testy prokazují uložení a doručení přes simulovaný transport, opakování
bez duplicity, vypnuté staff endpointy a všechny tři zápisové operace bez
SQL/commitu při vypnutých zápisech. Nejde o živé síťové ani hlasové ověření.
V této části žádné produkční nasazení ani změny Firebirdu.
Další krok: připravit izolované nasazení Operator inboxu a servisní instalaci
workeru, poté propojený živý test před zapojením ElevenLabs.

Uživatel schválil konsolidovaný návrh výslovným „Schvaluji“.
Neznámé databázové mapování tím není potvrzeno. Produkce zatím nezměněna.

## První lokální část: dostupnost

Deterministická sada obsahuje 29 scénářů a kontrolu jejich kontraktu.
Vstupy obsahují rozvrhy, objednávky, očekávané nabídky a odůvodnění.
Před opravou selhalo sedm scénářů: arrival_preference,
conflicting_doctor_identity, global_doctor_order, invalid_booking_reversed,
invalid_booking_zero, past_bucket, weekend_not_overrideable.

Opraveno:
- časové preference a minulost zohledňují skutečný příchod včetně skenu;
- nabídky se řadí napříč lékaři před omezením počtu;
- rozporná kombinace jména a ID lékaře se neakceptuje;
- neplatný interval objednávky zastaví výpočet místo nabídnutí volného místa;
- veřejné hledání nepovolí víkendy ani při požadavku na jejich zahrnutí;
- pevné i pohyblivé české svátky se blokují nezávisle na rozvrhu;
- interní přesné ověření technického času má samostatný selektor,
  aby nebylo zaměňováno s pacientovým filtrem příchodu.

Svátky: [zákon 245/2000 Sb.](https://ppropo.mpsv.cz/zakon_245_2000),
referenční kalendář [ČNB](https://www.cnb.cz/cs/verejnost/servis-pro-media/harmonogramy-a-dalsi-informace/svatky-v-ceske-republice/index.html).
Roční seznam se počítá lokálně, bez síťové závislosti při hledání.

Ověření: `../operator_backend/.venv/Scripts/python.exe -m unittest discover -s tests -q`
— 98 testů, OK. Dvě starší zkoušky bucketů nyní vybírají technický čas
výslovným selektorem; zachovávají původní očekávaný příchod a čas skenu.
Výstraha knihovny Starlette o budoucí změně HTTP klienta neovlivnila výsledek.

## Hranice důkazů a další práce

Jde o lokální testy, nikoli ověření živého Medicusu. Rozvinuté opakování
a výjimky ve fixtures nedokládají správnost skutečných Firebird procedur.
Říjnový konflikt v LASER je pokryt, nikoli skutečná vazba identit MAIN/LASER.

Zbývá zejména hodinový předstih s důvěryhodným začátkem hovoru, šest
kalendářních měsíců, intervaly jednotlivých bloků, rozvrhové výjimky,
ověření identit a aktivit, neměnné nabídky, schvalování a ochrany zápisů,
Operator, prompt a tool kontrakty, notifikace, klientský test a nasazení.
Přímé veřejné zápisy nejsou touto změnou zapnuty. Celý pilot není dokončen.

## Doplnění rozsahu: empirické ověření databázového mapování

Na výslovný požadavek uživatele patří do stejného pilotního cíle porovnání
skutečných minulých, současných a budoucích termínů napříč MAIN a LASER.
Nevzniká samostatný úkol ani druhá implementace.

Výběr bude kombinovat náhodné dny a cílené pokrytí všech relevantních typů
termínů, lékařů, intervalů, bucketů, opakování a rozvrhových výjimek.
Incident 7. 10. 2026 bude pevný regresní případ. Prázdný den nenahrazuje
důkaz pro vzácný typ termínu; chybějící příklad zůstane explicitní mezerou.

Pro každý vzorek porovnat tentýž stav: kalendář ve frontendu Medicus,
surové řádky a vazby v příslušné databázi, výsledek zobrazovacích procedur
a výsledek našeho API. Zaznamenat čas odečtu, zdrojovou DB, technické ID,
typ, lékaře, pracoviště, začátek/konec, stav a vazby; v exportovaných
regresních příkladech anonymizovat identifikátory a vynechat osobní údaje.
Shoda samotného API s procedurou, kterou API používá, není nezávislý důkaz.

Historický řádek dokládá uložený stav, nikoli automaticky jeho původ,
všechny vedlejší zápisy či správnou posloupnost vytvoření/přesunu/zrušení.
Pro tyto operace doplnit řízený test přes skutečný frontend Medicus na
určené testovací kartě a porovnat databázový stav před a po. Pokud není
frontend dostupný, zaznamenat tuto hranici důkazů a připravit konkrétní
ověřovací kroky pro personál; neodvozovat zápisový kontrakt pouze z názvů.

Výstup: tabulka potvrzených a nepotvrzených mapování s odkazy na důkazy,
seznam rozporů a anonymizované regresní fixtures. Zvlášť ověřit rozporný
význam aktivity 5, propojení skenu s vyšetřením a identity mezi databázemi.
Nasazení příslušných zápisových cest vyžaduje vyřešení těchto rozporů.

## Vyhledávací horizont

Lokální hledání nově používá šest kalendářních měsíců od požadovaného
počátku, včetně koncového dne, místo pevně daných 180 dní. Respektuje kratší
explicitní datum konce a úzké okno bez automatického rozšíření. Kontrola
po roce není odmítnuta jen proto, že její počátek leží daleko od dneška.
Konec měsíce se přizpůsobí délce cílového měsíce, včetně přestupného února.
Převrácené intervaly jsou odmítnuty, extrémní počty dní omezeny před
výpočtem data. Response uvádí skutečnou délku vymezeného intervalu.
Původní implicitní rozšíření bez preference lékaře zatím zachováno;
úzká kontrolní okna vyžadují explicitní date_to nebo vypnutí rozšíření.

Sedm nových testů, celá sada 109 testů OK. Změna zatím není nasazena.

## Veřejná cesta k API

Neautentizované GET /health a /openapi.json z lokálního prostředí rovněž
vracejí HTTP 403, Server cloudflare a text `error code: 1010`.
Podle [oficiální dokumentace](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)
jde o odmítnutí podle podpisu klienta. To odpovídá infrastrukturnímu
odmítnutí diagnostického klienta; není to důkaz špatného API tokenu ani
globálního výpadku. Nastavení ochrany nebylo měněno. Skutečná veřejná
tool cesta z ElevenLabs stále vyžaduje ověření při řízeném testu.

## Délka jednotlivých políček rozvrhu

Engine nově zachovává mapu délky každého skutečného políčka. Dosavadní
nejkratší interval kontextu zůstává jen jako kompatibilní souhrnná hodnota;
nové nabídky skin, dermatoscope_first a jednoduchých služeb používají
délku konkrétního začátku. Kontrola delší pevné procedury prochází skutečně
navazující volná políčka, takže zvládne kombinaci 10 a 15 minut, ale nikdy
nepřeskočí mezeru. Překryv rezervace s kteroukoli částí políčka je blokuje.

Čtyři nové regresní testy používají skutečný výpočet denní dostupnosti
nad dodanými rozvrhovými bloky a navazující konstrukci nabídek. Ověřují
všechny tři konstrukce nabídek, smíšenou souvislou kapacitu, mezeru a kolizi
v posledních pěti minutách. Celá sada 113 testů OK. Kombinace bloků jsou
syntetické regresní příklady, nikoli tvrzení o konkrétním pacientovi.
Tato část zatím nebyla nasazena ani ověřena zápisem přes frontend.

## Neměnnost nabídky ve schvalovacím prototypu

Serverový snapshot nabídky nyní obsahuje technický čas, sdělovaný čas,
nejčasnější nutný příchod, délku políčka/prohlídky, instrukci k příchodu,
nezávislou kopii skenu a hash aktuálních business rules. Při novém ověření
se porovnává celý snapshot. Změna příchodu nebo pravidel proto vyžaduje
novou nabídku, i když lékař a technický začátek zůstali stejní.

Při odeslání návrhu se odmítají také rozporné zopakované časy příchodu,
konce a skenu; personální souhrn tyto časy přebírá ze serverové nabídky.
Čtyři nové testy: změna příchodu, změna pravidel, nezávislost vnořených dat
a podvržený sdělovaný čas. Celá sada 117 testů OK.

Jde o místní schvalovací prototyp, nikoli hotový schvalovací tok. Hash
pravidel zatím nepokrývá všechny zdrojové konfigurace (například mapování
LASER); neměnnost tokenu sama neprokazuje, co agent skutečně vyslovil.
Zbývá provázání s výsledným promptem, kontrakty toolů a personálním UI,
dále identity, předstih, expirace a kontroly před skutečným zápisem.

## Ověření identity a historie termínů

Lookup a vydávání pacientského tokenu používají společné pravidlo:
jediná nezkrácená shoda celého jména, příjmení a data narození. Diakritika,
velikost písmen a nadbytečné mezery se normalizují; částečné a fuzzy shody
zůstávají kandidáty bez ověření. Samotný telefon či IDPAC identitu nepotvrdí.
Alternativou je jednoznačný výsledek přesného SQL hledání podle celého RČ
(9 nebo 10 číslic). Povolení této alternativy pouze po nabídnuté volbě
volajícího zatím musí navázat na prompt a stav dialogu; samotný lookup
historii souhlasu neprokazuje. Last4 není ověřovací metoda.

Neověřená karta neposkytne budoucí ani minulé termíny a nevydá pacientský
token pro návrh. Zadání limit=1 už nemůže skrýt druhou shodu; SQL načte
alespoň dva kandidáty. Při dosažení limitu fallback hledání se výsledek
označí search_truncated a nelze z něj dokázat jednoznačnou identitu.

Upraveny staré testy, které výslovně očekávaly dnes odmítnuté ověření pouze
telefonem, příjmením nebo fuzzy shodou. Nové testy ověřují částečná jména,
nezpřístupnění historie, limit=1, uříznutý fallback a celé RČ versus last4.
Celkem 121 testů OK. Změna je lokální; v produkci zatím nasazena není.

## Hodinový předstih a stabilní serverový čas hovoru

Schvalovací režim ukládá první autentizované zpracování s X-Conversation-Id
do SQLite pod dvojicí tenant/hovor. INSERT OR IGNORE zachová první čas při
opakování i souběhu; záznam přežije restart. Hledání dostává čas samostatným
serverovým parametrem, nikoli z JSON agentova požadavku. Nejčasnější příchod
včetně skenu/bucketu musí být alespoň hodinu po tomto čase a zároveň stále
v budoucnosti. Přesná hranice hodiny je přípustná.

Nabídkový token uchovává tento začátek pro pozdější kontrolu návrhu,
takže ověření nevytváří nový hodinový předstih. Diagnostika odpovědi uvádí
minimum_arrival_at a call_time_source. Jde o fallback first_server_processing,
nikoli ověřený čas spojení od poskytovatele telefonie. Před prvním požadavkem
s identifikátorem hovoru čas neznáme. Bez schvalovacího režimu se použije
konzervativní aktuální požadavek; trvalý kontext je součástí konfigurace v2.

Čtyři nové testy potvrzují hranici hodiny, stabilitu při dalším hledání,
ignorování podvrženého data v JSON a trvalost/izolaci kontextu. Starší test
filtrování minulosti dostal výslovný začátek již probíhajícího hovoru.
Celá sada 125 testů OK před doplněním diagnostických polí; nasazení neproběhlo.
Ještě zbývá retenční úklid kontextů a skutečný řízený test ElevenLabs.

## Propojení schvalovacích žádostí do Operatoru

Backend Operatoru má nové tenant-scoped endpointy pro seznam, detail
a zamítnutí žádosti. Volají serverový Medicus endpoint s odděleným staff
tokenem; konfigurace je pevně svázaná s jedním tenantem. Žádný přístup
jiného tenanta se na Medicus nepřepošle. Výstupní modely odstraňují interní
payload, pacientská ID a tokeny i z vnořených objektů. Timeout nevyvolá
automatické opakování rozhodnutí; odpověď vyzve k obnovení stavu.

Dashboard má odpovídající serverové API cesty. Přístup vychází ze Supabase
session a členství, tenant z konfigurace a actor_user_id z přihlášeného
uživatele. Prohlížeč může poslat pouze verzi žádosti pro zamítnutí.
Mezi dashboardem a backendem zůstává stávající důvěryhodný interní token;
backend sám neověřuje Supabase JWT koncového uživatele.

Ověření: 5 cílených backendových testů OK; dashboard npm run lint a
npm run build OK (včetně TypeScriptu a všech nových routes). UI karet,
skutečné schválení/zápis, živý test oprávnění a nasazení ještě zbývají.
Konfigurační hodnoty pro review bridge zůstávají v příkladu prázdné;
produkční konfigurace nebyla změněna.

## První UI žádostí

Dashboard obsahuje sekci Žádosti, dostupnou i přes mobilní výběr sekce.
Karty oddělují původní a požadovaný termín, příchod, sken a prohlídku.
Otevřený filtr zahrnuje i konflikty, chyby a neznámé stavy; uzavřené lze
zobrazit přepínačem. Omezení seznamu na 100 nejnovějších položek je viditelné.
Zamítnutí má explicitní potvrzení, posílá verzi karty a při nejistém výsledku
vyžaduje obnovení seznamu před dalším pokusem. Schválení je výslovně
označeno jako nedostupné, dokud není hotová zápisová cesta.

Ověření: cílený ESLint a produkční build prošly. Následná drobná úprava
skryla neaplikovatelný filtr období u žádostí a prošla tsc --noEmit.
Vizuální a interakční ověření se skutečnými kartami, propojení detailu
hovoru, stránkování celé historie a schválení zůstávají nedokončené.
UI není nasazené ani prohlášené za připravené pro finální klientský test.

## Kandidát promptu a hlasový kontrakt

Vznikl samostatný `elevenlabs_prompt_v2_candidate_cs.txt`, který zachovává
klientem dodané údaje o pracovišti a okamžité předání, ale nahrazuje přímé
zápisy žádostmi ke schválení. Sjednocuje identitu, kontroly podle doporučení,
nedělitelné nabídky, out-of-scope handoff a nejasné výsledky. Produkční
prompt ani lokální current soubor nebyl nahrazen.

Capabilities nyní v režimu staff_review vrací review_services, ne seznam
přímo rezervovatelných služeb; API předává skutečný nakonfigurovaný režim.
Compact nabídka doplnila arrival_time a zachovává offer_token. Dva nové
kontraktní testy a celá sada 127 testů OK. Podmínky rollout a deset scénářů
jsou v elevenlabs_v2_rollout.md. Žádná změna zatím nebyla publikována
v ElevenLabs; prompt čeká na dokončení a ověření provázaných funkcí.

## Trvalé uložení handoff požadavků

Režim v2 ukládá handoff do stejného chráněného on-host store před odpovědí
stored=true. Unikátní klíč tenant/hovor/request_id a digest obsahu zabraňují
duplicitě při opakování; rozdílný obsah pod stejným klíčem se odmítne.
created_at nevstupuje do porovnání obsahu, aby serverový čas opakování
nezpůsobil falešný konflikt. Kontext má limit 32 kB.

Odpověď rozlišuje uložený požadavek od delivery_status=pending. Legacy
režim výslovně vrací stored=false, not_queued. Selhání úložiště nevrací
úspěch a nevystavuje text interní výjimky. Technická telemetrie handoffu
obsahuje pouze režim a výsledek uložení, nikoli volný text či osobní údaje.

Šest nových testů: trvalost a opakování, kolize obsahu, tenant/hovor,
povinné request_id, endpoint uložení a ochrana telemetrie, chyba úložiště.
Celá sada 133 testů OK. Prompt a rollout kontrakt doplněny o request_id.

Chybí doručovací worker, personální inbox tohoto záznamu, opakování
doručování a admin upozornění na trvalé selhání. Samotná nová tabulka
není hotové předání ani důkaz SMS/e-mailového doručení. Nasazení neproběhlo.

## Doručování do Operatoru a personální kontext

Doplněn handoff_delivery.py: samostatný worker čte trvalou frontu, rezervuje
položku na 60 sekund a posílá staff.handoff.requested se stabilním event_id.
Úspěch označí pouze po accepted=true od Operatoru; timeout/neplatná odpověď
plánují opakování s odstupem, po deseti dokončených neúspěšných pokusech
zůstane stav failed. Po pádu workeru zanikne lease, položka se neztratí.
Zastaralý worker nesmí přepsat výsledek novějšího lease. Síťové přesměrování
není sledováno, aby se přihlašovací údaje nepřenesly na jinou adresu.

Operator ukládá požadavek do existující tenant-scoped tabulky událostí,
označí hovor k vyřízení a zobrazí shrnutí v detailu. Nečeká na post-call.
Opakované event_id se nezpracuje znovu a neotevře už vyřízený požadavek;
změněný obsah pod stejným ID se odmítá. Telefon je uložen do oprávněného
staff pole hovoru, ne do technického event payloadu. Worker odstraňuje
automaticky vložený telefon/IDPAC a číselné RČ ze shrnutí; volný text
personálního shrnutí přesto není úplně automaticky anonymizovatelný.

Kontroly: Medicus 136 testů OK; Operator 7 cílených testů OK (inbox a review
bridge); dashboard tsc --noEmit OK. Zápis stored_in_operator znamená
přijetí backendem, nikoli přečtení personálem ani doručení SMS.
Worker není nasazený/spuštěný v produkci. Zbývá jeho servisní instalace,
živý test celé cesty, admin alert pro failed a SMS poskytovatel.

## Akutní požadavky a ranní příchod

Availability už při emergency=true neodemyká ranní rezervace. Vrací prázdnou
nabídku a explicitní next_action=handoff_to_staff / emergency_requires_staff;
tento pokyn zachová i compact odpověď pro hlasového agenta. Větev nečte
kalendáře. Neznamená to provedené přesměrování: to musí vykonat hlasový agent.
Ranní hranice se kontroluje podle nejčasnějšího nutného příchodu včetně skenu,
nikoli pouze podle času následného vyšetření. Sken 07:45 před prohlídkou
08:00 se proto nevrátí jako běžná nabídka. Regrese ověřuje i povolenou
hranici skenu 08:00. Celá sada: 137 testů OK. Změna pouze lokální,
publikování a živý test předání zůstávají součástí rollout.

## Podklady pro řízený GUI test zápisů

Přidán tools/diagnostics/gui_write_evidence.py a konkrétní postup
v docs/stage1_mapping_audit/gui_write_protocol.md. Capture je read-only;
porovnání zjišťuje změny všech sloupců OBJOBJ, včetně neveřejných polí pomocí
HMAC, bez exportu jejich hodnot. Odmítá rozdílné klíče, dny a schémata.
Pokrývá jen OBJOBJ, nikoli všechny případné vedlejší změny frontendu.

Tři cílené testy prošly (ochrana údajů a detekce změny, přidané/zmizelé
řádky, odmítnutí neporovnatelných snapshotů). Nástroj byl spuštěn přes stdin
na skutečném DB hostu bez instalace či zápisu do Medicusu: 7. 10. 2026,
MAIN 64 řádků, LASER 20 řádků, obě tabulky 48 sloupců. Omezeně přístupný
lokální výstup tmp/gui_evidence_smoke.json; jednorázový klíč nebyl uchován.
Jde o ověření čtečky, nikoli o provedený GUI zápis nebo before/after test.
Pro skutečnou session bude nový společný klíč a čtyři postupné snapshoty.
Uživatel má otevřený dotaz na dostupnost desktopového/webového Medicusu.

## Opakování již přijaté žádosti

submit_proposal nově nejdřív vyhledá původní žádost pomocí tenant/hovor/request_id
 a otisku přesného vstupu. Stejné opakování vrací aktuální stav původní karty
bez opětovného řešení tokenů, identity a dostupnosti. Změna obsahu pod stejným
ID je konflikt. Vstupní otisk generuje server; neukládají se samotné tokeny.
Klíč používá JSON dvojici místo nejednoznačného spojování dvojtečkou.
Staré lokální karty bez otisku se odmítnou k ručnímu dořešení, nevytvoří se
vedle nich automaticky nová karta. Souběžné stejné přijetí zachová první
uložený snapshot i při rozdílu mezitím načtených dat.

Celá sada po první části opravy: 143 testů OK. Dodatečný souběžný test:
6 testů approval_store OK. Ověřeno opakování po zamítnutí bez čtení grantů,
změněný request, stará karta, souběžné přijetí a tenant hranice.
HTTP endpoint stále navazuje DB spojení před submit_proposal; výpadek
samotného připojení tedy může blokovat i replay. Tato provozní návaznost
není touto změnou odstraněna. Nasazení neproběhlo.

## HTTP replay bez závislosti na Medicusu

Navazující oprava odstranila výše uvedenou provozní závislost: endpoint
/book-appointment v režimu staff review vyhledá přijatou žádost ještě před
connect_to_db. Sdílené submission_identity/replay_proposal zachovávají stejné
ověření vstupu a izolaci tenant/hovor. Nová žádost nadále potřebuje Medicus
pro ověření; výpadek spojení nevrátí úspěch a neuloží nepotvrzenou kartu.
Chybová HTTP odpověď již nezveřejňuje interní text databázové výjimky.

Ověřeno přes FastAPI TestClient s reálným dočasným ApprovalStore a simulovaným
selháním connect_to_db: opakovaná přijatá žádost vrací původní pending kartu
bez jediného pokusu o spojení, nová žádost vrací 500 a nevytvoří kartu.
Celá sada 146 testů OK. Nejde o živý výpadkový test produkce; nasazení neproběhlo.

## Fail-closed autentizace veřejných toolů

require_auth už nepovolí neautentizovaný provoz při chybějícím bearer tokenu,
CHANGE_ME nebo chybné konfiguraci. Tyto stavy vracejí 503; nesprávná klientská
hlavička 401. Kontrola proběhne před call anchor i před databázovým připojením.
Bearer scheme nerozlišuje velikost písmen, samotný token ano; porovnání je
constant-time. Staff autentizace navíc odmítá chybný typ konfigurace a zvládá
neplatný ne-ASCII vstup bez TypeError.

Testy pokrývají všech pět veřejných tool cest, chybné konfigurace, neplatné
credentials a nulové vedlejší volání DB/store při odmítnutí. Celá sada 150 OK.
Read-only kontrola produkčního konfiguračního souboru potvrdila platný token
alespoň 32 znaků, staff review vypnutý. Hodnota tajemství nebyla vypsána.
Tato kontrola neověřovala případný override v prostředí běžící služby.
Oprava je lokální a čeká na společné nasazení.

## Metadata vedlejších účinků objednávek

Read-only audit skutečných MAIN/LASER: každá 22 triggerů a 2 navazující
procedury. Důkazy appointment_dependencies_observed.json, interpretace
appointment_side_effects.md. DELETE a UPDATE mají odlišné zápisy do historie
a podmíněné externí synchronizace (COS, ES, ClickDoc), proto DELETE+INSERT
není prokázanou náhradou přesunu přes frontend. IDREC v jedné větvi aktualizuje
PROPRI, není obecným důkazem párování sken/prohlídka. Rozsah GUI experimentu
musí doplnit související tabulky, stávající capture jen OBJOBJ nestačí.
Produkční data ani aplikace nezměněny. Audit skutečně proběhl na Firebirdu;
nezahrnoval rekurzi triggerů cílových tabulek ani provedení podmíněných větví.

## Příchozí vazby na OBJOBJ

Rozšířený metadata audit proti oběma živým DB prokázal FK_OBJPROC_OBJOBJ:
OBJPROC.IDOBJ -> OBJOBJ.IDOBJ, UPDATE i DELETE CASCADE. OBJPROC nemá vlastní
uživatelské triggery. Ve vzorku září–listopad 2026 nebyla v žádné DB žádná
navázaná OBJPROC; nevztahovat tento výsledek na všechna data. Zjištění je
v appointment_side_effects.md a GUI protokolu: smazání + nové vytvoření
nesmí ztratit tyto návaznosti. Význam IDOBJSAB/IDOBJPLAN zůstává neověřený.
Read-only provedení odhalilo rezervované SQL slovo POSITION; alias opraven
na FIELD_ORDINAL, následný celý sběr proti Firebirdu proběhl úspěšně.
Žádné produkční zápisy ani deployment.

## Integrační kontrakt handoff Medicus -> Operator

Nový test v operator_backend/tests/test_medicus_handoff_contract.py používá
skutečné implementace obou sousedních repozitářů a jejich izolovaná úložiště.
Volá handoff-summary, skutečný delivery worker a skutečný workflow ingest
Operatoru přes transportní adaptér. Simuluje ztracené potvrzení po úspěšném
uložení v Operatoru. Retry dorazí se stejným ID, ve staff detailu je jedno
shrnutí a již vyřešený požadavek se znovu neotevře. Telefon se zobrazí staff.

Cílená sada Operatoru inbox + cross-repo handoff + review bridge: 8 testů OK.
Test se explicitně přeskočí, pokud sousední Medicus repo není dostupné.
Neověřuje produkční HTTP síť, PostgreSQL, prohlížeč ani SMS/email. Autoritativní
operator_backend/CURRENT_STATE.md doplněn o aktuální lokální UI a handoff stav.
Žádná produkční zpráva nebyla odeslána ani služba nasazena.

## Pozdní post-call nesmí smazat kontakt pro callback

Integrační handoff test rozšířen o podepsaný ElevenLabs post-call webhook a
skutečný normalizační worker. Dvě varianty nejprve reprodukovaly chybu:
chybějící číslo nebo anonymous přepsalo dříve uložený kontakt na prázdný
či maskovaný nesmyslný údaj. Platné nové číslo fungovalo.

Operator normalizace nyní vybírá první použitelný telefon z kandidátů,
zachová existující kontakt při chybějícím/neplatném čísle a pro platné číslo
aktualizuje současně plný údaj, masku i hash. Podepsaný post-call neodstraní
staff summary a neotevře už vyřešený požadavek. Cílená sada: 14 testů OK
(handoff contract ve třech variantách, phone search, staff followup, webhook).
Jde o lokální opravu; stará ztracená čísla neobnovuje a produkce nezměněna.

## Trvalé upozornění na selhání handoff doručení

Po vyčerpání deseti pokusů se ve stejné SQLite transakci uloží samostatný
technický alert. Worker má pro alert vlastní lease a opakování po pěti
minutách; stabilní event_id a čas přežijí restart. Událost obsahuje jen
identifikátor hovoru/požadavku a generický kód chyby, ne shrnutí či telefon.
Doručení původního handoffu zůstává failed a vyžaduje dořešení, alert není
předáním pacientského požadavku ani důkazem e-mailového doručení.

Připraven append-only Supabase SQL 20261002_handoff_failure_alerts.sql,
navazující na existující hypercare outbox, pevného příjemce a retry pravidla.
SQL nebyl aplikován ani ověřen spuštěním v PostgreSQL; živý email test zbývá.
Při úplném výpadku Operatoru je alert rovněž odložen, nezastupuje nezávislý
monitoring hosta. Lokální unit test prokazuje atomické založení po selhání,
persistenci, retry, potvrzení a bezpečný obsah. Medicus celá sada 151 OK.

## SQL alert ověřen skutečným PostgreSQL

Docker daemon byl spuštěn, následně použit jednorázový PostgreSQL 16 kontejner
bez sítě/portů. Skutečné původní SQL a nová migrace vykonány nad minimálními
vstupními fixtures. Prošly: handoff enqueue, vyřazení demo/starých/jiného
zdroje, deduplikace probíhajícího i odeslaného alertu, odmítnutí cizího lease,
stabilní retry klíč, zachování rezervačních alertů a oprávnění. Skutečné
SET ROLE service_role dokázalo zavolat wrapper, anon/authenticated právo nemají.
Reprodukce v operator_backend/tests/sql/README.md. Kontejner po testu zastaven
a automaticky odstraněn. Žádné emaily, produkční data ani Supabase migrace.
Zbývá vlastní aplikace do Supabase a živý řízený test doručení přes Resend.

## Řízené obnovení selhaného handoffu

Přidán host-admin příkaz scripts/handoff_recovery.py: seznam pouze technických
údajů selhaných položek a --retry pro jedno konkrétní ID. Atomicky ověřuje
failed stav, nepřítomnost aktivního lease a tenant; zachovává původní event ID
 i payload a eviduje systémového uživatele, čas a minulý počet pokusů.
Přijatou či již znovu zařazenou položku odmítne. Nepovoluje žádný nový nástroj
agentovi. Pět testů doručování prošlo včetně tenant izolace, duplicitního retry,
auditního záznamu a stejného ID po obnovení. Postup handoff_recovery.md uvádí
povinné ověření výsledku, běžící worker a zachování původního failure alertu.
Nenahrazuje SMS a není zatím instalován na produkčním hostu.

## Nasazovací konfigurace v2

Příklad api.local.example.json doplněn o dosud chybějící enable_staff_approval,
approval_store_path a staff_approval_token, výchozí režim zůstává vypnutý.
Nový deployment_configuration.md propojuje konkrétní klíče Medicus/Operator,
oddělené tokeny, chráněný trvalý store, skutečný význam worker --once a stav
čekající Supabase migrace. Výslovně uvádí nedokončené backup/retention,
servisní instalaci a schvalovací zápis, nevydává konfiguraci za hotový pilot.
JSON úspěšně parsován a oba CLI --help příkazy ověřeny bez spuštění doručování.
Produkční konfigurace nezměněna.

## GUI capture v2: historie a procedury

Nástroj gui_write_evidence.py nyní v témže read-only snapshotu čte také
OBJHIST podle dat termínů a OBJPROC podle zachycených či historických IDOBJ.
Neveřejná pole exportuje jen jako HMAC; porovnání souvisejících tabulek
zachovává násobnost řádků. Odlišné verze či pokrytí se odmítají. Čtyři cílené
testy OK a skutečný Firebird sběr pro 7. 10. 2026 úspěšný: MAIN historie 42,
LASER historie 6, OBJPROC 0 v obou. Výstup tmp/gui_evidence_related_smoke.json.
Jednorázový klíč neuchován. Žádné GUI operace ani zápisy do produkce.
Synchronizační tabulky a ostatní podmíněné vedlejší účinky stále zbývají.

## Konkrétní fragmenty ElevenLabs nástrojů

Z uložených exportů ověřen starý kontrakt: appointment_write stále požadoval
IDPAC/patient_verified a přiřazoval write_ok z ok; handoff nepřenášel stabilní
request_id ani conversation_summary. Připraveny dva patch.json fragmenty
v tool_patches s kompletní náhradou body schématu, popisu a assignments.
Neobsahují credentials, URL ani autentizační hlavičky. Rollout popisuje přesné
vnořené nahrazení bez ztráty auth a omezení: nejde o celé importovatelné tools,
živý export a zbývající tools ještě nejsou upravené. Lokální strukturální
kontroly prošly; ElevenLabs import/publish ani tool-call test nebyly provedeny.

## Kompletní sada pěti v2 webhook fragmentů

Doplněny patient_lookup, doctor_availability a agent_capabilities patch.json.
Odstraněny phone-only a last4 instrukce i patient_idpac assignment, historie
je volitelná místo natvrdo false. Availability drží review_services, konzistentní
příchod/skener, akutní předání a konstantní limit 3. Capabilities rozlišují
review od potvrzeného zápisu. In-memory sloučení všech pěti fragmentů s místním
exportem ověřilo zachování transportu/autentizace a unikátní pole. Žádné tajemství
ani celé autentizované definice nebyly nově exportovány. Živá konfigurace,
provider validace a publikace zůstávají neprovedené; rollout dokument upraven.

## Ověření alternativního desktopového přístupu

Po načtení computer-use skillu a jeho dokumentace byl objeven a skutečně
zavolán dostupný node_repl s inicializací @oai/sky. Selhal před ovládáním UI:
failed to write kernel assets, systém nemůže nalézt uvedenou cestu (os error 3).
Podporovaný reset kernelu proběhl, opakovaná inicializace skončila totožně.
Nejde tedy pouze o chybějící browser tool: oba dostupné běhové mechanismy
ovládání UI aktuálně selhávají před zahájením práce. Žádné okno Medicusu
nebylo přečteno ani ovládáno. Pro řízenou GUI session je nutná spolupráce
uživatele nebo oprava runtime nástrojů. Databázový přístup přes SSH funguje,
ale nepředstavuje náhradu požadovaného experimentu přes skutečný frontend.

## Živé ověření Supabase migrace po aplikaci uživatelem

Dne 2. 10. 2026 (lokální čas) ověřeny oba claim objekty v read-only transakci:
wrapper odpovídá nové migraci, přejmenovaná funkce původnímu SQL; postgres owner,
SECURITY DEFINER, prázdný search_path. Anon/authenticated nemají EXECUTE;
service_role smí pouze wrapper. JSON důkaz uložen v Operator tests/sql.
Privátní outbox/config ani cron schema nejsou dostupné runtime roli. Neproběhl
nový skutečný e-mailový test, žádná změna oprávnění ani Firebird operace.
GUI ověření odloženo dle uživatele, celý cíl zůstává aktivní.

## Konzistentní záloha trvalé fronty

Přidán host-admin nástroj scripts/approval_backup.py: read-only zdroj,
SQLite backup API, integrita, výhradně nový cílový soubor, časový limit a
úklid neúspěšné zálohy. Výstup neobsahuje data pacientů ani cesty.
Dva cílené testy prošly: kopie potvrzených WAL dat při otevřeném zdroji,
samostatné čtení stavu handoffu a failure alertu, izolace od následných změn,
ochrana existující zálohy/zdroje a úklid při neplatné databázi.
Deployment dokument obsahuje postup obnovy s pozastavením pouze dotčených
procesů a povinným vyhodnocením nejasných zápisů před spuštěním. Produkční
záloha, plánování, retence a host recovery drill zatím nejsou provedeny.
