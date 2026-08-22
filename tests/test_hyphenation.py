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
        "trojuholník": "troj·u·hol·ník",
        "viacfarebný": "viac·fa·reb·ný",
        "MODLOSLUŽOBNÍČKA": "MOD·LO·SLU·ŽOB·NÍČ·KA",
        "stredoamerický": "stre·do·a·me·ric·ký",
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
    assert get_syllables("ihrisko") == ["ih", "ris", "ko"]
    assert get_syllables("robota") == ["ro", "bo", "ta"]
    assert get_syllables("choroba") == ["cho", "ro", "ba"]
    assert get_syllables("Slovensko") == ["slo", "ven", "sko"]
    assert get_syllables("odpornosťou") == ["od", "por", "nos", "ťou"]


def test_intervocalic_consonant_count_boundaries():
    expected = {
        "žena": "že·na",
        "maslo": "mas·lo",
        "láska": "lás·ka",
        "mašlička": "maš·lič·ka",
        "sestra": "ses·tra",
        "Angličan": "An·gli·čan",
        "lingvistika": "lin·gvis·ti·ka",
        "špendlík": "špen·dlík",
    }

    assert {word: hyphenate(word) for word in expected} == expected


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
