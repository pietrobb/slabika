# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Optional experimental English G2P route; no access to human review databases."""

import json
import logging
import math
from functools import lru_cache
from pathlib import Path

from .english_projection import COMPOUND_HEADS, EnglishMorphology, project_psp_points

_LOG = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _runtime():
    try:
        from slabika_pronunciation import pronounce
    except ImportError:
        return None
    return pronounce


@lru_cache(maxsize=100_000)
def _pronunciation(word):
    pronounce = _runtime()
    if pronounce is None:
        return None
    try:
        result = pronounce(word, "english")
        if (result.word != word or result.language != "english"
                or not math.isfinite(result.score)
                or "".join(s for s, _ in result.spans) != word
                or not result.spans
                or not any(ps for _, ps in result.spans)
                or "".join(p for _, ps in result.spans for p in ps)
                != result.phones.replace(" ", "")):
            raise ValueError("invalid English pronunciation alignment")
        return result
    except Exception as error:  # Optional native model boundary; keep the core usable.
        _LOG.warning("English pronunciation unavailable for %r: %s", word, error)
        return None


@lru_cache(maxsize=1)
def _members():
    resource = Path(__file__).parent / "data/english_morphology_members.json"
    return frozenset(json.loads(resource.read_text(encoding="utf-8"))["members"])


@lru_cache(maxsize=100_000)
def _project(word):
    pronunciation = _pronunciation(word)
    if pronunciation is None:
        return None
    points, complete = project_psp_points(pronunciation)
    if not complete:
        return None
    candidates = set()
    for head in COMPOUND_HEADS:
        if word.endswith(head):
            candidates.update((word[:-len(head)], head))
    if word.endswith("ly"):
        candidates.update((word[:-2], word[:-2] + "ness"))
    evidence = [_pronunciation(member) for member in sorted(candidates & _members())]
    return EnglishMorphology(p for p in evidence if p is not None).refine(pronunciation, points)


def english_points(word):
    """Abstain for unsupported spelling, local readings or incomplete projection."""
    from .language import detect_language, is_english
    from .syllabify import _LEXICAL_FALLING_HIATUS, _lexical_syllables
    from .typo import _SLOVAK_READING_STEMS

    normalized = word.lower()
    if (not word.isascii() or not word.isalpha()
            or detect_language(word) != "english" or not (is_english(word) or normalized in _members())
            or _lexical_syllables(word) is not None
            or normalized.startswith(_SLOVAK_READING_STEMS)
            or any(normalized.startswith(stem) for stem, _ in _LEXICAL_FALLING_HIATUS)):
        return None
    points = _project(normalized)
    return None if points is None else (set(points), set(), set())
