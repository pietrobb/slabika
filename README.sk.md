# slabika

Slovenské slabikovanie a typografické rozdeľovanie slov na konci riadka — dva samostatné výsledky založené na spoločnej hláskovej a morfematickej analýze.

```python
>>> import slabika
>>> slabika.syllables("najneuveriteľnejšími")
['naj', 'ne', 'u', 've', 'ri', 'teľ', 'nej', 'ší', 'mi']
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

Nezačalo sa to ako jazykovedný projekt, ale ako sadzobný problém: autor potreboval sádzať slovenský text automaticky — na danú šírku, do bloku a so správnym delením — bez človeka, ktorý by výsledok prechádzal riadok po riadku. Zarovnaný riadok je buď zlomený na prípustnom mieste, alebo je zle a čitateľ to vidí okamžite.

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

### Najťažšia časť: vnímaný kmeň

Vokalické jadrá, rozdelenie spoluhlások a okrajové obmedzenia sú často mechanické až po určení jazykovej analýzy. Morfematické švíky sú ťažšie: rovnaký zápis môže znamenať produktívnu predponu a rozpoznateľný kmeň alebo zlexikalizovaný celok. Zo samotných písmen sa to nedá spoľahlivo určiť.

Široká slovná zásoba poskytuje evidenciu na testovanie rodín a kontrastných prípadov. Uprednostňujeme najužšie doložené zovšeobecnenie pred zapamätaním jednotlivého slova. Súčasný kód však obsahuje aj malú explicitnú tabuľku posúdených cudzích delení popri lexikálnych čítaniach; tvrdenie, že je úplne bez výnimiek, by nebolo presné. Nevyriešené prípady zostávajú viditeľné.

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

Skupiny `sch`, `ch`, `ck`, `tz` a `ng` sa na tomto spojení mapujú ako hláskové jednotky. `ng` zostáva celé pri predpoklade zachovanej nemeckej výslovnosti [ŋ]. Samotná slovenská prípona nedokazuje vznik samostatného [g]. Konkrétny umelo odvodený tvar nižšie nemá nezávisle doloženú výslovnosť.

| vstup | aktuálny výstup `hyphenate()` |
| --- | --- |
| `Frankensteinovi` | `Fran·ken·stei·no·vi` |
| `Sternwoodovi` | `Stern·woo·do·vi` |
| `Beaurevoiru` | `Beau·re·voi·ru` |
| `Pickelgeringen` | `Pi·ckel·ge·rin·gen` |
| `Schneiderovská` | `Schnei·de·rov·ská` |
| `Arbeitsunfähigkeitsbescheinigung` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gung` |
| `Arbeitsunfähigkeitsbescheinigungovská` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gu·ngov·ská` |
| `people` (voliteľné G2P) | `peo·ple` |
| `pepper` (voliteľné G2P) | `pep·per` |
| `penknife` (voliteľné G2P) | `pen·knife` |
| `modestly` (voliteľné G2P) | `mo·dest·ly` |
| `penthouse` (voliteľné G2P) | `pent·house` |

Sú to regresné príklady overené 2026-09-12, nie certifikovaný PSP gold súbor. Jazykový odhad, výslovnosť aj morfológia zostávajú omylné.

## Inštalácia a revízne konzoly

Jadro je **alfa verzia 0.1.0** pre Python 3.10+ bez povinných runtime závislostí:

```console
python -m pip install -e .
slabika-review
```

DE/FR vzory a explicitné čítania sú pribalené. Širšia angličtina potrebuje samostatne zostavený/nainštalovaný `slabika-pronunciation==0.1.0`; extra `pronunciation` deklaruje závislosť, nie dostupnosť verejného wheelu. Zostavenie a obmedzenia opisuje [pronunciation/README.md](pronunciation/README.md). Modely majú samostatné licencie a otvorené provenienčné otázky; nejde o neobmedzené vydanie iba pod MIT.

Slovenské review číta inventár a počíta **aktuálny výstup enginu**, vrátane prípustných cudzích ciest. Rozhodnutia ukladá oddelene do `review_decisions.sqlite` v spúšťacom priečinku; `--db` a `--decisions` vyberajú iné súbory. `run_review_local.bat` je pre externého recenzenta, bez inštalácie a s rozhodnutiami v `%LOCALAPPDATA%\slabika-review`. Správcovský `run_review.bat` zámerne otvára verzované rozhodnutia projektu.

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

Stav k **2026-09-12**: slovenský inventár má **206 272 tvarov**, úložisko rozhodnutí **17 944 riadkov**: 16 742 `confirm`, 1 149 `correct`, 25 `uncertain`, 19 `classify`, 8 `invalid`, 1 `flag`. Sú to akcie uložených riadkov, nie automaticky dokončené kontroly typografického delenia; slabikovanie a klasifikácia sa evidujú zvlášť.

| lokálny korpus | tvary | vygenerovaná IPA | návrhy delenia |
| --- | ---: | ---: | --- |
| DE | 131 150 | 131 150 | 131 150 kandidátnych |
| FR | 35 552 | 35 546 | 35 552 kandidátnych, aj pri 6 chybách IPA |
| EN | 55 638 | 55 637 | 53 331 úplných experimentálnych, 2 306 neúplných, 1 chyba |

Tieto počty nie sú presnosť ani počet ľudsky overených slov. Starší inventár 195 230 tvarov mal 10 210 autorských rozhodnutí (9 519 potvrdení, 660 opráv, 22 neistých, 8 chybných, 1 označený). Zjednotenie s vtedajšími slepými auditmi pokrývalo 14 970 tvarov, prienik 3 268; nejde o dnešné percentá pokrytia.

Štyri zmrazené slepé audity obsahujú 8 100 rozhodnutí nad 8 028 tvarmi: 6 601 vyriešených, 1 477 neistých a 22 chybných. Izolovaní LLM recenzenti dostali holé tvary bez enginu a starších názorov, neboli to kontroly autora. Dvojmodelová evidencia obsahuje 17 behov, 1 346 posúdení nad 1 239 tvarmi, s modelovými pozíciami `claude-opus-5[high]` a `gpt-6-astra[sub][high]`: 1 079 nezávislých zhôd, 145 po krížovej kontrole, 23 po zmierení a 99 nerozhodnutých posúdení nad 71 tvarmi.

Vrstvy sa prekrývajú, preto sa nesčítavajú na „počet skontrolovaných slov“. Staršie porovnanie autora a AI našlo 49 nezhôd v 350 spoločných tvaroch, v 14 rodinách. Je to historické meranie, nie počet dnes otvorených sporov. Ľudský názor ani modelový konsenzus nenahrádza nezávislý argument z PSP.

## Liangove vzory: regenerovanie a hodnotenie

Nainštalujte vývojové nástroje cez `python -m pip install -e ".[dev]"` a pridajte `patgen` z TeX Live alebo MiKTeXu na `PATH`. Z koreňa repozitára:

```console
python tools/liang_experiment.py --mode preferred --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

Príkazy prepíšu dva verzované súbory vzorov. Generátor prijíma `resolved`/`inferred` tvary, vynechá vyradené `invalid`, prevedie na malé písmená, odstráni duplikáty a nepodporované zápisy. Deterministické rozdelenie používa soľ `slabika-liang-v1`. Pridáva generované číslovky; príslušné korpusové číslovky presunie do tréningu, aby neboli aj v teste. Výstup zahŕňa `train.dic`, `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` a `report.json` s počtami, hashmi, metrikami a ukážkami nezhôd.

Generovanie **2026-09-12** prijalo 203 919 podporovaných unikátnych slov: **163 156 tréningových a 40 763 odložených**. Preferovaný súbor má **5 577 vzorov**, presné celé slová **98,4643 %** (40 137/40 763), precision bodov 99,5399 % a recall 99,4341 %. Permisívny má **5 259 vzorov**, presné celé slová **98,6115 %** (40 197/40 763), precision 99,5682 % a recall 99,5101 %. Pri rovnakých minimách TeXu 2/3 zopakuje základňa Chlebíkovej príslušné ciele na 89,5886 % a 89,0489 % celých slov. Ide o **vernosť enginu**, nie nezávislú správnosť podľa PSP. Použitý bol Python 3.11.9, MiKTeX-PATGEN 1.0 (MiKTeX 26.5) a `slabika-pronunciation==0.1.0` s anglickým MFA G2P v3.0.0. Súbory sa zapisujú s LF aj na Windows; presné SHA-256 sú v časti **Reproduce and evaluate Liang patterns** v [anglickom README](README.md), úplné reporty v `patterns/`. Oproti starším 98,6866 %/98,8240 % ide o mierny pokles, ale zmenil sa aj engine a testovací inventár. Zmena enginu, inventára alebo prítomnosti anglického runtime môže zmeniť výsledné hashe.

Preferovaný súbor sa učí z `break_points(word)`, permisívny z `break_points(word, all_points=True, contextual=True)`. Jeden Liangov súbor nevie niesť prioritu bodov, preto sa tieto politiky publikujú samostatne a **nesmú sa načítať naraz**. Nemajú výnimky celých slov, neobsahujú jazykový detektor ani model výslovnosti a nie sú finálnym vydaním. Python balík nepoužíva vlastné slovenské vzory; DE/FR upstream vzory však používa.

Staršie vzory Chlebíkovej slúžia ako porovnávacia základňa v `tex/hyph-sk.tex`. Ich vznik podľa autorky opisuje [docs/hyph-sk-1992-povod.md](docs/hyph-sk-1992-povod.md). Rozdiely často ukazujú morfematické švíky: pri minimách 2/3 napríklad `be·z·od·kladne` oproti `bez·od·kladne`, `na·jús·peš·nejší` oproti `naj·ús·peš·nejší`, či `rozum` oproti `ro·zum`. Nie je to automaticky zoznam chýb: nesúhlas dvoch systémov treba posúdiť podľa PSP.

### Použitie inde

Štandardné Liangove vzory možno načítať TeX-kompatibilným nástrojom alebo previesť pre Hunspell-style delenie v LibreOffice, OpenOffice, Scribuse či Pyphen, prípadne pre JavaScriptový Hyphenopoly. Každý cieľ vyžaduje formát, kódovanie, minimá, registráciu a testovanie. Skopírovanie `.tex` súboru ho nenainštaluje; webové API na vloženie vlastných vzorov do CSS `hyphens: auto` nie je.

Vzory predpovedajú iba písané deliace body, nie hovorené slabiky, morfematické vysvetlenie ani tri úrovne priorít.

## Validácia a známe hranice

```console
python -m pytest
python -m ruff check .
reuse lint
```

Pri zdrojovom Windows behu použite `set PYTHONPATH=src&& python -m pytest`; po zmene enginu overujte v čerstvom procese, nie cez staré importy. Plný beh z 2026-09-12 eviduje **931 úspešných testov, 1 očakávané zlyhanie a 3 licenčné/provenienčné zlyhania**. Jazykové a revízne regresie prešli; otvorené sú deklarácie voliteľných modelov, chýbajúci koreňový text CC-BY-4.0 a klasifikácia samostatného výslovnostného podstromu. Testy správnosti kódu nie sú schválením redistribučnej proveniencie.

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
