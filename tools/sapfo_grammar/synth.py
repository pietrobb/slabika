# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Lexicon-free paradigm synthesis.

The synthesis in the sibling Sapfo project reads pattern overrides out of its
lexicon; those rows are the ones this project may not distribute. What is left
once they are gone is pure grammar — a table of case suffixes, the alternation
rules that reshape the root before the suffix is attached, and the orthographic
rule that drops the háčik before an i-vowel — and grammar needs no lexicon.

Vendored from sapfo/core/morphology.py (MorphologicalSynthesizer.synthesize_noun,
.synthesize_adjective and the normalization helpers) for build-time use by
tools/build_composita.py. Not part of the distributed package.
"""
from __future__ import annotations

from .adjective_patterns import ADJECTIVE_PATTERNS
from .alternations import get_alternated_root
from .noun_patterns import (
    CASE_INDEX,
    NOUN_ALTERNATIONS,
    NOUN_GENDER,
    NOUN_PATTERNS,
)
from .verb_patterns import (
    L_PARTICIPLE_SUFFIXES,
    PRESENT_SUFFIXES,
    VERB_PATTERNS,
)

# Slovak orthography: háčik (ˇ) is dropped before i, í, ia, ie, iu
# because these vowels inherently imply palatalization.
_SOFT_TO_HARD = {'ť': 't', 'ď': 'd', 'ň': 'n', 'ľ': 'l'}
_I_VOWELS = ('ia', 'ie', 'iu', 'í', 'i', 'é', 'e')  # longest first

CASES = ('nom', 'gen', 'dat', 'acc', 'loc', 'ins')
NUMBERS = ('sg', 'pl')
ADJ_KEYS = (
    ('muž', 'živ', 'sg'), ('muž', 'neživ', 'sg'), ('žen', None, 'sg'),
    ('str', None, 'sg'), ('muž', 'živ', 'pl'), ('muž', 'neživ', 'pl'),
    ('žen', None, 'pl'), ('str', None, 'pl'),
)


def normalize_soft_consonants(form: str) -> str:
    """Drop the háčik before an i-vowel: oblasťi -> oblasti, hosťia -> hostia."""
    for soft, hard in _SOFT_TO_HARD.items():
        for iv in _I_VOWELS:
            form = form.replace(soft + iv, hard + iv)
    return form


def noun_paradigm(root: str, pattern: str) -> dict[int, str] | None:
    """Every case form of *root* declined by *pattern*, keyed by CASE_INDEX."""
    paradigm = NOUN_PATTERNS.get(pattern)
    if paradigm is None:
        return None
    alternations = NOUN_ALTERNATIONS.get(pattern, [])
    out: dict[int, str] = {}
    for case_idx, raw in enumerate(paradigm):
        suffix = raw.replace("'", "")
        alt_root = get_alternated_root(root, alternations, case_idx)
        out[case_idx] = normalize_soft_consonants(alt_root + suffix)
    return out


def adjective_paradigm(root: str, pattern: str) -> dict[tuple, str] | None:
    """Every form of the adjective *root* declined by *pattern*."""
    data = ADJECTIVE_PATTERNS.get(pattern)
    if data is None:
        return None
    out: dict[tuple, str] = {}
    for key in ADJ_KEYS:
        suffixes = data.get(key)
        if suffixes is None:
            continue
        for case, suffix in zip(CASES, suffixes):
            out[(*key, case)] = root + suffix
    return out


def verb_paradigm(inf_stem: str, pattern: str) -> dict[str, str] | None:
    """The forms of a verb stem conjugated by *pattern*.

    Approximate where Sapfo reads the present stem out of its lexicon: the
    present stem is taken to be the infinitive stem, with the one derivation
    rule the -ovať class needs (pracov- -> pracuj-). Missing forms only cost
    the verb reading evidence, they never invent any.
    """
    data = VERB_PATTERNS.get(pattern)
    if data is None:
        return None
    inf_sfx, l_sfx, _v_sfx, nt_sfx, _pres_marker, _imper, pres_class = data
    out = {'inf': normalize_soft_consonants(inf_stem + inf_sfx + 'ť')}
    for (gender, number), ending in L_PARTICIPLE_SUFFIXES.items():
        out[f'l.{gender}.{number}'] = inf_stem + l_sfx + 'l' + ending
    for key, ending in (('m', 'ý'), ('f', 'á'), ('n', 'é'), ('p', 'í')):
        out[f'nt.{key}'] = normalize_soft_consonants(inf_stem + nt_sfx + ending)
    pres_stem = inf_stem
    if pres_class == 'ú' and inf_stem.endswith('ov'):
        pres_stem, pres_class = inf_stem[:-2] + 'uj', 'ujú'
    suffixes = PRESENT_SUFFIXES.get(pres_class)
    if suffixes is not None:
        for (person, number), ending in suffixes.items():
            out[f'pres.{person}{number}'] = normalize_soft_consonants(
                pres_stem + ending)
    return out


def noun_patterns_for(gender: str | None = None) -> tuple[str, ...]:
    """Pattern names, optionally restricted to one gender."""
    if gender is None:
        return tuple(NOUN_PATTERNS)
    return tuple(p for p in NOUN_PATTERNS if NOUN_GENDER.get(p) == gender)


__all__ = [
    'CASE_INDEX', 'CASES', 'NUMBERS', 'NOUN_GENDER',
    'adjective_paradigm', 'noun_paradigm', 'noun_patterns_for',
    'normalize_soft_consonants', 'verb_paradigm',
]
