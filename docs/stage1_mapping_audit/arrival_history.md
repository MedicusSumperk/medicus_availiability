# Historie společných příchodů a dermatoskopie — 2026-10-01

Pouze Stage1, bez změny chování. Proveden git fetch origin --prune a prohledání
všech dostupných lokálních/remote refs pomocí git log --all (grep, -G a -S).
Nejde o prohledání smazaných větví, nedostupných PR nebo původních konverzací.

## Doložené změny

- `0e14995` Add production business rules config: původní arrival bucket15–16→15 je pouze pro service=skin.
- `d5e6c042719f2be7941b71ce7bc114ace2976fe5` (27.7.): oddělení technického času a sdělovaného labelu, deduplikace společných labelů, hledání nejbližšího termínu. Není to scan offset.
- `194c52f4772f153e3a48571cca319c17143feea8` (28.7.): přidává11–12→11 a denní odpolední buckety; všechny výslovně service=skin. Dopolední poznámka obsahuje Draft.
- `cc846e7e3c02dc0a77d491f9a861dffd52057b20` (31.7.): odděluje běžné kožní od dermatoskopie; přidává scan_before_minutes=15, scan_duration_minutes=15 a build_dermatoscope_options. Standardní scan_end=start_time lékaře, scan_start=scan_end−15. Nemění bucket service=skin na dermatoskopii.
- `c767598749d8b02aa8912eff1ed2990151ce040f` (31.7.): prompt/tools dokumentují zvlášť termín lékaře z start_time a příchod na scan ze scan_start_time; mají se zopakovat oba časy.

Kódová historie tedy potvrzuje individuální technický termín lékaře−15 pro
scan, nikoli odečtení15 od společného bucket labelu pro dermatoskopii. Současný
snapshot efektivní konfigurace rovněž obsahuje jen skin buckety. V dostupné
prohledané historii nebyla nalezena implementace dermatoskopického bucketu.
To není důkaz, že se o něm uživatel dříve nebavil; pouze že nalezený kód a
verzované dokumenty takové rozhodnutí nedokládají.

## Offline reprodukce současného mapování

Syntetický kontext: čtvrtek, idprac1,15min sloty11:15 a11:30, bez blockerů.
Volány build_dermatoscope_options a _apply_spoken_time s pravidly z repa.

| Služba | Technický čas lékaře | Sdělovaný label lékaře | Scan / příchod |
| --- | --- | --- | --- |
| dermatoscope_first |11:15|11:15|11:00–11:15|
| dermatoscope_first |11:30|11:30|11:15–11:30|
| skin |11:15|11:00|žádný|

Tento test nečte skutečnou obsazenost ani nepotvrzuje, že takové termíny jsou
volné; reprodukuje pouze transformaci časů. Neprovádí rezervaci. Původní
main-only write navíc scan rezervaci v LASER nevytvářel. Veřejná dermatoskopie
a zápisy zůstávají vypnuté dle dřívějšího containment stavu.

Uživatelský příklad11:15→11:00 odpovídá nalezenému offsetu, pokud11:15 znamená
termín u lékaře a11:00 scan/příchod. Ani správná rezervace negarantuje okamžité
skutečné zahájení provozu. Zda klinika chce i pro další dermatoskopické pacienty
společný příchod, nebo individuální čas scanu, zůstává provozní otázkou, kterou
uživatel slíbil upřesnit. Jeho hypotézu neoznačujeme za nové schválení pravidla.
