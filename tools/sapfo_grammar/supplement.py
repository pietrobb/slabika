# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Explicit project-authored lexical assumptions, separate from induced evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .adjective_patterns import ADJECTIVE_PATTERNS
from .alternations import get_alternated_root
from .noun_patterns import NOUN_PATTERNS, NOUN_ALTERNATIONS
from .synth import adjective_paradigm, normalize_soft_consonants, noun_paradigm


def bound_forms(head: dict) -> set[str]:
    synth = adjective_paradigm if head.get("pos", "sub") == "adj" else noun_paradigm
    return set(synth(head["root"], head["pattern"]).values())


def load_supplement(path: Path) -> dict:
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("schema_version") != 1 or not data.get("source"):
        raise ValueError("supplement needs schema_version 1 and an explicit source")
    forms = data["surface_forms"]
    if len(forms) != len(set(forms)) or any(
        not isinstance(f, str) or not f.isalpha() or f != f.lower() for f in forms
    ):
        raise ValueError("supplement forms must be unique lowercase words")
    for member in data["first_members"]:
        form, kind = member["form"], member["kind"]
        if not form.isalpha() or form != form.lower() or len(form) < 3:
            raise ValueError("invalid first member")
        if kind not in {"bound", "indeclinable"}:
            raise ValueError("unknown first-member kind")
        if not member["examples"] or any(
            not e.startswith(form) or len(e) <= len(form) for e in member["examples"]
        ):
            raise ValueError("first member needs compound examples")
    for head in data["bound_heads"]:
        root, pos = head["root"], head.get("pos", "sub")
        if not root.isalpha() or root != root.lower() or len(root) < 3:
            raise ValueError("invalid bound head")
        patterns = {"sub": NOUN_PATTERNS, "adj": ADJECTIVE_PATTERNS}.get(pos, {})
        if head["pattern"] not in patterns or not head.get("reason") or head["pattern"] == "môj":
            raise ValueError("bound head needs a valid part of speech, pattern and reason")
        paradigm = bound_forms(head)
        if not head["examples"] or any(
            not any(e.endswith(f) and len(e) > len(f) for f in paradigm) for e in head["examples"]
        ):
            raise ValueError("bound head needs compound examples")
    return {**data, "sha256": hashlib.sha256(raw).hexdigest()}


def supplement_inventory(result: dict, data: dict, corpus: set[str]) -> dict:
    """Project bound heads with grammar; never pretend they are standalone words.

    Examples must occur in the original corpus, not in the authored additions.
    These authored declarations need one licensed occurrence, not statistical
    induction support. They never fabricate owned cells; the audit labels them.
    """
    evidence = []
    for member in data.get("first_members", []):
        examples = sorted(set(member["examples"]) & corpus)
        if not examples or (member["kind"] == "indeclinable" and member["form"] not in corpus):
            continue
        result["first_members"][member["form"]] = member["kind"]
        evidence.append({**member, "attested_examples": examples})
    for head in data.get("bound_heads", []):
        root, pos = head["root"], head.get("pos", "sub")
        forms = bound_forms(head)
        spellings = (
            {root}
            if pos == "adj"
            else {
                get_alternated_root(root, NOUN_ALTERNATIONS.get(head["pattern"], []), i)
                for i in range(12)
            }
        )
        examples = sorted(
            e
            for e in set(head["examples"]) & corpus
            if any(e.endswith(f) and e[: -len(f)] in result["first_members"] for f in forms)
        )
        if not examples:
            continue
        role = "root" if pos == "adj" else "lemma"
        for spelling in sorted(
            spellings | {normalize_soft_consonants(s + "i")[:-1] for s in spellings}
        ):
            licensed = {f for f in forms if f.startswith(spelling)}
            if not licensed:
                continue
            roles = result["head_paradigms"].setdefault(spelling, {})
            roles[role] = sorted(set(roles.get(role, [])) | licensed)
            if pos == "sub" or spelling not in result["heads"]:
                result["heads"][spelling] = role
        evidence.append({**head, "attested_examples": examples, "generated_forms": sorted(forms)})
    result["supplement_evidence"] = evidence
    return result
