# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Exception tables loaded from the CC0 data layer."""

import json
from importlib.resources import files
from typing import Final

_RAW = json.loads(
    files("slabika").joinpath("data/exceptions.json").read_text(encoding="utf-8")
)

#: Words whose boundary no general rule derives reliably.
LEXICAL_SYLLABIFICATIONS: Final[dict[str, tuple[str, ...]]] = {
    word: tuple(parts) for word, parts in _RAW["lexical_syllabifications"].items()
}

#: Stems whose prefix-shaped opening has lexicalized and forms no boundary.
LEXICALIZED_STEMS: Final[tuple[str, ...]] = tuple(_RAW["lexicalized_stems"])

#: Adjacent vowel spellings that form one nucleus in a foreign lexical stem.
FOREIGN_NUCLEUS_SPELLINGS: Final[dict[str, str]] = dict(
    _RAW["foreign_nucleus_spellings"]
)

#: Unadapted foreign spellings that Slovak syllable rules must not guess at.
UNHYPHENATED_FOREIGN_WORDS: Final[frozenset[str]] = frozenset(
    _RAW["unhyphenated_foreign"]
)
