# Porovnání dodaného produkčního promptu s dohodnutými pravidly

**Stage 1, pouze revize návrhu. Žádná změna promptu v ElevenLabs, nástrojů, runtime ani produkce.**

Zdroj: [přesná kopie promptu dodaného uživatelem](production_prompt_supplied_2026-10-01.txt). Označení „produkční“ pochází od uživatele; živou konfiguraci agenta ani schémata toolů jsme při tomto porovnání nečetli. Soubor docs/elevenlabs_agent_prompt_current_cs.md jsme nepřepsali.

SHA-256 zdroje: `f2888f84cdb5149f98e23f40d5d3531d25dd979468c16f57ad5dcf80f6dc4d24`.

Pravidla: USER-REVIEW-01 až 45 v [review_log.md](review_log.md) a [rules.json](rules.json). Pozdější rozhodnutí upřesňují starší formulace; některé historické otevřené otázky v inventáři již nelze interpretovat jako nevyřešené business rozhodnutí.

## Co už funguje na úrovni textu a zachovat

- Okamžitý handoff na výslovnou žádost bez dalších otázek.
- Nedělitelnost objektu nabídky: nemíchat lékaře a časy mezi options.
- Relativní datum podle aktuálního místního času, weekday_cs z výsledku, zákaz minulých termínů.
- Žádný rutinní last4; identita před zápisem; zákaz sdělování údajů neověřených pacientů.
- Recheck dostupnosti před create/reschedule, čekání na výslovné potvrzení, potvrzení výsledku až po zápisu.
- Rozlišení komunikovaného a technického času; zákaz rozloučení při předání.

Přítomnost pravidla v promptu není důkaz funkční integrace nebo jeho dodržení v hovoru.

## Konkrétní rozdíly

### P01 — Předání na žádost

**ZACHOVAT.** [prompt, ř. 263](production_prompt_supplied_2026-10-01.txt#L263). Navazuje na USER-REVIEW 19, 20, 38.

Okamžité předání bez dalších otázek je již výslovné. handoff_summary a transfer_to_number jsou uvedeny. Návrhově doplnit, že selhání shrnutí nesmí samo zablokovat pokus o transfer; pokračování po chybě musí podpořit integrace.

### P02 — Požadavek mimo scope

**ROZPOR.** [prompt, ř. 290](production_prompt_supplied_2026-10-01.txt#L290). Navazuje na USER-REVIEW 19, 38.

Závěrečná sekce zdravotních dotazů nabízí objednání či změnu místo předání původního požadavku. Další sekce naopak přikazují handoff. Sjednotit na předání; nevnucovat náhradní službu. Stejně omezit návrh měnit typ služby po neúspěšném hledání a zabránit náhradní nabídce při použití voice_answer_cs.

### P03 — Technické chyby a nejistý zápis

**ROZPOR / CHYBÍ.** [prompt, ř. 228](production_prompt_supplied_2026-10-01.txt#L228). Navazuje na USER-REVIEW 20, 37, 38.

Neověřitelný výsledek není jistý neúspěch. Rozlišit známou kolizi, známé odmítnutí a neznámý výsledek zápisu. U technické chyby informovat, zaznamenat původní požadavek i chybu, notifikovat admina a přesměrovat; nejistou mutaci slepě neopakovat. Aktuálně je uvedena jen nabídka předání a tvrzení, že se změna nepodařila.

### P04 — Výsledek konkrétní operace

**ZPŘESNIT.** [prompt, ř. 227](production_prompt_supplied_2026-10-01.txt#L227). Navazuje na USER-REVIEW 38, 39.

Úspěch vázat na aktuální odpověď a konkrétní operaci, nikoli na možné staré write_ok ve stavu konverzace. To je technický návrh k již schválenému potvrzování skutečného výsledku, ne doklad prokázané produkční chyby.

### P05 — Ověření pacienta pro všechny změny

**ROZPOR / NEDOSTATEČNĚ JASNÉ.** [prompt, ř. 177](production_prompt_supplied_2026-10-01.txt#L177). Navazuje na USER-REVIEW 29–35.

Standard je jméno, příjmení a datum narození. Prompt vyžaduje příjmení+datum explicitně pro create, ale dovoluje phone-first u existujících termínů a dále spoléhá na verified. To není jednoznačná záruka stejného standardu pro read/move/cancel. Dřívější audit navíc našel phone-only verified v lookupu. Potřebná úprava smlouvy API i promptu, nikoli jen věta o zákazu phone-only zápisu.

### P06 — Nedohledaná nebo nejednoznačná karta

**DOPLNIT.** [prompt, ř. 181](production_prompt_supplied_2026-10-01.txt#L181). Navazuje na USER-REVIEW 32–35.

Po nulové shodě zopakovat použité jméno, příjmení a datum; opravu znovu hledat, při potvrzení původních údajů nabídnout personál. Při více shodách po úplných údajích volba celého RČ nebo personálu. Rutinní zákaz last4 zachovat. Opakování údajů dodaných volajícím odlišit od zakázaného zveřejňování hodnot z DB.

### P07 — Objednání za jinou osobu a existující karta

**ROZPOR V ROZHODOVACÍM POSTUPU.** [prompt, ř. 105](production_prompt_supplied_2026-10-01.txt#L105). Navazuje na USER-REVIEW 29–31.

Rozhoduje existence karty cílového pacienta a IDPAC, ne minulá osobní návštěva volajícího. Současné oslovení „už jste u nás byl“ může nesprávně odmítnout rodiče objednávajícího dítě nebo člověka s již založenou kartou bez minulé návštěvy. Nové karty agent nezakládá; zastupování výslovně povoleno pro create/move/cancel.

### P08 — Typy návštěv a aktivní capabilities

**ZMĚNA NÁVRHU / ZÁVISLOST NA API.** [prompt, ř. 119](production_prompt_supplied_2026-10-01.txt#L119). Navazuje na USER-REVIEW 19, 40–43.

Nový návrh rozlišuje skin, dermatoskopii se skenem, dermatoscope_followup jako prohlídku po skenu bez vyšetření a regular_check po vyšetření/zákroku. Kontroly může agent řešit na výslovnou žádost. Prompt je dosud předává a jinde tvrdí pevný produkční scope skin+derm v rozporu s dynamickými capabilities. Zachovat skutečné příznaky API; kontroly nezapínat jen promptem. Plazma/laser/zákroky zůstávají mimo první scope.

### P09 — Kontrola v doporučeném odstupu

**CHYBÍ.** [prompt, ř. 177](production_prompt_supplied_2026-10-01.txt#L177). Navazuje na USER-REVIEW 41, 42, 44, 45.

Podle sděleného doporučení pacienta lze použít historii jako podklad data relevantní návštěvy a hledat cíleně za rok či jindy. Žádný univerzální roční limit. Neznámý interval -> personál. Okno dva týdny nebo měsíc podle zátěže, i krátce před cílovým datem, s explicitními hranicemi. Minulá rezervace není automaticky důkaz absolvování. Výjimka z pozdního lookupu může být potřebná, pokud datum určuje až historie; technický návrh ještě musí sladit pořadí kroků.

### P10 — Preference lékaře a rozšíření hledání

**DOPLNIT.** [prompt, ř. 133](production_prompt_supplied_2026-10-01.txt#L133). Navazuje na USER-REVIEW 21, 25, 26, 43–45.

Při zadaném lékaři nejprve respektovat jeho výběr, pak rozšířit maximálně na šest měsíců v mezích požadavku; po neúspěchu volba jiného lékaře nebo personálu. Bez preference hledat nejbližší napříč skutečně ordinujícími lékaři. Totéž přesun a kontroly, i preference zmíněná dříve. Rozšíření nesmí zrušit explicitní date_to pacienta; cílené budoucí kontroly mají vlastní krátké okno.

### P11 — Minimální předstih a skutečný příchod

**CHYBÍ.** [prompt, ř. 96](production_prompt_supplied_2026-10-01.txt#L96). Navazuje na USER-REVIEW 17, 22.

Samotný zákaz minulého začátku nestačí. Přidat schválený default jedné hodiny od zavolání a časové preference počítat již pro požadovaný příchod včetně skenu/společného příchodu. Autoritativní čas hovoru a revalidaci řešit v API; runtime čas sám není potvrzeným časem začátku hovoru.

### P12 — Víkendy a svátky

**CHYBÍ.** [prompt, ř. 132](production_prompt_supplied_2026-10-01.txt#L132). Navazuje na USER-REVIEW 23, 24.

Jen pondělí až pátek, bez víkendové výjimky, i když API vrátí slot. Samostatná blokace českých svátků pro všechny roky dotčené hledáním. Vynucovat v dostupnosti; prompt nesmí sám vymýšlet kalendář svátků.

### P13 — Příchod, sken a společný blok

**ROZPOR / OTEVŘENÉ MAPOVÁNÍ.** [prompt, ř. 121](production_prompt_supplied_2026-10-01.txt#L121). Navazuje na USER-REVIEW 06, 08, 10, 12–16, 22.

Pevná formulace start_time lékaře a scan_start_time se musí sladit s obecnou sekcí spoken_time_label a návrhem společných příchodů také pro dermatoskopii. Nepřidávat vlastní další minus15 ani nepokládat několik skenů na stejný čas. Pořadí sken před prohlídkou a jediný přístroj musí vynutit backend. Oddělit příchod od garance přesného zahájení lékařem.

### P14 — Výjimečný samotný sken

**CHYBÍ / ZÁVISLOST NA API.** [prompt, ř. 117](production_prompt_supplied_2026-10-01.txt#L117). Navazuje na USER-REVIEW 02–06, 42.

Běžně nabídnout sken+prohlídku. Na výslovnou žádost umožnit scan-only podle návrhu, informovat o následné prohlídce a nevydávat naději na domluvu na místě za potvrzenou rezervaci. Zachovat samostatné pravidlo odložené prohlídky po skenu: nad tři měsíce předat personálu; nemíchat s roční kontrolou.

### P15 — Akutní požadavky

**NEPŘEDBÍHAT POTVRZENÍ PROVOZU.** [prompt, ř. 139](production_prompt_supplied_2026-10-01.txt#L139). Navazuje na USER-REVIEW 18, 38.

Prompt dovoluje odemknout ranní sloty pomocí emergency=true, zatímco rezervování pohotovosti a konkrétní doporučený čas zůstávají k potvrzení klientem. Návrh emergency tagu znamená předání, ne automatické oprávnění rezervovat. Dvě rozdílné instrukce k 155 („nesouvisející nebo obecný zdravotní požadavek“ versus „podle závažnosti“) nejsou sjednocené; klinickou eskalační formulaci má posoudit klinický garant, nikoli odvozovat agent z příslušnosti dotazu k ambulanci.

### P16 — Přesun a rušení celé návštěvy

**CHYBÍ / ZÁVISLOST NA API.** [prompt, ř. 220](production_prompt_supplied_2026-10-01.txt#L220). Navazuje na USER-REVIEW 26–28, 36, 37.

Prompt pracuje s jedním idobj; pro běžnou dermatoskopii má změna zahrnout sken i navazující prohlídku. Změna jedné části -> personál. Výběr při více návštěvách a potvrzení již existují; backend musí bezpečně spojit řádky a zachovat původní rezervaci při neúspěšném přesunu. Změnu těsně před původní návštěvou nezakazovat, nový termín však splňuje předstih.

### P17 — Potvrzení nové rezervace

**TÉMĚŘ HOTOVO.** [prompt, ř. 231](production_prompt_supplied_2026-10-01.txt#L231). Navazuje na USER-REVIEW 37, 39.

Výslovné potvrzení a čekání už je správně. Doplnit službu, aby krátké shrnutí obsahovalo službu, lékaře, datum a příchod; u dermatoskopie jasně sdělit sken i navazující prohlídku. Po obsazení a novém výběru znovu získat potvrzení.

### P18 — Předání, callback a ukončení

**DOPLNIT PRIORITU A FALLBACK.** [prompt, ř. 291](production_prompt_supplied_2026-10-01.txt#L291). Navazuje na USER-REVIEW 20, 21, 38.

Zachovat zákaz rozloučení při live transferu a dát mu výslovnou přednost před obecným ukončením. Handoff summary samo nedokazuje doručení. Pro obsazeno/nezvednuto má být callback dle zmeškaného hovoru; při technické chybě zachovat požadavek a admin alert. Skutečný návrat AI, hlášku a původní caller ID ověřit až testem po implementaci podle dohody.

## Co samotný prompt nevyřeší

- Správné MAIN/LASER aktivity pro služby, identitu pacienta v obou DB a spolehlivé párování skenu s prohlídkou. Zejména regular_check je business potvrzené, ale mapování na aktivitu5 je stále v rozporu s názvem aktivity.
- Ověření jména a data narození ve verified, aktuálnost stavu operace, úplnou revalidaci dostupnosti a bezpečné změny dvou rezervací.
- Zákaz víkendů, kalendář svátků, předstih, řazení napříč lékaři, krátké budoucí okno a jeho výkon.
- Skutečné doručení požadavku personálu, admin notifikaci a chování telefonního transferu.
- Úplný sken/prohlídku při společných příchodech a scan-only flow.

Předchozí serverový snímek z 1.10.2026 měl zápisy i dermatoskopické nabídky vypnuté. Tato revize jejich dnešní stav znovu nezjišťovala. Věta v promptu o produkční podpoře služby neznamená, že je API aktuálně povoluje.

## Krátké otázky pro personál

1. **Sken a společný příchod:** Je běžný sken 15 minut? Na jednom konkrétním bloku ukažte příchod, sken a prohlídku prvního a dalšího pacienta; podle čeho předáváte nestandardně dlouhou návštěvu personálu?

2. **Kam se objednávají kontroly:** Ukažte v Medicusu příklad prohlídky po samotném skenu a kontroly po vyšetření/zákroku. Kterou položku v UI vybíráte? Názvy aktivit/ID následně přiřadíme sami. Význam služeb už je potvrzen, znovu jej neotevíráme.

3. **Kalendář přístroje:** Ukažte, kde evidujete obsazenost jediného dermatoskopu a zda se samostatně eviduje nepřítomnost obsluhy. Tím ověříme úplnost čtených kalendářů.

4. **Pohotovost:** Jaký příchod smí recepční doporučit při akutním požadavku a musí jej nejprve schválit personál? Rezervuje se vůbec konkrétní políčko? Pravidlo předat personálu už platí.

5. **Výjimky pouze pokud je chcete:** Má být jiný než prozatímní hodinový předstih pro nové objednání nebo časové omezení rušení/přesunu? Do změny platí současné domluvené defaulty.

Pro klinického garanta, nikoli databázový dotaz recepci: sjednotit znění eskalace akutních a obecných zdravotních dotazů. Zde neposuzujeme medicínskou správnost jednotlivých hlášek.

## Další postup v rámci návrhu

Připravit konsolidovaný návrh úprav promptu se zachováním již správných pasáží až po sladění nástrojových kontraktů. Nepřepisovat produkční prompt na nové service keys nebo parametry před jejich podporou. Aktivace kontrol, zápisy a schvalovací workflow nejsou tímto porovnáním povoleny. Praktické telefonní testy zůstávají podle dohody až po implementaci.

## Ověření této revize

Zdrojová kopie byte-for-byte, dohledání všech 18 odkazovaných pasáží, kontrola navazujících USER-REVIEW záznamů a lokálních odkazů. Nebyl proveden telefonní test, živý API dotaz, klinické ověření informací o pracovišti ani test runtime.
