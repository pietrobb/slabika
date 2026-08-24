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

## Prečo to vzniklo

Slovenčina nie je bez vlastných deliacich vzorov: Jana Chlebíková zverejnila
slovenské vzory pre TeX už v roku 1992. Tento projekt si preto nenárokuje
prvenstvo; rieši užší problém: vytvoriť moderný a testovateľný pravidlový
engine a z jednej konzistentnej analýzy odvodiť otvorene použiteľné Liangove
vzory.

Liangov algoritmus ani `patgen` nie sú spornou časťou. Kvalitu vzorov ohraničuje
kvalita a konzistentnosť označených slov použitých na tréning; rozporné delenia
vo vstupných zoznamoch sa môžu preniesť aj do výsledných vzorov.

## V čom je tento projekt iný

Algoritmus, ktorým sa robia deliace vzory (Liangov `patgen`), je vynikajúci a
nikto ho nemení. Problém nikdy nebol v ňom — problém je vo vstupe. Vzory sú
presne tak dobré, ako dobrý a konzistentný je zoznam už rozdelených slov, na
ktorom sa učili.

Bežný postup je taký, že sa zoznam **pozbiera** — z voľných slovníkov, z
existujúcich zdrojov. Tým sa do vzorov prenesú aj všetky nedôslednosti tých
zdrojov.

Tento projekt vytvára tréningové delenia **výpočtom**. Súčasný Python engine
počíta slabiky aj typografické deliace body z explicitného modelu vokalických a
diftongických jadier, slabikotvorných `ŕ`, `ĺ`, `r`, `l`, spoluhláskových skupín
a rozpoznaných švíkov medzi morfémami. Experimentálne Liangove vzory sa potom
učia z tvarov označených týmto enginom, nie zo zozbieraného slovníka delenia.
Označenia sú preto vnútorne konzistentné s enginom; to však **automaticky
neznamená**, že sú správne podľa PSP. Existujúci text slúži len na určenie
slovnej zásoby, ktorú treba pokryť — nie ako zdroj hotových delení.

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

Normatívnou autoritou projektu sú *Pravidlá slovenského pravopisu* (JÚĽŠ SAV),
kapitola **V. Rozdeľovanie slov**. Samostatne formulovanú projektovú referenciu
obsahuje dokument [`docs/pravidla-delenia-slov.md`](docs/pravidla-delenia-slov.md).
PSP určujú, čo má byť správny výsledok — nepoužívajú sa ako zdroj dát.
Tento projekt nie je nijako spojený s JÚĽŠ SAV a nie je ním schválený.

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
ho niekto z tej dvojice vyberie. MIT je tu ako druhá možnosť pre firemné
procesy, ktoré CC0 neuznávajú; o práve k databáze nehovorí nič, ale ani nič
z toho, čo CC0 už uvoľnilo, nezužuje.

**Samotné licenčné podmienky CC0 neukladajú povinnosť uvádzať autora.** Tým nie
sú dotknuté osobnostné práva, ktorých sa podľa použiteľného práva vzdať nemožno
— napr. práva autora podľa § 18 autorského zákona; pri dokumentácii, ktorá je
autorským textom, to nie je teoretická výhrada. Poteší nás, keď nás uvediete,
ale nič od vás nechceme. Pri
kóde tiež nič nepropagujete a nikoho neuvádzate — len pri jeho ďalšom šírení
platia bežné notice povinnosti tej licencie, ktorú si vyberiete (MIT alebo
Apache-2.0).

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

## Súčasný stav

`slabika` je **alfa verzia** (`0.1.0`) balíka pre Python 3.10 a novší. Nemá
žiadne závislosti potrebné za behu a z pracovnej kópie sa dá nainštalovať
príkazom `python -m pip install -e .`.

Čo dnes zverejnený repozitár obsahuje — a čo neobsahuje:

| súčasť | dnešný stav |
| --- | --- |
| pravidlový Python engine | **je** — slabikovanie a typografické delenie sú implementované a testované oddelene |
| verejné API | **je** — `syllables`, `break_points`, `divisions` a `hyphenate` |
| úrovne výstupu podľa projektovej interpretácie PSP | **sú** — predvolené body, kodifikované dublety cez `all_points=True`, neodporúčané, ale prípustné body cez `contextual=True` |
| slovník výnimiek celých slov | **nie je, zámerne** — reprezentatívne známe nevyriešené prípady zostávajú ako padajúce špecifikácie `xfail`, kým ich nevysvetlí pravidlo |
| pracovné dáta slov a revízií | **sú** — SQLite snapshoty v `tests/data/` obsahujú izolované tvary a stav kontroly, nie súvislý text |
| revízna konzola | **čiastočne** — server a UI sú verzované, ale pomocný modul na porovnanie s TeXom ešte nie je zverejnený, takže čistý checkout nespustí celú konzolu |
| zdrojový prozaický korpus | **nie je zverejnený** — repozitár neobsahuje vety, poradie slov ani štruktúru zdrojových textov |
| experimentálne Liangove vzory | **sú** — `patterns/hyph-sk-slabika.tex`, výslovne označené ako rozpracované |
| úplný vstup a pipeline k zverejneným vzorom | **zatiaľ nie sú** — samotný repozitár nevie zopakovať experiment so 702 438 tvarmi |
| používanie Liangových vzorov balíkom Python | **nie je implementované** — balík spúšťa priamo pravidlový engine |
| nezávislý PSP gold benchmark alebo certifikovaná celková presnosť | **zatiaľ nie sú** |
| finálne vydanie vzorov a integrácie pre prehliadače, kancelárske či sadzobné systémy | **zatiaľ nie sú** |

Verzované testy enginu a proveniencie pokrývajú jazykové pravidlá, hraničné
triedy, verejné API a licenčné obmedzenia. Testy revíznej konzoly sú tiež
verzované, ale čistý checkout ich dnes nevie ani načítať, pretože chýba pomocný
modul uvedený vyššie. Známe nevyriešené jazykové prípady zostávajú viditeľné ako
striktné očakávané zlyhania namiesto toho, aby ich zakryl zoznam slov. Pracovný
inventár 179 537 tvarov sa používal
aj na kontroly robustnosti vo veľkom, väčšina týchto tvarov však nebola
nezávisle posúdená. To, že spracovanie nespadne, dokazuje robustnosť, nie
správnosť každého delenia. Projekt preto dnes neuvádza percento celkovej
presnosti pravidlového enginu.

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

### Experimentálne Liangove vzory

[`patterns/hyph-sk-slabika.tex`](patterns/hyph-sk-slabika.tex) je prvá
zverejnená **pracovná verzia** vzorov. Obsahuje 6 376 vzorov a ani jednu výnimku
celého slova. PATGEN sa ich naučil zo 702 438 tvarov označených predvolenými
bodmi súčasného enginu `slabika`; pevná testovacia množina bola z tréningu
vylúčená.

Na 33 734 odložených slovách pri rovnakých ľavých/pravých minimách TeXu 2/3 pre
oba súbory aj cieľ vyšiel tento výsledok:

| vzory | presné celé slová | precision bodov | recall bodov |
| --- | ---: | ---: | ---: |
| **slabika WIP (6 376 vzorov)** | **98,7075 %** (33 298/33 734) | **99,8194 %** | **99,4032 %** |
| Jana Chlebíková 1992 | 86,7997 % | 94,7457 % | 93,6176 % |

Je to benchmark **vernosti súčasnému pravidlovému enginu**, nie nezávislý
benchmark správnosti podľa PSP. Body enginu mimo spoločných miním TeXu sa
nehodnotili. Súbor sa už dá skúšať a použiť v nadväzujúcich experimentoch, ale
nie je finálnym vydaním, balík Python ho zatiaľ nepoužíva a zo samotného
zverejneného repozitára ho ešte nemožno nanovo vygenerovať.

Prípona `.tex` označuje zdrojový zápis, nie jediné prostredie, v ktorom sa vzory
dajú použiť. Samotný obsah tvoria štandardné Liangove vzory: možno ich načítať
nástrojmi kompatibilnými s TeXom, prebaliť do deliaceho slovníka vo formáte
libhyphen/Hunspell pre aplikácie ako LibreOffice, OpenOffice, Scribus či Pyphen,
alebo skonvertovať do formátu Liangovho JavaScriptového enginu, napríklad
Hyphenopoly. Každé cieľové prostredie ešte potrebuje vlastné údaje o kódovaní a
minimách, obal alebo skompilovaný formát, registráciu jazyka a otestovanie;
samotné skopírovanie tohto súboru do aplikácie alebo na web ho nenainštaluje.
Prehliadače neposkytujú webové API, ktorým by stránka vložila ľubovoľný vlastný
súbor vzorov do CSS `hyphens: auto`.

Vzory robia iba jednu vec: predpovedajú typografické deliace body v slovách.
Nevracajú jazykové slabiky, morfematickú analýzu ani tri úrovne výstupu
pravidlového enginu a nerozlišujú nepodporovaný zápis od podporovaného slova bez
dostupného deliaceho bodu.

## Autor

**Peter Bezemek** — <peter.bezemek@gmail.com>,
[@pietrobb](https://github.com/pietrobb).

Ak nájdete slovo, ktoré sa delí zle, otvorte issue — jedno zle rozdelené slovo
je väčšinou príznak chýbajúceho pravidla, nie výnimka. Presne to je najužitočnejší
príspevok, aký môžete poslať.
