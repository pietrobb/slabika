# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Vendored from the sibling Sapfo project (sapfo/dictionaries/alternations.py) for build-time use
# by the compound builders. Included in the sdist, not the runtime wheel.
"""
Koreňové alternácie - Root alternation rules for Slovak morphology.

Alternation types as defined in SAPFO specification (p. 44):

Vowel alternations (vokalické):
  ≤  predĺženie (lengthening): a/á, i/í, y/ý, u/ú, o/ó, e/é/ie, r/ŕ, l/ĺ, ä/ia
  ≥  skrátenie (shortening): reverse of ≤
  »« vypustenie (elision): e/ø, o/ø, i/ø, á/ø, ie/ø
  «» vloženie (insertion): ø/ie, ø/e, ø/o, ø/ó, ø/á

Consonant alternations (konsonantické):
  /  zámena (substitution): k/c, s/d, s/r, s/n, ch/s
  +  rozšírenie koreňa (root expansion): +n, +m, +t, +ať, +enc, +c, +ik, +er
  -  zúženie koreňa (root contraction): -us, -os, -es, -as, -um, -ex
  *  lingválna/dorzálna: ľ/l, ť/t, ď/d

Source: Emil Páleš, Sapfo (1994), pp. 44-45
"""

from .phonology import (
    LENGTHEN_VOWEL, SHORTEN_VOWEL, is_vowel, is_consonant,
    PALATALIZATION
)


def apply_lengthening(root: str) -> str:
    """Apply vowel lengthening (predĺženie ≤) to the last vowel in root.

    Standard morphological lengthening pairs:
      a→á, e→ie, i→í, o→ô, u→ú, y→ý, ä→ia, r→ŕ, l→ĺ
    Note: e→ie (diphthong) and o→ô (diphthong [uo]) are the standard
    declension lengthening forms. 'é' and 'ó' only appear in loanwords.
    """
    result = list(root)
    for i in range(len(result) - 1, -1, -1):
        c = result[i]
        # Special case: e → ie (diphthong, not é)
        if c == 'e':
            result[i] = 'i'
            result.insert(i + 1, 'e')
            break
        # Special case: o → ô (diphthong [uo], not ó)
        if c == 'o':
            result[i] = 'ô'
            break
        # Special case: ä → ia
        if c == 'ä':
            result[i] = 'a'
            result.insert(i, 'i')
            break
        # Special case: syllabic r → ŕ, l → ĺ
        if c == 'r' and (i == 0 or not is_vowel(result[i - 1])):
            result[i] = 'ŕ'
            break
        if c == 'l' and (i == 0 or not is_vowel(result[i - 1])):
            result[i] = 'ĺ'
            break
        # Standard lengthening: a→á, i→í, u→ú, y→ý
        if c in LENGTHEN_VOWEL:
            result[i] = LENGTHEN_VOWEL[c]
            break
    return ''.join(result)


def apply_shortening(root: str) -> str:
    """Apply vowel shortening (skrátenie ≥) to the last long vowel in root."""
    # Handle diphthongs first
    if 'ie' in root:
        return root.replace('ie', 'e', 1)
    if 'ô' in root:
        return root.replace('ô', 'o', 1)
    if 'ia' in root:
        return root.replace('ia', 'a', 1)

    result = list(root)
    for i in range(len(result) - 1, -1, -1):
        c = result[i]
        if c in SHORTEN_VOWEL:
            result[i] = SHORTEN_VOWEL[c]
            break
        if c == 'ŕ':
            result[i] = 'r'
            break
        if c == 'ĺ':
            result[i] = 'l'
            break
    return ''.join(result)


def apply_elision(root: str) -> str:
    """
    Apply vowel elision (vypustenie »«).
    Remove the mobile vowel (pohyblivá samohláska) from the root.
    Typically removes e or o from the last syllable.
    Examples: dravec -> dravca, švagor -> švagra, otec -> otca
    """
    # Try to find and remove mobile vowel before last consonant cluster
    if len(root) < 3:
        return root

    # Common pattern: remove vowel between last two consonants
    for i in range(len(root) - 2, 0, -1):
        if is_vowel(root[i]) and is_consonant(root[i-1]) and i + 1 < len(root) and is_consonant(root[i+1]):
            return root[:i] + root[i+1:]
        # Also handle: ie -> ø
        if i > 0 and root[i-1:i+1] == 'ie':
            return root[:i-1] + root[i+1:]

    return root


def apply_insertion(root: str, vowel: str = 'e') -> str:
    """
    Apply vowel insertion (vloženie «»).
    Insert a vowel before the final consonant cluster.
    Examples: kráska -> krások (insert o), perla -> perál (insert á)
    """
    # Find the last consonant cluster and insert before it
    for i in range(len(root) - 1, 0, -1):
        if is_consonant(root[i]) and is_consonant(root[i-1]):
            return root[:i] + vowel + root[i:]
    return root


def apply_consonant_substitution(root: str, old: str, new: str) -> str:
    """
    Apply consonant substitution (zámena /).
    Replace consonant at end of root.
    Examples: Turek -> Turci (k/c), Izis -> Izidy (s/d)
    """
    if root.endswith(old):
        return root[:-len(old)] + new
    return root


def apply_root_expansion(root: str, expansion: str) -> str:
    """
    Apply root expansion (rozšírenie koreňa +).
    Add morpheme to end of root.
    Examples: dievča -> dievčat (root = dievč + at)
    """
    return root + expansion


def apply_root_contraction(root: str, contraction: str) -> str:
    """
    Apply root contraction (zúženie koreňa -).
    Remove ending from root.
    Examples: génius -> génia (remove -us), rytmus -> rytmy (remove -us)
    """
    if root.endswith(contraction):
        return root[:-len(contraction)]
    return root


def apply_lingual_dorsal(root: str) -> str:
    """
    Apply lingválna/dorzálna alternation (*).
    Soften the final consonant.
    Examples: loď -> lode (ď -> d), kosť -> kosti (ť -> t)
    """
    if not root:
        return root

    # Check for digraphs at end
    if len(root) >= 2:
        last_two = root[-2:]
        if last_two in PALATALIZATION:
            return root[:-2] + PALATALIZATION[last_two]

    last = root[-1]
    if last in PALATALIZATION:
        return root[:-1] + PALATALIZATION[last]

    return root


def apply_alternation(root: str, alt_code: str) -> str:
    """
    Apply a single alternation code to a root.
    Returns the alternated root form.
    """
    if alt_code == '≤':
        return apply_lengthening(root)
    elif alt_code == '≥':
        return apply_shortening(root)
    elif alt_code == '»«':
        return apply_elision(root)
    elif alt_code == '*':
        return apply_lingual_dorsal(root)
    elif alt_code.startswith('«') and alt_code.endswith('»'):
        # Insertion of specific vowel: «ie», «e», «o», «ó», «á»
        vowel = alt_code[1:-1]
        return apply_insertion(root, vowel)
    elif alt_code.startswith('+'):
        # Root expansion
        expansion = alt_code[1:]
        # Remove position specifiers like -1sg, -14sg, +2pl etc.
        for suffix in ['-1sg', '-14sg', '-1pl', '+1pl', '+2pl',
                       '+2367sg', '-1sg-2pl']:
            expansion = expansion.replace(suffix, '')
        if expansion:
            return apply_root_expansion(root, expansion)
        return root
    elif alt_code.startswith('-') and not alt_code[1:].startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
        # Root contraction (not a position specifier)
        contraction = alt_code[1:]
        # Remove position specifiers
        for suffix in ['-1sg', '-14sg', '-1pl']:
            contraction = contraction.replace(suffix, '')
        if contraction:
            return apply_root_contraction(root, contraction)
        return root
    elif '/' in alt_code:
        # Consonant substitution
        parts = alt_code.split('/')
        if len(parts) == 2:
            return apply_consonant_substitution(root, parts[0], parts[1])
    return root


def _is_position_specifier(code: str) -> bool:
    """Check if a standalone code is a pure position specifier (not an alternation).

    Position specifiers start with +/- followed by a digit, or are 'pl'/'+pl'.
    Alternation codes like '+n' (root expansion) or '-us' (root contraction)
    start with +/- followed by a letter.
    """
    if code in ('pl', '+pl'):
        return True
    if len(code) > 1 and code[0] in ('+', '-') and code[1].isdigit():
        return True
    return False


def _parse_position_set(spec: str) -> set[int]:
    """Parse a position specifier string into a set of case indices.

    Book case numbering (1-based): 1=nom, 2=gen, 3=dat, 4=acc, 5=loc, 6=ins.
    Our indices (0-based): sg 0-5, pl 6-11.

    Prefix semantics:
      + = ONLY at these positions (include)
      - = at ALL positions EXCEPT these (exclude)

    Position specifiers:
      -1sg:      all except nom.sg          = {1,2,3,4,5,6,7,8,9,10,11}
      -14sg:     all except nom.sg & acc.sg  = {1,2,4,5,6,7,8,9,10,11}
      -1sg-2pl:  all except nom.sg & gen.pl  = {1,2,3,4,5,6,8,9,10,11}
      -1pl:      all except nom.pl           = {0,1,2,3,4,5,7,8,9,10,11}
      +1pl:      only nom.pl                 = {6}
      +2pl:      only gen.pl                 = {7}
      +2367sg:   gen,dat,loc,ins sg + gen.pl = {1,2,4,5,7}
      pl / +pl:  all plural positions        = {6,7,8,9,10,11}
    """
    ALL = set(range(12))
    if spec in ('-14sg',):
        return ALL - {0, 3}  # exclude nom.sg and acc.sg
    elif spec in ('-1sg-2pl',):
        return ALL - {0, 7}  # exclude nom.sg and gen.pl
    elif spec in ('-1sg',):
        return ALL - {0}  # exclude nom.sg
    elif spec in ('-1pl',):
        return ALL - {6}  # exclude nom.pl
    elif spec in ('+1pl',):
        return {6}
    elif spec in ('+2pl',):
        return {7}
    elif spec in ('+2367sg',):
        return {1, 2, 4, 5, 7}
    elif spec in ('pl', '+pl'):
        return {6, 7, 8, 9, 10, 11}
    else:
        return ALL  # unknown -> all positions


def _extract_embedded_spec(code: str) -> tuple[str, str] | None:
    """Extract an embedded position specifier from a compound code.

    E.g. '+ať+2367sg' -> ('+2367sg', '+ať')
    Returns (specifier, base_code) or None if no embedded specifier.
    """
    if _is_position_specifier(code):
        return None

    SPECS = ['-14sg', '-1sg-2pl', '-1sg', '-1pl', '+1pl', '+2pl', '+2367sg']
    for spec in SPECS:
        if spec in code:
            base = code.replace(spec, '').strip()
            if base:
                return (spec, base)
    return None


def get_alternated_root(root: str, alternation_codes: list[str],
                        case_index: int) -> str:
    """
    Get the alternated form of a root for a specific case position.

    Alternation codes are grouped with their position specifiers:
    - A position specifier (e.g. '+2pl', '-1sg') applies to ALL alternation
      codes that precede it since the last position specifier.
    - Codes with embedded specifiers (e.g. '+ať+2367sg') form their own group.
    - Alternation codes with no following position specifier apply to all positions.

    Examples:
      ['≤', '+2pl']           -> lengthening at gen.pl only
      ['≥', '»«', '-14sg']   -> shortening + elision at gen.sg and acc.sg
      ['+ať+2367sg', '≥', 'pl'] -> expansion at specific sg positions,
                                    shortening at all plural positions
    """
    result = root

    # Build groups: (list_of_alternation_codes, position_set_or_None)
    groups: list[tuple[list[str], set[int] | None]] = []
    current_group: list[str] = []

    for code in alternation_codes:
        # Check for embedded position specifiers (e.g., '+ať+2367sg')
        embedded = _extract_embedded_spec(code)
        if embedded:
            # Flush accumulated alternations as unrestricted group
            if current_group:
                groups.append((list(current_group), None))
                current_group = []
            spec_str, base_code = embedded
            groups.append(([base_code], _parse_position_set(spec_str)))
            continue

        # Check if this is a standalone position specifier
        if _is_position_specifier(code):
            # Applies to all accumulated alternations since last specifier
            groups.append((list(current_group), _parse_position_set(code)))
            current_group = []
            continue

        # Regular alternation code - accumulate
        current_group.append(code)

    # Flush remaining alternations (no position specifier = all positions)
    if current_group:
        groups.append((current_group, None))

    # Apply each group
    for alts, positions in groups:
        if positions is not None and case_index not in positions:
            continue
        for alt_code in alts:
            result = apply_alternation(result, alt_code)

    return result
