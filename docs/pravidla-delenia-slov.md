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

## 3. Delenie na hranici morfém

Ak je stavba slova jasná, hranica jeho významových častí je prípustným miestom
delenia. Takýto bod pomáha čitateľovi rozpoznať slovo aj po prenesení medzi dva
riadky.

### 3.1 Predpony

Slabičná predpona sa oddeľuje od základu, napríklad `pre|písať`, `roz|obrať`,
`proti|hráč` alebo `nad|priemerný`.

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

Ak sa druhá časť zloženiny začína samohláskou, táto samohláska sa podľa možnosti
nepripája k prvej časti. Zachovanie hranice zloženia zlepšuje čitateľnosť, napr.
`stredo|európsky`.

### 3.5 Nejasná alebo dvojako vnímateľná stavba

Ak morfematickú hranicu nemožno spoľahlivo určiť alebo ju bežný používateľ
nemusí vnímať, prednosť dostáva slabičné delenie. PSP výslovne pripúšťajú
varianty najmä v troch situáciách:

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
7. Predvolene odstrániť bod za jednopísmenovou začiatočnou slabikou.
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

## 10. Zdroj a spôsob použitia

Normatívnym podkladom sú *Pravidlá slovenského pravopisu*, 3., upravené a
doplnené vydanie (Bratislava: Veda, vydavateľstvo Slovenskej akadémie vied,
2000), kapitola V. **Rozdeľovanie slov** a doplnkovo kapitola VIII, časť
**Spojovník**. ISBN 80-224-0655-4.

Bibliografický údaj identifikuje kodifikačný zdroj. Všetky vysvetlenia a členenie
v tomto dokumente sú novou projektovou formuláciou; text PSP sa nepreberá ako
dokumentácia ani ako tréningový zoznam rozdelených slov. Jednotlivé ukážkové
hranice slúžia iba na objasnenie pravidiel.
