# Obnovení doručení požadavku na personál

Určeno správci hosta po instalaci v2 workeru. V produkci zatím není nasazeno.
Přístup chrání oprávnění ke konfiguračnímu souboru a SQLite adresáři;
příkaz není veřejný endpoint ani nástroj hlasového agenta.

Recovery funguje při `enable_durable_handoff: true` i bez zapnutého schvalování
rezervací. Vyžaduje existující store na absolutní cestě a nakonfigurovaný tenant;
stejnou konfiguraci musí používat API a doručovací worker.

1. V Operatoru podle hovoru ověřit, zda požadavek nebyl přijat navzdory timeoutu.
   Pokud nebyl, zajistit předání personálu při řešení delšího výpadku.
2. Odstranit příčinu nedostupnosti/autentizace, ověřit stav služby doručovacího
   workeru a jeho konfiguraci. Původní chybu nemažte ručně z SQLite.
3. Na Medicus hostu z kořene repozitáře vypsat selhané požadavky:

   ```powershell
   C:\python\python.exe scripts/handoff_recovery.py
   ```

4. Vybrat přesné ID ze seznamu a znovu zařadit pouze tento požadavek:

   ```powershell
   C:\python\python.exe scripts/handoff_recovery.py --retry handoff_ID_ZE_SEZNAMU
   ```

5. Ověřit v Operatoru příjem shrnutí a jeho stav vyřízení. Samotná odpověď
   `pending` z příkazu znamená pouze opětovné zařazení; musí běžet worker.

ID požadavku a jeho obsah se nemění. Pokud Operator první pokus již přijal,
je opakování deduplikované a znovu neotevře personálem vyřešený požadavek.
Přijaté, probíhající a cizímu tenantovi patřící položky příkaz odmítne.
Lokální audit zaznamená systémového uživatele, čas a počet minulých pokusů.
Původní failure alert zůstává zachován a pod stejným incidentem se neduplikuje;
správce po ručním obnovení sám ověří konečný výsledek.
