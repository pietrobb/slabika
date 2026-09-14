# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Nominal cells alone do not establish a soft adjective or a consonantal stem."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_composita_grammar import SUPPLEMENT, build
from sapfo_grammar.induction import readings
from sapfo_grammar.supplement import load_supplement
from sapfo_grammar.synth import adjective_paradigm, noun_paradigm


@pytest.mark.parametrize("root", ["tren", "chcen", "tvoren"])
def test_deverbal_noun_is_not_soft_adjective_evidence(root):
    corpus = set(noun_paradigm(root, "vysvedčenie").values())
    corpus |= set(adjective_paradigm(root, "pekný").values())
    assert not any(r.pattern == "cudzí" for r in readings(root + "í", corpus))


def test_real_soft_adjective_retains_characteristic_oblique_evidence():
    corpus = {"oslí", "oslia", "oslie", "oslieho", "osliemu", "osľom", "osľou", "oslích"}
    assert any(r.pattern == "cudzí" for r in readings("oslí", corpus))
    forms = set(adjective_paradigm("osl", "cudzí").values())
    assert {"osľom", "osľou", "oslej", "oslieho", "oslí"} <= forms
    assert not {"oslom", "oslou", "osľieho", "osľí"} & forms


@pytest.mark.parametrize("root,pattern", [("po", "papier"), ("auto", "dub"), ("neo", "chlap")])
def test_vowel_final_root_cannot_borrow_a_consonantal_noun_pattern(root, pattern):
    corpus = set(noun_paradigm(root, pattern).values())
    assert not any(r.pattern == pattern for r in readings(root, corpus))


def test_bound_heads_use_inflected_compound_evidence(monkeypatch):
    corpus = {
        "názvoslovie",
        "múdrosloviu",
        "samostatnosť",
        "samostatnosti",
        "žltochvost",
        "žltochvostovi",
    }
    corpus |= set(noun_paradigm("názov", "pojem").values())
    for root, pattern in [("múdr", "krásny"), ("sam", "pekný"), ("žlt", "pekný")]:
        corpus |= set(adjective_paradigm(root, pattern).values())
    data = build(corpus, supplement=load_supplement(SUPPLEMENT))
    assert "sloviu" in data["head_paradigms"]["slov"]["lemma"]
    assert "statnosti" in data["head_paradigms"]["statnost"]["lemma"]
    assert "chvostovi" in data["head_paradigms"]["chvost"]["lemma"]
    assert not any(a["lemma"] in {"slovie", "statnosť"} for a in data["analyses"])
    engine = importlib.import_module("slabika.syllabify")
    monkeypatch.setattr(engine, "_GENERATED_FIRST_MEMBERS", frozenset(data["first_members"]))
    monkeypatch.setattr(
        engine,
        "_INFERRED_FIRST_MEMBERS",
        frozenset(k for k, v in data["first_members"].items() if v == "noun stem"),
    )
    monkeypatch.setattr(engine, "_GENERATED_HEADS", data["heads"])
    monkeypatch.setattr(engine, "_GENERATED_HEAD_PARADIGMS", data["head_paradigms"])
    api = importlib.import_module("slabika")
    assert api.hyphenate("názvoslovie") == "náz·vo·slo·vie"
    assert api.hyphenate("samostatnosť") == "sa·mo·stat·nosť"
    assert api.hyphenate("žltochvostovi") == "žl·to·chvos·to·vi"
