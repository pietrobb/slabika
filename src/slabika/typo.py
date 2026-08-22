# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Typographic hyphenation (rozdeľovanie slov).

Syllable boundaries are linguistic facts; line-break points follow the separate
written convention codified in PSP, chapter V. Morpheme seams take precedence;
inside a morpheme, the boundary is derived from the number of consonants between
nuclei. A one-letter vowel is not left at either edge by default, non-native
graphemes are left untouched, and original casing is preserved.

The default marker is the middle dot (U+00B7) so that output is unambiguous in
tests; pass ``separator="-"`` or ``separator="\\u00ad"`` for line-breaking use,
or call :func:`break_points` for raw character offsets.
"""

from .exceptions import (
    FOREIGN_NUCLEUS_SPELLINGS as _FOREIGN_NUCLEUS_SPELLINGS,
    LEXICAL_SYLLABIFICATIONS as _LEXICAL_SYLLABIFICATIONS,
    UNHYPHENATED_FOREIGN_WORDS as _UNHYPHENATED_FOREIGN_WORDS,
)
from .phonology import is_consonant, is_vowel
from .syllabify import (
    _SK_SUFFIXES_CONS,
    get_morpheme_parts,
    phoneme_layout,
)

#: Letters that the Slovak writing system uses natively.
_NATIVE_SK_LETTERS = set('aáäbcčdďeéfghiíjklĺľmnňoóôprŕsštťuúvxyýzž')

#: Middle dot — the default, unambiguous break marker.
MIDDLE_DOT = '\u00b7'

#: Soft hyphen — what you want when the output goes into rendered text.
SOFT_HYPHEN = '\u00ad'


def _nucleus_spans(word: str) -> tuple[list[str], list[int], list[tuple[int, int]]]:
    """Return phonemes, offsets, and logical nucleus spans for PSP division."""
    phonemes, offsets, nuclei = phoneme_layout(word)
    spans = [(index, index + 1) for index in nuclei]
    wl = word.casefold()

    for stem, spelling in _FOREIGN_NUCLEUS_SPELLINGS.items():
        if not wl.startswith(stem):
            continue
        char_start = wl.find(spelling)
        char_end = char_start + len(spelling)
        members = [
            index for index in nuclei
            if char_start <= offsets[index] < char_end
        ]
        if len(members) < 2:
            continue
        first, last = members[0], members[-1]
        spans = [span for span in spans if span[0] not in members]
        spans.append((first, last + 1))
        spans.sort()

    return phonemes, offsets, spans


def _psp_points(word: str, base: int = 0) -> list[int]:
    """Apply PSP 2a–2d inside one morphological unit."""
    _, offsets, nuclei = _nucleus_spans(word)
    points = []
    for (_, previous_end), (next_start, _) in zip(nuclei, nuclei[1:]):
        between = list(range(previous_end, next_start))
        if not between:
            point = offsets[next_start]          # 2d: genuine hiatus
        elif len(between) == 1:
            point = offsets[between[0]]          # 2a: before the consonant
        else:
            point = offsets[between[1]]          # 2b/2c: after the first
        points.append(base + point)
    return points


def _variant_crosses_seam(left: str, right: str) -> bool:
    """Whether PSP also licenses the syllabic point across this morpheme seam."""
    _, _, right_nuclei = _nucleus_spans(right)
    initial_cluster = right_nuclei[0][0] if right_nuclei else 0
    leftl, rightl = left.casefold(), right.casefold()
    suffix_cluster = any(rightl.startswith(suffix) for suffix in _SK_SUFFIXES_CONS)
    unclear_compound = leftl == 'jedno' and rightl.startswith('tl')
    return (
        bool(left)
        and is_vowel(left[-1])
        and initial_cluster >= 2
        and (suffix_cluster or unclear_compound)
    ) or rightl.startswith('cia')


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

    lexical = _LEXICAL_SYLLABIFICATIONS.get(word.casefold())
    if lexical is not None:
        points, pos = [], 0
        for part in lexical[:-1]:
            pos += len(part)
            points.append(pos)
        if word and is_vowel(word[0]) and points[:1] == [1]:
            points.pop(0)
        if word and is_vowel(word[-1]) and points[-1:] == [len(word) - 1]:
            points.pop()
        return points

    if len(_nucleus_spans(word)[2]) <= 1:
        return []

    parts = get_morpheme_parts(word)
    points: set[int] = set()
    seams: list[tuple[int, str, str]] = []
    pos = 0
    for index, part in enumerate(parts):
        points.update(_psp_points(part, pos))
        pos += len(part)
        if index < len(parts) - 1:
            points.add(pos)
            seams.append((pos, part, parts[index + 1]))

    # PSP explicitly permits both the morphemic point and the competing
    # syllabic point in these structural classes. The raw whole-word rule gives
    # that second point; only a consonant-only shift across the seam is admitted.
    raw_points = _psp_points(word)
    for seam, left, right in seams:
        if len(right) > 1 and is_vowel(right[0]):
            points.discard(seam + 1)

        if _variant_crosses_seam(left, right):
            alternatives = [
                point for point in raw_points
                if point != seam
                and all(is_consonant(char) for char in word[min(point, seam):max(point, seam)])
            ]
            if alternatives:
                points.add(min(alternatives, key=lambda point: abs(point - seam)))

        # Borrowed nouns in -cia form -čný adjectives by c/č alternation. When
        # the consonant before č remains visible, PSP permits both komerč|ný and
        # komer|čný (likewise funkč|ný and funk|čný).
        if (
            len(left) >= 2
            and left.casefold().endswith('č')
            and is_consonant(left[-2])
            and right.casefold().startswith('n')
        ):
            points.add(seam - 1)

    # A one-letter vowel is not carried alone to the next line. At the start PSP
    # allows it only in exceptionally narrow columns, so the context-free API
    # follows the normal, conservative form and suppresses that point too.
    if word and is_vowel(word[0]):
        points.discard(1)
    if word and is_vowel(word[-1]):
        points.discard(len(word) - 1)

    return sorted(points)


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
