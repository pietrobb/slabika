# Pravidlá rozdeľovania slov a súvisiace slabičné hranice

Tento dokument je pracovná referencia projektu **slabika**. Vlastnými slovami
zhŕňa pravidlá, podľa ktorých sa v spisovnej slovenčine vyberajú miesta na
rozdelenie slova na konci riadka. Vychádza najmä z kapitoly **V. Rozdeľovanie
slov** v *Pravidlách slovenského pravopisu* (PSP); súvisiaci spôsob používania
spojovníka opisuje aj kapitola **VIII. Interpunkcia**, časť **Spojovník**.

Nejde o citáciu, úplnú teóriu fonologického slabikovania ani o náhradu
kodifikačnej príručky. Je to samostatne formulovaná technická interpretácia
určená na návrh algoritmu, testov a kontrolu výsledkov. Pri pochybnostiach je
rozhodujúce znenie PSP.

V príkladoch označuje zvislá čiara `|` abstraktnú hranicu, na ktorej možno slovo
zalomiť. Nie je súčasťou slova ani výslednej sadzby. Znak `-` v ukážke celého
slova označuje skutočný spojovník; pri zápise `v-` alebo `-ný` iba tradične
naznačuje otvorenú stranu morfémy.

## 1. Dva rozdielne výsledky

Treba rozlišovať:

- **slabikovanie** — zvukové členenie vysloveného slova na slabiky;
- **rozdeľovanie slova** — výber typograficky prípustného miesta, na ktorom sa
  môže slovo preniesť na ďalší riadok.

Tieto výsledky sa často zhodujú, ale nie sú totožné. Pri typografickom delení sa
okrem zvukovej stavby rešpektuje aj stavba slova z významových častí a
čitateľnosť oboch vzniknutých úsekov.

PSP nie sú úplným opisom slovenskej fonotaktiky. Pre rozdeľovanie slov uvádzajú
dva rovnocenné základy:

1. hranice morfém, teda významových častí slova;
2. hranice slabík, teda zvukových a rytmických jednotiek.

PSP neurčujú, že jeden z týchto základov musí algoritmus vždy vypočítať pred
druhým. Oddelenie fonologického výsledku od typografických bodov je architektúra
tohto projektu, nie ďalšie pravidlo PSP.

## 2. Základné obmedzenie

Na konci riadka možno rozdeliť iba viacslabičné slovo. Jednoslabičné slovo sa
nedelí ani vtedy, keď je dlhé alebo obsahuje slabikotvorné `r`, `ŕ`, `l` či `ĺ`.

Počet slabík sa preto nemôže určovať iba počtom napísaných samohlások. Jadro
slabiky môže tvoriť:

- samohláska;
- dvojhláska;
- slabikotvorné `r`, `ŕ`, `l` alebo `ĺ`.

### 2.1 Projektové pravidlo: `r`, `ŕ`, `l`, `ĺ` medzi dvoma spoluhláskami

V domácich a zdomácnených slovách je `r`, `ŕ`, `l` alebo `ĺ` medzi dvoma
spoluhláskami vždy slabikotvorné, teda tvorí jadro samostatnej slabiky:
`vl|na`, `ja|bl|ko`, `po|ho|dl|ný` (nie `po|hodl|ný`), `ne|po|ho|dl|ný`,
`zdr|ve|ný`. Nejde o variant ani o otázku odhadu výslovnosti; skupina `dl` v
`pohodlný` sa teda nepočíta ako dve spoluhlásky pred `n`, ale ako slabika `dl`.

Pôvod pravidla: PSP ho výslovne takto neformulujú. Projekt ho odvodzuje z
týchto podkladov:

- PSP pokladajú slová `vlk`, `prst`, `tŕň`, `tĺk` za jednoslabičné, takže
  `r`/`l` medzi spoluhláskami v nich tvorí jadro slabiky;
- všetky príklady PSP so slabičným `r`, `l`, `ŕ`, `ĺ` ako jadrom majú túto
  hlásku medzi dvoma spoluhláskami (`vl-na`, `vr-tieť`, `vŕ-ba`, `Sĺ-ňa-va`,
  `prch-ký`, `mĺk-vy`, `chrb-tami`) a PSP neuvádzajú nijaký opačný príklad;
- implementácia projektu toto pravidlo uplatňuje od začiatku
  (`obr|ne|ný`, `po|dl|ho|vas|tý`, `ja|bl|ko|vý`);
- slepý AI audit ukázal, že bez výslovného pravidla modely o slabičnosti
  hádali a pri tvaroch `pohodlného` a `najpohodlnejšej` dospeli k opačným
  dohodám. Operátor potom rozhodol, že správne je `po|ho|dl|né|ho`, a pravidlo
  sa preto zapísalo výslovne.

## 3. Delenie na hranici morfém

Ak je stavba slova jasná, hranica jeho významových častí je prípustným miestom
delenia. Takýto bod pomáha čitateľovi rozpoznať slovo aj po prenesení medzi dva
riadky.

### 3.1 Predpony

Slabičná predpona sa oddeľuje od základu, napríklad `pre|písať`, `vy|brať`,
`proti|hráč` alebo `nad|priemerný`.

Vokalizovaná podoba predpony sa oddeľuje celá, aj so svojím `-o-`, napríklad
`odo|brať`, `predo|strieť`, `zo|stúpiť` alebo `vzo|prieť sa`. Ak sa však základ
začína samohláskou, predpona zostáva nevokalizovaná a oddeľuje sa bez nej, napr.
`roz|ísť sa`.

Začiatok základu za predponou sa v preferovanom delení posudzuje ako začiatok
slova (§6.2). Ak sa základ začína jednopísmenovou samohláskovou slabikou, bod
hneď za ňou do preferovaného delenia nepatrí: `ne|omyl|ná`, `ne|od|išiel`,
`naj|ne|otra|si|teľ|nej|šej`, `ne|ukla|da|jú`; `ne|o|myl|ná` iba v mimoriadne
úzkej sadzbe. Na prvom riadku by inak zostalo `neo-`, ktoré čitateľ ľahko
prečíta ako prvú časť zloženiny `neo-` (ako v `neo|klasicizmus`), hoci ide o
zápornú predponu `ne-` a základ `omylná`. Pôvod: rozhodnutie operátora z 5. 9.
2026 (verdikt 2: bod za samohláskou po predpone je kontextový, nie preferovaný),
pri rules r3 doplnené výslovne, lebo slepý AI audit (prompt v5) takéto body
zaraďoval do preferovaného delenia.

Výnimkou je rodina `záujem`: `zá|u|jem`, `za|u|jí|mať`, `za|u|jí|ma|vý`,
`za|u|jať`, `ne|za|u|ja|tý` (rozhodnutie operátora 2026-10-01). Ak za `u`
nasleduje skupina spoluhlások, delí sa ako doteraz: `zá|uj|my`, `za|uj|me`.

Z toho istého dôvodu sa nedelí skupina spoluhlások na začiatku základu za
predponou, rovnako ako by sa nedelila na začiatku slova. Platí to aj vtedy, keď
bod na hranici predpony blokuje §6.2 (jednopísmenová predpona `u-`, `o-`,
`i-`): delenie sa vtedy nepresúva dovnútra skupiny. Preferované je `ustá|lil`,
nie `us|tá|lil`; `otrá|ve|ný`, nie `ot|rá|ve|ný`; `usmer|ňo|vať`, `uškŕ|ňa`,
`osla|bu|jem`, `ovplyv|ňu|júc`; `ihrá` (`i|hrať`) sa nedelí vôbec. Pri dlhšej
predpone sa delí na jej hranici: `prí|stro|ji`, nie `prís|tro|ji`. Pôvod:
rozhodnutie operátora z 1. 10. 2026 po slepom audite blind1000 (prompt v5),
v ktorom engine aj AI delili takéto skupiny nekonzistentne.

Samostatne sa však neoddeľujú neslabičné predpony `v-`, `s-`/`z-` a `vz-`.
Samotná spoluhláska teda nemá zostať na konci riadka ako prvá časť slova.

### 3.2 Slovotvorné prípony

Od slovotvorného základu sa oddeľuje prípona začínajúca spoluhláskou alebo
spoluhláskovou skupinou, napríklad `staviteľ|ský`, `rybár|stvo` alebo
`robot|ník`. Rozhodujúca je skutočná morfematická stavba, nie iba náhodná zhoda
písmen s bežnou príponou.

### 3.3 Gramatické prípony

Od základu sa oddeľuje aj pádová alebo osobná prípona začínajúca spoluhláskou,
napríklad v tvaroch typu `chlap|mi`, `pracuj|me` či `urob|te`.

### 3.4 Zložené slová

Zloženina sa delí na hranici svojich častí, napríklad `troj|uholník`,
`viac|účelový` alebo `video|hovor`. Spájacia samohláska zostáva s prvou časťou
zloženiny, napríklad `vodo|vod`.

Ak sa druhá časť zloženiny začína samohláskou, táto samohláska sa nepripája k
prvej časti. Slovo sa delí na hranici zloženia: `stredo|americký`, nie
`stredoa|merický`; `stredo|ázijský`, `stredo|európsky`; `auto|elektrikár`, nie
`autoe|lektrikár`.

Začiatok druhej časti sa v preferovanom delení posudzuje ako začiatok slova
(§6.2). Bod hneď za jej začiatočnou jednopísmenovou slabikou preto do
preferovaného delenia nepatrí, ani keď je bod na hranici zloženia zároveň
použitý: `au|to|elek|tri|kár|mi`, nie `au|to|e|lek|tri|kár|mi`. Na prvom riadku
by inak zostalo `autoe-` alebo by medzi dvoma bodmi zostala osamotená
samohláska, čo je pre čitateľa horšie, než keď celá časť `elektrikár` prejde na
nový riadok. Rovnako ako pri §6.2 ide o predvolené správanie; v mimoriadne úzkej
sadzbe ho môže konkrétny layout uvoľniť.

Pôvod pravidla: PSP, kapitola V, posledný odsek: „V zložených slovách podľa
možnosti prvú samohlásku z druhej časti nepripájame k prvej časti, ale slová
rozdeľujeme na rozhraní medzi obidvoma časťami, napr. stredo-americký,
stredo-ázijský. Dodržiavanie rozhrania medzi prvou a druhou časťou zložených
slov umožňuje lepšie čítať rozdelené slová.“ Príklad `americký` zároveň
zodpovedá príkladu PSP `a-merický` pri ochrane začiatočnej slabiky. Slovné
spojenie „podľa možnosti“ projekt číta ako pokyn pre preferované delenie, nie
ako prípustnosť bodu `autoe|`. Do pravidiel sa to zapísalo výslovne, lebo
skoršie znenie tohto paragrafu bolo mäkšie a v slepom AI audite (beh
`blind1000-20260930`) jeden model trval na `au·to·e·lek·tri·kár·mi` s
odôvodnením, že paragraf rieši iba samotný šev zloženiny. Operátor potvrdil
`au·to·elek·tri·kár·mi`.

Ak sa prvá časť zloženiny končí samohláskou, ktorá s predchádzajúcou
samohláskou tvorí hiát (`bio-`, `geo-`, `teo-`, `video-`, `choreo-`,
`biblio-`, `rádio-`, `zoo-`), prvá časť zostáva v preferovanom delení celá. Hiátový bod
vnútri nej je prípustný, ale menej vhodný, rovnako ako bod za jednopísmenovou
začiatočnou slabikou (§6.2): `bio|lóg|mi`, `teo|ló|gia`, `geo|met|ria`,
`zoo|lóg`, `vi|deo|po|ži|čov|ňa`; `bi|o|lóg|mi` iba v mimoriadne úzkej sadzbe.
`zoo-` doplnil operátor 2026-10-01 po AI kontrole (`zoo·lóg`, nie `zo·o·lóg`). Pravidlo sa
týka iba časti zloženiny, ktorá stojí na začiatku slova. Za predponou alebo inou
časťou zloženiny platia oba body (operátor 2026-10-01): `an|ti|bi|o|ti|ka|mi`,
`an|ti|zo|o|lo|gič|ky`, `pred|ge|o|lo|gic|kých`, `mik|ro|bi|o|lóg`. Hiát pred príponou (`ak|ci|o|nár`, `si|tu|á|cia`) ani
hiát vnútri koreňa bez hranice zloženia (`ar|che|o|lóg`, `pi|o|nier`) sa ním
neoslabuje.

Pôvod pravidla: projektový výklad, nie doslovné znenie PSP. PSP hiátový bod
výslovne povoľujú (kap. V, bod 2d, `pi-onier`) a zároveň pri zloženinách
uvádzajú delenie na rozhraní `teo-lógia`, `geo-metria` s odôvodnením, že
rozhranie „umožňuje lepšie čítať rozdelené slová“. Pri `bi-ológmi` sa začiatok
`bio` roztrhne a na druhom riadku zostane `ológmi`. Do 2026-10-01 projekt
držal oba body ako rovnocenné (`te·o·ló·gia`, rozhodnutie z 2026-09-05 po AI
audite `ar·che·o·lóg`). Operátor to zmenil v pravidlách r3 po otázke
`bi·o·lóg·mi` v slepom AI audite.

### 3.5 Nejasná alebo dvojako vnímateľná stavba

Ak morfematickú hranicu nemožno spoľahlivo určiť alebo ju bežný používateľ
nemusí vnímať, prednosť dostáva slabičné delenie. PSP (kap. V, bod 1,
Poznámka 1) to formulujú doslova takto:

> „Ak morfematické členenie slov nie je dostatočne zreteľné alebo si ho
> neuvedomujeme, dávame prednosť slabičnému deleniu (deleniu na rozhraní
> slabík), napr. nav-štíviť, príj-mu (tvar podst. mena príjem), náj-mu (tvar
> podst. mena nájom).“

Toto pravidlo nie je výnimka z delenia na hranici predpony, ale jeho súčasť:
predpona sa oddeľuje iba tam, kde je stavba slova zreteľná. Príklady PSP sa
týkajú celých slovných rodín, takže rovnako ako `príj|mu` a `náj|mu` sa delia aj
tvary so základom `-jm-`: `prij|me|te`, `ne|prij|me`, `naj|mem`, `uj|me`,
`za|uj|me`, `zá|uj|my`, `obj|me`. Pri slovese `prijať` je medzi samohláskami
jediná spoluhláska, preto `pri|jať` (§4.1).

Samotná skutočnosť, že základ samostatne nežije, ešte neznamená nezreteľnú
stavbu: PSP v tej istej kapitole uvádzajú `za-mknúť` s oddelenou predponou.

Okrem toho PSP výslovne pripúšťajú varianty najmä v troch situáciách:

- základ sa končí samohláskou a prípona sa začína skupinou spoluhlások, napr.
  `lieta|dlo` aj `lietad|lo`;
- prídavné meno na `-ný` vzniklo z prevzatého slova na `-cia` a pri odvodení sa
  `c` zmenilo na `č`, napr. `funkč|ný` aj `funk|čný`;
- hranica v spoluhláskovej skupine nie je jednoznačná, napr. `fun|kcia` aj
  `funk|cia`.

Algoritmus teda nemá každú zhodu so známou predponou či príponou automaticky
pokladať za morfematický švík. Pri variantnom pravidle sú kodifikované oba
uvedené výsledky.

## 4. Delenie podľa slabík

Nasledujúce pravidlá sa použijú tam, kde nerozhodne zreteľná morfematická
hranica. Za jadro sa v tomto prehľade považuje samohláska, dvojhláska alebo
slabikotvorná spoluhláska.

### 4.1 Jedna spoluhláska medzi jadrami

Ak je medzi dvoma slabičnými jadrami jediná spoluhláska, patrí k nasledujúcej
slabike. Deliaci bod je pred ňou: `že|na`, `bie|ly`, `vl|na`.

### 4.2 Dve spoluhlásky medzi jadrami

Ak sú medzi jadrami dve spoluhlásky, deliaci bod leží medzi nimi: `lás|ka`,
`mas|lo`, `všet|ci`.

### 4.3 Tri alebo viac spoluhlások medzi jadrami

Ak skupina najmenej troch spoluhlások neobsahuje rozpoznanú morfematickú
hranicu, prvá spoluhláska zostáva s predchádzajúcou slabikou a všetky ostatné
prechádzajú k nasledujúcej: `ses|tra`, `pas|tva`, `zaj|tra`.

PSP pri tomto pravidle neurčujú ďalšiu podmienku podľa toho, či sa zvyškom
skupiny môže začínať slovenské slovo, ani neposúvajú deliaci bod doprava podľa
fonotaktiky. Ak je hranica v skupine nejasná, uplatní sa variantné pravidlo z
časti 3.5; napríklad prípustné sú oba body `fun|kcia` aj `funk|cia`, pričom PSP
jeden z nich neurčujú ako predvolený.

### 4.4 Dve susediace samohlásky

Deliť možno medzi samohláskami, iba ak patria do dvoch rôznych slabík, napríklad
v slovách typu `ide|ál`, `ritu|ál` alebo `po|užiť`. Samotné susedstvo dvoch
samohláskových písmen nestačí: najprv treba rozhodnúť, či nejde o dvojhlásku
alebo o cudziu grafickú skupinu vyslovovanú ako jeden celok.

## 5. Celky, ktoré sa nesmú roztrhnúť

### 5.1 Slovenské zložky `ch`, `dz`, `dž`

Keď `ch`, `dz` alebo `dž` označuje jednu hlásku, obe písmená zostávajú spolu:
`rú|cho`, `me|dza`, `há|džem`.

Na hranici morfém však rovnaké písmená môžu predstavovať dve samostatné hlásky.
Vtedy je delenie medzi nimi prípustné, napríklad `viac|hlasný`, `od|zemok` alebo
`od|žať`.

### 5.2 Dvojhlásky `ia`, `ie`, `iu`

V domácich a zdomácnených slovách sa písmená tvoriace dvojhlásku nerozdeľujú:
`čia|ra`, `bie|ly`, `cu|dziu`.

V prevzatých slovách alebo na morfematickom švíku môžu rovnaké písmená patriť
do rozdielnych slabík. Rozhoduje výslovnosť a stavba konkrétneho slova, nie
samotný reťazec `ia`, `ie` alebo `iu`.

### 5.3 Prepisové `io`

Skupina `io`, ktorá v slovenskom prepise z azbuky zastupuje jeden celok, sa
nerozdeľuje. Toto pravidlo sa nevzťahuje mechanicky na každé `io` v ľubovoľnom
slove.

### 5.4 Cudzie grafické skupiny

V slove cudzieho pôvodu sa nesmie roztrhnúť skupina písmen, ktorá v príslušnej
výslovnosti označuje jedinú samohlásku alebo spoluhlásku. Platí to aj pre
prevzaté všeobecné slová, nielen pre cudzie mená. Rovnako sa zachovávajú
samohláskové skupiny vyslovované ako jedna slabika, napríklad `leu|kémia`.
Slovenské pravidlá preto nemožno aplikovať na cudzie písanie bez znalosti jeho
výslovnosti.

Pri dvoch rovnakých spoluhláskových písmenách, ktoré spolu označujú jednu
spoluhlásku, PSP pripúšťajú v niektorých tvaroch delenie medzi nimi, ak za
skupinou nasleduje samohláska. Ide o osobitný prípad závislý od cudzej
výslovnosti, nie o všeobecné pravidlo pre zdvojené písmená.

## 6. Ochrana krátkych okrajových slabík

### 6.1 Koniec slova

Na nasledujúci riadok sa nesmie oddeliť koncová slabika tvorená iba jediným
samohláskovým písmenom. Deliaci bod, po ktorom by na druhom riadku zostalo iba
jedno písmeno, je vždy neprípustný.

### 6.2 Začiatok slova

Začiatočná slabika tvorená jediným samohláskovým písmenom sa zvyčajne
neoddeľuje. PSP pripúšťajú výnimku v mimoriadne úzkej sadzbe, napríklad v úzkom
novinovom stĺpci.

Pre všeobecné API bez informácie o šírke sadzby je bezpečným predvoleným
správaním takýto deliaci bod neponúknuť. Aplikácia, ktorá pozná konkrétny layout,
ho môže povoliť osobitnou typografickou politikou.

## 7. Slová, ktoré už obsahujú spojovník

Spojovník je kratší než pomlčka a píše sa bez okolitých medzier. Ak je súčasťou
slova alebo názvu, nie je totožný so znamienkom vloženým iba pre zalomenie
riadka.

Ak sa slovo rozdelí presne na mieste svojho pôvodného spojovníka, spojovník sa
zobrazí na oboch riadkoch: raz za prvou časťou a znova pred druhou časťou. Napr.
`slovensko-český` sa pri takom zalomení vysádza ako `slovensko-` na prvom a
`-český` na druhom riadku. Ak spojovník v pôvodnom slove nebol, na začiatku
druhého riadka sa neopakuje.

Táto požiadavka patrí do vrstvy sadzby. Funkcia vracajúca iba číselné deliace
body musí vedieť odlíšiť pôvodný spojovník od nového bodu vloženého na konci
riadka alebo ponechať jeho vykreslenie volajúcej aplikácii.

## 8. Poradie rozhodovania pre implementáciu

Pre jeden kandidátsky deliaci bod je praktické použiť toto poradie:

1. Určiť hláskové a slabičné jadrá; rozpoznať slovenské aj relevantné cudzie
   nedeliteľné grafické celky.
2. Vylúčiť jednoslabičné slovo.
3. Nájsť dôveryhodné hranice predpôn, prípon a častí zloženín.
4. Na ostatných miestach odvodiť hranice podľa počtu spoluhlások medzi
   slabičnými jadrami a podľa skutočného hiátu medzi samohláskami.
5. Odstrániť body, ktoré roztrhnú jednu hlásku, dvojhlásku alebo cudziu
   jednoslabičnú grafickú skupinu; osobitne posúdiť povolený prípad dvoch
   rovnakých cudzích spoluhláskových písmen pred samohláskou.
6. Odstrániť bod pred jednopísmenovou koncovou slabikou.
7. Predvolene odstrániť bod za jednopísmenovou začiatočnou slabikou, a to aj
   na začiatku základu za predponou (§3.1, `ne|omyl|ná`) a na začiatku druhej
   časti zloženiny (§3.4), a hiátový bod vnútri prvej časti
   zloženiny (§3.4, `bio|lóg`).
8. Pri pôvodnom spojovníku odovzdať sadzbe informáciu, že ho treba na ďalšom
   riadku zopakovať.

Morfematické pravidlá nesmú byť iba zoznamom reťazcových prefixov a suffixov.
Falošne rozpoznaná morféma môže vytvoriť deliaci bod, ktorý nezodpovedá ani
významovej stavbe, ani výslovnosti slova.

## 9. Normatívna sila pravidiel

Pre testovanie je užitočné rozlíšiť tri úrovne:

- **základné:** nedeliť jednoslabičné slová; deliť na zreteľných hraniciach
  morfém alebo podľa pravidiel slabičnej stavby; neroztrhnúť dvojhlásku ani
  grafickú skupinu označujúcu jednu hlásku; neoddeliť jednopísmenovú koncovú
  slabiku;
- **variantné:** použiť morfematický alebo slabičný bod v troch prípadoch
  opísaných v časti 3.5 a osobitne posúdiť cudzie zdvojené spoluhláskové
  písmená;
- **kontextové:** spravidla neoddeľovať jednopísmenovú začiatočnú slabiku, no
  pripustiť ju v mimoriadne úzkej sadzbe.

Z toho vyplýva, že referenčné dáta môžu pri niektorých slovách obsahovať viac
než jeden prípustný výsledok. Test by v takom prípade nemal bez ďalšieho dôvodu
vyhlásiť jeden kodifikovaný variant za jediný správny.

### 9.1 Mapovanie na výstupy enginu a Liangove vzory

Aktuálne API vracia predvolene iba preferovanú úroveň. Napríklad
`hyphenate("všeobecne")` dá `vše·obec·ne`. Volanie s `contextual=True` pridá aj
prípustný, ale nepreferovaný slabičný bod `všeo|becne`, takže výsledkom je
`vše·o·bec·ne`. Parameter `all_points=True` osobitne pridáva rovnocenné varianty
kodifikované v časti 3.5.

Projekt preto zverejňuje dva pracovné Liangove súbory. Predvolený
`patterns/hyph-sk-slabika.tex` sa učí z preferovaných bodov volania
`break_points(word)`. Súbor `patterns/hyph-sk-slabika-permissive.tex` sa učí zo
zjednotenia všetkých troch úrovní cez
`break_points(word, all_points=True, contextual=True)` a je určený pre úzku
sadzbu. Bežný formát Liangových vzorov nevie zachovať prioritu medzi bodmi: bod
je pri použití buď sprístupnený, alebo zakázaný. Preto sa význam úrovní zachováva
dvoma samostatnými súbormi a tieto súbory sa nemajú načítať naraz.

## 10. Zdroj a spôsob použitia

Normatívnym podkladom sú *Pravidlá slovenského pravopisu*, 3., upravené a
doplnené vydanie (Bratislava: Veda, vydavateľstvo Slovenskej akadémie vied,
2000), kapitola V. **Rozdeľovanie slov** a doplnkovo kapitola VIII, časť
**Spojovník**. ISBN 80-224-0655-4.

Bibliografický údaj identifikuje kodifikačný zdroj. Všetky vysvetlenia a členenie
v tomto dokumente sú novou projektovou formuláciou; text PSP sa nepreberá ako
dokumentácia ani ako tréningový zoznam rozdelených slov. Jednotlivé ukážkové
hranice slúžia iba na objasnenie pravidiel.
