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

from .foreign import foreign_points
from .foreign_patterns import _LETTERS, adapt_foreign_word, german_inflected_points
from .language import detect_language, german_evidence, is_french, is_german
from .phonology import (
    HYPHENATABLE_LETTERS,
    is_consonant,
    is_vowel,
)
from .syllabify import (
    _DLO_INFLECTIONS,
    _LEXICAL_FALLING_HIATUS,
    _PREFIXES,
    _SK_SUFFIXES_CONS,
    _final_sonorant_needs_following_context,
    _lexical_syllables,
    breaks_after_stop,
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
_TYPOGRAPHIC_NOST_DERIVATIVE_ONSETS = ('n', 'ň')
_CNOST_INFLECTIONS = frozenset({
    'cnosť', 'cnosťami', 'cnostiach', 'cnostiam', 'cnosťou', 'cností', 'cnosti',
})
_CHRAN_ROOT_CONTEXTS = (
    ('ochran', ('', 'ne', 'seba')),
    ('záchran', ('', 'ne', 'seba')),
    ('ochraň', ('', 'ne', 'vše')),
    ('zachraň', ('', 'ne')),
    ('uchraň', ('', 'ne')),
)
_VYRVAN_VARIANT_ENDINGS = frozenset({'á', 'é'})
_PREFERRED_SYLLABIC_DLO_FORMS = frozenset({'páčidlá', 'páčidlom'})
# Adapted Slovak loans keep their local consonant reading despite foreign spelling matches.
_SLOVAK_READING_STEMS = ('gangst', 'soused')

# Exact pronunciation-backed points for unadapted foreign spellings. Generic
# Slovak grapheme rules cannot infer these safely.
_REVIEWED_FOREIGN_BREAK_POINTS = {
    'adrienne': (2,),
    'advienne': (2,),
    'aequata': (2, 5),
    'again': (),
    'against': (),
    'agnes': (2,),  # /g/ + /n/, not the French gn digraph.
    'albastone': (2, 4),
    'aliquandiu': (3, 7),
    'aliquid': (3,),
    'ambagesque': (2, 4, 7),
    'applausit': (2, 6),
    'blackburna': (5, 8),
    'blake': (),
    'cypress': (3,),
    'department': (2, 6),
    'elenore': (3,),
    'excellence': (2, 5),
    'fahrenheita': (3, 6, 9),
    'fahrenheitovho': (3, 6, 9, 12),
    'fairfaxe': (4, 6),
    'fairfaxovci': (4, 6, 9),
    'fallbrook': (4,),
    'fallbrookovej': (4, 8, 10),
    'fallbrooková': (4, 8, 10),
    'fallbrooku': (4, 8),
    'falls': (),
    'gleisdorf': (5,),
    'gleisdorfu': (5, 8),
    'glendower': (4,),
    'glenview': (4,),
    'grossglockner': (5, 10),
    'grossglocknera': (5, 10, 12),
    'grossglockneru': (5, 10, 12),
    'großglockner': (4, 9),
    'großglocknera': (4, 9, 11),
    'großglockneri': (4, 9, 11),
    'großglocknerom': (4, 9, 11),
    'großglocknerov': (4, 9, 11),
    'hornblende': (4,),
    'immense': (2,),
    'jacques': (),
    'jacquesa': (2,),
    'jaira': (3,),
    'joea': (),
    'joeom': (3,),
    'joeovi': (3, 4),
    'johnnie': (4,),
    'joinvilla': (4, 7),
    'joinville': (4,),
    'joinvillovcov': (4, 7, 10),
    'jonesa': (4,),
    'jonesovi': (4, 6),
    'jonesovia': (4, 6),
    'jowette': (2,),
    'joyce': (),
    'joycea': (3,),
    'lockridge': (4,),
    'loira': (3,),
    'loire': (),
    'lois': (),
    'loquantut': (2, 6),
    'loua': (),
    'louis': (),
    'louisa': (3, 4),
    'louisovi': (3, 4, 6),
    'lounge': (),
    'lowry': (3,),
    'loyoly': (2, 4),
    'loyseleura': (3, 5, 8),
    'loyseleurovi': (3, 5, 8, 10),
    'loyseleurovo': (3, 5, 8, 10),
    'macquarie': (3, 6),
    'maelströme': (4, 8),
    'maelströmu': (4, 8),
    'magoon': (2,),
    'magoona': (2, 5),
    'magoonom': (2, 5),
    'magoonovi': (2, 5, 7),
    'mahalaleela': (2, 4, 6, 8, 9),
    'mahalaleelom': (2, 4, 6, 8, 9),
    'mahalaleelov': (2, 4, 6, 8, 9),
    'mahalaleelovi': (2, 4, 6, 8, 9, 11),
    'mahalaleelovmu': (2, 4, 6, 8, 9, 12),
    'main': (),
    'maine': (),
    'maioranos': (2, 4, 6),
    'maioranosa': (2, 4, 6, 8),
    'maiorem': (2, 4),
    'maisie': (3,),
    'marlene': (3,),
    'oglethorpe': (4,),
    'salvatorque': (3, 5),
    'teufelsbrücke': (3, 7, 11),
    'teufelsgalgen': (3, 7, 10),
    'teufelsritt': (3, 7),

    'teufelswand': (7,),
}


def _preferred_internal_vowel_points(word: str) -> set[int]:
    """Operator-approved family seams that remain preferred around one vowel."""
    folded = word.casefold()
    if folded.startswith('opotreb'):
        return {1}
    if folded.startswith('neupotrebiteľn'):
        return {3}
    if folded.startswith('zneucten'):
        return {4}
    if folded.startswith('dvojokamih'):
        return {5}
    if folded.startswith('najúhlavnejš'):
        return {4}
    return set()


def _nucleus_spans(word: str) -> tuple[list[str], list[int], list[tuple[int, int]]]:
    """Return phonemes, offsets, and logical nucleus spans for PSP division."""
    phonemes, offsets, nuclei = phoneme_layout(word)
    spans = [(index, index + 1) for index in nuclei]
    return phonemes, offsets, spans


def _psp_points(word: str, base: int = 0) -> list[int]:
    """Apply PSP 2a–2d inside one morphological unit."""
    phonemes, offsets, nuclei = _nucleus_spans(word)
    points = []
    for (_, previous_end), (next_start, _) in zip(nuclei, nuclei[1:]):
        between = list(range(previous_end, next_start))
        if not between:
            point = offsets[next_start]          # 2d: genuine hiatus
        elif len(between) == 1:
            point = offsets[between[0]]          # 2a: before the consonant
        elif breaks_after_stop(phonemes, previous_end - 1, between):
            point = offsets[between[2]]          # vrst·va, like krst·ná
        else:
            point = offsets[between[1]]          # 2b/2c: after the first
        points.append(base + point)
    return points


def _variant_crosses_seam(left: str, right: str) -> bool:
    """Whether PSP also licenses the syllabic point across this morpheme seam.

    Section 3.5 names three classes and no more: a base ending in a vowel before
    a suffix opening with a cluster, the c/č alternation of -cia adjectives, and
    an unclear cluster. A prefix seam is in none of them — what follows a prefix
    is the base, and the cluster there is the root's own onset, not a suffix that
    happens to be spelled alike. TeX offers nas|kladať; PSP does not, so neither
    do we.
    """
    if left.casefold() in _PREFIXES:
        return False
    _, _, right_nuclei = _nucleus_spans(right)
    initial_cluster = right_nuclei[0][0] if right_nuclei else 0
    leftl, rightl = left.casefold(), right.casefold()
    suffix_cluster = any(
        rightl.startswith(suffix)
        for suffix in (*_SK_SUFFIXES_CONS, *_DLO_INFLECTIONS)
    )
    unclear_compound = leftl == 'jedno' and rightl.startswith('tl')
    return (
        bool(left)
        and is_vowel(left[-1])
        and initial_cluster >= 2
        and (suffix_cluster or unclear_compound)
    ) or rightl.startswith('cia')


def _typographic_nost_seams(parts: list[str]) -> list[int]:
    """Return productive -nosť/-nost- seams without changing syllabification."""
    word = "".join(parts)
    folded = word.casefold()
    if (
        len(parts) >= 2
        and parts[0].casefold() == 'ne'
        and ''.join(parts[1:]).casefold() in _CNOST_INFLECTIONS
    ):
        return []
    for onset in _TYPOGRAPHIC_NOST_DERIVATIVE_ONSETS:
        marker = f'nost{onset}'
        start = folded.find(marker)
        if start >= 3 and any(is_vowel(char) for char in word[:start]):
            # Both seams are real: the stem before -nost- and the derivative
            # suffix after it. Returning only the second one leaves -nost-
            # open to the consonant-cluster rule, which then cuts the stem
            # short (vlas·tnost·né instead of vlast·nost·né). In cnosť the
            # n belongs to the root, so there the leading seam is not one.
            if folded[start - 1] == 'c':
                return [start + 4]
            return [start, start + 4]
    for form in _TYPOGRAPHIC_NOST_FORMS:
        if folded.endswith(form):
            seam = len(word) - len(form)
            stem = word[:seam]
            if seam >= 3 and any(is_vowel(char) for char in stem):
                return [seam]
            break
    return []


def _chran_root_spans(word: str) -> list[tuple[int, int]]:
    """Return attested chran-/chraň- roots after their family prefixes."""
    folded = word.casefold()
    spans = []
    for family, leaders in _CHRAN_ROOT_CONTEXTS:
        root_offset = family.index('ch')
        for leader in leaders:
            if folded.startswith(leader + family):
                start = len(leader) + root_offset
                spans.append((start, start + 5))
                break
    return spans


def _french_gn_point(word: str) -> int | None:
    """Offset inside a French word-final ``-gne``, which spells a single /ɲ/.

    Section 5.4 bars tearing a foreign letter group that stands for one sound.
    A Slovak ``-gne`` is a different structure: a stem-final ``g`` meeting the
    ``-ne`` ending, and there a consonant precedes the ``g`` (preglg|ne). Only
    the French shape has a vowel in that position.
    """
    folded = word.casefold()
    if len(folded) < 5 or not folded.endswith('gne') or not is_vowel(folded[-4]):
        return None
    return len(word) - 2


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
    if not word.isalpha():
        return set(), set(), set()

    # Lower-cased, not case-folded: folding turns ß into ss, which collapses
    # Großglockner and Grossglockner onto one key although the review divides
    # them at different offsets (Groß·glock·ner, Gross·glock·ner). No key in
    # the table has ever relied on the folding.
    reviewed_foreign = _REVIEWED_FOREIGN_BREAK_POINTS.get(word.lower())
    if reviewed_foreign is not None:
        return set(reviewed_foreign), set(), set()

    routed = foreign_points(word, _psp_points)
    if routed is not None:
        return routed

    lexical_parts = _lexical_syllables(word)
    language = detect_language(word)
    german = german_evidence(word)
    if german.is_german and german.ending and detect_language(german.stem) == "german":
        # The Slovak ending can obscure the whole-word language vote.
        language = "german"
    if (
        lexical_parts is None
        and not word.casefold().startswith(_SLOVAK_READING_STEMS)
        and not any(word.casefold().startswith(stem) for stem, _ in _LEXICAL_FALLING_HIATUS)
        and language in _LETTERS
        and (is_german(word) if language == "german" else is_french(word))
    ):
        if language == "german":
            if german.is_german and german.ending:
                stem = word[:-len(german.ending)]
                ending = word[len(stem):]
                if (
                    stem.lower() == german.stem
                    and ending.lower() == german.ending
                    and all(char.lower() in _LETTERS[language] for char in stem)
                    and all(char.lower() in _DIVISIBLE_LETTERS for char in ending)
                ):
                    return german_inflected_points(stem, ending, _psp_points), set(), set()
        if all(char.lower() in _LETTERS[language] for char in word):
            return set(adapt_foreign_word(word, language).points), set(), set()

    if any(char.lower() not in _DIVISIBLE_LETTERS for char in word):
        return set(), set(), set()

    if len(_nucleus_spans(word)[2]) <= 1 and lexical_parts is None:
        return set(), set(), set()

    parts = lexical_parts or get_morpheme_parts(word)
    points: set[int] = set()
    variants: set[int] = set()
    contextual: set[int] = set()
    seams: list[tuple[int, str, str]] = []
    pos = 0
    for index, part in enumerate(parts):
        next_part = parts[index + 1] if index < len(parts) - 1 else ''
        if lexical_parts is None:
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

    folded = word.casefold()
    preferred_internal_vowels = _preferred_internal_vowel_points(word)
    if folded.startswith('vyrvan') and folded[6:] in _VYRVAN_VARIANT_ENDINGS:
        variants.add(3)

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
    raw_points = _psp_points(word)
    for seam, left, right in seams:
        if folded == 'poslednýkrát' and left.casefold() == 'po':
            variants.add(seam + 1)
        if left.casefold() == 'obo' and right.casefold().startswith('zret'):
            variants.add(seam - 2)

        # Section 3.4 keeps the second part's initial vowel off the first part
        # "podľa možnosti" — a preference, not a ban. Section 3.5 does not name
        # this class, so pou|čiť is no codified doublet of po|učiť; it is a
        # plain 4.1 point the norm asks the typesetter not to take unless the
        # measure forces it. That is the contextual level, not the variant one.
        if (
            len(right) > 1
            and is_vowel(right[0])
            and seam + 1 in points
            and seam + 1 not in preferred_internal_vowels
        ):
            points.discard(seam + 1)
            contextual.add(seam + 1)

        if left.casefold().endswith('ec') and right.casefold().startswith('tv'):
            variants.add(seam - 1)
        elif _variant_crosses_seam(left, right):
            alternatives = [
                point for point in raw_points
                if point != seam
                and all(is_consonant(char) for char in word[min(point, seam):max(point, seam)])
            ]
            if alternatives:
                alternative = min(alternatives, key=lambda point: abs(point - seam))
                # In the -ctv- doublet, prefer the point that leaves c with
                # the base (baníc·tvo); keep the morphemic point as a variant.
                if right.casefold().startswith('ctv'):
                    points.discard(seam)
                    points.add(alternative)
                    variants.add(seam)
                elif folded in _PREFERRED_SYLLABIC_DLO_FORMS:
                    points.discard(seam)
                    points.add(alternative)
                    variants.add(seam)
                else:
                    variants.add(alternative)

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

    for seam, end in _chran_root_spans(word):
        points.add(seam)
        first_nucleus = next(
            index for index in range(seam, end) if is_vowel(word[index])
        )
        points = {point for point in points if not seam < point <= first_nucleus}
        variants = {point for point in variants if not seam < point <= first_nucleus}
        contextual = {point for point in contextual if not seam < point <= first_nucleus}

    # The two edges are not the same rule. Leaving a one-letter syllable at the
    # end of a word is barred outright (section 9, basic level), so that point
    # is dropped from every level. Detaching a one-letter opening syllable is
    # merely discouraged — "predvolene odstrániť", admitted in exceptionally
    # narrow measure — which is the contextual level and nothing stronger.
    if word and is_vowel(word[0]) and 1 not in preferred_internal_vowels:
        if 1 in points or 1 in variants:
            contextual.add(1)
        points.discard(1)
        variants.discard(1)
    if word and is_vowel(word[-1]):
        points.discard(len(word) - 1)
        variants.discard(len(word) - 1)
        contextual.discard(len(word) - 1)

    # Inside the word the same asymmetry holds as at its start. A prefix that is
    # a single vowel letter (ne|u|kladajú, naj|u|tajenejšia) has a real seam on
    # both of its sides, but taking both leaves that letter standing alone. The
    # seam before it is the readable one — section 3.4 keeps the vowel with the
    # base it belongs to — so the point that closes it drops to the contextual
    # level, admitted only in exceptionally narrow measure.
    seam_offsets = {seam for seam, _, _ in seams}
    for point in sorted(points):
        if (
            point in preferred_internal_vowels
            or lexical_parts is not None
            or point - 1 not in points
            or not is_vowel(word[point - 1])
        ):
            continue
        # Only a prefix does this. The vowel is a morpheme of its own, seamed on
        # both sides, and breaking after it welds it to what precedes into a
        # shape the word does not have (naju|tajenejšia reads na-ju-ta). Two
        # vowels merely meeting inside a stem weld nothing (arche|o|lóg), and a
        # connecting vowel carries its own seam (§3.4, teo|lógia); both keep
        # their points at the basic level.
        if point - 1 not in seam_offsets:
            continue
        points.discard(point)
        contextual.add(point)

    gn_point = _french_gn_point(word)
    if gn_point is not None:
        points.discard(gn_point)
        variants.discard(gn_point)
        contextual.discard(gn_point)

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

    Original casing is preserved. Supported DE/FR words use native patterns
    adapted to PSP when both the shared router and language evidence agree.
    Existing lexical readings take precedence; unsupported spellings stay unchanged.

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
