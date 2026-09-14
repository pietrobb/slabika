# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Vendored from the sibling Sapfo project (sapfo/core/phonology.py) for build-time use
# by tools/build_composita.py only. Not part of the distributed package.
"""
Fonológia - Phonology module for SAPFO.

Complete classification of Slovak phonemes (foném) based on their properties,
as specified in Chapter 2 of the SAPFO specification (Dvončová 1980, Horecký 1977).

Phoneme properties are used by the morphology module for:
- Root alternations during declension/conjugation
- Vowel insertion (vkladanie vokálu) in genitive plural
- Rhythmic law (rytmický zákon)
- Consonant voicing assimilation
"""

# =============================================================================
# VOWELS (SAMOHLÁSKY / VOKÁLY)
# =============================================================================

SHORT_VOWELS = set('aeiouy')
LONG_VOWELS = {'á', 'é', 'í', 'ó', 'ú', 'ý'}
DIPHTHONGS = {'ia', 'ie', 'iu', 'ô'}  # ô = uo

ALL_VOWELS = SHORT_VOWELS | LONG_VOWELS
ALL_VOWEL_GRAPHEMES = ALL_VOWELS | DIPHTHONGS

# By resonance space (podľa rezonančných priestorov)
BACK_VOWELS = {'o', 'ó', 'u', 'ú'}        # zadné (velárne)
CENTRAL_VOWELS = {'a', 'á'}                # stredné
FRONT_VOWELS = {'e', 'é', 'i', 'í', 'y', 'ý'}  # predné (palatálne)

# By height (podľa výšky)
HIGH_VOWELS = {'i', 'í', 'y', 'ý', 'u', 'ú'}
MID_VOWELS = {'e', 'é', 'o', 'ó'}
LOW_VOWELS = {'a', 'á', 'ä'}

# By lip rounding (podľa zaokrúhlenia pier)
ROUNDED_VOWELS = {'u', 'ú', 'o', 'ó', 'y', 'ý'}  # labializované
UNROUNDED_VOWELS = {'i', 'í', 'e', 'é', 'a', 'á'}  # nelabializované

# By openness (podľa otvorenosti pier)
OPEN_VOWELS = {'a', 'á'}
HALF_OPEN_VOWELS = {'e', 'é', 'o', 'ó'}  # v is semivowel, listed separately
CLOSED_VOWELS = {'i', 'í', 'y', 'ý', 'u', 'ú'}

# Vowel length pairs (for alternations: predĺženie ≤ / skrátenie ≥)
VOWEL_LENGTH_PAIRS = {
    'a': 'á', 'á': 'a',
    'e': 'é', 'é': 'e',
    'i': 'í', 'í': 'i',
    'o': 'ó', 'ó': 'o',
    'u': 'ú', 'ú': 'u',
    'y': 'ý', 'ý': 'y',
}

LENGTHEN_VOWEL = {
    'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú', 'y': 'ý',
}

SHORTEN_VOWEL = {
    'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ý': 'y',
}

# =============================================================================
# SEMIVOWELS (POLOVOKÁLY)
# =============================================================================

SEMIVOWELS = {'v'}  # v functions as semivowel in some contexts

# =============================================================================
# SONORITY HIERARCHY
# =============================================================================

SONORY = {'r', 'l', 'ŕ', 'ĺ'}  # sonóry - syllabic consonants in Slovak

# =============================================================================
# CONSONANTS (SPOLUHLÁSKY / KONSONANTY)
# =============================================================================

# By length (podľa dĺžky)
SHORT_CONSONANTS = {'r', 'l'}
LONG_CONSONANTS = {'ŕ', 'ĺ'}

# By hardness (podľa tvrdosti) - crucial for spelling rules (i/y after consonants)
HARD_CONSONANTS = {'h', 'ch', 'k', 'g', 'd', 't', 'n', 'l'}
SOFT_CONSONANTS = {'c', 'č', 'dz', 'dž', 'f', 'j', 'š', 'ž', 'ť', 'ď', 'ň', 'ľ'}
AMBIGUOUS_CONSONANTS = {'v', 'm', 'r', 'b', 'p', 's', 'ŕ', 'z'}  # obojaké

# By voicing (podľa účasti hlasu)
VOICED_CONSONANTS = {'b', 'd', 'ď', 'g', 'dz', 'dž', 'z', 'ž'}
VOICELESS_CONSONANTS = {'p', 't', 'ť', 'k', 'c', 'č', 's', 'š'}

# Voiced-voiceless pairs (párové)
VOICING_PAIRS = {
    'b': 'p', 'p': 'b',
    'd': 't', 't': 'd',
    'ď': 'ť', 'ť': 'ď',
    'g': 'k', 'k': 'g',
    'dz': 'c', 'c': 'dz',
    'dž': 'č', 'č': 'dž',
    'z': 's', 's': 'z',
    'ž': 'š', 'š': 'ž',
}

UNPAIRED_CONSONANTS = {'r', 'l', 'm', 'n', 'ň', 'j'}  # nepárové

# By place of articulation (podľa miesta artikulácie)
BILABIAL = {'p', 'b', 'm'}                       # pernoperné (bilabiálne)
LABIODENTAL = {'f', 'v'}                          # pernozubné (labiodentálne)
PREALVEOLAR = {'t', 'd', 'n', 's', 'z', 'c', 'dz'}  # predoďasnové
POSTALVEOLAR = {'š', 'ž', 'č', 'dž', 'r', 'ŕ', 'l', 'ĺ'}  # zadoďasnové
ALVEOPALATAL = {'ť', 'ď', 'ň', 'ľ'}             # ďasnovopodnebnné
PALATAL = {'j'}                                    # tvrdopodnebnné
VELAR = {'k', 'g', 'ch'}                          # mäkkopodnebnné
LARYNGEAL = {'h'}                                  # hrtanové

# By manner of articulation (podľa sluchového dojmu)
PLOSIVES = {'p', 'b', 'm', 't', 'd', 'n', 'ť', 'ď', 'ň', 'k', 'g'}  # explozívne
AFFRICATES = {'c', 'č', 'dz', 'dž'}                                    # afrikáty
FRICATIVES = {'s', 'z', 'š', 'ž', 'h', 'ch', 'f', 'v', 'ŕ', 'l', 'ĺ', 'ľ'}  # frikatívy
SONORITY_CONSONANTS = {'m', 'n', 'ň', 'j', 'r', 'l', 'ĺ', 'ľ'}  # sonóry (consonant)
LIQUIDS = {'r', 'l', 'ŕ', 'ĺ'}                    # likvidy (plynné)
VIBRANTS = {'r', 'ŕ'}                              # vibranty

ALL_CONSONANTS = (
    VOICED_CONSONANTS | VOICELESS_CONSONANTS | UNPAIRED_CONSONANTS |
    {'h', 'ch', 'f', 'v', 'ľ', 'ĺ', 'ŕ'}
)

# =============================================================================
# PALATALIZATION PAIRS (for lingválna/dorzálna alternácia *)
# =============================================================================

# Consonant softening (zmäkčovanie) - used in declension/derivation
PALATALIZATION = {
    'k': 'č',   'č': 'k',
    'g': 'ž',   'ž': 'g',
    'ch': 'š',  'š': 'ch',
    'h': 'ž',
    'c': 'č',
    'd': 'ď',   'ď': 'd',
    't': 'ť',   'ť': 't',
    'n': 'ň',   'ň': 'n',
    'l': 'ľ',   'ľ': 'l',
    'r': 'r',  # r doesn't change
}

# Specific consonant alternation in verb stems (lingválna/dorzálna)
LINGUAL_DORSAL = {
    'k': 'c',  'c': 'k',    # piecť/pekú
    'g': 'dz', 'dz': 'g',
    'ch': 's',  's': 'ch',   # not always bidirectional
    'h': 'z',  'z': 'h',
    'sk': 'šť', 'šť': 'sk',
    'st': 'šť',
}

# =============================================================================
# ALL PHONEMES SET
# =============================================================================

ALL_PHONEMES = ALL_VOWELS | ALL_CONSONANTS | DIPHTHONGS | SEMIVOWELS


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
    if 'ŕ' in s or 'ĺ' in s:
        return True
    return False


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
        # Try trigraph first: dž
        if i + 2 < len(w) and w[i:i+2] == 'dž':
            phonemes.append('dž')
            i += 2
            continue
        # Try digraphs: ch, dz
        if i + 1 < len(w):
            digraph = w[i:i+2]
            if digraph == 'ch':
                phonemes.append('ch')
                i += 2
                continue
            if digraph == 'dz':
                phonemes.append('dz')
                i += 2
                continue
            # Diphthongs: ia, ie, iu
            if digraph in ('ia', 'ie', 'iu'):
                phonemes.append(digraph)
                i += 2
                continue
        phonemes.append(w[i])
        i += 1
    return phonemes


# Slovak productive prefixes — longest first (order matters for matching)
