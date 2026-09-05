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
        "neohraničený": "ne·ohra·ni·če·ný",
        "ohrádka": "ohrád·ka",
        "ohrádzať": "ohrá·dzať",
        "obohraných": "ob·ohra·ných",
        "obohratá": "ob·ohra·tá",
        "rozohrať": "roz·ohrať",
        "neohrabaný": "ne·ohra·ba·ný",
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
        "neukrátené": "ne·ukrá·te·né",
        "úkryt": "úkryt",
        "samozrejme": "sa·mo·zrej·me",
        "afrodiziakum": "af·ro·di·zi·a·kum",
        "akciami": "ak·ci·ami",
        "funkciami": "funk·ci·ami",
        "klientka": "klient·ka",
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


def test_client_and_patient_keep_codified_diphthongal_ie():
    expected = {
        "klient": "klient",
        "klienta": "klien·ta",
        "klientka": "klient·ka",
        "klientov": "klien·tov",
        "pacient": "pa·cient",
        "pacienta": "pa·cien·ta",
        "pacientka": "pa·cient·ka",
        "pacientov": "pa·cien·tov",
        "koeficientom": "ko·e·fi·ci·en·tom",
        "preorientovanie": "pre·ori·en·to·va·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_pokrytectvo_prefers_the_agent_noun_seam_and_keeps_the_variant():
    assert hyphenate("pokrytectvo") == "po·kry·tec·tvo"
    assert hyphenate("pokrytectvo", all_points=True) == "po·kry·te·c·tvo"
    assert hyphenate("pokrytectvom") == "po·kry·tec·tvom"
    assert hyphenate("pokrytectvom", all_points=True) == "po·kry·te·c·tvom"


def test_aleut_hiatus_does_not_split_later_ou_endings():
    assert get_syllables("aleutskí") == ["a", "le", "ut", "skí"]
    assert get_syllables("Aleutkou") == ["a", "le", "ut", "kou"]


def test_u_prefix_keeps_the_kryt_root_cluster_intact():
    expected = {
        "ukryť": "ukryť",
        "ukrytú": "ukry·tú",
        "ukrytý": "ukry·tý",
        "ukrývať": "ukrý·vať",
        "ukrývali": "ukrý·va·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("úkrytu") == "úkry·tu"
    assert hyphenate("krytý") == "kry·tý"


def test_pra_lookalikes_keep_lexical_stems_and_true_prefix_contrasts():
    expected = {
        "prachmi": "prach·mi",
        "prahla": "prah·la",
        "prahli": "prah·li",
        "prahlo": "prah·lo",
        "prakmi": "prak·mi",
        "prašná": "praš·ná",
        "prašteným": "praš·te·ným",
        "praštiť": "praš·tiť",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("prahistorický") == "pra·his·to·ric·ký"
    assert hyphenate("prakmeň") == "pra·kmeň"
    assert hyphenate("prakrajania") == "pra·kra·ja·nia"
    assert hyphenate("praskali") == "pras·ka·li"
    assert hyphenate("prašpecifické") == "pra·špe·ci·fic·ké"


def test_attested_bd_onset_licenses_real_prefix_boundaries():
    expected = {
        "prebdel": "pre·bdel",
        "prebdela": "pre·bde·la",
        "prebdená": "pre·bde·ná",
        "prebdieť": "pre·bdieť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_prazd_family_keeps_suffix_and_compound_seams():
    expected = {
        "prázdna": "práz·dna",
        "prázdneho": "práz·dne·ho",
        "zaneprázdnená": "za·ne·práz·dne·ná",
        "zaneprázdnenosti": "za·ne·práz·dne·nos·ti",
        "prázdny": "práz·dny",
        "prázdnymi": "práz·dny·mi",
        "prázdnohlaví": "práz·dno·hla·ví",
        "prázdnosť": "prázd·nosť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_reviewed_rmss_families_follow_psp_morpheme_evidence():
    expected = {
        "halapartne": "ha·la·par·tne",
        "najprospešnejšie": "naj·pro·speš·nej·šie",
        "nepozostáva": "ne·po·zo·stá·va",
        "nepozostávajú": "ne·po·zo·stá·va·jú",
        "nepozostávali": "ne·po·zo·stá·va·li",
        "neprospech": "ne·pro·spech",
        "nevyprázdni": "ne·vy·práz·dni",
        "poloprázdna": "po·lo·práz·dna",
        "ľudoprázdna": "ľu·do·práz·dna",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_rmss_root_conflicts_are_independently_decided_by_psp():
    expected = {
        "doktor": "dok·tor",
        "doktorský": "dok·tor·ský",
        "Doktrína": "Dok·trí·na",
        "doktrinálne": "dok·tri·nál·ne",
        "poloprázdny": "po·lo·práz·dny",
        "prázdniny": "práz·dni·ny",
        "prázdninový": "práz·dni·no·vý",
        "zostra": "zos·tra",
        "povrázok": "pov·rá·zok",
        "transcendentný": "trans·cen·dent·ný",
        "transcendentálne": "trans·cen·den·tál·ne",
        "transcendentálny": "trans·cen·den·tál·ny",
        "súkromie": "súk·ro·mie",
        "súkromne": "súk·rom·ne",
        "súkromník": "súk·rom·ník",
        "súkromný": "súk·rom·ný",
        "poklad": "pok·lad",
        "pokladník": "pok·lad·ník",
        "potmehúdsky": "pot·me·húd·sky",
        "prestíž": "pres·tíž",
        "prestížny": "pres·tíž·ny",
        "doska": "dos·ka",
        "halapartňa": "ha·la·par·tňa",
        "Haitská": "Hait·ská",
        "nektár": "nek·tár",
        "poklop": "pok·lop",
        "pokrový": "pok·ro·vý",
        "krídlo": "kríd·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected

    true_prefixes = {
        "doskočiť": "do·sko·čiť",
        "doskákal": "do·ská·kal",
        "pokladať": "po·kla·dať",
        "poklopal": "po·klo·pal",
        "pokropiť": "po·kro·piť",
        "zostrelil": "zo·stre·lil",
    }
    assert {word: hyphenate(word) for word in true_prefixes} == true_prefixes


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


def test_prost_short_comparative_is_not_misread_as_pro_prefix():
    assert hyphenate("prostší") == "prost·ší"
    assert hyphenate("najprostšia") == "naj·prost·šia"


def test_superlatives_keep_the_naj_prefix_and_compound_stem_seams():
    assert hyphenate("najranejší") == "naj·ra·nej·ší"
    assert hyphenate("najprvotriednejšieho") == "naj·pr·vo·tried·nej·šie·ho"


def test_lengthened_na_and_za_prefixes_keep_lexical_root_seams():
    expected = {
        "náklad": "ná·klad",
        "nákladnými": "ná·klad·ný·mi",
        "náklaďákov": "ná·kla·ďá·kov",
        "náklaďáku": "ná·kla·ďá·ku",
        "náklaďáky": "ná·kla·ďá·ky",
        "nástup": "ná·stup",
        "nástupníctvo": "ná·stup·níc·tvo",
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
    assert hyphenate("ustupovať") == "ustu·po·vať"


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
    assert hyphenate("oplatí") == "opla·tí"


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
    assert hyphenate("sprostredkovanie") == "s·pro·stred·ko·va·nie"
    assert hyphenate("ústredný") == "ústred·ný"
    assert hyphenate("umierať") == "umie·rať"
    assert hyphenate("oklamal") == "ok·la·mal"
    assert hyphenate("sklamal") == "skla·mal"
    assert hyphenate("správny") == "správ·ny"
    assert hyphenate("ochladenie") == "och·la·de·nie"
    assert hyphenate("schladenie") == "schla·de·nie"
    assert hyphenate("svetlochladne") == "svet·loch·lad·ne"


def test_stred_family_keeps_the_documented_root_seams():
    expected = {
        "prostredie": "pro·stred·ie",
        "prostredníctvo": "pro·stred·níc·tvo",
        "sprostredkovanie": "s·pro·stred·ko·va·nie",
        "nesprostredkuje": "ne·s·pro·stred·ku·je",
        "ústredia": "ústred·ia",
        "ústredný": "ústred·ný",
        "praústrednou": "pra·ústred·nou",
        "uprostred": "upro·stred",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("najbezprostrednejšia") == "naj·bez·pro·stred·nej·šia"
    assert hyphenate("všestredové") == "vše·stre·do·vé"
    assert hyphenate("stredoeurópania") == "stre·do·eu·ró·pa·nia"


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
    assert hyphenate("označený") == "ozna·če·ný"
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
    assert hyphenate("oplodnenie") == "oplod·ne·nie"
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
    assert hyphenate("utvrdenie") == "utvr·de·nie"
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
    assert hyphenate("ustúpi") == "ustú·pi"
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
        "neosobný": "ne·osob·ný",
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
    assert hyphenate("ustojíme") == "usto·jí·me"
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
    assert hyphenate("otlačky") == "otlač·ky"
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
        "ochrana": "ochra·na",
        "záchrana": "zá·chra·na",
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
        "obohatiť": "obo·ha·tiť",
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
        "utrasie": "utra·sie",
        "sústrasti": "sú·stras·ti",
        "rozložiť": "roz·lo·žiť",
        "bezradný": "bez·rad·ný",
        "rozradostený": "roz·ra·dos·te·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_poslat_and_postit_do_not_gain_a_false_po_prefix():
    expected = {
        "nepošle": "ne·poš·le",
        "nepošlem": "ne·poš·lem",
        "nepošlete": "ne·poš·le·te",
        "nepostí": "ne·pos·tí",
        "nepostia": "ne·pos·tia",
        "nepostil": "ne·pos·til",
        "nepostíme": "ne·pos·tí·me",
        "nepošliapal": "ne·po·šlia·pal",
        "nepošmykli": "ne·po·šmyk·li",
        "nepostihne": "ne·po·stih·ne",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_postul_posva_and_potk_families_do_not_gain_a_false_po_prefix():
    expected = {
        "postulátom": "pos·tu·lá·tom",
        "pošvy": "poš·vy",
        "potkana": "pot·ka·na",
        "potkla": "pot·kla",
        "potkne": "potk·ne",
        "potknúť": "potk·núť",
        "potkol": "pot·kol",
        "potkýnajú": "pot·ký·na·jú",
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
        "veľadôstojní": "ve·ľa·dôs·toj·ní",
        "najveľadôstojnejší": "naj·ve·ľa·dôs·toj·nej·ší",
        "stočlenná": "sto·člen·ná",
        "stočlennou": "sto·člen·nou",
        "ostrihané": "ostri·ha·né",
        "neostrihané": "ne·ostri·ha·né",
        "uvravené": "uv·ra·ve·né",
        "dohromady": "do·hro·ma·dy",
        "pohroma": "po·hro·ma",
        "včlenenie": "včle·ne·nie",
        "nevčlenili": "ne·včle·ni·li",
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
        "neohlásil": "ne·ohlá·sil",
        "právnik": "práv·nik",
        "trávnik": "tráv·nik",
        "kávnik": "káv·nik",
        "uchopiť": "ucho·piť",
        "schopný": "schop·ný",
        "psychopat": "psy·cho·pat",
        "uschopnil": "us·chop·nil",
        "ustáliť": "ustá·liť",
        "neustále": "ne·ustá·le",
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
        "spoluvlastníctve": "spo·lu·vlast·níc·tve",
        "plnohodnotný": "pl·no·hod·not·ný",
        "zhodnotenie": "zhod·no·te·nie",
        "maškrtami": "maš·kr·ta·mi",
        "uškrtil": "uš·kr·til",
        "spracovať": "spra·co·vať",
        "opracovať": "opra·co·vať",
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
        "lesklo": "lesk·lo",
        "prásklo": "prásk·lo",
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
        "svetočlovek": "sve·to·člo·vek",
        "svetloprázdna": "svet·lo·práz·dna",
        "svetoslepý": "sve·to·sle·pý",
        "svetosliedičský": "sve·to·slie·dič·ský",
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
        "ovplyvniť": "ovplyv·niť",
        "neovplyvnený": "ne·ovplyv·ne·ný",
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
        "podelo": "po·de·lo",
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
        "uspôsobené": "uspô·so·be·né",
        "neuspôsobil": "ne·uspô·so·bil",
        "uzdravený": "uzdra·ve·ný",
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
        "utrápený": "utrá·pe·ný",
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
        "neopatrnosť": "ne·opa·tr·nosť",
        "veľkopatriarcha": "veľ·ko·pat·riar·cha",
        "nedopatrenie": "ne·do·pat·re·nie",
        "ozbrojený": "ozbro·je·ný",
        "neozbrojený": "ne·ozbro·je·ný",
        "rozbroj": "roz·broj",
        "zaútočil": "za·úto·čil",
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
        "nezhustla": "ne·zhust·la",
        "substancia": "sub·stan·cia",
        "protestant": "pro·tes·tant",
        "novoustanovený": "no·vo·usta·no·ve·ný",
        "novopovstanie": "no·vo·po·vsta·nie",
        "dohorel": "do·ho·rel",
        "bohorúhač": "bo·ho·rú·hač",
        "stredohoria": "stre·do·ho·ria",
        "praskajúce": "pras·ka·jú·ce",
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


def test_forty_first_discovered_family_batch_keeps_only_clear_plav_compounds():
    expected = {
        "pieskovoplavých": "pies·ko·vo·pla·vých",
        "ryšavoplavé": "ry·ša·vo·pla·vé",
        "sivoplavý": "si·vo·pla·vý",
        "svetloplavé": "svet·lo·pla·vé",
        "svetloplavými": "svet·lo·pla·vý·mi",
        "svetlozlatoplavé": "svet·lo·zla·to·pla·vé",
        "tmavoplavé": "tma·vo·pla·vé",
        "tmavoplavých": "tma·vo·pla·vých",
        "tmavozlatoplavej": "tma·vo·zla·to·pla·vej",
        "vzduchoplavby": "vzdu·cho·plav·by",
        "vzduchoplavci": "vzdu·cho·plav·ci",
        "vzduchoplavcov": "vzdu·cho·plav·cov",
        "zlatoplavé": "zla·to·pla·vé",
        "zlatoplavými": "zla·to·pla·vý·mi",
        "špinavoplavými": "špi·na·vo·pla·vý·mi",
        "povznáša": "po·vzná·ša",
        "roznáša": "roz·ná·ša",
        "neuznášali": "ne·uzná·ša·li",
        "prieplavu": "priep·la·vu",
        "záplava": "záp·la·va",
        "splaviť": "spla·viť",
        "vplavuje": "vpla·vu·je",
        "úplavicu": "úp·la·vi·cu",
        "neustať": "ne·ustať",
        "ostať": "os·tať",
        "vstať": "vstať",
        "povstať": "po·vstať",
        "zaostať": "za·os·tať",
        "sprístupniť": "sprí·stup·niť",
        "sprísniť": "sprís·niť",
        "obluda": "ob·lu·da",
        "najobludnejší": "naj·ob·lud·nej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_povsimnut_family_keeps_the_prefix_seam():
    assert hyphenate("povšimnúť") == "po·všim·núť"
    assert hyphenate("nepovšimnutý") == "ne·po·všim·nu·tý"
    assert hyphenate("všimnúť") == "všim·núť"
    assert hyphenate("povstať") == "po·vstať"


def test_forty_second_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "bledozelenozlaté": "ble·do·ze·le·no·zla·té",
        "ryšavozlatých": "ry·ša·vo·zla·tých",
        "svetlozlato": "svet·lo·zla·to",
        "svetlozlatoplavé": "svet·lo·zla·to·pla·vé",
        "tmavozlatoplavej": "tma·vo·zla·to·pla·vej",
        "trávovozlatozelená": "trá·vo·vo·zla·to·ze·le·ná",
        "zelenkastozlato": "ze·len·kas·to·zla·to",
        "zelenkastozlaté": "ze·len·kas·to·zla·té",
        "zelenozlato": "ze·le·no·zla·to",
        "zelenozlatá": "ze·le·no·zla·tá",
        "zlozvyk": "zlo·zvyk",
        "zlozvykom": "zlo·zvy·kom",
        "zlozvykov": "zlo·zvy·kov",
        "zlozvyku": "zlo·zvy·ku",
        "zlozvyky": "zlo·zvy·ky",
        "útvar": "út·var",
        "paútvarov": "pa·út·va·rov",
        "lektvar": "lek·tvar",
        "neodolal": "ne·odo·lal",
        "stodola": "sto·do·la",
        "ubrániť": "ub·rá·niť",
        "neubránil": "ne·ub·rá·nil",
        "desaťzlatkovú": "de·sať·zlat·ko·vú",
        "bledozlaté": "ble·do·zla·té",
        "dozlata": "do·zla·ta",
        "nezvyklé": "ne·zvyk·lé",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_third_discovered_family_batch_keeps_only_nested_uza_vrel_seam():
    expected = {
        "uzavrel": "uza·vrel",
        "uzavrela": "uza·vre·la",
        "uzavreli": "uza·vre·li",
        "uzavrelo": "uza·vre·lo",
        "neuzavrel": "ne·uza·vrel",
        "neuzavrela": "ne·uza·vre·la",
        "neuzavreli": "ne·uza·vre·li",
        "neuzavrelo": "ne·uza·vre·lo",
        "vzklíčiť": "vzklí·čiť",
        "sklíčka": "sklíč·ka",
        "oplátku": "op·lát·ku",
        "splátka": "splát·ka",
        "sklapne": "sklap·ne",
        "poschodovom": "po·scho·do·vom",
        "vchodové": "vcho·do·vé",
        "sedemchodovú": "se·dem·cho·do·vú",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_fourth_discovered_family_batch_keeps_only_clear_prefix_seams():
    expected = {
        "odopierať": "od·opie·rať",
        "neodopieral": "ne·od·opie·ral",
        "preduchovnenie": "pre·du·chov·ne·nie",
        "preduchovniť": "pre·du·chov·niť",
        "neokresávať": "ne·ok·re·sá·vať",
        "pohanokresťanmi": "po·ha·no·kres·ťan·mi",
        "netopierom": "ne·to·pie·rom",
        "popierať": "po·pie·rať",
        "vzduchové": "vzdu·cho·vé",
        "zduchovnenie": "zdu·chov·ne·nie",
        "mierumilovný": "mie·ru·mi·lov·ný",
        "zmilovať": "zmi·lo·vať",
        "uhrešiť": "uh·re·šiť",
        "zhrešiť": "zhre·šiť",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_fifth_discovered_family_batch_needs_no_new_runtime_seam():
    expected = {
        "nezbehla": "ne·zbeh·la",
        "rozbehla": "roz·beh·la",
        "neotvoril": "ne·ot·vo·ril",
        "pootvorené": "po·ot·vo·re·né",
        "divotvorné": "di·vo·tvor·né",
        "potvora": "po·tvo·ra",
        "prežila": "pre·ži·la",
        "použila": "po·uži·la",
        "ožila": "oži·la",
        "protismerné": "pro·ti·smer·né",
        "obojsmerná": "oboj·smer·ná",
        "usmernenie": "us·mer·ne·nie",
        "neusmerní": "ne·us·mer·ní",
        "sebausmernenie": "se·ba·us·mer·ne·nie",
        "pohnutie": "po·hnu·tie",
        "prahnutie": "prah·nu·tie",
        "dobehnutie": "do·beh·nu·tie",
        "trhnutie": "trh·nu·tie",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_sixth_discovered_family_batch_keeps_only_spolu_vzrus_seam():
    expected = {
        "spoluvzrušiteľnom": "spo·lu·vzru·ši·teľ·nom",
        "spoluvzdor": "spo·luv·zdor",
        "spoluvzrast": "spo·luv·zrast",
        "odchýlil": "od·chý·lil",
        "neodchýlila": "ne·od·chý·li·la",
        "uchýliť": "uchý·liť",
        "neuchýlil": "ne·uchý·lil",
        "schýlil": "schý·lil",
        "vyliečiť": "vy·lie·čiť",
        "mliečny": "mlieč·ny",
        "mliečnobiela": "mlieč·no·bie·la",
        "bezzákonnosť": "bez·zá·kon·nosť",
        "novozákonný": "no·vo·zá·kon·ný",
        "protizákonný": "pro·ti·zá·kon·ný",
        "uzákonený": "uzá·ko·ne·ný",
        "napriamo": "na·pria·mo",
        "upriamovať": "upria·mo·vať",
        "neupriamil": "ne·upria·mil",
        "vzpriamiť": "vzpria·miť",
        "narušiteľ": "na·ru·ši·teľ",
        "porušiteľný": "po·ru·ši·teľ·ný",
        "vzrušiteľný": "vzru·ši·teľ·ný",
        "nezrušiteľný": "ne·zru·ši·teľ·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_seventh_discovered_family_batch_keeps_only_pre_dier_seam():
    expected = {
        "predierať": "pre·die·rať",
        "predierajúce": "pre·die·ra·jú·ce",
        "predierkovaných": "pre·dier·ko·va·ných",
        "odierať": "odie·rať",
        "doudierané": "do·udie·ra·né",
        "udierať": "udie·rať",
        "zdierať": "zdie·rať",
        "bokombradami": "bo·kom·bra·da·mi",
        "brada": "bra·da",
        "vlastizrada": "vlas·ti·zra·da",
        "rozvážny": "roz·váž·ny",
        "nerozvážnosť": "ne·roz·váž·nosť",
        "zuhoľnatenie": "zu·hoľ·na·te·nie",
        "rozvrat": "roz·vrat",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_eighth_discovered_family_batch_keeps_only_na_pri_znak_seams():
    expected = {
        "náznak": "ná·znak",
        "náznakmi": "ná·znak·mi",
        "náznakoch": "ná·zna·koch",
        "náznakom": "ná·zna·kom",
        "náznakov": "ná·zna·kov",
        "náznaku": "ná·zna·ku",
        "náznaky": "ná·zna·ky",
        "príznak": "prí·znak",
        "príznakoch": "prí·zna·koch",
        "príznakov": "prí·zna·kov",
        "príznaky": "prí·zna·ky",
        "ploskočelí": "plos·ko·če·lí",
        "uskočiť": "us·ko·čiť",
        "vskočil": "vsko·čil",
        "úskočný": "ús·koč·ný",
        "obralo": "ob·ra·lo",
        "žobralo": "žob·ra·lo",
        "dalajláma": "da·laj·lá·ma",
        "olámali": "olá·ma·li",
        "vlámania": "vlá·ma·nia",
        "zlámať": "zlá·mať",
        "osprchovať": "os·pr·cho·vať",
        "sprcha": "spr·cha",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_forty_ninth_discovered_family_batch_needs_no_new_runtime_seam():
    expected = {
        "neskľúči": "ne·skľú·či",
        "skľúčený": "skľú·če·ný",
        "zvečerilo": "zve·če·ri·lo",
        "zvečerievať": "zve·če·rie·vať",
        "inadiaľ": "ina·diaľ",
        "tadiaľ": "ta·diaľ",
        "zdiaľky": "zdiaľ·ky",
        "vzdiaľme": "vzdiaľ·me",
        "protiústavné": "pro·ti·ús·tav·né",
        "nesústavné": "ne·sú·stav·né",
        "sústava": "sú·sta·va",
        "opálené": "opá·le·né",
        "spáleného": "spá·le·né·ho",
        "upálené": "upá·le·né",
        "vpálené": "vpá·le·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fiftieth_discovered_family_batch_keeps_only_novo_polo_zver_seams():
    expected = {
        "novozverbovaného": "no·vo·zver·bo·va·né·ho",
        "polozvermi": "po·lo·zver·mi",
        "bezverný": "bez·ver·ný",
        "číslovanie": "čís·lo·va·nie",
        "veslovanie": "ves·lo·va·nie",
        "reportér": "re·por·tér",
        "športový": "špor·to·vý",
        "prírodovedec": "prí·ro·do·ve·dec",
        "svedectvo": "sve·dec·tvo",
        "pahreba": "pah·re·ba",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_first_discovered_family_batch_keeps_only_clear_psp_seams():
    expected = {
        "návnad": "ná·vnad",
        "návnada": "ná·vna·da",
        "návnady": "ná·vna·dy",
        "matkovraha": "mat·ko·vra·ha",
        "matkovrahmi": "mat·ko·vrah·mi",
        "otcovrahov": "ot·co·vra·hov",
        "samovrah": "sa·mo·vrah",
        "samovrahovia": "sa·mo·vra·ho·via",
        "nesťažoval": "ne·sťa·žo·val",
        "nesťažuj": "ne·sťa·žuj",
        "posťažovať": "po·sťa·žo·vať",
        "posťažujete": "po·sťa·žu·je·te",
        "zjavovať": "zja·vo·vať",
        "nezjavovalo": "ne·zja·vo·va·lo",
        "omastené": "omas·te·né",
        "zmastili": "zmas·ti·li",
        "šlamastika": "šla·mas·ti·ka",
        "osťažená": "os·ťa·že·ná",
        "dvojsťažňové": "dvoj·sťaž·ňo·vé",
        "trojsťažník": "troj·sťaž·ník",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_second_discovered_family_batch_needs_no_new_runtime_seam():
    expected = {
        "aktov": "ak·tov",
        "kataraktov": "ka·ta·rak·tov",
        "extraktov": "ex·tra·ktov",
        "faktov": "fak·tov",
        "kontaktov": "kon·tak·tov",
        "paktovania": "pak·to·va·nia",
        "skontaktovali": "skon·tak·to·va·li",
        "plán": "plán",
        "kaplán": "kap·lán",
        "kaplánovi": "kap·lá·no·vi",
        "naplánovať": "na·plá·no·vať",
        "bezplánovité": "bez·plá·no·vi·té",
        "kvet": "kvet",
        "okvetné": "ok·vet·né",
        "okvetí": "ok·ve·tí",
        "vzkvetať": "vzkve·tať",
        "krížokveté": "krí·žo·kve·té",
        "rozkvet": "roz·kvet",
        "kroč": "kroč",
        "vkročiť": "vkro·čiť",
        "nevkročil": "ne·vkro·čil",
        "prekročiť": "pre·kro·čiť",
        "vykročiť": "vy·kro·čiť",
        "alej": "alej",
        "malej": "ma·lej",
        "nalej": "na·lej",
        "zalejú": "za·le·jú",
        "galejník": "ga·lej·ník",
        "dokonalejších": "do·ko·na·lej·ších",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_third_discovered_family_batch_keeps_only_polo_spolu_znic_seams():
    expected = {
        "polozničenú": "po·lo·zni·če·nú",
        "spoluzničený": "spo·lu·zni·če·ný",
        "železničná": "že·lez·nič·ná",
        "hriešny": "hrieš·ny",
        "orieška": "orieš·ka",
        "roztriešti": "roz·trieš·ti",
        "zmiluje": "zmi·lu·je",
        "nezmiluje": "ne·zmi·lu·je",
        "povlakom": "po·vla·kom",
        "tlakomery": "tla·ko·me·ry",
        "areál": "are·ál",
        "zreálnili": "zre·ál·ni·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_fourth_discovered_family_batch_keeps_only_sto_stop_and_samo_sviet_seams():
    expected = {
        "stostopovej": "sto·sto·po·vej",
        "tridsaťstopové": "trid·sať·sto·po·vé",
        "samosvietiace": "sa·mo·svie·tia·ce",
        "samosvietiacich": "sa·mo·svie·tia·cich",
        "osvieti": "osvie·ti",
        "cestopisných": "ces·to·pis·ných",
        "čistopis": "čis·to·pis",
        "druhoradú": "dru·ho·ra·dú",
        "huhora": "hu·ho·ra",
        "dotvárať": "do·tvá·rať",
        "stvárať": "stvá·rať",
        "utvárať": "ut·vá·rať",
        "dlhopis": "dl·ho·pis",
        "neopisuje": "ne·opi·su·je",
        "dopis": "do·pis",
        "popis": "po·pis",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_fifth_discovered_family_batch_keeps_only_prie_zrac_seams():
    expected = {
        "priezračný": "prie·zrač·ný",
        "najpriezračnejší": "naj·prie·zrač·nej·ší",
        "prízračný": "príz·rač·ný",
        "zázračný": "zá·zrač·ný",
        "spriateľovať": "spria·te·ľo·vať",
        "neopadne": "ne·opad·ne",
        "dopadne": "do·pad·ne",
        "popadne": "po·pad·ne",
        "nájazd": "ná·jazd",
        "krasojazdec": "kra·so·jaz·dec",
        "vjazd": "vjazd",
        "zjazd": "zjazd",
        "neotočil": "ne·oto·čil",
        "pootočil": "po·oto·čil",
        "červotoč": "čer·vo·toč",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_sixth_discovered_family_batch_keeps_only_bystro_sluch_seam():
    expected = {
        "bystrosluchých": "bys·tro·slu·chých",
        "poslucháč": "pos·lu·cháč",
        "praobyvateľov": "pra·oby·va·te·ľov",
        "dobyvateľ": "do·by·va·teľ",
        "nádych": "ná·dych",
        "vdychovať": "vdy·cho·vať",
        "vzdych": "vzdych",
        "vládychtivý": "vlá·dych·ti·vý",
        "očista": "očis·ta",
        "najočistnejšie": "naj·očist·nej·šie",
        "nastoknutý": "na·stok·nu·tý",
        "stokrát": "sto·krát",
        "aristokrat": "aris·to·krat",
        "čistokrvné": "čis·to·krv·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_seventh_discovered_family_batch_keeps_only_polo_krot_seam():
    expected = {
        "polokrotký": "po·lo·krot·ký",
        "zhodli": "zhod·li",
        "sťahovať": "sťa·ho·vať",
        "odsťahovať": "od·sťa·ho·vať",
        "uťahovať": "uťa·ho·vať",
        "vzťahovať": "vzťa·ho·vať",
        "vpichu": "vpi·chu",
        "bankrot": "ban·krot",
        "skrotiť": "skro·tiť",
        "oplácať": "op·lá·cať",
        "splácať": "splá·cať",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_eighth_discovered_family_batch_keeps_only_spolu_hrac_seam():
    expected = {
        "spoluhráč": "spo·lu·hráč",
        "spoluhráča": "spo·lu·hrá·ča",
        "spoluhráči": "spo·lu·hrá·či",
        "spoluhráčov": "spo·lu·hrá·čov",
        "zbudovať": "zbu·do·vať",
        "skrížiť": "skrí·žiť",
        "zášklb": "záš·klb",
        "ošklbali": "oš·kl·ba·li",
        "neskvasených": "ne·skva·se·ných",
        "trkvasovia": "trk·va·so·via",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_fifty_ninth_discovered_family_batch_keeps_only_pri_zvuk_seam():
    expected = {
        "prízvuk": "prí·zvuk",
        "prízvukom": "prí·zvu·kom",
        "prízvukoval": "prí·zvu·ko·val",
        "prízvukujem": "prí·zvu·ku·jem",
        "ubiedená": "ubie·de·ná",
        "uposlúchnuť": "upos·lúch·nuť",
        "neuposlúchnutie": "ne·upos·lúch·nu·tie",
        "spolúradník": "spo·lú·rad·ník",
        "spoluúradníkom": "spo·lu·úrad·ní·kom",
        "súradnice": "sú·rad·ni·ce",
        "splesniveli": "sples·ni·ve·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixtieth_discovered_family_batch_has_no_safe_new_seam():
    expected = {
        "episkopátu": "epis·ko·pá·tu",
        "dopátrať": "do·pát·rať",
        "zakonopátené": "za·ko·no·pá·te·né",
        "popreli": "po·pre·li",
        "opreli": "opre·li",
        "podopreli": "pod·opre·li",
        "upreli": "up·re·li",
        "divokosť": "di·vo·kosť",
        "veľkosť": "veľ·kosť",
        "sladkosť": "slad·kosť",
        "ľudskosť": "ľud·skosť",
        "zaplieta": "za·plie·ta",
        "splieta": "splie·ta",
        "vplieta": "vplie·ta",
        "upliesť": "up·liesť",
        "špliechanie": "šplie·cha·nie",
        "odbytovali": "od·by·to·va·li",
        "ubytovanie": "uby·to·va·nie",
        "neubytoval": "ne·uby·to·val",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_first_discovered_family_batch_keeps_only_clear_psp_seams():
    expected = {
        "zimomravý": "zi·mo·mra·vý",
        "umravniť": "um·rav·niť",
        "jemnocit": "jem·no·cit",
        "neocitol": "ne·oci·tol",
        "pocit": "po·cit",
        "prediabolskú": "pre·dia·bol·skú",
        "zdiabolenie": "zdia·bo·le·nie",
        "nalakované": "na·la·ko·va·né",
        "oblakových": "ob·la·ko·vých",
        "tlakový": "tla·ko·vý",
        "nevkusnejší": "ne·vkus·nej·ší",
        "najnevkusnejších": "naj·ne·vkus·nej·ších",
        "najvkusnejšie": "naj·vkus·nej·šie",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_second_discovered_family_batch_keeps_only_clear_psp_seams():
    expected = {
        "nezhasne": "ne·zhas·ne",
        "pozhasínal": "po·zha·sí·nal",
        "rozhasilo": "roz·ha·si·lo",
        "záchvat": "zá·chvat",
        "záchvatovito": "zá·chva·to·vi·to",
        "úchvatný": "úch·vat·ný",
        "uchvatiteľovi": "uch·va·ti·te·ľo·vi",
        "nespáchal": "ne·spá·chal",
        "spolupáchateľov": "spo·lu·pá·cha·te·ľov",
        "hostíš": "hos·tíš",
        "postíš": "pos·tíš",
        "nezniesol": "ne·znie·sol",
        "rozniesol": "roz·nie·sol",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_third_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "ohnivovlasý": "oh·ni·vo·vla·sý",
        "plavovlasého": "pla·vo·vla·sé·ho",
        "tmavovlasá": "tma·vo·vla·sá",
        "žltovlasého": "žl·to·vla·sé·ho",
        "kriedovobiele": "krie·do·vo·bie·le",
        "mliečnobielou": "mlieč·no·bie·lou",
        "snehobiely": "sne·ho·bie·ly",
        "striebristobielymi": "strieb·ris·to·bie·ly·mi",
        "ustricovobiela": "us·tri·co·vo·bie·la",
        "pranajstaršieho": "pra·naj·star·šie·ho",
        "patrón": "pat·rón",
        "rozmar": "roz·mar",
        "obielený": "obie·le·ný",
        "stebielko": "ste·biel·ko",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_fourth_discovered_family_batch_has_no_safe_new_seam():
    expected = {
        "ukolísať": "uko·lí·sať",
        "ukolísaný": "uko·lí·sa·ný",
        "oprasiť": "opra·siť",
        "sprasiť": "spra·siť",
        "barokovo": "ba·ro·ko·vo",
        "brokovnica": "bro·kov·ni·ca",
        "krokový": "kro·ko·vý",
        "nárokovanie": "ná·ro·ko·va·nie",
        "otrokovi": "ot·ro·ko·vi",
        "úrokového": "úro·ko·vé·ho",
        "opakujeme": "opa·ku·je·me",
        "neopakuj": "ne·opa·kuj",
        "zopakuje": "zo·pa·ku·je",
        "ukameňovať": "uka·me·ňo·vať",
        "neukameňovaná": "ne·uka·me·ňo·va·ná",
        "prakameňmi": "pra·ka·meň·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_fifth_discovered_family_batch_keeps_only_zvero_kruh_seam():
    expected = {
        "neraduj": "ne·ra·duj",
        "zaraduje": "za·ra·du·je",
        "úraduje": "úra·du·je",
        "traduje": "tra·du·je",
        "dotvorenie": "do·tvo·re·nie",
        "utvorenie": "utvo·re·nie",
        "stvorenie": "stvo·re·nie",
        "znovuotvorenie": "zno·vu·ot·vo·re·nie",
        "zverokruh": "zve·ro·kruh",
        "zverokruhom": "zve·ro·kru·hom",
        "zverokruhu": "zve·ro·kru·hu",
        "okruh": "ok·ruh",
        "polkruh": "pol·kruh",
        "ustrážiť": "ustrá·žiť",
        "postrážil": "po·strá·žil",
        "nestráži": "ne·strá·ži",
        "oľutuje": "oľu·tu·je",
        "zľutuje": "zľu·tu·je",
        "neľutuj": "ne·ľu·tuj",
        "poľutujú": "po·ľu·tu·jú",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_sixth_discovered_family_batch_has_no_safe_new_seam():
    expected = {
        "prechmat": "pre·chmat",
        "vychmatol": "vy·chma·tol",
        "schmatnúť": "schmat·núť",
        "uchmatnúť": "uch·mat·núť",
        "nemalá": "ne·ma·lá",
        "himalájske": "hi·ma·láj·ske",
        "zmalátniem": "zma·lát·niem",
        "nešteká": "ne·šte·ká",
        "poštekliť": "po·štek·liť",
        "noštek": "noš·tek",
        "ibišteka": "ibiš·te·ka",
        "oprášiť": "oprá·šiť",
        "poprášiť": "po·prá·šiť",
        "rozprášenie": "roz·prá·še·nie",
        "nesníma": "ne·sní·ma",
        "zosnímal": "zo·sní·mal",
        "objasním": "ob·jas·ním",
        "ujasním": "ujas·ním",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_seventh_discovered_family_batch_keeps_only_na_za_skok_seams():
    expected = {
        "náskok": "ná·skok",
        "náskokom": "ná·sko·kom",
        "záskok": "zá·skok",
        "úskok": "ús·kok",
        "odskoku": "od·sko·ku",
        "rímskokatolícky": "rím·sko·ka·to·líc·ky",
        "zákrok": "zák·rok",
        "makrokozmos": "mak·ro·koz·mos",
        "vodostehoch": "vo·do·ste·hoch",
        "dvanásteho": "dva·nás·te·ho",
        "vyhlasuje": "vy·hla·su·je",
        "ohlasuje": "oh·la·su·je",
        "neohlasuj": "ne·ohla·suj",
        "slovosled": "slo·vo·sled",
        "oslovovať": "oslo·vo·vať",
        "zmyslovo": "zmys·lo·vo",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_eighth_discovered_family_batch_has_no_safe_new_seam():
    expected = {
        "splatiteľné": "spla·ti·teľ·né",
        "nesplatiteľnú": "ne·spla·ti·teľ·nú",
        "urazia": "ura·zia",
        "vrazia": "vra·zia",
        "zrazia": "zra·zia",
        "neobýval": "ne·obý·val",
        "obývali": "obý·va·li",
        "pohladenie": "po·hla·de·nie",
        "kladenie": "kla·de·nie",
        "ochladenie": "och·la·de·nie",
        "zvráskavená": "zvrás·ka·ve·ná",
        "zvrásňovalo": "zvrás·ňo·va·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_sixty_ninth_discovered_family_batch_keeps_only_kral_compound_seams():
    expected = {
        "miestokráľ": "mies·to·kráľ",
        "miestokráľa": "mies·to·krá·ľa",
        "miestokráľom": "mies·to·krá·ľom",
        "miestokráľovi": "mies·to·krá·ľo·vi",
        "spolukráľ": "spo·lu·kráľ",
        "tisíckráľom": "ti·síc·krá·ľom",
        "veľkokráľom": "veľ·ko·krá·ľom",
        "veľkokráľovná": "veľ·ko·krá·ľov·ná",
        "vicekráľom": "vi·ce·krá·ľom",
        "oškrabaná": "oš·kra·ba·ná",
        "okopaniny": "oko·pa·ni·ny",
        "skopať": "sko·pať",
        "vkopaný": "vko·pa·ný",
        "rozbor": "roz·bor",
        "ôsmej": "ôs·mej",
        "usmeje": "us·me·je",
        "pousmeje": "po·us·me·je",
        "rozosmeje": "ro·zo·sme·je",
        "nerozosmeje": "ne·ro·zo·sme·je",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventieth_discovered_family_batch_keeps_only_rozo_zvon_seam():
    expected = {
        "rozozvonil": "ro·zo·zvo·nil",
        "rozvoniavať": "roz·vo·nia·vať",
        "bezstromovú": "bez·stro·mo·vú",
        "mnohostrom": "mno·ho·strom",
        "majstrom": "maj·strom",
        "ministrom": "mi·nis·trom",
        "orchestrom": "or·ches·trom",
        "svetlozlato": "svet·lo·zla·to",
        "trávovozlatozelená": "trá·vo·vo·zla·to·ze·le·ná",
        "kladkostrojov": "klad·ko·stro·jov",
        "nástrojovej": "nás·tro·jo·vej",
        "prístrojov": "prís·tro·jov",
        "ústrojov": "ús·tro·jov",
        "zazvonil": "za·zvo·nil",
        "ropucha": "ro·pu·cha",
        "opuchlina": "opuch·li·na",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_first_discovered_family_batch_keeps_only_three_compound_families():
    expected = {
        "spolukňazi": "spo·lu·kňa·zi",
        "spolukňazom": "spo·lu·kňa·zom",
        "novozjaveného": "no·vo·zja·ve·né·ho",
        "novozjavujúcou": "no·vo·zja·vu·jú·cou",
        "polozvieracej": "po·lo·zvie·ra·cej",
        "polozvieracích": "po·lo·zvie·ra·cích",
        "polozvieratý": "po·lo·zvie·ra·tý",
        "človekozvieraťom": "člo·ve·ko·zvie·ra·ťom",
        "okrikoval": "ok·ri·ko·val",
        "bezviera": "bez·vie·ra",
        "predzvieratami": "pred·zvie·ra·ta·mi",
        "nadkráľovskej": "nad·krá·ľov·skej",
        "prakráľovná": "pra·krá·ľov·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_second_discovered_family_batch_keeps_only_two_compound_families():
    expected = {
        "ohňožrúti": "oh·ňo·žrú·ti",
        "písmenožrútstvo": "pís·me·no·žrút·stvo",
        "všežrúta": "vše·žrú·ta",
        "samostvoriteľkou": "sa·mo·stvo·ri·teľ·kou",
        "samostvoriteľom": "sa·mo·stvo·ri·te·ľom",
        "rotmajstrovi": "rot·maj·stro·vi",
        "rybmajstrovi": "ryb·maj·stro·vi",
        "stolmajstrov": "stol·maj·strov",
        "zmajstrovať": "zmaj·stro·vať",
        "opálenie": "opá·le·nie",
        "spálenie": "spá·le·nie",
        "upálenie": "upá·le·nie",
        "rozráža": "roz·rá·ža",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_third_discovered_family_batch_keeps_only_vysoko_skol_seam():
    expected = {
        "vysokoškolské": "vy·so·ko·škol·ské",
        "vysokoškoláci": "vy·so·ko·ško·lá·ci",
        "stredoškolskú": "stre·do·škol·skú",
        "vyškolenie": "vy·ško·le·nie",
        "ušliapali": "uš·lia·pa·li",
        "zmnožuje": "zmno·žu·je",
        "správou": "sprá·vou",
        "životosprávou": "ži·vo·to·sprá·vou",
        "druhoradej": "dru·ho·ra·dej",
        "mnohorakosť": "mno·ho·ra·kosť",
        "hrachora": "hra·cho·ra",
        "zhora": "zho·ra",
        "úhora": "úho·ra",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_fourth_discovered_family_batch_has_no_safe_new_seam():
    expected = {
        "spoluradca": "spo·lu·rad·ca",
        "poradca": "po·rad·ca",
        "veľradca": "veľ·rad·ca",
        "velezradca": "ve·le·zrad·ca",
        "vlastizradca": "vlas·ti·zrad·ca",
        "zradca": "zrad·ca",
        "spolužitie": "spo·lu·ži·tie",
        "nežitie": "ne·ži·tie",
        "použitie": "po·uži·tie",
        "využitie": "vy·uži·tie",
        "zneužitie": "zne·uži·tie",
        "bohoslovec": "bo·ho·slo·vec",
        "bohosloveckou": "bo·ho·slo·vec·kou",
        "uspôsobil": "uspô·so·bil",
        "neuspôsobil": "ne·uspô·so·bil",
        "prispôsobil": "pri·spô·so·bil",
        "nezdrapíte": "ne·zdra·pí·te",
        "rozdrapiť": "roz·dra·piť",
        "nerozdrapilo": "ne·roz·dra·pi·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_fifth_discovered_family_batch_keeps_only_spolu_stolov_seam():
    expected = {
        "spolustolovníkom": "spo·lu·sto·lov·ní·kom",
        "spolustolovníkov": "spo·lu·sto·lov·ní·kov",
        "kostolov": "kos·to·lov",
        "zdrevenel": "zdre·ve·nel",
        "zdrevnatejú": "zdrev·na·te·jú",
        "arciesejca": "ar·ci·esej·ca",
        "neseje": "ne·se·je",
        "porozumenie": "po·ro·zu·me·nie",
        "šumenie": "šu·me·nie",
        "zvlečením": "zvle·če·ním",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_sixth_discovered_family_batch_keeps_only_clear_prefix_seams():
    expected = {
        "prieklep": "prie·klep",
        "prieklepové": "prie·kle·po·vé",
        "neodumiera": "ne·od·umie·ra",
        "neodumierajú": "ne·od·umie·ra·jú",
        "neodcestoval": "ne·od·ces·to·val",
        "scestovaný": "sces·to·va·ný",
        "sprieči": "sprie·či",
        "vzprieči": "vzprie·či",
        "ohanbia": "ohan·bia",
        "ohanbie": "ohan·bie",
        "preklepnúť": "pre·klep·núť",
        "odumierať": "od·umie·rať",
        "neumiera": "ne·umie·ra",
        "zmierať": "zmie·rať",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_seventh_discovered_family_batch_keeps_only_pre_dobr_seam():
    expected = {
        "predobré": "pre·dob·ré",
        "predobrého": "pre·dob·ré·ho",
        "predobrému": "pre·dob·ré·mu",
        "predobrý": "pre·dob·rý",
        "predobrým": "pre·dob·rým",
        "predobrať": "pred·ob·rať",
        "preddobrého": "pred·dob·ré·ho",
        "všedobré": "vše·dob·ré",
        "scivilizovaný": "sci·vi·li·zo·va·ný",
        "krovinatých": "kro·vi·na·tých",
        "uvedenie": "uve·de·nie",
        "zvedenie": "zve·de·nie",
        "zamračenie": "za·mra·če·nie",
        "omračujúce": "om·ra·ču·jú·ce",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_eighth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "mimopriestorové": "mi·mo·pries·to·ro·vé",
        "mimopriestorový": "mi·mo·pries·to·ro·vý",
        "časopriestorový": "ča·so·pries·to·ro·vý",
        "sedmospáč": "sed·mo·spáč",
        "sedmospáči": "sed·mo·spá·či",
        "sedmospáčov": "sed·mo·spá·čov",
        "nedosušeného": "ne·do·su·še·né·ho",
        "zosušilo": "zo·su·ši·lo",
        "ektoplazma": "ek·top·laz·ma",
        "vplaziť": "vpla·ziť",
        "ohrýzať": "oh·rý·zať",
        "priesmyk": "pries·myk",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_seventy_ninth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "spoluzľutovaniu": "spo·lu·zľu·to·va·niu",
        "všezľutovnej": "vše·zľu·tov·nej",
        "zrušenie": "zru·še·nie",
        "vzrušenie": "vzru·še·nie",
        "znervóznel": "zner·vóz·nel",
        "zmena": "zme·na",
        "zámena": "zá·me·na",
        "bremena": "bre·me·na",
        "písmenami": "pís·me·na·mi",
        "znamenajú": "zna·me·na·jú",
        "zdemoralizovaní": "zde·mo·ra·li·zo·va·ní",
        "sedemoktávový": "se·dem·ok·tá·vo·vý",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_eightieth_discovered_family_batch_keeps_only_clear_compound_seams():
    expected = {
        "telocvik": "te·lo·cvik",
        "telocvikom": "te·lo·cvi·kom",
        "novoprijatou": "no·vo·pri·ja·tou",
        "novoprijatí": "no·vo·pri·ja·tí",
        "nácvik": "ná·cvik",
        "výcviku": "vý·cvi·ku",
        "udržanie": "udr·ža·nie",
        "zdržanie": "zdr·ža·nie",
        "tryskáča": "trys·ká·ča",
        "tryskáčov": "trys·ká·čov",
        "poslaná": "pos·la·ná",
        "neposlaná": "ne·pos·la·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_eighty_first_discovered_family_batch_needs_no_new_runtime_seam():
    expected = {
        "dôveryhodnosť": "dô·ve·ry·hod·nosť",
        "pozoruhodnosť": "po·zo·ru·hod·nosť",
        "vhodnosť": "vhod·nosť",
        "nevhodnosť": "ne·vhod·nosť",
        "neporušil": "ne·po·ru·šil",
        "oporu": "opo·ru",
        "sporu": "spo·ru",
        "generálporučík": "ge·ne·rál·po·ru·čík",
        "samočinnosťou": "sa·mo·čin·nos·ťou",
        "zločinnosť": "zlo·čin·nosť",
        "účinnosť": "účin·nosť",
        "doplnenie": "do·pl·ne·nie",
        "nesplnenie": "ne·spl·ne·nie",
        "splnenie": "spl·ne·nie",
        "protispise": "pro·ti·spi·se",
        "jaspisom": "jas·pi·som",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_eighty_second_discovered_family_batch_keeps_only_velko_spekulant_seam():
    expected = {
        "veľkošpekulanta": "veľ·ko·špe·ku·lan·ta",
        "veľkošpekulantovi": "veľ·ko·špe·ku·lan·to·vi",
        "uváženie": "uvá·že·nie",
        "zváženie": "zvá·že·nie",
        "škola": "ško·la",
        "školami": "ško·la·mi",
        "rukolapný": "ru·ko·lap·ný",
        "pozvoľnom": "po·zvoľ·nom",
        "svojvoľnom": "svoj·voľ·nom",
        "odovzdanosť": "odo·vzda·nosť",
        "usporiadanosť": "uspo·ria·da·nosť",
        "veľkolepý": "veľ·ko·le·pý",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_eighty_third_discovered_family_batch_keeps_only_safe_nested_seams():
    expected = {
        "neodohráva": "ne·odo·hrá·va",
        "neodohrávajú": "ne·odo·hrá·va·jú",
        "svetaskúsení": "sve·ta·skú·se·ní",
        "svetaskúsený": "sve·ta·skú·se·ný",
        "oboplávanie": "obo·plá·va·nie",
        "vplávanie": "vplá·va·nie",
        "vprúdi": "vprú·di",
        "vprúdiť": "vprú·diť",
        "ostrapkaná": "os·trap·ka·ná",
        "ostrapkanými": "os·trap·ka·ný·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_eighty_fourth_discovered_family_batch_keeps_only_real_existing_seams():
    expected = {
        "učenie": "uče·nie",
        "poučenie": "po·uče·nie",
        "ponaučenie": "po·na·uče·nie",
        "mučenie": "mu·če·nie",
        "zaručenie": "za·ru·če·nie",
        "zdravie": "zdra·vie",
        "vyzdravie": "vy·zdra·vie",
        "vyzdraviete": "vy·zdra·vie·te",
        "vyzdravieť": "vy·zdra·vieť",
        "nevyzdravie": "ne·vy·zdra·vie",
        "ozdravie": "oz·dra·vie",
        "ozdravieť": "oz·dra·vieť",
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


def test_batch_72_guarded_po_and_nested_prefix_families():
    expected = {
        "podať": "po·dať",
        "podajú": "po·da·jú",
        "nepodala": "ne·po·da·la",
        "podarený": "po·da·re·ný",
        "nepodarok": "ne·po·da·rok",
        "podeliť": "po·de·liť",
        "podeje": "po·de·je",
        "podela": "po·de·la",
        "podenka": "po·den·ka",
        "podeniek": "po·de·niek",
        "podesta": "po·des·ta",
        "podošva": "po·doš·va",
        "podieť": "po·dieť",
        "podierkovaný": "po·dier·ko·va·ný",
        "podívaná": "po·dí·va·ná",
        "podojiť": "po·do·jiť",
        "podomácky": "po·do·mác·ky",
        "podomový": "po·do·mo·vý",
        "podlý": "pod·lý",
        "podlo": "pod·lo",
        "podotknem": "po·dotk·nem",
        "podotkol": "po·dot·kol",
        "podotýka": "po·do·tý·ka",
        "nepodieľali": "ne·po·die·ľa·li",
        "nepodujme": "ne·pod·uj·me",
        "nepohla": "ne·po·hla",
        "nepohli": "ne·po·hli",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nepodopiera") == "ne·pod·opie·ra"
    assert hyphenate("podrobiť") == "po·dro·biť"


def test_batch_129_keeps_the_po_hreb_seam():
    expected = {
        "pohreb": "po·hreb",
        "pohrebe": "po·hre·be",
        "pohrebiská": "po·hre·bis·ká",
        "pohrebník": "po·hreb·ník",
        "pohrebnými": "po·hreb·ný·mi",
        "pohrebníctvo": "po·hreb·níc·tvo",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_130_keeps_pol_quantity_and_polo_compound_seams():
    expected = {
        "pollibra": "pol·lib·ra",
        "polliter": "pol·li·ter",
        "pollitrovka": "pol·lit·rov·ka",
        "poloblázna": "po·lo·bláz·na",
        "poločlovek": "po·lo·člo·vek",
        "polofrancúzskych": "po·lo·fran·cúz·skych",
        "polohmotným": "po·lo·hmot·ným",
        "poloplášť": "po·lo·plášť",
        "poloplešatú": "po·lo·ple·ša·tú",
        "poloprázdna": "po·lo·práz·dna",
        "polopriznania": "po·lo·pri·zna·nia",
        "poloprorok": "po·lo·pro·rok",
        "poloslová": "po·lo·slo·vá",
        "polosmrteľné": "po·lo·smr·teľ·né",
        "polospánku": "po·lo·spán·ku",
        "polospoločenskom": "po·lo·spo·lo·čen·skom",
        "pološtrbinami": "po·lo·štr·bi·na·mi",
        "polotmavé": "po·lo·tma·vé",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("polostrov") == "pol·os·trov"


def test_batch_131_keeps_pol_polo_and_pomsty_compound_seams():
    expected = {
        "polotme": "po·lo·tme",
        "polozdivočených": "po·lo·zdi·vo·če·ných",
        "polozhnitá": "po·lo·zhni·tá",
        "polozrenie": "po·lo·zre·nie",
        "polročné": "pol·roč·né",
        "polrok": "pol·rok",
        "polrúra": "pol·rú·ra",
        "pomste": "pom·ste",
        "pomstychtivá": "pom·sty·chti·vá",
        "pomstychtivosť": "pom·sty·chti·vosť",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("polostrov") == "pol·os·trov"
    assert hyphenate("robte") == "rob·te"


def test_batch_132_keeps_nested_po_prefixes_and_the_lexical_poplach_stem():
    expected = {
        "poodišiel": "po·od·išiel",
        "poodišli": "po·od·iš·li",
        "poodtiahnuté": "po·od·tiah·nu·té",
        "poodvihne": "po·od·vih·ne",
        "poohmatával": "po·ohma·tá·val",
        "pootáčal": "po·otá·čal",
        "pootočení": "po·oto·če·ní",
        "poplach": "pop·lach",
        "poplachu": "pop·la·chu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("poplakať") == "po·pla·kať"
    assert hyphenate("poplašiť") == "po·pla·šiť"
    assert hyphenate("ohmatať") == "oh·ma·tať"
    assert hyphenate("zaobísť") == "za·ob·ísť"


def test_batch_133_keeps_the_lexical_popruh_stem():
    expected = {
        "popruh": "pop·ruh",
        "popruhmi": "pop·ruh·mi",
        "popruhoch": "pop·ru·hoch",
        "popruhu": "pop·ru·hu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("poprosiť") == "po·pro·siť"
    assert hyphenate("poprieť") == "po·prieť"


def test_batch_135_keeps_post_compound_and_postel_family_boundaries():
    expected = {
        "postgraduálny": "post·gra·du·ál·ny",
        "postgraduálne": "post·gra·du·ál·ne",
        "posteľ": "pos·teľ",
        "postele": "pos·te·le",
        "postieľkach": "pos·tieľ·kach",
        "postieľok": "pos·tie·ľok",
        "pošta": "poš·ta",
        "poštový": "poš·to·vý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("postihnúť") == "po·stih·núť"
    assert hyphenate("postiť") == "pos·tiť"
    assert hyphenate("poštípal") == "po·ští·pal"


def test_batch_127_distinguishes_po_drazd_drep_driemk_from_pod_raz():
    expected = {
        "podráždená": "po·dráž·de·ná",
        "podráždiť": "po·dráž·diť",
        "podrepe": "po·dre·pe",
        "podriemkavali": "po·driem·ka·va·li",
        "podrážajú": "pod·rá·ža·jú",
        "podrážka": "pod·ráž·ka",
        "podrástlo": "pod·rást·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_73_guarded_po_prefix_and_lexical_stem_families():
    expected = {
        "nepohne": "ne·po·hne",
        "nepohnú": "ne·po·hnú",
        "nepoklonila": "ne·po·klo·ni·la",
        "praskajúce": "pras·ka·jú·ce",
        "nepopraskajú": "ne·po·pras·ka·jú",
        "rozumieť": "ro·zu·mieť",
        "neporozumie": "ne·po·ro·zu·mie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("praktický") == "prak·tic·ký"
    assert hyphenate("praarchív") == "pra·ar·chív"
    assert hyphenate("nepodopiera") == "ne·pod·opie·ra"


def test_batch_79_nested_pri_klon_keeps_both_prefix_seams():
    assert hyphenate("nepriklonila") == "ne·pri·klo·ni·la"


def test_batch_80_keeps_nested_roz_oh_rozo_zrat_and_sknut_seams():
    assert hyphenate("nerozohnil") == "ne·roz·oh·nil"
    assert hyphenate("nerozožerú") == "ne·ro·zo·že·rú"
    assert hyphenate("nerisknem") == "ne·risk·nem"
    assert hyphenate("nerozlúsknem") == "ne·roz·lúsk·nem"
    assert hyphenate("magnete") == "mag·ne·te"


def test_batch_81_keeps_ne_before_s_prefixed_stems():
    assert hyphenate("nesčervenieš") == "ne·sčer·ve·nieš"
    assert hyphenate("nesčervivela") == "ne·sčer·vi·ve·la"
    assert hyphenate("nescudzoložíš") == "ne·scu·dzo·lo·žíš"
    assert hyphenate("nescio") == "nes·cio"


def test_batch_82_keeps_negative_nested_seams_and_padlo_past_forms():
    expected = {
        "nespadlo": "ne·spad·lo",
        "nedopadlo": "ne·do·pad·lo",
        "nespoluprežíva": "ne·spo·lu·pre·ží·va",
        "nesťahuje": "ne·sťa·hu·je",
        "neuchránia": "ne·uchrá·nia",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("klopadlo") == "klo·pa·dlo"
    assert hyphenate("kúpadlo") == "kú·pa·dlo"
    assert hyphenate("stúpadlo") == "stú·pa·dlo"


def test_batch_83_keeps_nested_u_prefixes_and_d_final_past_forms():
    expected = {
        "neuchváti": "ne·uchvá·ti",
        "neudržateľnosti": "ne·udr·ža·teľ·nos·ti",
        "neuhladenou": "ne·uhla·de·nou",
        "Neuhryzne": "Ne·uhryz·ne",
        "neuhryznem": "ne·uhryz·nem",
        "neukradlo": "ne·ukrad·lo",
        "neumlčali": "ne·uml·ča·li",
        "neumĺkol": "ne·umĺ·kol",
        "neumŕtvil": "ne·umŕt·vil",
        "neupadlo": "ne·upad·lo",
        "neuplatňuje": "ne·uplat·ňu·je",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    protected = {
        "neutrál": "ne·ut·rál",
        "zrkadlo": "zr·ka·dlo",
        "čerpadlo": "čer·pa·dlo",
        "lietadlo": "lie·ta·dlo",
        "poslucháč": "pos·lu·cháč",
        "neuposlúchnuté": "ne·upos·lúch·nu·té",
    }
    assert {word: hyphenate(word) for word in protected} == protected


def test_batch_84_keeps_the_nested_u_sporad_allomorph_seam():
    assert hyphenate("Neusporadúvala") == "Ne·uspo·ra·dú·va·la"
    assert hyphenate("neusporadúvali") == "ne·uspo·ra·dú·va·li"
    assert hyphenate("usporadúvala") == "us·po·ra·dú·va·la"


def test_batch_85_keeps_guarded_negative_and_nested_u_seams():
    expected = {
        "neutrpel": "ne·utr·pel",
        "neutŕžili": "ne·utŕ·ži·li",
        "neutvrdili": "ne·utvr·di·li",
        "neuvrhlo": "ne·uvrh·lo",
        "neuzdravujem": "ne·uzdra·vu·jem",
        "neuznám": "ne·uznám",
        "nevčasnými": "ne·včas·ný·mi",
        "nevchádzajte": "ne·vchá·dzaj·te",
        "nevčleňovali": "ne·včle·ňo·va·li",
        "nevďakom": "ne·vďa·kom",
        "nevdýchnete": "ne·vdých·ne·te",
        "nevdychuje": "ne·vdy·chu·je",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("usvedčiť") == "us·ved·čiť"
    assert hyphenate("uzdravený") == "uzdra·ve·ný"


def test_batch_86_keeps_guarded_negative_v_stem_seams():
    expected = {
        "nevkladá": "ne·vkla·dá",
        "nevkradlo": "ne·vkrad·lo",
        "nevkročíte": "ne·vkro·čí·te",
        "nevľúdnymi": "ne·vľúd·ny·mi",
        "nevmiešal": "ne·vmie·šal",
        "nevpadnem": "ne·vpad·nem",
        "nevpálili": "ne·vpá·li·li",
        "nevpili": "ne·vpi·li",
        "nevpláva": "ne·vplá·va",
        "nevplývajú": "ne·vplý·va·jú",
        "nevpúšťajú": "ne·vpúš·ťa·jú",
        "nevpustíte": "ne·vpus·tí·te",
        "nevsádzate": "ne·vsá·dza·te",
        "nevšednému": "ne·všed·né·mu",
        "nevšímavosti": "ne·vší·ma·vos·ti",
        "nevšimnúť": "ne·všim·núť",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neviestkami") == "ne·viest·ka·mi"
    assert hyphenate("nevohnali") == "ne·vo·hna·li"
    assert hyphenate("nevrhla") == "ne·vrh·la"
    assert hyphenate("nevstanem") == "ne·vsta·nem"


def test_batch_87_keeps_guarded_negative_and_nested_vy_seams():
    expected = {
        "nevštepil": "ne·všte·pil",
        "nevštepíte": "ne·všte·pí·te",
        "nevťahuj": "ne·vťa·huj",
        "nevyhne": "ne·vy·hne",
        "nevykla": "ne·vy·kla",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nevyhnutný") == "ne·vyh·nut·ný"
    assert hyphenate("nevykladaj") == "ne·vy·kla·daj"


def test_batch_88_keeps_the_nested_vy_schnut_seam():
    expected = {
        "nevyschli": "ne·vy·schli",
        "nevyschlo": "ne·vy·schlo",
        "nevyschne": "ne·vy·schne",
        "nevyschnú": "ne·vy·schnú",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("vyschli") == "vy·schli"


def test_batch_90_keeps_the_nested_vy_zniest_seam():
    assert hyphenate("nevyznejú") == "ne·vy·zne·jú"
    assert hyphenate("nevyznieva") == "ne·vy·znie·va"


def test_batch_91_keeps_guarded_nested_za_allomorph_seams():
    expected = {
        "nezačne": "ne·za·čne",
        "nezačnú": "ne·za·čnú",
        "nezahla": "ne·za·hla",
        "nezahná": "ne·za·hná",
        "nezahnila": "ne·za·hni·la",
        "nezamkla": "ne·za·mkla",
        "nezamknuté": "ne·za·mknu·té",
        "nezamknutými": "ne·za·mknu·tý·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nezáklad") == "ne·zá·klad"


def test_batch_92_keeps_guarded_nested_za_seams():
    expected = {
        "nezaobíde": "ne·za·ob·íde",
        "nezaobišla": "ne·za·ob·iš·la",
        "nezaobišlo": "ne·za·ob·iš·lo",
        "nezapodieva": "ne·za·po·die·va",
        "nezapodievajte": "ne·za·po·die·vaj·te",
        "nezapodieval": "ne·za·po·die·val",
        "Nezapodievali": "Ne·za·po·die·va·li",
        "nezatkne": "ne·za·tkne",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nezaoberám") == "ne·za·obe·rám"
    assert hyphenate("nezaopatrí") == "ne·za·opat·rí"


def test_batch_93_keeps_the_nested_za_zat_seam_and_the_lexical_nezbed_stem():
    assert hyphenate("nezažne") == "ne·za·žne"
    assert hyphenate("nezažnú") == "ne·za·žnú"
    expected = {
        "nezbed": "nez·bed",
        "nezbedná": "nez·bed·ná",
        "nezbedník": "nez·bed·ník",
        "nezbednosť": "nez·bed·nosť",
        "nezbednosti": "nez·bed·nos·ti",
        "nezbednými": "nez·bed·ný·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_94_keeps_negative_ne_before_nonsyllabic_z_and_past_zjedlo():
    expected = {
        "nezhltli": "ne·zhlt·li",
        "nezhrabli": "ne·zhrab·li",
        "nezhrdzavel": "ne·zhr·dza·vel",
        "nezhreš": "ne·zhreš",
        "nezhrnula": "ne·zhr·nu·la",
        "nezhromažďuje": "ne·zhro·maž·ďu·je",
        "nezhrozte": "ne·zhroz·te",
        "nezhustla": "ne·zhust·la",
        "nezjedlo": "ne·zjed·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("jedlo") == "jed·lo"
    assert hyphenate("neziđu") == "neziđu"


def test_batch_95_keeps_the_lexical_nezn_stem():
    expected = {
        "nežná": "než·ná",
        "nežného": "než·né·ho",
        "nežnej": "než·nej",
        "nežnosť": "než·nosť",
        "nežnosťami": "než·nos·ťa·mi",
        "nežnosti": "než·nos·ti",
        "nežnosťou": "než·nos·ťou",
        "nežnou": "než·nou",
        "nežný": "než·ný",
        "nežnými": "než·ný·mi",
        "nezobrazuje": "ne·zob·ra·zu·je",
        "nezohľadňoval": "ne·zoh·ľad·ňo·val",
        "nezohneš": "ne·zoh·neš",
        "nezostal": "ne·zos·tal",
        "nezostáva": "ne·zos·tá·va",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nezobral") == "ne·zo·bral"
    assert hyphenate("nezohnali") == "ne·zo·hna·li"
    assert hyphenate("nezohrieva") == "ne·zo·hrie·va"
    assert hyphenate("nezostarne") == "ne·zo·star·ne"


def test_batch_96_keeps_only_documented_prefix_and_compound_seams():
    expected = {
        "nezotročení": "ne·zot·ro·če·ní",
        "nezožne": "ne·zo·žne",
        "nezožnú": "ne·zo·žnú",
        "niekoľkodňové": "nie·koľ·ko·dňo·vé",
        "niekoľkoposchodovom": "nie·koľ·ko·pos·cho·do·vom",
        "niekde": "nie·kde",
        "niekto": "nie·kto",
        "nikde": "ni·kde",
        "nikdy": "ni·kdy",
        "nikto": "ni·kto",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("niekdajší") == "niek·daj·ší"
    assert hyphenate("niklák") == "nik·lák"
    assert hyphenate("nezostrojí") == "ne·zo·stro·jí"


def test_batch_97_keeps_documented_foreign_and_morpheme_seams():
    expected = {
        "nonplusultra": "non·plus·ul·tra",
        "Northrup": "North·rup",
        "Northrupa": "North·ru·pa",
        "Novocainom": "No·vo·cai·nom",
        "novopovstalého": "no·vo·po·vsta·lé·ho",
        "novopovstanie": "no·vo·po·vsta·nie",
        "novostvoreného": "no·vo·stvo·re·né·ho",
        "novovzbudený": "no·vo·vzbu·de·ný",
        "novozdolanom": "no·vo·zdo·la·nom",
        "novozhotovenej": "no·vo·zho·to·ve·nej",
        "novozrodený": "no·vo·zro·de·ný",
        "novozvolený": "no·vo·zvo·le·ný",
        "Obadiáša": "Oba·di·á·ša",
        "obaja": "oba·ja",
        "obalamutiť": "oba·la·mu·tiť",
        "obale": "oba·le",
        "obalená": "oba·le·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obava") == "oba·va"
    assert hyphenate("obrúsil") == "ob·rú·sil"
    assert hyphenate("naivný") == "na·iv·ný"


def test_batch_98_blocks_false_ob_prefixes_in_documented_lexical_families():
    expected = {
        "obálka": "obál·ka",
        "obálkami": "obál·ka·mi",
        "obálok": "obá·lok",
        "obaľuje": "oba·ľu·je",
        "obaľujú": "oba·ľu·jú",
        "obecenstvo": "obe·cen·stvo",
        "obecenstvu": "obe·cen·stvu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obarených") == "ob·are·ných"
    assert hyphenate("občerstvenie") == "ob·čer·stve·nie"


def test_batch_99_blocks_false_ob_prefixes_across_obe_families():
    expected = {
        "obecný": "obec·ný",
        "obecných": "obec·ných",
        "obeda": "obe·da",
        "obedienciu": "obe·dien·ciu",
        "obedňajšiu": "obed·ňaj·šiu",
        "obedoval": "obe·do·val",
        "obehne": "obeh·ne",
        "obehnutí": "obeh·nu·tí",
        "obelhávať": "obel·há·vať",
        "obeliskových": "obe·lis·ko·vých",
        "obelstiť": "obel·stiť",
        "oberačku": "obe·rač·ku",
        "oberačky": "obe·rač·ky",
        "oberajúcej": "obe·ra·jú·cej",
        "oberie": "obe·rie",
        "oberte": "ober·te",
        "obeseného": "obe·se·né·ho",
        "obesiť": "obe·siť",
        "obešli": "obeš·li",
        "obetavosťou": "obe·ta·vos·ťou",
        "Obetavý": "Obe·ta·vý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("občerstvenie") == "ob·čer·stve·nie"
    assert hyphenate("oboznámiť") == "ob·oz·ná·miť"


def test_batch_100_blocks_false_ob_prefixes_and_keeps_true_ones():
    expected = {
        "obeživo": "obe·ži·vo",
        "obežnica": "obež·ni·ca",
        "obézneho": "obéz·ne·ho",
        "obidvoch": "obid·voch",
        "obiehajú": "obie·ha·jú",
        "obiehanie": "obie·ha·nie",
        "obieľať": "obie·ľať",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obhrýzať") == "ob·hrý·zať"
    assert hyphenate("obídeme") == "ob·íde·me"


def test_batch_101_blocks_false_ob_prefixes_and_keeps_true_ones():
    expected = {
        "obielené": "obie·le·né",
        "obiet": "obiet",
        "obilie": "obi·lie",
        "obitá": "obi·tá",
        "oboch": "oboch",
        "obočie": "obo·čie",
        "obohacovať": "obo·ha·co·vať",
        "obohatiť": "obo·ha·tiť",
        "Obohaťte": "Obo·hať·te",
        "obohnať": "obo·hnať",
        "obohnaného": "obo·hna·né·ho",
        "obojaký": "obo·ja·ký",
        "obojka": "oboj·ka",
        "obojpohlavná": "oboj·poh·lav·ná",
        "obojstranná": "oboj·stran·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obišiel") == "ob·išiel"
    assert hyphenate("obľahnúť") == "ob·ľah·núť"
    assert hyphenate("obohratá") == "ob·ohra·tá"


def test_batch_102_handles_vocalized_obo_and_lexical_ob_lookalikes():
    expected = {
        "obolov": "obo·lov",
        "obolus": "obo·lus",
        "obom": "obom",
        "oboma": "obo·ma",
        "obopínať": "obo·pí·nať",
        "obopla": "obo·pla",
        "oboplávanie": "obo·plá·va·nie",
        "obopnúť": "obo·pnúť",
        "obopol": "obo·pol",
        "obore": "obo·re",
        "oboriť": "obo·riť",
        "oborovať": "obo·ro·vať",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obplietlo") == "ob·pliet·lo"
    assert hyphenate("obrať") == "ob·rať"
    assert hyphenate("obruč") == "ob·ruč"
    assert hyphenate("obrúsila") == "ob·rú·si·la"
    assert hyphenate("oboznámiť") == "ob·oz·ná·miť"
    assert hyphenate("obozretný") == "ob·oz·ret·ný"


def test_batch_76_prefixed_zna_verbs_do_not_gain_a_false_na_suffix():
    expected = {
        "nepozná": "ne·po·zná",
        "neprahnite": "ne·prah·ni·te",
        "nerozpozná": "ne·roz·po·zná",
        "spozná": "spo·zná",
        "prizná": "pri·zná",
        "víťazná": "ví·ťaz·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_76_predat_family_keeps_the_pre_prefix_seam():
    expected = {
        "predať": "pre·dať",
        "predajú": "pre·da·jú",
        "nepredala": "ne·pre·da·la",
        "predaný": "pre·da·ný",
        "predajná": "pre·daj·ná",
        "nepredávajú": "ne·pre·dá·va·jú",
        "predám": "pre·dám",
        "predísť": "pred·ísť",
        "predobrý": "pre·dob·rý",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_144_pre_d_families_keep_real_morpheme_boundaries():
    expected = {
        "predákov": "pre·dá·kov",
        "predátory": "pre·dá·to·ry",
        "predavač": "pre·da·vač",
        "predchnutý": "pre·dchnu·tý",
        "predchnutného": "pre·dchnut·né·ho",
        "predelená": "pre·de·le·ná",
        "prederavená": "pre·de·ra·ve·ná",
        "prederiete": "pre·de·rie·te",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("predadamiti") == "pred·ada·mi·ti"
    assert hyphenate("Predexistenciu") == "Pred·exis·ten·ciu"
    assert hyphenate("predgeologických") == "pred·ge·o·lo·gic·kých"


def test_batch_145_distinguishes_pre_pred_and_predo_families():
    expected = {
        "predikáciu": "pre·di·ká·ciu",
        "prediskutovali": "pre·dis·ku·to·va·li",
        "predispozície": "pre·dis·po·zí·cie",
        "predivná": "pre·div·ná",
        "predivuhodná": "pre·di·vu·hod·ná",
        "predná": "pred·ná",
        "predný": "pred·ný",
        "predohra": "pre·do·hra",
        "predoslať": "pre·do·slať",
        "predošlé": "pre·do·šlé",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("predišiel") == "pred·išiel"
    assert hyphenate("predísť") == "pred·ísť"
    assert hyphenate("predizbe") == "pred·iz·be"
    assert hyphenate("predobraz") == "pred·ob·raz"


def test_batch_146_distinguishes_pre_pred_and_predo_families():
    expected = {
        "predostiera": "pre·do·stie·ra",
        "predostrieť": "pre·do·strieť",
        "predrahý": "pre·dra·hý",
        "predrať": "pre·drať",
        "predražený": "pre·dra·že·ný",
        "predriekať": "pre·drie·kať",
        "predrieknuté": "pre·driek·nu·té",
        "predupal": "pre·du·pal",
        "predvčerajšia": "pred·vče·raj·šia",
        "predvčerom": "pred·vče·rom",
        "predpredvčerom": "pred·pred·vče·rom",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("predúčinku") == "pred·účin·ku"
    assert hyphenate("predurčiť") == "pred·ur·čiť"
    assert hyphenate("predvoj") == "pred·voj"
    assert hyphenate("predtvoru") == "pred·tvo·ru"


def test_batch_147_distinguishes_preglejka_and_pre_prefix_families():
    expected = {
        "preglejky": "pre·glej·ky",
        "preglgla": "pre·glg·la",
        "prekvapenie": "pre·kva·pe·nie",
        "prekvapkávať": "pre·kvap·ká·vať",
        "preľstená": "pre·ľste·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_148_distinguishes_presn_and_pre_prefix_families():
    expected = {
        "prepošti": "pre·poš·ti",
        "prepoštov": "pre·poš·tov",
        "presný": "pres·ný",
        "presného": "pres·né·ho",
        "presnosť": "pres·nosť",
        "presníval": "pre·sní·val",
        "presnoril": "pre·sno·ril",
        "presťahovať": "pre·sťa·ho·vať",
        "presťahoval": "pre·sťa·ho·val",
        "preplieskal": "pre·plies·kal",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_149_keeps_pre_and_prie_prefix_boundaries():
    expected = {
        "presťahovať": "pre·sťa·ho·vať",
        "pretkaný": "pre·tka·ný",
        "pretnúť": "pre·tnúť",
        "pretrhnúť": "pre·trh·núť",
        "prezdobenom": "pre·zdo·be·nom",
        "prežhavená": "pre·žha·ve·ná",
        "priehľadný": "prie·hľad·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_150_distinguishes_prikrov_and_prikry_families():
    expected = {
        "priehrští": "prie·hrš·tí",
        "priehrštím": "prie·hrš·tím",
        "priekupníctvo": "prie·kup·níc·tvo",
        "príkrov": "prí·krov",
        "príkrovom": "prí·kro·vom",
        "príkrovu": "prí·kro·vu",
        "príkra": "prík·ra",
        "príkrejší": "prík·rej·ší",
        "príkro": "prík·ro",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert get_syllables("priehrští") == ["prie", "hrš", "tí"]
    assert {9, 10} <= set(break_points("priekupníctvo", all_points=True))


def test_batch_152_keeps_pri_stah_and_pri_stres_boundaries():
    expected = {
        "prisťahovalec": "pri·sťa·ho·va·lec",
        "prisťahovaní": "pri·sťa·ho·va·ní",
        "prístrešie": "prí·stre·šie",
        "prístreškami": "prí·streš·ka·mi",
        "prístrešok": "prí·stre·šok",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("prístroj") == "prís·troj"
    assert hyphenate("prísvit") == "prís·vit"


def test_batch_153_keeps_pri_zrak_and_pro_initial_lexical_stems():
    expected = {
        "prízrakmi": "prí·zrak·mi",
        "problematické": "prob·le·ma·tic·ké",
        "prognostickú": "prog·nos·tic·kú",
        "prognóza": "prog·nó·za",
        "program": "prog·ram",
        "progresii": "prog·re·sii",
        "prosme": "pros·me",
        "prospech": "pro·spech",
        "prospeje": "pros·pe·je",
        "prospekt": "pros·pekt",
        "prosperovať": "pros·pe·ro·vať",
        "prospešná": "pro·speš·ná",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("prorokstvo") == "pro·rok·stvo"
    assert hyphenate("prozápadný") == "pro·zá·pad·ný"


def test_batch_154_keeps_prospiet_stem_and_proti_alkohol_seam():
    expected = {
        "prospie": "pros·pie",
        "prospieť": "pros·pieť",
        "protialkoholickej": "pro·ti·al·ko·ho·lic·kej",
        "protialkoholickú": "pro·ti·al·ko·ho·lic·kú",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("protiopatrenia") == "pro·ti·opat·re·nia"


def test_batch_155_distinguishes_lexical_stems_and_compound_seams():
    expected = {
        "protivenstiev": "pro·ti·ven·stiev",
        "protivný": "pro·tiv·ný",
        "protivníčke": "pro·tiv·níč·ke",
        "protivzbura": "pro·ti·vzbu·ra",
        "protizázraky": "pro·ti·zá·zra·ky",
        "Proust": "Proust",
        "prozreteľný": "proz·re·teľ·ný",
        "prozreteľnosť": "proz·re·teľ·nosť",
        "prvostvoreného": "pr·vo·stvo·re·né·ho",
        "prvotlači": "pr·vo·tla·či",
        "prvotriedna": "pr·vo·tried·na",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_156_keeps_psohlav_seam_and_foreign_consonant_graphemes():
    expected = {
        "psohlavca": "pso·hlav·ca",
        "Ptolemaios": "Pto·le·mai·os",
        "Ptolemaiovi": "Pto·le·mai·o·vi",
        "Pullmana": "Pull·ma·na",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    # Ptolemaiovi is where the two part company: o is a syllable of its own, but
    # a break may not leave it standing alone, so -ovi stays whole in the break.
    assert get_syllables("Ptolemaiovi") == ["pto", "le", "mai", "o", "vi"]
    coinciding = {w: r for w, r in expected.items() if w != "Ptolemaiovi"}
    assert {word: get_syllables(word) for word in coinciding} == {
        word: result.casefold().split("·") for word, result in coinciding.items()
    }


def test_batch_157_keeps_rastlina_seam_and_inflectional_iach_nucleus():
    expected = {
        "rastlina": "rast·li·na",
        "rastlinách": "rast·li·nách",
        "rastlinkami": "rast·lin·ka·mi",
        "rastlinného": "rast·lin·né·ho",
        "rastlinstva": "rast·lin·stva",
        "reakciách": "re·ak·ci·ách",
        "relikviách": "re·lik·vi·ách",
        "reprezentáciách": "rep·re·zen·tá·ci·ách",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("radiátor") == "ra·di·á·tor"
    assert hyphenate("reprezentáciou") == "rep·re·zen·tá·ci·ou"


def test_batch_158_keeps_reuma_hiatus_without_splitting_other_eu_nuclei():
    expected = {
        "reumatické": "re·u·ma·tic·ké",
        "reumatizmus": "re·u·ma·tiz·mus",
        "reume": "re·u·me",
        "reumu": "re·u·mu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("pneumatika") == "pneu·ma·ti·ka"
    assert hyphenate("neurológ") == "neu·ro·lóg"
    assert hyphenate("leukémia") == "leu·ké·mia"
    assert hyphenate("eufória") == "eu·fó·ria"
    assert hyphenate("Európa") == "Eu·ró·pa"


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


def test_inflected_teen_numeral_keeps_its_seams_inside_hundreds():
    expected = {
        "sedemstošestnástku": "se·dem·sto·šest·nást·ku",
        "dvestojedenástka": "dve·sto·je·de·nást·ka",
        "päťstodevätnástkou": "päť·sto·de·vät·nást·kou",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("sedemnástke") == "se·dem·nást·ke"


def test_semien_family_does_not_gain_a_false_semi_compound_seam():
    expected = {
        "semienka": "se·mien·ka",
        "semienkach": "se·mien·kach",
        "semienko": "se·mien·ko",
        "semienkom": "se·mien·kom",
        "semienku": "se·mien·ku",
        "semienok": "se·mie·nok",
        "semienkami": "se·mien·ka·mi",
        "semienkový": "se·mien·ko·vý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("semifinále") == "se·mi·fi·ná·le"


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
        "ohňovzdorná": "oh·ňo·vzdor·ná",
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
    assert hyphenate("lživý") == "lži·vý"
    assert hyphenate("najlživejšie") == "naj·lži·vej·šie"
    assert hyphenate("najlživejšou") == "naj·lži·vej·šou"
    assert hyphenate("najľstivejší") == "naj·ľsti·vej·ší"
    assert hyphenate("predlžovať") == "pre·dl·žo·vať"


def test_batch_42_nested_one_letter_prefixes_keep_guarded_root_seams():
    expected = {
        "najneohrozenejšieho": "naj·ne·ohro·ze·nej·šie·ho",
        "najneotrasiteľnejšej": "naj·ne·otra·si·teľ·nej·šej",
        "najneúplatnejšia": "naj·ne·úplat·nej·šia",
        "najneusporiadanejšia": "naj·ne·uspo·ria·da·nej·šia",
        "najneústupnejšou": "naj·ne·ústup·nej·šou",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ohromný") == "oh·rom·ný"
    assert hyphenate("otrok") == "ot·rok"
    assert hyphenate("úplný") == "úpl·ný"
    assert hyphenate("ústredný") == "ústred·ný"
    assert hyphenate("uspávanka") == "us·pá·van·ka"


def test_batch_52_nested_u_prefix_keeps_guarded_root_seams():
    expected = {
        "najupokojujúcejšiu": "naj·upo·ko·ju·jú·cej·šiu",
        "najurodzenejších": "naj·uro·dze·nej·ších",
        "najuspokojivejšie": "naj·uspo·ko·ji·vej·šie",
        "najušľachtilejšie": "naj·ušľach·ti·lej·šie",
        "najutajenejšia": "naj·uta·je·nej·šia",
        "najutláčanejší": "naj·utlá·ča·nej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("usilovný") == "usi·lov·ný"
    assert hyphenate("urputný") == "ur·put·ný"
    assert hyphenate("užitočný") == "uži·toč·ný"


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
    assert hyphenate("najopodstatnenejšia") == "naj·opod·stat·ne·nej·šia"
    assert hyphenate("najopravdivejší") == "naj·oprav·di·vej·ší"
    assert hyphenate("ohromný") == "oh·rom·ný"
    assert hyphenate("opatrný") == "opa·tr·ný"


def test_batch_45_nested_o_prefix_and_ostro_compound_keep_guarded_seams():
    expected = {
        "najoprávnenejší": "naj·opráv·ne·nej·ší",
        "najopustenejšie": "naj·opus·te·nej·šie",
        "najoslnivejšie": "naj·osl·ni·vej·šie",
        "najostrieľanejších": "naj·ostrie·ľa·nej·ších",
        "najostrozrakejší": "naj·os·tro·zra·kej·ší",
        "najotrhanejší": "naj·otr·ha·nej·ší",
        "najotupenejší": "naj·otu·pe·nej·ší",
        "najoživujúcejšie": "naj·oži·vu·jú·cej·šie",
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
    assert hyphenate("uhrádzať") == "uhrá·dzať"
    assert hyphenate("úhrada") == "úhra·da"


def test_batch_46_lexical_stems_and_pravdo_compound_keep_their_seams():
    expected = {
        "najpospolitejší": "naj·pos·po·li·tej·ší",
        "najpotrebnejší": "naj·po·treb·nej·ší",
        "najpraktickejšie": "naj·prak·tic·kej·šie",
        "najpravdovravnejší": "naj·prav·do·vrav·nej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("pokročilý") == "po·kro·či·lý"
    assert hyphenate("posvätný") == "po·svät·ný"
    assert hyphenate("pradávny") == "pra·dáv·ny"


def test_potreb_family_keeps_psp_attested_morpheme_boundary():
    expected = {
        "potreba": "po·tre·ba",
        "potrebný": "po·treb·ný",
        "nepotrebný": "ne·po·treb·ný",
        "potrebovali": "po·tre·bo·va·li",
        "nepotrebovali": "ne·po·tre·bo·va·li",
        "neopotrebovali": "ne·opo·tre·bo·va·li",
        "neopotrebovateľný": "ne·opo·tre·bo·va·teľ·ný",
        "neopotrebuje": "ne·opo·tre·bu·je",
        "spotreba": "spo·tre·ba",
        "nespotrebované": "ne·spo·tre·bo·va·né",
        "nespotrebuje": "ne·spo·tre·bu·je",
        "upotrebiť": "upo·tre·biť",
        # A point after the u would leave neu at the end of the line.
        "neupotrebiteľným": "ne·upo·tre·bi·teľ·ným",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_cten_family_keeps_its_root_against_the_two_consonant_rule():
    expected = {
        "poctený": "po·cte·ný",
        "poctenú": "po·cte·nú",
        "zneuctený": "zne·ucte·ný",
        "zneuctenie": "zne·ucte·nie",
        "nezneuctenú": "ne·zne·ucte·nú",
        "vysokoctený": "vy·so·ko·cte·ný",
        "najvysokoctenejší": "naj·vy·so·ko·cte·nej·ší",
        "veľactený": "ve·ľa·cte·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_compound_seams_survive_the_linking_vowel_and_the_prefix():
    assert hyphenate("letohrádok") == "le·to·hrá·dok"
    assert hyphenate("letohrádku") == "le·to·hrád·ku"
    assert hyphenate("priehlavok") == "prie·hla·vok"
    assert hyphenate("priehlavku") == "prie·hlav·ku"


def test_batch_56_lexical_stems_keep_their_documented_boundaries():
    assert hyphenate("napospas") == "na·po·spas"
    assert hyphenate("napospol") == "na·pos·pol"
    assert hyphenate("naozajstný") == "na·ozaj·stný"
    assert hyphenate("naozajstnými") == "na·ozaj·stný·mi"
    assert hyphenate("naozaj") == "na·ozaj"
    assert hyphenate("pospať") == "po·spať"
    assert hyphenate("pozdravil") == "po·zdra·vil"


def test_batch_57_guarded_na_prefix_families_keep_their_seams():
    expected = {
        "nasťahoval": "na·sťa·ho·val",
        "nasťahovať": "na·sťa·ho·vať",
        "nástenné": "ná·sten·né",
        "nástennými": "ná·sten·ný·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("naschvál") == "na·schvál"
    assert hyphenate("nástojčivý") == "nás·toj·či·vý"


def test_batch_58_guarded_prefix_families_keep_their_seams():
    expected = {
        "nátlakovým": "ná·tla·ko·vým",
        "návratom": "ná·vra·tom",
        "naukladaného": "na·ukla·da·né·ho",
        "neukladajú": "ne·ukla·da·jú",
        "poukladaných": "po·ukla·da·ných",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ukladať") == "uk·la·dať"
    assert hyphenate("nástroj") == "nás·troj"


def test_batch_59_guarded_na_prefix_families_keep_their_seams():
    expected = {
        "nažgrlil": "na·žgr·lil",
        "nazhromaždeného": "na·zhro·maž·de·né·ho",
        "nazhromaždili": "na·zhro·maž·di·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("žgrliť") == "žgr·liť"
    assert hyphenate("zhromaždiť") == "zhro·maž·diť"
    assert hyphenate("nazlostiť") == "na·zlos·tiť"


def test_batch_60_necht_and_cnost_families_keep_their_documented_structure():
    expected = {
        "nechta": "nech·ta",
        "nechtami": "nech·ta·mi",
        "nechte": "nech·te",
        "nechtom": "nech·tom",
        "nechtov": "nech·tov",
        "nechty": "nech·ty",
        "necnosť": "ne·cnosť",
        "necnosti": "ne·cnos·ti",
        "necnostiam": "ne·cnos·tiam",
        "necnosťou": "ne·cnos·ťou",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nechtiac") == "ne·chtiac"
    assert hyphenate("nechtu") == "nech·tu"
    assert hyphenate("nechtoch") == "nech·toch"
    assert hyphenate("bezsúdnosť") == "bez·súd·nosť"


def test_batch_61_nested_prefixes_survive_suppletive_past_endings():
    expected = {
        "nedošla": "ne·do·šla",
        "nedošli": "ne·do·šli",
        "nedošlo": "ne·do·šlo",
        "neprišla": "ne·pri·šla",
        "nevyšla": "ne·vy·šla",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("došla") == "do·šla"
    assert hyphenate("nedorástli") == "ne·do·rást·li"
    assert hyphenate("nedostali") == "ne·do·sta·li"


def test_batch_62_keeps_the_nested_do_tkn_prefix_seam():
    expected = {
        "nedotkne": "ne·do·tkne",
        "nedotknú": "ne·do·tknú",
        "nedotknuteľný": "ne·do·tknu·teľ·ný",
        "najnedotknuteľnejšieho": "naj·ne·do·tknu·teľ·nej·šie·ho",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("dotkne") == "do·tkne"
    assert hyphenate("podotknúť") == "po·dotk·núť"


def test_batch_63_ne_shaped_lexical_stems_do_not_gain_a_false_prefix():
    expected = {
        "nefrit": "nef·rit",
        "nefrite": "nef·ri·te",
        "nefritové": "nef·ri·to·vé",
        "nefritového": "nef·ri·to·vé·ho",
        "nefritovozelenými": "nef·ri·to·vo·ze·le·ný·mi",
        "nefritu": "nef·ri·tu",
        "neger": "ne·ger",
        "negra": "neg·ra",
        "negrami": "neg·ra·mi",
        "negroch": "neg·roch",
        "negrovi": "neg·ro·vi",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("negrék") == "ne·grék"


def test_batch_65_keeps_documented_nested_ob_and_o_prefix_seams():
    expected = {
        "neobíde": "ne·ob·íde",
        "neobídete": "ne·ob·íde·te",
        "neobišiel": "ne·ob·išiel",
        "neobišli": "ne·ob·iš·li",
        "neobomkne": "ne·ob·omk·ne",
        "neobopínajú": "ne·obo·pí·na·jú",
        "neobozretne": "ne·ob·oz·ret·ne",
        "neobrúsi": "ne·obrú·si",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obíde") == "ob·íde"
    assert hyphenate("obozretne") == "ob·oz·ret·ne"
    assert hyphenate("obrúsi") == "ob·rú·si"
    assert hyphenate("neobohatil") == "ne·obo·ha·til"
    assert hyphenate("neobýva") == "ne·obý·va"


def test_batch_66_keeps_documented_nested_o_prefix_seams_before_ch():
    expected = {
        "neochladí": "ne·ochla·dí",
        "neochladzujú": "ne·ochla·dzu·jú",
        "neochráni": "ne·ochrá·ni",
        "neochránili": "ne·ochrá·ni·li",
        "neochromil": "ne·ochro·mil",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neochotne") == "ne·ochot·ne"
    assert hyphenate("neochorejú") == "ne·ocho·re·jú"


def test_chran_family_keeps_direct_one_letter_prefix_seams():
    expected = {
        "nezáchranne": "ne·zá·chran·ne",
        "ochrana": "ochra·na",
        "ochranca": "ochran·ca",
        "ochrane": "ochra·ne",
        "ochranou": "ochra·nou",
        "ochranu": "ochra·nu",
        "ochrany": "ochra·ny",
        "ochranný": "ochran·ný",
        "ochraňovať": "ochra·ňo·vať",
        "sebaochrane": "se·ba·ochra·ne",
        "všeochraňujúcej": "vše·ochra·ňu·jú·cej",
        "uchraňujem": "uchra·ňu·jem",
        "záchrana": "zá·chra·na",
        "záchranca": "zá·chran·ca",
        "záchrane": "zá·chra·ne",
        "záchranu": "zá·chra·nu",
        "záchrany": "zá·chra·ny",
        "záchranný": "zá·chran·ný",
        "zachraňovať": "za·chra·ňo·vať",
        "ochránené": "ochrá·ne·né",
        "ochráni": "ochrá·ni",
        "ochránila": "ochrá·ni·la",
        "ochráň": "ochráň",
        "uchránený": "uchrá·ne·ný",
        "uchránia": "uchrá·nia",
        "uchránite": "uchrá·ni·te",
        "uchráňte": "uchráň·te",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("chrániť") == "chrá·niť"
    assert hyphenate("zachrániť") == "za·chrá·niť"
    assert hyphenate("neochráni") == "ne·ochrá·ni"
    assert hyphenate("neuchránia") == "ne·uchrá·nia"
    assert hyphenate("schránka") == "schrán·ka"
    assert hyphenate("Cochrane") == "Coch·ra·ne"
    assert hyphenate("načuchrané") == "na·čuch·ra·né"


def test_batch_67_keeps_documented_nested_od_and_odo_prefix_seams():
    expected = {
        "neodíde": "ne·od·íde",
        "neodišli": "ne·od·iš·li",
        "neodísť": "ne·od·ísť",
        "neodoberie": "ne·odo·be·rie",
        "neodohnal": "ne·odo·hnal",
        "neodohrá": "ne·odo·hrá",
        "neodohráva": "ne·odo·hrá·va",
        "neodomkne": "ne·odo·mkne",
        "neodopiera": "ne·od·opie·ra",
        "neodoprel": "ne·odo·prel",
        "neodoprie": "ne·odo·prie",
        "neodovzdá": "ne·odo·vzdá",
        "neodoženie": "ne·odo·že·nie",
        "neodumiera": "ne·od·umie·ra",
        "neodumrel": "ne·od·um·rel",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neodieva") == "ne·odie·va"
    assert hyphenate("neodolá") == "ne·odo·lá"
    assert hyphenate("neodpláca") == "ne·od·plá·ca"


def test_batch_68_keeps_documented_nested_od_and_o_prefix_seams():
    expected = {
        "neodžijú": "ne·od·ži·jú",
        "Neodzrkadľuje": "Ne·od·zr·kad·ľu·je",
        "neohlasuj": "ne·ohla·suj",
        "neohluchli": "ne·ohluch·li",
        "neohnuteľné": "ne·ohnu·teľ·né",
        "neohryzená": "ne·ohry·ze·ná",
        "neoklamal": "ne·okla·mal",
        "neokrídlené": "ne·okríd·le·né",
        "neomdlieva": "ne·omdlie·va",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neolit") == "ne·o·lit"
    assert hyphenate("neoficiálne") == "ne·ofi·ci·ál·ne"
    assert hyphenate("neohybný") == "ne·ohyb·ný"
    assert hyphenate("neokázalý") == "ne·oká·za·lý"
    assert hyphenate("neokrôchaný") == "ne·ok·rô·cha·ný"
    assert hyphenate("neomylný") == "ne·omyl·ný"
    assert hyphenate("ohnivovlasý") == "oh·ni·vo·vla·sý"
    assert hyphenate("oklamal") == "ok·la·mal"


def test_batch_69_keeps_only_documented_nested_o_prefix_seams():
    expected = {
        "neoplatí": "ne·opla·tí",
        "neoplatilo": "ne·opla·ti·lo",
        "neoplatím": "ne·opla·tím",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neomylný") == "ne·omyl·ný"
    assert hyphenate("neopakoval") == "ne·opa·ko·val"
    assert hyphenate("neopätovať") == "ne·opä·to·vať"
    assert hyphenate("neopatrný") == "ne·opa·tr·ný"
    assert hyphenate("neopodstatnený") == "ne·opod·stat·ne·ný"
    assert hyphenate("neónové") == "ne·ó·no·vé"


def test_batch_70_keeps_only_documented_nested_o_prefix_seams():
    expected = {
        "neošklbal": "ne·oškl·bal",
        "neošklbali": "ne·oškl·ba·li",
        "neoslavuje": "ne·osla·vu·je",
        "neostrihané": "ne·ostri·ha·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neosobný") == "ne·osob·ný"
    assert hyphenate("neospravedlnený") == "ne·ospra·ve·dl·ne·ný"
    assert hyphenate("Ostrihom") == "Os·tri·hom"


def test_batch_71_keeps_only_documented_nested_o_prefix_seams():
    expected = {
        "neovplyvnene": "ne·ovplyv·ne·ne",
        "neovplyvnila": "ne·ovplyv·ni·la",
        "neozbrojený": "ne·ozbro·je·ný",
        "neozbrojenými": "ne·ozbro·je·ný·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ovplyvniť") == "ovplyv·niť"
    assert hyphenate("ozbrojiť") == "ozbro·jiť"
    assert hyphenate("ovládanie") == "ov·lá·da·nie"
    assert hyphenate("zvládnuť") == "zvlád·nuť"


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
        "delostrelectvo": "de·lo·stre·lec·tvo",
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
        "zvláštny": "zvlášt·ny",
        "zvláštna": "zvlášt·na",
        "zvláštneho": "zvlášt·ne·ho",
        "zvláštnemu": "zvlášt·ne·mu",
        "zvláštnych": "zvlášt·nych",
        "zvláštnym": "zvlášt·nym",
        "zvláštnymi": "zvlášt·ny·mi",
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
        "podvodníček": "pod·vod·ní·ček",
        "podvodníčka": "pod·vod·níč·ka",
        "podvodníčkov": "pod·vod·níč·kov",
        "podvodníckeho": "pod·vod·níc·ke·ho",
        "podvodníckym": "pod·vod·níc·kym",
        "podvodníckymi": "pod·vod·níc·ky·mi",
        "protivník": "pro·tiv·ník",
        "povozník": "po·voz·ník",
        "predchodník": "pred·chod·ník",
        "podnik": "pod·nik",
        "podnikať": "pod·ni·kať",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert get_syllables("podvodník") == ["pod", "vod", "ník"]


def test_one_letter_o_prefix_is_recognised_only_in_known_families():
    expected = {
        "opláchol": "oplá·chol",
        "oplachoval": "opla·cho·val",
        "oplakať": "opla·kať",
        "opláštenie": "opláš·te·nie",
        "oplešatejú": "ople·ša·te·jú",
        "opletačky": "ople·tač·ky",
        "oplodnenie": "oplod·ne·nie",
        "oplodňovať": "oplod·ňo·vať",
        "oplotená": "oplo·te·ná",
        "opľuť": "opľuť",
        "opľúvaný": "opľú·va·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("neoplakal") == "ne·opla·kal"
    assert hyphenate("oplácať") == "op·lá·cať"
    assert hyphenate("oplátku") == "op·lát·ku"
    assert hyphenate("oplývať") == "op·lý·vať"
    assert hyphenate("oslobodiť") == "oslo·bo·diť"
    assert hyphenate("oslabiť") == "osla·biť"
    assert hyphenate("ospravedlniť") == "ospra·ve·dl·niť"
    assert hyphenate("osvietiť") == "osvie·tiť"
    assert hyphenate("osvojiť") == "osvo·jiť"
    assert hyphenate("ostro") == "os·tro"
    assert hyphenate("ospalý") == "os·pa·lý"
    assert hyphenate("osemdesiat") == "osem·de·siat"


def test_batch_114_keeps_guarded_o_prefixes_and_foreign_ei():
    expected = {
        "opracovať": "opra·co·vať",
        "opradený": "opra·de·ný",
        "opraďte": "opraď·te",
        "oprali": "opra·li",
        "oprasiť": "opra·siť",
        "oprašovať": "opra·šo·vať",
        "oprať": "oprať",
        "oprášiť": "oprá·šiť",
        "Oppenheimer": "Op·pen·hei·mer",
        "Oppenheimerova": "Op·pen·hei·me·ro·va",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("oprátke") == "op·rát·ke"
    assert hyphenate("neistý") == "ne·is·tý"


def test_batch_115_suppresses_the_one_letter_o_prefix_in_guarded_families():
    expected = {
        "opreli": "opre·li",
        "opretého": "opre·té·ho",
        "opriasť": "opriasť",
        "oprie": "oprie",
        "oprite": "opri·te",
        "oprostí": "opros·tí",
        "oproti": "opro·ti",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_118_keeps_guarded_o_prefixes_and_lexical_contrasts():
    expected = {
        "ostreľovať": "ostre·ľo·vať",
        "ostrihané": "ostri·ha·né",
        "otlačili": "otla·či·li",
        "otlačky": "otlač·ky",
        "otlaky": "otla·ky",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("Ostrihom") == "Os·tri·hom"
    assert hyphenate("ostrapkaná") == "os·trap·ka·ná"
    assert hyphenate("otráviť") == "ot·rá·viť"
    assert hyphenate("ostro") == "os·tro"


def test_batch_122_keeps_nested_quantity_compound_seams():
    expected = {
        "päťizbovom": "päť·iz·bo·vom",
        "päťoktávový": "päť·ok·tá·vo·vý",
        "päťdesiatmiligramové": "päť·de·siat·mi·li·gra·mo·vé",
        "osemdesiatmiligramový": "osem·de·siat·mi·li·gra·mo·vý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("päťdesiatosem") == "päť·de·siat·osem"
    assert hyphenate("miliarda") == "mi·li·ar·da"


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


def test_batch_138_distinguishes_lexical_povraz_from_po_vrazdit():
    expected = {
        "povďakom": "po·vďa·kom",
        "povkladali": "po·vkla·da·li",
        "povodni": "po·vod·ni",
        "povodňou": "po·vod·ňou",
        "povraz": "pov·raz",
        "povrazca": "pov·raz·ca",
        "povraž": "po·vraž",
        "povraždené": "po·vraž·de·né",
        "povraždení": "po·vraž·de·ní",
        "povraždených": "po·vraž·de·ných",
        "povraždí": "po·vraž·dí",
        "povraždia": "po·vraž·dia",
        "povraždil": "po·vraž·dil",
        "povraždili": "po·vraž·di·li",
        "povraždiť": "po·vraž·diť",
        "povraždite": "po·vraž·di·te",
        "povrazníkom": "pov·raz·ní·kom",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("povracal") == "po·vra·cal"
    assert hyphenate("povodiť") == "po·vo·diť"


def test_batch_140_keeps_po_before_nonsyllabic_z_prefix_families():
    expected = {
        "pozháňal": "po·zhá·ňal",
        "pozhovárajme": "po·zho·vá·raj·me",
        "pozhovárali": "po·zho·vá·ra·li",
        "pozhovárať": "po·zho·vá·rať",
        "pozhŕňa": "po·zhŕ·ňa",
        "pozhŕňali": "po·zhŕ·ňa·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("pozvanie") == "po·zva·nie"
    assert hyphenate("požičať") == "po·ži·čať"
    assert hyphenate("pozhasínal") == "po·zha·sí·nal"


def test_podrobnost_inflections_do_not_trigger_drobno_compounds():
    expected = {
        "podrobnosti": "po·drob·nos·ti",
        "podrobností": "po·drob·nos·tí",
        "podrobnostiach": "po·drob·nos·tiach",
        "podrobnostiam": "po·drob·nos·tiam",
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
        "Sokrata": "Sok·ra·ta",
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
    assert divisions("niekto") == ["nie-kto"]
    assert divisions("niektorý") == ["nie-ktorý", "niekto-rý"]
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
        "súcna": "súc·na",
        "súdmi": "súd·mi",
        "súdnictvo": "súd·nic·tvo",
        "súdnosť": "súd·nosť",
        "bezsúdnosť": "bez·súd·nosť",
        "súkna": "súk·na",
        "súprava": "súp·ra·va",
        "súdržný": "sú·drž·ný",
        "súhrnný": "sú·hrn·ný",
        "súkmeňovci": "sú·kme·ňov·ci",
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


def test_cakat_prefixed_allomorph_keeps_the_prefix_boundary():
    expected = {
        "dočkať": "do·čkať",
        "počkajme": "po·čkaj·me",
        "prečkali": "pre·čka·li",
        "vyčkávanie": "vy·čká·va·nie",
        "počtár": "poč·tár",
        "počte": "poč·te",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_short_nut_and_sk_grammatical_suffixes_keep_the_stem_boundary():
    expected = {
        "písknuť": "písk·nuť",
        "rozlúsknuť": "roz·lúsk·nuť",
        "Pleskni": "Plesk·ni",
        "pľaskla": "pľask·la",
        "plesklo": "plesk·lo",
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_foreign_one_nucleus_spellings_are_not_split_as_hiatuses():
    assert get_syllables("flauta") == ["flau", "ta"]
    assert get_syllables("leukémia") == ["leu", "ké", "mia"]
    assert get_syllables("Sieur") == ["sieur"]
    assert break_points("Sieur", all_points=True, contextual=True) == []
    assert hyphenate("Sieur") == "Sieur"

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


def test_batch_103_keeps_distinct_ob_lookalike_families_apart():
    expected = {
        "obúchal": "obú·chal",
        "obušok": "obu·šok",
        "obuškami": "obuš·ka·mi",
        "obvyklý": "ob·vyk·lý",
        "obvyklého": "ob·vyk·lé·ho",
        "obvyklejšie": "ob·vyk·lej·šie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("obujte") == "ob·uj·te"
    assert hyphenate("obuvníckeho") == "ob·uv·níc·ke·ho"
    assert hyphenate("obvyklopil") == "ob·vy·klo·pil"


def test_batch_105_odieť_and_odev_are_not_split_as_the_prefix_od():
    expected = {
        "odeje": "ode·je",
        "odejte": "odej·te",
        "odela": "ode·la",
        "odený": "ode·ný",
        "odetého": "ode·té·ho",
        "odetejší": "ode·tej·ší",
        "odetie": "ode·tie",
        "odeve": "ode·ve",
        "odevmi": "odev·mi",
        "odevné": "odev·né",
        "odevnej": "odev·nej",
        "odevnými": "odev·ný·mi",
        "odevoch": "ode·voch",
        "odevu": "ode·vu",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("odetymologizovať") == "od·ety·mo·lo·gi·zo·vať"


def test_batch_106_keeps_odol_and_odovod_lexical_but_odtn_prefixal():
    expected = {
        "odolá": "odo·lá",
        "odolný": "odol·ný",
        "odolnosťou": "odol·nos·ťou",
        "odôvodnenie": "odô·vod·ne·nie",
        "odôvodniť": "odô·vod·niť",
        "odôvodňovali": "odô·vod·ňo·va·li",
        "odtnú": "od·tnú",
        "Odtnite": "Od·tni·te",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("odopierať") == "od·opie·rať"
    assert hyphenate("odtínať") == "od·tí·nať"


def test_batch_107_keeps_od_lookalikes_and_vyknut_paradigm_apart():
    expected = {
        "oduševnená": "odu·šev·ne·ná",
        "oduševniť": "odu·šev·niť",
        "oduševňovať": "odu·šev·ňo·vať",
        "oduté": "odu·té",
        "oduto": "odu·to",
        "Odvyknite": "Od·vyk·ni·te",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("oduhličiť") == "od·uh·li·čiť"
    assert hyphenate("odumierať") == "od·umie·rať"
    assert hyphenate("vyknísať") == "vy·kní·sať"


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


def test_rozarium_is_a_lexical_stem_and_not_the_roz_prefix():
    assert hyphenate("rozárium") == "ro·zá·ri·um"
    assert hyphenate("rozáriu") == "ro·zá·riu"


def test_productive_nost_derivatives_keep_their_morpheme_seam():
    expected = {
        "uprednostnení": "up·red·nost·ne·ní",
        "uprednostnený": "up·red·nost·ne·ný",
        "uprednostníš": "up·red·nost·níš",
        "uprednostniť": "up·red·nost·niť",
        "uprednostňoval": "up·red·nost·ňo·val",
        "uprednostňovanie": "up·red·nost·ňo·va·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("nostalgia") == "nos·tal·gia"


def test_batch_161_distinguishes_rozo_allomorph_from_nested_roz_prefixes():
    expected = {
        "rozochvieť": "ro·zo·chvieť",
        "rozodnieva": "ro·zo·dnie·va",
        "rozodraté": "ro·zo·dra·té",
        "rozohnať": "ro·zo·hnať",
        "rozoklaný": "ro·zo·kla·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("rozohniť") == "roz·oh·niť"
    assert hyphenate("rozohrať") == "roz·ohrať"
    assert hyphenate("rozohriať") == "roz·oh·riať"


def test_batch_162_expands_rozo_allomorph_and_keeps_vowel_initial_bases():
    expected = {
        "rozoklaných": "ro·zo·kla·ných",
        "rozomelie": "ro·zo·me·lie",
        "rozomletý": "ro·zo·mle·tý",
        "rozopnúť": "ro·zo·pnúť",
        "rozopretie": "ro·zo·pre·tie",
        "rozosadení": "ro·zo·sa·de·ní",
        "rozosiať": "ro·zo·siať",
        "rozoslali": "ro·zo·sla·li",
        "rozošle": "ro·zo·šle",
        "rozosmial": "ro·zo·smial",
        "rozosmutnil": "ro·zo·smut·nil",
        "rozospaté": "ro·zo·spa·té",
        "rozospievalo": "ro·zo·spie·va·lo",
        "rozostlaná": "ro·zo·stla·ná",
        "rozostrú": "ro·zo·strú",
        "rozoštváva": "ro·zo·štvá·va",
        "rozotnem": "ro·zo·tnem",
        "rozotrie": "ro·zo·trie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("rozorvať").startswith("ro·zo·")
    assert hyphenate("rozorala") == "roz·ora·la"
    assert hyphenate("rozostrené") == "roz·os·tre·né"
    assert hyphenate("rozostril") == "roz·os·tril"


def test_batch_163_completes_attested_rozo_root_alternants():
    expected = {
        "rozovrel": "ro·zo·vrel",
        "rozovretie": "ro·zo·vre·tie",
        "rozoženie": "ro·zo·že·nie",
        "rozoženiete": "ro·zo·že·nie·te",
        "rozožlčili": "ro·zo·žl·či·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("rozplakať") == "roz·pla·kať"
    assert hyphenate("rozpoznať") == "roz·po·znať"


def test_nested_ne_pri_prefixes_keep_the_snit_root_seam():
    expected = {
        "neprisnilo": "ne·pri·sni·lo",
        "neprisní": "ne·pri·sní",
        "neprisnívalo": "ne·pri·sní·va·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("prisnilo") == "pri·sni·lo"


def test_clear_plec_compounds_keep_their_compositional_seam():
    expected = {
        "širokoplecí": "ši·ro·ko·ple·cí",
        "širokoplecím": "ši·ro·ko·ple·cím",
        "úzkoplecý": "úz·ko·ple·cý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("plecia") == "ple·cia"
    assert hyphenate("protiplechu") == "pro·ti·ple·chu"


def test_clear_slabo_zrak_compounds_keep_their_compositional_seam():
    assert hyphenate("slabozraký") == "sla·bo·zra·ký"
    assert hyphenate("slabozrakým") == "sla·bo·zra·kým"
    assert hyphenate("slabosť") == "sla·bosť"


def test_smrs_noun_forms_do_not_gain_a_false_imperative_suffix():
    expected = {
        "smršte": "smrš·te",
        "smršti": "smrš·ti",
        "smrští": "smrš·tí",
        "smrštiam": "smrš·tiam",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("urobte") == "urob·te"


def test_so_initial_lexical_stems_do_not_gain_a_false_prefix_seam():
    expected = {
        "sodného": "sod·né·ho",
        "Sokrates": "Sok·ra·tes",
        "somnambul": "som·nam·bul",
        "sopliak": "sop·liak",
        "soška": "soš·ka",
        "sotva": "sot·va",
        "výsosti": "vý·sos·ti",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("zobrať") == "zo·brať"


def test_batch_175_keeps_clear_spolu_compounds_and_spohan_st_derivatives():
    expected = {
        "spohanštiť": "spo·han·štiť",
        "spohanštených": "spo·han·šte·ných",
        "spolublaženým": "spo·lu·bla·že·ným",
        "spoluchvenia": "spo·lu·chve·nia",
        "spolučlovek": "spo·lu·člo·vek",
        "spolukmitajúca": "spo·lu·kmi·ta·jú·ca",
        "spolukrúžiace": "spo·lu·krú·žia·ce",
        "spolupráca": "spo·lu·prá·ca",
        "spoluprečistenie": "spo·lu·pre·čis·te·nie",
        "spoluprecítená": "spo·lu·pre·cí·te·ná",
        "spolupreciťovania": "spo·lu·pre·ci·ťo·va·nia",
        "spoluprežiť": "spo·lu·pre·žiť",
        "spolupríčinou": "spo·lu·prí·či·nou",
        "spolusluha": "spo·lu·slu·ha",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("spolok") == "spo·lok"


def test_batch_176_extends_clear_spolu_compounds_without_splitting_s_z_vz_prefixes():
    expected = {
        "spoluslužobníci": "spo·lu·slu·žob·ní·ci",
        "spolusmrťou": "spo·lu·smr·ťou",
        "spolusprisahanec": "spo·lu·spri·sa·ha·nec",
        "spolustvoreniach": "spo·lu·stvo·re·niach",
        "spoluvšemohúcim": "spo·lu·vše·mo·hú·cim",
        "spoluvzbudením": "spo·lu·vzbu·de·ním",
        "spoluzachránená": "spo·lu·za·chrá·ne·ná",
        "spoluzachvátenie": "spo·lu·za·chvá·te·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("spolok") == "spo·lok"


def test_batch_177_keeps_clear_staro_compounds_and_cina_language_suffixes():
    expected = {
        "staroamerická": "sta·ro·ame·ric·ká",
        "staroarabčine": "sta·ro·arab·či·ne",
        "staroaristokratická": "sta·ro·aris·to·kra·tic·ká",
        "staroegyptčine": "sta·ro·egypt·či·ne",
        "staroegyptská": "sta·ro·egypt·ská",
        "starogréčtiny": "sta·ro·gréč·ti·ny",
        "Hindčina": "Hind·či·na",
        "Urdčina": "Urd·či·na",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("staroosvedčenými") == "sta·ro·os·ved·če·ný·mi"
    assert hyphenate("oberlerchenfeldčiny") == "ob·er·ler·chen·fel·dči·ny"


def test_batch_178_keeps_the_steto_skop_compound_seam():
    expected = {
        "stetoskop": "ste·to·skop",
        "stetoskopom": "ste·to·sko·pom",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("Stetson") == "Stet·son"


def test_batch_180_keeps_the_stvor_uhol_compound_seam():
    expected = {
        "štvoruhlej": "štvor·uh·lej",
        "štvoruholník": "štvor·uhol·ník",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("štvorité") == "štvo·ri·té"


def test_batch_179_keeps_inflectional_i_a_hiatus_distinct_from_native_ia():
    expected = {
        "gymnáziách": "gym·ná·zi·ách",
        "médiách": "mé·di·ách",
        "štúdiách": "štú·di·ách",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("uliciach") == "uli·ciach"


def test_batch_182_does_not_mistake_lexical_syn_stems_for_a_prefix():
    expected = {
        "synáčik": "sy·ná·čik",
        "synagóga": "sy·na·gó·ga",
        "synekdochu": "sy·nek·do·chu",
        "synovec": "sy·no·vec",
        "synovskou": "sy·nov·skou",
        "prasynami": "pra·sy·na·mi",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("symptómy") == "sym·ptó·my"
    assert hyphenate("synchrónny") == "syn·chrón·ny"


def test_batch_184_keeps_nested_numeral_and_tisic_compound_seams():
    expected = {
        "tisícdvesto": "ti·síc·dve·sto",
        "tisícdvestom": "ti·síc·dve·stom",
        "tisíchlavá": "ti·síc·hla·vá",
        "tisíchlavej": "ti·síc·hla·vej",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("tisíckráľom") == "ti·síc·krá·ľom"
    assert hyphenate("tisícosemsto") == "ti·síc·osem·sto"


def test_batch_185_keeps_clear_compound_seams_and_triumf_hiatus():
    expected = {
        "trasochvost": "tra·so·chvost",
        "tretidňová": "tre·ti·dňo·vá",
        "trištvrte": "tri·štvr·te",
        "triumf": "tri·umf",
        "triumfálne": "tri·um·fál·ne",
        "triumfálnymi": "tri·um·fál·ny·mi",
        "triumfoval": "tri·um·fo·val",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("trhnutie") == "trh·nu·tie"
    assert hyphenate("trieskami") == "tries·ka·mi"


def test_batch_186_distinguishes_troj_derivatives_from_true_compounds():
    expected = {
        "trojaký": "tro·ja·ký",
        "trojica": "tro·ji·ca",
        "trojitý": "tro·ji·tý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("trojosobný") == "troj·osob·ný"
    assert hyphenate("trojuholník") == "troj·uhol·ník"


def test_batch_188_keeps_u_bud_prefix_and_past_tense_seams():
    assert hyphenate("ubudlo") == "ubud·lo"
    assert hyphenate("neubudne") == "ne·ubud·ne"
    assert hyphenate("pribudlo") == "pri·bud·lo"
    assert hyphenate("zabudlo") == "za·bud·lo"
    assert hyphenate("nezabudlo") == "ne·za·bud·lo"
    assert hyphenate("nenadobudlo") == "ne·na·do·bud·lo"
    assert hyphenate("páčidlo") == "pá·či·dlo"
    assert hyphenate("zrkadlo") == "zr·ka·dlo"


def test_batch_183_keeps_clear_tele_telo_teplo_seams_and_lexical_termosk_stems():
    expected = {
        "telegramom": "te·le·gra·mom",
        "teleskop": "te·le·skop",
        "telocvičné": "te·lo·cvič·né",
        "teplovzdušný": "tep·lo·vzduš·ný",
        "termoska": "ter·mos·ka",
        "termoskou": "ter·mos·kou",
        "termosky": "ter·mos·ky",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("teológia") == "te·o·ló·gia"
    assert hyphenate("termostatom") == "ter·mo·sta·tom"


def test_batch_167_keeps_vod_stems_and_clear_samo_compound_seams():
    expected = {
        "rozvodnená": "roz·vod·ne·ná",
        "rozvodnenom": "roz·vod·ne·nom",
        "rozvodnený": "roz·vod·ne·ný",
        "rozvodní": "roz·vod·ní",
        "rozvodňuje": "roz·vod·ňu·je",
        "rozvodných": "roz·vod·ných",
        "samochvála": "sa·mo·chvá·la",
        "samovzdelávaniu": "sa·mo·vzde·lá·va·niu",
        "samovznietenia": "sa·mo·vznie·te·nia",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_199_suppresses_one_letter_u_prefix_seams_only_in_clear_families():
    expected = {
        "uspôsobené": "uspô·so·be·né",
        "ustajniť": "ustaj·niť",
        "ustal": "ustal",
        "ustať": "ustať",
        "ustatý": "usta·tý",
        "ustania": "usta·nia",
        "ustáliť": "ustá·liť",
        "ustaľuje": "usta·ľu·je",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("úsporná") == "ús·por·ná"
    assert hyphenate("ústach") == "ús·tach"
    assert hyphenate("ustarostený") == "us·ta·ros·te·ný"


def test_batch_201_suppresses_one_letter_u_prefix_seams_in_clear_verb_families():
    expected = {
        "ustelú": "uste·lú",
        "ustlal": "ustlal",
        "ustojíme": "usto·jí·me",
        "ustrápi": "ustrá·pi",
        "ustrážili": "ustrá·ži·li",
        "ustrnúť": "ustr·núť",
        "ustrnutie": "ustr·nu·tie",
        "ustrojenie": "ustro·je·nie",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("ustráchaný") == "us·trá·cha·ný"
    assert hyphenate("ustrašený") == "us·tra·še·ný"
    assert hyphenate("ústranie") == "ús·tra·nie"
    assert hyphenate("ústredný") == "ústred·ný"
    assert hyphenate("ústrižok") == "ús·tri·žok"
    assert hyphenate("ústrojenstvo") == "ús·tro·jen·stvo"


def test_batch_202_suppresses_one_letter_u_prefix_seams_in_clear_families():
    expected = {
        "uštudovať": "uštu·do·vať",
        "ustúpi": "ustú·pi",
        "ustupoval": "ustu·po·val",
        "utiahnutá": "utiah·nu·tá",
        "utíchnutie": "utích·nu·tie",
        "utkajú": "utka·jú",
        "utkaných": "utka·ných",
        "utkáva": "utká·va",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("uštvať") == "uš·tvať"
    assert hyphenate("usvedčiť") == "us·ved·čiť"
    assert hyphenate("úsvit") == "ús·vit"
    assert hyphenate("utkvejú") == "ut·kve·jú"


def test_batch_203_suppresses_one_letter_u_prefix_seams_in_clear_families():
    expected = {
        "utláčateľovi": "utlá·ča·te·ľo·vi",
        "utlačil": "utla·čil",
        "útlakom": "útla·kom",
        "utrápeného": "utrá·pe·né·ho",
        "utrasie": "utra·sie",
        "utrela": "utre·la",
        "utreté": "utre·té",
        "utŕhačstva": "utŕ·hač·stva",
        "utrhnúť": "utrh·núť",
        "utriediť": "utrie·diť",
        "utrúsenými": "utrú·se·ný·mi",
        "utrusovali": "utru·so·va·li",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("utratil") == "ut·ra·til"
    assert hyphenate("utvárať") == "ut·vá·rať"
    assert hyphenate("útrpný") == "útrp·ný"
    assert hyphenate("utkvejú") == "ut·kve·jú"


def test_batch_204_suppresses_one_letter_u_prefix_seams_in_clear_families():
    expected = {
        "utváraného": "ut·vá·ra·né·ho",
        "utvárneného": "ut·vár·ne·né·ho",
        "utvorenie": "utvo·re·nie",
        "Utvorme": "Utvor·me",
        "utvrdenie": "utvr·de·nie",
        "uvravené": "uv·ra·ve·né",
        "uvrešťanou": "uv·reš·ťa·nou",
        "uzamkla": "uza·mkla",
        "uzamknúť": "uza·mknúť",
        "uzdravené": "uzdra·ve·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("uvrhnuté") == "uvrh·nu·té"
    assert hyphenate("Uzbečtina") == "Uz·beč·ti·na"
    assert hyphenate("uzdou") == "uz·dou"


def test_batch_206_preserves_clear_compound_seams():
    expected = {
        "vajcohlavý": "vaj·co·hla·vý",
        "vďakyvzdávaní": "vďa·ky·vzdá·va·ní",
        "veľactený": "ve·ľa·cte·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("poctivý") == "poc·ti·vý"
    assert hyphenate("doctrina") == "doc·tri·na"


def test_batch_207_preserves_clear_compound_seams():
    expected = {
        "veľavážený": "ve·ľa·vá·že·ný",
        "veľavedomí": "ve·ľa·ve·do·mí",
        "veľavýznamnými": "ve·ľa·vý·znam·ný·mi",
        "veľavznešený": "ve·ľa·vzne·še·ný",
        "veľkočloveka": "veľ·ko·člo·ve·ka",
        "veľkošťastní": "veľ·ko·šťast·ní",
    }
    assert {word: hyphenate(word) for word in expected} == expected


def test_batch_208_preserves_clear_native_morpheme_and_diphthong_boundaries():
    expected = {
        "vládlo": "vlád·lo",
        "ovládlo": "ovlád·lo",
        "neovládlo": "ne·ovlád·lo",
        "zvládlo": "zvlád·lo",
        "vlákienkami": "vlá·kien·ka·mi",
        "vlákienok": "vlá·kie·nok",
        "vlasoštiepnych": "vla·so·štiep·nych",
        "vodlivosť": "vod·li·vosť",
        "vodlivý": "vod·li·vý",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("meradlo") == "me·ra·dlo"
    assert hyphenate("pradienko") == "pra·dien·ko"
    assert hyphenate("vlasový") == "vla·so·vý"
    assert hyphenate("zvodlivý") == "zvod·li·vý"


def test_batch_209_preserves_lexical_stems_suffixes_and_foreign_nuclei():
    expected = {
        "Voltaira": "Vol·tai·ra",
        "Voltaire": "Vol·taire",
        "vonkajškovo": "von·kajš·ko·vo",
        "vonkajškovosť": "von·kajš·ko·vosť",
        "vonkajškovosti": "von·kajš·ko·vos·ti",
        "vonkajškovostí": "von·kajš·ko·vos·tí",
        "neviestkovosti": "ne·viest·ko·vos·ti",
        "voška": "voš·ka",
        "voskovaným": "vos·ko·va·ným",
        "vozmi": "voz·mi",
        "vozne": "voz·ne",
        "vozni": "voz·ni",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("vohnal") == "vo·hnal"
    assert hyphenate("votkal") == "vo·tkal"
    assert hyphenate("voviedlo") == "vo·vied·lo"


def test_batch_210_preserves_abdrushin_and_abeundi_pronunciation():
    expected = {
        "Abdrushin": "Abd·ru·shin",
        "Abdrushina": "Abd·ru·shi·na",
        "Abdrushinov": "Abd·ru·shi·nov",
        "Abdrushinovej": "Abd·ru·shi·no·vej",
        "Abdrushinovi": "Abd·ru·shi·no·vi",
        "Abdrushinovo": "Abd·ru·shi·no·vo",
        "Abdrushinovu": "Abd·ru·shi·no·vu",
        "Abdrushinových": "Abd·ru·shi·no·vých",
        "Abdrushinovým": "Abd·ru·shi·no·vým",
        "abeundi": "abe·un·di",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert get_syllables("Abdrushin") == ["Abd", "ru", "shin"]
    assert get_syllables("abeundi") == ["a", "be", "un", "di"]


def test_reviewed_foreign_names_and_alzbeta_family():
    expected = {
        "Action": "Ac·tion",
        "Addition": "Ad·di·tion",
        "Allbright": "All·bright",
        "Allbrighta": "All·brighta",
        "Allgemeine": "All·ge·mei·ne",
        "Alžbeta": "Alž·be·ta",
        "Alžbete": "Alž·be·te",
        "Alžbetin": "Alž·be·tin",
        "Alžbetinho": "Alž·be·tin·ho",
        "Alžbetinom": "Alž·be·ti·nom",
        "Alžbetou": "Alž·be·tou",
        "Alžbetu": "Alž·be·tu",
        "Alžbety": "Alž·be·ty",
        "Ambivius": "Am·bi·vi·us",
        "Antonius": "An·to·ni·us",
        "Archelaus": "Ar·che·la·us",
        "Aucklandskom": "Auck·land·skom",
        "Beaujolais": "Beau·jo·lais",
        "drugstore": "drug·store",
        "Jones": "Jones",
        "Mahalaleel": "Ma·ha·la·leel",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    expected_syllables = {
        word: division.split("·") for word, division in expected.items()
    }
    expected_syllables["Allbrighta"] = ["All", "bright", "a"]
    for word in expected:
        if word.startswith("Alž"):
            expected_syllables[word] = [
                part.casefold() for part in expected_syllables[word]
            ]
    assert {word: get_syllables(word) for word in expected} == expected_syllables


def test_batch_211_preserves_d_final_past_tense_stems():
    assert hyphenate("vyhladlo") == "vy·hlad·lo"
    assert hyphenate("vyhliadlo") == "vy·hliad·lo"


def test_batch_212_preserves_native_prefixes_and_the_mrstit_paradigm():
    expected = {
        "vylhané": "vy·l·ha·né",
        "vymrštená": "vy·mrš·te·ná",
        "vymrští": "vy·mrš·tí",
        "odmrštenie": "od·mrš·te·nie",
        "vynadajú": "vy·na·da·jú",
        "vynadíva": "vy·na·dí·va",
        "vynadivil": "vy·na·di·vil",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("Mrštne") == "Mršt·ne"
    assert hyphenate("vynadhodiť") == "vy·nad·ho·diť"


def test_batch_213_keeps_the_lexical_vysk_family_intact():
    expected = {
        "výška": "výš·ka",
        "výškach": "výš·kach",
        "výšková": "výš·ko·vá",
        "výškových": "výš·ko·vých",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("výskok") == "vý·skok"


def test_batch_214_preserves_clear_vy_prefix_seams():
    expected = {
        "vysťahoval": "vy·sťa·ho·val",
        "vysťahovanými": "vy·sťa·ho·va·ný·mi",
        "vysťahujte": "vy·sťa·huj·te",
        "vytnem": "vy·tnem",
        "vytne": "vy·tne",
        "vytnite": "vy·tni·te",
        "vytnú": "vy·tnú",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("vystihnúť") == "vy·stih·núť"


def test_batch_216_preserves_compound_and_suffix_boundaries():
    expected = {
        "vzduchoprázdny": "vzdu·cho·práz·dny",
        "vzhliadlo": "vzhliad·lo",
        "vzrastlý": "vzrast·lý",
        "vzrastlých": "vzrast·lých",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("smelý") == "sme·lý"
    assert hyphenate("rastlina") == "rast·li·na"


def test_batch_218_preserves_clear_za_prefix_seams():
    expected = {
        "zábradlia": "zá·brad·lia",
        "zábradliami": "zá·brad·lia·mi",
        "zábradlie": "zá·brad·lie",
        "zábradlí": "zá·brad·lí",
        "zábradlíčko": "zá·brad·líč·ko",
        "zábran": "zá·bran",
        "Zábrana": "Zá·bra·na",
        "zábranami": "zá·bra·na·mi",
        "zábranou": "zá·bra·nou",
        "zábranu": "zá·bra·nu",
        "zábrany": "zá·bra·ny",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("zábrus") == "záb·rus"


def test_batch_219_preserves_the_clear_zahlavie_prefix_seam():
    expected = {
        "záhlavia": "zá·hla·via",
        "záhlavie": "zá·hla·vie",
        "záhlavných": "zá·hlav·ných",
        "záhlaví": "zá·hla·ví",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("záchrana") == "zá·chra·na"


def test_batch_224_preserves_the_clear_za_tn_prefix_seam():
    assert hyphenate("Zatnete") == "Za·tne·te"


def test_batch_226_preserves_the_zazrak_alternant_prefix_seam():
    expected = {
        "zavďak": "za·vďak",
        "zavdať": "za·vdať",
        "zavdávajú": "za·vdá·va·jú",
        "zázračik": "zá·zra·čik",
        "zázračnejších": "zá·zrač·nej·ších",
        "zázračnosti": "zá·zrač·nos·ti",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("prízračný") == "príz·rač·ný"


def test_batch_227_preserves_the_zazraku_chtiv_compound_seam():
    expected = {
        "zázrakuchtivého": "zá·zra·ku·chti·vé·ho",
        "zázrakuchtivejší": "zá·zra·ku·chti·vej·ší",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("vládychtivý") == "vlá·dych·ti·vý"


def test_batch_228_preserves_clear_compound_seams():
    expected = {
        "zhrubohmotnenia": "zhru·bo·hmot·ne·nia",
        "zmrštené": "zmrš·te·né",
        "zmrštenosti": "zmrš·te·nos·ti",
        "zmrštia": "zmrš·tia",
        "zmrštili": "zmrš·ti·li",
        "žiaruvzdornej": "žia·ru·vzdor·nej",
        "žiaruvzdorné": "žia·ru·vzdor·né",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("smršti") == "smrš·ti"
    assert hyphenate("zlatohlavu") == "zla·toh·la·vu"


def test_batch_229_preserves_the_zmurkat_past_tense_stem():
    expected = {
        "žmurkla": "žmurk·la",
        "žmurkli": "žmurk·li",
        "žmurklo": "žmurk·lo",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("žmurkol") == "žmur·kol"


def test_batch_230_preserves_clear_zo_and_znovu_seams():
    expected = {
        "nezotne": "ne·zo·tne",
        "znovusmrti": "zno·vu·smr·ti",
        "zotne": "zo·tne",
        "zotnem": "zo·tnem",
        "zotnúc": "zo·tnúc",
        "zotnúť": "zo·tnúť",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("zotol") == "zo·tol"


def test_batch_223_preserves_clear_za_prefix_seams():
    expected = {
        "zardievajúc": "za·rdie·va·júc",
        "zarmucuje": "za·rmu·cu·je",
        "zarmútenými": "za·rmú·te·ný·mi",
        "zarmútiť": "za·rmú·tiť",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    assert hyphenate("rmútiť") == "rmú·tiť"
    assert hyphenate("zarmu") == "zar·mu"
    assert hyphenate("zarputilo") == "zar·pu·ti·lo"


def test_calibration_verdicts_keep_the_one_letter_vowel_prefix_seam():
    """Operator PSP verdicts of 2026-09-05 on the 200-form calibration sample.

    A word-initial o-/u- prefix is a morpheme seam, and section 6.2 drops the
    point after it outright. Without that seam the whole-word rule of section
    4.2 placed a point inside the root's own onset instead: oz|načte, oh|lávku,
    up|rime, uk|ráť. The root families below are attested, so the seam is found
    and the invalid point disappears.
    """
    expected = {
        "uprime": "upri·me",
        "ukráť": "ukráť",
        "označte": "označ·te",
        "ohlávku": "ohláv·ku",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    family = {
        "označiť": "ozna·čiť",
        "označ": "označ",
        "ohlávka": "ohláv·ka",
        "upriamiť": "upria·miť",
        "ukrátiť": "ukrá·tiť",
    }
    assert {word: hyphenate(word) for word in family} == family
    # The o and u inside a root are no prefix; their point stays where 4.2 puts it.
    guarded = {
        "okno": "ok·no",
        "ostrov": "os·trov",
        "otrok": "ot·rok",
        "ovca": "ov·ca",
        "značka": "znač·ka",
        "hlávka": "hláv·ka",
    }
    assert {word: hyphenate(word) for word in guarded} == guarded


def test_a_one_letter_vowel_prefix_is_not_left_standing_alone():
    """A vowel prefix has a seam on both sides; taking both isolates the letter.

    Section 9 grades this the same way as the word-initial case: the point that
    would strand the vowel is legal but discouraged, so it lives at the
    contextual level and never in the default output.
    """
    expected = {
        "neukladajú": "ne·ukla·da·jú",
        "neohrada": "ne·ohra·da",
        "najutajenejšia": "naj·uta·je·nej·šia",
        "podopreli": "pod·opre·li",
        "pootočil": "po·oto·čil",
        "obohraných": "ob·ohra·ných",
        "neúnavný": "ne·únav·ný",
    }
    assert {word: hyphenate(word) for word in expected} == expected
    # Discouraged, not barred: a narrow measure may still take the point.
    assert hyphenate("neukladajú", all_points=True, contextual=True) == "ne·u·kla·da·jú"
    assert hyphenate("najutajenejšia", all_points=True, contextual=True) == (
        "naj·u·ta·je·nej·šia"
    )

    # Section 3.4 decides which of the two points yields: a connecting vowel
    # belongs to the first part of a compound, so there the later point is the
    # seam and the earlier one gives way.
    compounds = {
        "teológia": "te·o·ló·gia",
        "geológia": "ge·o·ló·gia",
        "choreografiek": "cho·re·o·gra·fiek",
        "predgeologických": "pred·ge·o·lo·gic·kých",
    }
    assert {word: hyphenate(word) for word in compounds} == compounds
