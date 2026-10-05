# Podklad a návrh pilotu v2

Aktuální podklad v1-review-2 (5. 10. 2026). API, Operator a ElevenLabs prompt
jsou nasazené v režimu schvalování personálem. Závěrečné hlasové přejímací
testy nejsou uzavřené. Čekající žádosti neblokují termíny; při schválení
se dostupnost ověřuje znovu. SMS nejsou součástí první verze.

- [PDF k tisku](../../output/pdf/Dermacentrum_pilot_v2_podklad_pro_schuzku.pdf)
- [Upravitelný text schůzky](podklad_pro_schuzku.md)
- [Konsolidovaný návrh ke schválení](konsolidovany_navrh.md)
- [Pokrytí všech 40 bodů inventáře](pokryti_inventare.md)
- [Ověření dokumentu](verification.json)
- [Stav celého cíle](stav_cile.md)

PDF obsahuje 18 konkrétních otázek, 24 pracovních kroků a kopírovatelný list
zpětné vazby. Otázky mají místa pro ruční odpovědi. Technické detaily jsou
v samostatném návrhu, nikoli v instrukcích pro recepci.

Generátor `tools/diagnostics/build_pilot_v2_review.py` běží pouze offline.
Používá Python/reportlab z Codex runtime, Arial pro českou diakritiku, obsah
zapsaný v generátoru a vytváří JSON, Markdown i PDF. Opětovné spuštění přepíše
generované soubory; klientské odpovědi ukládat do samostatného souboru nebo
nejprve začlenit do zdroje. Aktuální QA obrázky jsou v `tmp/pilot_v2_review/v1-review-2`.
