# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Phonological inventory of Slovak.

Complete classification of Slovak phonemes by their articulatory and
distributional properties: vowel quantity and quality, diphthongs, syllabic
consonants, hardness, voicing pairs, place and manner of articulation,
palatalization and lingual-dorsal alternations.

This is the base layer of the package. Everything else — syllabification,
typographic hyphenation, pattern generation — is derived from it, and this
module imports nothing from the package itself.

The inventory is not written out here. It is a table of linguistic facts, so it
lives in the data layer, in ``data/phonology.json``, and this module reads it
and derives the working sets from it. That keeps the boundary between facts and
code where the licensing already puts it: the data is `CC0-1.0 OR MIT`, this
module is `Apache-2.0 OR MIT` like the rest of the code. Anyone who wants the
inventory takes the JSON and no code obligations with it.

The classification follows Emil Páleš, "Sapfo — parafrázovač slovenčiny"
(VEDA, Bratislava, 1994, ISBN 80-224-0109-9), ch. 2 "Fonológia", who attributes it to
J. Dvončová (1980) and J. Horecký (1977). See LICENSING.md §5.
"""

import json
from importlib.resources import files

_INVENTORY = json.loads(
    (files(__package__) / "data" / "phonology.json").read_text(encoding="utf-8")
)

_VOWELS = _INVENTORY["vowels"]
_CONSONANTS = _INVENTORY["consonants"]
_ALTERNATIONS = _INVENTORY["alternations"]

#: Slovak names of the classes below, as given in the descriptive literature.
TERMINOLOGY = _INVENTORY["terminology"]

# =============================================================================
# VOWELS (SAMOHLÁSKY / VOKÁLY)
# =============================================================================

SHORT_VOWELS = set(_VOWELS["short"])
LONG_VOWELS = set(_VOWELS["long"])
DIPHTHONGS = set(_VOWELS["diphthongs"])  # ô = uo

ALL_VOWELS = SHORT_VOWELS | LONG_VOWELS
ALL_VOWEL_GRAPHEMES = ALL_VOWELS | DIPHTHONGS

# By resonance space (podľa rezonančných priestorov)
BACK_VOWELS = set(_VOWELS["by_resonance"]["back"])
CENTRAL_VOWELS = set(_VOWELS["by_resonance"]["central"])
FRONT_VOWELS = set(_VOWELS["by_resonance"]["front"])

# By height (podľa výšky)
HIGH_VOWELS = set(_VOWELS["by_height"]["high"])
MID_VOWELS = set(_VOWELS["by_height"]["mid"])
LOW_VOWELS = set(_VOWELS["by_height"]["low"])

# By lip rounding (podľa zaokrúhlenia pier)
ROUNDED_VOWELS = set(_VOWELS["by_rounding"]["rounded"])
UNROUNDED_VOWELS = set(_VOWELS["by_rounding"]["unrounded"])

# By openness (podľa otvorenosti pier)
OPEN_VOWELS = set(_VOWELS["by_openness"]["open"])
HALF_OPEN_VOWELS = set(_VOWELS["by_openness"]["half_open"])  # v is a semivowel, listed apart
CLOSED_VOWELS = set(_VOWELS["by_openness"]["closed"])

# Vowel length alternations (predĺženie ≤ / skrátenie ≥)
LENGTHEN_VOWEL = dict(_VOWELS["lengthening"])
SHORTEN_VOWEL = {long: short for short, long in LENGTHEN_VOWEL.items()}
VOWEL_LENGTH_PAIRS = {**LENGTHEN_VOWEL, **SHORTEN_VOWEL}

# =============================================================================
# SEMIVOWELS (POLOVOKÁLY)
# =============================================================================

SEMIVOWELS = set(_INVENTORY["semivowels"])  # v functions as a semivowel in some contexts

# =============================================================================
# SONORITY HIERARCHY
# =============================================================================

SONORY = set(_CONSONANTS["syllabic"])  # sonóry - syllabic consonants in Slovak

#: Sonority of each consonant: the index of the tier it belongs to, counting
#: from the least sonorous. A syllable boundary falls where sonority stops
#: falling, so this is what decides which consonants of a cluster open the next
#: syllable and which close the one before it.
SONORITY = {
    phoneme: rank
    for rank, tier in enumerate(_INVENTORY["sonority_scale"].values())
    for phoneme in tier
}

#: Consonant clusters that may open a syllable — attested word-initially and
#: rising in sonority. See :mod:`slabika.syllabify`.
ONSET_CLUSTERS = frozenset(_INVENTORY["onset_clusters"])

#: Consonant clusters a written Slovak word opens with before a vowel — what a
#: syllable *can* begin with, as opposed to what wins the sonority contest word
#: -internally. PSP 4.3 hands the tail of a three-consonant cluster to the next
#: syllable, which presupposes the tail is one of these. See
#: :func:`slabika.typo.break_points`.
ATTESTED_ONSETS = frozenset(_INVENTORY["attested_onsets"])

# =============================================================================
# CONSONANTS (SPOLUHLÁSKY / KONSONANTY)
# =============================================================================

# By length (podľa dĺžky)
SHORT_CONSONANTS = set(_CONSONANTS["short"])
LONG_CONSONANTS = set(_CONSONANTS["long"])

# By hardness (podľa tvrdosti) - crucial for spelling rules (i/y after consonants)
HARD_CONSONANTS = set(_CONSONANTS["by_hardness"]["hard"])
SOFT_CONSONANTS = set(_CONSONANTS["by_hardness"]["soft"])
AMBIGUOUS_CONSONANTS = set(_CONSONANTS["by_hardness"]["ambiguous"])  # obojaké

# By voicing (podľa účasti hlasu). The inventory lists each pair once, voiced
# first; both directions and both classes follow from that.
VOICED_CONSONANTS = set(_CONSONANTS["voicing_pairs"])
VOICELESS_CONSONANTS = set(_CONSONANTS["voicing_pairs"].values())
VOICING_PAIRS = {
    **_CONSONANTS["voicing_pairs"],
    **{voiceless: voiced for voiced, voiceless in _CONSONANTS["voicing_pairs"].items()},
}

UNPAIRED_CONSONANTS = set(_CONSONANTS["unpaired"])  # nepárové

# By place of articulation (podľa miesta artikulácie)
_PLACE = _CONSONANTS["by_place"]
BILABIAL = set(_PLACE["bilabial"])
LABIODENTAL = set(_PLACE["labiodental"])
PREALVEOLAR = set(_PLACE["prealveolar"])
POSTALVEOLAR = set(_PLACE["postalveolar"])
ALVEOPALATAL = set(_PLACE["alveopalatal"])
PALATAL = set(_PLACE["palatal"])
VELAR = set(_PLACE["velar"])
LARYNGEAL = set(_PLACE["laryngeal"])

# By manner of articulation (podľa sluchového dojmu)
_MANNER = _CONSONANTS["by_manner"]
PLOSIVES = set(_MANNER["plosive"])
AFFRICATES = set(_MANNER["affricate"])
FRICATIVES = set(_MANNER["fricative"])
SONORITY_CONSONANTS = set(_MANNER["sonorant"])
LIQUIDS = set(_MANNER["liquid"])
VIBRANTS = set(_MANNER["vibrant"])

# Every consonant is articulated somewhere, so the places exhaust the class.
ALL_CONSONANTS = set().union(*(set(members) for members in _PLACE.values()))

# =============================================================================
# PALATALIZATION PAIRS (for lingválna/dorzálna alternácia *)
# =============================================================================

# Consonant softening (zmäkčovanie) - used in declension/derivation
PALATALIZATION = dict(_ALTERNATIONS["palatalization"])

# Specific consonant alternation in verb stems (lingválna/dorzálna)
LINGUAL_DORSAL = dict(_ALTERNATIONS["lingual_dorsal"])

# =============================================================================
# ALL PHONEMES SET
# =============================================================================

ALL_PHONEMES = ALL_VOWELS | ALL_CONSONANTS | DIPHTHONGS | SEMIVOWELS

#: Letters the Slovak writing system uses natively. A property of the
#: orthography rather than of the phoneme inventory — see the comment beside it
#: in the data file. Anything outside this set is a foreign spelling, and the
#: rules may not be applied to it without knowing its pronunciation (PSP §5.4).
NATIVE_LETTERS = frozenset(_INVENTORY["native_letters"])

#: Non-Slovak letters that reliably stand for a consonant, so a syllable count
#: over them is sound even though the spelling is foreign. See the data file.
TOLERATED_FOREIGN_CONSONANTS = frozenset(_INVENTORY["tolerated_foreign_consonants"])

#: Foreign vowel letters whose pronunciation is known — one sound each, so
#: PSP §5.4 has nothing to forbid and the rules may be applied. See the data file.
PRONOUNCED_FOREIGN_VOWELS = frozenset(_INVENTORY["pronounced_foreign_vowels"])

#: The same for consonants, each mapped to the native letter whose slot it fills
#: in a cluster: ř behaves as r, so dob·ře divides where dob·re would.
PRONOUNCED_FOREIGN_CONSONANTS = dict(_INVENTORY["pronounced_foreign_consonants"])

#: Letters that carry a syllable nucleus on their own — the Slovak vowels plus
#: the foreign vowel letters above.
VOWEL_LETTERS = ALL_VOWELS | PRONOUNCED_FOREIGN_VOWELS

#: What :func:`slabika.syllables` will analyse: Slovak spelling, plus the
#: foreign letters above. Everything else is refused rather than guessed at.
ANALYSABLE_LETTERS = (
    NATIVE_LETTERS
    | TOLERATED_FOREIGN_CONSONANTS
    | PRONOUNCED_FOREIGN_VOWELS
    | frozenset(PRONOUNCED_FOREIGN_CONSONANTS)
)

#: What :func:`slabika.hyphenate` will divide: Slovak spelling plus the letters
#: whose pronunciation is known. q and w are missing on purpose — a syllable
#: count over them is sound, but a line break has to be defensible letter by
#: letter and their sound value in Slovak text is not.
HYPHENATABLE_LETTERS = (
    NATIVE_LETTERS | PRONOUNCED_FOREIGN_VOWELS | frozenset(PRONOUNCED_FOREIGN_CONSONANTS)
)

_FOREIGN_TWINS = str.maketrans(PRONOUNCED_FOREIGN_CONSONANTS)


def native_spelling(cluster: str) -> str:
    """Rewrite foreign consonant letters as the native letter they behave like.

    Only for looking a cluster up in the onset tables: those list what Slovak
    words are written with, and ř is not one of them although the cluster it
    forms behaves exactly as the one with r does.
    """
    return cluster.translate(_FOREIGN_TWINS)

# Multi-character graphemes, longest-match first, for segmentation.
_DIGRAPHS = tuple(_INVENTORY["digraphs"])
_TWO_CHAR_DIPHTHONGS = tuple(d for d in _VOWELS["diphthongs"] if len(d) == 2)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_vowel(char: str) -> bool:
    """Check if character is a vowel letter (short, long, or foreign).

    A question about the writing system, not about the Slovak inventory: ě and ů
    are vowels wherever they are written. Use :data:`ALL_VOWELS` directly where
    only the Slovak inventory counts.
    """
    return char.lower() in VOWEL_LETTERS


def is_short_vowel(char: str) -> bool:
    return char.lower() in SHORT_VOWELS


def is_long_vowel(char: str) -> bool:
    return char.lower() in LONG_VOWELS


def is_diphthong(s: str) -> bool:
    """Check if string is a diphthong."""
    return s.lower() in DIPHTHONGS


def is_consonant(char: str) -> bool:
    return char.lower() in ALL_CONSONANTS or char.lower() in PRONOUNCED_FOREIGN_CONSONANTS


def is_hard_consonant(char: str) -> bool:
    return char.lower() in HARD_CONSONANTS


def is_soft_consonant(char: str) -> bool:
    return char.lower() in SOFT_CONSONANTS


def is_voiced(char: str) -> bool:
    return char.lower() in VOICED_CONSONANTS


def is_voiceless(char: str) -> bool:
    return char.lower() in VOICELESS_CONSONANTS


def voice_pair(char: str) -> str | None:
    """Get the voicing pair of a consonant."""
    return VOICING_PAIRS.get(char.lower())


def lengthen(vowel: str) -> str:
    """Lengthen a short vowel (predĺženie ≤)."""
    return LENGTHEN_VOWEL.get(vowel, vowel)


def shorten(vowel: str) -> str:
    """Shorten a long vowel (skrátenie ≥)."""
    return SHORTEN_VOWEL.get(vowel, vowel)


def is_long_syllable(syllable: str) -> bool:
    """Check if a syllable contains a long vowel or diphthong (for rhythmic law)."""
    s = syllable.lower()
    for d in DIPHTHONGS:
        if d in s:
            return True
    for v in LONG_VOWELS:
        if v in s:
            return True
    return any(c in s for c in LONG_CONSONANTS)


def palatalize(consonant: str) -> str | None:
    """Get palatalized form of a consonant."""
    return PALATALIZATION.get(consonant.lower())


def lingual_dorsal_alt(consonant: str) -> str | None:
    """Get lingválna/dorzálna alternation of a consonant."""
    return LINGUAL_DORSAL.get(consonant.lower())


def split_into_phonemes(word: str) -> list[str]:
    """Split a word into individual phonemes, handling digraphs (ch, dz, dž)."""
    phonemes = []
    i = 0
    w = word.lower()
    while i < len(w):
        pair = w[i:i + 2]
        # Digraphs first (dž before dz), then the two-character diphthongs.
        if pair in _DIGRAPHS or pair in _TWO_CHAR_DIPHTHONGS:
            phonemes.append(pair)
            i += 2
            continue
        phonemes.append(w[i])
        i += 1
    return phonemes
