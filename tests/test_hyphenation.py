# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Golden cases for syllabification and typographic hyphenation."""

import pytest

from slabika import (
    break_points,
    divisions,
    hyphenate,
    is_vowel,
    split_into_phonemes,
    syllables as get_syllables,
)
from tools.liang_experiment import (
    cardinal_parts,
    cardinal_word,
    generate_numeral_training_words,
)


def test_slovak_hyphenation_golden_cases():
    expected = {
        "Prekladateľský": "Pre·kla·da·teľ·ský",
        "rozdeľovanie": "roz·de·ľo·va·nie",
        "podzemie": "pod·ze·mie",
        "zemepisný": "ze·me·pis·ný",
        "pastva": "pas·tva",
        "priateľstvo": "pria·teľ·stvo",
        "trojuholník": "troj·uhol·ník",
        "viacfarebný": "viac·fa·reb·ný",
        "MODLOSLUŽOBNÍČKA": "MOD·LO·SLU·ŽOB·NÍČ·KA",
        "stredoamerický": "stre·do·ame·ric·ký",
        "pohľad": "po·hľad",
        "pakľúč": "pa·kľúč",
        "pakľúčov": "pa·kľú·čov",
        "parafráza": "pa·ra·frá·za",
        "parafrázované": "pa·ra·frá·zo·va·né",
        "paragraf": "pa·ra·graf",
        "paragrafoch": "pa·ra·gra·foch",
        "pohľadom": "po·hľa·dom",
        "pohľady": "po·hľa·dy",
        "Opatrnosť": "Opa·tr·nosť",
        "krátkosti": "krát·kos·ti",
        "krátkostí": "krát·kos·tí",
        "krátkozraký": "krát·ko·zra·ký",
        "dôkladne": "dô·klad·ne",
        "ohrada": "ohra·da",
        "ohradený": "ohra·de·ný",
        "ohradzovať": "ohra·dzo·vať",
        "ohradným": "ohrad·ným",
        "ohraničený": "ohra·ni·če·ný",
        "neohraničený": "ne·o·hra·ni·če·ný",
        "ohrádka": "ohrád·ka",
        "ohrádzať": "ohrá·dzať",
        "obohraných": "ob·o·hra·ných",
        "obohratá": "ob·o·hra·tá",
        "rozohrať": "roz·o·hrať",
        "neohrabaný": "ne·o·hra·ba·ný",
        "porkpie": "por·kpie",
        "pornograf": "por·no·graf",
        "pornografickej": "por·no·gra·fic·kej",
        "porisko": "po·ris·ko",
        "porota": "po·ro·ta",
        "Excelencia": "Ex·ce·len·cia",
        "Excelencie": "Ex·ce·len·cie",
        "Excelenciu": "Ex·ce·len·ciu",
        "najnešťastnejší": "naj·ne·šťast·nej·ší",
        "najprostejšiu": "naj·pros·tej·šiu",
        "najistejšiu": "naj·is·tej·šiu",
        "neurológ": "neu·ro·lóg",
        "neurológovia": "neu·ro·ló·go·via",
        "neukrátené": "ne·u·krá·te·né",
        "afrodiziakum": "af·ro·di·zi·a·kum",
        "akciami": "ak·ci·ami",
        "funkciami": "funk·ci·ami",
        "klientka": "kli·ent·ka",
        "koeficientom": "ko·e·fi·ci·en·tom",
        "kocúrieho": "ko·cú·rie·ho",
        "Kazaština": "Ka·zaš·ti·na",
        "Malgaština": "Mal·gaš·ti·na",
        "francúzština": "fran·cúz·šti·na",
        "koliesko": "ko·lies·ko",
        "laoský": "la·o·ský",
        "koktailový": "kok·tai·lo·vý",
        "detail": "de·tail",
        "naivný": "na·iv·ný",
        "aeronauti": "ae·ro·nau·ti",
        "aeronautika": "ae·ro·nau·ti·ka",
        "aleutskí": "ale·ut·skí",
        "aleutských": "ale·ut·ských",
        "naučiť": "na·učiť",
        "nautešujú": "na·ute·šu·jú",
        "arciposlami": "ar·ci·pos·la·mi",
        "arciposlovia": "ar·ci·pos·lo·via",
        "mahagónovohneda": "ma·ha·gó·no·vo·hne·da",
        "mastnoksichtej": "mast·no·ksich·tej",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_aleut_hiatus_does_not_split_later_ou_endings():
    assert get_syllables("aleutskí") == ["a", "le", "ut", "skí"]
    assert get_syllables("Aleutkou") == ["a", "le", "ut", "kou"]


def test_pa_prefix_is_limited_to_the_pakluc_family():
    assert hyphenate("pakľúč") == "pa·kľúč"
    assert hyphenate("pakľúčov") == "pa·kľú·čov"
    assert hyphenate("pahreba") == "pah·re·ba"


def test_para_prefix_is_limited_to_known_families():
    assert hyphenate("paragraf") == "pa·ra·graf"
    assert hyphenate("paragrafov") == "pa·ra·gra·fov"
    assert hyphenate("parafráza") == "pa·ra·frá·za"
    assert hyphenate("paradajka") == "pa·ra·daj·ka"
    assert hyphenate("parazit") == "pa·ra·zit"


def test_pri_prefix_is_recognised_in_the_stup_and_krat_families():
    assert hyphenate("prístup") == "prí·stup"
    assert hyphenate("neprístupný") == "ne·prí·stup·ný"
    assert hyphenate("príkratko") == "prí·krat·ko"


def test_lengthened_na_and_za_prefixes_keep_lexical_root_seams():
    expected = {
        "náklad": "ná·klad",
        "nákladnými": "ná·klad·ný·mi",
        "nástup": "ná·stup",
        "nástupníctvo": "ná·stup·ní·ctvo",
        "prazáklad": "pra·zá·klad",
        "základňa": "zá·klad·ňa",
        "zástup": "zá·stup",
        "zástupcovia": "zá·stup·co·via",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_discovered_stup_families_keep_their_morpheme_seams():
    expected = {
        "priestupok": "prie·stu·pok",
        "rozostupovanie": "ro·zo·stu·po·va·nie",
        "sprístupniť": "sprí·stup·niť",
        "nesprístupnená": "ne·sprí·stup·ne·ná",
        "novonastupujúci": "no·vo·na·stu·pu·jú·ci",
        "rovnostupňové": "rov·no·stup·ňo·vé",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("vstupovať") == "vstu·po·vať"
    assert hyphenate("ustupovať") == "us·tu·po·vať"


def test_discovered_plat_families_keep_their_morpheme_seams():
    expected = {
        "príplatok": "prí·pla·tok",
        "záplata": "zá·pla·ta",
        "právoplatný": "prá·vo·plat·ný",
        "neprávoplatnými": "ne·prá·vo·plat·ný·mi",
        "plnoplatný": "pl·no·plat·ný",
        "spoplatnené": "spo·plat·ne·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("splatil") == "spla·til"
    assert hyphenate("oplatí") == "op·la·tí"


def test_second_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "všestredové": "vše·stre·do·vé",
        "plnoprávny": "pl·no·práv·ny",
        "prirodzenoprávna": "pri·ro·dze·no·práv·na",
        "rovnoprávnosť": "rov·no·práv·nosť",
        "svetskoprávne": "svet·sko·práv·ne",
        "nevychladlo": "ne·vy·chlad·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("sprostredkovanie") == "spros·tred·ko·va·nie"
    assert hyphenate("ústredný") == "ús·tred·ný"
    assert hyphenate("umierať") == "umie·rať"
    assert hyphenate("oklamal") == "ok·la·mal"
    assert hyphenate("sklamal") == "skla·mal"
    assert hyphenate("správny") == "správ·ny"
    assert hyphenate("ochladenie") == "och·la·de·nie"
    assert hyphenate("schladenie") == "schla·de·nie"
    assert hyphenate("svetlochladne") == "svet·loch·lad·ne"


def test_third_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "formotvorné": "for·mo·tvor·né",
        "mierotvorný": "mie·ro·tvor·ný",
        "obrazotvornosť": "ob·ra·zo·tvor·nosť",
        "novotvorba": "no·vo·tvor·ba",
        "novovytvorený": "no·vo·vy·tvo·re·ný",
        "samovytvorený": "sa·mo·vy·tvo·re·ný",
        "spolutvorcami": "spo·lu·tvor·ca·mi",
        "prístav": "prí·stav",
        "novostavieb": "no·vo·sta·vieb",
        "novopostavený": "no·vo·po·sta·ve·ný",
        "vysokopostavený": "vy·so·ko·po·sta·ve·ný",
        "rovnoznačný": "rov·no·znač·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("otvorený") == "ot·vo·re·ný"
    assert hyphenate("pootvorený") == "po·ot·vo·re·ný"
    assert hyphenate("znovuotvorenie") == "zno·vu·ot·vo·re·nie"
    assert hyphenate("stvorený") == "stvo·re·ný"
    assert hyphenate("kosoštvorec") == "ko·so·štvo·rec"
    assert hyphenate("ústavný") == "ús·tav·ný"
    assert hyphenate("zástava") == "zás·ta·va"
    assert hyphenate("chvastavý") == "chvas·ta·vý"
    assert hyphenate("označený") == "oz·na·če·ný"
    assert hyphenate("príznačný") == "príz·nač·ný"
    assert hyphenate("spred") == "spred"
    assert hyphenate("uhladený") == "uh·la·de·ný"
    assert hyphenate("chladný") == "chlad·ný"


def test_fourth_discovered_family_batch_keeps_only_clear_seams():
    assert hyphenate("slovosled") == "slo·vo·sled"
    assert hyphenate("slovosledu") == "slo·vo·sle·du"
    assert hyphenate("spoluploditeľka") == "spo·lu·plo·di·teľ·ka"
    assert hyphenate("následok") == "nás·le·dok"
    assert hyphenate("posledný") == "pos·led·ný"
    assert hyphenate("splodenie") == "splo·de·nie"
    assert hyphenate("oplodnenie") == "op·lod·ne·nie"
    assert hyphenate("briadka") == "briad·ka"
    assert hyphenate("zriadenie") == "zria·de·nie"
    assert hyphenate("skrátenie") == "skrá·te·nie"
    assert hyphenate("opatrenie") == "opat·re·nie"
    assert hyphenate("patriarcha") == "pat·riar·cha"


def test_fifth_discovered_family_batch_keeps_only_clear_seams():
    assert hyphenate("všestranný") == "vše·stran·ný"
    assert hyphenate("najvšestrannejšieho") == "naj·vše·stran·nej·šie·ho"
    assert hyphenate("prítvrdo") == "prí·tvr·do"
    assert hyphenate("priestranný") == "pries·tran·ný"
    assert hyphenate("utvrdenie") == "ut·vr·de·nie"
    assert hyphenate("stvrdnutie") == "stvrd·nu·tie"
    assert hyphenate("pohľad") == "po·hľad"
    assert hyphenate("zrozumiteľný") == "zro·zu·mi·teľ·ný"


def test_sixth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "samovládca": "sa·mo·vlád·ca",
        "spoluvládkyňa": "spo·lu·vlád·ky·ňa",
        "svetovláda": "sve·to·vlá·da",
        "veľkovládu": "veľ·ko·vlá·du",
        "vševládny": "vše·vlád·ny",
        "polobrat": "po·lo·brat",
        "spolubratia": "spo·lu·bra·tia",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ovládanie") == "ov·lá·da·nie"
    assert hyphenate("zvládnuť") == "zvlád·nuť"
    assert hyphenate("schovať") == "scho·vať"
    assert hyphenate("uprosiť") == "up·ro·siť"
    assert hyphenate("neúprosný") == "ne·úp·ros·ný"
    assert hyphenate("obratný") == "ob·rat·ný"
    assert hyphenate("zbratať") == "zbra·tať"
    assert hyphenate("chradnúť") == "chrad·núť"


def test_seventh_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "polohlasne": "po·lo·hlas·ne",
        "tisíchlasným": "ti·síc·hlas·ným",
        "tisícohlasnú": "ti·sí·co·hlas·nú",
        "rozoznám": "ro·zo·znám",
        "spoznávame": "spo·zná·va·me",
        "nespoznáme": "ne·spo·zná·me",
        "staroznáme": "sta·ro·zná·me",
        "svetoznámy": "sve·to·zná·my",
        "novovzniknutého": "no·vo·vznik·nu·té·ho",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ohlas") == "oh·las"
    assert hyphenate("chlastom") == "chlas·tom"
    assert hyphenate("uniesol") == "unie·sol"
    assert hyphenate("zniesol") == "znie·sol"
    assert hyphenate("oznámenie") == "oz·ná·me·nie"
    assert hyphenate("oboznámenie") == "ob·oz·ná·me·nie"
    assert hyphenate("ochutiť") == "ochu·tiť"
    assert hyphenate("schuti") == "schu·ti"
    assert hyphenate("unikajú") == "uni·ka·jú"
    assert hyphenate("nevznikali") == "ne·vzni·ka·li"
    assert hyphenate("technika") == "tech·ni·ka"


def test_eighth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "životaschopnosť": "ži·vo·ta·schop·nosť",
        "práceschopným": "prá·ce·schop·ným",
        "vydajaschopného": "vy·da·ja·schop·né·ho",
        "činuschopnou": "či·nu·schop·nou",
        "hvezdopravec": "hvez·do·pra·vec",
        "polopravdivé": "po·lo·prav·di·vé",
        "príprava": "prí·pra·va",
        "nápravný": "ná·prav·ný",
        "svätopravdivého": "svä·to·prav·di·vé·ho",
        "samospravodlivých": "sa·mo·spra·vod·li·vých",
        "všespravodlivý": "vše·spra·vod·li·vý",
        "spoluspravovať": "spo·lu·spra·vo·vať",
        "rozostúpiť": "ro·zo·stú·piť",
        "nanebovstúpenie": "na·ne·bo·vstú·pe·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("uschopnil") == "us·chop·nil"
    assert hyphenate("spraviť") == "spra·viť"
    assert hyphenate("upraviť") == "up·ra·viť"
    assert hyphenate("kamienka") == "ka·mien·ka"
    assert hyphenate("spomienka") == "spo·mien·ka"
    assert hyphenate("ustúpi") == "us·tú·pi"
    assert hyphenate("poodstúpiť") == "po·od·stú·piť"
    assert hyphenate("nárast") == "ná·rast"
    assert hyphenate("prírastok") == "prí·ras·tok"
    assert hyphenate("urastený") == "uras·te·ný"
    assert hyphenate("vzrastie") == "vzras·tie"


def test_ninth_discovered_family_batch_has_no_safe_new_output_points():
    expected = {
        "desaťnásobný": "de·sať·ná·sob·ný",
        "dvojnásobný": "dvoj·ná·sob·ný",
        "svetonázor": "sve·to·ná·zor",
        "zaobstarať": "za·ob·sta·rať",
        "prelahodný": "pre·la·hod·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("znásobiť") == "zná·so·biť"
    assert hyphenate("predvorie") == "pred·vo·rie"
    assert hyphenate("zdvorilý") == "zdvo·ri·lý"
    assert hyphenate("znázorniť") == "zná·zor·niť"
    assert hyphenate("bastard") == "bas·tard"
    assert hyphenate("ustarostený") == "us·ta·ros·te·ný"
    assert hyphenate("blahodarný") == "bla·ho·dar·ný"
    assert hyphenate("ulahodiť") == "ula·ho·diť"


def test_tenth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "onosvetský": "ono·svet·ský",
        "polosvetlo": "po·lo·svet·lo",
        "samosvetlo": "sa·mo·svet·lo",
        "starosvetský": "sta·ro·svet·ský",
        "všesvety": "vše·sve·ty",
        "praarchanjel": "pra·arch·an·jel",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("pasvetla") == "pas·vet·la"
    assert hyphenate("samovysvetľujúce") == "sa·mo·vys·vet·ľu·jú·ce"
    assert hyphenate("zásvetie") == "zás·ve·tie"
    assert hyphenate("ostáva") == "os·tá·va"
    assert hyphenate("zhrozenie") == "zhro·ze·nie"
    assert hyphenate("evanjelium") == "evan·je·li·um"
    assert hyphenate("transport") == "trans·port"
    assert hyphenate("bezosporu") == "bez·os·po·ru"


def test_eleventh_discovered_family_batch_has_no_safe_new_output_points():
    expected = {
        "najosudnejšie": "naj·osud·nej·šie",
        "poškodenie": "po·ško·de·nie",
        "najskalnatejšia": "naj·skal·na·tej·šia",
        "zachovanie": "za·cho·va·nie",
        "zapamätať": "za·pa·mä·tať",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("posudok") == "po·su·dok"
    assert hyphenate("vrchnosudcovský") == "vrch·no·sud·cov·ský"
    assert hyphenate("uškodiť") == "uš·ko·diť"
    assert hyphenate("získal") == "zís·kal"
    assert hyphenate("úskalie") == "ús·ka·lie"
    assert hyphenate("schovať") == "scho·vať"
    assert hyphenate("uchovať") == "ucho·vať"
    assert hyphenate("spamätať") == "spa·mä·tať"


def test_twelfth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "nerestný": "ne·rest·ný",
        "hrozostrašnú": "hro·zo·straš·nú",
        "neosobný": "ne·o·sob·ný",
        "tristojednotke": "tri·sto·jed·not·ke",
        "všejednotou": "vše·jed·no·tou",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("prestrel") == "pre·strel"
    assert hyphenate("zvrchovaný") == "zvr·cho·va·ný"
    assert hyphenate("ustrašene") == "us·tra·še·ne"
    assert hyphenate("zosobnenie") == "zo·sob·ne·nie"
    assert hyphenate("zjednotenie") == "zjed·no·te·nie"


def test_thirteenth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "okolostojaci": "oko·lo·sto·ja·ci",
        "okolostojaceho": "oko·lo·sto·ja·ce·ho",
        "duchoveda": "du·cho·ve·da",
        "márnotratný": "már·no·trat·ný",
        "najšetrnejší": "naj·še·tr·nej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("okraj") == "ok·raj"
    assert hyphenate("dozvedať") == "do·zve·dať"
    assert hyphenate("strata") == "stra·ta"
    assert hyphenate("dôstojný") == "dôs·toj·ný"
    assert hyphenate("neprístojnosť") == "ne·prís·toj·nosť"
    assert hyphenate("nástojčivý") == "nás·toj·či·vý"
    assert hyphenate("ustojíme") == "us·to·jí·me"
    assert hyphenate("ošetriť") == "ošet·riť"


def test_fourteenth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "nevhodný": "ne·vhod·ný",
        "najnevhodnejší": "naj·ne·vhod·nej·ší",
        "vševíťaznou": "vše·ví·ťaz·nou",
        "sedemmiestny": "se·dem·mies·tny",
        "veľkomiest": "veľ·ko·miest",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("jahodovočervené") == "ja·ho·do·vo·čer·ve·né"
    assert hyphenate("zhodovať") == "zho·do·vať"
    assert hyphenate("zvíťaziť") == "zví·ťa·ziť"
    assert hyphenate("umiestniť") == "umies·tniť"
    assert hyphenate("pohyb") == "po·hyb"


def test_fifteenth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "nevďačný": "ne·vďač·ný",
        "najnevďačnejší": "naj·ne·vďač·nej·ší",
        "povďační": "po·vďač·ní",
        "prevďačná": "pre·vďač·ná",
        "zavďačiť": "za·vďa·čiť",
        "vďakyvzdania": "vďa·ky·vzda·nia",
        "nezhoda": "ne·zho·da",
        "nezhodil": "ne·zho·dil",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nezdanená") == "ne·zda·ne·ná"
    assert hyphenate("hvízdanie") == "hvíz·da·nie"
    assert hyphenate("odovzdanie") == "odo·vzda·nie"
    assert hyphenate("ožiarený") == "ožia·re·ný"
    assert hyphenate("mažiare") == "ma·žia·re"
    assert hyphenate("rozhodnutie") == "roz·hod·nu·tie"
    assert hyphenate("údaje") == "úda·je"
    assert hyphenate("pribúdajú") == "pri·bú·da·jú"


def test_sixteenth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "prvotlači": "pr·vo·tla·či",
        "prítlačnej": "prí·tlač·nej",
        "velezradca": "ve·le·zrad·ca",
        "vlastizrada": "vlas·ti·zra·da",
        "kníhtlače": "kníh·tla·če",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("hviezda") == "hviez·da"
    assert hyphenate("zviezť") == "zviezť"
    assert hyphenate("plávať") == "plá·vať"
    assert hyphenate("sláva") == "slá·va"
    assert hyphenate("stlačenie") == "stla·če·nie"
    assert hyphenate("otlačky") == "ot·lač·ky"
    assert hyphenate("otriasa") == "ot·ria·sa"
    assert hyphenate("striasa") == "stria·sa"
    assert hyphenate("bezradný") == "bez·rad·ný"
    assert hyphenate("rozradostený") == "roz·ra·dos·te·ný"


def test_seventeenth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "plnozvučného": "pl·no·zvuč·né·ho",
        "rovnozvučne": "rov·no·zvuč·ne",
        "rozozvučať": "ro·zo·zvu·čať",
        "spoluzvučnú": "spo·lu·zvuč·nú",
        "veľkozvučné": "veľ·ko·zvuč·né",
        "rozostretých": "ro·zo·stre·tých",
        "znovustretnutie": "zno·vu·stret·nu·tie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("bezvodé") == "bez·vo·dé"
    assert hyphenate("rozvod") == "roz·vod"
    assert hyphenate("ozvučná") == "oz·vuč·ná"
    assert hyphenate("ohovoriť") == "oho·vo·riť"
    assert hyphenate("zhovorčivý") == "zho·vor·či·vý"
    assert hyphenate("skamenieť") == "ska·me·nieť"
    assert hyphenate("ústretový") == "ús·tre·to·vý"


def test_eighteenth_discovered_family_batch_has_no_safe_new_output_points():
    expected = {
        "vdýchnuť": "vdých·nuť",
        "ustarostený": "us·ta·ros·te·ný",
        "stráviť": "strá·viť",
        "otráviť": "ot·rá·viť",
        "zvetrávať": "zvet·rá·vať",
        "osemhranný": "osem·hran·ný",
        "štvorhranný": "štvor·hran·ný",
        "uhrančivý": "uh·ran·či·vý",
        "ochrana": "och·ra·na",
        "záchrana": "zách·ra·na",
        "chryzolit": "chry·zo·lit",
        "ohryzok": "oh·ry·zok",
        "uhryznúť": "uh·ryz·núť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_nineteenth_discovered_family_batch_has_no_safe_new_output_points():
    expected = {
        "odkýchať": "od·ký·chať",
        "slovenských": "slo·ven·ských",
        "medzitriedy": "me·dzi·trie·dy",
        "zriedkavý": "zried·ka·vý",
        "vyvarovať": "vy·va·ro·vať",
        "pretvarovať": "pre·tva·ro·vať",
        "pridružiť": "pri·dru·žiť",
        "združenie": "zdru·že·nie",
        "obohatiť": "ob·oha·tiť",
        "zbohatnúť": "zbo·hat·núť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twentieth_discovered_family_batch_has_no_safe_new_output_points():
    expected = {
        "kníhviazač": "kníh·via·zač",
        "uviazať": "uvia·zať",
        "zviazať": "zvia·zať",
        "bohapusto": "bo·ha·pus·to",
        "kapusta": "ka·pus·ta",
        "spustenie": "spus·te·nie",
        "upustiť": "upus·tiť",
        "vpustiť": "vpus·tiť",
        "priepustka": "prie·pust·ka",
        "malomestský": "ma·lo·mest·ský",
        "veľkomesta": "veľ·ko·mes·ta",
        "námestie": "ná·mes·tie",
        "zmestiť": "zmes·tiť",
        "vmestiť": "vmes·tiť",
        "skleslý": "skles·lý",
        "pokles": "po·kles",
        "ovisnúť": "ovis·núť",
        "parkovisko": "par·ko·vis·ko",
        "stanovisko": "sta·no·vis·ko",
        "jehovista": "je·ho·vis·ta",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_first_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "poslúžiť": "po·slú·žiť",
        "neposlúži": "ne·po·slú·ži",
        "spoluslúžia": "spo·lu·slú·žia",
        "veľkoslúžiaci": "veľ·ko·slú·žia·ci",
        "záhrobie": "zá·hro·bie",
        "záhrobný": "zá·hrob·ný",
        "posol": "po·sol",
        "poslať": "pos·lať",
        "poslúchať": "pos·lú·chať",
        "chrobák": "chro·bák",
        "záhrada": "zá·hra·da",
        "strasie": "stra·sie",
        "utrasie": "ut·ra·sie",
        "sústrasti": "sú·stras·ti",
        "rozložiť": "roz·lo·žiť",
        "bezradný": "bez·rad·ný",
        "rozradostený": "roz·ra·dos·te·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_second_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "priesvitný": "prie·svit·ný",
        "nepriesvitné": "ne·prie·svit·né",
        "polopriesvitný": "po·lo·prie·svit·ný",
        "priestrel": "prie·strel",
        "nepriestrelný": "ne·prie·strel·ný",
        "rozostrel": "ro·zo·strel",
        "priesmyk": "pries·myk",
        "priestor": "pries·tor",
        "prieskum": "pries·kum",
        "úsvit": "ús·vit",
        "prísvit": "prís·vit",
        "vstrel": "vstrel",
        "zbystreli": "zbys·tre·li",
        "spríjemniť": "sprí·jem·niť",
        "blesk": "blesk",
        "doručiteľ": "do·ru·či·teľ",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_third_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "kladkostroj": "klad·ko·stroj",
        "kladkostrojmi": "klad·ko·stroj·mi",
        "ohňostroj": "oh·ňo·stroj",
        "ohňostrojové": "oh·ňo·stro·jo·vé",
        "nástroj": "nás·troj",
        "prístroj": "prís·troj",
        "sestroja": "ses·tro·ja",
        "ústrojenstvo": "ús·tro·jen·stvo",
        "splynie": "sply·nie",
        "neuplynul": "ne·up·ly·nul",
        "ochudobniť": "ochu·dob·niť",
        "schudla": "schud·la",
        "dvadsaťdvojok": "dvad·sať·dvo·jok",
        "tridsaťdvojka": "trid·sať·dvoj·ka",
        "podvojná": "pod·voj·ná",
        "predvoj": "pred·voj",
        "zdvojnásobiť": "zdvoj·ná·so·biť",
        "naskladať": "na·skla·dať",
        "poskladať": "po·skla·dať",
        "ukladať": "uk·la·dať",
        "vkladať": "vkla·dať",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_fourth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "samovrave": "sa·mo·vra·ve",
        "samovravu": "sa·mo·vra·vu",
        "veľavravne": "ve·ľa·vrav·ne",
        "veľavravnými": "ve·ľa·vrav·ný·mi",
        "stočlenná": "sto·člen·ná",
        "stočlennou": "sto·člen·nou",
        "ostrihané": "os·tri·ha·né",
        "neostrihané": "ne·os·tri·ha·né",
        "uvravené": "uv·ra·ve·né",
        "dohromady": "do·hro·ma·dy",
        "pohroma": "po·hro·ma",
        "včlenenie": "včle·ne·nie",
        "nevčlenili": "nev·čle·ni·li",
        "komunikácia": "ko·mu·ni·ká·cia",
        "exkomunikácia": "ex·ko·mu·ni·ká·cia",
        "tunika": "tu·ni·ka",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_fifth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "samohláskami": "sa·mo·hlás·ka·mi",
        "samohlások": "sa·mo·hlá·sok",
        "spoluhláskami": "spo·lu·hlás·ka·mi",
        "spoluhlások": "spo·lu·hlá·sok",
        "chliev": "chliev",
        "vlieva": "vlie·va",
        "zlieva": "zlie·va",
        "omdlievať": "om·dlie·vať",
        "ohlásenie": "oh·lá·se·nie",
        "neohlásil": "ne·oh·lá·sil",
        "právnik": "práv·nik",
        "trávnik": "tráv·nik",
        "kávnik": "káv·nik",
        "uchopiť": "ucho·piť",
        "schopný": "schop·ný",
        "psychopat": "psy·cho·pat",
        "uschopnil": "us·chop·nil",
        "ustáliť": "us·tá·liť",
        "neustále": "ne·us·tá·le",
        "piedestál": "pie·des·tál",
        "vestálka": "ves·tál·ka",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_sixth_discovered_family_batch_keeps_only_clear_seams():
    expected = {
        "polozrelý": "po·lo·zre·lý",
        "spolupracovať": "spo·lu·pra·co·vať",
        "nespolupracuje": "ne·spo·lu·pra·cu·je",
        "prívlastok": "prí·vlas·tok",
        "spoluvlastníctve": "spo·lu·vlast·ní·ctve",
        "plnohodnotný": "pl·no·hod·not·ný",
        "zhodnotenie": "zhod·no·te·nie",
        "maškrtami": "maš·kr·ta·mi",
        "uškrtil": "uš·kr·til",
        "spracovať": "spra·co·vať",
        "opracovať": "op·ra·co·vať",
        "uzrel": "uz·rel",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_seventh_discovered_family_batch_has_no_safe_new_seams():
    expected = {
        "spolucestujúcimi": "spo·lu·ces·tu·jú·ci·mi",
        "prícestným": "prí·cest·ným",
        "polceste": "pol·ces·te",
        "scestie": "sces·tie",
        "incestu": "in·ces·tu",
        "lesklo": "les·klo",
        "prásklo": "prás·klo",
        "zhnusenie": "zhnu·se·nie",
        "uvelebiť": "uve·le·biť",
        "zvelebovať": "zve·le·bo·vať",
        "ovládať": "ov·lá·dať",
        "zvládať": "zvlá·dať",
        "sebaovládanie": "se·ba·ov·lá·da·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_eighth_discovered_family_batch_keeps_only_clear_svat_seams():
    expected = {
        "novovysvätený": "no·vo·vy·svä·te·ný",
        "spoluposvätená": "spo·lu·po·svä·te·ná",
        "svätosväte": "svä·to·svä·te",
        "všesvätá": "vše·svä·tá",
        "nezbledne": "ne·zbled·ne",
        "zbledol": "zble·dol",
        "uzmieriť": "uz·mie·riť",
        "modrobielu": "mod·ro·bie·lu",
        "neodrobil": "ne·od·ro·bil",
        "odrobinku": "od·ro·bin·ku",
        "fízlom": "fíz·lom",
        "kúzlom": "kúz·lom",
        "rozlomil": "roz·lo·mil",
        "uzlom": "uz·lom",
        "žezlom": "žez·lom",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_twenty_ninth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "poloslepý": "po·lo·sle·pý",
        "svetoslepý": "sve·to·sle·pý",
        "päťuholník": "päť·uhol·ník",
        "sedemuholníkový": "se·dem·uhol·ní·ko·vý",
        "tridsaťdvauholníková": "trid·sať·dva·uhol·ní·ko·vá",
        "štvoruholník": "štvor·uhol·ník",
        "podotknúť": "po·dotk·núť",
        "stuhol": "stu·hol",
        "nestuhol": "ne·stu·hol",
        "rozmer": "roz·mer",
        "nadrozmerné": "nad·roz·mer·né",
        "encyklopédia": "en·cyk·lo·pé·dia",
        "kyklopi": "kyk·lo·pi",
        "neobklopuje": "ne·ob·klo·pu·je",
        "sklopiť": "sklo·piť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirtieth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "znovunavrátený": "zno·vu·na·vrá·te·ný",
        "spolublížni": "spo·lu·blíž·ni",
        "spolusprávca": "spo·lu·správ·ca",
        "životospráva": "ži·vo·to·sprá·va",
        "zvrátiť": "zvrá·tiť",
        "neodvrátený": "ne·od·vrá·te·ný",
        "ovplyvniť": "ov·plyv·niť",
        "neovplyvnený": "ne·ov·plyv·ne·ný",
        "ublížiť": "ub·lí·žiť",
        "zblížiť": "zblí·žiť",
        "dvojposchodový": "dvoj·pos·cho·do·vý",
        "desaťposchodovú": "de·sať·pos·cho·do·vú",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_first_discovered_family_batch_keeps_only_clear_slav_seams():
    expected = {
        "spolusláviť": "spo·lu·slá·viť",
        "staroslávny": "sta·ro·sláv·ny",
        "víťazoslávny": "ví·ťa·zo·sláv·ny",
        "skriviť": "skri·viť",
        "ukrivdil": "uk·riv·dil",
        "neukrivdil": "ne·uk·riv·dil",
        "šumel": "šu·mel",
        "ošumelý": "ošu·me·lý",
        "rumelku": "ru·mel·ku",
        "bdelo": "bde·lo",
        "podelo": "pod·elo",
        "údelom": "úde·lom",
        "usvedčiť": "us·ved·čiť",
        "neusvedčili": "ne·us·ved·či·li",
        "staroosvedčenými": "sta·ro·os·ved·če·ný·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_second_discovered_family_batch_keeps_only_clear_ktor_seams():
    expected = {
        "hociktorý": "ho·ci·kto·rý",
        "kdektorému": "kde·kto·ré·mu",
        "niektorými": "nie·kto·rý·mi",
        "faktor": "fak·tor",
        "detektormi": "de·tek·tor·mi",
        "šéfredaktor": "šéf·re·dak·tor",
        "uspôsobené": "us·pô·so·be·né",
        "neuspôsobil": "ne·us·pô·so·bil",
        "uzdravený": "uz·dra·ve·ný",
        "ozdravenie": "oz·dra·ve·nie",
        "zmorený": "zmo·re·ný",
        "ošľahaný": "oš·ľa·ha·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_third_discovered_family_batch_keeps_only_clear_krestan_seams():
    expected = {
        "pohanokresťanmi": "po·ha·no·kres·ťan·mi",
        "spolukresťanov": "spo·lu·kres·ťa·nov",
        "židokresťanskými": "ži·do·kres·ťan·ský·mi",
        "protiliek": "pro·ti·liek",
        "mliekar": "mlie·kar",
        "navliekať": "na·vlie·kať",
        "utrápený": "ut·rá·pe·ný",
        "strápnili": "stráp·ni·li",
        "okríkol": "ok·rí·kol",
        "skríkne": "skrík·ne",
        "cukríky": "cuk·rí·ky",
        "bezmenný": "bez·men·ný",
        "rozmeniť": "roz·me·niť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_fourth_discovered_family_batch_keeps_only_clear_graf_and_slub_seams():
    expected = {
        "orografia": "oro·gra·fia",
        "stenograf": "ste·no·graf",
        "telegrafický": "te·le·gra·fic·ký",
        "topograficky": "to·po·gra·fic·ky",
        "typografický": "ty·po·gra·fic·ký",
        "prísľubmi": "prí·sľub·mi",
        "veľasľubné": "ve·ľa·sľub·né",
        "neopatrnosť": "ne·o·pa·tr·nosť",
        "veľkopatriarcha": "veľ·ko·pat·riar·cha",
        "nedopatrenie": "ne·do·pat·re·nie",
        "ozbrojený": "oz·bro·je·ný",
        "neozbrojený": "ne·oz·bro·je·ný",
        "rozbroj": "roz·broj",
        "zaútočil": "za·ú·to·čil",
        "smútočný": "smú·toč·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_fifth_discovered_family_batch_keeps_only_clear_stan_and_spev_seams():
    expected = {
        "novostanovenom": "no·vo·sta·no·ve·nom",
        "príspevok": "prí·spe·vok",
        "príspevky": "prí·spev·ky",
        "žalospev": "ža·lo·spev",
        "žalospevoch": "ža·lo·spe·voch",
        "zhustený": "zhus·te·ný",
        "nezhustla": "nez·hust·la",
        "substancia": "sub·stan·cia",
        "protestant": "pro·tes·tant",
        "novoustanovený": "no·vo·us·ta·no·ve·ný",
        "novopovstanie": "no·vo·pov·sta·nie",
        "dohorel": "do·ho·rel",
        "bohorúhač": "bo·ho·rú·hač",
        "stredohoria": "stre·do·ho·ria",
        "praskajúce": "pra·ska·jú·ce",
        "spolukajúcnikov": "spo·lu·ka·júc·ni·kov",
        "chválospev": "chvá·lo·spev",
        "ospevoval": "ospe·vo·val",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_sixth_discovered_family_batch_keeps_only_the_clear_blesk_seam():
    expected = {
        "záblesk": "zá·blesk",
        "zábleskami": "zá·bles·ka·mi",
        "záblesková": "zá·bles·ko·vá",
        "neuplynul": "ne·up·ly·nul",
        "splynul": "sply·nul",
        "vplynulo": "vply·nu·lo",
        "vliezol": "vlie·zol",
        "zliezť": "zliezť",
        "želiezka": "že·liez·ka",
        "zhoršenie": "zhor·še·nie",
        "nezhoršil": "nez·hor·šil",
        "choršie": "chor·šie",
        "ubúdanie": "ubú·da·nie",
        "neubúda": "ne·ubú·da",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_seventh_discovered_family_batch_keeps_only_nested_ob_oznam_seams():
    expected = {
        "neoboznámené": "ne·ob·oz·ná·me·né",
        "neoboznámil": "ne·ob·oz·ná·mil",
        "ozval": "oz·val",
        "neozvala": "ne·oz·va·la",
        "rozvaliť": "roz·va·liť",
        "uviaže": "uvia·že",
        "zviažeme": "zvia·že·me",
        "poukazovať": "po·uka·zo·vať",
        "príkazov": "prí·ka·zov",
        "zviera": "zvie·ra",
        "uzavierajú": "uza·vie·ra·jú",
        "poznámka": "po·znám·ka",
        "svetoznámy": "sve·to·zná·my",
        "neoznámi": "ne·oz·ná·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_eighth_discovered_family_batch_has_no_safe_new_seams():
    expected = {
        "sklenej": "skle·nej",
        "presklené": "pre·skle·né",
        "zasklený": "za·skle·ný",
        "pošteklenie": "po·štek·le·nie",
        "pasvetla": "pas·vet·la",
        "samovysvetľujúce": "sa·mo·vys·vet·ľu·jú·ce",
        "zásvetie": "zás·ve·tie",
        "bostonské": "bos·ton·ské",
        "albastone": "al·bas·to·ne",
        "šestonedelí": "šes·to·ne·de·lí",
        "umierať": "umie·rať",
        "neumiera": "ne·umie·ra",
        "odumierať": "od·umie·rať",
        "zmierať": "zmie·rať",
        "všehomiera": "vše·ho·mie·ra",
        "striekačka": "strie·kač·ka",
        "postriekali": "po·strie·ka·li",
        "škriekanie": "škrie·ka·nie",
        "zriekať": "zrie·kať",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_thirty_ninth_discovered_family_batch_keeps_only_po_diel_and_za_prah_seams():
    expected = {
        "podiel": "po·diel",
        "podiele": "po·die·le",
        "podielnici": "po·diel·ni·ci",
        "podielom": "po·die·lom",
        "podielu": "po·die·lu",
        "záprah": "zá·prah",
        "záprahový": "zá·pra·ho·vý",
        "záprahu": "zá·pra·hu",
        "bezvládny": "bez·vlád·ny",
        "údiel": "údiel",
        "náprahu": "náp·ra·hu",
        "polovyprahnutom": "po·lo·vy·prah·nu·tom",
        "sprahnutej": "sprah·nu·tej",
        "vsiaknuť": "vsiak·nuť",
        "zúčtovať": "zúč·to·vať",
        "naúčtovať": "na·úč·to·vať",
        "neúčtoval": "ne·úč·to·val",
        "vyúčtovanie": "vy·úč·to·va·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fortieth_discovered_family_batch_keeps_only_pol_ostrov_seams():
    expected = {
        "polostrov": "pol·os·trov",
        "polostrova": "pol·os·tro·va",
        "polostrove": "pol·os·tro·ve",
        "polostrovu": "pol·os·tro·vu",
        "polostrovy": "pol·os·tro·vy",
        "rozväzovať": "roz·vä·zo·vať",
        "guráž": "gu·ráž",
        "kurážne": "ku·ráž·ne",
        "samovládca": "sa·mo·vlád·ca",
        "neovláda": "ne·ov·lá·da",
        "umiestniť": "umies·tniť",
        "vmiesť": "vmiesť",
        "zmiesť": "zmiesť",
        "kostrové": "kos·tro·vé",
        "súostrovie": "sú·os·tro·vie",
        "zaostrovali": "za·os·tro·va·li",
        "zostrovať": "zo·stro·vať",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_pri_prefix_is_recognised_in_the_slov_and_slus_families():
    assert hyphenate("príslovie") == "prí·slo·vie"
    assert hyphenate("príslovka") == "prí·slov·ka"
    assert hyphenate("príslušný") == "prí·sluš·ný"


def test_po_prefix_is_recognised_in_the_slus_family():
    assert hyphenate("poslušný") == "po·sluš·ný"
    assert hyphenate("neposlušnosť") == "ne·po·sluš·nosť"
    assert hyphenate("najposlušnejší") == "naj·po·sluš·nej·ší"


def test_podob_and_podiv_do_not_gain_a_false_pod_prefix():
    assert hyphenate("podoba") == "po·do·ba"
    assert hyphenate("napodobenie") == "na·po·do·be·nie"
    assert hyphenate("podivný") == "po·div·ný"


def test_dobr_family_does_not_gain_a_false_do_prefix():
    assert hyphenate("dobro") == "dob·ro"
    assert hyphenate("dobrom") == "dob·rom"
    assert hyphenate("dobrý") == "dob·rý"
    assert hyphenate("dobrota") == "dob·ro·ta"
    assert hyphenate("dobrák") == "dob·rák"
    assert hyphenate("dobrácka") == "dob·rác·ka"
    assert get_syllables("dobrom") == ["do", "brom"]
    assert hyphenate("dobrať") == "do·brať"
    assert hyphenate("dobrúsiť") == "do·brú·siť"


def test_dobro_compounds_keep_their_compositional_seam():
    assert hyphenate("dobroprajnosť") == "dob·ro·praj·nosť"
    assert hyphenate("dobrodruh") == "dob·ro·druh"
    assert get_syllables("dobroprajnosť") == ["do", "bro", "praj", "nosť"]


def test_dom_stems_are_not_mistaken_for_the_do_prefix():
    assert hyphenate("domkárov") == "dom·ká·rov"
    assert hyphenate("domnelý") == "dom·ne·lý"
    assert hyphenate("domnienka") == "dom·nien·ka"
    assert hyphenate("domnievať") == "dom·nie·vať"
    assert hyphenate("domlátenú") == "do·mlá·te·nú"


def test_batch_14_morpheme_seams_outweigh_cluster_fallbacks():
    expected = {
        "dorástli": "do·rást·li",
        "dorástlo": "do·rást·lo",
        "doštička": "doš·tič·ka",
        "dotknúť": "do·tknúť",
        "doviedlo": "do·vied·lo",
        "dovtedy": "do·vte·dy",
        "dôvtip": "dô·vtip",
        "dozdobená": "do·zdo·be·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("doškriabané") == "do·škria·ba·né"


def test_st_final_past_participles_keep_their_grammatical_suffix():
    expected = {
        "hustla": "hust·la",
        "hustli": "hust·li",
        "hustlo": "hust·lo",
        "rástla": "rást·la",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_15_compounds_keep_their_compositional_seams():
    expected = {
        "drevoskladu": "dre·vo·skla·du",
        "drobnohľadov": "drob·no·hľa·dov",
        "dutohlavci": "du·to·hlav·ci",
        "dvetisícštyristo": "dve·ti·síc·šty·ri·sto",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_16_compounds_keep_their_compositional_seams():
    expected = {
        "dvojuchú": "dvoj·uchú",
        "etylalkoholu": "etyl·al·ko·ho·lu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("dvojica") == "dvo·ji·ca"
    assert hyphenate("dvojitý") == "dvo·ji·tý"


def test_batch_18_fajn_compounds_keep_their_compositional_seam():
    expected = {
        "fajnšmeker": "fajn·šme·ker",
        "fajnšmekerka": "fajn·šme·ker·ka",
        "fajnšmekerstvo": "fajn·šme·ker·stvo",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_19_gramo_compound_keeps_its_compositional_seam():
    assert hyphenate("gramoplatňami") == "gra·mo·plat·ňa·mi"
    assert hyphenate("gramofón") == "gra·mo·fón"


def test_batch_20_hemi_compound_keeps_its_compositional_seam():
    assert hyphenate("hemisféry") == "he·mi·sfé·ry"


def test_inter_compositum_does_not_split_lexical_interes_and_interier_stems():
    expected = {
        "interesentov": "in·te·re·sen·tov",
        "interesovať": "in·te·re·so·vať",
        "interiér": "in·te·ri·ér",
        "interiérový": "in·te·ri·é·ro·vý",
        "interakcia": "in·ter·ak·cia",
        "interurbánny": "in·ter·ur·bán·ny",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_audited_linking_vowel_compounds_keep_their_compositional_seam():
    expected = {
        "bielovlasý": "bie·lo·vla·sý",
        "bledozlaté": "ble·do·zla·té",
        "blahoprajný": "bla·ho·praj·ný",
        "bohočlovek": "bo·ho·člo·vek",
        "bohoslužba": "bo·ho·služ·ba",
        "bleskozvod": "bles·ko·zvod",
        "celoštátny": "ce·lo·štát·ny",
        "červenovlasý": "čer·ve·no·vla·sý",
        "hnedovlasá": "hne·do·vla·sá",
        "holobradý": "ho·lo·bra·dý",
        "holobriadok": "ho·lo·bria·dok",
        "holohlavý": "ho·lo·hla·vý",
        "hromozvod": "hro·mo·zvod",
        "hrôzostrašný": "hrô·zo·straš·ný",
        "hrôzovláda": "hrô·zo·vlá·da",
        "hrubohmotný": "hru·bo·hmot·ný",
        "hrubozmyslový": "hru·bo·zmys·lo·vý",
        "inohmotný": "ino·hmot·ný",
        "jasnozrivý": "jas·no·zri·vý",
        "jedinovládca": "je·di·no·vlád·ca",
        "jemnohmotný": "jem·no·hmot·ný",
        "Juhoslávie": "Ju·ho·slá·vie",
        "kosodrevina": "ko·so·dre·vi·na",
        "kosoštvorec": "ko·so·štvo·rec",
        "kozmografický": "koz·mo·gra·fic·ký",
        "krepovlasý": "kre·po·vla·sý",
        "krivoprísažný": "kri·vo·prí·saž·ný",
        "krížokvetý": "krí·žo·kve·tý",
        "krutovláda": "kru·to·vlá·da",
        "krviprelievanie": "kr·vi·pre·lie·va·nie",
        "krvosmilstvo": "kr·vo·smil·stvo",
        "kučeravohlavý": "ku·če·ra·vo·hla·vý",
        "kušostrelec": "ku·šo·stre·lec",
        "ľanovlasý": "ľa·no·vla·sý",
        "letokruhy": "le·to·kru·hy",
        "leukoplast": "leu·ko·plast",
        "ľubozvučný": "ľu·bo·zvuč·ný",
        "ľudoprázdny": "ľu·do·práz·dny",
        "lukostrelec": "lu·ko·stre·lec",
        "lykožrút": "ly·ko·žrút",
        "lyrochvostov": "ly·ro·chvos·tov",
        "málokde": "má·lo·kde",
        "máloktorým": "má·lo·kto·rým",
        "málovravný": "má·lo·vrav·ný",
        "márnotratný": "már·no·trat·ný",
        "medenoplavými": "me·de·no·pla·vý·mi",
        "medosladký": "me·do·slad·ký",
        "melodramatickému": "me·lo·dra·ma·tic·ké·mu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("celostný") == "ce·lost·ný"
    assert hyphenate("červenosť") == "čer·ve·nosť"
    assert hyphenate("hnedosť") == "hne·dosť"
    assert hyphenate("holosť") == "ho·losť"
    assert hyphenate("hrubosť") == "hru·bosť"
    assert hyphenate("celistvý") == "ce·lis·tvý"
    assert hyphenate("málosti") == "má·los·ti"
    assert hyphenate("márnosti") == "már·nos·ti"
    assert hyphenate("medenosť") == "me·de·nosť"
    assert hyphenate("medovina") == "me·do·vi·na"
    assert hyphenate("melodický") == "me·lo·dic·ký"


def test_batch_33_guarded_compounds_and_mini_lookalikes():
    assert hyphenate("miligramov") == "mi·li·gra·mov"
    assert hyphenate("mimohmotného") == "mi·mo·hmot·né·ho"
    assert hyphenate("miliarda") == "mi·li·ar·da"
    assert hyphenate("miliardtinami") == "mi·li·ard·ti·na·mi"
    assert hyphenate("miliardtinu") == "mi·li·ard·ti·nu"
    assert hyphenate("mimochodom") == "mi·mo·cho·dom"
    assert hyphenate("minieme") == "mi·nie·me"
    assert hyphenate("miniete") == "mi·nie·te"
    assert hyphenate("minister") == "mi·nis·ter"
    assert hyphenate("ministra") == "mi·nis·tra"
    assert hyphenate("miništrant") == "mi·niš·trant"
    assert hyphenate("minisukňa") == "mi·ni·suk·ňa"
    assert hyphenate("minigolf") == "mi·ni·golf"


def test_batch_34_productive_morpheme_boundaries():
    expected = {
        "miništrovať": "mi·niš·tro·vať",
        "miništrujú": "mi·niš·tru·jú",
        "mľasknutiami": "mľask·nu·tia·mi",
        "momentkovejšie": "mo·ment·ko·vej·šie",
        "mnohohlavej": "mno·ho·hla·vej",
        "mnohohrannému": "mno·ho·hran·né·mu",
        "mnohoskúsení": "mno·ho·skú·se·ní",
        "mnohosľubný": "mno·ho·sľub·ný",
        "mnohoštítovú": "mno·ho·ští·to·vú",
        "mnohostrannosť": "mno·ho·stran·nosť",
        "mnohostrom": "mno·ho·strom",
        "mnohotlam": "mno·ho·tlam",
        "mnohotvárnosť": "mno·ho·tvár·nosť",
        "mnohovládcovia": "mno·ho·vlád·co·via",
        "mnohovravnosť": "mno·ho·vrav·nosť",
        "mnohožrúta": "mno·ho·žrú·ta",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("mnohosti") == "mno·hos·ti"
    assert hyphenate("mnohostnejšie") == "mno·host·nej·šie"


def test_batch_35_compounds_and_prefix_lookalikes():
    expected = {
        "moreplavba": "mo·re·plav·ba",
        "mrchožrútom": "mr·cho·žrú·tom",
        "mrkvovlasého": "mrk·vo·vla·sé·ho",
        "nácvik": "ná·cvik",
        "nácviku": "ná·cvi·ku",
        "nadácie": "na·dá·cie",
        "nadáciou": "na·dá·ci·ou",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("morela") == "mo·re·la"
    assert hyphenate("mrchavý") == "mr·cha·vý"
    assert hyphenate("mrkvový") == "mrk·vo·vý"
    assert hyphenate("nadpriemerný") == "nad·prie·mer·ný"


def test_batch_36_na_prefix_roots_do_not_become_false_nad_prefixes():
    expected = {
        "nadaného": "na·da·né·ho",
        "nadarmo": "na·dar·mo",
        "nadávanie": "na·dá·va·nie",
        "nadeliť": "na·de·liť",
        "nadeľujem": "na·de·ľu·jem",
        "nadevšetko": "na·de·všet·ko",
        "nadiktovať": "na·dik·to·vať",
        "nadivoko": "na·di·vo·ko",
        "nadobro": "na·dob·ro",
        "nadobúdanie": "na·do·bú·da·nie",
        "nadoďakovať": "na·do·ďa·ko·vať",
        "nadojené": "na·do·je·né",
        "nadopovaný": "na·do·po·va·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nadchnúť") == "nad·chnúť"
    assert hyphenate("nadešiel") == "nad·ešiel"
    assert hyphenate("nadíde") == "nad·íde"
    assert hyphenate("nadočnicový") == "nad·oč·ni·co·vý"
    assert hyphenate("nadkrbový") == "nad·kr·bo·vý"


def test_batch_37_na_and_na_prefix_roots_keep_their_morpheme_seams():
    expected = {
        "nadoraz": "na·do·raz",
        "nadostač": "na·do·stač",
        "nadrobno": "na·drob·no",
        "nadurený": "na·du·re·ný",
        "nadutosti": "na·du·tos·ti",
        "nadúvanie": "na·dú·va·nie",
        "nádvorie": "ná·dvo·rie",
        "náhľad": "ná·hľad",
        "náhrobok": "ná·hro·bok",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nadučenec") == "nad·uče·nec"
    assert hyphenate("nadvihnúť") == "nad·vih·núť"
    assert hyphenate("nadzmyslový") == "nad·zmys·lo·vý"


def test_batch_38_na_j_roots_do_not_become_false_superlatives():
    expected = {
        "najala": "na·ja·la",
        "najali": "na·ja·li",
        "najatého": "na·ja·té·ho",
        "najatým": "na·ja·tým",
        "najavo": "na·ja·vo",
        "najazdené": "na·jaz·de·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("najarogantnejší") == "naj·aro·gant·nej·ší"
    assert hyphenate("najbezohľadnejší") == "naj·bez·oh·ľad·nej·ší"


def test_batch_39_na_j_roots_do_not_become_false_superlatives():
    expected = {
        "najedia": "na·je·dia",
        "najedla": "na·jed·la",
        "najedli": "na·jed·li",
        "najedol": "na·je·dol",
        "najedz": "na·jedz",
        "najedzme": "na·jedz·me",
        "najedzte": "na·jedz·te",
        "najeme": "na·je·me",
        "najemno": "na·jem·no",
        "najesť": "na·jesť",
        "naježená": "na·je·že·ná",
        "naježené": "na·je·že·né",
        "naježil": "na·je·žil",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("najenergickejšie") == "naj·ener·gic·kej·šie"
    assert hyphenate("najestetickejšie") == "naj·es·te·tic·kej·šie"
    assert hyphenate("najéterickejších") == "naj·éte·ric·kej·ších"
    assert hyphenate("najextrémnejšie") == "naj·ex·trém·nej·šie"


def test_batch_40_na_jim_root_does_not_become_a_false_superlative():
    expected = {
        "najíma": "na·jí·ma",
        "najímajú": "na·jí·ma·jú",
        "najímal": "na·jí·mal",
        "najímam": "na·jí·mam",
        "najímať": "na·jí·mať",
        "najímate": "na·jí·ma·te",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("najideálnejšie") == "naj·ide·ál·nej·šie"
    assert hyphenate("najinteligentnejšie") == "naj·in·te·li·gent·nej·šie"
    assert hyphenate("najistejšie") == "naj·is·tej·šie"


def test_batch_41_lz_root_keeps_the_superlative_prefix_seam():
    assert hyphenate("najlživejšie") == "naj·l·ži·vej·šie"
    assert hyphenate("najlživejšou") == "naj·l·ži·vej·šou"
    assert hyphenate("najľstivejší") == "naj·ľsti·vej·ší"


def test_batch_42_nested_one_letter_prefixes_keep_guarded_root_seams():
    expected = {
        "najneohrozenejšieho": "naj·ne·o·hro·ze·nej·šie·ho",
        "najneotrasiteľnejšej": "naj·ne·o·tra·si·teľ·nej·šej",
        "najneúplatnejšia": "naj·ne·ú·plat·nej·šia",
        "najneusporiadanejšia": "naj·ne·u·spo·ria·da·nej·šia",
        "najneústupnejšou": "naj·ne·ú·stup·nej·šou",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ohromný") == "oh·rom·ný"
    assert hyphenate("otrok") == "ot·rok"
    assert hyphenate("úplný") == "úpl·ný"
    assert hyphenate("ústredný") == "ús·tred·ný"
    assert hyphenate("uspávanka") == "us·pá·van·ka"


def test_batch_43_y_cannot_start_a_prefix_remainder():
    expected = {
        "obyčaj": "oby·čaj",
        "obydlie": "obyd·lie",
        "obytný": "obyt·ný",
        "obyvateľ": "oby·va·teľ",
        "obávaný": "obá·va·ný",
        "najobávanejší": "naj·obá·va·nej·ší",
        "najobyčajnejší": "naj·oby·čaj·nej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert get_syllables("obyčaj") == ["o", "by", "čaj"]
    assert hyphenate("najobyčajnejší", contextual=True) == "naj·o·by·čaj·nej·ší"
    assert hyphenate("obývať") == "obý·vať"


def test_batch_44_nested_o_prefix_keeps_guarded_root_seams():
    assert hyphenate("najopodstatnenejšia") == "naj·o·pod·stat·ne·nej·šia"
    assert hyphenate("najopravdivejší") == "naj·o·prav·di·vej·ší"
    assert hyphenate("ohromný") == "oh·rom·ný"
    assert hyphenate("opatrný") == "opa·tr·ný"


def test_batch_45_nested_o_prefix_and_ostro_compound_keep_guarded_seams():
    expected = {
        "najoprávnenejší": "naj·o·práv·ne·nej·ší",
        "najopustenejšie": "naj·o·pus·te·nej·šie",
        "najoslnivejšie": "naj·o·sl·ni·vej·šie",
        "najostrieľanejších": "naj·o·strie·ľa·nej·ších",
        "najostrozrakejší": "naj·os·tro·zra·kej·ší",
        "najotrhanejší": "naj·o·tr·ha·nej·ší",
        "najotupenejší": "naj·o·tu·pe·nej·ší",
        "najoživujúcejšie": "naj·o·ži·vu·jú·cej·šie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("osobný") == "osob·ný"
    assert hyphenate("otravný") == "ot·rav·ný"
    assert hyphenate("otvorený") == "ot·vo·re·ný"
    assert hyphenate("ostrosť") == "os·trosť"
    assert hyphenate("ostrovný") == "os·trov·ný"
    assert hyphenate("ozdobný") == "oz·dob·ný"


def test_prie_hlad_and_prie_hrad_families_keep_their_root_seams():
    expected = {
        "priehľad": "prie·hľad",
        "priehľadný": "prie·hľad·ný",
        "polopriehľadné": "po·lo·prie·hľad·né",
        "priehrada": "prie·hra·da",
        "priehradný": "prie·hrad·ný",
        "náhrada": "ná·hra·da",
        "náhradný": "ná·hrad·ný",
        "záhrada": "zá·hra·da",
        "záhradník": "zá·hrad·ník",
        "predzáhradka": "pred·zá·hrad·ka",
        "vinohrad": "vi·no·hrad",
        "vinohradníci": "vi·no·hrad·ní·ci",
        "Petrohrad": "Pet·ro·hrad",
        "Belehrad": "Be·le·hrad",
        "Belehradu": "Be·le·hra·du",
        "belehradský": "be·le·hrad·ský",
        "najpriehľadnejšia": "naj·prie·hľad·nej·šia",
        "najnepriehľadnejšiu": "naj·ne·prie·hľad·nej·šiu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("Leningrad") == "Le·nin·grad"
    assert hyphenate("chradnúť") == "chrad·núť"
    assert hyphenate("ohrada") == "ohra·da"
    assert hyphenate("uhradiť") == "uhra·diť"
    assert hyphenate("úhrada") == "úhra·da"


def test_batch_46_lexical_stems_and_pravdo_compound_keep_their_seams():
    expected = {
        "najpospolitejší": "naj·pos·po·li·tej·ší",
        "najpotrebnejší": "naj·pot·reb·nej·ší",
        "najpraktickejšie": "naj·prak·tic·kej·šie",
        "najpravdovravnejší": "naj·prav·do·vrav·nej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("pokročilý") == "po·kro·či·lý"
    assert hyphenate("posvätný") == "po·svät·ný"
    assert hyphenate("pradávny") == "pra·dáv·ny"


def test_audited_lexical_compounds_keep_their_morpheme_seams():
    expected = {
        "bohuprisám": "bo·hu·pri·sám",
        "bojaschopná": "bo·ja·schop·ná",
        "Božechráň": "Bo·že·chráň",
        "bratovražednej": "bra·to·vra·žed·nej",
        "bystrozraká": "bys·tro·zra·ká",
        "čarokrásna": "ča·ro·krás·na",
        "čarovná": "ča·rov·ná",
        "choreografiek": "cho·re·o·gra·fiek",
        "choroboplodný": "cho·ro·bo·plod·ný",
        "chválospevom": "chvá·lo·spe·vom",
        "čiernovlasá": "čier·no·vla·sá",
        "cudzokrajnými": "cu·dzo·kraj·ný·mi",
        "ďalekohľadov": "ďa·le·ko·hľa·dov",
        "darmožráčsky": "dar·mo·žráč·sky",
        "delostrelectvo": "de·lo·stre·le·ctvo",
        "divotvorca": "di·vo·tvor·ca",
        "dlhochvostý": "dl·ho·chvos·tý",
        "dlhotrvajúci": "dl·ho·tr·va·jú·ci",
        "dlhovlasý": "dl·ho·vla·sý",
        "kvartsextakord": "kvart·sex·ta·kord",
        "kvarteto": "kvar·te·to",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_audited_de_prefix_families_keep_their_morpheme_seam():
    expected = {
        "deflogistón": "de·flo·gis·tón",
        "deflorácii": "de·flo·rá·cii",
        "degradovaný": "de·gra·do·va·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_rhythmically_shortened_nik_suffix_keeps_its_seam():
    expected = {
        "básnik": "bás·nik",
        "dáždnik": "dážd·nik",
        "pútnik": "pút·nik",
        "strážnik": "stráž·nik",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_rhythmically_shortened_ny_suffix_keeps_its_seam():
    expected = {
        "hviezdny": "hviezd·ny",
        "hviezdna": "hviezd·na",
        "hviezdneho": "hviezd·ne·ho",
        "hviezdnemu": "hviezd·ne·mu",
        "hviezdnych": "hviezd·nych",
        "hviezdnym": "hviezd·nym",
        "hviezdnymi": "hviezd·ny·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_tvrdo_compounds_keep_their_compositional_seam():
    assert hyphenate("tvrdohlavý") == "tvr·do·hla·vý"
    assert hyphenate("najtvrdohlavejší") == "naj·tvr·do·hla·vej·ší"
    assert get_syllables("tvrdohlavý") == ["tvr", "do", "hla", "vý"]
    assert hyphenate("tvrdosti") == "tvr·dos·ti"
    assert hyphenate("tvrdostiach") == "tvr·dos·tiach"


def test_nut_suffix_preserves_the_consonant_final_stem():
    assert hyphenate("pumpnúť") == "pump·núť"
    assert hyphenate("dotknúť") == "do·tknúť"
    assert hyphenate("risknúť") == "risk·núť"


def test_liv_suffix_preserves_the_consonant_final_stem():
    assert hyphenate("hanblivý") == "hanb·li·vý"
    assert hyphenate("kostlivec") == "kost·li·vec"
    assert hyphenate("kostlivca") == "kost·liv·ca"
    assert hyphenate("kostlivce") == "kost·liv·ce"
    assert hyphenate("kostlivcom") == "kost·liv·com"
    assert hyphenate("trpezlivý") == "tr·pez·li·vý"
    assert hyphenate("palivo") == "pa·li·vo"
    assert hyphenate("jednotlivý") == "jed·no·tli·vý"
    assert hyphenate("ošklivý") == "oš·kli·vý"


def test_nik_suffix_precedes_prefix_lookalikes():
    expected = {
        "pomník": "pom·ník",
        "podvodník": "pod·vod·ník",
        "protivník": "pro·tiv·ník",
        "povozník": "po·voz·ník",
        "predchodník": "pred·chod·ník",
        "podnik": "pod·nik",
        "podnikať": "pod·ni·kať",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert get_syllables("podvodník") == ["pod", "vod", "ník"]


def test_one_letter_o_prefix_is_recognised_only_in_known_families():
    assert hyphenate("oslobodiť") == "oslo·bo·diť"
    assert hyphenate("oslabiť") == "osla·biť"
    assert hyphenate("ospravedlniť") == "ospra·ve·dl·niť"
    assert hyphenate("osvietiť") == "osvie·tiť"
    assert hyphenate("osvojiť") == "osvo·jiť"
    assert hyphenate("ostro") == "os·tro"
    assert hyphenate("ospalý") == "os·pa·lý"
    assert hyphenate("osemdesiat") == "osem·de·siat"


def test_audited_prefix_families_keep_their_psp_seams():
    expected = {
        "nadobudnúť": "na·do·bud·núť",
        "podozrenie": "po·do·zre·nie",
        "pozdraviť": "po·zdra·viť",
        "rozostaviť": "ro·zo·sta·viť",
        "rozoznať": "ro·zo·znať",
        "podzemie": "pod·ze·mie",
        "rozísť": "roz·ísť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_syllabification_and_typographic_hyphenation_are_separate_layers():
    assert get_syllables("Evanjeliá") == ["e", "van", "je", "li", "á"]
    assert hyphenate("Evanjeliá") == "Evan·je·liá"
    assert get_syllables("Opatrnosť") == ["o", "pa", "tr", "nosť"]
    assert get_syllables("dychtivosťou") == ["dych", "ti", "vos", "ťou"]
    assert hyphenate("dychtivosťou") == "dych·ti·vos·ťou"
    assert get_syllables("ženou") == ["že", "nou"]
    assert get_syllables("použiť") == ["po", "u", "žiť"]
    assert get_syllables("pakľúč") == ["pa", "kľúč"]
    assert get_syllables("ohrada") == ["o", "hra", "da"]
    assert get_syllables("ohradený") == ["o", "hra", "de", "ný"]
    assert get_syllables("ohradzovať") == ["o", "hra", "dzo", "vať"]
    assert get_syllables("ohradným") == ["o", "hrad", "ným"]
    assert get_syllables("ohraničený") == ["o", "hra", "ni", "če", "ný"]
    assert get_syllables("neohraničený") == ["ne", "o", "hra", "ni", "če", "ný"]
    assert get_syllables("ohrádka") == ["o", "hrád", "ka"]
    assert get_syllables("ohrádzať") == ["o", "hrá", "dzať"]
    assert get_syllables("obohraných") == ["ob", "o", "hra", "ných"]
    assert get_syllables("obohratá") == ["ob", "o", "hra", "tá"]
    assert get_syllables("rozohrať") == ["roz", "o", "hrať"]
    assert get_syllables("neohrabaný") == ["ne", "o", "hra", "ba", "ný"]
    assert get_syllables("porkpie") == ["pork", "pie"]
    assert get_syllables("pornograf") == ["por", "no", "graf"]
    assert get_syllables("pornografickej") == ["por", "no", "gra", "fic", "kej"]
    assert get_syllables("porisko") == ["po", "ris", "ko"]
    assert get_syllables("porota") == ["po", "ro", "ta"]
    assert get_syllables("ihrisko") == ["i", "hris", "ko"]
    assert get_syllables("robota") == ["ro", "bo", "ta"]
    assert get_syllables("choroba") == ["cho", "ro", "ba"]
    assert get_syllables("Slovensko") == ["slo", "ven", "sko"]
    assert get_syllables("odpornosťou") == ["od", "por", "nos", "ťou"]
    assert get_syllables("akciami") == ["ak", "ci", "a", "mi"]
    assert get_syllables("aeronauti") == ["a", "e", "ro", "nau", "ti"]

    # The same spelling can have a sonority boundary and a different PSP break.
    assert get_syllables("maslo") == ["ma", "slo"]
    assert hyphenate("maslo") == "mas·lo"
    assert get_syllables("okno") == ["o", "kno"]
    assert hyphenate("okno") == "ok·no"
    assert get_syllables("mydlo") == ["my", "dlo"]
    assert hyphenate("mydlo") == "myd·lo"
    assert get_syllables("jedla") == ["je", "dla"]
    assert hyphenate("jedla") == "jed·la"
    assert get_syllables("modla") == ["mo", "dla"]
    assert hyphenate("modla") == "mod·la"
    assert get_syllables("advokát") == ["a", "dvo", "kát"]
    assert hyphenate("advokát") == "ad·vo·kát"


def test_a_cluster_that_rises_towards_the_nucleus_opens_the_next_syllable():
    """The onset takes everything that still rises and can open a word.

    ``maslo`` and ``sestra`` are the two halves of the same rule: sl rises from
    obstruent to liquid and opens ``slovo``, so it is an onset; st does not
    rise, so the s is left behind to close the syllable before it.
    """
    expected = {
        "žena": "že·na",
        "maslo": "ma·slo",
        "láska": "lás·ka",
        "mašlička": "ma·šlič·ka",
        "sestra": "ses·tra",
        "Angličan": "an·gli·čan",
        "lingvistika": "ling·vis·ti·ka",
        "špendlík": "špen·dlík",
    }

    assert {word: "·".join(get_syllables(word)) for word in expected} == expected


def test_psp_cluster_boundaries_are_independent_of_syllabification():
    expected = {
        # 2a: one consonant — before it
        "žena": "že·na",
        # 2b: two consonants — between them
        "maslo": "mas·lo",
        "mašlička": "maš·lič·ka",
        "okno": "ok·no",
        "advokát": "ad·vo·kát",
        # 2c: three or more — after the first
        "sestra": "ses·tra",
        "lingvistika": "lin·gvis·ti·ka",
        "špendlík": "špen·dlík",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_typographic_nost_seam_preserves_syllabic_r():
    expected = {
        "absurdnosť": "ab·surd·nosť",
        "počestnosť": "po·čest·nosť",
        "počestnosťou": "po·čest·nos·ťou",
        "opatrnosť": "opa·tr·nosť",
        "opatrnosti": "opa·tr·nos·ti",
    }

    assert {word: hyphenate(word) for word in expected} == expected
    assert get_syllables("opatrnosť") == ["o", "pa", "tr", "nosť"]
    assert hyphenate("mäsovosť") == "mä·so·vosť"


def test_psp_doublets_offer_both_break_points():
    expected = {
        "lietadlo": {5, 6},
        "baníctvo": {4, 5},
        "laoský": {3, 4},
        "komerčný": {5, 6},
        "funkčný": {4, 5},
        "jednotlivý": {5, 6},
        "funkcia": {3, 4},
    }

    for word, points in expected.items():
        assert points <= set(break_points(word, all_points=True))
        assert len(points & set(break_points(word))) == 1


def test_dlo_suffix_keeps_its_preferred_seam_through_inflection():
    expected = {
        "páčidlo": "pá·či·dlo",
        "páčidla": "pá·či·dla",
        "páčidlu": "pá·či·dlu",
        "páčidle": "pá·či·dle",
        "páčidlom": "pá·či·dlom",
        "páčidlá": "pá·či·dlá",
        "páčidiel": "pá·či·diel",
        "páčidlám": "pá·či·dlám",
        "páčidlách": "pá·či·dlách",
        "páčidlami": "pá·či·dla·mi",
    }

    assert {word: hyphenate(word) for word in expected} == expected
    assert ["pá", "či", "dlá"] == get_syllables("páčidlá")
    assert {4, 5} <= set(break_points("páčidlá", all_points=True))
    assert 4 in break_points("páčidlá")
    assert 5 not in break_points("páčidlá")


def test_section_43_leaves_only_the_first_consonant_on_the_left():
    """PSP 4.3 does not move the point according to a possible onset."""
    expected = {
        "alžbetínska": "al·žbe·tín·ska",
        "ústna": "ús·tna",
        "zamestnáva": "za·mes·tná·va",
        "gangster": "gan·gster",
        "očistca": "očis·tca",
        "veštba": "veš·tba",
        "avantgardu": "avan·tgar·du",
        "sestra": "ses·tra",
        "pastva": "pas·tva",
        "zajtra": "zaj·tra",
        "lingvistika": "lin·gvis·ti·ka",
        "abstinencia": "ab·sti·nen·cia",
        "monštrancie": "mon·štran·cie",
        "najvľúdnejšou": "naj·vľúd·nej·šou",
        "chrbtica": "chrb·ti·ca",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_a_prefix_seam_outranks_the_consonant_count():
    """3.1 decides before 4.3 does, even when the base opens with a consonant.

    ``vždy`` is a word, so ``navždy`` is ``na`` before it and the seam is the
    division point. Counting consonants instead offers ``nav|ždy`` — a reading
    of a boundary that is not there.
    """
    assert hyphenate("navždy") == "na·vždy"
    assert hyphenate("povždy") == "po·vždy"


def test_tva_is_a_cluster_the_rules_handle_and_not_a_suffix():
    """``pas|tva`` is 4.3 already: tv- opens ``tvoj``, so the point never moves.

    Listing ``tva`` as a suffix bought that one word and cost two families. It
    outranked the real suffix in the genitive of ``·stvo`` (``mužs|tva`` for
    ``muž|stva``, while ``muž|stvo`` was right all along), and it overrode 4.2
    wherever tv is the whole cluster between two nuclei (``bri|tva``).
    """
    assert hyphenate("pastva") == "pas·tva"
    assert hyphenate("mužstva") == hyphenate("mužstvo").replace("stvo", "stva")
    expected = {
        "mužstva": "muž·stva",
        "božstva": "bož·stva",
        "bohatstva": "bo·hat·stva",
        "majstrovstva": "maj·strov·stva",
        "britva": "brit·va",
        "mŕtva": "mŕt·va",
        "plytvala": "plyt·va·la",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_two_consonants_are_untouched_by_the_opening_test():
    """4.2 leaves one consonant on each side and 4.3 never reaches that case."""
    for word, expected in (("láska", "lás·ka"), ("maslo", "mas·lo"), ("okno", "ok·no")):
        assert hyphenate(word) == expected


def test_bound_greek_second_member_divides_at_its_seam():
    """3.4 with the recognisability test of 3.5: -krat/-krac alternate visibly."""
    expected = {
        "aristokrat": "aris·to·krat",
        "aristokraciu": "aris·to·kra·ciu",
        "demokrat": "de·mo·krat",
        "demokracia": "de·mo·kra·cia",
        "byrokratickými": "by·ro·kra·tic·ký·mi",
        "teokracia": "te·o·kra·cia",
    }
    assert {word: hyphenate(word) for word in expected} == expected

    # No first part of its own, or none that a reader would see — no seam.
    untouched = {
        "Sokrata": "So·kra·ta",
        "kratochvíle": "kra·to·chví·le",
        "skracovanie": "skra·co·va·nie",
        "Demokrita": "De·mok·ri·ta",
        "demontovali": "de·mon·to·va·li",
        "demolačnej": "de·mo·lač·nej",
    }
    assert {word: hyphenate(word) for word in untouched} == untouched


def test_default_output_never_isolates_a_single_letter():
    """The doublet of 3.5 is two readings of one boundary, not two boundaries.

    Offered together they read as a stray letter — ``lie·ta·d·lo`` — which is
    what a typesetter wants and a human never does.
    """
    for word in ("lietadlo", "celistvej", "naskladať", "funkčný", "audienčnej"):
        parts = hyphenate(word, separator="-").split("-")
        assert all(len(part) > 1 for part in parts), (word, parts)


def test_all_points_is_a_superset_of_the_preferred_reading():
    for word in ("lietadlo", "celistvej", "naskladať", "funkčný", "prekladateľský"):
        assert set(break_points(word)) <= set(break_points(word, all_points=True))


def test_the_three_levels_of_section_9_are_kept_apart():
    """Basic, variant and contextual are three grades, not two.

    Section 9 lists the variant rules exhaustively — the three classes of 3.5
    and the doubled foreign consonants — so neither of the two rules phrased as
    "spravidla nie, ale niekedy áno" belongs there. ``pou|čiť`` (3.4) and the
    one-letter opening syllable (step 7 of section 8) are legal points the norm
    tells the typesetter to leave alone unless the measure forces his hand.
    """
    for word in ("poučiť", "neužil", "trojuholník", "všeobecne", "ideál"):
        assert break_points(word) == break_points(word, all_points=True), word
        assert set(break_points(word)) < set(break_points(word, contextual=True)), word

    assert hyphenate("poučiť") == "po·učiť"
    assert hyphenate("poučiť", contextual=True) == "po·u·čiť"
    assert hyphenate("všeobecne") == "vše·obec·ne"
    assert hyphenate("všeobecne", contextual=True) == "vše·o·bec·ne"
    assert hyphenate("ideál") == "ide·ál"
    assert hyphenate("ideál", contextual=True) == "i·de·ál"


def test_a_one_letter_syllable_is_contextual_at_the_start_and_barred_at_the_end():
    """The two edges are graded differently and the code must not blur them.

    Section 9 puts "neoddeliť jednopísmenovú koncovú slabiku" among the basic
    rules — an outright ban — while the opening syllable is only "spravidla"
    avoided. So no level may end a word on a lone vowel, and only the
    contextual level may start one on it.
    """
    for word in ("ideál", "Mária", "rádio", "štúdio"):
        for flags in ({}, {"all_points": True}, {"contextual": True},
                      {"all_points": True, "contextual": True}):
            points = break_points(word, **flags)
            assert len(word) - 1 not in points, (word, flags)


def test_divisions_writes_out_every_permitted_break():
    assert divisions("lietadlo") == ["lie-tadlo", "lieta-dlo", "lietad-lo"]
    assert divisions("pes") == []


def test_variant_reading_is_closed_to_the_three_classes_of_35():
    """A prefix seam is not one of them, whatever the TeX patterns offer.

    ``nas|kladať`` has no footing in PSP: what follows na· is the base, and skl·
    is the root's own onset, not a suffix spelled alike.
    """
    for word in ("naskladať", "neposkytla", "naskakovali", "doskočiť"):
        assert break_points(word) == break_points(word, all_points=True), word


def test_compound_seam_of_the_multiplicative_numeral():
    expected = {
        "dvakrát": "dva·krát",
        "stokrát": "sto·krát",
        "obakrát": "oba·krát",
        "koľkokrát": "koľ·ko·krát",
        "dvanásťkrát": "dva·násť·krát",
        "desaťstokrát": "de·sať·sto·krát",
        "tristošesťdesiatpäťkrát": "tri·sto·šesť·de·siat·päť·krát",
        "štyristokrát": "šty·ri·sto·krát",
        "štyristotisíckrát": "šty·ri·sto·ti·síc·krát",
        "podruhýkrát": "po·dru·hý·krát",
        "šestnásťkrát": "šest·násť·krát",
        "nekonečnekrát": "ne·ko·neč·ne·krát",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_every_cardinal_through_one_thousand_keeps_its_component_seams():
    for number in range(1, 1001):
        parts = cardinal_parts(number)
        word = cardinal_word(number)
        expected = "·".join(hyphenate(part) for part in parts)
        assert hyphenate(word) == expected, (number, word, parts, hyphenate(word))
    assert hyphenate("dvestopätnástky") == "dve·sto·pät·nást·ky"


def test_generated_numerals_cover_decimal_places_through_milliards():
    words = generate_numeral_training_words()

    assert len(words) == 1035
    assert {cardinal_word(number) for number in range(1, 1001)} <= words
    for place in (1, 10, 100):
        for digit in range(1, 10):
            count = digit * place
            expected = "tisíc" if count == 1 else cardinal_word(count) + "tisíc"
            assert expected in words
            if count != 1:
                parts = cardinal_parts(count) + ("tisíc",)
                assert hyphenate(expected) == "·".join(hyphenate(part) for part in parts)
    assert {
        "jedna", "jedno", "dve",
        "milión", "milióny", "miliónov",
        "miliarda", "miliardy", "miliárd",
    } <= words
    assert {
        word: hyphenate(word)
        for word in ("miliarda", "miliardy", "miliárd")
    } == {
        "miliarda": "mi·li·ar·da",
        "miliardy": "mi·li·ar·dy",
        "miliárd": "mi·li·árd",
    }


def test_grammatical_suffix_precedes_a_compound_lookalike():
    assert hyphenate("autormi") == "au·tor·mi"


def test_noun_stem_ending_stm_is_not_mistaken_for_the_me_suffix():
    assert hyphenate("astme") == "as·tme"


def test_lexical_stems_and_suffixes_outweigh_prefix_lookalikes():
    expected = {
        "problém": "prob·lém",
        "bezproblémovejšie": "bez·prob·lé·mo·vej·šie",
        "bezpríkladným": "bez·prí·klad·ným",
        "súdnosť": "súd·nosť",
        "bezsúdnosť": "bez·súd·nosť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_suffix_precedes_a_vowel_final_prefix_lookalike():
    expected = {
        "bezdôvodná": "bez·dô·vod·ná",
        "bezdôvodne": "bez·dô·vod·ne",
        "bezdôvodného": "bez·dô·vod·né·ho",
        "bezodný": "bez·od·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_arci_is_a_prefix_and_arch_lexicalizes_before_a_borrowed_stem():
    expected = {
        "arcikňazov": "ar·ci·kňa·zov",
        "arcizloduch": "ar·ci·zlo·duch",
        "arciaristokrat": "ar·ci·aris·to·krat",
        "arciesejca": "ar·ci·esej·ca",
        "archanjel": "arch·an·jel",
        "krátkozraký": "krát·ko·zra·ký",
        "kratochvíle": "kra·to·chví·le",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_arch_keeps_its_seam_only_where_the_second_part_is_a_word():
    assert hyphenate("archívu") == "ar·chí·vu"
    assert hyphenate("archeológ") == "ar·che·o·lóg"


def test_productive_morpheme_boundaries_from_reviewed_families():
    expected = {
        "Nebzučala": "Ne·bzu·ča·la",
        "mäsožravce": "mä·so·žrav·ce",
        "mäsožravé": "mä·so·žra·vé",
        "múdrostkársky": "múd·rost·kár·sky",
        "nebzučalo": "ne·bzu·ča·lo",
        "nezabzučí": "ne·za·bzu·čí",
        "nostkárstvo": "nost·kár·stvo",
        "pobožnostkári": "po·bož·nost·ká·ri",
        "pobožnostkárov": "po·bož·nost·ká·rov",
        "pobožnostkárske": "po·bož·nost·kár·ske",
        "pobzukovať": "po·bzu·ko·vať",
        "tajnostkár": "taj·nost·kár",
        "tajnostkársky": "taj·nost·kár·sky",
        "tajnostkárskym": "taj·nost·kár·skym",
        "tajnostkárskymi": "taj·nost·kár·sky·mi",
        "tajnostkárstve": "taj·nost·kár·stve",
        "tajnostkárstvo": "taj·nost·kár·stvo",
        "tajnostkárstvom": "taj·nost·kár·stvom",
        "zabzučal": "za·bzu·čal",
        "zabzučali": "za·bzu·ča·li",
        "zabzučalo": "za·bzu·ča·lo",
        "zabzučať": "za·bzu·čať",
        "Šťastkár": "Šťast·kár",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_foreign_one_nucleus_spellings_are_not_split_as_hiatuses():
    assert get_syllables("flauta") == ["flau", "ta"]
    assert get_syllables("leukémia") == ["leu", "ké", "mia"]

    expected = {
        "flauta": (4, 3),
        "leukémia": (3, 2),
    }

    for word, (required, forbidden) in expected.items():
        points = break_points(word)
        assert required in points
        assert forbidden not in points


def test_ai_is_one_nucleus_in_a_borrowed_stem():
    assert get_syllables("medaila") == ["me", "dai", "la"]


def test_a_lexical_compound_seam_does_not_turn_into_a_productive_prefix():
    assert get_syllables("šéflekár") == ["šéf", "le", "kár"]
    assert hyphenate("šéflekár") == "šéf·le·kár"
    assert get_syllables("šéfovať") == ["šé", "fo", "vať"]
    assert hyphenate("šéfovať") == "šé·fo·vať"


def test_an_onset_rises_in_sonority_and_opens_some_slovak_word():
    """Both halves of the test are needed, and each one alone gives a wrong answer.

    Sonority alone would make anjel a·njel, because nj rises — but no Slovak
    word opens with nj. Attestation alone would make sestra se·stra, because
    stôl opens with st — but st falls, and what opens a word need not open a
    syllable inside one.
    """
    assert get_syllables("Abrahám") == ["a", "bra", "hám"]
    assert get_syllables("Agricola") == ["a", "gri", "co", "la"]
    assert get_syllables("Ahriman") == ["a", "hri", "man"]
    assert get_syllables("adresa") == ["a", "dre", "sa"]
    assert get_syllables("akonáhle") == ["a", "ko", "ná", "hle"]
    assert get_syllables("ohryzok") == ["o", "hry", "zok"]
    assert get_syllables("okno") == ["o", "kno"]
    assert get_syllables("dobre") == ["do", "bre"]
    assert get_syllables("zebra") == ["ze", "bra"]
    # ...and where nothing rises, the cluster is divided.
    assert get_syllables("matka") == ["mat", "ka"]
    assert get_syllables("kapsa") == ["kap", "sa"]
    assert get_syllables("Alžbetou") == ["alž", "be", "tou"]
    assert get_syllables("rovnako") == ["rov", "na", "ko"]
    assert get_syllables("anjel") == ["an", "jel"]
    # A doubled consonant is two of the same sonority, so it never opens one.
    assert get_syllables("Agrippa") == ["a", "grip", "pa"]
    assert get_syllables("Abba") == ["ab", "ba"]


def test_a_short_r_or_l_is_a_nucleus_only_between_consonants():
    """It is a nucleus where no vowel can be one, and nowhere else.

    At the end of a word it is the coda of the syllable before it: Annamierl
    has three nuclei, not four, and an·na·mie·rl invents one.
    """
    assert get_syllables("vlk") == ["vlk"]
    assert get_syllables("prst") == ["prst"]
    assert get_syllables("Opatrnosť") == ["o", "pa", "tr", "nosť"]
    assert get_syllables("Annamierl") == ["an", "na", "mierl"]


def test_latin_qu_is_an_onset_and_not_a_syllable_of_its_own():
    assert get_syllables("aliquid") == ["a", "li", "quid"]
    assert get_syllables("quido") == ["qui", "do"]


def test_a_foreign_spelling_is_refused_rather_than_guessed_at():
    """What §5.4 forbids is applying the rules without knowing the pronunciation.

    Unknown foreign letters are refused rather than assigned a guessed sound.
    The refusal is about the sound value, not about the word being foreign —
    see the test below for the letters whose value is known.
    """
    with pytest.raises(ValueError, match="not spelled in Slovak"):
        get_syllables("Ærø")


def test_a_foreign_letter_with_a_known_sound_is_divided_by_slovak_rules():
    """§5.4 is a prohibition, not a referral to the foreign norm.

    The listed letters each occupy one known vowel or consonant slot, so there
    is no group to tear apart; the word is then divided by §3 and §4 like any
    other word in a Slovak sentence. This is not a Czech hyphenator — ÚJČ would print
    ak-cio-nář where §4.4 gives ak·ci·o·nář, and PSP is what binds here.
    """
    assert get_syllables("měsíc") == ["mě", "síc"]
    assert get_syllables("vůle") == ["vů", "le"]
    assert hyphenate("Dvořák") == "Dvo·řák"
    assert hyphenate("auflösen") == "auf·lö·sen"
    assert get_syllables("auflösen") == ["auf", "lö", "sen"]
    assert hyphenate("Alençon") == "Alen·çon"
    assert get_syllables("Alençon") == ["a", "len", "çon"]
    assert hyphenate("München") == "Mün·chen"
    assert hyphenate("Straße") == "Stra·ße"
    assert hyphenate("Noël") == "No·ël"
    assert hyphenate("Compiègne") == "Com·pi·èg·ne"
    assert hyphenate("Neufchâteau") == "Ne·uf·châ·te·au"

    # ř fills the r slot, so a cluster containing it divides where the one
    # written with r does — the tables list what Slovak words are written with.
    assert hyphenate("bratře") == "brat·ře"
    assert hyphenate("bratre") == "brat·re"

    # PSP §5.4 second sentence: a vowel group read as one syllable stays whole.
    assert hyphenate("koupě") == "kou·pě"


@pytest.mark.xfail(
    strict=True,
    reason="Proust and soused are foreign words the engine reads as so-/pro- "
           "plus a u- root; this needs the word-identity layer",
)
def test_a_foreign_ou_is_not_split_behind_a_prefix_shaped_opening():
    assert hyphenate("Proust") == "Proust"
    assert hyphenate("Prousta") == "Prous·ta"
    assert hyphenate("Souci") == "Sou·ci"
    assert hyphenate("soused") == "sou·sed"


def test_a_productive_prefix_keeps_its_seam_in_front_of_u():
    assert hyphenate("poučka") == "po·uč·ka"
    assert hyphenate("naučiť") == "na·učiť"
    assert hyphenate("neuveriteľný") == "ne·uve·ri·teľ·ný"


@pytest.mark.xfail(
    strict=True,
    reason="do- is a real prefix that does take u- roots (do·učiť), so nothing "
           "but knowing douglaska is a loan refuses the seam",
)
def test_a_lexicalized_ou_survives_a_prefix_shaped_opening():
    assert hyphenate("douglaska") == "doug·las·ka"
    assert hyphenate("douglasky") == "doug·las·ky"


def test_a_prefix_before_a_u_root_keeps_its_seam():
    assert hyphenate("doučiť") == "do·učiť"


def test_german_and_french_vowel_letters_are_hyphenation_nuclei():
    for vowel in "àâæèêëěîïöœùûüůÿ":
        assert is_vowel(vowel)
        assert hyphenate(f"b{vowel}ba") == f"b{vowel}·ba"

    assert is_vowel("ä")
    assert hyphenate("mäkký") == "mäk·ký"


def test_terminal_dz_is_one_phoneme():
    assert split_into_phonemes("dž") == ["dž"]


def test_uncertain_non_slovak_tokens_are_not_hyphenated():
    for token in ("d’Arc", "L'Arbre", "Saint-Denis"):
        assert hyphenate(token) == token


def test_break_points_agree_with_hyphenate():
    for word in ("Prekladateľský", "rozdeľovanie", "podzemie", "trojuholník"):
        offsets = break_points(word)
        rebuilt = []
        prev = 0
        for pos in offsets:
            rebuilt.append(word[prev:pos])
            prev = pos
        rebuilt.append(word[prev:])
        assert "\u00b7".join(rebuilt) == hyphenate(word)


def test_separator_is_configurable():
    assert hyphenate("podzemie", separator="-") == "pod-ze-mie"
    assert hyphenate("podzemie", separator="\u00ad") == "pod\u00adze\u00admie"


def test_unbreakable_words_have_no_break_points():
    for word in ("vlk", "prst", "Saint-Denis", "d’Arc"):
        assert break_points(word) == []
        assert hyphenate(word) == word
