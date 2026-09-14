# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Regression mechanisms discovered while comparing the complete release corpus."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_composita_grammar import SUPPLEMENT, build
from sapfo_grammar.induction import Reading, induce, inventory
from sapfo_grammar.supplement import load_supplement, supplement_inventory
from sapfo_grammar.synth import (
    adjective_paradigm,
    closed_class_paradigms,
    noun_paradigm,
    verb_paradigm,
)


def test_short_verb_exports_the_full_participle_stem():
    forms = frozenset(verb_paradigm("chc", "rozumieť").values())
    reading = Reading("verb", "rozumieť", "chc", "chcieť", forms, forms - {"chcieť"})
    data = inventory([(reading, reading.support)])
    assert "chc" not in data["heads"]
    assert "chceným" in data["head_paradigms"]["chcen"]["verb"]
    assert "chceniem" not in data["head_paradigms"]["chcen"]["verb"]


def test_adverb_derivation_does_not_fabricate_corpus_support():
    forms = frozenset(adjective_paradigm("statn", "pekný").values())
    reading = Reading("adj", "pekný", "statn", "statný", forms, forms - {"statný"})
    data = inventory([(reading, reading.support)])
    assert "statne" in data["head_paradigms"]["statn"]["root"]
    assert data["analyses"][0]["derived_forms"] == ["statne"]
    assert "statne" not in data["analyses"][0]["support"]


def test_zero_ending_oblique_is_not_a_standalone_head():
    corpus = set(noun_paradigm("škár", "dáma").values())
    data = inventory(induce(corpus, corpus))
    assert "škáry" in data["head_paradigms"]["škár"]["lemma"]
    assert "škár" not in data["head_paradigms"]["škár"]["lemma"]
    assert any("škár" in a["forms"] for a in data["analyses"])


def test_anatomical_plural_competes_with_false_use_lemma():
    corpus = {
        "ucho",
        "ucha",
        "uchu",
        "uchom",
        "uchá",
        "uši",
        "uší",
        "ušiach",
        "ušiam",
        "ušami",
        "uše",
    }
    assert {"uši", "uší", "ušiam", "ušiach", "ušami"} <= set(noun_paradigm("uch", "mesto").values())
    assert "uše" not in inventory(induce(corpus, corpus))["first_members"]


def test_numeral_one_cannot_become_a_feminine_noun():
    corpus = set(closed_class_paradigms()["jeden"])
    assert any(r.pos == "pron" and r.lemma == "jeden" for r, own in induce(corpus, corpus))
    assert "jedno" not in inventory(induce(corpus, corpus))["first_members"]


def test_bound_plural_alternation_is_exported():
    supplement = load_supplement(SUPPLEMENT)
    result = inventory([])
    result["first_members"]["vetro"] = "noun stem"
    data = supplement_inventory(result, supplement, {"vetroplacha", "vetroplasi"})
    assert "placha" in data["head_paradigms"]["plach"]["lemma"]
    assert "plasi" in data["head_paradigms"]["plas"]["lemma"]
    assert "plachi" not in data["head_paradigms"]["plach"]["lemma"]


def test_authored_bound_adjective_requires_a_licensed_corpus_example():
    result = inventory([])
    result["first_members"]["tučno"] = "adjective"
    result = supplement_inventory(result, load_supplement(SUPPLEMENT), {"tučnotvára"})
    assert "tvára" in result["head_paradigms"]["tvár"]["root"]
    assert result["analyses"] == []
    assert result["supplement_evidence"][-1]["attested_examples"] == ["tučnotvára"]
    absent = supplement_inventory(inventory([]), load_supplement(SUPPLEMENT), {"tučnotvára"})
    assert "tvár" not in absent["heads"]


@pytest.fixture
def candidate(monkeypatch):
    corpus = {"vetroplacha", "vetroplasi", "uše", "tučnotvára", "svätoplukovo"}
    for root, pattern in [
        ("statn", "pekný"),
        ("sam", "pekný"),
        ("svät", "pekný"),
        ("tučn", "pekný"),
    ]:
        corpus |= set(adjective_paradigm(root, pattern).values())
    for root, pattern in [
        ("škár", "dáma"),
        ("uch", "mesto"),
        ("tren", "vysvedčenie"),
        ("vietor", "vietor"),
    ]:
        corpus |= set(noun_paradigm(root, pattern).values())
    corpus |= set(verb_paradigm("chc", "rozumieť").values())
    data = build(corpus, supplement=load_supplement(SUPPLEMENT))
    engine = importlib.import_module("slabika.syllabify")
    monkeypatch.setattr(engine, "_GENERATED_FIRST_MEMBERS", frozenset(data["first_members"]))
    monkeypatch.setattr(
        engine,
        "_INFERRED_FIRST_MEMBERS",
        frozenset(k for k, v in data["first_members"].items() if v == "noun stem"),
    )
    monkeypatch.setattr(engine, "_GENERATED_HEADS", data["heads"])
    monkeypatch.setattr(engine, "_GENERATED_HEAD_PARADIGMS", data["head_paradigms"])
    return importlib.import_module("slabika")


@pytest.mark.parametrize(
    "word,expected",
    [
        ("samostatne", "sa·mo·stat·ne"),
        ("samochceným", "sa·mo·chce·ným"),
        ("vetroplacha", "vet·ro·pla·cha"),
        ("vetroplasi", "vet·ro·pla·si"),
        ("svätoškársku", "svä·toš·kár·sku"),
        ("ušetrení", "ušet·re·ní"),
        ("jednotke", "jed·not·ke"),
        ("tristojednotke", "tri·sto·jed·not·ke"),
        ("tučnotvára", "tuč·no·tvá·ra"),
        ("Svätoplukovo", "Svä·to·plu·ko·vo"),
    ],
)
def test_candidate_preserves_clear_morphological_division(candidate, word, expected):
    assert candidate.hyphenate(word) == expected
