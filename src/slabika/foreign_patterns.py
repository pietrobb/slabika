# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""DE/FR native-pattern proposals with a local PSP adaptation layer.

This adapter is not a complete morphological analyser or a PSP gold standard.
Native boundaries are the baseline; every adaptation is exposed for audit.
Verified morpheme boundaries take precedence over local spelling rules. English
is unsupported; typo selects DE/FR automatically using language evidence.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from .phonology import is_vowel

from .review.tex_patterns import break_points, load_tex

_LANGUAGES = {"de": "german", "german": "german", "fr": "french", "french": "french"}
_FILES = {"german": "hyph-de-1996.tex", "french": "hyph-fr.tex"}
_VOWELS = "aeiouyäöüàâæéèêëîïôœùûÿ"
_LETTERS = {
    "german": frozenset("abcdefghijklmnopqrstuvwxyzäöüß"),
    "french": frozenset("abcdefghijklmnopqrstuvwxyzàâäæçéèêëîïôöœùûüÿ"),
}
# These are spelling rules, not a claim that every matching seam is non-morphemic.
_DE_ST = re.compile(rf"(?<=[{_VOWELS}])([lmnr])st(?=[{_VOWELS}])")
_FR_CLUSTER = re.compile(rf"(ch|ph|th|[bcdfgptv])([lr])(?=[{_VOWELS}])")
# Explicit hiatus spellings only: do NOT split oi, eau, ou, ui, i+vowel, or final ée.
_FR_HIATUS = re.compile(r"(?=(é[aoâ]|[ao]é))")
_FR_INITIAL = re.compile(rf"^[{_VOWELS}](?:ch|ph|th|[bcdfgptv])[lr][aiouyàâæéèêëîïôœùûüÿ]")


@dataclass(frozen=True)
class PatternChange:
    before: int | None
    after: int | None
    rule: str


@dataclass(frozen=True)
class PatternDivision:
    word: str
    language: str
    native_points: tuple[int, ...]
    points: tuple[int, ...]
    changes: tuple[PatternChange, ...]

    def render(self, separator: str = "·") -> str:
        return "".join((separator if i in self.points else "") + c for i, c in enumerate(self.word))


@lru_cache(maxsize=2)
def _patterns(language: str):
    return load_tex(Path(__file__).parent / "patterns/foreign" / _FILES[language])


def _normalized(word: str) -> tuple[str, dict[int, int]]:
    normalized = unicodedata.normalize("NFC", word).lower().replace("’", "'")
    # Map only complete Unicode clusters, keeping offsets in the caller's spelling.
    mapping = {}
    for index in range(len(word) + 1):
        prefix = unicodedata.normalize("NFC", word[:index]).lower().replace("’", "'")
        if normalized.startswith(prefix):
            mapping[len(prefix)] = index
    return normalized, mapping


def adapt_foreign_word(
    word: str, language: str, *, morpheme_points: tuple[int, ...] = ()
) -> PatternDivision:
    """Return native and adapted line-break candidates (2/2 letter margins).

    ``morpheme_points`` are independently established boundaries in the original
    spelling, not guessed prefixes. They are inserted and protected. With none,
    local rules cannot distinguish all compounds from identically spelled units;
    e.g. German t|z may be a compound seam, not the affricate tz. Audit ``changes``
    before treating proposals as authoritative. Unchanged native points are not
    certified PSP decisions either. Possible French prefix spellings inhibit shifts,
    without being certified as morphemes. Slovak inflected endings are not stripped.
    """
    try:
        language = _LANGUAGES[language]
    except KeyError:
        raise ValueError("language must be de/german or fr/french") from None
    lower, mapping = _normalized(word)
    if any(char not in _LETTERS[language] and char != "'" for char in lower):
        raise ValueError("expected one DE/FR word (apostrophes are allowed)")
    reverse = {original: normal for normal, original in mapping.items()}
    if any(
        type(p) is not int or p not in reverse or not 0 < reverse[p] < len(lower)
        for p in morpheme_points
    ):
        raise ValueError("morpheme_points must be internal character-cluster boundaries")
    protected = {reverse[p] for p in morpheme_points}
    patterns, exceptions = _patterns(language)
    raw = set(break_points(lower, patterns, exceptions, left_min=1, right_min=1)) | (
        {1} if language == "french" and _FR_INITIAL.match(lower) else set()
    )
    native = {p for p in raw if 2 <= p <= len(lower) - 2}
    points = raw | protected
    changes = [
        PatternChange(None, mapping[p], "verified_morpheme")
        for p in sorted(protected - raw)
        if 2 <= p <= len(lower) - 2
    ]

    def move(before: int, after: int, rule: str) -> None:
        if before not in points or before in protected:
            return
        points.remove(before)
        # Invalid original cuts must also disappear when their replacement is
        # excluded by the margins: At|zen must not survive merely because A|tzen cannot.
        valid = 2 <= after <= len(lower) - 2 and after in mapping
        if valid:
            points.add(after)
        changes.append(PatternChange(mapping[before], mapping[after] if valid else None, rule))

    if language == "german":
        for match in re.finditer(rf"(?<=[{_VOWELS}])tz(?=[{_VOWELS}])", lower):
            move(match.start() + 1, match.start(), "de_tz_single_affricate")
        for match in _DE_ST.finditer(lower):
            move(match.start() + 2, match.start() + 1, "de_three_consonants")
    else:
        for point in sorted(raw):
            match = _FR_CLUSTER.match(lower, point)
            if (
                match
                and point > 0
                and lower[point - 1] in _VOWELS
                and lower[:point] not in {"re", "ré", "dé", "pré", "mé"}
            ):
                move(point, point + len(match[1]), "fr_two_consonants")
        for match in _FR_HIATUS.finditer(lower):
            point = match.start() + 1
            if point not in points and 2 <= point <= len(lower) - 2 and point in mapping:
                points.add(point)
                changes.append(PatternChange(None, mapping[point], "fr_hiatus"))

    return PatternDivision(
        word,
        language,
        tuple(mapping[p] for p in sorted(native)),
        tuple(mapping[p] for p in sorted(points) if 2 <= p <= len(lower) - 2),
        tuple(changes),
    )


def german_inflected_points(
    stem: str, ending: str, psp_points: Callable[[str], list[int]]
) -> set[int]:
    """Keep DE stem points and apply PSP at an evidenced Slovak ending.

    Only the final consonant run is resyllabified before a vowel-initial ending;
    the rest of the stem is never fed to Slovak spelling rules.
    """
    points = set(adapt_foreign_word(stem, "german").points)
    seam = len(stem)
    if not is_vowel(ending[0]):
        points.add(seam)
        points.update(seam + p for p in psp_points(ending))
    else:
        lower = stem.lower()
        start = seam
        while start and lower[start - 1] not in _VOWELS:
            start -= 1
        # German postvocalic h marks vowel length, not a new consonant.
        if start < seam and lower[start] == "h":
            start += 1
        # A synthetic nucleus protects ei/ie/au/etc.; map consonant units back
        # as whole spellings, retaining German ng as a single consonant.
        mapping = [0, start]
        proxy = "a"
        for match in re.finditer(r"tsch|dsch|sch|ch|ck|tz|ph|th|ng|.", lower[start:]):
            unit = match[0]
            proxy += {"tsch": "č", "dsch": "ž", "sch": "š", "ch": "h",
                      "ck": "k", "tz": "c", "ph": "f", "th": "t", "ng": "n"}.get(unit, unit)
            mapping.append(start + match.end())
        proxy += ending
        mapping.extend(range(seam + 1, seam + len(ending) + 1))
        points = {p for p in points if p < start}
        points.update(mapping[p] for p in psp_points(proxy))
    return {p for p in points if 2 <= p <= seam + len(ending) - 2}


def foreign_hyphenate(
    word: str, language: str, separator: str = "·", *, morpheme_points: tuple[int, ...] = ()
) -> str:
    """Render opt-in DE/FR adapter proposals; see adapt_foreign_word for limitations."""
    return adapt_foreign_word(word, language, morpheme_points=morpheme_points).render(separator)
