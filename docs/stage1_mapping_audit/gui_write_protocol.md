# Řízené ověření zápisu z Medicusu

Účel: prokázat, co skutečně dělá frontend při vytvoření, přesunu a zrušení.
Dosavadní čtení dat ani technický insert/rollback tento důkaz nenahrazují.

## Příprava společné session

1. Otevřít MAIN i LASER v Medicusu. Na místě ověřit určenou testovací kartu
   podle interní dokumentace `research/db-mapping/phase3_rollback_insert_test.md`;
   nepřenášet její osobní údaje do reportu. Potvrdit správnou kartu v každé
   databázi zvlášť, shodné IDPAC neprokazuje totožnost mezi databázemi.
2. Vybrat dva volné budoucí pracovní dny a konkrétní lékaře/časy. Zahrnout
   zdrojový i cílový den do všech snapshotů. Personál nesmí testovací slot
   zaměnit za skutečnou objednávku; rezervaci označit jako test dle praxe klienta.
3. Pro celou session nastavit na DB hostu stejný náhodný soukromý
   `MEDICUS_AUDIT_KEY` (alespoň 32 bajtů). Klíč neukládat do repa ani reportu.
   Je nutný pro porovnatelnost otisků; po session jej odstranit z prostředí.
4. Zapsat do protokolu datum, časy, lékaře, službu a popisky v UI. U snímků
   obrazovky skrýt ostatní pacienty. Technická ID termínů evidovat podle databáze.

## Pro každou variantu služby

Varianty: vyšetření bez skenu, sken a vyšetření, samotný sken, vyšetření po
dřívějším skenu, navazující kontrola po vyšetření/zákroku. Nejprve potvrdit
výběr skutečné položky v UI; nezaměňovat obchodní kategorii s číslem aktivity.

1. Zachytit **S0**: oba dny v obou databázích, UI a dostupnost našeho API.
2. Personál vytvoří rezervaci přes frontend, uloží a obnoví kalendář.
   Zachytit **S1**, porovnat S0→S1. U kombinované návštěvy zkontrolovat oba
   kalendáře a evidovat všechny vytvořené části, jejich aktivity a vazby.
3. Přes frontend přesunout na druhý zvolený den. Zachytit **S2**, porovnat
   S1→S2. Ověřit, zda se mění ID, zda starý termín uvolnil dostupnost a zda
   se přesunuly obě části návštěvy. Neodvozovat párování pouze z časové blízkosti.
4. Přes frontend zrušit rezervaci. Zachytit **S3**, porovnat S2→S3 a ověřit
   uvolnění obou zdrojů v UI i API. Zaznamenat, zda UI provádí odstranění,
   změnu stavu nebo jinou operaci; absence řádku ve vybraných dnech sama
   neprokazuje fyzické smazání.
5. Potvrdit úklid všech testovacích částí v obou kalendářích. Rozdíly způsobené
   souběžnou prací personálu vyřadit pouze s doložením, nikoli automaticky.

## Nástroj

Na DB hostu z kořene repozitáře:

```powershell
python tools/diagnostics/gui_write_evidence.py capture --date YYYY-MM-DD --date YYYY-MM-DD > S0.json
```

Po každé operaci zopakovat se stejnými daty a klíčem, změnit název výstupu.
Lokálně nebo na hostu:

```powershell
python tools/diagnostics/gui_write_evidence.py compare S0.json S1.json > S0-S1.json
```

Nástroj používá read-only transakce. Prohlíží všech 48 aktuálních sloupců
OBJOBJ; osobní a neznámá pole exportuje jen jako HMAC otisky. Výstupy stále
patří mezi omezeně přístupné auditní podklady, nejsou veřejným datasetem.
Vzniklé anonymizované regresní fixtures se mají vytvořit zvlášť.

## Meze důkazu

- Capture verze 2 pokrývá OBJOBJ a vybrané dny včetně rozsahu opakování,
  OBJHIST podle původního data termínu a OBJPROC navázané na zachycené objednávky
  nebo na historická IDOBJ v těchto dnech. Historie tak pomůže dohledat vazby
  i po zmizení objednávky z aktuálního kalendáře. Rozdíly historie a procedur
  jsou multiset přidaných/odebraných řádků; změna se projeví jako odebrání a přidání.
  Neprokazuje vedlejší změny jiných tabulek, triggerů ani externích systémů.
- MAIN a LASER mají samostatné konzistentní snapshoty, nikoli jednu společnou
  atomickou transakci. Časově blízké změny nejsou důkazem vazby.
- Srovnání všech polí upozorní na neznámý změněný sloupec. Jeho význam je
  nutné ověřit schématem, procedurami a konkrétní operací, nikoli uhodnout.
- Pro úplné schválení zápisové cesty doplnit analýzu triggerů a souvisejících
  tabulek podle zachycených změn a vazeb; tento nástroj je první část důkazu.
- Synchronizační tabulky, LOG/ZURNAL a podmíněné vazby PROPRI/COS_PAC stále
  nejsou součástí capture. Při GUI testu je podle přítomných vazeb ověřit zvlášť.
  Snapshot verze 2 není porovnatelný se starším snapshotem verze 1.
- Bez provedené frontendové session nelze variantu označit jako ověřenou.

## Záznam výsledku

Pro každou operaci: služba, zdrojový/cílový den, popisek UI, technická ID v MAIN
a LASER, změněné sloupce, důkaz propojení, odpověď API před/po, stav úklidu,
nejasnosti a závěr **potvrzeno / rozpor / chybí důkaz**.
