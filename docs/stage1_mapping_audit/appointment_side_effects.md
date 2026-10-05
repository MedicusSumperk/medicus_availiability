# Vedlejší účinky změn OBJOBJ

Zdroj: `appointment_dependencies_observed.json`, čtení metadat živých MAIN
a LASER nástrojem `tools/diagnostics/appointment_dependencies.py`. Žádný
pacientský řádek ani zápis nebyl potřeba. V každé DB zjištěno 22 triggerů
a dvě procedury volané ze zjištěných triggerů. U pojmenovaných uživatelských
triggerů souhlasí text a příznak aktivity mezi oběma DB; systémové CHECK
triggery mají odlišná jména. Shoda definic není důkazem shodné konfigurace
externích integrací nebo skutečného vykonání podmíněných větví.

## Potvrzené chování ze zdrojů triggerů

| Změna / podmínka | Účinek |
| --- | --- |
| Smazání objednávky | OBJOBJ_BD0 vloží původní obsah do OBJHIST s AKCE=D; zahrnuje osobní údaje a poznámky. |
| Změna sledovaných polí | OBJOBJ_BU2 vloží původní obsah do OBJHIST s AKCE=U a novým DUVODZMENY. |
| Přesun internetové objednávky s IDEXT a IDCAL_EXT | OBJOBJ_BU0 vynuluje externí vazbu a vloží původní dvojici do COS_DELOBJ. |
| Smazání objednávky s IDEXT a IDCAL_EXT | OBJOBJ_AD0 vloží dvojici do COS_DELOBJ. |
| INSERT/UPDATE a DELETE | Volají COS_NEEDCALSYNC; ta podle COS_CALEND označuje datum/pracoviště v COS_CALEND_SYNC. Při chybě ji procedura zachytí; úspěšný zápis OBJOBJ sám neprokazuje synchronizaci. |
| UPDATE s původním TYPPROH=D a neprázdným IDREC | IDREC_REF_AU mění datum/čas v PROPRI, s podmínkou shody IDPAC a IDPRAC. IDREC tedy nelze obecně označit za vazbu sken–vyšetření. |
| UPDATE odeslané objednávky s ES_UID a změnou času | OBJOBJ_AU1 spravuje ES_APPUPD s typem U; další větev může nulovat ODESLANO v ES_APP. |
| DELETE objednávky s ES_UID | OBJOBJ_AD1 podle stavu vloží ES_APPUPD s typem D, nebo změní stav neodeslané ES_APP na C. |
| UPDATE | OBJOBJ_AU10 nastaví CLICKDOC_OBJ.REMOTECHANGE=F pro IDOBJ. |
| INSERT/UPDATE/DELETE | TRG_OBJOBJ_LOG_* volají SP_LOG; podle nastavení vzniká LOG nebo ZURNAL. Update pod uživatelem ESER má výjimku. |
| Změny a DELETE | POST_EVENT oznamuje OBJOBJ_AIUD, při DELETE také OBJOBJ_DELETED. Reakce posluchačů není ze samotné definice prokázaná. |

OBJOBJ_BI generuje IDOBJ, další triggery nastavují CREATED/CHANGED a skládají
CELEJMENO. Generátor PIN OBJOBJ_BI2 je v obou DB neaktivní.

## Důsledek pro v2 a GUI experiment

**Přesun pomocí DELETE + INSERT nelze pokládat za ekvivalent UPDATE.**
Liší se historie, ID objednávky i větve externí synchronizace. Zatím není
prokázáno, kterou variantu používá frontend pro jednotlivé služby.

Před schválením zápisové cesty je nutné rozšířit before/after důkazy také o
OBJHIST, relevantní LOG/ZURNAL a podle přítomných vazeb o COS_DELOBJ,
COS_CALEND_SYNC, ES_APPUPD/ES_APP, CLICKDOC_OBJ a případně PROPRI/COS_PAC.
Vybrat pouze řádky související s testovací operací; nepřenášet volný obsah
historie pacientů do reportu. Existující gui_write_evidence.py je stále
omezený na OBJOBJ a tuto novou část sám nepokrývá.

Dále ověřit příchozí cizí klíče a triggery cílových tabulek. Získaný graf
sleduje procedury přímo či nepřímo volané z OBJOBJ triggerů; neprochází
rekurzivně triggery všech tabulek, do nichž se zapisuje, ani kód aplikace.
Nezjišťuje skutečné doručení do COS/ES/ClickDoc. To vyžaduje samostatný důkaz.

Zjištění podporuje zachování blokace neověřených přesunů a rušení.
Nedokládá vazbu skenu a vyšetření mezi MAIN a LASER.

## Doplnění: příchozí cizí klíč

Přímý dotaz do systémových katalogů v obou DB zjistil jediný příchozí
cizí klíč na OBJOBJ: `OBJPROC.IDOBJ → OBJOBJ.IDOBJ`, s UPDATE CASCADE
a DELETE CASCADE. Smazání objednávky tedy může fyzicky odstranit také
související OBJPROC. Nové vytvoření objednávky tyto řádky samo neobnovuje.
OBJPROC má sloupce IDOBJPROC, IDOBJ, IDOBJSAB a IDOBJPLAN; obchodní význam
posledních dvou identifikátorů zde není potvrzen. Nemá vlastní uživatelské
triggery podle aktuálního katalogu.

Ve vzorku objednávek s DATUM od 1. 9. do 30. 11. 2026 nebyla nalezena žádná
navázaná OBJPROC v MAIN ani LASER (0 vazeb, 0 objednávek). Tento nulový
výsledek platí pouze pro uvedené období, nikoli pro celou databázi. Nejde
o vysvětlení říjnového incidentu a neumožňuje vazbu obecně ignorovat.

Pro GUI test přidat capture OBJPROC podle původních i nových IDOBJ a zachovat
původní ID při dohledávání po zrušení. Případnou větev s navázaným OBJPROC
nepovolovat pro automatický přesun DELETE+INSERT bez samostatného ověření.
Nenalezení dalšího cizího klíče nevylučuje logické vazby bez databázové constraint.

Následná implementace: gui_write_evidence.py verze 2 již zachycuje OBJHIST
a navázané OBJPROC; dřívější poznámky o omezení pouze na OBJOBJ popisují
předchozí stav nástroje. Ostatní výše uvedené tabulky stále nepokrývá.
Read-only zkušební sběr pro 7. 10. 2026 zachytil v MAIN 42 historických
řádků a v LASER 6, navázané OBJPROC v obou 0. Nejde o provedený GUI zápisový
experiment ani o rekonstrukci historie v okamžiku původního hovoru.

## Kandidát společného zápisu MAIN/LASER (5. 10. 2026)

`scripts/paired_appointments.py` implementuje vytvoření, přesun a zrušení
technické dvojice MAIN aktivita 1 + LASER aktivita 28. Laser má IDPAC NULL;
MAIN IDPAC se do druhé databáze nekopíruje. Každý řádek nese v INFO stejný
náhodný identifikátor s rolí MAIN/LASER. INFO má podle živých metadat limit
80 znaků, proto se krátí pouze uživatelská část poznámky, nikoli identifikátor.
Neoznačené starší rezervace se nepárují podle jména ani času. Chybějící,
duplicitní či změněný protějšek, cizí pacient, externí vazby a OBJPROC vedou
k odmítnutí a předání personálu. Autoři zápisu se ověřují v každé DB zvlášť:
MAIN účet 10 nelze použít v Laseru, kde neexistuje. Pro izolovaný test je
použit LASER účet 2, který existuje a je autorem posledních tří skenů.
Produkční autor musí být výslovně nakonfigurován; příklad má hodnotu null.

Obě DB používají jednu distribuovanou transakci FDB ConnectionGroup (2PC).
Přesun dočasně vyjme přesně oba původní řádky v SAVEPOINT, ověří dostupnost
ve stejné transakci, vrátí SAVEPOINT a provede UPDATE původních IDOBJ.
Dočasné DELETE ani jejich transakční historie se necommitují. Jde o kandidátní
mechanismus: úspěšný živý přesun a vedlejší účinky ještě nebyly potvrzeny.

Pro ochranu proti souběžnému vložení je OBJOBJ v obou DB rezervována
PROTECTED WRITE s NOWAIT. To chrání i proti ručnímu zápisu v Medicusu,
ale má významné provozní omezení: 5. 10. oba živé HTTP pokusy skončily
SQLCODE -901 / 335544345 již při zahájení transakce. Samostatný test MAIN
i LASER s izolací SNAPSHOT i READ COMMITTED potvrdil odmítnutí zámku.
Monitorovací pohledy ukázaly aktivní transakce Medicusu; neurčují jednoznačně
konkrétního držitele zámku. Žádná relace nebyla ukončena. Zámek nebyl oslaben.
V posledním kandidátu se tento případ vrací jako calendar_busy_retry_later.
Nejde o úspěšné živé ověření zápisové cesty. Produkční zapnutí je blokované
do ověření dvojice a provozní použitelnosti zámků při práci personálu.

Obnova a opakování požadavku:

1. Konfigurace vyžaduje `enable_paired_appointment_writes=true`, LASER
   `write_enabled=true` a absolutní `paired_write_journal_path` v adresáři
   s omezenými ACL a zálohováním. Tyto příznaky jsou v produkci vypnuté.
2. Každá operace potřebuje stabilní request_id. Lokální SQLite journal je
   mimo Medicus; nevyžaduje Firebird ani Supabase migraci. Obsahuje identifikátory
   a výsledky, proto se nesmí publikovat jako veřejný log.
3. Opakování dokončeného request_id vrátí uložený výsledek. Jiné tělo se stejným
   ID je odmítnuto. Stav started nebo commit_started blokuje další dvojice;
   nemá automatickou expiraci ani automatické opakování commitů.
4. Po výpadku neodstraňovat journal a neopakovat zápis s novým ID. Správce
   ověří stav distribuované transakce v obou DB, případný limbo stav a přesné
   řádky podle uložených ID a značek. Rozhodnutí o obnově nesmí vycházet pouze
   z chybějící HTTP odpovědi. Dokud není stav jednoznačný, zápisy zůstanou blokované.
5. Ruční uzavření journalu ani automatický recovery executor nejsou tímto
   kandidátem implementovány. Živý test ztraceného spojení během 2PC neprovádět
   na produkční databázi; vyžaduje izolované databáze a ověřený postup obnovy.

Dokumentace driveru: https://www.firebirdsql.org/file/documentation/drivers_documentation/python/fdb/usage-guide.html
Implementace ConnectionGroup byla ověřena také přímo ve FDB 2.0.4 na serveru.

### Diagnostika přerušeného páru

`scripts/paired_recovery.py --journal <absolutní-cesta> --request-id <ID>`
otevírá journal v SQLite mode=ro a případné dotazy na obě databáze ve
výslovných READ ONLY / NOWAIT transakcích. Nikdy nepotvrzuje transakci,
neodblokuje journal a nemění limbo stav. Výstup neobsahuje jméno, IDPAC ani
volný text. Pro vytvoření/přesun rozliší oba odpovídající řádky, neúplný či
změněný pár a absenci obou. Pro zrušení označí pouze viditelnou absenci;
ta sama není důkazem úspěšného commitu. Snapshoty obou DB nejsou atomické.

Sedm testů pokrývá shodu, změnu času/identity/značky, částečný zápis, absenci
obou částí, zrušení, nedostatek commit intentu a neměnnost journalu při čtení.
Na serveru ověřeno spuštění nad PAIRTEST_20261005_create2: state=rejected,
observation=no_recorded_commit_intent, journal_changed=false. Tento konkrétní
kontrolní běh nepotřeboval připojení k Medicusu a neprokazuje obnovu 2PC.

5. 10. doplněn úklid diagnostických spojení: selhání rollback/close jedné DB
nepřeskočí pokus o uzavření druhé. Původní chyba inspekce má přednost;
samostatná chyba úklidu se vrátí jako neúspěch diagnostiky. Deset cílených testů
prošlo, včetně výpadku druhého připojení a chyby při úklidu. Jde o lokální
regresní důkaz s náhradami spojení, nikoli živou obnovu nebo uvolnění zámků.

## Candidate update — 2026-10-05

### Superseding decision — staff first, 2026-10-05

User explicitly accepted rare concurrent-insert collisions after revalidation.
The local candidate now uses fresh SNAPSHOT/NOWAIT transactions without an
OBJOBJ table reservation for both single and paired writes. Known conflicts
must return without a write; a late collision is resolved by staff contacting
the patient. No automatic overwrite/deletion of another booking is permitted.
2PC, idempotency and uncertain-commit reconciliation remain required. Nineteen
paired transaction tests passed, including revalidation-before-write, refusal
before insertion and both paths without table reservations. These are local
mocked-connection regressions; live write/GUI validation is still required.

The vendor locking contract below is no longer a prerequisite for this accepted
policy. Its earlier prohibition on reducing reservation scope is superseded by
the user's explicit decision. Production configuration remains unchanged.

### Historical protected-table concurrency gate

The current protected-write reservation covers OBJOBJ as a table, not only the
selected doctor/day or the managed pair. The live NOWAIT probe fails before DML
in both databases (335544345). A subsequent targeted MON snapshot finds open
Medicus GUI transactions, including transactions started around 14:24–14:30;
it does not identify the exact blocking owner. Evidence:
`live_projection_lock_check_20261005.json` and
`live_transaction_groups_20261005.json`.

Firebird documents that PROTECTED WRITE prevents concurrent SNAPSHOT/READ
COMMITTED transactions from writing the reserved tables:
https://www.firebirdsql.org/file/documentation/chunk/en/refdocs/fblangref25/fblangref25-transacs.html
This supports treating the lock scope as an operational integration issue,
not assuming an API read error or simply retrying writes until a test passes.

Technical questions for the Medicus integrator/vendor (not reception staff):
1. Which supported transaction/locking contract coordinates appointment inserts
   from the GUI with an external writer, including inserts into previously empty
   intervals? Identify the exact existing lock/resource and when the GUI takes it.
2. Is there an existing supported booking operation that validates and reserves
   both MAIN doctor capacity and LASER scanner capacity? Specify rollback and
   ambiguous-commit recovery semantics without changing DB objects.
3. How should an external writer coexist with the GUI's long-lived transactions,
   and which restart-free operational procedure releases its reservations?
4. Which existing GUI/database mechanism links anonymous LASER rows to MAIN
   visits, if any, without inferring linkage from adjacent times?

Until verified, preserve disabled write flags. A quiet-window test can validate
row/trigger mapping but cannot prove safe concurrent production operation.
An application-only mutex cannot coordinate an unmodified external GUI; a
read/check/write without shared coordination is not equivalent protection.
No schema/trigger/procedure change, killing GUI sessions, or reduced isolation
is authorized as a workaround for this gate. Vendor correspondence is a draft
only; no message has been sent. Other pilot requirements remain in scope.

The current local single/pair move candidates no longer temporarily DELETE
source rows to query availability. They filter only verified source IDOBJ values
from the read projection and then UPDATE the original rows. This supersedes the
SAVEPOINT/temp-delete approach described in the historical notes below. Pair
identity and ordinary-row guards remain mandatory; protected transaction locks
are unchanged. Live Firebird behavior of the new candidate remains unverified.
