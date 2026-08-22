# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Typographic hyphenation (rozdeľovanie slov).

Syllable boundaries are linguistic facts; line-break points are a typographic
convention layered on top of them. This module applies that convention:
a one-vowel syllable is never left alone at the start of a line nor carried
alone to the next one, non-native graphemes are left untouched, and original
casing is preserved.

The default marker is the middle dot (U+00B7) so that output is unambiguous in
tests; pass ``separator="-"`` or ``separator="\\u00ad"`` for line-breaking use,
or call :func:`break_points` for raw character offsets.
"""

from .exceptions import UNHYPHENATED_FOREIGN_WORDS as _UNHYPHENATED_FOREIGN_WORDS
from .phonology import is_vowel
from .syllabify import get_syllables

#: Letters that the Slovak writing system uses natively.
_NATIVE_SK_LETTERS = set('aáäbcčdďeéfghiíjklĺľmnňoóôprŕsštťuúvxyýzž')

#: Middle dot — the default, unambiguous break marker.
MIDDLE_DOT = '\u00b7'

#: Soft hyphen — what you want when the output goes into rendered text.
SOFT_HYPHEN = '\u00ad'


def break_points(word: str) -> list[int]:
    """
    Return the character offsets at which *word* may be broken across lines.

    Offsets are positions in the original string: a value ``i`` means a break
    is allowed between ``word[i - 1]`` and ``word[i]``. An empty list means the
    word must not be broken.

    >>> break_points("Prekladateľský")
    [3, 6, 8, 11]
    """
    if (
        not word.isalpha()
        or any(char.lower() not in _NATIVE_SK_LETTERS for char in word)
        or word.casefold() in _UNHYPHENATED_FOREIGN_WORDS
    ):
        return []

    parts = get_syllables(word)
    if len(parts) <= 1:
        return []

    # A one-vowel syllable stays on its line at the start of a word and is never
    # carried alone to the next line at its end. Internal one-vowel syllables
    # remain valid break points (Slov·o·si·vo, šesť·u·hol·ník).
    if len(parts) > 1 and len(parts[0]) == 1 and is_vowel(parts[0]):
        parts = [parts[0] + parts[1], *parts[2:]]
    if len(parts) > 1 and len(parts[-1]) == 1 and is_vowel(parts[-1]):
        parts = [*parts[:-2], parts[-2] + parts[-1]]

    if len(parts) <= 1 or ''.join(parts) != word.lower():
        return []

    offsets = []
    pos = 0
    for part in parts[:-1]:
        pos += len(part)
        offsets.append(pos)
    return offsets


def hyphenate(word: str, separator: str = MIDDLE_DOT) -> str:
    """
    Return *word* with *separator* inserted at every valid break point.

    Original casing is preserved. Tokens containing punctuation or non-native
    graphemes, and known unadapted foreign spellings, are returned unchanged.

    >>> hyphenate('Prekladateľský')
    'Pre·kla·da·teľ·ský'
    >>> hyphenate('Prekladateľský', separator='-')
    'Pre-kla-da-teľ-ský'
    """
    offsets = break_points(word)
    if not offsets:
        return word

    out = []
    prev = 0
    for pos in offsets:
        out.append(word[prev:pos])
        prev = pos
    out.append(word[prev:])
    return separator.join(out)
