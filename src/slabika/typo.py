# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Typographic hyphenation (rozdeľovanie slov).

Syllable boundaries are linguistic facts; line-break points follow the separate
written convention codified in PSP, chapter V. Morpheme seams take precedence;
inside a morpheme, the boundary is derived from the number of consonants between
nuclei. A one-letter vowel is not left at either edge by default, non-native
graphemes are left untouched, and original casing is preserved.

Where PSP codifies two equally correct readings of one boundary (``lieta|dlo``
aj ``lietad|lo``), the default output offers the preferred one; ``all_points``
adds the competing point, which is what a line-breaking engine wants and a
human reader does not.

The default marker is the middle dot (U+00B7) so that output is unambiguous in
tests; pass ``separator="-"`` or ``separator="\\u00ad"`` for line-breaking use,
or call :func:`break_points` for raw character offsets.
"""

from .exceptions import (
    FOREIGN_NUCLEUS_SPELLINGS as _FOREIGN_NUCLEUS_SPELLINGS,
    LEXICAL_SYLLABIFICATIONS as _LEXICAL_SYLLABIFICATIONS,
    UNHYPHENATED_FOREIGN_WORDS as _UNHYPHENATED_FOREIGN_WORDS,
)
from .phonology import ATTESTED_ONSETS, is_consonant, is_vowel
from .syllabify import (
    _SK_PREFIXES,
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


def _psp_points(word: str, base: int = 0, mechanical: bool = False) -> list[int]:
    """Apply PSP 2a–2d inside one morphological unit.

    With *mechanical* the cluster rule is read without the opening test of
    section 4.3 — the point falls after the first consonant whatever follows it.
    That is the reading PSP prints as the competing member of a 3.5 doublet
    (``fun|kcia`` beside ``funk|cia``), and nothing else wants it.
    """
    phonemes, offsets, nuclei = _nucleus_spans(word)
    points = []
    for (_, previous_end), (next_start, _) in zip(nuclei, nuclei[1:]):
        between = list(range(previous_end, next_start))
        if not between:
            point = offsets[next_start]          # 2d: genuine hiatus
        elif len(between) == 1:
            point = offsets[between[0]]          # 2a: before the consonant
        else:
            index = 1 if mechanical else _opening_consonant(phonemes, between, next_start)
            point = offsets[between[index]]      # 2b/2c: after the first
        points.append(base + point)
    return points


def _opening_consonant(phonemes: list[str], between: list[int], next_start: int) -> int:
    """Which consonant of *between* starts the next syllable, per section 4.3.

    Two consonants divide between them and there is nothing to decide. Three or
    more leave the first with the preceding syllable and give the rest to the
    next one — but the rule says the rest *opens* that syllable, and a cluster
    only opens a syllable if Slovak words are written with it. ``al|žbetínska``
    hands over ``žb``, which opens no Slovak word before a vowel, so the point
    moves right until what follows it does: ``alž|betínska``. The same reading
    keeps ``ses|tra``, ``pas|tva`` and ``zaj|tra`` exactly where PSP prints them.

    A single consonant always opens a syllable, so the search terminates.
    """
    for index in range(1, len(between)):
        if ''.join(phonemes[between[index]:next_start]) in ATTESTED_ONSETS:
            return index
    return len(between) - 1


def _variant_crosses_seam(left: str, right: str) -> bool:
    """Whether PSP also licenses the syllabic point across this morpheme seam.

    Section 3.5 names three classes and no more: a base ending in a vowel before
    a suffix opening with a cluster, the c/č alternation of -cia adjectives, and
    an unclear cluster. A prefix seam is in none of them — what follows a prefix
    is the base, and the cluster there is the root's own onset, not a suffix that
    happens to be spelled alike. TeX offers nas|kladať; PSP does not, so neither
    do we.
    """
    if left.casefold() in _SK_PREFIXES:
        return False
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


def _collect_points(word: str) -> tuple[set[int], set[int]]:
    """Return (preferred, variant) break offsets for *word*.

    The preferred set holds one point per boundary: a morpheme seam where the
    analysis finds one, otherwise the syllabic point of section 4. The variant
    set holds the competing point that PSP codifies alongside it in the classes
    of section 3.5 — ``lietad|lo`` next to ``lieta|dlo``, ``funk|čný`` next to
    ``funkč|ný``. Both are legal; only the preferred one is shown by default.
    """
    if (
        not word.isalpha()
        or any(char.lower() not in _NATIVE_SK_LETTERS for char in word)
        or word.casefold() in _UNHYPHENATED_FOREIGN_WORDS
    ):
        return set(), set()

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
        return set(points), set()

    if len(_nucleus_spans(word)[2]) <= 1:
        return set(), set()

    parts = get_morpheme_parts(word)
    points: set[int] = set()
    variants: set[int] = set()
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
    raw_points = _psp_points(word, mechanical=True)
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
                variants.add(min(alternatives, key=lambda point: abs(point - seam)))

        # Borrowed nouns in -cia form -čný adjectives by c/č alternation. When
        # the consonant before č remains visible, PSP permits both komerč|ný and
        # komer|čný (likewise funkč|ný and funk|čný).
        if (
            len(left) >= 2
            and left.casefold().endswith('č')
            and is_consonant(left[-2])
            and right.casefold().startswith('n')
        ):
            variants.add(seam - 1)

    # A one-letter vowel is not carried alone to the next line. At the start PSP
    # allows it only in exceptionally narrow columns, so the context-free API
    # follows the normal, conservative form and suppresses that point too.
    if word and is_vowel(word[0]):
        points.discard(1)
        variants.discard(1)
    if word and is_vowel(word[-1]):
        points.discard(len(word) - 1)
        variants.discard(len(word) - 1)

    return points, variants - points


def break_points(word: str, all_points: bool = False) -> list[int]:
    """
    Return the character offsets at which *word* may be broken across lines.

    Offsets are positions in the original string: a value ``i`` means a break
    is allowed between ``word[i - 1]`` and ``word[i]``. An empty list means the
    word must not be broken.

    By default one point per boundary is returned — the reading a human expects.
    Pass ``all_points=True`` to also get the competing points PSP codifies as
    equally correct; a typesetter wants those, because every extra opportunity
    is one more place a line may be broken.

    >>> break_points("Prekladateľský")
    [3, 6, 8, 11]
    >>> break_points("lietadlo")
    [3, 5]
    >>> break_points("lietadlo", all_points=True)
    [3, 5, 6]
    """
    preferred, variants = _collect_points(word)
    return sorted(preferred | variants) if all_points else sorted(preferred)


def divisions(word: str) -> list[str]:
    """
    Return every permissible division of *word*, written out with a hyphen.

    >>> divisions("lietadlo")
    ['lie-tadlo', 'lieta-dlo', 'lietad-lo']
    """
    return [
        f"{word[:point]}-{word[point:]}"
        for point in break_points(word, all_points=True)
    ]


def hyphenate(word: str, separator: str = MIDDLE_DOT, all_points: bool = False) -> str:
    """
    Return *word* with *separator* inserted at every valid break point.

    Original casing is preserved. Tokens containing punctuation or non-native
    graphemes, and known unadapted foreign spellings, are returned unchanged.

    >>> hyphenate('Prekladateľský')
    'Pre·kla·da·teľ·ský'
    >>> hyphenate('Prekladateľský', separator='-')
    'Pre-kla-da-teľ-ský'
    >>> hyphenate('lietadlo')
    'lie·ta·dlo'
    >>> hyphenate('lietadlo', all_points=True)
    'lie·ta·d·lo'
    """
    offsets = break_points(word, all_points)
    if not offsets:
        return word

    out = []
    prev = 0
    for pos in offsets:
        out.append(word[prev:pos])
        prev = pos
    out.append(word[prev:])
    return separator.join(out)
