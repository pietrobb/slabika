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
        "porkpie": "pork·pie",
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
        "aeronauti": "ae·ro·nau·ti",
        "aeronautika": "ae·ro·nau·ti·ka",
        "naučiť": "na·učiť",
        "nautešujú": "na·ute·šu·jú",
        "arciposlami": "ar·ci·pos·la·mi",
        "arciposlovia": "ar·ci·pos·lo·via",
        "mahagónovohneda": "ma·ha·gó·no·vo·hne·da",
        "mastnoksichtej": "mast·no·ksich·tej",
    }

    assert {word: hyphenate(word) for word in expected} == expected


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


def test_cluster_tail_of_43_must_be_able_to_open_a_syllable():
    """4.3 says the tail *opens* the next syllable, so it has to be an opening.

    ``al|žbetínska`` hands over ``žb``, which begins no Slovak word before a
    vowel; the point moves right until the tail is one Slovak words are written
    with. The three readings PSP prints stay where they are, because in each of
    them the tail already opens words: tra-, tva-, tra-.
    """
    moved = {
        "alžbetínska": "alž·be·tín·ska",
        "ústna": "úst·na",
        "zamestnáva": "za·mest·ná·va",
        "gangster": "gang·ster",
        "očistca": "očist·ca",
        "veštba": "vešt·ba",
    }
    kept = {
        "sestra": "ses·tra",
        "pastva": "pas·tva",
        "zajtra": "zaj·tra",
        "lingvistika": "lin·gvis·ti·ka",   # gv- opens gvaš, which PSP prints
        "abstinencia": "ab·sti·nen·cia",
        "monštrancie": "mon·štran·cie",
        "najvľúdnejšou": "naj·vľúd·nej·šou",
        "chrbtica": "chrb·ti·ca",
    }
    assert {word: hyphenate(word) for word in moved} == moved
    assert {word: hyphenate(word) for word in kept} == kept


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


@pytest.mark.xfail(
    strict=True,
    reason="ai is one nucleus in medaila and two in naivný; the falling-"
           "diphthong rule covers au/eu/ou only",
)
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
