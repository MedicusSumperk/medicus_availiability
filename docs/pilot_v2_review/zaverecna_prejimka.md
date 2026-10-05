# Závěrečná přejímka V1 — 6. 10. 2026

Navazuje na celý původní cíl. Uživatel požaduje co nejméně kroků: zbývající
ověření provést ve třech společných blocích, neopakovat hotové testy ani
otevírat další izolované historické vzorky bez konkrétního chybějícího důkazu.
Cíl není dokončený a tento seznam neznamená zúžení jeho rozsahu.

## 1. Technická přejímka a GUI

| Oblast | Co už je doloženo | Co ještě chybí |
| --- | --- | --- |
| MAIN běžná prohlídka | GUI vytvoření/přesun/zrušení, srovnání dat a úklid (`gui_skin_cycle_20261005.json`) | Neopakovat |
| LASER sken | Anonymní GUI vytvoření/zrušení a obsazenost (`gui_scan_pair_20261005.json`) | Řízený GUI přesun se snímky před/po a úklidem; API přesun s GUI pozorováním není tentýž důkaz |
| Kombinovaná návštěva | API a staff HTTP vytvoření/přesun/zrušení, oba kalendáře, zachování ID a úklid (`release_gui_pair_cycle_20261005.json`) | Kanonický postup personálu a obchodní význam MAIN kategorie nejsou potvrzeny pouhým API testem; uvést jako otázku klientovi, ne jako empiricky ověřený fakt |
| Rozvrhy a obsazenost | Náhodné DB/procedurální vzorky; konkrétní GUI celodenní blokace, nulový interval, část historické výjimky a incident 7. října; 14 živých HTTP hledání pro 7 lékařů × 2 služby | GUI pokrytí není úplné. Případné doplnění vybrat podle chybějícího významu, ne dalším náhodným opakováním stejného případu |
| Opakování a ostatní kategorie | Výklad procedur a syntetické regrese; v dosavadním živém vzorku nebyl TYP 9/10 | Bez živého příkladu nelze tvrdit empirické potvrzení. Neověřené zápisové cesty pro další služby zůstávají předáním personálu |
| Operator | Nasazení, backendové testy a dřívější přihlášený staff průchod | Finální produkční UI: číslo/hledání, souhrn požadavku, žádná rezervace před schválením, konflikt a výsledek provedení. Browser tool opakovaně timeoutuje |
| Upozornění a Supabase | Migrace/view ověřeny; endpoint 401 bez klíče, 200/idle s klíčem; owner potvrdil minutový cron, 5 úspěšných běhů, správného příjemce, sent=1/pending=0 | Nový skutečný e-mail nebyl při poslední kontrole vyvolán; dřívější doručení potvrdil uživatel |

Všechny zápisové experimenty pouze v předem autorizovaném testovacím rozsahu.
Žádné Firebird DDL ani změny procedur/triggerů. Předchozí testovací záznamy
jsou uklizené. Skutečný překryv MAIN 144588/141243 se bez rozhodnutí personálu
nemění. Připravená oprava blokuje nulový interval i ve staff validaci a writeru.

## 2. Jedna společná session hlasových testů

Použít existující T01–T15 a testovací kartu, nikoli nové nezávislé scénáře.
V jedné session spojit objednání, požadavek na změnu/zrušení a předání personálu.
Po každém hovoru zaznamenat čas/reference a porovnat řeč, nástroje, Operator
a případný schválený DB výsledek. Pending požadavek není potvrzená rezervace.
Chyby vyvolávat pouze v řízeném testu, ne rozbitím produkčního spojení.
Poslední metadata kontrola po 20:00 UTC 5. října nenalezla nový kandidátní
hovor; absence záznamu sama nevylučuje chybu ingestu.

## 3. Opravy nálezů a předání

Provést pouze opravy nalezené v přejímce, odpovídající cílené regrese a ověření
nasazení. Předat stávající 11stránkové PDF (18 otázek, 24 pravidel, feedback),
verze nasazení a konkrétní neuzavřené významy mapování. Odpovědi klienta
přicházejí až po představení V1. Nejistotu označit výslovně; nepřepsat ji na
splněnou podmínku jen proto, že ostatní testy prošly.

Odkazy na důkazy v tabulce míří do `../stage1_mapping_audit/`; stav nasazení
je v `production_rollout_20261005.json`, celková historie v `stav_cile.md`.
