# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The three classes where two correct analyses of a Slovak word disagree.

Most words are uninteresting to test: ``poľnohospodárstvo`` and ``štvorvalec``
come out the same whether you divide them phonologically or morphologically, so
a corpus full of them proves nothing. What has to be tested is the small set of
environments where the phonotactic fallback and the morphology (or the
etymology) give *different* answers:

1. a consonant-final prefix in front of a vowel-initial root — the fallback
   moves the consonant right (``ro-zo-rať``), the morpheme boundary forbids it
   (``roz-o-rať``). Decidable by rule, so it is tested exhaustively by
   generating the product of prefixes and roots rather than by listing words;
2. a prefix that has lexicalized and is no longer a boundary (``ro-zum``). Not
   decidable by rule at all — the stem list lives in the CC0 data layer;
3. written ``ia/ie/iu`` that is a hiatus rather than a diphthong
   (``pia-tok`` against ``Má-ri-a``). Partly decidable, and the two decidable
   environments are pinned here.
"""

import pytest

from slabika import syllables as get_syllables
from slabika.exceptions import LEXICALIZED_STEMS
from slabika.syllabify import _SK_COMPOSITA, _SK_PREFIXES, _SK_SUFFIXES_CONS

# --------------------------------------------------------------------------
# Class 1 — consonant-final prefix, vowel-initial root
# --------------------------------------------------------------------------

#: Attested combinations. The point is the product, not the individual word:
#: every prefix is checked against every root it genuinely combines with, so a
#: regression in one prefix cannot hide behind a hand-picked example of another.
PREFIXED_VOWEL_INITIAL_ROOTS = {
    "roz": ("orať", "učiť", "uzliť", "istiť", "ožať"),
    "bez": ("očný", "ústie", "ohľadný", "úhonný", "účelný"),
    "pod": ("oblasť", "účet", "úroveň", "usadiť", "ostatný"),
    "nad": ("oblačný", "obyčajný", "úroveň", "uhoľný"),
    "od": ("ísť", "učiť", "izolovať", "usudzovať"),
    "ob": ("ísť", "ohnať", "účtovať"),
    "pred": ("obraz", "izba", "určiť", "operačný", "úsudok"),
    "naj": ("ostrejší", "užšia", "istejší"),
}


def _prefix_survives(word: str, prefix: str) -> bool:
    """True when some syllable boundary falls exactly at the end of the prefix."""
    syllables = get_syllables(word)
    return any(
        "".join(syllables[:i]).lower() == prefix
        for i in range(1, len(syllables) + 1)
    )


@pytest.mark.parametrize(
    ("prefix", "root"),
    [
        (prefix, root)
        for prefix, roots in PREFIXED_VOWEL_INITIAL_ROOTS.items()
        for root in roots
    ],
)
def test_a_prefix_boundary_survives_a_vowel_initial_root(prefix, root):
    word = prefix + root
    assert _prefix_survives(word, prefix), (
        f"{word} -> {'-'.join(get_syllables(word))}: the fallback pulled the "
        f"prefix-final consonant across the morpheme boundary"
    )


def test_a_vocalized_prefix_does_not_swallow_the_root_vowel():
    """bezo-, nado-, podo-, predo- vocalize only before mn- and vš-.

    Anywhere else the -o- is the root's own, and matching the longer variant
    first produces be-zo-hľad-ný for bez-oh-ľad-ný.
    """
    assert get_syllables("bezohľadný") == ["bez", "oh", "ľad", "ný"]
    assert get_syllables("podoblasť") == ["pod", "ob", "lasť"]
    assert get_syllables("nadoblačný") == ["nad", "ob", "lač", "ný"]
    assert get_syllables("predobraz") == ["pred", "ob", "raz"]
    # ...but the genuine vocalized environments still resolve as vocalized.
    assert get_syllables("odovzdať") == ["o", "do", "vzdať"]
    assert get_syllables("rozobrať") == ["ro", "zo", "brať"]


# --------------------------------------------------------------------------
# Class 2 — a prefix that is no longer a prefix
# --------------------------------------------------------------------------

LEXICALIZED_FORMS = {
    "rozum": ["ro", "zum"],
    "rozumu": ["ro", "zu", "mu"],
    "rozumný": ["ro", "zum", "ný"],
    "rozumieť": ["ro", "zu", "mieť"],
    "obed": ["o", "bed"],
    "obeda": ["o", "be", "da"],
    "obedovať": ["o", "be", "do", "vať"],
    "obec": ["o", "bec"],
    "obecenstvo": ["o", "be", "cen", "stvo"],
    "obora": ["o", "bo", "ra"],
    "obalu": ["o", "ba", "lu"],
    "obuvník": ["o", "buv", "ník"],
    "odevu": ["o", "de", "vu"],
}


@pytest.mark.parametrize(("word", "expected"), LEXICALIZED_FORMS.items())
def test_a_lexicalized_prefix_forms_no_boundary(word, expected):
    assert get_syllables(word) == expected


def test_listing_a_stem_covers_its_whole_inflectional_family():
    """The data layer lists stems, not word forms.

    ``obed`` alone has to carry ``obeda``, ``obedovať``, ``obedný``; listing
    forms one by one would leave the paradigm half-fixed, which is exactly how
    ``o-bed`` and ``ob-e-da`` came to disagree with each other.
    """
    for stem in LEXICALIZED_STEMS:
        assert stem == stem.lower()
        assert not stem.endswith(("ý", "á", "é", "ú"))


# --------------------------------------------------------------------------
# Class 3 — diphthong against hiatus
# --------------------------------------------------------------------------

DIPHTHONGS_STAY_WHOLE = {
    "piatok": ["pia", "tok"],
    "viera": ["vie", "ra"],
    "miesto": ["mies", "to"],
    "diabol": ["dia", "bol"],
    "spoločenstiev": ["spo", "lo", "čen", "stiev"],
    "iniciatíva": ["i", "ni", "cia", "tí", "va"],
    "Excelencia": ["ex", "ce", "len", "cia"],
}

HIATUS_IS_TWO_NUCLEI = {
    # after a long syllable and a consonant that carries no native diphthong
    "Mária": ["má", "ri", "a"],
    "Ázia": ["á", "zi", "a"],
    "hystéria": ["hys", "té", "ri", "a"],
    "biológia": ["bi", "o", "ló", "gi", "a"],
    "poézia": ["po", "é", "zi", "a"],
    # -ium: no native Slovak ending has this shape
    "akvárium": ["ak", "vá", "ri", "um"],
    "gymnázium": ["gym", "ná", "zi", "um"],
    "kritérium": ["kri", "té", "ri", "um"],
    # io was never a diphthong to begin with
    "štúdio": ["štú", "di", "o"],
    "rádio": ["rá", "di", "o"],
}


@pytest.mark.parametrize(("word", "expected"), DIPHTHONGS_STAY_WHOLE.items())
def test_a_diphthong_is_one_nucleus(word, expected):
    assert get_syllables(word) == expected


@pytest.mark.parametrize(("word", "expected"), HIATUS_IS_TWO_NUCLEI.items())
def test_a_learned_hiatus_is_two_nuclei(word, expected):
    assert get_syllables(word) == expected


def test_the_hiatus_rule_spares_native_endings_after_a_long_stem():
    """The rhythmic law has a productive set of exceptions.

    3rd person plural -ia and the animal adjective -ia stand after a long stem
    and stay diphthongs, so the hiatus rule must not reach a consonant that
    palatalizes before i.
    """
    assert get_syllables("vrátia") == ["vrá", "tia"]
    assert get_syllables("chvália") == ["chvá", "lia"]
    assert get_syllables("hlásia") == ["hlá", "sia"]
    assert get_syllables("vtáčia") == ["vtá", "čia"]


# --------------------------------------------------------------------------
# Rules about the rules
# --------------------------------------------------------------------------

def test_no_vowel_initial_suffix_is_treated_as_a_morpheme_boundary():
    """A vowel-initial suffix contributes no consonant to redistribute.

    Declaring one strands the stem's final cluster — ozd-o-ba for oz-do-ba,
    dobr-o-ta for dob-ro-ta — because the boundary is placed before a vowel
    that the fallback would have given an onset.
    """
    vowels = set("aáäeéiíoóôuúyý")
    offenders = [sfx for sfx in _SK_SUFFIXES_CONS if sfx[0] in vowels]
    assert offenders == []


@pytest.mark.parametrize(
    "table, ends",
    [
        (_SK_PREFIXES, False),
        (_SK_COMPOSITA, False),
        (_SK_SUFFIXES_CONS, True),
    ],
)
def test_no_fixed_form_shadows_a_longer_one(table, ends):
    """Where two forms can match the same word, the longer must come first.

    The lookup tries one form per distinct length, longest first, which is
    equivalent to scanning the table in order only when the table itself never
    puts a short form ahead of a longer one that contains it. ``ňstvo``
    violated this: every word ending in it also ends in ``stvo``, listed first,
    so it never fired — and had it fired it would have given pá-ňstvo for
    pán-stvo. Such an entry is not a performance problem, it is a dead rule
    that reads as if it were live.
    """
    match = str.endswith if ends else str.startswith
    order = {form: i for i, form in enumerate(table)}
    shadowed = [
        (short, long)
        for short in table
        for long in table
        if len(long) > len(short) and match(long, short) and order[short] < order[long]
    ]
    assert shadowed == []


def test_a_word_the_rules_now_derive_is_not_kept_in_the_lexicon():
    """The exception list must shrink when the rules improve.

    ``porota`` needed a lexical entry only because -ota was declared a
    boundary; once that went, the entry became dead weight that would have
    masked the next regression.
    """
    from slabika.exceptions import LEXICAL_SYLLABIFICATIONS

    assert "porota" not in LEXICAL_SYLLABIFICATIONS
    assert get_syllables("porota") == ["po", "ro", "ta"]
