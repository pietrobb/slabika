# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Golden cases for syllabification and typographic hyphenation."""

from slabika import (
    break_points,
    hyphenate,
    is_vowel,
    split_into_phonemes,
    syllables as get_syllables,
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
        "pohľadom": "po·hľa·dom",
        "pohľady": "po·hľa·dy",
        "Opatrnosť": "Opa·tr·nosť",
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
    }

    assert {word: hyphenate(word) for word in expected} == expected


def test_syllabification_and_typographic_hyphenation_are_separate_layers():
    assert get_syllables("Evanjeliá") == ["e", "van", "je", "li", "á"]
    assert hyphenate("Evanjeliá") == "Evan·je·liá"
    assert get_syllables("Fastolfe") == ["fas", "tolfe"]
    assert hyphenate("Fastolfe") == "Fas·tolfe"
    assert get_syllables("Opatrnosť") == ["o", "pa", "tr", "nosť"]
    assert get_syllables("dychtivosťou") == ["dych", "ti", "vos", "ťou"]
    assert hyphenate("dychtivosťou") == "dych·ti·vos·ťou"
    assert get_syllables("ženou") == ["že", "nou"]
    assert get_syllables("použiť") == ["po", "u", "žiť"]
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
        assert points <= set(break_points(word))


def test_foreign_one_nucleus_spellings_are_not_split_as_hiatuses():
    assert get_syllables("flauta") == ["flau", "ta"]
    assert get_syllables("leukémia") == ["leu", "ké", "mia"]
    assert get_syllables("medaila") == ["me", "dai", "la"]

    expected = {
        "flauta": (4, 3),
        "leukémia": (3, 2),
        "medaila": (5, 4),
    }

    for word, (required, forbidden) in expected.items():
        points = break_points(word)
        assert required in points
        assert forbidden not in points


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


def test_a_umlaut_is_a_short_vowel_and_hyphenation_nucleus():
    assert is_vowel("ä")
    assert hyphenate("mäkký") == "mäk·ký"


def test_terminal_dz_is_one_phoneme():
    assert split_into_phonemes("dž") == ["dž"]


def test_uncertain_non_slovak_tokens_are_not_hyphenated():
    for token in ("d’Arc", "L'Arbre", "Saint-Denis", "Neufchâteau", "Compiègne"):
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
    for word in ("vlk", "prst", "Saint-Denis", "Compiègne"):
        assert break_points(word) == []
        assert hyphenate(word) == word
