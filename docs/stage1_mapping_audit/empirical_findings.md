# Empirické ověřování – první databázový vzorek

Zdroj: `empirical_calendar_observed.json`, získaný nástrojem
`tools/diagnostics/empirical_calendar_audit.py` přímo na hostu Medicusu.
Aktuální číselníky a procedury: `observed_server_recheck.json`.
Oba nástroje používají read-only transakce a rollback. Žádný zápis termínu
ani nasazení v této části neproběhl. Export neobsahuje pacientská jména,
IDPAC, rodná čísla, kontakty ani volné texty; obsahuje technická ID termínů
pro následné dohledání ve frontendu.

## Zjištěno

Rozsah 1. 9. až 30. 11. 2026; 12 náhodných dat s pevným seedem 20261007,
doplněných dny pro nalezené kombinace TYP/IDCINNOSTI a 2. a 7. říjnem.

| Databáze | Surové záznamy v rozsahu | Porovnané dny | Rozdíly oproti OBJOBJ_SEL |
| --- | ---: | ---: | ---: |
| MAIN | 2801 | 16 | 0 |
| LASER | 1265 | 22 | 0 |

Porovnání používá multiset celých vybraných technických polí, nikoli jen
počet řádků. Probíhá v konzistentním snapshotu jednotlivé databáze; snapshoty
MAIN a LASER nejsou společnou atomickou transakcí.

Všechny nalezené záznamy mají TYP=1. MAIN obsahuje aktivity 1, 2, 3, 5, 6
a NULL; LASER výrazně více aktivit. TYP samotný proto v tomto vzorku
nerozlišuje obchodní význam termínu.

Aktuální MAIN číselník výslovně označuje aktivitu 5 jako „Sken znamének 2
a vyšší“ a 2 jako „kontrola po skenu“. Aktivitu 5 nelze na základě názvu
považovat za obecnou kontrolu po vyšetření či zákroku.

V obou databázích není žádný současně uložený záznam TYP 9 nebo 10, ani
mimo zvolené období. Opakování tedy nelze empiricky potvrdit existujícími
řádky; implementaci rozvinutí známe ze zdroje procedury, což je jiný důkaz.

Aktivní rozvrhy v rozsahu používají TYPTYD=4 a intervaly 10 i 15 minut.
Jiné týdenní režimy tento vzorek neověřuje.

V rozsahu nejsou výjimky OBSODLIS. V celé MAIN je 24 řádků výjimek,
nejnovější 25. 6. 2026; v LASER 41, nejnovější 17. 2. 2026.
Procedura OBSDNE_PRAVODLIS_SEL preferuje objednávací výjimky za celé
pracoviště před běžným rozvrhem. Dostupnost to musí respektovat i při
následném filtrování konkrétního lékaře.

## Co zatím potvrzeno není

- Shoda s viditelným frontendem Medicus a správnost jeho obchodních popisků.
- Shoda nabídky našeho API se skutečnou obsazeností všech zdrojů.
- Propojení pacienta a dvojice sken/vyšetření mezi MAIN a LASER.
- Zápisový postup frontendu a všechny změny při přesunu či zrušení.
- Rozvrhové výjimky: navázat konkrétními historickými daty uvedenými výše.

Následuje porovnání historických výjimek s běžným rozvrhem a výstupem
procedury, poté API a UI. Absence rozdílů v tabulce není schválením celého
mapování ani uvolněním zápisů do produkce.

## Doplnění: historické výjimky a oprava výběru kontextu

Prověřeno všech 8 kombinací datum/pracoviště s výjimkou v MAIN a 16 v LASER.
Je-li alespoň jedna výjimka objednávací, její technické bloky souhlasí
s výstupem procedury. Parametr týdenního typu byl 4; jiné režimy se tím
nepotvrzují. Výjimka s OBJED odlišným od A sama o sobě nezavře rozvrh:
procedura ji ignoruje a použije běžný rozvrh.

Nasazený find_schedule_contexts přehlédl v obou databázích lékaře 1,
pracoviště 1, dne 10. 10. 2007. Výjimka obsahuje blok 08:00–11:00 s krokem
15 minut a procedura jej vrací, ale běžný rozvrh nedává API žádný kontext.
Tento historický důkaz potvrzuje chybu výběru, nikoli příčinu říjnového
incidentu s nabídkou obsazených termínů.

Lokální oprava přidává kontexty z OBSODLIS a potlačí běžné kontexty celého
pracoviště, pokud na daný den existuje objednávací výjimka. Zachovává
fallback při neobjednávacích výjimkách a izolaci dne/pracoviště.

Upravená funkce byla spuštěna samostatně přes stdin na hostu proti živému
Firebirdu, v read-only transakcích, bez přepsání souborů produkční aplikace.
První pokus odhalil nekompatibilní ORDER BY za UNION; po změně na ordinální
řazení proběhlo všech 24 historických kontrol bez přehlédnutého lékaře.
Důkaz: `empirical_calendar_candidate.json`; původní stav zůstává
v `empirical_calendar_observed.json`.

Čtyři nové regresní testy pokrývají běžný rozvrh, výjimku bez běžného
rozvrhu, neobjednávací výjimku a oddělení pracoviště/dne. Celá lokální
sada: 102 testů OK. SQLite testy samy neprokazují Firebird kompatibilitu;
tu pro tento dotaz potvrzuje uvedené přímé read-only spuštění.

Nadále zbývá porovnání API a frontendu, mapování vazeb a řízené zápisové
testy. Produkční aplikace ani data nebyly touto opravou změněny.

## Doplnění: incident 7. října a skutečné HTTP odpovědi

Důkaz `october_incident_current.json` pochází ze samostatného čtení API
a databází; nejde o atomický snapshot ani rekonstrukci času původního hovoru.

| Nabídnutý začátek prohlídky | MAIN lékař 12 | LASER skenový kalendář 5 |
| --- | --- | --- |
| 15:00 | interval 15:00–15:10 bez překryvu | sken 14:45–15:00 koliduje s 98683 |
| 15:10 | interval 15:10–15:20 bez překryvu | sken 14:55–15:10 koliduje s 98683 |
| 15:50 | interval 15:50–16:00 koliduje s 143677 od 15:55 | sken 15:35–15:50 koliduje s 98692 |

Aktuálně tedy neprojde žádná ze tří kombinovaných návštěv. Existující
anonymizovaný regresní případ oct7_combined odpovídá těmto překryvům;
jeho rozvrhové bloky jsou úmyslně syntetické výřezy a nejsou exportem
skutečného celodenního rozvrhu. Doplněn odkaz na skutečné důkazy.

Volání veřejné adresy ze serveru vrátila 403 a ne-JSON odpověď (17 bajtů).
Příčina síťového odmítnutí zatím nezjištěna; nelze tvrdit globální výpadek.
Přímé autentizované HTTP volání lokální aplikace na nakonfigurovaném portu:
- dermatoscope_first: 400, služba není aktuálně povolena pro nabídku;
- skin pro lékaře 12 dne 7. října: 200, nabídky 15:00–15:10 a 15:10–15:20;
- skin nenabízí konfliktní 15:50. Tyto dvě nabídky nevyžadují skener.

Produkční ochrana tedy dermatoskopii aktuálně odmítá; tuto odpověď nelze
vydávat za úspěšné ověření budoucího zapnutého hledání dermatoskopie.
UI ověření a ověření veřejné cesty z klientského prostředí zbývají.
