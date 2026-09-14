# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Lexicon-free paradigm synthesis for the build-time grammar experiment.

Noun/adjective synthesis is adapted from Sapfo's MorphologicalSynthesizer,
without lexical overrides. Closed-class paradigms below encode grammatical
alternations, not entries extracted from a dictionary.
"""

from __future__ import annotations

import re

from .adjective_patterns import ADJECTIVE_PATTERNS, ADJ_PALATALIZATION_PATTERNS
from .alternations import get_alternated_root
from .noun_patterns import CASE_INDEX, NOUN_ALTERNATIONS, NOUN_GENDER, NOUN_PATTERNS
from .verb_patterns import L_PARTICIPLE_SUFFIXES, PRESENT_SUFFIXES, VERB_PATTERNS

_SOFT_TO_HARD = {"ť": "t", "ď": "d", "ň": "n", "ľ": "l"}
_I_VOWELS = ("ia", "ie", "iu", "í", "i", "é", "e")
VOWELS = frozenset("aáäeéiíoóôuúyý")
LONG_NUCLEI = frozenset(("á", "é", "í", "ó", "ô", "ú", "ý", "ŕ", "ĺ", "ia", "ie", "iu"))
PRONOUN_ROOTS = ("môj", "tvoj", "svoj", "naš", "vaš")

CASES = ("nom", "gen", "dat", "acc", "loc", "ins")
NUMBERS = ("sg", "pl")
ADJ_KEYS = (
    ("muž", "živ", "sg"),
    ("muž", "neživ", "sg"),
    ("žen", None, "sg"),
    ("str", None, "sg"),
    ("muž", "živ", "pl"),
    ("muž", "neživ", "pl"),
    ("žen", None, "pl"),
    ("str", None, "pl"),
)


def last_nucleus_long(root: str) -> bool:
    nuclei = [(m.start(), m.group()) for m in re.finditer("ia|ie|iu|[aáäeéiíoóôuúyýŕĺ]", root)]
    nuclei.extend(
        (i, c)
        for i, c in enumerate(root)
        if c in "rl"
        and 0 < i < len(root) - 1
        and root[i - 1] not in VOWELS
        and root[i + 1] not in VOWELS
    )
    return bool(nuclei and max(nuclei)[1] in LONG_NUCLEI)


def normalize_soft_consonants(form: str) -> str:
    """Drop the háčik before an i-vowel: oblasťi -> oblasti, hosťia -> hostia."""
    for soft, hard in ((s, h) for s, h in _SOFT_TO_HARD.items() if s in form):
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
    return (
        {**out, **dict(enumerate("uši uší ušiam uši ušiach ušami".split(), 12))}
        if root == "uch" and pattern == "mesto"
        else out
    )


def adjective_paradigm(root: str, pattern: str) -> dict[tuple, str] | None:
    """Every form, including the citation/oblique alternation of môj and náš."""
    data = ADJECTIVE_PATTERNS.get(pattern)
    if data is None or (pattern == "môj" and root not in PRONOUN_ROOTS):
        return None
    out: dict[tuple, str] = {}
    for key in ADJ_KEYS:
        suffixes = data.get(key)
        if suffixes is None:
            continue
        for case, suffix in zip(CASES, suffixes):
            stem = (
                root[:-1] + {"d": "ď", "t": "ť", "n": "ň", "l": "ľ"}.get(root[-1], root[-1])
                if pattern in ADJ_PALATALIZATION_PATTERNS
                else root
            )
            if pattern == "môj":
                # môjho/môjmu but moja/mojím; náš/naša/našich/naším.
                if root == "môj" and suffix not in ("", "ho", "mu"):
                    stem = "moj"
                if root in ("naš", "vaš"):
                    stem = root.replace("a", "á") if suffix in ("", "ho", "mu") else root
                if key[2] == "pl" and case in ("dat", "ins"):
                    suffix = {"dat": "ím", "ins": "imi"}[case]
            out[(*key, case)] = (
                normalize_soft_consonants(stem + suffix)
                if pattern in ADJ_PALATALIZATION_PATTERNS
                else stem + suffix
            )
    return out


def closed_class_paradigms() -> dict[str, frozenset[str]]:
    """Finite pronominal/numeral inflection, used only as competing analyses."""
    result = {}
    for root in PRONOUN_ROOTS:
        forms = adjective_paradigm(root, "môj")
        result[forms[("muž", "živ", "sg", "nom")]] = frozenset(forms.values())
    # Suppletive demonstrative stems and numeral oba/obe.
    demonstrative = frozenset("ten toho tomu tom tým tá tej tú tou to tí tých tými tie".split())
    result["ten"] = demonstrative
    result["tento"] = frozenset(f + "to" for f in demonstrative)
    result["tamten"] = frozenset("tam" + f for f in demonstrative)
    result["oba"] = frozenset("oba obe obaja oboch obom oboma".split())
    result["obidva"] = frozenset("obidva obidve obidvaja obidvoch obidvom obidvoma".split())
    result["jeden"] = frozenset(
        "jeden jedného jednému jednom jedným jedna jednej jednou jednu jedno jedni jedny jedných jednými".split()
    )
    return result


def verb_paradigm(inf_stem: str, pattern: str) -> dict[str, str] | None:
    """Conjugation plus fully declined passive and present active participles.

    Present-stem alternations not derivable here remain an experimental
    limitation. Synthesis is a hypothesis: it is not lexical attestation.
    """
    data = VERB_PATTERNS.get(pattern)
    if data is None:
        return None
    inf_sfx, l_sfx, _v_sfx, nt_sfx, pres_marker, _imper, pres_class = data
    out = {"inf": normalize_soft_consonants(inf_stem + inf_sfx + "ť")}
    for (gender, number), ending in L_PARTICIPLE_SUFFIXES.items():
        out[f"l.{gender}.{number}"] = inf_stem + l_sfx + "l" + ending
    passive = normalize_soft_consonants(inf_stem + nt_sfx)
    adj_pattern = "krásny" if last_nucleus_long(passive) else "pekný"
    for key, form in adjective_paradigm(passive, adj_pattern).items():
        out["nt." + ".".join(str(k) for k in key)] = form
    pres_stem = inf_stem
    if pres_class == "ú" and inf_stem.endswith("ov"):
        pres_stem, pres_class = inf_stem[:-2] + "uj", "ujú"
    if pres_class in PRESENT_SUFFIXES:
        endings = (pres_marker + e for e in ("m", "š", "", "me", "te"))
        for key, ending in zip(
            ("1sg", "2sg", "3sg", "1pl", "2pl", "3pl"),
            (*endings, pres_class if pres_class != "ujú" else "ú"),
        ):
            out[f"pres.{key}"] = normalize_soft_consonants(pres_stem + ending)
        active = out["pres.3pl"] + "c"
        for key, form in adjective_paradigm(active, "rýdzi").items():
            out["active." + ".".join(str(k) for k in key)] = form
    return out


def noun_patterns_for(gender: str | None = None) -> tuple[str, ...]:
    """Pattern names, optionally restricted to one gender."""
    if gender is None:
        return tuple(NOUN_PATTERNS)
    return tuple(p for p in NOUN_PATTERNS if NOUN_GENDER.get(p) == gender)


__all__ = [
    "CASE_INDEX",
    "CASES",
    "NUMBERS",
    "NOUN_GENDER",
    "adjective_paradigm",
    "closed_class_paradigms",
    "last_nucleus_long",
    "noun_paradigm",
    "noun_patterns_for",
    "normalize_soft_consonants",
    "verb_paradigm",
]
