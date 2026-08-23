# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
slabika — syllabification and hyphenation of Slovak.

The package has a shared linguistic foundation and distinct outputs:

    phonology     shared phoneme inventory: quantity, voicing, place, manner
    syllabify     phonotactic division of the spoken word into syllables
    typo          legal written-word break points under PSP conventions
    phonotactics  well-formedness, rhythmic law, preposition vocalization

Syllabification and typographic word division use the same phonological and
morphological analysis, but each applies its own boundary rules.

Typical use::

    >>> import slabika
    >>> slabika.syllables("najneuveriteľnejšími")
    ['naj', 'ne', 'u', 've', 'ri', 'teľ', 'nej', 'ší', 'mi']
    >>> slabika.hyphenate("Prekladateľský", separator="-")
    'Pre-kla-da-teľ-ský'
"""

from .phonology import (
    is_consonant,
    is_diphthong,
    is_long_syllable,
    is_vowel,
    split_into_phonemes,
)
from .phonotactics import (
    apply_rhythmic_law,
    check_preposition_form,
    check_rhythmic_law,
    is_phonotactically_valid,
)
from .syllabify import get_syllables as syllables
from .typo import break_points, divisions, hyphenate

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "apply_rhythmic_law",
    "break_points",
    "check_preposition_form",
    "check_rhythmic_law",
    "divisions",
    "hyphenate",
    "is_consonant",
    "is_diphthong",
    "is_long_syllable",
    "is_phonotactically_valid",
    "is_vowel",
    "split_into_phonemes",
    "syllables",
]
