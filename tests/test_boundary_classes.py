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

from slabika import hyphenate
from slabika import syllables as get_syllables
from slabika.syllabify import (
    _SK_COMPOSITA,
    _SK_PREFIXES,
    _SK_SUFFIXES_CONS,
    get_morpheme_parts,
)

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
    assert get_syllables("bezohľadný") == ["bez", "o", "hľad", "ný"]
    assert get_syllables("podoblasť") == ["pod", "ob", "lasť"]
    assert get_syllables("nadoblačný") == ["nad", "ob", "lač", "ný"]
    assert get_syllables("predobraz") == ["pred", "ob", "raz"]
    # ...but the genuine vocalized environments still resolve as vocalized.
    assert get_syllables("odovzdať") == ["o", "do", "vzdať"]
    assert get_syllables("rozobrať") == ["ro", "zo", "brať"]
    assert get_syllables("predovšetkým") == ["pre", "do", "všet", "kým"]
    assert get_syllables("nadovšetko") == ["na", "do", "všet", "ko"]


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


#: Forms the lexicalized-stem list used to answer for. The list is gone, so
#: these are open regressions: the expectation is PSP-correct and stays here as
#: the specification a rule has to meet, not as a word that may be listed.
_NEEDS_A_RULE = frozenset(LEXICALIZED_FORMS) - {"rozum", "obed", "obec"}


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        pytest.param(
            word,
            expected,
            marks=pytest.mark.xfail(
                word in _NEEDS_A_RULE,
                reason="etymological lexicalization, no rule derives it yet",
                strict=True,
            ),
        )
        for word, expected in LEXICALIZED_FORMS.items()
    ],
)
def test_a_lexicalized_prefix_forms_no_boundary(word, expected):
    assert get_syllables(word) == expected


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
    "akvárium": ["a", "kvá", "ri", "um"],
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


# au, eu and ou are written like a hiatus and read like one nucleus. PSP §4.4
# forbids deciding that by the letters alone, and the morphology is what
# decides: the pair is one nucleus wherever no seam runs through it.
FALLING_DIPHTHONG_IS_ONE_NUCLEUS = {
    "pauza": ["pau", "za"],
    "klauzúra": ["klau", "zú", "ra"],
    "pneumatika": ["pneu", "ma", "ti", "ka"],
    "reumatizmus": ["reu", "ma", "ti", "zmus"],
    "rukou": ["ru", "kou"],
    "neurológ": ["neu", "ro", "lóg"],
    "nautika": ["nau", "ti", "ka"],
}

SEAM_KEEPS_THE_VOWELS_APART = {
    "poučiť": ["po", "u", "čiť"],
    "neužil": ["ne", "u", "žil"],
    "zneužiť": ["zne", "u", "žiť"],
    "zaujímavý": ["za", "u", "jí", "ma", "vý"],
    "vierouka": ["vie", "ro", "u", "ka"],
    "sebaurčenie": ["se", "ba", "ur", "če", "nie"],
    # the Latin second declension of a stem in -e, the -ium of _resolve_hiatus
    # in the neuter and the masculine
    "múzeum": ["mú", "ze", "um"],
    "Orfeus": ["or", "fe", "us"],
}


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        pytest.param(
            word,
            expected,
            marks=pytest.mark.xfail(
                word in ("neurológ", "nautika"),
                reason="a loan whose opening looks like ne-/na-; needs the "
                       "word-identity layer, not a list",
                strict=True,
            ),
        )
        for word, expected in FALLING_DIPHTHONG_IS_ONE_NUCLEUS.items()
    ],
)
def test_au_eu_ou_are_one_nucleus_inside_a_morpheme(word, expected):
    assert get_syllables(word) == expected


@pytest.mark.parametrize(("word", "expected"), SEAM_KEEPS_THE_VOWELS_APART.items())
def test_a_seam_divides_what_would_otherwise_be_one_nucleus(word, expected):
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

def test_every_onset_cluster_rises_in_sonority():
    """The two tables in the data layer have to agree with each other.

    ``onset_clusters`` is the attested half of the rule and ``sonority_scale``
    is the phonological half; an entry that opens a word without rising (st-,
    šp-, vl-) opens no syllable inside one, so it does not belong in the table.
    Without this check the list would silently drift into a list of word
    beginnings, which is exactly what it must not be.
    """
    from slabika.phonology import ONSET_CLUSTERS, SONORITY, split_into_phonemes

    for cluster in sorted(ONSET_CLUSTERS):
        levels = [SONORITY[phoneme] for phoneme in split_into_phonemes(cluster)]
        assert all(a < b for a, b in zip(levels, levels[1:])), (
            f"{cluster} does not rise: {levels}"
        )


def test_reviewed_morpheme_rules_do_not_overreach_neighbouring_stems():
    assert get_morpheme_parts("mäsožravce") == ["mäso", "žravce"]
    assert get_morpheme_parts("mäsovosť") == ["mäsovosť"]
    assert get_morpheme_parts("tajnostkár") == ["tajnost", "kár"]
    assert get_morpheme_parts("bankár") == ["bankár"]


def test_k_suffix_outranks_43_but_leaves_the_sk_suffix_alone():
    """·k· is a morpheme boundary, so section 3 decides before section 4.3.

    Without it the cluster ntk goes to 4.3, which moves the point left of the
    whole tk- because tk- opens tkáč: klien|tka. A stem ending in a sibilant is
    not this suffix — there the k belongs to ·sk· and reading it as ·k· would
    strand the s.
    """
    assert get_morpheme_parts("klientka") == ["klient", "ka"]
    assert hyphenate("klientka") == "klient·ka"
    assert hyphenate("klientkou") == "klient·kou"
    assert hyphenate("poistky") == "po·ist·ky"
    assert hyphenate("veštkyňa") == "vešt·ky·ňa"

    assert get_morpheme_parts("Benátska") == ["Benát", "ska"]
    assert hyphenate("Benátska") == "Be·nát·ska"
    assert hyphenate("francúzska") == "fran·cúz·ska"
    assert hyphenate("miska") == "mis·ka"


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


def test_no_table_answers_for_whole_words():
    """The engine carries no word list at all.

    ``porota``, ``porkpie``, the thirty-seven lexicalized stems and the
    fifty-two French names of one corpus each had an entry; every one of them
    was either derivable or contradicted by an adjudicated decision, and a
    stored answer hides the next regression behind itself. The module that
    loaded them is gone, so a regression can only be fixed by a rule.
    """
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("slabika.exceptions")
    assert get_syllables("porota") == ["po", "ro", "ta"]
    assert get_syllables("porkpie") == ["pork", "pie"]
