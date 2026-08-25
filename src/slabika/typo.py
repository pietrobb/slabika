# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Typographic hyphenation (rozdeľovanie slov).

Syllable boundaries are linguistic facts; line-break points follow the separate
written convention codified in PSP, chapter V. Morpheme seams take precedence;
inside a morpheme, the boundary is derived from the number of consonants between
nuclei. A one-letter vowel is not left at either edge by default, non-native
graphemes are left untouched, and original casing is preserved.

PSP grade their own rules (section 9), and the API keeps the three grades apart.
The default output is the basic reading. ``all_points`` adds the codified
doublets of section 3.5 (``lieta|dlo`` aj ``lietad|lo``). ``contextual`` adds
what the norm permits but advises against — a one-letter opening syllable
(``i|deál``), or a compound's second part surrendering its initial vowel
(``pou|čiť``) — which only an exceptionally narrow measure justifies.

The default marker is the middle dot (U+00B7) so that output is unambiguous in
tests; pass ``separator="-"`` or ``separator="\\u00ad"`` for line-breaking use,
or call :func:`break_points` for raw character offsets.
"""

from .phonology import (
    ATTESTED_ONSETS,
    HYPHENATABLE_LETTERS,
    is_consonant,
    is_vowel,
    native_spelling,
)
from .syllabify import (
    _SK_PREFIXES,
    _SK_SUFFIXES_CONS,
    _final_sonorant_needs_following_context,
    get_morpheme_parts,
    phoneme_layout,
)

#: Letters a break may stand beside: Slovak spelling, plus the foreign letters
#: whose pronunciation is known, so that PSP §5.4 is satisfied — data layer.
_DIVISIBLE_LETTERS = HYPHENATABLE_LETTERS

#: Middle dot — the default, unambiguous break marker.
MIDDLE_DOT = '\u00b7'

#: Soft hyphen — what you want when the output goes into rendered text.
SOFT_HYPHEN = '\u00ad'

#: Inflected forms of productive -nosť whose seam belongs only to typographic
#: morphology. Splitting them before linguistic syllabification hides a short
#: syllabic r/l at the edge of the stem (opatrnosť: o-pa-tr-nosť).
_TYPOGRAPHIC_NOST_FORMS = (
    'nosťami', 'nostiach', 'nostiam', 'nosťou', 'ností', 'nosti', 'nosť',
)


def _nucleus_spans(word: str) -> tuple[list[str], list[int], list[tuple[int, int]]]:
    """Return phonemes, offsets, and logical nucleus spans for PSP division."""
    phonemes, offsets, nuclei = phoneme_layout(word)
    spans = [(index, index + 1) for index in nuclei]
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
        if native_spelling(''.join(phonemes[between[index]:next_start])) in ATTESTED_ONSETS:
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


def _typographic_nost_seams(parts: list[str]) -> list[int]:
    """Return productive -nosť/-nost- seams without changing syllabification."""
    seams = []
    offset = 0
    for part in parts:
        folded = part.casefold()
        for form in _TYPOGRAPHIC_NOST_FORMS:
            if folded.endswith(form):
                stem_length = len(part) - len(form)
                stem = part[:stem_length]
                if stem_length >= 3 and any(is_vowel(char) for char in stem):
                    seams.append(offset + stem_length)
                break
        offset += len(part)
    return seams


def _collect_points(word: str) -> tuple[set[int], set[int], set[int]]:
    """Return (preferred, variant, contextual) break offsets for *word*.

    The three sets are the three normative levels section 9 distinguishes.

    *preferred* holds one point per boundary: a morpheme seam where the analysis
    finds one, otherwise the syllabic point of section 4.

    *variant* holds the competing point PSP codifies as equally correct beside
    it, in the three classes of section 3.5 — ``lietad|lo`` next to
    ``lieta|dlo``, ``funk|čný`` next to ``funkč|ný``.

    *contextual* holds a point that is legal but that PSP tells the typesetter
    to avoid unless the measure leaves no choice: the one-letter opening
    syllable (``i|deál``), and the point that pulls the vowel opening a
    compound's second part onto its first (``pou|čiť``). Neither is a codified
    doublet, so neither belongs in *variant*.
    """
    if not word.isalpha() or any(
        char.lower() not in _DIVISIBLE_LETTERS for char in word
    ):
        return set(), set(), set()

    if len(_nucleus_spans(word)[2]) <= 1:
        return set(), set(), set()

    parts = get_morpheme_parts(word)
    points: set[int] = set()
    variants: set[int] = set()
    contextual: set[int] = set()
    seams: list[tuple[int, str, str]] = []
    pos = 0
    for index, part in enumerate(parts):
        next_part = parts[index + 1] if index < len(parts) - 1 else ''
        if _final_sonorant_needs_following_context(part, next_part):
            points.update(
                point for point in _psp_points(part + next_part[0], pos)
                if point < pos + len(part)
            )
        else:
            points.update(_psp_points(part, pos))
        pos += len(part)
        if index < len(parts) - 1:
            points.add(pos)
            seams.append((pos, part, parts[index + 1]))

    # Productive -nosť belongs to typographic morphology, but must not split the
    # input to linguistic syllabification: opatr|nosť still contains syllabic r.
    # Its seam replaces only a competing point inside the same consonant run.
    nost_seams = _typographic_nost_seams(parts)
    if nost_seams:
        _, offsets, nuclei = phoneme_layout(word)
        nucleus_offsets = {offsets[index] for index in nuclei}
        for seam in nost_seams:
            points = {
                point for point in points
                if point == seam
                or any(
                    offset in nucleus_offsets
                    for offset in range(min(point, seam), max(point, seam))
                )
                or not all(
                    is_consonant(char)
                    for char in word[min(point, seam):max(point, seam)]
                )
            }
            points.add(seam)

    # PSP explicitly permits both the morphemic point and the competing
    # syllabic point in these structural classes. The raw whole-word rule gives
    # that second point; only a consonant-only shift across the seam is admitted.
    raw_points = _psp_points(word, mechanical=True)
    for seam, left, right in seams:
        # Section 3.4 keeps the second part's initial vowel off the first part
        # "podľa možnosti" — a preference, not a ban. Section 3.5 does not name
        # this class, so pou|čiť is no codified doublet of po|učiť; it is a
        # plain 4.1 point the norm asks the typesetter not to take unless the
        # measure forces it. That is the contextual level, not the variant one.
        if len(right) > 1 and is_vowel(right[0]) and seam + 1 in points:
            points.discard(seam + 1)
            contextual.add(seam + 1)

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

    # Instrumental plural -ciami has the inflectional seam ci|ami. Its raw
    # syllable points also contain cia|mi, but offering both together would
    # isolate the one-letter syllable a; the morpheme seam is the preferred one.
    if word.casefold().endswith('ciami'):
        instrumental_seam = len(word) - 3
        points.add(instrumental_seam)
        points.discard(instrumental_seam + 1)
        variants.discard(instrumental_seam + 1)
        contextual.discard(instrumental_seam + 1)

    # The two edges are not the same rule. Leaving a one-letter syllable at the
    # end of a word is barred outright (section 9, basic level), so that point
    # is dropped from every level. Detaching a one-letter opening syllable is
    # merely discouraged — "predvolene odstrániť", admitted in exceptionally
    # narrow measure — which is the contextual level and nothing stronger.
    if word and is_vowel(word[0]):
        if 1 in points or 1 in variants:
            contextual.add(1)
        points.discard(1)
        variants.discard(1)
    if word and is_vowel(word[-1]):
        points.discard(len(word) - 1)
        variants.discard(len(word) - 1)
        contextual.discard(len(word) - 1)

    return points, variants - points, contextual - points - variants


def break_points(
    word: str, all_points: bool = False, contextual: bool = False
) -> list[int]:
    """
    Return the character offsets at which *word* may be broken across lines.

    Offsets are positions in the original string: a value ``i`` means a break
    is allowed between ``word[i - 1]`` and ``word[i]``. An empty list means the
    word must not be broken.

    The two flags follow the three normative levels of section 9. By default one
    point per boundary is returned — the reading a human expects.

    ``all_points=True`` adds the competing points PSP codifies as equally
    correct, the three classes of section 3.5.

    ``contextual=True`` adds the points PSP permits but tells the typesetter to
    avoid: a one-letter opening syllable, and the vowel that opens a compound's
    second part. Ask for these only when setting an exceptionally narrow
    measure — they are legal, and they are ugly.

    >>> break_points("Prekladateľský")
    [3, 6, 8, 11]
    >>> break_points("lietadlo")
    [3, 5]
    >>> break_points("lietadlo", all_points=True)
    [3, 5, 6]
    >>> break_points("poučiť")
    [2]
    >>> break_points("poučiť", contextual=True)
    [2, 3]
    >>> break_points("ideál", contextual=True)
    [1, 3]
    """
    preferred, variants, contextuals = _collect_points(word)
    offsets = set(preferred)
    if all_points:
        offsets |= variants
    if contextual:
        offsets |= contextuals
    return sorted(offsets)


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


def hyphenate(
    word: str,
    separator: str = MIDDLE_DOT,
    all_points: bool = False,
    contextual: bool = False,
) -> str:
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
    >>> hyphenate('poučiť')
    'po·učiť'
    >>> hyphenate('poučiť', contextual=True)
    'po·u·čiť'
    """
    offsets = break_points(word, all_points, contextual)
    if not offsets:
        return word

    out = []
    prev = 0
    for pos in offsets:
        out.append(word[prev:pos])
        prev = pos
    out.append(word[prev:])
    return separator.join(out)
