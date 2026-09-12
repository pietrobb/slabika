# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Conservative language evidence for words occurring in Slovak text."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .foreign import reading_candidates

_PROFILE_PATHS = {
    "german": Path(__file__).parent / "data" / "german_profile.json",
    "french": Path(__file__).parent / "data" / "french_profile.json",
    "english": Path(__file__).parent / "data" / "english_profile.json",
}
_ROUTER_PROFILE_PATH = Path(__file__).parent / "data" / "language_router_profile.json"


@dataclass(frozen=True)
class LanguageScore:
    """Comparable isolated-word score from the shared language model."""

    language: str
    score: float


@dataclass(frozen=True)
class GermanEvidence:
    """Corpus evidence; scored_unit identifies the text actually scored."""

    score: float
    support: int
    coverage: float
    stem: str
    ending: str
    is_german: bool
    scored_unit: str = ""


@dataclass(frozen=True)
class FrenchEvidence:
    """Corpus evidence, including supported Slovak inflections."""

    score: float
    support: int
    coverage: float
    is_french: bool
    stem: str = ""
    ending: str = ""
    scored_unit: str = ""


@dataclass(frozen=True)
class EnglishEvidence:
    """Corpus evidence, including supported Slovak inflections."""

    score: float
    support: int
    coverage: float
    is_english: bool
    stem: str = ""
    ending: str = ""
    scored_unit: str = ""


@lru_cache(maxsize=len(_PROFILE_PATHS))
def _profile(language: str) -> dict[str, object]:
    return json.loads(_PROFILE_PATHS[language].read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _router_profile() -> dict[str, object]:
    return json.loads(_ROUTER_PROFILE_PATH.read_text(encoding="utf-8"))


def _features(
    word: str,
    sizes: tuple[int, ...],
    letters: frozenset[str],
    boundary_markers: bool = False,
) -> set[str]:
    marked = f"^{word}$" if boundary_markers else word
    return {
        marked[index : index + size]
        for size in sizes
        for index in range(len(marked) - size + 1)
    } | (set(word) & letters)


@lru_cache(maxsize=100_000)
def language_scores(word: str) -> tuple[LanguageScore, ...]:
    """Rank EN/DE/FR/SK using one comparable model of the isolated word."""
    normalized = unicodedata.normalize("NFC", word).lower()
    if len(normalized) < 3 or not normalized.isalpha():
        return ()
    profile = _router_profile()
    languages = tuple(profile["languages"])
    totals = [0.0] * len(languages)
    matched = 0
    marked = f"^{normalized}$"
    weights = profile["weights"]
    for size in profile["gram_sizes"]:
        for index in range(len(marked) - size + 1):
            values = weights.get(marked[index : index + size])
            if values is None:
                continue
            matched += 1
            for language_index, value in enumerate(values):
                totals[language_index] += value
    if not matched:
        return ()
    return tuple(sorted(
        (LanguageScore(language, totals[index]) for index, language in enumerate(languages)),
        key=lambda result: result.score,
        reverse=True,
    ))


def detect_language(word: str) -> str | None:
    """Return the most likely EN/DE/FR/SK language from the word alone."""
    ranking = language_scores(word)
    return ranking[0].language if ranking else None


def _unit_evidence(
    word: str,
    sizes: tuple[int, ...],
    letters: frozenset[str],
    weights: dict[str, float],
    boundary_markers: bool = False,
) -> tuple[float, int, float]:
    word_features = _features(word, sizes, letters, boundary_markers)
    known = word_features & weights.keys()
    score = (
        sum(weights[feature] for feature in sorted(known)) / len(known)
        if known
        else -100.0
    )
    support = len(known)
    return score, support, support / max(1, len(word_features))


def _word_evidence(word: str, language: str) -> dict:
    normalized = unicodedata.normalize("NFC", word).lower()
    result = dict(score=-100.0, support=0, coverage=0.0, stem=normalized,
                  ending="", scored_unit=normalized, **{"is_" + language: False})
    if len(normalized) < 3 or not normalized.isalpha():
        return result
    profile = _profile(language)

    def score(text):
        return _unit_evidence(text, tuple(profile["gram_sizes"]),
                              frozenset(profile["informative_letters"]), profile["weights"],
                              profile.get("boundary_markers", False))

    def passes(evidence, threshold):
        return (evidence[0] >= threshold and evidence[1] >= profile["minimum_support"]
                and evidence[2] >= profile["minimum_coverage"])

    evidence = score(normalized)
    stem, ending, scored_unit = normalized, "", normalized
    if language == "german":
        # Preserve the already calibrated German statistical stripping path.
        for suffix in sorted(profile["slovak_endings"], key=lambda item: (-len(item), item)):
            if not normalized.endswith(suffix) or len(normalized) - len(suffix) < 4:
                continue
            base = normalized[:-len(suffix)]
            candidate = score(base)
            if passes(candidate, profile["stripped_stem_threshold"]) and candidate[0] > evidence[0]:
                evidence, stem, ending, scored_unit = candidate, base, suffix, base

    candidates = [r for r in reading_candidates(normalized) if r.language == language]
    if len(candidates) == 1:
        reading = candidates[0]
        # Known morphology exposes a base/member to the SAME corpus gate. It
        # never bypasses that gate or treats a matching suffix as proof by itself.
        units = [reading.stem]
        if len(reading.parts) > 1:
            units.append(reading.member)
        for unit in units:
            candidate = score(unit)
            if passes(candidate, profile["threshold"]):
                evidence = candidate
                stem, ending, scored_unit = reading.stem, reading.ending, unit
                break
    result.update(score=evidence[0], support=evidence[1], coverage=evidence[2],
                  stem=stem, ending=ending, scored_unit=scored_unit,
                  **{"is_" + language: passes(evidence, profile["threshold"])})
    return result


@lru_cache(maxsize=100_000)
def german_evidence(word: str) -> GermanEvidence:
    """German-vs-Slovak routing evidence, not permission to divide at any point."""
    return GermanEvidence(**_word_evidence(word, "german"))


def is_german(word: str) -> bool:
    """Return whether the German corpus profile flags the word or supported base."""
    return german_evidence(word).is_german


@lru_cache(maxsize=100_000)
def french_evidence(word: str) -> FrenchEvidence:
    """French-vs-Slovak routing evidence, not permission to divide at any point."""
    return FrenchEvidence(**_word_evidence(word, "french"))


def is_french(word: str) -> bool:
    """Return whether the French corpus profile flags the word or supported base."""
    return french_evidence(word).is_french


@lru_cache(maxsize=100_000)
def english_evidence(word: str) -> EnglishEvidence:
    """English-vs-Slovak routing evidence, not permission to divide at any point."""
    return EnglishEvidence(**_word_evidence(word, "english"))


def is_english(word: str) -> bool:
    """Return whether the English corpus profile flags the word or supported base."""
    return english_evidence(word).is_english
