# slabika

Slovenské slabikovanie a typografické rozdeľovanie slov na konci riadka — dva
samostatné výsledky založené na spoločnej hláskovej a morfematickej analýze.

```python
>>> import slabika
>>> slabika.syllables("najneuveriteľnejšími")
['naj', 'ne', 'u', 've', 'ri', 'teľ', 'nej', 'ší', 'mi']
>>> slabika.hyphenate("Prekladateľský", separator="-")
'Pre-kla-da-teľ-ský'
>>> slabika.break_points("Prekladateľský")
[3, 6, 8, 11]
```

> 🇬🇧 The English README is [here](README.md). It is the reference document for
> packagers and for licence review.

## Prečo tento projekt vznikol

Nezačalo sa to ako jazykovedný projekt, ale ako sadzobný problém: autor
potreboval sádzať slovenský text automaticky — na danú šírku, do bloku a so
správnym delením — bez toho, aby výsledok riadok po riadku prechádzal človek.
Rozdeľovanie slov je práve tá časť, ktorú stroj musí zvládnuť spoľahlivo,
pretože zarovnaný riadok je buď zlomený na prípustnom mieste, alebo je zle — a
čitateľ to vidí okamžite.

Prvým krokom bolo nájsť niečo, čo sa dá použiť. Existovala sada TeXových vzorov
z roku 1992 a nič, čo by sa dalo preveriť, na jednom mieste opraviť a znovu
zostaviť: zoznam slov, z ktorého sa tie vzory učili, nebol nikdy zverejnený,
neexistoval otvorený engine, ktorý by slovenské delenia odvodzoval z vyslovených
pravidiel, a jedno zle delené slovo sa nedalo opraviť inak než ručným zásahom do
hotovej tabuľky. Súbor vzorov, ktorý sa nedá odvodiť nanovo, sa dá iba nahradiť,
nie opraviť.

Záver bol, že chýbajúcim dielom nie je ďalší algoritmus, ale vstup — a že ten
bude treba postaviť. Presne tým je tento repozitár: najprv slovná zásoba a
pravidlá, vzory až ako ich dôsledok.

## Čo je to vlastne Liangov vzor

Väčšina zverejneného delenia slov stojí na algoritme z dizertácie Franka Lianga
z roku 1983 — na tom, ktorý je zabudovaný v TeXu a cez neho vo väčšine
sadzobných a textových programov. Nepozná nijakú gramatiku. Vzor je krátky úsek
písmen s číslicami medzi nimi, napríklad `1ná2`: nepárna číslica znamená, že
delenie je na tom mieste dovolené, párna ho zakazuje, všetky vzory, ktoré sa na
slovo hodia, sa preložia cez seba a na každej pozícii vyhrá najvyššia číslica.
Pár tisíc takýchto úsekov pokryje celý jazyk v niekoľkých kilobajtoch a beží
okamžite.

Vzory nepíše človek. Učí ich program `patgen` zo zoznamu slov, v ktorom sú
delenia už vyznačené, a pridáva ďalšie a ďalšie vzory, kým ten zoznam dostatočne
verne nezopakuje. A práve toto je jadro veci: **`patgen` reprodukuje svoj
tréningový zoznam, takže celá otázka kvality je otázkou toho zoznamu.** Čo je vo
vstupe nedôsledné, to sa zovšeobecní do výstupu — a zovšeobecní sa to potichu,
lebo súbor vzorov si neuchováva nijaké zdôvodnenie. Nedá sa skontrolovať tým, že
si ho prečítate. Preto tento projekt považuje za skutočnú prácu slovnú zásobu, a
nie algoritmus.

## V čom je to nové

Slovenské deliace vzory existujú: Jana Chlebíková zverejnila vzory pre TeX už
v roku 1992 a tento projekt si na tú myšlienku nenárokuje prvenstvo. Nové je to,
že **celý reťazec, ktorým vznikli vzory v tomto repozitári, je v tom istom
repozitári** — a pod licenciami, ktoré dovoľujú komukoľvek spustiť ho znovu:

| krok | kde to je | licencia |
| --- | --- | --- |
| slovná zásoba — 195 230 izolovaných tvarov | [`tests/data/translatemaster_hyphenation_working.sqlite`](tests/data/translatemaster_hyphenation_working.sqlite) | `CC0-1.0 OR MIT` |
| delenia použité ako tréningové označenia | počíta ich pravidlový engine v [`src/slabika/`](src/slabika) | `Apache-2.0 OR MIT` |
| tréning, rozdelenie dát a vyhodnotenie | [`tools/liang_experiment.py`](tools/liang_experiment.py) | `Apache-2.0 OR MIT` |
| výsledné Liangove vzory | [`patterns/`](patterns) | `CC0-1.0 OR MIT` |

Nič iné netreba: žiadny súkromný prozaický korpus, žiadny licencovaný slovník,
žiadny vopred rozdelený zoznam slov. S programom `patgen` na `PATH` dva príkazy
znovu vytvoria oba zverejnené súbory vzorov z pribalenej slovnej zásoby a
nezávislé spustenia nad tou istou pracovnou kópiou dávajú bajtovo zhodné súbory.

Tým sa uzatvára kruh, ktorý býva otvorený. Zverejnený súbor vzorov je zvyčajne
konečný výrobok: dá sa načítať, ale nedá sa preveriť, nedá sa v ňom opraviť jeden
prípad a znovu ho zostaviť, nedá sa vôbec odvodiť nanovo. Tu je čitateľná a
zmeniteľná každá vrstva — opravte pravidlo v engine, pridajte vlastné slová,
zmeňte rozdelenie dát alebo parametre `patgen`, spustite generátor a máte vlastné
vzory aj strojovo čitateľný report o tom, čo presne sa zmenilo. Pokiaľ je autorovi
známe, je to prvá sada slovenských deliacich vzorov zverejnená spolu s úplným
vstupom, z ktorého vznikla.

Reprodukovateľnosť nie je správnosť. Všetko nižšie tieto dve veci dôsledne
oddeľuje: projekt vie doložiť, že vzory vyplývajú z pribalených dát a zo
súčasného enginu, a zámerne netvrdí, že každé delenie v nich je správne podľa
*Pravidiel slovenského pravopisu* (PSP).

## Prečo sa delenia počítajú, a nie zbierajú

Liangov algoritmus ani `patgen` nie sú spornou časťou. Kvalitu vzorov ohraničuje
kvalita a konzistentnosť označených slov použitých na tréning; rozporné delenia
vo vstupných zoznamoch sa prenesú aj do výsledných vzorov. Bežný postup je taký,
že sa taký zoznam **pozbiera** z existujúcich zdrojov — a tým sa preberú aj ich
nedôslednosti, bez možnosti vidieť ich alebo opraviť.

Tento projekt vytvára tréningové delenia **výpočtom**. Python engine počíta
slabiky aj typografické deliace body z explicitného modelu vokalických a
diftongických jadier, slabikotvorných `ŕ`, `ĺ`, `r`, `l`, spoluhláskových skupín
a rozpoznaných švíkov medzi morfémami. Liangove vzory sa potom učia z tvarov
označených týmto enginom, nie zo zozbieraného slovníka delenia. Označenia sú
preto vnútorne konzistentné s enginom; to však **automaticky neznamená**, že sú
správne podľa PSP. Existujúci text slúži len na určenie slovnej zásoby, ktorú
treba pokryť — nie ako zdroj hotových delení.

### Najťažšia časť: vnímaný kmeň

Mnohé pravidlá sú po určení jazykovej analýzy mechanické: vokalické jadrá,
slabikotvorné spoluhlásky, rozdelenie spoluhláskových skupín aj typografické
obmedzenia na okrajoch možno implementovať priamo. Najťažšie sú morfematické
švíky, pri ktorých čitateľ intuitívne rozhoduje, či časť slova ešte vníma ako
kmeň. Rovnaký sled písmen môže byť v jednom slove produktívnou predponou a
rozpoznaným kmeňom, no v inom súčasťou lexikalizovaného alebo prevzatého celku.
Algoritmus pracujúci iba so znakmi toto rozlíšenie zo zápisu spoľahlivo neurčí.

Preto projekt potrebuje rozsiahlu a pestrú slovnú zásobu. Nie je zdrojom hotových
delení ani slovníkom výnimiek celých slov; je evidenciou, na ktorej sa hľadajú
kandidátne analýzy, overujú celé paradigmy a porovnávajú podobné, ale odlišné
prípady. Jednotlivé prípady treba posúdiť podľa PSP, implementácia však následne
zachytí najužšie doložené pravidlo pre celú rodinu namiesto zapamätania jedného
slova. Prípady bez dostatočného dôkazu zostávajú výslovne nerozhodnuté. Budovanie
a posudzovanie tejto lexikálnej evidencie preto tvorí najväčšiu časť práce, hoci
veľká časť výsledného enginu je pravidlová.

## Koľko slovnej zásoby je naozaj skontrolované

Engine vypočíta delenie pre všetkých 195 230 tvarov, lenže vypočítať neznamená
skontrolovať. Individuálna kontrola je samostatná, oveľa menšia a celá
evidovaná vrstva — a poctivé zhrnutie znie, že väčšinu inventára nikto slovo po
slove neprešiel:

| vrstva kontroly | tvarov | podiel z 195 230 |
| --- | ---: | ---: |
| rozhodnuté autorom v revíznej konzole | 10 210 | 5,23 % |
| rozhodnuté v štyroch zmrazených slepých auditoch | 8 028 | 4,11 % |
| aspoň jedno z toho (zjednotenie, 3 268 v oboch) | 14 970 | 7,67 % |
| posúdené dvoma AI modelmi podľa PSP | 1 239 | 0,63 % |
| nikdy individuálne neskontrolované | ~180 000 | ~92 % |

**Vlastná kontrola autora** je v `tests/data/review_decisions.sqlite` a pokrýva
10 210 tvarov: 9 519 potvrdilo engine, 660 ho opravilo, 22 je označených ako
neisté, 8 ako chybný tvar a 1 je vyznačený na doriešenie. Práve tieto
rozhodnutia poháňali prácu na pravidlách enginu.

**Slepé audity** sú štyri sady `tests/data/blind_*` — 5 000, 2 000, 1 000 a 100
tvarov, zmrazené aj s hashom manifestu. Ich zmluva je *iba tvary*: recenzent
dostane holé slovo bez výstupu enginu, bez staršieho rozhodnutia a bez
posúdenia, takže odpoveď sa nemá o čo oprieť. Robili ich izolované LLM
inštancie, nie autor — a práve preto sú uložené ako dôkaz, nikdy nie ako
autorita. Z 8 100 rozhodnutí je 6 601 vyriešených, 1 477 neistých a 22
označených za chybný tvar.

**Dvojmodelové posúdenie** je v `tests/data/ai_adjudication/` — 17 behov,
1 346 posúdení nad 1 239 rôznymi tvarmi. Každý beh použil tie isté dva nezávislé
modely, doslovne zapísané v každom súbore ako `models.A` a `models.B`:

| pozícia | model tak, ako je zapísaný |
| --- | --- |
| A | `claude-opus-5[high]` |
| B | `gpt-6-astra[sub][high]` |

Každý model odpovedá sám, bez toho, aby videl druhého. Keď sa odpovede líšia,
každý dostane odôvodnenie toho druhého a môže svoj názor zmeniť (*krížová
kontrola*); ak sa stále líšia, nasleduje zmierovacie kolo; a ak sa nezhodnú ani
potom, prípad sa zapíše ako otvorený spor, nie ako priemer. Cez všetky behy:
1 079 zhôd hneď nezávisle, 145 po krížovej kontrole, 23 po zmierovaní a 99
nerozhodnutých — teda 71 rôznych tvarov.

### Kde sa AI kontrola a kontrola autora stále nezhodujú

350 tvarov má aj rozhodnutie autora, aj konsenzus modelov. Pri 297 z nich sa
zhodujú. **53 sa stále líši**, v 15 slovných rodinách, a sú tu vypísané, nie
potichu zmierené:

| povaha rozdielu | tvarov | príklad: autor | príklad: modely |
| --- | ---: | --- | --- |
| modely dali prednosť enginu pred autorom | 30 | `dô·stoj·nom` | `dôs·toj·nom` |
| autor svoje rozhodnutie po behu zmenil | 13 | `o·po·tre·bu·je` | `opot·re·bu·je` |
| modely odmietli obe odpovede | 4 | `Jac·kson` | `Jack·son` |
| závisí od výslovnosti cudzieho mena | 4 | `Arch·ae·a·lus` | `Ar·chae·a·lus` |
| modely uznali obe ako kodifikované varianty | 2 | `pá·čid·lom` | `pá·či·dlom` |

Ide o rodiny `opotrebovať`, `dôstojný`, `najposlednejší`, `neposlať`,
`apartmán`, `Jackson`, `obojpohlavný`, `alžbetínska`, `avantgarda`,
`najúhlavnejší`, `Hippokratov`, `páčidlo`, `Archaealus`, `Glendower` a
`Arbre`/`Lois`. Ani jeden z týchto
prípadov nie je vyriešený konsenzom — a ani nesmie byť: väčšina modelov nie je
normatívna autorita. Zostávajú otvorené, kým ich nerozhodne argument z PSP, a
dajú sa kedykoľvek znovu odvodiť z verzovaných dát. Každá kontrolná vrstva
uvedená vyššie je detektorom miest, kde treba rozhodnúť podľa PSP — nič viac.

## V čom sa to líši od vzorov z roku 1992

V hodnotení na odloženej množine nižšie zopakujú vzory Jany Chlebíkovej delenie
tohto enginu pri 89,63 % celých slov, takže zhruba každé desiate slovo je
rozdelené inak. Tie rozdiely nie sú náhodné. Najväčšiu skupinu tvorí
morfematický švík: tie vzory nesú morfológiu ako ručne písaný zoznam 994
predpôn a slovných základov, takže slovo mimo toho zoznamu prepadne na
fonotaktické pravidlá a švík zmizne. Ako súbor z roku 1992 vznikol — slovami
jeho autorky — a čo to o týchto rozdieloch predpovedá, je zdokumentované
v [`docs/hyph-sk-1992-povod.md`](docs/hyph-sk-1992-povod.md).

| slovo | vzory 1992 | tento engine | čo by ten bod navyše dovolil |
| --- | --- | --- | --- |
| bezodkladne | `be·z·od·kladne` | `bez·od·kladne` | `be-zodkladne`, teda rozbitie `bez-` |
| najúspešnejší | `na·jús·peš·nejší` | `naj·ús·peš·nejší` | `na-júspešnejší`, teda `j` mimo `naj-` |
| trojuholník | `tro·j·u·hol·ník` | `troj·uhol·ník` | `tro-juholník` |
| nadužívanie | `na·du·ží·va·nie` | `nad·uží·va·nie` | `na-dužívanie` |
| rozorať | `ro·zo·rať` | `roz·orať` | `ro-zorať` |
| abstrakcia | `ab·s·trak·cia` | `ab·strak·cia` | `abs-trakcia` |

Existuje aj opačný prípad: body, ktoré staršie vzory neponúkajú vôbec. To
správnosť nekazí, ale v úzkej sadzbe to stojí zalomenia.

| slovo | vzory 1992 | tento engine |
| --- | --- | --- |
| rozum | `rozum` (bez delenia) | `ro·zum` |
| poobede | `po·obede` | `po·o·bede` |
| predĺžiť | `pre·dĺžiť` | `pre·dĺ·žiť` |
| administratíva | `ad·mi·ni·stra·tíva` | `ad·mi·nis·tra·tíva` |

Oba stĺpce vznikli pri rovnakých okrajových minimách TeXu 2/3, takže porovnanie
je rovnaké s rovnakým; `tex/hyph-sk.tex` je pribalený v tomto repozitári, takže
ktorýkoľvek riadok sa dá overiť priamo. Nie je to zoznam chýb. Tie vzory vznikli
v roku 1992 s možnosťami roku 1992, tri desaťročia slúžili slovenskej sadzbe a
zmyslom tohto porovnania je jediná vec: pravidlový engine vie uniesť rozlíšenie
— *toto je predpona* —, ktoré tabuľka úsekov písmen nemá ako vyjadriť.

## Architektúra

Architektúra má spoločný základ a dva samostatné výstupy:

| modul | čo to je |
| --- | --- |
| `slabika.phonology` | spoločný inventár foném: dĺžka, znelosť, miesto a spôsob artikulácie, mäkkosť |
| `slabika.syllabify` | fonotaktické členenie vysloveného slova na slabiky |
| `slabika.typo` | deliace body napísaného slova podľa projektovej interpretácie PSP a typografických obmedzení |
| `slabika.phonotactics` | správnosť tvaru, rytmický zákon, vokalizácia predložiek |

`slabika.syllabify` a `slabika.typo` netvoria potrubie, v ktorom druhý modul iba
preberá výsledok prvého. Oba používajú spoločnú hláskovú a morfematickú analýzu,
no každý nad ňou rozhoduje podľa vlastných pravidiel. Preto môže byť fonologický
výsledok `ma·slo`, kým prípustný typografický deliaci bod je `mas|lo`. Hranice sa
často zhodujú, ale jeden výstup nemožno zamieňať za druhý.

Typografické delenie má tri úrovne výstupu a sú to reálne odlišné výsledky toho
istého algoritmu, nie vzájomné opravy. Napríklad `hyphenate("všeobecne")` vráti
preferované `vše·obec·ne`, kým `hyphenate("všeobecne", contextual=True)` pridá aj
prípustný, ale nepreferovaný bod a vráti `vše·o·bec·ne`. Druhý výsledok
neznamená opravu prvého: iba sprístupňuje bod, ktorý môže sadzba použiť, keď
preferované body nestačia. Rovnocenné kodifikované dublety sprístupní
`all_points=True`.

## Čo je v repozitári

| cesta | čo to je |
| --- | --- |
| `src/slabika/` | pravidlový engine a verejné API — `syllables`, `break_points`, `divisions`, `hyphenate` |
| `src/slabika/review/` | lokálna revízna konzola, ktorá je súčasťou balíka |
| `tests/data/translatemaster_hyphenation_working.sqlite` | pracovný inventár slov: 195 230 izolovaných tvarov so stavom veľkosti písmen a kontroly |
| `tests/data/blind_*`, `tests/data/ai_adjudication/` | zmrazené vzorky slepého auditu a poradné AI posúdenia — dôkazy, nie autorita |
| `tests/` | testy: engine, hraničné triedy, revízna konzola, invarianty vzorov, proveniencia a licencie |
| `tools/liang_experiment.py` | generátor: označenia, deterministické rozdelenie, tréning `patgen`, vyhodnotenie, `report.json` |
| `tools/review/`, `tools/morph/` | pomôcky na audit, dopad zmien a indukciu morfológie používané pri posudzovaní |
| `patterns/hyph-sk-slabika.tex` | zverejnené preferované Liangove vzory |
| `patterns/hyph-sk-slabika-permissive.tex` | zverejnené permisívne Liangove vzory |
| `tex/hyph-sk.tex` | slovenské vzory Jany Chlebíkovej z roku 1992, pribalené pod ich licenciou MIT ako porovnávacia základňa |
| `docs/pravidla-delenia-slov.md` | samostatne formulovaný projektový prepis kapitoly V. PSP |
| `docs/hyph-sk-1992-povod.md` | ako vznikli vzory Jany Chlebíkovej z roku 1992 podľa jej vlastného opisu a čo to predpovedá o tu nameraných rozdieloch |
| `LICENSING.md`, `CONTRIBUTING.md`, `REUSE.toml` | licencie po vrstvách, proveniencia dát a podmienky príspevkov |
| `run_review_local.bat`, `run_review.bat` | spúšťače revíznej konzoly pre Windows (externý recenzent / správca) |

Zverejnené nie sú vety, poradie slov ani štruktúra zdrojových textov: inventár
obsahuje výlučne izolované tvary.

## Ako si vzory pregenerovať sami

Potrebný je Python 3.10 alebo novší a program `patgen` z TeX Live alebo MiKTeXu
dostupný cez `PATH`. Ak chcete spustiť aj všetky projektové kontroly,
nainštalujte vývojové nástroje príkazom `python -m pip install -e ".[dev]"`.

Tieto dva príkazy spustené v koreni repozitára nanovo vytvoria všetky tréningové
rozdelenia aktuálnym enginom, natrénujú oba režimy, vyhodnotia ich na
deterministicky odloženej množine a prepíšu dva verzované súbory vzorov:

```console
python tools/liang_experiment.py --mode preferred --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

Generátor číta `tests/data/translatemaster_hyphenation_working.sqlite`. Prijme
riadky so stavom veľkosti písmen `resolved` alebo `inferred`, prevedie ich na
malé písmená, odstráni duplikáty, vyradí nepodporované zápisy a so stabilnou
soľou `slabika-liang-v1` vytvorí tréningovú a testovaciu množinu. Vygenerovaný
`train.dic` obsahuje tréningové slová rozdelené enginom. Každý výstupný priečinok
obsahuje aj `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` a strojovo
čitateľný `report.json`. Cesta zadaná cez `--patterns-output` je výsledný balený
zdroj pre TeX.

Táto snímka inventára má 195 767 riadkov a SHA-256
`d2bcafa945c86cf7eca000bc8ee6a4dc272311977669aa057ffa6182b1d2b821`. Po
filtrovaní dáva 193 119 podporovaných unikátnych slov: 154 496 tréningových a
38 623 odložených. Výsledný preferovaný a permisívny súbor majú SHA-256
`3460bdc9e28bd657cb926d1f1a74d069db09733e6b43cce6e300d882b1208743` a
`61f6346392bde47e8aaf77635c67fbc3e3c76a9c393090927b27f62724e7ab57`.

### Ako overiť nové generovanie alebo príspevok

1. Prečítajte oba súbory `report.json`. Objekty `corpus` a `split` presne
   ukazujú, koľko riadkov sa prijalo, vyradilo, zlúčilo, trénovalo a odložilo;
   `files` obsahuje SHA-256 vstupu, tréningového slovníka a výsledných vzorov;
   `evaluation` obsahuje úspešnosť celých slov, precision, recall a prvých 30
   nezhôd.
2. Pri nezmenenej pracovnej kópii a zhodnom `patgen` majú mať výsledné súbory
   vyššie uvedené hashe a `git diff --exit-code -- patterns/` nemá ukázať
   rozdiel. Po zámernej zmene enginu alebo slovnej zásoby treba namiesto
   očakávania starých hashov posúdiť rozdiel oboch súborov vzorov aj zmenu
   metrík.
3. Spustite projektové kontroly:

```console
python -m pytest
python -m ruff check .
reuse lint
```

Testy pokrývajú engine, revíznu konzolu, invarianty vygenerovaných vzorov,
provenienciu aj licenčnú konzistentnosť. Ruff kontroluje zdrojový kód Pythonu a
REUSE správne licenčné metadáta každého distribuovaného súboru. Tieto kontroly a
výsledok na odloženej množine dokazujú reprodukovateľnosť a vernosť aktuálnemu
enginu; **nedokazujú** správnosť zmeneného delenia podľa PSP. Jazyková zmena
stále potrebuje doklad z PSP a regresnú kontrolu opísanú nižšie.

## Ako zmeniť vstup a pretrénovať

Všetko, čo generátor spracúva, sa dá zmeniť — a licencie nekladú na ďalšie
šírenie odvodeného výsledku žiadnu podmienku.

- **Zmena jazykového pravidla.** Upravte engine, spustite testy a potom oba
  príkazy generátora. Označenia, oba súbory vzorov aj metriky z toho vyplynú
  automaticky.
- **Doplnenie slovnej zásoby.** Pridajte do inventára ďalšie tvary a pretrénujte.
  Pestrejšia evidencia je hlavnou pákou na kvalitu; nové slová však musia byť
  vlastný materiál alebo verejná doména (pozri nižšie).
- **Zmena experimentu.** Soľ rozdelenia, veľkosť odloženej množiny, parametre
  `patgen` aj režim výstupu sú v `tools/liang_experiment.py` a každý beh sa sám
  zdokumentuje v `report.json`.
- **Výsledok je váš.** Vzory odvodené z týchto dát možno zverejniť, prebaliť aj
  komerčne šíriť pod ktoroukoľvek z ponúkaných licencií, bez záväzku voči tomuto
  projektu.

### Ako kontrolovať a poslať opravy podľa PSP

Pribalená revízna konzola umožňuje prezerať slovnú zásobu bez zásahu do
verzovaných rozhodnutí projektu. Z pracovnej kópie ju nainštalujete a spustíte
takto:

```console
python -m pip install -e .
slabika-review
```

Otvorí lokálnu adresu v predvolenom prehliadači. Pribalený inventár sa iba číta;
práca recenzenta sa ukladá oddelene do `review_decisions.sqlite` v priečinku, z
ktorého bol príkaz spustený. Voľba `--decisions` určí iné úložisko rozhodnutí a
`--db` iný inventár.

Na Windows je pre nezávislého recenzenta odporúčaný súbor
`run_review_local.bat`. Nevyžaduje inštaláciu balíka, skontroluje Python 3.10
alebo novší a rozhodnutia každého používateľa uloží do
`%LOCALAPPDATA%\slabika-review`. Nemôže teda zmeniť revíznu databázu projektu.
`run_review.bat` je spúšťač pre správcu: zámerne otvára verzované projektové
revízne dáta a externý recenzent ho používať nemá.

Konzola oddeľuje dve rozdielne otázky:

- **typografické delenie** určuje, kde sa smie napísané slovo rozdeliť na konci
  riadka; práve tento výstup sa používa na trénovanie Liangových vzorov;
- **slabikovanie** opisuje hovorené slabiky a jeho hranice môžu byť oprávnene
  iné.

Ak chcete poslať užitočnú opravu, vyhľadajte slovo, skontrolujte aktuálne
typografické delenie, zapíšte navrhované hranice a návrh uložte. Ako značku
hranice možno použiť `-` aj `·`; písmená slova sa nesmú meniť, vynechať ani
pridávať. Vlastné meno, cudzie slovo, skratku, chybný tvar alebo neistý prípad
radšej príslušne označte, než aby ste vynútili nedoloženú odpoveď.

Normatívnou autoritou je kapitola V. *Rozdeľovanie slov* v PSP. Najrýchlejšou
pomôckou je samostatne formulovaný projektový prepis
[`docs/pravidla-delenia-slov.md`](docs/pravidla-delenia-slov.md). Aktuálny
engine, slabikovanie, TeXové vzory z roku 1992, AI kontrola aj staršie ľudské
rozhodnutia sú iba dôkazy alebo porovnávacie hlasy, nie autorita. Najcennejší
návrh uvedie presné pravidlo PSP, vysvetlí morfematickú alebo hláskovú analýzu a
pridá príbuzné tvary či kontrastný podobný prípad. Treba rozlíšiť preferovaný bod
od rovnocenného kodifikovaného variantu a od prípustného, ale neodporúčaného
bodu.

Tlačidlo **Stiahnuť opravy** vytvorí časovo označený JSON vo formáte
`slabika-corrections` iba z uložených návrhov, ktoré sa stále nezhodujú s
aktuálnym enginom. Obsahuje tvar, výstup a verziu enginu, navrhnutý výsledok,
poznámku a príznaky. Súbor pošlite nezmenený autorovi e-mailom alebo ho priložte
k issue; podklady z PSP možno dopísať do správy. Odoslanie JSON-u nemení
repozitár a nerobí z návrhu automaticky kanonické rozhodnutie. Každá prijatá
oprava sa nezávisle overí podľa PSP a proti regresiám v celom korpuse. Keďže
jedno zle delené slovo býva príznakom chýbajúceho pravidla pre rodinu slov,
oprava spravidla pridá najužšie doložené pravidlo a testy, nie výnimku pre celé
slovo.

### Ako prispieť slovnou zásobou

Novú slovnú zásobu možno pridať iba z vlastného materiálu prispievateľa alebo
z verejnej domény. Neposielajte výpisy z cudzích slovníkov, lexikálnych databáz
ani zoznamov slov. Licenčné a provenienčné požiadavky sú v
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Zverejnené Liangove vzory

Projekt zverejňuje dve **pracovné verzie** vzorov, naučené výlučne z pracovnej
slovnej zásoby pribalenej v tomto repozitári. Z jej 195 767 inventárnych riadkov
po vylúčení tvarov `needs_review` a filtrovaní abecedy a veľkosti písmen ostáva
193 119 podporovaných unikátnych slov. Deterministické rozdelenie priradí
154 496 slov do tréningu a 38 623 slov ponechá nevidených pre obe vyhodnotenia:

- [`patterns/hyph-sk-slabika.tex`](patterns/hyph-sk-slabika.tex) je predvolený
  preferovaný súbor (5 231 vzorov), trénovaný z `break_points(word)`;
- [`patterns/hyph-sk-slabika-permissive.tex`](patterns/hyph-sk-slabika-permissive.tex)
  je permisívny súbor pre úzku sadzbu (4 835 vzorov), trénovaný z
  `break_points(word, all_points=True, contextual=True)`.

Oba súbory sú bez výnimiek celého slova. Na vstup aj vyhodnotenie sa uplatnili
okrajové minimá TeXu 2/3.

Štandardný Liangov súbor sprístupňuje iba jednu nerozlíšenú množinu bodov; nevie
zachovať informáciu „tento bod preferuj, tento použi iba v úzkej sadzbe“.
Rozlíšenie preto nesú dva samostatné súbory. Bežná sadzba má používať preferovaný
súbor. Permisívny súbor navyše sprístupňuje rovnocenné kodifikované varianty aj
prípustné, ale nepreferované kontextové body; oba súbory sa nemajú načítať naraz.

Na 38 623 odložených slovách pri rovnakých ľavých/pravých minimách TeXu 2/3 pre
oba súbory aj cieľ vyšiel tento výsledok:

| vzory | presné celé slová | precision bodov | recall bodov |
| --- | ---: | ---: | ---: |
| **slabika preferovaný (5 231 vzorov)** | **98,6770 %** (38 112/38 623) | **99,6283 %** | **99,5121 %** |
| Jana Chlebíková 1992 proti preferovanému cieľu | 89,6279 % | 96,0111 % | 95,3423 % |
| **slabika permisívny (4 835 vzorov)** | **98,7728 %** (38 149/38 623) | **99,6545 %** | **99,5635 %** |
| Jana Chlebíková 1992 proti permisívnemu cieľu | 89,1023 % | 96,3877 % | 94,8691 % |

Je to benchmark **vernosti súčasnému pravidlovému enginu**, nie nezávislý
benchmark správnosti podľa PSP. Body enginu mimo spoločných miním TeXu sa
nehodnotili. Súbory sa už dajú skúšať a použiť v nadväzujúcich experimentoch, ale
nie sú finálnym vydaním a balík Python ich zatiaľ nepoužíva.

### Použitie vzorov mimo TeXu

Prípona `.tex` označuje zdrojový zápis, nie jediné prostredie, v ktorom sa vzory
dajú použiť. Samotný obsah tvoria štandardné Liangove vzory: možno ich načítať
nástrojmi kompatibilnými s TeXom, prebaliť do deliaceho slovníka vo formáte
Hunspell pre aplikácie ako LibreOffice, OpenOffice, Scribus či Pyphen, alebo
skonvertovať do formátu Liangovho JavaScriptového enginu, napríklad Hyphenopoly.
Každé cieľové prostredie ešte potrebuje vlastné údaje o kódovaní a minimách, obal
alebo skompilovaný formát, registráciu jazyka a otestovanie; samotné skopírovanie
tohto súboru do aplikácie alebo na web ho nenainštaluje. Prehliadače
neposkytujú webové API, ktorým by stránka vložila ľubovoľný vlastný súbor vzorov
do CSS `hyphens: auto`.

Vzory robia iba jednu vec: predpovedajú typografické deliace body v slovách.
Nevracajú jazykové slabiky, morfematickú analýzu ani tri úrovne výstupu
pravidlového enginu a nerozlišujú nepodporovaný zápis od podporovaného slova bez
dostupného deliaceho bodu.

## Súčasný stav

`slabika` je **alfa verzia** (`0.1.0`) balíka pre Python 3.10 a novší. Nemá
žiadne závislosti potrebné za behu a z pracovnej kópie sa dá nainštalovať
príkazom `python -m pip install -e .`.

| súčasť | dnešný stav |
| --- | --- |
| pravidlový Python engine | **je** — slabikovanie a typografické delenie sú implementované a testované oddelene |
| verejné API | **je** — `syllables`, `break_points`, `divisions` a `hyphenate` |
| úrovne výstupu podľa projektovej interpretácie PSP | **sú** — predvolené body, kodifikované dublety cez `all_points=True`, neodporúčané, ale prípustné body cez `contextual=True` |
| slovník výnimiek celých slov | **nie je, zámerne** — reprezentatívne známe nevyriešené prípady zostávajú ako padajúce špecifikácie `xfail`, kým ich nevysvetlí pravidlo |
| úplný vstup a pipeline k zverejneným vzorom | **sú** — pribalená SQLite slovná zásoba a verzovaný generátor reprodukujú oba súbory bez externého korpusu |
| zdrojový prozaický korpus | **nie je zverejnený** — repozitár neobsahuje vety, poradie slov ani štruktúru zdrojových textov |
| experimentálne Liangove vzory | **sú** — preferovaný a permisívny súbor v `patterns/`, výslovne označené ako rozpracované |
| používanie Liangových vzorov balíkom Python | **nie je implementované** — balík spúšťa priamo pravidlový engine |
| nezávislý PSP gold benchmark alebo certifikovaná celková presnosť | **zatiaľ nie sú** |
| finálne vydanie vzorov a integrácie pre prehliadače, kancelárske či sadzobné systémy | **zatiaľ nie sú** |

Verzované testy enginu, revíznej konzoly a proveniencie pokrývajú jazykové
pravidlá, hraničné triedy, verejné API, lokálny editor a licenčné obmedzenia a
fungujú aj z čistého checkoutu. Známe nevyriešené jazykové prípady zostávajú
viditeľné ako striktné očakávané zlyhania namiesto toho, aby ich zakryl zoznam
slov. Pracovný inventár 195 230 tvarov sa používal aj na kontroly robustnosti vo
veľkom, väčšina týchto tvarov však nebola nezávisle posúdená. To, že spracovanie
nespadne, dokazuje robustnosť, nie správnosť každého delenia. Projekt preto dnes
neuvádza percento celkovej presnosti pravidlového enginu.

### Známe hranice Python enginu

- Zo zápisu sa nedá vždy určiť identita ani výslovnosť slova. Zdanlivé predpony,
  ktoré už zlexikalizovali, prevzaté vokalické skupiny a neadaptované cudzie mená
  stále obsahujú známe nevyriešené prípady.
- Tabuľka opráv celých slov zámerne neexistuje. Chýbajúce jazykové rozlíšenie
  zostáva otvorenou regresiou, kým ho nemožno vyjadriť pravidlom alebo
  odôvodnenou budúcou vrstvou jazykových dát.
- `hyphenate` ponechá nepodporovaný zápis bez zmeny, kým `syllables` pri
  alfabetických znakoch mimo analyzovateľného inventára vyvolá `ValueError`.
  Prázdny výsledok `break_points` nerozlišuje nepodporovaný zápis od slova bez
  prípustného deliaceho bodu.
- Morfematická analýza enginu je pravidlová a zámerne neúplná. Nie je to
  všeobecný morfologický analyzátor slovenčiny a nepozná jazyk ani výslovnosť
  ľubovoľného cudzieho slova.

## Normatívna autorita

Normatívnou autoritou projektu sú *Pravidlá slovenského pravopisu* (JÚĽŠ SAV),
kapitola **V. Rozdeľovanie slov**. Samostatne formulovanú projektovú referenciu
obsahuje dokument
[`docs/pravidla-delenia-slov.md`](docs/pravidla-delenia-slov.md). PSP určujú, čo
má byť správny výsledok — nepoužívajú sa ako zdroj dát. Testovacia slovná zásoba
pochádza z vlastného slovného materiálu projektu. Tento projekt nie je nijako
spojený s JÚĽŠ SAV a nie je ním schválený.

## Licencia po slovensky

Právne záväzné znenie je v [`LICENSES/`](LICENSES) — `Apache-2.0.txt`,
`MIT.txt`, `CC0-1.0.txt` — po anglicky; kontext vysvetľuje
[`LICENSING.md`](LICENSING.md). Toto je len zhrnutie, čo to znamená v praxi:

| vrstva | licencia | čo to znamená |
| --- | --- | --- |
| zdrojový kód | `Apache-2.0 OR MIT` | vyberte si jednu, nemusíte spĺňať obe |
| jazykové dáta | `CC0-1.0 OR MIT` | pod CC0 je to ako verejné vlastníctvo |
| deliace vzory | `CC0-1.0 OR MIT` | rovnaké podmienky ako dáta, z ktorých vznikli |
| dokumentácia | `CC0-1.0 OR MIT` | vyberte si, čo sa vám lepšie hodí |

Na dáta je aplikované CC0, takže je vyriešené aj **osobitné právo k databáze**
(smernica 96/9/ES, zákon č. 185/2015 Z. z.). To je dôležité práve v EÚ: samotné
autorské právo sa na jednotlivé slová nevzťahuje, ale právo k databáze by
teoreticky mohlo brániť tomu, aby si niekto zobral celý zoznam. CC0 sa tohto
práva vzdáva priamo vo svojom texte — nie je na to potrebná žiadna ďalšia
doložka. A keďže CC0 nie je bežná podmienená licencia, ale vzdanie sa práv voči
verejnosti, platí to od chvíle, keď je na dáta aplikované — nie až vtedy, keď si
ho niekto z tej dvojice vyberie. MIT je tu ako druhá možnosť pre firemné procesy,
ktoré CC0 neuznávajú; o práve k databáze nehovorí nič, ale ani nič z toho, čo CC0
už uvoľnilo, nezužuje.

**Samotné licenčné podmienky CC0 neukladajú povinnosť uvádzať autora.** Tým nie
sú dotknuté osobnostné práva, ktorých sa podľa použiteľného práva vzdať nemožno
— napr. práva autora podľa § 18 autorského zákona; pri dokumentácii, ktorá je
autorským textom, to nie je teoretická výhrada. Poteší nás, keď nás uvediete, ale
nič od vás nechceme. Pri kóde tiež nič nepropagujete a nikoho neuvádzate — len
pri jeho ďalšom šírení platia bežné notice povinnosti tej licencie, ktorú si
vyberiete (MIT alebo Apache-2.0).

Rozdelenie na vrstvy nie je komplikovanie pre komplikovanie. Apache-2.0 je
nekompatibilná s GPL-2.0-only a MPL-1.1 nemá ustanovenia o kompatibilite s
Apache-2.0, ktoré pribudli až v MPL-2.0 — a pod týmito licenciami stojí kus
existujúceho sadzobného a slovníkového kódu, ktorý by mal slovenské delenie
prevziať. Keby všetko viselo len na Apache-2.0, tá časť ekosystému by to zabaliť
nemohla. Preto je kód ponúkaný aj pod MIT.

Tá istá úvaha ide naprieč všetkými vrstvami: **každá z nich je ponúkaná aj pod
MIT**. Kto CC0 nesmie použiť (a takých firemných pravidiel je viac, než by sa
čakalo), zoberie si na všetko MIT. Kto chce nulové podmienky — alebo komu ide o
právo k databáze, ktoré MIT nerieši — zoberie si CC0. Nikto nie je blokovaný.

## Odkiaľ je fonológia

Klasifikácia foném pochádza z knihy **Emila Páleša**, *Sapfo — parafrázovač
slovenčiny: počítačový nástroj na modelovanie v jazykovede* (VEDA,
vydavateľstvo Slovenskej akadémie vied, Bratislava 1994, ISBN 80-224-0109-9),
kapitola 2 *Fonológia*. Páleš ju sám preberá od **J. Dvončovej** (1980) a
**J. Horeckého** (1977).

Tá kniha stojí za prečítanie aj mimo tohto projektu. Je v nej presne
sformulované, prečo formálny model jazyka musí začať pri hláskosloví — a prečo
tvaroslovie bez fonológie nemôže fungovať správne (napr. vkladanie vokálu:
*matka → matiek*, *jamka → jamôk*, *perla → perál*).

Všetko nad inventárom foném — slabikovanie, morfematické švíky, typografická
konvencia, slovný materiál aj generovanie vzorov — je pôvodná práca tohto
projektu. Páleš sa rozdeľovaním slov nezaoberá.

Slovenské TeXové vzory Jany Chlebíkovej z roku 1992 sú pribalené v
`tex/hyph-sk.tex` pod ich licenciou MIT a slúžia tu iba ako porovnávacia
základňa.

## Autor

**Peter Bezemek** — <peter.bezemek@gmail.com>,
[@pietrobb](https://github.com/pietrobb).

Ak nájdete slovo, ktoré sa delí zle, otvorte issue — jedno zle rozdelené slovo
je väčšinou príznak chýbajúceho pravidla, nie výnimka. Presne to je najužitočnejší
príspevok, aký môžete poslať.
