# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Pronunciation-backed foreign stems, projected onto Slovak PSP division rules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from .english import english_points
from .phonology import is_vowel


@dataclass(frozen=True)
class ForeignReading:
    language: str
    stem: str
    ending: str
    parts: tuple[tuple[tuple[str, str], ...], ...]

    @property
    def member(self) -> str:
        return "".join(spelling for spelling, _ in self.parts[-1])


@lru_cache(maxsize=1)
def _inventory():
    data = json.loads((Path(__file__).parent / "data/foreign_readings.json").read_text(
        encoding="utf-8"
    ))
    stems = {}
    for language in ("english", "german", "french"):
        source = data[language]
        entries = list(source["bases"])
        if "compounds" in source:
            compounds = source["compounds"]
            terminals = compounds.get("terminals", [compounds.get("terminal")])
            entries.extend({"parts": [*head.split("|"), terminal]} for head in compounds["heads"]
                           for terminal in terminals)
        for entry in entries:
            parts = tuple(tuple((unit, source["units"].get(unit, unit))
                                for unit in part.split()) for part in entry["parts"])
            stem = "".join(unit for part in parts for unit, _ in part)
            stems[stem] = (language, parts, entry.get("inflect", True))
    return stems, frozenset(data["endings"])


@lru_cache(maxsize=100_000)
def reading_candidates(word: str) -> tuple[ForeignReading, ...]:
    """Known spelling analyses only; none of these is yet authorized by a profile."""
    stems, endings = _inventory()
    if word in stems:
        language, parts, _ = stems[word]
        return (ForeignReading(language, word, "", parts),)
    candidates = []
    for cut in range(3, len(word)):
        if word[cut:] not in endings:
            continue
        found = stems.get(word[:cut])
        if found is not None and found[2]:
            candidates.append(ForeignReading(found[0], word[:cut], word[cut:], found[1]))
    return tuple(candidates)


@lru_cache(maxsize=100_000)
def foreign_reading(word: str) -> ForeignReading | None:
    """Route only an unambiguous profile with a matching, fully described reading."""
    # Language scoring consumes reading_candidates, not this routing function.
    from .language import english_evidence, french_evidence, german_evidence

    candidates = reading_candidates(word.lower())
    if not candidates:
        return None
    evidence = {"english": english_evidence(word), "german": german_evidence(word),
                "french": french_evidence(word)}
    flagged = {lang for lang, result in evidence.items() if getattr(result, "is_" + lang)}
    if len(flagged) != 1:
        return None
    language = next(iter(flagged))
    result = evidence[language]
    matching = [r for r in candidates if r.language == language
                and r.stem == result.stem and r.ending == result.ending]
    return matching[0] if len(matching) == 1 else None


def foreign_points(
    word: str, psp_points: Callable[[str], list[int]]
) -> tuple[set[int], set[int], set[int]] | None:
    """Map PSP offsets back to the original spelling; never import foreign breaks."""
    reading = foreign_reading(word)
    if reading is None:
        return english_points(word)
    # Lowercasing may expand a Unicode letter. Never map those offsets to input.
    if len(word.lower()) != len(word):
        return None
    points = set()
    offset = 0
    for index, part in enumerate(reading.parts):
        mapping = [offset]
        proxy = ""
        for spelling, symbol in part:
            proxy += symbol
            offset += len(spelling)
            mapping.append(offset)
        last = index == len(reading.parts) - 1
        ending = reading.ending if last else ""
        if ending and is_vowel(ending[0]):
            # Inflection resyllabifies the final consonant: stein + ovi -> stei-no-vi.
            proxy += ending
            mapping.extend(range(offset + 1, offset + len(ending) + 1))
        points.update(mapping[p] for p in psp_points(proxy))
        if not last:
            points.add(offset)
        elif ending and not is_vowel(ending[0]):
            # Consonant-initial Slovak suffix retains the morpheme seam (PSP V).
            points.add(offset)
            points.update(offset + p for p in psp_points(ending))
    contextual = {1} & points if is_vowel(word[0]) else set()
    points -= contextual
    points.discard(len(word) - 1)
    contextual.discard(len(word) - 1)
    return points, set(), contextual
