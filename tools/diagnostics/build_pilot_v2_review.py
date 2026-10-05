"""Build the client meeting packet from explicit review content, without API access."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs' / 'pilot_v2_review'
OUT.mkdir(parents=True, exist_ok=True)
PDF = ROOT / 'output' / 'pdf' / 'Dermacentrum_pilot_v2_podklad_pro_schuzku.pdf'
PDF.parent.mkdir(parents=True, exist_ok=True)

# q = ID, question, evidence requested, proposed default, source mapping
questions = [
('Sken a příchod pacienta', [
('Q01', 'Je běžný sken vždy na 15 minut a lékařská návštěva na jedno políčko jeho kalendáře?', 'Ukažte jedno 10minutové a jedno 15minutové políčko. Jak recepce pozná požadavek, který potřebuje delší čas, a komu ho předává?', 'Sken 15 minut, lékař jedno skutečné políčko. Nestandardní délku řeší personál. Prodloužení agent sám neposuzuje.', 'MAP-15/16/17/18'),
('Q02', 'Kdy přesně přicházejí první a další pacient na dermatoskopii ve společném bloku?', 'Příklad: lékařská políčka 11:15 a 11:30, společný příchod 11:00. Doplňte pro oba pacienty příchod, začátek skenu a prohlídku. Patří poslední políčko na hranici bloku ještě ke stejnému příchodu?', 'Sken musí předcházet prohlídce a dva skeny se nesmějí překrývat. Společný příchod není automaticky společný začátek skenů. Přesné rozložení před zapnutím této nabídky ověříme.', 'MAP-16/17/18/25'),
('Q03', 'Kdo po samostatném skenu domluví chybějící lékařskou prohlídku a jak řešíte dlouhý odstup?', 'Domluví ji recepce na místě, nebo má pacient znovu zavolat? Kdo rozhodne o prohlídce po více než třech měsících, přesně na hranici tří měsíců a po více než šesti měsících?', 'Samostatný sken jen na výslovnou žádost. Informovat o nutnosti prohlídky; nad tři měsíce předat personálu. Agent neslibuje, že pozdější termín již domluvil.', 'MAP-03/04'),
]),
('Co se zapisuje do kalendářů', [
('Q04', 'Kterou položku v Medicusu vybíráte pro každý ze čtyř typů návštěvy?', 'Ukažte běžnou prohlídku, sken s prohlídkou, prohlídku po dřívějším samotném skenu a kontrolu po vyšetření nebo zákroku. Jak odlišujete první a další sken při zápisu?', 'Obsah služeb je domluvený. Potřebujeme ukázku výběru v aplikaci, nikoli nové názvy služeb. Nejasný typ zápisu nepovolíme, dokud jej technicky nepřiřadíme.', 'MAP-02/03/04/05/09/22/28'),
('Q05', 'Který kalendář ukazuje všechnu obsazenost jediného dermatoskopu?', 'Ukažte také nepřítomnost obsluhy, servis přístroje a případné jiné místnosti. Stačí volné místo v kalendáři přístroje, nebo ještě kontrolujete další kalendář?', 'Volný musí být přístroj i navazující lékař. Pokud chybí informace o potřebném zdroji, agent termín nepotvrdí.', 'MAP-01/13/14/22/23'),
('Q06', 'Které dnešní kalendáře patří skutečně ordinujícím lékařům a které jsou pomocné?', 'Ukažte aktivní lékaře, duplicity a kalendáře recepce. U změny Filip Ferencz / Tamara Hrudová potvrďte, zda jde o převzetí kalendáře a zda se změnila pravidla objednání. Jaké přezdívky nebo zkrácená jména pacienti běžně používají?', 'Bez preference hledat napříč skutečnými ordinujícími lékaři. Aktuální jména vycházejí z databáze; pomocný účet není lékař.', 'MAP-10/11/12/37'),
]),
('Výjimky a změny rozvrhu', [
('Q07', 'Jak zadáváte dovolenou, mimořádnou ordinaci a střídání týdnů?', 'Ukažte den s běžnou ordinací a výjimkou a den s ordinací jen výjimečně. Ruší výjimka celý den, místnost, nebo jen část práce jednoho lékaře?', 'Nabídka musí odpovídat skutečnému rozvrhu včetně výjimek. O víkendech a svátcích se nenabízí ani při volném políčku.', 'MAP-19/20/21/27'),
('Q08', 'Které záznamy v kalendáři znamenají blokaci a nesmějí se nabídnout pacientovi?', 'Ukažte přestávku, celodenní blokaci, opakovanou událost a záznam bez běžného času konce. Jak vypadá zrušená událost? Změníte někdy jen jeden výskyt opakované události?', 'Žádný výkon nesmí zasáhnout do obsazenosti ani přestávky. Nejasnou blokaci nesmíme ignorovat. Výjimky řeší personál.', 'MAP-08/09/17/18/19/22/40'),
('Q09', 'Jak v Medicusu přesouváte a rušíte celou návštěvu se skenem a prohlídkou?', 'Ukažte oba původní záznamy a postup přesunu či zrušení. Poznáte jejich spojení přímo v aplikaci? Zůstává historie a odchází pacientovi zpráva? U opakované rezervace měníte jen jednu návštěvu, nebo celou řadu?', 'Agent změní sken i prohlídku jako celek. Změnu jen jedné části předá. Při neúspěšném přesunu musí zůstat původní návštěva zachovaná.', 'MAP-08/19/28/29/30/31/39'),
]),
('Pacient a termín kontroly', [
('Q10', 'Podle čeho v historii poznáte, že pacient sken nebo zákrok skutečně absolvoval?', 'Ukažte rozdíl mezi absolvovanou návštěvou, zrušenou návštěvou a nedostavením. Kde je doporučený odstup kontroly a kdo jej umí potvrdit?', 'Historie pomáhá určit datum. Samotné staré objednání nedokazuje absolvování. Neznámý interval kontroly upřesňuje personál; agent automaticky neurčuje jeden rok.', 'MAP-03/04/05/32'),
('Q11', 'Jak postupujete, když pacient má kartu v hlavním systému, ale v kalendáři pro sken jej nenajdete?', 'Ukažte, jak ověříte, že jde v obou systémech o stejného pacienta, a kdo doplní chybějící kartu. Co má personál dostat v předaném požadavku?', 'Agent nezakládá pacientské karty a nepoužije cizí kartu. Nejednoznačné spojení předá personálu.', 'MAP-01/32/33'),
('Q12', 'Vyhovuje pro kontrolu kolem doporučeného data následující krátké období?', 'Návrh: nejprve sedm dní před a sedm dní po cílovém datu. Pokud nic nenajdeme, nabídnout se souhlasem pacienta rozšíření nejvýše na patnáct dní před a po. Příklad: lékař doporučil kontrolu začátkem října, pacient může i koncem září.', 'Jde o návrh přesného rozsahu, nikoli již potvrzenou lhůtu. Výslovné omezení pacienta vždy platí; chybějící nebo nejasné doporučení předat personálu.', 'MAP-05/27'),
]),
('Předání hovoru a informace', [
('Q13', 'Co přesně má agent říci při akutním požadavku a kdy má předat personálu?', 'Klinický garant doplní schválenou větu pro naléhavý stav a doporučení tísňové pomoci. Recepce upřesní pohotovostní příchod, případné rezervování a postup mimo tuto dobu.', 'Agent nehodnotí diagnózu. Akutní požadavek klidně předá; ranní pohotovostní políčko běžně nenabízí. Konkrétní čas bez potvrzeného provozního pravidla neslibuje.', 'MAP-26/35'),
('Q14', 'Kam a v jakých hodinách se přepojuje a kdo vybírá zmeškané hovory?', 'Zapište cílové číslo, dostupné hodiny a zástup. Co mimo tuto dobu? Co když volající skryje číslo nebo potřebuje zpětný kontakt na jiné? U přesměrování z hlavního čísla ověříme, že se hovor nevrací k agentovi.', 'Při obsazení má následovat zpětné zavolání personálu. Neslibovat přesný čas. Funkci zmeškaných hovorů a zobrazení správného čísla ověříme telefonním testem.', 'MAP-35'),
('Q15', 'Jsou správné informace o pracovišti, které dnes agent sděluje?', 'Potvrďte Zábřežská 69/41, recepci 777 177 729, sken a laser 725 708 248, výsledky 734 420 966, info@laserstudio.cz, parkování a bezhotovostní platbu. Doplňte platné hodiny obou provozů, bezbariérovost a případný schválený ceník.', 'Agent sděluje jen potvrzené údaje. Ordinační hodiny nejsou nabídka volného termínu. Neznámou informaci a výsledky předá personálu.', 'MAP-35/37; dodaný prompt'),
]),
('Schvalování a odpovědnost personálu', [
('Q16', 'Kdo bude schvalovat žádosti o objednání, přesun a zrušení?', 'Zapište odpovědnou osobu nebo roli, zástup a dobu kontroly žádostí. Když se termín mezitím obsadí, kdo zavolá pacientovi pro nový výběr? Může personál žádost odmítnout s důvodem?', 'Agent přijme žádost k potvrzení personálem. Teprve schválení a úspěšné provedení vytvoří, přesune nebo zruší rezervaci. Bez schválení agent sám do kalendáře nezapisuje.', 'MAP-28/29/30/34/37/38/39; původní Stage 5'),
('Q17', 'Kdo kontroluje frontu v Operatoru a kdo dostane technické chyby?', 'Určete, kdo a jak často kontroluje nové požadavky v Operatoru, včetně zástupu. Potvrďte příjemce technických upozornění e-mailem a postup při jeho nepřítomnosti.', 'Požadavek se trvale uloží a zobrazí v Operatoru. SMS nejsou součástí první verze. Technické upozornění správci nenahrazuje vyřízení požadavku personálem. Rodné číslo do upozornění nepatří.', 'MAP-32/34/35; schválený rozsah verze 1'),
('Q18', 'Jak pacient dostane konečné potvrzení a kdo řeší žádost bez výsledku?', 'Výchozí postup: konečný výsledek oznamuje personál telefonicky. Určete očekávanou dobu vyřízení a odpovědnou osobu. Kdo kontaktuje pacienta, pokud se požadovaný termín mezitím obsadí?', 'Čekající žádost termín neblokuje. Personál má přednost; při schválení systém znovu ověří dostupnost. Při kolizi personál s pacientem vybere jiný termín. Při nejistém výsledku nejprve ověří stav zápisu, aby nevznikla duplicita.', 'MAP-34/35/39; schválený postup personál má přednost'),
]),
]

# Practical agreed rules; "Do ověření" and "Návrh" are intentionally visible.
rules = [
('Pracovní postup pro začátek hovoru', [
('R01 Zjistit skutečný požadavek', 'Krátce pozdravit a zjistit, co pacient potřebuje. Již sdělené údaje a preference znovu nevyžadovat. Nejasný požadavek krátce upřesnit.'),
('R02 Předat bez přesvědčování', 'Při výslovné žádosti o člověka ihned přepojit bez dalšího výslechu. U služby mimo rozsah zachovat původní požadavek a nabídnout personál; nenahrazovat jej nabídkou kožního vyšetření.'),
('R03 Rozlišit obsah návštěvy', 'Běžná prohlídka neobsahuje sken. Dermatoskopie běžně zahrnuje sken personálem a následnou prohlídku lékařem. Samostatná prohlídka po dřívějším skenu a kontrola po zákroku či vyšetření jsou odlišné požadavky.'),
('R04 Dodržet rozsah služeb', 'První verze přijímá ke schválení běžnou prohlídku a sken s prohlídkou. Kontrolu po zákroku či vyšetření a prohlídku po dřívějším skenu předává personálu do ověření jejich zápisu. Plazmu, laser, zákroky, výsledky a zdravotní rady řeší personál. Agent nezakládá karty.'),
('R05 Výjimečně jen sken', 'Samotný sken běžně nenabízet. Na výslovnou žádost jej v první verzi předat personálu. Upozornit na nutnost pozdější osobní prohlídky; neprohlašovat ji za domluvenou. Odstup nad tři měsíce posoudí personál.'),
('R06 Objednání za jinou osobu', 'Lze objednat, přesunout i zrušit návštěvu za dítě, partnera či jinou osobu. Vždy pracovat s kartou a návštěvou skutečného pacienta, nikoli automaticky s kartou majitele volajícího telefonu.'),
]),
('Pracovní postup pro hledání termínu', [
('R07 Zachovat preference', 'Zohlednit přání pacienta z celého hovoru. Bez preference lékaře hledat nejbližší vyhovující termíny napříč ordinujícími lékaři. Původního lékaře automaticky neupřednostňovat ani při přesunu nebo kontrole.'),
('R08 Hledat u vybraného lékaře', 'Nejprve hledat u požadovaného lékaře. Při neúspěchu rozšířit období nejvýše na šest měsíců, stále v mezích pacientova přání. Pokud termín není, nabídnout volbu jiného lékaře nebo personálu.'),
('R09 Počítat skutečný příchod', 'Časové omezení pacienta musí splnit už příchod na sken, ne pouze pozdější prohlídka. Nový termín má mít nejméně hodinu předstihu od zavolání. Nenabízet minulý příchod ani minulý sken.'),
('R10 Pracovní dny a svátky', 'Nabízet jen pondělí až pátek, mimo české svátky. Víkendový slot se nenabízí ani tehdy, když v systému vypadá volný. Běžně nenabízet ranní pohotovostní termíny před 08:00.'),
('R11 Společné příchody', 'Potvrzené časy příchodů jsou Po až Pá dopoledne 11:00; Po odpoledne 15:00; Út až Čt odpoledne 16:00; Pá odpoledne 14:00. Platí ve stanovených blocích, nikoli pro všechny návštěvy dne. Přesné začlenění skenu ověříme podle Q02.'),
('R12 Kontrola v doporučeném odstupu', 'V první verzi předat kontrolu personálu spolu s doporučeným odstupem sděleným pacientem. Zamýšlené hledání po ověření zápisu: krátké období kolem cílového data, i za rok a krátce před ním. Přesný rozsah určí Q12. Agent sám neurčuje roční interval.'),
]),
('Pracovní postup pro ověření a potvrzení', [
('R13 Ověřit správnou kartu', 'Standardně vyžádat jméno, příjmení a datum narození pacienta. Samotné telefonní číslo nestačí. Bez existující karty nelze vytvořit termín. Do ověření konkrétního výsledku nepotvrzovat, že je pacient dohledán.'),
('R14 Nenalezená karta', 'Zopakovat použité jméno, příjmení a datum narození. Po opravě hledání zopakovat. Pokud volající údaje potvrdí a karta není nalezena, nabídnout volbu dohledání podle celého rodného čísla nebo předání personálu. Nezacyklit dotazování.'),
('R15 Více shodných karet', 'Nabídnout volbu dohledat podle celého rodného čísla, nebo rovnou předat personálu. Rodné číslo není běžný povinný údaj. Pokud ani tato zvolená cesta nepomůže, návrh výchozího postupu je předání personálu.'),
('R16 Vybrat konkrétní návštěvu', 'Při více budoucích rezervacích zjistit, které se změna týká, a výslovně ji potvrdit. Nevybírat automaticky první nebo nejbližší. Běžnou dermatoskopii přesouvat či rušit jako celek; změnu jen skenu nebo jen prohlídky předat.'),
('R17 Stručně potvrdit požadavek', 'Před objednáním shrnout službu, lékaře, datum a příchod, u dermatoskopie jasně také sken. Počkat na výslovný souhlas. Při přesunu potvrdit původní i nový termín, při zrušení rušenou návštěvu.'),
('R18 Přijmout žádost ke schválení', 'V první verzi platí schválení personálem. Souhlas pacienta je souhlas s předáním konkrétní žádosti. Čekající žádost termín neblokuje ani nevytváří rezervaci. Agent smí potvrdit předání až po potvrzení přijetí systémem.'),
]),
('Pracovní postup pro změny a potíže', [
('R19 Změna těsně před návštěvou', 'Zrušení i přesun zatím přijímat bez časové hranice před původní návštěvou. Nový termín při přesunu musí znovu splnit podmínky dostupnosti a hodinového předstihu. Prošlé návštěvy nejsou tímto pravidlem povoleny ke změně.'),
('R20 Termín se mezitím obsadil', 'Personál má přednost. Při schválení systém znovu ověří dostupnost a známou kolizi nezapíše. Personál kontaktuje pacienta a domluví nový výběr; nesmí sám změnit lékaře či čas. Při neúspěšném přesunu zachovat původní rezervaci. Souběh se zápisem v Medicusu řeší personál.'),
('R21 Potvrdit jen skutečný výsledek', 'Čekající žádost, schválení a dokončený zápis jsou různé stavy. Objednání, přesun nebo zrušení označit za dokončené až po potvrzeném provedení. Výchozí postup: personál oznámí výsledek pacientovi telefonicky; upřesnění odpovědností viz Q18.'),
('R22 Technická chyba', 'Informovat volajícího o potížích, zaznamenat chybu i původní požadavek, upozornit správce a přesměrovat na personál. Kvůli chybě jednoduše neukončit hovor. Při nejasném výsledku změnu neoznačit za úspěšnou ani jistě neúspěšnou.'),
('R23 Personál nezvedá', 'Při obsazení či nezvednutí počítat se zpětným kontaktem podle zmeškaného hovoru. Zamýšlená hláška: „Omlouváme se, ale personál je momentálně zaneprázdněn. Zavolá vám, jakmile to bude možné.“ Zda může zaznít po přepojení, ověříme testem.'),
('R24 Selže i přesměrování', 'Zachovat požadavek pro personál a oznámit technickou chybu správci. Je-li agent stále na lince, omluvit se a informovat o následném kontaktu, jehož podklad se skutečně uložil. Neslibovat konkrétní čas zpětného zavolání.'),
]),
]

content={'version':'v1-review-2','status':'podklad k nasazené první verzi; hlasové přejímací testy a uvedené provozní otázky zůstávají k ověření','questions':questions,'rules':rules}
(OUT/'meeting_content.json').write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Dermacentrum Šumperk\n\nPodklad pro osobní projednání pilotu v2\n',
'Nejprve představte první verzi podle pracovních postupů R01 až R24 a vyzkoušejte společný hovor. Potom doplňte odpovědi Q01 až Q18 pro další úpravy. API, Operator a prompt jsou nasazené; hlasové přejímací testy ještě nejsou uzavřené. Zamýšlené rozšíření a neověřené chování jsou výslovně označené.\n',
'Datum schůzky: ____________________  Účastníci: ____________________\n']
for title,qs in questions:
 md.append('## '+title+'\n')
 for id,q,example,default,source in qs:
  md.append(f'### {id} {q}\n\n{example}\n\nPracovní návrh: {default}\n\nOdpověď a odpovědná osoba:\n\n____________________________________________________________\n\n____________________________________________________________\n')
md.append('# Pracovní pravidla první verze agenta\n')
for title,rs in rules:
 md.append('## '+title+'\n')
 for id,body in rs: md.append(f'### {id}\n\n{body}\n\nSouhlas / změnit: ____________________\n')
(OUT/'podklad_pro_schuzku.md').write_text('\n'.join(md),encoding='utf-8')

fontdir=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Body',str(fontdir/'arial.ttf')))
pdfmetrics.registerFont(TTFont('Bold',str(fontdir/'arialbd.ttf')))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
W,H=595.276,841.89
c=canvas.Canvas(str(PDF),pagesize=(W,H))
c.setTitle('Dermacentrum Šumperk Podklad pro schůzku k pilotu v2')
c.setAuthor('Dermacentrum pilot v2')
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=10.4,leading=14.4,spaceAfter=6),
 'small':ParagraphStyle('small',fontName='Body',fontSize=9,leading=12.3,textColor=HexColor('#444444')),
 'q':ParagraphStyle('q',fontName='Bold',fontSize=11.5,leading=15.2),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=21,leading=25),
}
page=0
def text(txt,y,style='body',x=44,width=W-88):
 para=Paragraph(escape(txt),styles[style]); _,h=para.wrap(width,H)
 if y-h<43: raise ValueError(f'Page overflow {page}: {txt[:45]} at {y-h}')
 para.drawOn(c,x,y-h); return y-h
def begin(section,title):
 global page
 page+=1
 c.setFillColor(HexColor('#000000'))
 text('DERMACENTRUM ŠUMPERK  /  PILOT V2',H-30,'small')
 y=text(title,H-60,'title')-12
 y=text(section,y,'small')-17
 return y
def end():
 c.setFont('Body',9); c.setFillColor(HexColor('#444444'))
 c.drawString(44,22,'Verze 1  /  5. 10. 2026  /  Hlasové přejímací testy zbývají')
 c.setFont('Body',9); c.drawRightString(W-44,22,str(page)); c.showPage()
for idx,(title,qs) in enumerate(questions):
 y=begin('Otázky pro klienta  /  '+str(idx+1)+' ze 6',title)
 if idx==0:
  y=text('Nejprve představte verzi 1 podle stran 7 až 10 a otestujte hovor. Potom upřesněte otázky pro další úpravy. API, Operator a prompt jsou nasazené; hlasové přejímací testy zbývají.',y)-8
  y=text('Datum: __________________   Účastníci: __________________',y,'small')-18
 for id,q,example,default,source in qs:
  y=text(id+'  '+q,y,'q')-7
  y=text(example,y)-6
  y=text('Pracovní návrh: '+default,y,'small')-17
  for _ in range(2):
   c.setStrokeColor(HexColor('#BBBBBB')); c.setLineWidth(.45); c.line(44,y,W-44,y); y-=20
  y-=12
 end()
for idx,(title,rs) in enumerate(rules):
 y=begin('Pracovní pravidla  /  '+str(idx+1)+' ze 4',title)
 for name,body in rs:
  y=text(name,y,'q')-5
  y=text(body,y)-7
  y=text('Souhlas / změnit: __________________________________________',y,'small')-17
 end()
y=begin('Záznam zpětné vazby  /  kopírujte pro každý testovací hovor','Ověření agenta s klientem')
y=text('Scénář: _____________________   Datum a čas: __________________',y)-9
y=text('Číslo hovoru nebo odkaz v Operatoru: __________________________',y)-14
y=text('Použijte domluvenou testovací kartu. Do tohoto listu nepište rodné číslo ani jiné citlivé údaje pacienta.',y,'small')-20
for heading,body in [
('Zadání volajícího','Co chtěl pacient vyřešit a jaká omezení uvedl?'),
('Očekávaný postup','Jak měl agent reagovat, jaký příchod nabídnout nebo kdy předat?'),
('Skutečný výsledek','Co řekl a udělal? U chybného termínu zapište datum, příchod, lékaře a kde byla kolize.'),
('Hodnocení a oprava','Správně / chybný termín / zbytečné dotazování / pozdní předání / chybný zápis / jiná chyba. Co přesně změnit?'),
]:
 y=text(heading,y,'q')-5; y=text(body,y,'small')-17
 for _ in range(2):
  c.setStrokeColor(HexColor('#BBBBBB')); c.line(44,y,W-44,y); y-=22
 y-=14
y=text('Zaznamenal: __________________  Vyřeší: __________________',y,'small')-12
y=text('Po opravě ověřeno dne: ______________  Výsledek: ______________',y,'small')
end(); c.save()
print(json.dumps({'pdf':str(PDF),'pages':page,'questions':sum(len(q) for _,q in questions),'rules':sum(len(r) for _,r in rules)},ensure_ascii=True))
