# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Induce lexemes from surface forms and project grammar, without a lexicon.

Evidence counts distinct forms, not syncretic grammatical cells. Ownership is
still a heuristic, not a decision about the meaning of homographs.
"""

from __future__ import annotations

from dataclasses import dataclass

from .adjective_patterns import ADJECTIVE_PATTERNS
from .alternations import get_alternated_root
from .noun_patterns import NOUN_ALTERNATIONS, NOUN_PATTERNS
from .synth import (
    PRONOUN_ROOTS,
    adjective_paradigm,
    closed_class_paradigms,
    last_nucleus_long,
    noun_paradigm,
    normalize_soft_consonants,
    verb_paradigm,
)
from .verb_patterns import VERB_PATTERNS

NOUN_CITATIONS = {
    p: tuple(sorted({s[0].replace("'", ""), s[6].replace("'", "")}))
    for p, s in NOUN_PATTERNS.items()
}
ADJ_CITATIONS = {
    p: tuple(sorted({suffixes[0] for suffixes in data.values()}))
    for p, data in ADJECTIVE_PATTERNS.items()
    if p != "môj"
}
CLOSED_PARADIGMS = closed_class_paradigms()
SOFT_FINALS = frozenset("cčšžďťňjľ")


@dataclass(frozen=True)
class Reading:
    pos: str
    pattern: str
    root: str
    lemma: str
    forms: frozenset[str]
    support: frozenset[str]

    @property
    def key(self):
        return self.pos, self.pattern, self.root


def adjective_admissible(root: str, pattern: str) -> bool:
    """Respect rhythmic shortening and the closed possessive/pronominal classes."""
    if pattern == "otcov":
        return len(root) > 3 and root.endswith(("ov", "in"))
    if pattern == "môj":
        return root in PRONOUN_ROOTS
    if pattern in ("krásny", "rýdzi"):
        return last_nucleus_long(root)
    if pattern in ("pekný", "cudzí"):
        return not last_nucleus_long(root)
    return True


def readings(probe: str, corpus: set[str]):
    """Enumerate citation cuts; require an exact synthesis round trip."""
    for lemma, forms in CLOSED_PARADIGMS.items():
        support = (forms & corpus) - {lemma}
        if probe in forms and lemma in corpus and support:
            yield Reading("pron", "closed", lemma, lemma, forms, support)
    for pos, patterns, synth in (
        ("sub", NOUN_CITATIONS, noun_paradigm),
        ("adj", ADJ_CITATIONS, adjective_paradigm),
        ("verb", {p: (d[0] + "ť",) for p, d in VERB_PATTERNS.items()}, verb_paradigm),
    ):
        for pattern, endings in patterns.items():
            for ending in endings:
                if not probe.endswith(ending):
                    continue
                root = probe[: -len(ending)] if ending else probe
                if (
                    len(root) < 2
                    or (
                        pos == "sub"
                        and pattern in {"dub", "chlap", "papier", "stroj", "čaj"}
                        and root[-1] in "aáäeéiíoóôuúyý"
                    )
                    or (
                        pos == "sub"
                        and len(root) > 4
                        and root.endswith("osť")
                        and pattern != "kosť"
                    )
                    or (
                        pos == "sub"
                        and len(get_alternated_root(root, NOUN_ALTERNATIONS.get(pattern, []), 1))
                        < 2
                    )
                ):
                    continue
                if pos == "adj" and (
                    not adjective_admissible(root, pattern)
                    or (
                        pattern == "cudzí"
                        and not any(root + s in corpus for s in ("ieho", "iemu", "ích", "ími"))
                    )
                ):
                    continue
                paradigm = synth(root, pattern)
                if paradigm is None:
                    continue
                forms = frozenset(paradigm.values())
                if probe not in forms:
                    continue
                citation_key = {"sub": 0, "adj": ("muž", "živ", "sg", "nom"), "verb": "inf"}[pos]
                lemma = paradigm[citation_key]
                if lemma not in corpus:
                    continue
                support = (forms & corpus) - {lemma}
                if support:
                    yield Reading(
                        "poss" if pattern == "otcov" else pos, pattern, root, lemma, forms, support
                    )


def induce(candidates, corpus: set[str], min_support: int = 3):
    """Compete for distinct attested forms; retain the best reading per probe.

    Repeated probes of the same analysis are one claim, not independent
    witnesses. Genuine homographs remain distinct and deterministic tie-breaking
    must not be mistaken for linguistic disambiguation.
    """
    lexemes = {}
    for probe in sorted(set(candidates)):
        best = max(
            readings(probe, corpus), key=lambda r: (len(r.support), r.pos == "pron"), default=None
        )
        if best is not None:
            lexemes.setdefault(best.key, best)
    scored = sorted(
        lexemes.values(), key=lambda r: (-len(r.support), r.pos != "pron", r.lemma, r.key)
    )
    owners = {}
    for reading in scored:
        for form in reading.support:
            owners.setdefault(form, reading.key)
    survivors = []
    for reading in scored:
        own = frozenset(f for f in reading.support if owners[f] == reading.key)
        if len(own) >= min_support:
            survivors.append((reading, own))
    return survivors


def compound_stem(reading: Reading) -> str:
    """Use the oblique noun stem, not its mobile citation vowel (vietor/vetr-)."""
    if reading.pos == "sub":
        return get_alternated_root(reading.root, NOUN_ALTERNATIONS.get(reading.pattern, []), 1)
    return reading.root


def inventory(survivors):
    """Export exact grammatical head forms, with auditable supporting analyses.

    The runtime must not append universal endings to these heads: a verb's
    paradigm cannot license a noun ending merely because their roots coincide.
    No previous inventory or lexical collision stop-list is merged here.
    """
    members, heads, head_paradigms, analyses = {}, {}, {}, []
    head_priority = {"root": 0, "verb": 1, "lemma": 2}
    for reading, own in sorted(survivors, key=lambda item: item[0].key):
        pos, root, lemma = reading.pos, reading.root, reading.lemma
        stem = compound_stem(reading)
        derived_forms = (
            {root + "e"}
            if pos == "adj" and reading.pattern in {"pekný", "krásny"} and root.endswith("n")
            else set()
        )
        if pos in ("sub", "adj"):
            member = stem + ("e" if stem[-1] in SOFT_FINALS else "o")
            if len(member) >= 3 and member.isalpha():
                kind = "noun stem" if pos == "sub" else "adjective"
                if kind == "adjective" or member not in members:
                    members[member] = kind
        if pos in ("sub", "adj", "verb"):
            kind = {"sub": "lemma", "adj": "root", "verb": "verb"}[pos]
            floor = 3 if pos in ("sub", "adj") else 4
            for head in sorted(
                {
                    stem,
                    root,
                    normalize_soft_consonants(stem + "i")[:-1],
                    normalize_soft_consonants(root + "i")[:-1],
                }
                | (
                    {verb_paradigm(root, reading.pattern)["nt.muž.živ.sg.nom"][:-1]}
                    if pos == "verb"
                    else set()
                )
            ):
                licensed = {
                    f
                    for f in reading.forms | derived_forms
                    if f.startswith(head) and (pos != "sub" or f != head or lemma == head)
                }
                if len(head) < floor or not head.isalpha() or not licensed:
                    continue
                previous = heads.get(head)
                if head_priority[kind] > head_priority.get(previous, -1):
                    heads[head] = kind
                head_paradigms.setdefault(head, {}).setdefault(kind, set()).update(licensed)
                # The summary kind is not the runtime permission. Every POS keeps
                # its exact forms, including when a homograph has a higher-ranked
                # summary kind (rozhodnúť must not erase rozhodný).
        analyses.append(
            {
                "pos": pos,
                "pattern": reading.pattern,
                "root": root,
                "lemma": lemma,
                "compound_stem": stem,
                "forms": sorted(reading.forms),
                "derived_forms": sorted(derived_forms),
                "support": sorted(reading.support),
                "owned": sorted(own),
            }
        )
    return {
        "note": "experimental: local grammar and project surface forms only",
        "schema_version": 3,
        "first_members": dict(sorted(members.items())),
        "heads": dict(sorted(heads.items())),
        "head_paradigms": {
            h: {k: sorted(fs) for k, fs in sorted(roles.items())}
            for h, roles in sorted(head_paradigms.items())
        },
        "analyses": analyses,
    }
