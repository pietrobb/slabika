# slabika

Slovenské slabikovanie a typografické rozdeľovanie slov na konci riadka — dva samostatné výsledky založené na spoločnej hláskovej a morfematickej analýze.

```python
>>> import slabika
>>> slabika.syllables("spravodlivosť")
['spra', 'vod', 'li', 'vosť']
>>> slabika.hyphenate("Prekladateľský", separator="-")
'Pre-kla-da-teľ-ský'
>>> slabika.break_points("Prekladateľský")
[3, 6, 8, 11]
>>> slabika.hyphenate("Schneiderovská")
'Schnei·de·rov·ská'
>>> slabika.hyphenate("théâtre")
'thé·âtre'
```

Podporované cudzie slová sa delia **v slovenskom texte podľa PSP**, nie podľa anglickej, nemeckej či francúzskej typografickej normy. Všetky tri cudzojazyčné cesty sú zapojené do `hyphenate`, `break_points`, `divisions` aj slovenského review. Širšia anglická podpora potrebuje voliteľný výslovnostný balík; nemecký a francúzsky vzorový adaptér nie.

English: [README.md](README.md), referenčný dokument pre balenie a licenčné posúdenie.

## Prečo tento projekt vznikol

Nezačalo sa to ako jazykovedný projekt, ale ako sadzobný problém: autor potreboval sádzať slovenský text automaticky — na danú šírku, do bloku a so správnym delením — bez človeka, ktorý by výsledok prechádzal riadok po riadku. Zarovnaný riadok je buď zalomený na prípustnom mieste alebo je nesprávne a čitateľ to vidí okamžite.

Existovali TeXové vzory z roku 1992, nie však úplný zoznam slov a reprodukovateľný postup, ktorým vznikli. Chýbala možnosť opraviť jedno zlé delenie zmenou preskúmateľného pravidla a nanovo zostaviť výsledok. Súbor vzorov, ktorý sa nedá odvodiť nanovo, možno nahradiť, ale nemožno opraviť jeho nezverejnený vstup.

Chýbajúcim dielom preto nie je ďalší algoritmus, ale **slovná zásoba, explicitné pravidlá a dohľadateľné posúdenia**. Opravte pravidlo, pridajte vlastné slová, spustite generátor a dostanete nové vzory aj report. Jana Chlebíková zverejnila slovenské vzory už v roku 1992; projekt si nenárokuje prvenstvo delenia slovenčiny. Prínosom je preskúmateľný reťazec od vstupu po vzory.

Vlastné preklady autora ukázali aj potrebu deliť cudzie mená so slovenskými koncovkami **po slovensky, ale s ohľadom na cudziu výslovnosť**. Ani slovenské čítanie každého písmena, ani slepé prevzatie cudzieho delenia nestačí. Dve stratégie adaptérov nižšie riešia túto potrebu s výslovne uvedenými obmedzeniami.

## Čo je Liangov vzor

Liangov algoritmus z roku 1983, používaný v TeXu a mnohých sadzobných systémoch, porovnáva krátke úseky písmen s číslicami medzi nimi. Vo vzore `1ná2` nepárna číslica dovoľuje delenie a párna ho zakazuje. Pri prekrytí vzorov vyhrá najvyššia číslica. Algoritmus nepozná gramatiku.

Program `patgen` sa vzory učí zo slov s vyznačenými hranicami. **Kvalitu vzorov ohraničuje kvalita tréningového zoznamu.** Rozporné označenia sa potichu zovšeobecnia; vzor si neuchováva jazykové zdôvodnenie. Skutočnou prácou je preto slovná zásoba a jej pravidlá, vzory sú odvodený výsledok.

| krok | miesto | licencia projektovej vrstvy |
| --- | --- | --- |
| inventár 206 272 izolovaných tvarov a revízna evidencia | `tests/data/` | `CC0-1.0 OR MIT` |
| engine a generátor | `src/slabika/`, `tools/liang_experiment.py` | `Apache-2.0 OR MIT` |
| výsledné slovenské Liangove vzory | `patterns/` | `CC0-1.0 OR MIT` |
| prevzaté DE/FR vzory | `src/slabika/patterns/foreign/` | MIT, pôvodné oznámenia zachované |

Tréningové delenia počíta engine, nepreberá sa hotový slovenský slovník delenia. Cudzie slová však môžu využívať DE/FR vzorové adaptéry alebo voliteľné anglické G2P. Na presnú reprodukciu preto treba rovnaký engine, inventár **aj výslovnostné prostredie**. Provenienciu slovnej zásoby vysvetľuje [LICENSING.md](LICENSING.md) §3. Reprodukovateľnosť ani zhoda s enginom nedokazujú správnosť podľa PSP.

### Prečo nový súbor slovenských vzorov

Jana Chlebíková zverejnila slovenské Liangove vzory v roku 1992; slúžia slovenskej sadzbe celé desaťročia a v `tex/hyph-sk.tex` zostávajú pribalenou porovnávacou základňou. Jej metóda bola starostlivým ručným prepisom gramatických pravidiel do Liangovej notácie, nie tréningom `patgen` nad zverejneným zoznamom slov. Bolo to dôležité praktické riešenie a tento projekt si nenárokuje prvenstvo delenia slovenčiny. Primárny opis a neskoršie hodnotenie sumarizuje [docs/hyph-sk-1992-povod.md](docs/hyph-sk-1992-povod.md).

Historický súbor však nestačí ako základ systému, ktorý sa má dať preskúmať a zlepšovať. Jeho úplný vznik nemožno zopakovať; písmenové úseky si neuchovávajú jazykové zdôvodnenie ani morfematickú analýzu hranice; cudzie slová a výnimky boli spracované iba obmedzene. To neznamená, že pôvodná práca bola zlá. Je to hodnotná historická základňa, ktorej praktické hranice dnes vieme zmerať a cielene opravovať.

Rozsah týchto hraníc ukazujú dve rozdielne merania:

| evidencia | súčasný projekt | Chlebíková 1992 | čo výsledok dokazuje |
| --- | ---: | ---: | --- |
| presné celé slová na odložených dátach oproti preferovanému cieľu enginu, minimá TeXu 2/3 | **98,5060 %** | **89,5690 %** | reprodukovateľnosť enginu, nie správnosť podľa PSP |
| prijaté podľa PSP medzi 21 514 uzavretými historickými nezhodami | **21 508** | **6 196** | posúdenie súboru nezhôd, nie náhodnú celkovú presnosť |

Druhý riadok tvorí 15 313 prípadov, v ktorých bol prijatý iba zmrazený engine, 6 195 prípadov s oboma prijatými výstupmi, 1 prípad iba pre Chlebíkovú a 5 prípadov, v ktorých nebol prijatý ani jeden výstup. Ďalších 1 659 prípadov zostáva nerozhodnutých. Audit vznikal s pomocou AI a zámerne obsahuje iba nezhody, preto je silnou diagnostickou evidenciou, nie nezávislým percentom presnosti; úplnú metodiku uvádza časť [Porovnávací súbor posúdený podľa PSP](#porovnávací-súbor-posúdený-podľa-psp).

Častou príčinou rozdielu je **rozpoznaná morfematická stavba**: predpona a základ, členy zloženiny alebo základ a slovotvorná či gramatická prípona. Písmenové vzory vidia opakujúce sa úseky, ale túto analýzu si neuchovávajú. Nasleduje 21 overených morfologických príkladov, nie prípadov vyhlásených za chybu iba preto, že sa dva systémy nezhodli. `·` označuje dostupné miesto zalomenia. Stĺpec vzorov z roku 1992 používa TeXové okrajové minimá 2/3; stĺpec aktuálneho enginu je doslovný výsledok `hyphenate(word)`, ktorého API tieto minimá neuplatňuje.

| typ | slovo | rozpoznaná stavba | vzory 1992 | aktuálny engine |
| --- | --- | --- | --- | --- |
| predpona a základ | `bezodkladne` | `bez- + od- + klad-` | `be·z·od·kladne` | `bez·od·klad·ne` |
| predpona a základ | `najúspešnejší` | `naj- + úspeš- + nejš-` | `na·jús·peš·nejší` | `naj·ús·peš·nej·ší` |
| predpona a základ | `rozkroj` | `roz- + kroj-` | `rozk·roj` | `roz·kroj` |
| vnorené predpony | `neočistí` | `ne- + o- + čist-` | `ne·očistí` | `ne·o·čis·tí` |
| predpona a základ | `predúradné` | `pred- + úrad- + n-` | `pre·dú·radné` | `pred·úrad·né` |
| zloženina | `trojuholník` | `troj- + uhol- + ník` | `tro·j·u·hol·ník` | `troj·uhol·ník` |
| zloženina | `samoobslužný` | `samo- + ob- + služ- + n-` | `sa·mo·obs·lužný` | `sa·mo·ob·služ·ný` |
| zloženina | `sebaistý` | `seba- + ist-` | `se·baistý` | `se·ba·is·tý` |
| zloženina | `pravouhlý` | `pravo- + uhl-` | `pra·vouhlý` | `pra·vo·uh·lý` |
| zloženina | `novovzbudený` | `novo- + vzbud- + en-` | `no·vovz·bu·dený` | `no·vo·vzbu·de·ný` |
| zloženina | `mäsožravce` | `mäso- + žrav- + ec` | `mä·sož·ravce` | `mä·so·žrav·ce` |
| zloženina | `pomstychtivý` | `pomsty- + chtiv-` | `po·mstych·tivý` | `pom·sty·chti·vý` |
| odvodzovanie | `kováčsky` | `kováč- + sk-` | `ko·váčsky` | `ko·váč·sky` |
| odvodzovanie | `dedičstiev` | `dedič- + stv-` | `de·dičs·tiev` | `de·dič·stiev` |
| odvodzovanie | `hráčske` | `hráč- + sk-` | `hráčske` | `hráč·ske` |
| odvodzovanie | `šéfstvom` | `šéf- + stv-` | `šéfs·tvom` | `šéf·stvom` |
| odvodzovanie | `víťazstvo` | `víťaz- + stv-` | `ví·ťazs·tvo` | `ví·ťaz·stvo` |
| odvodená číslovka | `Dvanástka` | `dvanásť- + k-` | `Dva·nás·tka` | `Dva·nást·ka` |
| zložená číslovka | `dvadsaťdva` | `dvadsať- + dva` | `dvad·saťdva` | `dvad·sať·dva` |
| zložená číslovka | `dvestotri` | `dve- + sto- + tri` | `dve·stotri` | `dve·sto·tri` |
| zložená číslovka | `stodvadsaťdva` | `sto- + dvadsať- + dva` | `stod·vad·saťdva` | `sto·dvad·sať·dva` |

Rozdielna politika okrajov vysvetľuje, prečo doslovný výstup enginu `Dva·nást·ka` obsahuje koncový bod, ktorý vo výsledku TeXových vzorov s minimami 2/3 chýba. Hodnotenie vzorov filtruje ciele enginu na rovnaké minimá; táto tabuľka zámerne ukazuje verejné API bez takej úpravy. Príklady neznamenajú, že každá ďalšia nezhoda je chybou: každý prípad treba naďalej rozhodnúť podľa PSP.

### Najťažšia časť: vnímaný kmeň

Vokalické jadrá, rozdelenie spoluhlások a okrajové obmedzenia sú často mechanické až po určení jazykovej analýzy. Morfematické švíky sú ťažšie: rovnaký zápis môže znamenať produktívnu predponu a rozpoznateľný kmeň alebo zlexikalizovaný celok. Zo samotných písmen sa to nedá spoľahlivo určiť.

Široká slovná zásoba poskytuje evidenciu na testovanie rodín a kontrastných prípadov. Uprednostňujeme najužšie doložené zovšeobecnenie pred zapamätaním jednotlivého slova. Súčasný kód však obsahuje aj malú explicitnú tabuľku posúdených cudzích delení popri lexikálnych čítaniach; tvrdenie, že je úplne bez výnimiek, by nebolo presné. Nevyriešené prípady zostávajú viditeľné.

### Odkiaľ prichádzajú morfematické hranice

Neexistuje jedna databáza hotových hraníc. `get_morpheme_parts()` skladá analýzu z troch vrstiev: ručne udržiavaných a regresne overených pravidiel pre predpony, prípony a nejednoznačné rodiny; strážených pravidiel pre číslovky, prefixoidy a osobitné zloženiny; a generovaného inventára produktívnych zloženín. `syllabify` aj `typo` používajú tú istú analýzu, ale vo vnútri rozpoznaných častí uplatňujú vlastné slabičné, resp. typografické pravidlá. Morfematický švík má v preferovanom typografickom výstupe prednosť pred mechanickým rozdelením spoluhláskovej skupiny.

Produktívna zloženinová vrstva vzniká príkazom `python tools/build_composita_grammar.py` z povrchových tvarov vlastného korpusu, lokálnej ohýbacej gramatiky a osobitne evidovaného doplnku. Pribalený `src/slabika/data/composita.json` obsahuje **11 470 prvých členov** a **20 207 hláv druhého člena**, s paradigmami podľa gramatickej roly a odtlačkami vstupov. Runtime číta iba tento verzovaný JSON; bežné používanie nepotrebuje korpusovú databázu. Regenerovanie vyžaduje projektový korpus a gramatiku na zostavenie; oboje je verzované v repozitári a oboje je aj v zverejnenom zdrojovom archíve, vo wheeli ani jedno. Štatisticky indukovaný `morphs.json` je auditnou pomôckou a produkčné hranice neurčuje.

Inventár neznamená „rozdeľ po každom známom reťazci“. Engine vyžaduje zároveň dôveryhodný prvý člen, doloženú hlavu druhého člena a iba prípustný ohýbací chvost. Nekombinuje dve slabé domnienky a blokuje viaceré kolízie s predponami a koncovkami — medzi nimi slovesotvorné `-ova-`, ktoré sa končí tým istým `-o-` ako spájacia samohláska, takže odvodený prvý člen nesmie rozdeliť `rezervovalo` ani `talentovanosť`. Preto vie odvodiť aj predtým nevidené `žlto|modrý`, `svetlo|zelený` či `modro|zelenkastý`, ale nevytvorí napríklad falošné `jahodo|vých`.

Bežný používateľ inventár **neregeneruje**; používa pribalený JSON. Overenie pokrýva **206 272 korpusových riadkov**, pričom jazykové rozhodnutia sa posudzujú podľa PSP. Testovacia sada má **1 143 úspešných testov s jedným očakávaným zlyhaním**. Tieto kontroly nezaručujú správnu analýzu každého slova. Zdroje dát a licencie uvádza [LICENSING.md](LICENSING.md).

### Ako generátor získava korene a kmene

„Koreň“ tu označuje technický základ paradigmy, nie nevyhnutne najmenší etymologický koreň. Generátor `tools/build_composita_grammar.py` postupuje takto:

1. Z tabuľky `forms`, stĺpca `form` v `tests/data/translatemaster_hyphenation_working.sqlite` načíta iba alfabetické povrchové tvary, prevedie ich na malé písmená a odstráni duplicity. **Nečíta ľudské rozhodnutia ani uložené delenia.** Základ korpusu pochádza z autorových textov a prekladov; neskoršie prírastky zahŕňajú slovnú zásobu a názvy obcí z Wikidata aj AI-generované zoznamy slov ručne skontrolované správcom. Presné obmedzenia proveniencie uvádza [LICENSING.md](LICENSING.md) §3.
2. Pridá samostatne evidované AI-autorské tvary z `tests/data/grammar_supplement.json`, napríklad chýbajúce pády `gram` alebo tvary `plavebný`. Pôvodnú databázu nemení. Doplnky sú výslovné jazykové predpoklady, nie nezávislé doklady správnosti algoritmu.
3. Lokálna ohýbacia gramatika projektu skúša menné, prídavné, zámenné a slovesné paradigmy. Z kandidáta odoberú možnú koncovku, znovu vytvoria paradigmu a overia spätnú zhodu s tvarmi korpusu vrátane základného tvaru. Automatické prijatie vyžaduje **aspoň tri rôzne podporné tvary okrem lemy**, ktoré po súťaži analýz patria danej analýze; synkretické pády sa nepočítajú viackrát. Výber je heuristika, nie dôkaz významu homografu.
4. Z prijatých kmeňov odvodia prvé členy so spájacím `-o-/-e-`; pri menách používajú aj nepriamy kmeň (`vietor → vetr- → vetro-`). Pre druhé členy ukladajú **presné povolené tvary podľa gramatickej roly**, vrátane alternácií, príčastí a osobitne evidovaných odvodení. Nepripájajú ku každému kmeňu všetky možné koncovky.
5. Viazané členy (`biblio-`, osobné `-graf`, prídavné `-tváry`, miestne `-plukovo`) a nesklonné prvé členy (`všade-`) majú osobitné deklarácie v doplnku. Viazaná hlava potrebuje aspoň jeden pôvodný korpusový príklad s rozpoznaným prvým členom a platným tvarom deklarovanej paradigmy. Je to kontrola výskytu **autorského pravidla**, nie oslabenie trojtvarového prahu automatickej indukcie; do auditu sa nezapisujú vymyslené nezávislé doklady.

Generátor odvodzuje kmene z korpusových tvarov pomocou ohýbacích pravidiel, ktorých tabuľky vzorov vychádzajú z gramatického opisu Páleša (1994), s. 41–47. Zdroje dát uvádza [LICENSING.md](LICENSING.md). Autoritou pre delenie slov sú PSP.

### Overenie a zostavenie kandidáta

Správca najprv uloží plný API snapshot základne a až potom zmení engine/inventár. Každý výstupný súbor musí byť nový:

```console
python tools/compare_composita.py --output scratch/baseline.json
python tools/build_composita_grammar.py --output scratch/grammar-audit.json --runtime-output scratch/grammar-runtime.json
python tools/compare_composita.py --inventory scratch/grammar-runtime.json --baseline scratch/baseline.json --output scratch/comparison.json --allow-engine-changes --check
python tools/review_composita_changes.py --report scratch/comparison.json --reviews tests/data/grammar_release_review.json --allowlist scratch/approved.json --audit-output scratch/review-audit.json
python tools/compare_composita.py --inventory scratch/grammar-runtime.json --baseline scratch/baseline.json --output scratch/comparison-checked.json --allow-engine-changes --allowlist scratch/approved.json --check
```

Prvé porovnanie pri rozdieloch zámerne skončí neúspešne, ale uloží report. `--allow-engine-changes` povoľuje porovnať rôzne revízie, **neschvaľuje rozdiely**. Posudzovací nástroj schváli len presné prechody podľa evidovaných PSP rozhodnutí; neschválené zmeny aj zastarané schválenia poslednú kontrolu zablokujú. Kontrolujú sa všetky štyri režimy `hyphenate`/`break_points` a `divisions`, nie iba predvolené delenie. Rozhodnutia AI neprepisujú Human review.

Audit uchováva analýzy, podporné tvary a autorské deklarácie; runtime JSON iba inventár a metadáta vstupov. SHA-256 identifikuje normalizovaný korpus, doplnok, gramatické súbory aj generátor, nie právne oprávnenie. Builder odmieta prepísať produkčný inventár a kontroluje zmenu zdrojov počas behu. Nasadenie vyžaduje plnú API kontrolu kvality a výslovné posúdenie zdrojových deklarácií a zostávajúcich neistôt správcom. Pri vlastnom `--corpus` sa štandardný doplnok nepridáva automaticky; treba explicitné `--supplement`.

Gramatika na zostavenie, slovný inventár aj review databázy chýbajú vo wheeli a sú v zdrojovom archíve. Regenerovanie preto funguje z checkoutu aj z `pip download --no-binary :all: slabika`; bežné používanie knižnice nepotrebuje ani jedno.

## Architektúra

| modul | zodpovednosť |
| --- | --- |
| `slabika.phonology` | inventár foném: dĺžka, znelosť, miesto a spôsob artikulácie, mäkkosť |
| `slabika.syllabify` | členenie hovorených slabík |
| `slabika.typo` | písané deliace body, poradie jazykových ciest, typografické obmedzenia |
| `slabika.phonotactics` | správnosť tvarov, rytmický zákon, vokalizácia predložiek |
| `slabika.language` | spoločné poradie EN/DE/FR/SK a samostatná konzervatívna jazyková evidencia |
| `slabika.foreign` | explicitné cudzie čítania a napojenie slovenských koncoviek |
| `slabika.english`, `slabika.english_projection` | voliteľné G2P, projekcia hlások do písmen, obmedzená anglická morfológia |
| `slabika.foreign_patterns` | nemecké a francúzske vzorové návrhy s PSP úpravami |
| `slabika.review.server`, `slabika.review.foreign` | slovenské review aktuálneho enginu a oddelené cudzojazyčné review uložených návrhov |

`syllabify` a `typo` nie sú potrubie, kde druhý iba filtruje prvý. Samostatne rozhodujú nad spoločnou analýzou: hovorené `ma·slo` a typografické `mas|lo` sa môžu oprávnene líšiť. Cudzojazyčná typografická podpora neznamená všeobecnú implementáciu EN/DE/FR v `syllables()`.

Typografický výstup rozlišuje preferované body, kodifikované varianty (`all_points=True`) a prípustné, ale nepreferované body (`contextual=True`). Napríklad `vše·obec·ne` sa s kontextovými bodmi rozšíri na `vše·o·bec·ne`. Širšie anglické a DE/FR adaptéry zatiaľ vracajú len preferované body, neklasifikujú každú cudziu hranicu do troch úrovní.

## Cudzie slová v slovenskom texte

### 1. N-gramy sú jazyková evidencia

`language_scores(word)` porovnáva angličtinu, nemčinu, francúzštinu a slovenčinu spoločným modelom **znakových 3-, 4- a 5-gramov**, vrátane značiek okrajov slova. Ide o úseky písmen izolovaného slova, nie o skupiny slov vo vete. `detect_language` vyberá najvyššie skóre; skóre nie je kalibrovaná pravdepodobnosť. Pri nevhodnom vstupe alebo bez zhôd môže vrátiť `None`.

Samostatné `is_english`, `is_german`, `is_french` a funkcie `*_evidence` používajú profily s prahmi skóre, podpory a pokrytia. Nemusia súhlasiť navzájom ani so spoločným poradím. Rozpoznaný základ a slovenská prípona môžu poskytnúť silnejšiu evidenciu než celý tvar. Ručné jazykové príznaky v review neprepisujú smerovanie produkčného enginu.

Spoločný profil eviduje historickú makropriemernú presnosť **91,50 %**: EN 88,28 %, DE 96,39 %, FR 85,67 %, SK 95,65 %. Ide o jazykové značky odvodené zo zdrojových korpusov, nie o nezávisle posúdené jazyky a už vôbec nie o presnosť delenia. Spoločné zápisy boli vyradené a príbuzné pravopisné rodiny zoskupené pri rozdelení dát.

### 2. Skutočné poradie ciest

1. Automatické smerovanie celého slova vyžaduje alfabetický vstup. Prednosť má malá tabuľka posúdených cudzích delení.
2. Nasledujú explicitné rodiny z `foreign_readings.json`: vyžadujú jednoznačnú jazykovú evidenciu a opísané čítanie. Spracúvajú aj deklarované slovenské koncovky.
3. Potom sa skúša voliteľná anglická cesta: angličtina musí vyhrať spoločné poradie a zároveň musí existovať anglická profilová evidencia **alebo** členstvo v pribalenom anglickom inventári. Domáce lexikálne čítania sú chránené.
4. Nasleduje DE/FR adaptér, ak súhlasí spoločné poradie a príslušný jazykový profil. Pri rozpoznanom nemeckom základe so slovenskou koncovkou môže jazyk základu prevážiť nad poradím celého tvaru.
5. Pri nesplnených podmienkach či nedostupnom modeli zostáva slovenská/lexikálna cesta; nepodporovaný zápis môže zostať bez delenia. Návrat na pôvodnú cestu nie je dôkaz správnosti cudzieho delenia.

Nie je to teda iba „zisti jazyk a vždy spusti jeho adaptér“. `Schneiderovská` môže mať celkový slovenský odhad, no nemecký základ umožní zmiešanú analýzu. Explicitné čítanie `Sternwoodovi` zase nepotrebuje, aby celé slovo vyhralo ako anglické.

### 3. Najprv výslovnosť: angličtina a opísané rodiny

`foreign.py` pri deklarovaných EN/DE/FR rodinách mapuje písané jednotky na zjednodušené hláskové roly, aplikuje slovenské pravidlá a prevedie hranice späť na pôvodné písmená. Viacpísmenové hláskové jednotky zostávajú celé; opísané morfematické švíky a koncovky sú súčasťou analýzy.

Širšia angličtina využíva samostatný balík `slabika-pronunciation`, ktorý predpovedá hlásky aj ich zarovnanie k úsekom zápisu. `english_projection.py` opravuje úzko rozpoznané chyby zarovnania, vyhľadáva jadrá a spoluhláskové skupiny, premieta PSP hranice späť do písmen a spracúva zdvojené spoluhlásky. **Naša je vrstva delenia/projekcie nad cudzím natrénovaným modelom výslovnosti**, nie celý výslovnostný model.

Obmedzená morfológia navyše rozpoznáva podporované zloženiny na `-knife/-knives`, `-house/-houses` a niektoré tvary na `-ly`. Overuje členy v korpuse aj kompatibilné výslovnosti, nie ľubovoľné spojenie podreťazcov. `english_morphology_members.json` obsahuje **55 637 tvarov**, nie IPA, ľudské rozhodnutia ani uložené deliace body.

Širšia cesta prijíma ASCII alfabetické zápisy; všeobecné pripájanie slovenských prípon k anglickým základom nemá. To zostáva v explicitných rodinách. Ak runtime chýba, zlyhá alebo neposkytne úplnú projekciu, cesta sa nepoužije. Napríklad `people` dá s runtime `peo·ple`, bez neho pôvodná cesta `pe·op·le`.

### 4. Najprv vzory: nemčina a francúzština

Druhá stratégia používa **TeXové vzory**, nie súvislý text ani G2P prepis počas delenia. `hyph-de-1996.tex` a `hyph-fr.tex` navrhnú pôvodné hranice a lokálne pravopisno-hláskové pravidlá ich prispôsobia PSP. Väčšina pôvodných bodov sa nemení: je to heuristický adaptér, nie úplný fonologický či morfologický dôkaz pre každé slovo.

Príklady úprav: nemecké `Kat·ze → Ka·tze` (ochrana `tz`), `Fens·ter → Fen·ster`, francúzske `pa·trie → pat·rie` a vybrané hiáty. `adapt_foreign_word` vracia `native_points`, výsledné `points` a pomenované `changes`. Voliteľné `morpheme_points` umožňujú dodať nezávisle doložené švíky; automatické smerovanie všetky takéto švíky neobjavuje.

```python
>>> slabika.foreign_hyphenate("patrie", "fr")
'pat·rie'
>>> result = slabika.adapt_foreign_word("Katze", "de")
>>> result.native_points, result.points
((3,), (2,))
>>> result.render("-")
'Ka-tze'
```

Explicitné API obchádza jazykový detektor, podporuje DE/FR, používa okrajové minimá 2/2 a zvláda aj normalizáciu Unicode a apostrofy. Automatické smerovanie celého slova je prísnejšie. Nejde o certifikované delenie podľa cudzojazyčných noriem.

### 5. Nemecký základ so slovenskou príponou

Slovenské `á` v prípone už samo osebe nevyradí nemecký základ. Adaptér zachová vnútorné nemecké delenie a slovenskými pravidlami spracuje príponu aj spojenie. Pred spoluhláskovou príponou ostáva švík; pred samohláskovou sa môžu prerozdeliť posledné spoluhlásky základu.

Skupiny `sch`, `ch`, `ck`, `tz` a `ng` sa na tomto spojení mapujú ako hláskové jednotky. Samotná nedeliteľnosť ešte neurčuje, na ktorej strane hranice jednotka zostane: koncové nemecké `ng` patrí ako kóda [ŋ] k základu, pretože nemôže otvárať nasledujúcu slovenskú slabiku. Samotná slovenská prípona nedokazuje vznik samostatného [g]. Konkrétny umelo odvodený tvar nižšie nemá nezávisle doloženú výslovnosť.

| vstup | aktuálny výstup `hyphenate()` |
| --- | --- |
| `Frankensteinovi` | `Fran·ken·stei·no·vi` |
| `Sternwoodovi` | `Stern·woo·do·vi` |
| `Beaurevoiru` | `Beau·re·voi·ru` |
| `Pickelgeringen` | `Pi·ckel·ge·rin·gen` |
| `Schneiderovská` | `Schnei·de·rov·ská` |
| `Arbeitsunfähigkeitsbescheinigung` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gung` |
| `Arbeitsunfähigkeitsbescheinigungovská` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gung·ov·ská` |
| `people` (voliteľné G2P) | `peo·ple` |
| `pepper` (voliteľné G2P) | `pep·per` |
| `penknife` (voliteľné G2P) | `pen·knife` |
| `modestly` (voliteľné G2P) | `mo·dest·ly` |
| `penthouse` (voliteľné G2P) | `pent·house` |

Sú to regresné príklady overené 2026-09-12, nie certifikovaný PSP gold súbor. Jazykový odhad, výslovnosť aj morfológia zostávajú omylné.

## Inštalácia a revízne konzoly

Jadro je **alfa verzia 0.4.0** pre Python 3.10+ bez povinných runtime závislostí:

```console
python -m pip install slabika
slabika-review --db /cesta/k/lokalnemu/inventory.sqlite
```

Pre editovateľný zdrojový checkout s testovacími a licenčnými nástrojmi použite namiesto toho `python -m pip install -e ".[dev]"`.

DE/FR vzory a explicitné čítania sú pribalené. Širšia angličtina potrebuje samostatne zostavený a nainštalovaný `slabika-pronunciation==0.1.0`; na PyPI nie je a vydanie jadra 0.4.0 ho zámerne nedeklaruje ako inštalovateľný extra balík. Zostavenie a obmedzenia opisuje [pronunciation/README.md](pronunciation/README.md). Modely majú samostatné licencie a otvorené provenienčné otázky; nejde o neobmedzené vydanie iba pod MIT.

Od verzie 0.4.0 sú pracovné inventáre a review databázy vylúčené z wheelu, ale sú v zdrojovom archíve a zostávajú verzované v repozitári. Checkout aj rozbalený archív si korpus nájdu samy a nepotrebujú ďalšie argumenty; `--db` otvorí inventár mimo nich. Slovenské review počíta **aktuálny výstup enginu**, vrátane prípustných cudzích ciest. Rozhodnutia ukladá oddelene do `review_decisions.sqlite` v spúšťacom priečinku; `--decisions` vyberá iný súbor. Zdrojový checkout naďalej automaticky nájde svoj lokálny korpus; ten je potrebný aj na celokorpusové testy a regenerovanie gramatického inventára. `run_review_local.bat` je pre externého recenzenta, bez inštalácie a s rozhodnutiami v `%LOCALAPPDATA%\slabika-review`. Správcovský `run_review.bat` zámerne otvára verzované rozhodnutia projektu.

Klasifikácia oddeľuje automatické profily, ľudské príznaky a import/AI. Neurčený jazyk nie je automaticky slovenčina. Textový upload vytvára pracovný zoznam; **Náhodných 200** vyberá abecedný blok nerevidovaných tvarov. Typografické delenie a hovorené slabiky sa posudzujú samostatne.

### Samostatné DE/FR/EN review

`run_review_de.bat`, `run_review_fr.bat`, `run_review_en.bat` spúšťajú oddelené inventáre a rozhodnutia. Predvolené požadované porty sú SK 8765, DE 8766, FR 8767 a EN 8768; server môže vybrať ďalší voľný. Po vytvorení cudzích inventárov možno použiť:

```console
slabika-review --language de
slabika-review --language fr
slabika-review --language en
```

`--foreign-dir` v checkoute predvolene ukazuje na `tests/data/foreign_review`; každý jazyk má `<jazyk>.sqlite` a `<jazyk>_decisions.sqlite`. Veľké lokálne databázy nie sú pribalené v obyčajnom checkoute ani wheeli a spúšťače ich samy nevytvárajú ani nesťahujú.

Tieto konzoly zobrazujú **uložené návrhy a vygenerovanú IPA**, stav, pôvodné hlásky, zarovnanie a model. Jazyk dodáva korpus, preto sa automatický detektor obchádza. DE/FR návrh delenia nezávisí od zobrazenej G2P výslovnosti. IPA je automatický odhad bez overenia a bez odhadovania prízvuku. Nie je tu editor cudzích hovorených slabík ani porovnanie s Chlebíkovou.

Rovnaké slovo má v každom korpuse nezávislé rozhodnutia. Ochrany odmietajú zámenu jazykov či slovenského úložiska. Zmena enginu ani generovaných návrhov neprepisuje ľudské rozhodnutia. Reštart slovenského servera načíta nový engine; **reštart cudzojazyčnej konzoly sám neprepočíta uložené návrhy**.

## Nástroje pre cudzie jazyky

Nástroje správcu používajú lokálne zdrojové korpusy vrátane TranslateMaster a anglickej cache. Knižnica ich potichu nesťahuje. Pred regenerovaním skontrolujte argumenty a predvolené cesty; router builder používa importované predvolené cesty. Foreign builder používa `hashlib.file_digest` z Pythonu 3.11, hoci jadro podporuje 3.10.

| nástroj | účel a zapisovanie |
| --- | --- |
| `tools/build_german_profile.py` | n-gramový profil DE/SK a auditné metadáta |
| `tools/build_french_profile.py` | profil FR/SK |
| `tools/build_english_profile.py` | profil EN/SK; voliteľné `--download` pre deklarovaný výber Gutenberg |
| `tools/build_language_router_profile.py` | porovnateľné poradie štyroch jazykov, rodinné rozdelenie a metriky korpusových značiek |
| `tools/audit_foreign_routing.py` | korpusový výstup smerovania a porovnanie so základňou |
| `tools/evaluate_foreign_corpora.py` | experiment na odložených korpusoch, smerovanie a voliteľná výslovnostná projekcia |
| `tools/evaluate_foreign_adapter.py` | DE/FR pôvodné a upravené delenia v TSV, zmeny a pokrytie, nie meranie správnosti |
| `tools/build_foreign_review.py` | vytvorenie/pokračovanie oddelených inventárov, IPA, návrhov, stavov a hashov modelov; bez zásahu do ľudských rozhodnutí |
| `tools/refresh_english_review.py` | prepočet uložených EN zarovnaní spoločnou projekciou; predvolene dry-run, `--apply` zálohuje a mení iba generované návrhy |
| `tools/export_english_morphology.py` | export členstva tvarov do runtime JSON, bez IPA a ľudských hraníc |
| `pronunciation/` | samostatný natívny balík, modelový manifest, atribúcie a testy |

Typický postup pri dostupných lokálnych korpusoch a runtime:

```console
python tools/build_foreign_review.py --language all
python tools/refresh_english_review.py
python tools/refresh_english_review.py --apply
python tools/export_english_morphology.py
```

Builder vloží všetky tvary a v obnoviteľných transakciách spracúva čakajúce/chybné riadky. `--limit` obmedzuje generovanie, nie vloženú slovnú zásobu. Úspešnú staršiu evidenciu zachováva; nejde o úplný refresh. Anglický dry-run treba prezrieť pred `--apply`, ktorý dopĺňa aj morfologické spresnenie. Členstvo exportujte po zmene zdrojového inventára. Explicitné korpusové review a automatické smerovanie nemusia pri každom tvare dať totožný výsledok.

## Dáta a stav kontroly

Stav verzovaných slovenských dát k **2026-09-14**:

| metrika | počet |
| --- | ---: |
| riadky inventára | **206 272** |
| aktívne jedinečné tvary v review po zlúčení iba veľko-/malopísmenkových aliasov | **206 200** |
| uložené riadky Human rozhodnutí (surová tabuľka) | **19 737** |
| aktívne kanonické tvary s ľubovoľnou Human evidenciou | **19 572 (9,49 %)** |
| skontrolované typografické delenia | **19 406 (9,41 %)** — 18 236 potvrdení, 1 170 opráv |
| skontrolované hovorené slabikovania | **346 (0,17 %)** — pri 264 tvaroch sú skontrolované oba výstupy |

Surových 19 737 riadkov tvorí 18 448 posledných akcií `confirm`, 1 218 `correct`, 37 `classify`, 25 `uncertain`, 8 `invalid` a 1 `flag`. Surová tabuľka zahŕňa aj odstránené tvary a veľko-/malopísmenkové aliasy, preto nie je čitateľom pokrytia; pokrytie používa aktuálny kanonický pohľad konzoly. Klasifikácia a slabikovanie sa evidujú oddelene od typografického delenia. Ľudské rozhodnutia sú evidencia, nie normatívna autorita.

| lokálny korpus | tvary | vygenerovaná IPA | návrhy delenia |
| --- | ---: | ---: | --- |
| DE | 131 150 | 131 150 | 131 150 kandidátnych |
| FR | 35 552 | 35 546 | 35 552 kandidátnych, aj pri 6 chybách IPA |
| EN | 55 638 | 55 637 | 53 331 úplných experimentálnych, 2 306 neúplných, 1 chyba |

Počty cudzích korpusov nie sú presnosť ani počet ľudsky overených slov.

Štyri zmrazené slepé audity obsahujú 8 100 rozhodnutí nad 8 028 tvarmi: 6 601 vyriešených, 1 477 neistých a 22 chybných. Izolovaní LLM recenzenti dostali holé tvary bez enginu a starších názorov, neboli to kontroly autora. Dvojmodelová evidencia obsahuje 17 behov, 1 346 posúdení nad 1 239 tvarmi, s modelovými pozíciami `claude-opus-5[high]` a `gpt-6-astra[sub][high]`: 1 079 nezávislých zhôd, 145 po krížovej kontrole, 23 po zmierení a 99 nerozhodnutých posúdení nad 71 tvarmi.

### Porovnávací súbor posúdený podľa PSP

Verzovaná databáza `tests/data/review_decisions.sqlite` obsahuje nemenný auditný rad `engine-chlebikova-exhaustive-2026-08-25-v1`: všetkých **23 173 jedinečných tvarov**, pri ktorých sa zmrazený engine a pribalené vzory z roku 1992 nezhodli pri rovnakých okrajových minimách 2/3. Tvary boli deterministicky zoradené a posúdené v 232 dávkach najviac po 100. Pri každom porovnaní sa uchováva pôvodný výstup, navrhnuté delenie a varianty podľa PSP, samostatný verdikt pre engine a Chlebíkovú, odkaz na PSP, zdôvodnenie a klasifikácia nerozhodnutého prípadu. Autorské rozhodnutia, slepé kontroly a dvojmodelová adjudikácia zostávajú oddelenou evidenciou; nehlasujú a navzájom sa neprepisujú.

Výsledky sú **15 313 iba engine**, **6 195 oba správne**, **1 iba Chlebíková**, **5 ani jeden** a **1 659 nerozhodnutých**: 21 514 uzavretých porovnaní, nie 23 173 certifikovaných odpovedí. Počty možno reprodukovať z tabuľky `psp_comparisons` filtrovaním podľa uvedeného `audit_id` a zoskupením podľa `comparison_outcome`; každý zmrazený tvar má zodpovedajúci riadok posúdenia. Ide o **porovnávací súbor posúdený podľa PSP**, nie o nezávislý náhodný gold benchmark: úplná interpretácia PSP vznikala s pomocou AI, výber obsahuje iba historické nezhody a neistá cudzia výslovnosť zostala zámerne nerozhodnutá.

K 2026-09-14 sa aktívne neodstránené Human riadky prekrývajú s PSP radom na **2 236 tvaroch**; pri 2 224 z nich existuje porovnateľné Human delenie. PSP uzavrelo 1 981 týchto porovnateľných prípadov: Human sa zhoduje aspoň s jedným prípustným PSP variantom v **1 858** a nezhoduje v **123**, teda zhoda je **93,79 %**. Ďalších 243 porovnateľných prípadov zostáva vo vrstve PSP nerozhodnutých. Prienik nerobí z vrstiev totožné ani nezávislé gold benchmarky; ľudský názor ani modelový konsenzus nenahrádza argument z PSP.

## Liangove vzory: regenerovanie a hodnotenie

Nainštalujte vývojové nástroje cez `python -m pip install -e ".[dev]"` a pridajte `patgen` z TeX Live alebo MiKTeXu na `PATH`. Z koreňa repozitára:

```console
python tools/liang_experiment.py --mode preferred --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

Príkazy prepíšu dva verzované súbory vzorov; bez `--patterns-output` sa release artefakty nedotknú a všetko sa zapíše do výstupného priečinka. Generátor prijíma `resolved`/`inferred` tvary, vynechá vyradené `invalid`, prevedie na malé písmená, odstráni duplikáty a nepodporované zápisy. Deterministické rozdelenie používa soľ `slabika-liang-v1`. Pridáva generované číslovky; príslušné korpusové číslovky presunie do tréningu, aby neboli aj v teste. Výstup zahŕňa `train.dic`, `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` a `report.json` s počtami, hashmi, metrikami a ukážkami nezhôd.

Generovanie **2026-09-15** prijalo 203 919 podporovaných unikátnych slov: **163 156 tréningových a 40 763 odložených**. Preferovaný súbor má **5 562 vzorov**, presné celé slová **98,5060 %** (40 154/40 763), precision bodov 99,5614 % a recall 99,4479 %. Permisívny má **5 233 vzorov**, presné celé slová **98,6409 %** (40 209/40 763), precision 99,5846 % a recall 99,5214 %. Pri rovnakých minimách TeXu 2/3 zopakuje základňa Chlebíkovej príslušné ciele na 89,5690 % a 88,9704 % celých slov. Ide o **vernosť enginu**, nie nezávislú správnosť podľa PSP. Použitý bol Python 3.11.9, MiKTeX-PATGEN 1.0 (MiKTeX 26.5) a `slabika-pronunciation==0.1.0` s anglickým MFA G2P v3.0.0. Súbory sa zapisujú s LF aj na Windows; presné SHA-256 sú v časti **Reproduce and evaluate Liang patterns** v [anglickom README](README.md), úplné reporty release behu sú v `patterns/`. Zmena enginu, inventára alebo prítomnosti anglického runtime môže zmeniť výsledné hashe.

Preferovaný súbor sa učí z `break_points(word)`, permisívny z `break_points(word, all_points=True, contextual=True)`. Jeden Liangov súbor nevie niesť prioritu bodov, preto sa tieto politiky publikujú samostatne a **nesmú sa načítať naraz**. Nemajú výnimky celých slov a neobsahujú jazykový detektor ani model výslovnosti. Sú verzovanými release artefaktmi popri Python balíku, ale knižnica ich automaticky nenačítava; používa iba prevzaté DE/FR vzory.

### Regenerovanie zo zverejneného zdrojového archívu

Zdrojový archív je sebestačný: nesie vstupy, dôkazy, pipeline aj testy. Netreba checkout ani samostatne sťahovaný korpus.

```console
pip download --no-binary :all: --no-deps slabika
tar -xf slabika-0.4.0.tar.gz
cd slabika-0.4.0
python -m pip install -e ".[dev]"
python -m pytest
python tools/liang_experiment.py --mode preferred --output-dir liang-preferred
python tools/liang_experiment.py --mode permissive --output-dir liang-permissive
```

Na Windows bez editovateľnej inštalácie použite `set PYTHONPATH=src&& python -m pytest`; generátor si cesty rieši sám a `PYTHONPATH` nepotrebuje.

Databázy v archíve, všetky pod `tests/data/`:

| súbor | veľkosť | čo to je | načo treba |
| --- | ---: | --- | --- |
| `translatemaster_hyphenation_working.sqlite` | 13,9 MB | inventár 206 272 tvarov, SHA-256 `480904ef…` | regenerovanie vzorov, celokorpusové testy, review konzola |
| `review_decisions.sqlite` | 42,6 MB | všetky ľudské rozhodnutia, vyčerpávajúce porovnanie s Chlebíkovou a dvojmodelové adjudikácie | overenie tvrdení o provenancii, testy štatistík v README |
| `blind_*/manifest.sqlite`, `blind_*/results.sqlite` | 3,9 MB | štyri zmrazené slepé audity s podpísanými manifestmi | kontroly slepých auditov, review konzola |

V archíve sa dobre stlačia, takže `.tar.gz` má asi 16,7 MB; wheel zostáva na 3,5 MB a databázy neobsahuje vôbec. Toto rozdelenie vynucuje `python tools/audit_release_artifacts.py --inventory src/slabika/data/composita.json <archív>`: databáza kdekoľvek mimo `tests/data/` je chyba a databáza vo wheeli je chyba vždy.

**Čo archív dodať nemôže.** Dve veci sú externý toolchain a nedajú sa tu redistribuovať:

- `patgen` — nainštalujte TeX Live alebo MiKTeX a dajte ho na `PATH`. Bez neho sa generátor zastaví pred syntézou vzorov.
- voliteľný anglický model G2P — `pip install slabika-pronunciation` (asi 40 MB). Bez neho sa menia označenia cudzích slov, takže hashe nebudú sedieť s publikovaným behom, hoci pipeline dobehne.

S obidvoma nainštalovanými sa beh zopakuje celý. Bez nich prebehne engine, filtrovanie korpusu aj hodnotenie, ale výsledné hashe sú potom vaše, nie release. Report zaznamenáva každý vstupný hash presne preto, aby bol tento rozdiel viditeľný, nie tichý.

### Použitie inde

Štandardné Liangove vzory možno načítať TeX-kompatibilným nástrojom alebo previesť pre Hunspell-style delenie v LibreOffice, OpenOffice, Scribuse či Pyphen, prípadne pre JavaScriptový Hyphenopoly. Každý cieľ vyžaduje formát, kódovanie, minimá, registráciu a testovanie. Skopírovanie `.tex` súboru ho nenainštaluje; webové API na vloženie vlastných vzorov do CSS `hyphens: auto` nie je.

Vzory predpovedajú iba písané deliace body, nie hovorené slabiky, morfematické vysvetlenie ani tri úrovne priorít.

## Validácia a známe hranice

```console
python -m pytest
python -m ruff check .
reuse lint
```

Pri zdrojovom Windows behu použite `set PYTHONPATH=src&& python -m pytest`; po zmene enginu overujte v čerstvom procese, nie cez staré importy. Release beh z 2026-09-15 eviduje **1 145 úspešných testov, 1 očakávané zlyhanie a žiadne neočakávané zlyhania**. Prešli aj Ruff a kontroly REUSE 3.3. Súlad s REUSE eviduje deklarované licencie a oznámenia; nerieši stále neistý pôvod a právne vysporiadanie tréningových dát voliteľných modelov MFA.

Obmedzenia zahŕňajú neistú identitu jazyka, neúplnú morfológiu, nejednoznačné zarovnanie písmen a hlások a heuristické DE/FR úpravy. `hyphenate` môže nepodporovaný zápis ponechať nezmenený; `syllables` pri nepodporovaných alfabetických znakoch môže vyvolať `ValueError`. Prázdne body nerozlišujú nepodporovaný vstup od správneho slova bez možného delenia. Projekt neuvádza certifikovanú celkovú PSP presnosť.

## Ako prispieť

**Autoritou je kapitola V PSP.** Projektovú referenciu obsahuje [docs/pravidla-delenia-slov.md](docs/pravidla-delenia-slov.md). Engine, TeX, AI aj ľudské review sú porovnávacie hlasy, nie autority. Projekt nie je spojený s JÚĽŠ SAV ani ním schválený.

V review zapisujte hranice pomocou `-` alebo `·`, bez zmeny písmen. Príznakmi označujte mená, cudzie slová, skratky, neistotu a chybné tvary. Doplňte konkrétne pravidlo PSP, výslovnosť alebo morfematickú analýzu, príbuzné a kontrastné tvary. **Stiahnuť opravy** exportuje časovo označený `slabika-corrections` JSON návrhov, ktoré sa stále líšia od enginu, aj s poznámkami a provenienciou. Export sám nerobí návrh kanonickým.

Slovnú zásobu dopĺňajte len z vlastného materiálu alebo verejnej domény, nie výpisom z cudzích slovníkov či lexikálnych databáz. Publikované izolované tvary neuchovávajú vety, poradie slov ani štruktúru zdrojového textu. Pozri [CONTRIBUTING.md](CONTRIBUTING.md) a [LICENSING.md](LICENSING.md).

## Licencie

| vrstva | licencia |
| --- | --- |
| projektový kód | `Apache-2.0 OR MIT` |
| projektové jazykové dáta, slovenské vzory, dokumentácia | `CC0-1.0 OR MIT` |
| prevzaté DE/FR vzory a Chlebíková | MIT, zachované pôvodné oznámenia |
| voliteľné výslovnostné modely | upstream deklarácie CC-BY-4.0; samostatná atribúcia a posúdenie proveniencie |

Vlastné vrstvy projektu ponúkajú aj MIT; **nemení to licencie cudzích modelov**. Alternatíva MIT obchádza nekompatibilitu Apache-2.0 s GPL-2.0-only a MPL-1.1. Výslovnostný balík má vlastné oznámenia v [pronunciation/MODEL_ATTRIBUTION.md](pronunciation/MODEL_ATTRIBUTION.md) a [pronunciation/THIRD_PARTY_NOTICES.md](pronunciation/THIRD_PARTY_NOTICES.md). Prevádzková funkčnosť nie je dôkaz voľnej redistribúcie. Licencia kódu nástroja sama neurčuje práva ku každému odvodenému datasetu či modelu.

CC0 výslovne rieši aj európske osobitné právo k databáze. Je to **vzdanie sa práv voči verejnosti**, nie iba voľba názvu vo firemnom registri. MIT nerieši osobitné databázové práva; výber MIT neruší nezávisle aplikované CC0. Komu ide o právo k databáze, ktoré MIT nerieši, môže sa oprieť o CC0.

**Samotné licenčné podmienky CC0 neukladajú povinnosť uvádzať autora.** Nedotýka sa to osobnostných práv, ktorých sa podľa použiteľného práva vzdať nemožno. Pri šírení kódu zostávajú oznámenia vyžadované zvolenou licenciou MIT alebo Apache-2.0. Projekt nemá dodatočný Apache `NOTICE`. Právne záväzné texty sú v `LICENSES/` a v deklaráciách konkrétnych súborov; toto je len zhrnutie.

## Autor a východiská

**Peter Bezemek** — <peter.bezemek@gmail.com>, [@pietrobb](https://github.com/pietrobb).

Klasifikácia foném vychádza z knihy **Emila Páleša**, *Sapfo — parafrázovač slovenčiny: počítačový nástroj na modelovanie v jazykovede* (VEDA, Bratislava 1994, ISBN 80-224-0109-9), kapitola 2 *Fonológia*. Páleš uvádza **J. Dvončovú** (1980) a **J. Horeckého** (1977). Klasifikácia tvorí hláskový základ; slabikovanie, morfematická analýza a deliace algoritmy nad ním sú samostatná práca projektu. Pálešova kniha sa delením slov nezaoberá.

Chlebíkovej vzory z roku 1992 zostávajú porovnávacou základňou pod MIT. Metodika merania a dôraz na kvalitu tréningového zoznamu vychádzajú aj z práce O. Metelku a P. Sojku *Hyph-bench: Benchmark Dataset of Hyphenated Words for Generating Hyphenation Patterns*, RASLAN 2025.
