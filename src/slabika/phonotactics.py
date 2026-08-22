# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Phonotactics and prosody: well-formedness, the rhythmic law, and preposition
vocalization.

These sit above syllabification because each of them needs to know where the
syllable boundaries fall.
"""

from .phonology import (
    ALL_VOWELS,
    DIPHTHONGS,
    SHORTEN_VOWEL,
    SONORY,
    is_consonant,
    is_long_syllable,
    split_into_phonemes,
)
from .syllabify import get_syllables


def check_rhythmic_law(stem: str, suffix: str) -> bool:
    """
    Check if the rhythmic law (rytmický zákon) applies.
    In Slovak, two consecutive long syllables are generally not allowed.
    Returns True if there is a rhythmic law violation.
    """
    combined = stem + suffix
    syllables = get_syllables(combined)
    for i in range(len(syllables) - 1):
        if is_long_syllable(syllables[i]) and is_long_syllable(syllables[i + 1]):
            return True
    return False


def apply_rhythmic_law(suffix: str) -> str:
    """
    Apply rhythmic law shortening to a suffix.
    If the suffix contains a long vowel, shorten it.
    """
    result = []
    for char in suffix:
        if char in SHORTEN_VOWEL:
            result.append(SHORTEN_VOWEL[char])
        else:
            result.append(char)
    return ''.join(result)


def ends_with_two_consonants(stem: str) -> bool:
    """Check if stem ends with a cluster of two consonants.

    Syllabic ŕ/ĺ, and r/l between consonants, form nuclei rather than clusters.
    """
    phonemes = split_into_phonemes(stem)
    if len(phonemes) < 2:
        return False
    # ŕ/ĺ are syllabic (vowel-like) — kŕm is one syllable, not a cluster
    _SYLLABIC = {'ŕ', 'ĺ'}
    last = phonemes[-1]
    prev = phonemes[-2]
    short_syllabic = (
        prev in {'r', 'l'}
        and len(phonemes) >= 3
        and is_consonant(phonemes[-3])
    )
    return (is_consonant(last) and last not in _SYLLABIC
            and is_consonant(prev) and prev not in _SYLLABIC
            and not short_syllabic)


# =============================================================================
# PHONOTACTIC VALIDATION
# =============================================================================

# Characters that belong to the Slovak alphabet (including diacritics)
_SLOVAK_CHARS = set(
    'aáäbcčdďeéfghchiíjklĺľmnňoóôpqrŕsštťuúvwxyýzž'
)


def is_phonotactically_valid(word: str) -> bool:
    """Check if a word could be a valid Slovak word based on phonotactics.

    Uses phoneme-level analysis to reject strings that violate basic
    Slovak phonotactic constraints. Designed for filtering out garbage
    strings before morphological guessing is attempted.

    Rules:
        1. Word must contain at least one Slovak letter.
        2. Word must contain at least one vowel or syllabic consonant (nucleus).
        3. Maximum 4 consecutive consonants (Slovak allows "vstrc" but not 5+).
        4. get_syllables() must produce at least 1 syllable with a nucleus.

    Returns True if the word passes all checks, False otherwise.
    """
    if not word:
        return False

    wl = word.lower()

    # Rule 1: must contain at least one Slovak letter
    if not any(c in _SLOVAK_CHARS for c in wl):
        return False

    phonemes = split_into_phonemes(wl)
    if not phonemes:
        return False

    # Rule 2: must have at least one vowel or syllabic consonant
    has_nucleus = any(
        ph in ALL_VOWELS or ph in DIPHTHONGS or ph in SONORY
        for ph in phonemes
    )
    if not has_nucleus:
        return False

    # Rule 3: max 4 consecutive consonants
    consecutive_consonants = 0
    for ph in phonemes:
        if is_consonant(ph) and ph not in SONORY:
            consecutive_consonants += 1
            if consecutive_consonants > 4:
                return False
        else:
            consecutive_consonants = 0

    # Rule 4: get_syllables must produce at least 1 real syllable
    syllables = get_syllables(wl)
    if not syllables:
        return False

    return True


# =============================================================================
# PREPOSITION VOCALIZATION (vokalizácia predložiek)
# =============================================================================

# Monosyllabic prepositions that vocalize before certain consonant clusters.
# v → vo, s → so, z → zo, k → ku
# Rules based on standard Slovak phonotactics.

# For each base preposition: the vocalized form, and the set of initial
# phonemes of the *following* word that trigger vocalization.
_VOCALIZATION_RULES: dict[str, tuple[str, set[str]]] = {
    'v': ('vo', {'v', 'f'}),
    's': ('so', {'s', 'z', 'š', 'ž'}),
    'z': ('zo', {'z', 's', 'š', 'ž'}),
    'k': ('ku', {'k', 'g'}),
}

# Also accept the vocalized forms mapping back to their base.
_VOCALIZED_TO_BASE: dict[str, str] = {
    'vo': 'v', 'so': 's', 'zo': 'z', 'ku': 'k',
}


def check_preposition_form(prep: str, next_word: str) -> bool:
    """Check if the preposition form is phonologically valid before *next_word*.

    Returns True if the form is acceptable, False if vocalization rules
    are violated (e.g. "v vozík" should be "vo vozík").

    Rules:
        - "v"  must be "vo"  before words starting with v, f
        - "s"  must be "so"  before words starting with s, z, š, ž
        - "z"  must be "zo"  before words starting with z, s, š, ž
        - "k"  must be "ku"  before words starting with k, g
        - Vocalized forms ("vo", "so", "zo", "ku") are always accepted.
        - Unknown prepositions are always accepted (permissive).
    """
    if not prep or not next_word:
        return True

    prep_low = prep.lower()
    next_low = next_word.lower()

    # Get the first phoneme of the next word
    phonemes = split_into_phonemes(next_low)
    if not phonemes:
        return True
    first_phoneme = phonemes[0]

    # Check if this is a base form that should be vocalized
    rule = _VOCALIZATION_RULES.get(prep_low)
    if rule is not None:
        _vocalized, triggers = rule
        if first_phoneme in triggers:
            # Base form used where vocalized form is required
            return False

    # Vocalized forms are always OK (vo, so, zo, ku)
    # Other prepositions (do, na, pri, ...) are always OK
    return True
