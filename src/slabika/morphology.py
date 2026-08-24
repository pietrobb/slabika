# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Morphological analysis over a morph lexicon induced from the corpus.

The lexicon in ``data/morphs.json`` is not a word list and not a list of
prefixes someone thought of. It is the set of morphs that makes the corpus
cheapest to write down, induced by tools/morph/induce.py: a morph is in it
because dropping it would cost more than keeping it. That is what lets this
module answer the question the syllabifier cannot answer from the spelling --
whether the letters after a prefix are a Slovak stem or the middle of a foreign
name.

Two numbers come out of the analysis and both are needed:

``parse``  the cheapest way to write the word as morphs. A boundary in it is a
           boundary the corpus pays for.
``price``  what that costs per character. Any string can be parsed -- the model
           can always buy letters one at a time -- so the boundary alone proves
           nothing. ucka is two morphs the corpus uses everywhere and is cheap;
           ust' has to be bought by the letter and is dear. The price is what
           separates a stem from a string of letters.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "morphs.json"

#: No Slovak morph is longer than this, and the cost of considering longer ones
#: is quadratic in the word, so the parse never looks past it.
_MAX_MORPH = 12


class Morphology:
    """The induced lexicon, and the parses it licenses."""

    def __init__(self, morphs: dict[str, int], tokens: int, alphabet: int = 65) -> None:
        self._morphs = morphs
        self._log_tokens = math.log(tokens) if tokens else 0.0
        self._log_a = math.log(alphabet + 1)

    @classmethod
    def load(cls, path: Path = _DATA) -> "Morphology":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(payload["morphs"], payload["tokens"])

    def morph_cost(self, morph: str) -> float:
        """What it costs to emit *morph*: cheap if the lexicon has it, dear if not."""
        n = self._morphs.get(morph)
        if n:
            return self._log_tokens - math.log(n)
        return (len(morph) + 1) * self._log_a + self._log_tokens

    @lru_cache(maxsize=8192)
    def _viterbi(self, word: str) -> tuple[tuple[str, ...], float]:
        best = [0.0] + [math.inf] * len(word)
        back = [0] * (len(word) + 1)
        for j in range(1, len(word) + 1):
            for i in range(max(0, j - _MAX_MORPH), j):
                c = best[i] + self.morph_cost(word[i:j])
                if c < best[j]:
                    best[j], back[j] = c, i
        parts, j = [], len(word)
        while j:
            parts.append(word[back[j]:j])
            j = back[j]
        return tuple(reversed(parts)), best[len(word)]

    def parse(self, word: str) -> tuple[str, ...]:
        """The cheapest analysis of *word* into morphs."""
        return self._viterbi(word.lower())[0]

    def price(self, word: str) -> float:
        """Cost of that analysis per character -- how foreign the string is."""
        word = word.lower()
        if not word:
            return 0.0
        return self._viterbi(word)[1] / len(word)

    def _cost_forbidding(self, word: str, position: int) -> float:
        """Cheapest analysis of *word* that does not cut at *position*."""
        best = [0.0] + [math.inf] * len(word)
        for j in range(1, len(word) + 1):
            if j == position:
                continue
            for i in range(max(0, j - _MAX_MORPH), j):
                if i == position:
                    continue
                c = best[i] + self.morph_cost(word[i:j])
                if c < best[j]:
                    best[j] = c
        return best[len(word)]

    def prefers_boundary(self, word: str, position: int) -> bool:
        """True when analysing *word* with a seam at *position* is the cheaper account.

        This is the whole question, asked without a threshold: the model already
        knows what every morph costs, so it can price the word both ways and say
        which account it would rather give. po|učka is cheaper cut, because po-
        and -ka and uč- are morphs it needs anyway; Bordu|rom is dearer cut,
        because urom is not a morph it has any other use for.

        Comparing the two accounts of one word is also what keeps the answer
        free of a length bias: a short stem is dear per character however
        Slovak it is, and it was that bias, not the morphology, that lost
        ne|učí its seam in the first attempt.
        """
        word = word.lower()
        with_seam = self._viterbi(word[:position])[1] + self._viterbi(word[position:])[1]
        return with_seam < self._cost_forbidding(word, position)

    def has_boundary(self, word: str, position: int) -> bool:
        """True when the cheapest analysis of *word* cuts at *position*."""
        at = 0
        for morph in self.parse(word):
            at += len(morph)
            if at == position:
                return True
            if at > position:
                return False
        return False


@lru_cache(maxsize=1)
def get_morphology() -> Morphology:
    return Morphology.load()
