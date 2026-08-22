# slabika

Delenie slovenských slov na slabiky — a až z toho odvodené rozdeľovanie slov na
konci riadka.

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

Otvorte si ľubovoľnú slovenskú knihu vysádzanú za posledných dvadsať rokov a
pozrite sa na úzky stĺpec. Nájdete tam `pos-tavil`, `dopo-ludnia`, `je-dnotka`.
To nie sú preklepy sadzača — to je to, čo mu ponúkol program.

Dôvod je prozaický: slovenčina nikdy nedostala vlastné delenie. To, čo je vo
Worde, v LibreOffice, v prehliadačoch aj v profesionálnych sadzobných
systémoch, vzniklo buď z českých vzorov, alebo z malého a vnútorne
nekonzistentného zoznamu slov. Čeština a slovenčina si sú blízke práve tak, aby
sa to na prvý pohľad zdalo v poriadku — a práve tak vzdialené, aby to bolo
zle: `ô`, `ä`, dvojhlásky `ia/ie/iu`, `ľ`, `ŕ`, `ĺ`, rytmický zákon.

## V čom je tento projekt iný

Algoritmus, ktorým sa robia deliace vzory (Liangov `patgen`), je vynikajúci a
nikto ho nemení. Problém nikdy nebol v ňom — problém je vo vstupe. Vzory sú
presne tak dobré, ako dobrý a konzistentný je zoznam už rozdelených slov, na
ktorom sa učili.

Bežný postup je taký, že sa zoznam **pozbiera** — z voľných slovníkov, z
existujúcich zdrojov. Tým sa do vzorov prenesú aj všetky nedôslednosti tých
zdrojov.

Tento projekt zoznam **generuje**. Slabičné hranice sa počítajú z fonológie
jazyka: z vokalických a diftongických jadier, zo slabikotvorných `ŕ`, `ĺ`, `r`,
`l`, zo spoluhláskových skupín a zo švíkov medzi morfémami; tvary sa dopĺňajú
morfologickým rozvinutím. Generovaný zoznam môže byť ľubovoľne veľký a je z
podstaty veci bezosporný. Existujúci text slúži len na to, aby sa vedelo, akú
slovnú zásobu treba pokryť — nie ako zdroj dát.

Poradie vrstiev je zámerné a je to hlavná myšlienka celého balíka:

| modul | čo to je |
| --- | --- |
| `slabika.phonology` | inventár foném: dĺžka, znelosť, miesto a spôsob artikulácie, mäkkosť |
| `slabika.syllabify` | fonotaktické delenie na slabiky — **primárny výsledok** |
| `slabika.typo` | typografická konvencia rozdeľovania — *odvodená* zo slabík |
| `slabika.phonotactics` | správnosť tvaru, rytmický zákon, vokalizácia predložiek |

Slabikovanie je produkt. Rozdeľovanie slov je len jeden jeho odberateľ —
ďalšími sú syntéza reči, prozódia, verzológia a tvaroslovie.

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

Zhoda s normou sa meria voči *Pravidlám slovenského pravopisu* (JÚĽŠ SAV),
kapitola **V. Rozdeľovanie slov**. PSP sa používajú ako vyjadrenie toho, čo je
správny výsledok — nie ako zdroj dát. Tento projekt nie je nijako spojený s
JÚĽŠ SAV a nie je ním schválený.

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

## Stav

Rané štádium — a je to tak zámerne. Knižnica funguje, má 167 testov a bola
prehnaná celou slovnou zásobou, ktorej má slúžiť: 197 749 rôznych tvarov z
vlastných prekladov držiteľa autorských práv (59 diel, 6,4 milióna tokenov;
samotný korpus tu zverejnený nie je). Na žiadnom z nich nespadla, pri asi
30 µs na tvar, a zopakovala všetkých 486 delení, ktoré sú ručne overené alebo
potvrdené pri kontrole — 486 zo 486.

To je celý dôkaz. Ostatné tvary jeden po druhom overené nie sú a dve chyby sú
známe a v tomto vydaní neopravené:

- prvá časť zloženiny `geo` sa zámerne nedelí (`geo·ló·gia`) a spúšťa sa aj na
  cudzích vlastných menách, ktoré sa tak len začínajú (`George` → `Geo·r·ge`);
  tá istá vetva ako jediná neprevádza výstup na malé písmená;
- 666 tvarov, väčšinou francúzskych a anglických mien, nedostane deliaci bod,
  hoci prípustný existuje. Odmietnuť deliť cudziu fonotaktiku je obhájiteľné,
  lenže volajúci zatiaľ nerozlíši toto odmietnutie od „toto slovo nemá žiadny
  prípustný deliaci bod“.

Vrstva generovania vzorov a zverejnený zoznam slov v tomto repozitári zatiaľ
nie sú.

## Autor

**Peter Bezemek** — <peter.bezemek@gmail.com>,
[@pietrobb](https://github.com/pietrobb).

Ak nájdete slovo, ktoré sa delí zle, otvorte issue — jedno zle rozdelené slovo
je väčšinou príznak chýbajúceho pravidla, nie výnimka. Presne to je najužitočnejší
príspevok, aký môžete poslať.
