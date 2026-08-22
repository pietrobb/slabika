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

# Multi-character graphemes, longest-match first, for segmentation.
_DIGRAPHS = tuple(_INVENTORY["digraphs"])
_TWO_CHAR_DIPHTHONGS = tuple(d for d in _VOWELS["diphthongs"] if len(d) == 2)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_vowel(char: str) -> bool:
    """Check if character is a vowel (short or long)."""
    return char.lower() in ALL_VOWELS


def is_short_vowel(char: str) -> bool:
    return char.lower() in SHORT_VOWELS


def is_long_vowel(char: str) -> bool:
    return char.lower() in LONG_VOWELS


def is_diphthong(s: str) -> bool:
    """Check if string is a diphthong."""
    return s.lower() in DIPHTHONGS


def is_consonant(char: str) -> bool:
    return char.lower() in ALL_CONSONANTS


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
