# Odkiaľ pochádzajú slovenské vzory z roku 1992

`tex/hyph-sk.tex` — súbor, ktorý distribúcie TeXu dodnes dodávajú ako slovenskú
deliacu tabuľku — je datovaný 24. apríla 1992 a podpísaný Janou Chlebíkovou
z Katedry didaktiky informatiky Univerzity Komenského v Bratislave. Tento
dokument rekonštruuje, ako vznikol, lebo tá história vysvetľuje tvar každého
rozdielu, ktorý voči nemu meriame, a je zároveň najzreteľnejším argumentom pre
to, prečo je prístup zvolený tu iný v podstate, nie iba novší.

Rekonštrukcia nie je dohad. Autorka svoju metódu opísala tlačou a samotný súbor
ten opis nezávisle potvrdzuje.

## Primárny prameň

> Jana Chlebíková. *Ako rozdeliť (slovo) Československo.* Zpravodaj
> Československého sdružení uživatelů TeXu, roč. 1 (1991), č. 4, s. 10–13.
> DOI [10.5300/1991-4/10](https://doi.org/10.5300/1991-4/10),
> trvalý odkaz <http://dml.cz/dmlcz/148815>.

Článok je voľne prístupný v Českej digitálnej matematickej knižnici. Predchádza
dodávanému súboru o rok a opisuje rozpracovanú prácu; súbor z roku 1992 je
hotovým výsledkom presne toho postupu, ktorý článok vykladá.

## Čo autorka hovorí, že urobila

Rozhodujúca veta stavia jej metódu proti Liangovej:

> „Na rozdiel od Lianga, ktorý základ svojich vzorov vyrobil z obrovského
> množstva slov […] (k dispozícii mal Webster's Pocket Dictionary v
> elektronickej forme — zhruba 50 000 slov), použitá metóda je založená priamo
> na prepise gramatických pravidiel na rozdeľovanie slov."

Nebol nijaký tréningový korpus a nijaký beh PATGENu. Vzory sú ručný prepis
pravidiel slovenského pravopisu, zapísaný v Liangovej notácii preto, lebo tú
TeX konzumuje. Článok potom menuje štyri fázy, v poradí:

1. **Mechanické delenie.** Zabrániť deleniu vnútri spřežiek `ch`, `dz`, `dž`
   a dvojhlások `ia`, `ie`, `iu`; každej samohláske dať nepárnu hodnotu, aby
   otvárala slabiku; potom vypísať `2b1b`, `2b1t`, `2b1č` … *pre všetky možné
   dvojice spoluhlások*, pričom `2c1h`, `2d1z`, `2d1ž` treba ručne vyčiarknuť,
   lebo sú to spřežky.
2. **Spoluhláskové zhluky.** Pridať vybrané trojice ako `s3t2r` (*ses-tra*),
   `n3d2r` (*han-dra*), `n3s2k` (*pán-sky*), potom štvorice, pätice a ďalej.
   Autorka označuje tento krok za ťažký a vysvetľuje prečo: pridaním `t3ĺ2k` by
   sa pokazilo už správne delenie slova *otlkať*, lebo slabikotvorné `l`, `ĺ`,
   `r`, `ŕ` sa správajú ako samohlásky.
3. **Predpony a časti zložených slov.** `.do3k4r`, `.bez5`, `5viac3h4`,
   `.štvor3r` … Každá predpona musí za sebou niesť kúsok slovného základu, inak
   by vzor pripustil *do-ktor*.
4. **Prípony, potom cudzie slová a ručný zoznam výnimiek.**

Článok sa uzatvára otázkou zo svojho názvu: *Čes-ko-slo-ven-sko*.

## Čo súbor nezávisle potvrdzuje

Tri vlastnosti `tex/hyph-sk.tex` ten opis potvrdzujú a ani jedna z nich sa
nezlučuje so strojovým generovaním.

**Má nadpisy kapitol.** Osemnásť slovenských komentárov rozdeľuje 2 467 vzorov
presne na fázy, ktoré článok opisuje:

| vzorov | komentár | príklady |
| ---: | --- | --- |
| 22 | `% samohlásky` | `a1 á1 ä1 e1` |
| 713 | `% dvojice spoluhlások` | `2b1b 2b1c 2b1č 2b1d` |
| 24 | `% 2 samohlásky` | `a1í2 a1o2 e1á2` |
| 264 | `% 3 spoluhlásky` | `b2l3b 3b2l3k` |
| 183 | `% 4 spoluhlásky` | `3b2l4č3n 3b2r4b3l` |
| 31 | `% 5 spoluhlások` | `3c4v4r4č3k 3č4ŕ4s3t4v` |
| 3 | `% 6 spoluhlások` | `3c4v4r4n3g4n 3š4k4v4r4k3n` |
| 129 | `% koncovka -ný` | `k4č3ný. k4č3ného.` |
| 34 | `% koncovky -ka` | `l2t3k2a. l2t3k2ou.` |
| 1 | `% koncovka -ty` | `5p4r4s3t` |
| 24 | `% koncovka -ský,-sky` | `b3s4k d3s4k ľ3s4k` |
| 3 | `% koncovky -ština,-čina` | `n2d3č r4z3š2t2` |
| 15 | `% koncovky -stvo` | `b3s4t4v ľ3s4t4v` |
| 658 | `% predpony` | `.bez5 .dvoj5 .cudzo5s4` |
| 279 | `% slovné základy` | `5alkohol 5b4lesk` |
| 57 | `% začiatky slov` | `.cv6 .ch6 .sp6 .st6` |
| 21 | `% koncovky` | `8c4h. 8d4z. 4j4s4ť.` |
| 6 | `% cudzie slová` | `akci3a2 gymnázi3um le2u3kémia` |

PATGEN vypíše plochý zoradený zoznam bez jediného komentára. Obsah členený
podľa gramatických kategórií píše iba človek.

**Obsahuje vzory, ktoré by nijaký korpus nedodal.** Vzor naučený z dát musí byť
podreťazcom niektorého tréningového slova. Keď sa všetkých 2 467 vzorov overí
proti 193 119-slovnej zásobe priloženej v tomto repozitári, **362 z nich opisuje
písmenovú sekvenciu, ktorá sa nevyskytuje v nijakom slovenskom slove** — `2ď1ď`,
`2č1č`, `2b1w`, `2b1x`, `2f1ť`. Blok `% dvojice spoluhlások` je takmer úplný
karteziánsky súčin slovenského spoluhláskového inventára: niekto prešiel abecedu
proti abecede a zapísal pravidlo „medzi dvoma spoluhláskami sa delí“, vrátane
dvojíc, ktoré jazyk nikdy nerealizuje.

**Končí sa ručným zoznamom výnimiek.** `\hyphenation{}` nesie päť položiek —
`dosť`, `me-tó-da`, `me-tó-dy`, `ne-do-stat-ka-mi`, `sep-tem-bra` — slová, ktoré
nevyšli a opravili sa jedno po druhom.

Sedia aj dva menšie detaily. Súbor používa úrovne priority 1 až 8, hoci
generované sady vystačia so štyrmi; Petr Sojka si toho všimol tiež a pripísal to
ručnému autorstvu. A článok z roku 1991 nastavuje obe deliace minimá na 2, kým
súbor z roku 1992 deklaruje `left: 2, right: 3` — parameter sa medzi článkom
a vydaním zmenil.

## Úzke miesto, ktoré autorka sama pomenúva

Článok korpus nielenže vynecháva; jeho absenciu identifikuje ako obmedzujúci
faktor. O spoluhláskových trojiciach:

> „Problém sa teda sústreďuje na získanie zoznamu všetkých možných trojíc
> spoluhlások, vyskytujúcich sa v slovenských slovách. Nejaké štatistické
> výsledky možno nájsť v [3], rozhodne však nie sú uspokojivé."

Odkaz [3] je Mistríkova frekvenčná príručka z roku 1985 — tlačená kniha.
Gramatika pochádzala z Oravcovej a Lacovej školskej príručky slovenského
pravopisu z roku 1976. Oba pramene sú autoritatívne a ani jeden nie je strojovo
čitateľný. Práca bola viazaná na pravidlá preto, lebo v roku 1991 v Bratislave
nebolo na čo iné sa viazať.

Autorka bola k postaveniu výsledku otvorená:

> „Možno niekomu poslúži ako inšpirácia na vytvorenie dokonalejšej verzie […]
> alebo ako ukážka toho, kadiaľ cesta nevedie."

O pravidlách pre cudzie slová a o zozname výnimiek napísala: *„Tejto časti však
nebola zatiaľ venovaná veľká pozornosť.“* Súbor má šesť vzorov pre celú kategóriu
cudzích slov a päť výnimiek. Po tridsiatich štyroch rokoch ich má stále toľko.

## Verdikt z roku 2004 a prečo neprešiel

Petr Sojka sa k problému vrátil v článku *Slovenské vzory dělení slov: čas pro
změnu?* (SLT 2004, s. 67–72). Jeho diagnóza súboru z roku 1992 sa zhoduje
s vyššie uvedenou a dochádza k zrejmému záveru:

> „Lze si ale těžko představit, že by se tímto způsobem podařilo zachytit
> několik miliónů slovních tvarů, které ve slovenštině existují. Na švech
> předpon a složených slov jsou mnohé výjimky, které jdou proti základnímu
> slabičnému principu. Těch jsou ale tisíce, či desetitisíce."

Urobil to, čo si technológia žiada: nazbieral takmer milión slovenských slov,
spustil PATGEN, iteroval bootstrappingom a vykázal vzory, ktoré si s
nepravidelnosťami poradili podstatne lepšie. Odporučil súbor z roku 1992
nahradiť.

Nestalo sa. Distribúcie dodnes dodávajú Chlebíkovú 1992. Jeden z dôvodov je
zaznamenaný v poznámke pod čiarou jeho vlastnej práce:

> „Bohužel výslednou množinu slov nelze volně šířit. Volně přístupný seznam slov
> by umožnil ještě mnohem flexibilnější vytváření variant dělicích vzorů
> optimalizovaných pro konkrétní projekty."

Lepšie vzory existovali a nikto iný ich nevedel zreprodukovať, lebo dáta za nimi
sa nedali zdieľať. Súbor vzorov, ktorého vstupy nie sú dostupné, je pre každý
účel okrem okamžitého použitia rovnako nepriehľadný ako ručne písaný — nedá sa
auditovať, opraviť ani pregenerovať po zmene pravidla.

## Čo robí tento projekt inak

Tri prístupy, tri úzke miesta:

| | Chlebíková 1992 | Sojka 2004 | tento projekt |
| --- | --- | --- | --- |
| o delení rozhoduje | ručne písané pravidlá | súkromný zoznam slov | pravidlový engine v repozitári |
| morfológia | konečný zoznam 994 riadkov | naučená z dát | vypočítaná analýzou |
| tréningový korpus | žiadny | ~10<sup>6</sup> slov, nešíriteľný | 195 767 tvarov, `CC0-1.0 OR MIT` |
| reprodukovateľné treťou stranou | neaplikovateľné | nie | áno, jedným príkazom |
| dôsledok zmeny pravidla | ručná úprava a nádej, že sa nič nepokazilo | nedostupné | znovu spustiť pipeline |

Nejde o to, že vzory tu dosahujú lepšie skóre proti vlastnému cieľu — to číslo
meria vernosť tomuto enginu a o správnosti nedokazuje nič. Ide o to, čo sa stane
nabudúce.

Súbor z roku 1992 sa nedá ďalej rozvíjať bez zopakovania pôvodnej práce. Jeho
morfológia je vyhľadávacia tabuľka: 658 predpôn, 279 slovných základov, 57
začiatkov slov — 994 riadkov vypísaných rukou. Pridať predponu znamená ručne
vyriešiť jej interakciu s každým už prítomným pravidlom pre zhluky, čo je presne
tá pasca `t3ĺ2k` / *otlkať*, ktorú autorka zdokumentovala v roku 1991. Niet
testovej sady, ktorá by povedala, že ste do nej stúpili.

Tu pravidlo žije na jednom mieste. Keď sa v tomto engine opravilo zaobchádzanie
s kompozitnými švami, celá sada vzorov sa z opraveného pravidla pregenerovala
asi za šesťdesiat sekúnd a sada 606 testov ohlásila, čo sa pohlo. Nič sa
neupravovalo ručne a výsledný `.tex` je bajtovo stabilný: rovnaký inventár dá
rovnaký SHA-256. Celá reťaz — slovná zásoba, engine, rozdelenie, volanie
PATGENu, vyhodnotenie, report — je v tomto repozitári pod licenciami, ktoré
komukoľvek dovolia spustiť ju znovu a dostať identický súbor.

To je presne ten rozdiel, o ktorý Sojkova poznámka pod čiarou žiadala — o dvadsať
rokov neskôr.

## Čo to vysvetľuje o nameraných rozdieloch

V hodnotení na odloženej množine zopakujú vzory z roku 1992 delenie tohto enginu
pri 89,62 % celých slov. História vzniku predpovedá presný tvar zvyšných
10,61 % a meranie to potvrdzuje:

- **Chyby chodia po rodinách, nie náhodne.** Morfologická vrstva je konečný
  zoznam. Slovo, ktorého predpona alebo základ sa v tých 994 riadkoch nachádza,
  je rozdelené správne; slovo, ktorého predpona tam nie je, prepadne na
  fonotaktickú vrstvu a švík zmizne. Celé paradigmy preto zlyhávajú naraz.
- **Prevažujúcim zlyhaním je zlom ponúknutý vnútri morfémy** — `be-zodkladne`,
  `na-júspešnejší`, `tro-juholník`. To je víťazstvo vrstvy 1, lebo vrstva 3 pre
  to slovo nemá záznam. Aspoň jeden taký zlom nesie 7,27 % odložených slov.
- **Cudzie slová sú pokryté len okrajovo**, presne ako autorka uviedla: šesť
  vzorov na celú kategóriu.

Nič z toho nie je nedostatok jej remesla. Je to strop metódy, ktorú si zvolila,
za obmedzenia, ktoré pomenovala, v roku, v ktorom pracovala. Ten súbor si plnil
úlohu tridsaťštyri rokov, čo je viac, než dosiahne väčšina softvéru.

## Pramene

1. Jana Chlebíková. *Ako rozdeliť (slovo) Československo.* Zpravodaj CSTUG,
   1(4):10–13, 1991. <http://dml.cz/dmlcz/148815>
2. Jana Chlebíková. *Hyphenation patterns for Slovak*, verzia 2.0, 24. apríla
   1992. Priložené tu ako [`tex/hyph-sk.tex`](../tex/hyph-sk.tex) pod licenciou
   MIT; distribuované v `hyph-utf8` a ako `skhyphen` v `csplain` pre IL2.
3. Petr Sojka. *Slovenské vzory dělení slov: čas pro změnu?* SLT 2004, s.
   67–72. <https://www.fi.muni.cz/usr/sojka/papers/skhyp.pdf>
4. Franklin M. Liang. *Word Hy-phen-a-tion by Com-put-er.* Dizertačná práca,
   Stanfordova univerzita, 1983.
5. Ján Oravec, Vincent Laca. *Príručka slovenského pravopisu pre školy.* SPN,
   Bratislava, 1976. — gramatický prameň, ktorý Chlebíková cituje.
6. Jozef Mistrík. *Frekvencia tvarov a konštrukcií v slovenčine.* VEDA,
   Bratislava, 1985. — štatistický prameň, ktorý označila za nepostačujúci.
