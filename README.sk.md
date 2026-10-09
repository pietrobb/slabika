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
| inventár 206 205 izolovaných tvarov a revízna evidencia | `tests/data/` | `CC0-1.0 OR MIT` |
| engine a generátor | `src/slabika/`, `tools/liang_experiment.py` | `Apache-2.0 OR MIT` |
| výsledné slovenské Liangove vzory | `patterns/` | `CC0-1.0 OR MIT` |
| prevzaté DE/FR vzory | `src/slabika/patterns/foreign/` | MIT, pôvodné oznámenia zachované |

Tréningové delenia počíta engine, nepreberá sa hotový slovenský slovník delenia. Cudzie slová však môžu využívať DE/FR vzorové adaptéry alebo voliteľné anglické G2P. Na presnú reprodukciu preto treba rovnaký engine, inventár **aj výslovnostné prostredie**. Provenienciu slovnej zásoby vysvetľuje [LICENSING.md](LICENSING.md) §3. Reprodukovateľnosť ani zhoda s enginom nedokazujú správnosť podľa PSP.

### Prečo nový súbor slovenských vzorov

Jana Chlebíková zverejnila slovenské Liangove vzory v roku 1992; slúžia slovenskej sadzbe celé desaťročia a v `tex/hyph-sk.tex` zostávajú pribalenou porovnávacou základňou. Jej metóda bola starostlivým ručným prepisom gramatických pravidiel do Liangovej notácie, nie tréningom `patgen` nad zverejneným zoznamom slov. Bolo to dôležité praktické riešenie a tento projekt si nenárokuje prvenstvo delenia slovenčiny. Primárny opis a neskoršie hodnotenie sumarizuje [docs/hyph-sk-1992-povod.md](docs/hyph-sk-1992-povod.md).

Historický súbor však nestačí ako základ systému, ktorý sa má dať preskúmať a zlepšovať. Jeho úplný vznik nemožno zopakovať; písmenové úseky si neuchovávajú jazykové zdôvodnenie ani morfematickú analýzu hranice; cudzie slová a výnimky boli spracované iba obmedzene. To neznamená, že pôvodná práca bola zlá. Je to hodnotná historická základňa, ktorej praktické hranice dnes vieme zmerať a cielene opravovať.

Rozsah týchto hraníc ukazuje toto meranie:

| evidencia | súčasný projekt | Chlebíková 1992 | čo výsledok dokazuje |
| --- | ---: | ---: | --- |
| presné celé slová na odložených dátach oproti preferovanému cieľu enginu, minimá TeXu 2/3 | **98,7438 %** | **90,4191 %** | reprodukovateľnosť enginu, nie správnosť podľa PSP |

Častou príčinou rozdielu je **rozpoznaná morfematická stavba**: predpona a základ, členy zloženiny alebo základ a slovotvorná či gramatická prípona. Písmenové vzory vidia opakujúce sa úseky, ale túto analýzu si neuchovávajú. Nasleduje 21 overených morfologických príkladov, nie prípadov vyhlásených za chybu iba preto, že sa dva systémy nezhodli. `·` označuje dostupné miesto zalomenia. Stĺpec vzorov z roku 1992 používa TeXové okrajové minimá 2/3; stĺpec aktuálneho enginu je doslovný výsledok `hyphenate(word)`, ktorého API tieto minimá neuplatňuje.

| typ | slovo | rozpoznaná stavba | vzory 1992 | aktuálny engine |
| --- | --- | --- | --- | --- |
| predpona a základ | `bezodkladne` | `bez- + od- + klad-` | `be·z·od·kladne` | `bez·od·klad·ne` |
| predpona a základ | `najúspešnejší` | `naj- + úspeš- + nejš-` | `na·jús·peš·nejší` | `naj·úspeš·nej·ší` |
| predpona a základ | `rozkroj` | `roz- + kroj-` | `rozk·roj` | `roz·kroj` |
| vnorené predpony | `neočistí` | `ne- + o- + čist-` | `ne·očistí` | `ne·očis·tí` |
| predpona a základ | `predúradné` | `pred- + úrad- + n-` | `pre·dú·radné` | `pred·úrad·né` |
| zloženina | `trojuholník` | `troj- + uhol- + ník` | `tro·j·u·hol·ník` | `troj·uhol·ník` |
| zloženina | `samoobslužný` | `samo- + ob- + služ- + n-` | `sa·mo·obs·lužný` | `sa·mo·ob·služ·ný` |
| zloženina | `sebaistý` | `seba- + ist-` | `se·baistý` | `se·ba·is·tý` |
| zloženina | `pravouhlý` | `pravo- + uhl-` | `pra·vouhlý` | `pra·vo·uh·lý` |
| zloženina | `novovzbudený` | `novo- + vzbud- + en-` | `no·vovz·bu·dený` | `no·vo·vzbu·de·ný` |
| zloženina | `mäsožravce` | `mäso- + žrav- + ec` | `mä·sož·ravce` | `mä·so·žrav·ce` |
| zloženina | `pomstychtivý` | `pomsty- + chtiv-` | `po·mstych·tivý` | `po·msty·chti·vý` |
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

Bežný používateľ inventár **neregeneruje**; používa pribalený JSON. Overenie pokrýva **206 205 korpusových riadkov**, pričom jazykové rozhodnutia sa posudzujú podľa PSP. Testovacia sada má **viac ako 1 570 úspešných testov s jedným očakávaným zlyhaním**. Tieto kontroly nezaručujú správnu analýzu každého slova. Zdroje dát a licencie uvádza [LICENSING.md](LICENSING.md).

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

Od verzie 0.4.0 sú pracovné inventáre a review databázy vylúčené z wheelu, ale sú v zdrojovom archíve a zostávajú verzované v repozitári. Checkout aj rozbalený archív si korpus nájdu samy a nepotrebujú ďalšie argumenty; `--db` otvorí inventár mimo nich. Slovenské review počíta **aktuálny výstup enginu**, vrátane prípustných cudzích ciest. Rozhodnutia ukladá oddelene do `review_decisions.sqlite` v spúšťacom priečinku; `--decisions` vyberá iný súbor. `run_review_local.bat` je pre externého recenzenta, bez inštalácie a s rozhodnutiami v `%LOCALAPPDATA%\slabika-review`. Správcovský `run_review.bat` zámerne otvára verzované rozhodnutia projektu.

Rozhodnutia projektu sú v repozitári skomprimované ako `tests/data/review_decisions.sqlite.xz` (13,0 MB namiesto 56,4 MB). Konzola si pracovnú kópiu `tests/data/review_decisions.sqlite` vedľa neho rozbalí podľa potreby: keď chýba, alebo keď `git pull` priniesol novší `.xz` a kópia nemá vlastné zmeny. Pri riadnom ukončení (Ctrl+C) nové rozhodnutia zabalí späť do `.xz`, ktorý sa potom commituje. Ak sa zmenil `.xz` aj rozbalená kópia, konzola sa nespustí, aby neprepísala ani jedno. Ručne to isté robí `python -m slabika.review.packed status|unpack|pack [--force]`. Súbor rozhodnutí zadaný cez `--decisions`, vedľa ktorého nie je `.xz`, sa otvára ako doteraz.

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

Stav verzovaných slovenských dát k **2026-10-09**:

| metrika | počet |
| --- | ---: |
| riadky inventára | **206 184** |
| aktívne jedinečné tvary v review po zlúčení iba veľko-/malopísmenkových aliasov | **206 112** |
| uložené riadky Human rozhodnutí (surová tabuľka) | **27 168** |
| aktívne kanonické tvary s ľubovoľnou Human evidenciou | **26 837 (13,02 %)** |
| skontrolované typografické delenia | **26 661 (12,94 %)** — 25 002 potvrdení, 1 659 opráv |
| skontrolované hovorené slabikovania | **349 (0,17 %)** — pri 266 tvaroch sú skontrolované oba výstupy |

Surových 27 168 riadkov tvorí 25 293 posledných akcií `confirm`, 1 709 `correct`, 121 `classify`, 36 `uncertain`, 8 `invalid` a 1 `flag`. Surová tabuľka zahŕňa aj odstránené tvary a veľko-/malopísmenkové aliasy, preto nie je čitateľom pokrytia; pokrytie používa aktuálny kanonický pohľad konzoly. Klasifikácia a slabikovanie sa evidujú oddelene od typografického delenia. Ľudské rozhodnutia sú evidencia, nie normatívna autorita.

| lokálny korpus | tvary | vygenerovaná IPA | návrhy delenia |
| --- | ---: | ---: | --- |
| DE | 131 150 | 131 150 | 131 150 kandidátnych |
| FR | 35 552 | 35 546 | 35 552 kandidátnych, aj pri 6 chybách IPA |
| EN | 55 638 | 55 637 | 53 331 úplných experimentálnych, 2 306 neúplných, 1 chyba |

Počty cudzích korpusov nie sú presnosť ani počet ľudsky overených slov.

Štyri zmrazené slepé audity obsahujú 8 100 rozhodnutí nad 8 028 tvarmi: 6 601 vyriešených, 1 477 neistých a 22 chybných. Izolovaní LLM recenzenti dostali holé tvary bez enginu a starších názorov, neboli to kontroly autora.

### Verzované verdikty dvoch modelov

`tests/data/review_decisions.sqlite` (v repozitári ako `review_decisions.sqlite.xz`) ukladá každý beh dvoch modelov spolu s presnými vstupmi, z ktorých vznikol. Tabuľky `ai_rule_sets`, `ai_prompts` a `ai_schemas` obsahujú celý text pravidiel, prompt a schému odpovede pod označením verzie; `ai_models` pomenúva modely; `engine_versions` zaznamenáva verziu balíka, Git commit, príznak necommitnutých zmien a obsahový hash enginu, s ktorým sa beh porovnával. `ai_runs` spája beh so všetkými týmito údajmi a uchováva jeho komprimovaný prepis, `ai_verdicts` obsahuje jeden výsledok na tvar a `ai_model_answers` každú odpoveď modelu v každom kole. Do tabuliek sa iba pridáva: zmenený text pravidiel je nová verzia a staršie verdikty zostávajú čitateľné spolu s pravidlami, podľa ktorých vznikli. `tools/review/import_ai_run.py` odmietne beh, ktorého hashe v dávkach nesedia s textami, pod ktoré sa má zapísať.

Prvý zapísaný beh `blind1000-20260930` (pravidlá r1, prompt v4, schéma s1, `claude-opus-5-5[high]` s `gpt-6.1-sol[sub][high]`) pokrýva 1 000 tvarov vybraných rovnomerne náhodne z inventára: 862 nezávislých zhôd, 26 zhôd po dohadovaní, 40 neistých, 2 nezhody a 70 neplatných odpovedí. Z 888 dohodnutých tvarov sa 860 zhoduje s výstupom enginu v čase behu a 28 sa líši. Zhoda modelov je poradná evidencia, nie verdikt podľa PSP, a nikdy neprepisuje Human rozhodnutie.

Doteraz je zapísaných dvanásť behov, spolu **37 331 verdiktov nad 37 323 rôznymi tvarmi** a 76 035 uložených odpovedí modelov:

| beh | pravidlá / prompt / schéma | tvary | zhoda (nezávislá + po dohadovaní) | neisté | nezhoda | neplatné | zhoda, ale iná ako engine v čase behu |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `blind1000-20260930` | r1 / v4 / s1 | 1 000 | 888 (862 + 26) | 40 | 2 | 70 | 28 |
| `blind3331-20261001` | r5 / v8 / s2 | 3 331 | 3 137 (3 083 + 54) | 172 | 2 | 20 | 268 |
| `blind3000-20261002` | r5 / v8 / s2 | 3 000 | 2 849 (2 818 + 31) | 128 | 3 | 20 | 89 |
| `blind2000-20261003` | r6 / v8 / s2 | 2 000 | 1 845 (1 831 + 14) | 92 | 3 | 60 | 44 |
| `blind3000b-20261003` | r6 / v8 / s2 | 3 000 | 2 768 (2 735 + 33) | 130 | 2 | 100 | 63 |
| `blind3000c-20261004` | r7 / v8 / s2 | 3 000 | 2 861 (2 834 + 27) | 136 | 3 | 0 | 61 |
| `blind3000d-20261004` | r7 / v8 / s2 | 3 000 | 2 557 (2 466 + 91) | 424 | 9 | 10 | 447 |
| `blind3000e-20261005` | r7 / v8 / s2 | 3 000 | 2 674 (2 570 + 104) | 311 | 15 | 0 | 268 |
| `blind4000f-20261007` | r7 / v8 / s2 | 4 000 | 3 788 (3 659 + 129) | 197 | 15 | 0 | 206 |
| `blind4000g-20261008` | r7 / v8 / s2 | 4 000 | 3 874 (3 775 + 99) | 109 | 17 | 0 | 72 |
| `blind4000h-20261008` | r7 / v8 / s2 | 4 000 | 3 861 (3 766 + 95) | 127 | 12 | 0 | 58 |
| `blind4000i-20261009` | r7 / v8 / s2 | 4 000 | 3 870 (3 810 + 60) | 123 | 7 | 0 | 66 |

Dohodnuté tvary, ktoré sa líšili od enginu, posúdil operátor. Prijaté delenia sa do enginu premietli pre **celú slovnú rodinu**, nie iba pre jeden tvar, a sú zafixované regresnými testami; zamietnuté ponechávajú delenie enginu a sú zafixované tiež. Po behu `blind3000b` operátor prijal 60 z jeho 63 rozdielov a rozšíril ich na rodiny (napríklad `kar·dio·ló·go·via`, `bú·ria·ce` s vyslovovanou dvojhláskou, ale `špe·ci·a·lis·ta` s vyslovovaným hiátom, `ne·opý·tam`, `úsko·koch`, `úc·ty·hod·ný`, `von·kajš·ko·vo`); ponechal `prázd·nej·ších`, `sto·trid·sať·šty·ri` a `šty·rid·sia·ti·de·via·ti`. Dvanásť starších Human potvrdení, ktoré prijatým rodinám odporovali, bolo prepísaných auditovanou cestou; predchádzajúca hodnota zostáva v `decision_log.previous_json`.

Po behu `blind3000c` operátor prijal 57 z jeho 61 rozdielov: samohláska alebo krátky nábeh na začiatku koreňa za predponou či na začiatku slova zostáva s koreňom (`ohľa·de`, `ozveš`, `usta·vič·ný`, `po·obe·do·val`, `za·opat·ru·je`, `ideo·ló·gi·ou`), viaceré spoluhláskové skupiny prechádzajú do nasledujúcej slabiky (`di·va·dla·mi`, `ka·di·dlu`, `ha·cko·va·nia`, `ne·jde·te`, `šnu·ro·va·čky`) alebo zostávajú pri predchádzajúcej (`jem·nos·ti`, `vi·ce·pre·zi·den·tom`, `pries·tran·ný` ako `pries·tor`, `zú·čast·ňo·va·li`) a niekoľko cudzích slov sa delí podľa výslovnosti (`In·di·a·mi`, `koz·mo·nau·ta`, `grape·frui·te`). Deväť prijatých rodín zmenilo staršie zafixované rozhodnutia (`ot·vo·rí`, `po·msta`, `odo·pie·rať`, `záz·rak`, `naš·la`, `očist·ca`, `za·mest·nan·ci`, `tan·co·va·čky`, `upra·to·va·čka`). Operátor ponechal `bejz·ba·lis·ta`, `pa·žra·vo`, `pot·ký·na·jú` a `na·vrst·ve·né`. Dvadsaťtri Human potvrdení v zmenených rodinách bolo prepísaných tou istou auditovanou cestou. Beh bol spustený s označením r6, hoci jeho text pravidiel už obsahoval doplnky prvých častí zloženín z `blind3000b`; je zapísaný ako r7 a importér takéto preznačenie prijme iba s písomným zdôvodnením.

`blind3000d` nebol rovnomerný výber: obsahoval 831 tvarov, pri ktorých sa s enginom rozchádzali publikované Liangove vzory, a 2 169 tvarov, pri ktorých sa s ním rozchádzali vzory Chlebíkovej z roku 1992; preto má oveľa vyšší podiel rozdielov. Operátor prešiel všetkých 447 po skupinách a prijal 391; tri slovesá z rodiny `-tknúť` dostali vlastné delenie operátora (`ne·pot·kla`, `ne·zat·kli`), lebo všetky slovesá na `-tknúť` sa teraz delia za `t`. Zvyšných 53 si ponecháva delenie enginu (napríklad `fi·al·kám`, `pot·kli`, `poz·dĺž·nej`, `úcti·vá`, `na·vni·voč`, `ozve·na·mi`). Prijaté delenia sa opäť premietli do celých rodín: predpona zostáva celá pred nábehom alebo samohláskou koreňa (`ovlá·da`, `usko·čí`, `úska·lie`, `ne·opil`, `zo·vše·obec·ní`, `pra·ide·a·mi`), tvary `vyjsť`, `nejsť` a `začať` sa delia za prvou spoluhláskou skupiny (`vyj·de`, `nej·de`, `zač·ne`), kmeň rozhoduje v `úcty·hod·ný`, `ost·na·tý`, `kost·na·tý`, `pre·do·šlé`, `von·kajš·ka`, `vešt·ba` a v slovách na `-os·ti` (`jas·nos·ti`) a cudzie mená sa delia podľa výslovnosti (`Gei·ge·rov·ho`, `Shake·spea·rov`). Viaceré z týchto rodín zmenili staršie zafixované rozhodnutia (`ne·jde·te`, `úc·ty·hod·ný`, `von·kaj·škom`, `pre·doš·lý`, `dis·ku·sia·mi`). Päť Human potvrdení v zmenených rodinách (`ovláda`, `zovšeobecní`, `úctyhodný`, `začne`, `začnú`) bolo prepísaných auditovanou cestou.

`blind3000e` bol vybraný rovnako z doteraz neposúdených tvarov. Z jeho 268 rozdielov operátor prijal 186 a pri 68 ponechal delenie enginu, väčšinou tam, kde rodinu už pokrývalo staršie rozhodnutie (`pot·kne`, `zač·ni·te`, `vyj·dú`, `naš·lo`, `úcti·vom`, `vrst·va·mi`, `an·gi·o·lóg`, `upo·doz·rie·vať`); 13 zostáva otvorených a zatiaľ si ponecháva delenie enginu a `ne·na·vrst·vi·lo` nasleduje rodinu `vrst·va`. Prijaté rodiny: predpona zostáva celá pred samohláskou alebo nábehom koreňa (`ne·oso·žia`, `za·ode·nej`, `ovla·že·nie`, `obo·hra·tá`, `ospr·cho·val`, `úspe·chy`, `úspeš·ní`), viaceré kmene si ponechávajú spoluhláskovú skupinu (`al·geb·ra`, `met·re`, `rif·le`, `ne·dôs·toj·nom`, `zne·uc·ti·lo`, `žried·lo`, `pišt·ci`), zložené slová zachovávajú svoje časti (`dez·or·ga·ni·zá·cia`, `pro·ti·otáz·ke`, `psy·cho·ana·lý·ze`, `pra·otec`) a cudzie mená sa delia podľa výslovnosti (`Shake·spea·ra`, `Frank·fur·tu`). Tvary na `-si·a·mi` a `-zi·a·mi` sa teraz delia ako `dis·ku·si·a·mi` (`mi·si·a·mi`, `di·men·zi·a·mi`). Šesťdesiatsedem Human potvrdení v zmenených rodinách (`dôstojný`, `úspech`, `zneuctenie`, `dimenziami`, `arcipraotec` a ich tvary) bolo prepísaných auditovanou cestou.

`blind4000f` obsahoval 12 tvarov, pri ktorých sa s enginom rozchádzali publikované Liangove vzory, a 3 988 tvarov, pri ktorých sa s ním rozchádzali vzory Chlebíkovej z roku 1992, opäť iba z doteraz neposúdených tvarov. Z jeho 206 rozdielov operátor prijal 107 a pri 99 ponechal delenie enginu, väčšinou tam, kde rodinu už pokrývalo staršie rozhodnutie (`vyj·de`, `zač·ne`, `pre·do·šlý`, `prázd·ny`, `vrst·va`, `an·ti·kvár`, `teo·ré·ma`, `cent·ná·rov`), a pri desiatkach `šty·rid·sať`, `dvad·sať`, ktorých `-dsať` už nie je živé slovo. Prijaté rodiny: samohláska na začiatku koreňa zostáva za predponou s koreňom (`ne·okú·ša`, `ne·úmer·ne`, `pre·exis·ten·cia`, `uklo·nil`, `omlá·te·ný`, `uchva·ti·teľ`, `ušlia·pa·li`), kmene a časti zložených slov zostávajú celé (`klád·lo`, `pri·vlast·ňu·je`, `roz·pro·stre·nia`, `naj·ozaj·stnej·ší`, `bo·jaz·li·vý`, `kryš·ta·lo·gra·fia`) a opravené boli zjavné chyby enginu (`na·pre·du·je`, `le·gen·da`, `high·ball`). Podstatné mená na `-čka` so základom na samohlásku teraz uprednostňujú bod pred `k` (`hrač·ka`, `tan·co·vač·ky`, `za·sa·dač·ke`, `upra·to·vač·ka`) a `hra·čka` ponechávajú ako prípustný bod; tým sa menia zafixované rozhodnutia `tan·co·va·čky` a `upra·to·va·čka` z behu `blind3000c`. Dvadsať Human potvrdení v zmenených rodinách (`bojazlivý` a `upratovačka` s ich tvarmi) bolo prepísaných auditovanou cestou.

`blind4000g` obsahoval 7 tvarov, pri ktorých sa s enginom rozchádzali publikované Liangove vzory, 2 215 tvarov, pri ktorých sa s ním rozchádzali vzory Chlebíkovej z roku 1992, a 1 778 tvarov vybraných rovnomerne z doteraz neposúdených. Z tých 2 215 dali modely za pravdu enginu v 2 083; z rovnomerne vybraných 1 778 sa s ním zhodli v 1 712. Z jeho 72 rozdielov operátor prijal 14 a pri 58 ponechal delenie enginu, vždy pri rodinách, ktoré už pokrývalo staršie rozhodnutie, test alebo Human potvrdenie (`pos·la·nie`, `úcty·hod·ný`, `prázd·ny`, `po·msty·chti·vý`, `be·ze·ctný`, `dvad·sať`). Prijaté: engine už netvorí slabiku bez samohlásky vo `vy·lha·ný` (ani v `Lha·sa`), `ne·vyk·la` je od `vyknúť` ako `zvyk·la`, `uzrú` sa nedelí ako `uzrie`, `os·lov·ský` je od `Os·lo`, `stereo-` zostáva celé pred `-metria` (`ste·reo·met·ria`) a `In·ter·pret`, `Du·nois`, `fo·to·gra·fi·a·mi` a `spo·lu·vy·sla·nec` nasledujú príbuzné tvary. Tri rodiny s predponou alebo hiátom, ktoré počuli modely, rozhodol operátor: `zá·snu·by`, `ná·klon·nosť` a `Ni·a·ga·ra`. Prepísané boli zafixované delenia `ne·vy·kla` a `vy·l·ha·né` zo starších auditných dávok; žiadne Human potvrdenie sa nezmenilo.

`blind4000h` obsahoval 3 tvary z fronty `?` v konzole, 1 408 tvarov, pri ktorých sa s enginom rozchádzali vzory Chlebíkovej z roku 1992, a 2 589 tvarov vybraných rovnomerne z doteraz neposúdených. Z tých 1 408 dali modely za pravdu enginu v 1 333; z rovnomerne vybraných 2 589 sa s ním zhodli v 2 468. Z jeho 58 rozdielov operátor prijal 8 a pri 50 ponechal delenie enginu, opäť pri rodinách, ktoré už pokrývalo staršie rozhodnutie, test alebo Human potvrdenie (`úcty·hod·ný`, `prázd·ny`, `pos·la·nie`, `dot·kne`, `bejz·bal`, `vlast·ný`, `dvad·sať`). Prijaté, vždy pre celú rodinu: `zá·ste·na` a `zá·šti·ta` zachovávajú predponu ako `zá·snu·by`, `ne·ctia` nasleduje `ne·ctnos·tí`, jednohlásková predpona zostáva s koreňom v `ušľa·pa·ný` a `úžľa·bi·na`, `ka·ri·e·riz·mus` nasleduje `ka·ri·é·ra`, `Brook·ly·ne` číta `oo` ako jednu samohlásku a pri `en·tu·zi·az·mus` zvolil hiát operátor. Z fronty operátor potvrdil `Mur·ray·ho`, kde `ay` je jedna samohláska. Žiadne zafixované delenie ani Human potvrdenie sa nezmenilo.

`blind4000i` obsahoval 811 tvarov, pri ktorých sa s enginom rozchádzali vzory Chlebíkovej z roku 1992, a 3 189 tvarov vybraných rovnomerne z doteraz neposúdených. Z tých 811 dali modely za pravdu enginu v 762; z rovnomerne vybraných 3 189 sa s ním zhodli v 3 042. Z jeho 66 rozdielov operátor prijal 8 a pri 58 ponechal delenie enginu, pri rodinách, ktoré už pokrývalo staršie rozhodnutie, test alebo Human potvrdenie (`úcty·hod·ný`, `prázd·ny`, `pos·la·nie`, `po·msty·chti·vý`, `ot·vá·rať`, `bejz·bal`, `záz·rak`), a pri `pie·tis·ta`. Prijaté, vždy pre celú rodinu: `vyh·ní` nasleduje podstatné meno `vyh·ňa`, `uza·vrú` nasleduje `uza·vrel`, `ar·ma·gnac·kí` nasleduje `ar·ma·gnac`, `se·mi·o·ti·ka` zachováva jednohláskovú slabiku a hiát v `di·a·dém` a `va·ri·e·té` zvolil operátor. `Rouen` sa riadi francúzskou výslovnosťou [rwɑ̃], jedna slabika ako `Du·nois`: `Rouen`, `Roue·ne`, `rouen·ský`. Beh odhalil aj krátke slovenské tvary, ktoré engine čítal ako anglické alebo francúzske slová s nemým *e* a nedelil ich; `ho·re`, `mo·re`, `po·le`, `ro·le`, `ba·be`, `lo·ne`, `pa·ce` a ďalších 21 sa teraz delí po slovensky, čo zodpovedá aj Human potvrdeniam `ba·be`, `lo·ne` a `pa·ce`. Žiadne zafixované delenie sa nezmenilo.

Staršie porovnanie enginu s Chlebíkovou a staršie dvojmodelové adjudikácie boli 2026-10-01 odstránené, lebo sa nedali priradiť k zaznamenanému textu pravidiel a promptu. Zostávajú dostupné v histórii Gitu.

## Liangove vzory: regenerovanie a hodnotenie

Nainštalujte vývojové nástroje cez `python -m pip install -e ".[dev]"` a pridajte `patgen` z TeX Live alebo MiKTeXu na `PATH`. Z koreňa repozitára:

```console
python tools/liang_experiment.py --mode preferred --train-on-all --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --train-on-all --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

Príkazy prepíšu dva verzované súbory vzorov; bez `--patterns-output` sa release artefakty nedotknú a všetko sa zapíše do výstupného priečinka. Generátor prijíma `resolved`/`inferred` tvary, vynechá vyradené `invalid`, prevedie na malé písmená, odstráni duplikáty a nepodporované zápisy. Deterministické rozdelenie používa soľ `slabika-liang-v1`. S `--train-on-all` sa model s rozdelením trénuje len na meranie zovšeobecnenia (v `<output-dir>/holdout`); zapísaný súbor vznikne z druhého behu na všetkých slovách, takže release súbory nevynechávajú žiadnu časť inventára. Pridáva generované číslovky; príslušné korpusové číslovky presunie do tréningu, aby neboli aj v teste. Výstup zahŕňa `train.dic`, `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` a `report.json` s počtami, hashmi, metrikami a ukážkami nezhôd.

Generovanie **2026-10-09** z enginu s rodinami prijatými z AI review (behy po `blind4000i-20261009`) prijalo 203 879 podporovaných unikátnych slov. **Odhad zovšeobecnenia:** model trénovaný na 163 121 slovách a meraný na 40 758 odložených. Preferovaný model má 5 417 vzorov, presné celé slová **98,7438 %** (40 246/40 758), precision bodov 99,5892 % a recall 99,5957 %. Permisívny má 5 096 vzorov, presné celé slová **98,8150 %** (40 275/40 758), precision 99,6184 % a recall 99,6286 %. Pri rovnakých minimách TeXu 2/3 zopakuje základňa Chlebíkovej príslušné ciele na 90,4191 % a 89,5677 % celých slov. `patgen` beží v šiestich úrovniach: štyri sú z profilu cshyphen (Metelka a Sojka, Hyph-bench 2025, tabuľka 4), dve ďalšie majú vzory dĺžky 2–8 a váhy 1/2/1. Pri štyroch úrovniach posledná, blokujúca úroveň zrušila asi 460 správnych bodov, ktoré už žiadna ďalšia úroveň nevedela obnoviť. **Publikované súbory** sú trénované na všetkých 203 879 slovách: preferovaný má **5 939 vzorov** a samotné vzory delia presne 99,9990 % slov inventára (203 877) s 2 chybnými a 0 vynechanými bodmi; permisívny má **5 523 vzorov**, 99,9971 % (203 873), 4 chybné a 2 vynechané body. Tieto slová (2 a 6) sú na konci súborov v zozname výnimiek `\hyphenation`, takže súbory delia všetky slová inventára presne ako engine. Toto druhé číslo ukazuje len vernosť na videných slovách; pre nové slová platí odhad zovšeobecnenia. Ide o **vernosť enginu**, nie nezávislú správnosť podľa PSP. Použitý bol Python 3.11.9, MiKTeX-PATGEN 1.0 (MiKTeX 26.5) a `slabika-pronunciation==0.1.0` s anglickým MFA G2P v3.0.0. Súbory sa zapisujú s LF aj na Windows; presné SHA-256 sú v časti **Reproduce and evaluate Liang patterns** v [anglickom README](README.md), úplné reporty release behu sú v `patterns/`. Zmena enginu, inventára alebo prítomnosti anglického runtime môže zmeniť výsledné hashe.

Preferovaný súbor sa učí z `break_points(word)`, permisívny z `break_points(word, all_points=True, contextual=True)`. Jeden Liangov súbor nevie niesť prioritu bodov, preto sa tieto politiky publikujú samostatne a **nesmú sa načítať naraz**. Výnimky celých slov sú v nich len v spomenutom krátkom zozname; neobsahujú jazykový detektor ani model výslovnosti. Sú verzovanými release artefaktmi popri Python balíku, ale knižnica ich automaticky nenačítava; používa iba prevzaté DE/FR vzory.

### Regenerovanie zo zverejneného zdrojového archívu

Zdrojový archív je sebestačný: nesie vstupy, dôkazy, pipeline aj testy. Netreba checkout ani samostatne sťahovaný korpus.

```console
pip download --no-binary :all: --no-deps slabika
tar -xf slabika-0.4.0.tar.gz
cd slabika-0.4.0
python -m pip install -e ".[dev]"
python -m pytest
python tools/liang_experiment.py --mode preferred --train-on-all --output-dir liang-preferred
python tools/liang_experiment.py --mode permissive --train-on-all --output-dir liang-permissive
```

Na Windows bez editovateľnej inštalácie použite `set PYTHONPATH=src&& python -m pytest`; generátor si cesty rieši sám a `PYTHONPATH` nepotrebuje.

Databázy v archíve, všetky pod `tests/data/`:

| súbor | veľkosť | čo to je | načo treba |
| --- | ---: | --- | --- |
| `translatemaster_hyphenation_working.sqlite` | 13,9 MB | inventár 206 205 tvarov, SHA-256 `6625bda4…` | regenerovanie vzorov, celokorpusové testy, review konzola |
| `review_decisions.sqlite.xz` | 13,0 MB (rozbalený 56,4 MB) | všetky ľudské rozhodnutia a verzované behy dvoch modelov | overenie tvrdení o provenancii, testy štatistík v README |
| `blind_*/manifest.sqlite`, `blind_*/results.sqlite` | 3,9 MB | štyri zmrazené slepé audity s podpísanými manifestmi | kontroly slepých auditov, review konzola |

V archíve sa dobre stlačia; wheel zostáva na 3,5 MB a databázy neobsahuje vôbec. Toto rozdelenie vynucuje `python tools/audit_release_artifacts.py --inventory src/slabika/data/composita.json <archív>`: databáza kdekoľvek mimo `tests/data/` je chyba a databáza vo wheeli je chyba vždy.

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
