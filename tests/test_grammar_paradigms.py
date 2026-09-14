# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Independent examples for the closed-class and participial grammar repairs."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from sapfo_grammar.induction import Reading, induce, inventory  # noqa: E402
from sapfo_grammar.synth import (  # noqa: E402
    adjective_paradigm,
    closed_class_paradigms,
    verb_paradigm,
)


@pytest.mark.parametrize(
    "root,citation,required,forbidden",
    [
        (
            "naš",
            "náš",
            {
                "naša",
                "naše",
                "naši",
                "našej",
                "náš",
                "našich",
                "naším",
                "našimi",
                "našom",
                "našou",
                "našu",
                "nášho",
                "nášmu",
            },
            {"naš", "našho", "našmu", "našim"},
        ),
        (
            "vaš",
            "váš",
            {"vaša", "vaše", "vaši", "vašej", "vašich", "vaším", "vašimi"},
            {"vaš", "vašho", "vašmu", "vašim"},
        ),
        (
            "môj",
            "môj",
            {
                "môjho",
                "môjmu",
                "moja",
                "moje",
                "moju",
                "mojom",
                "mojím",
                "moji",
                "mojich",
                "mojimi",
            },
            {"môja", "môje", "môji", "mojim"},
        ),
        ("tvoj", "tvoj", {"tvojho", "tvojmu", "tvoja", "tvojím", "tvojich", "tvojimi"}, {"tvojim"}),
        ("svoj", "svoj", {"svojho", "svojmu", "svoja", "svojím", "svojich", "svojimi"}, {"svojim"}),
    ],
)
def test_possessive_pronoun_alternations(root, citation, required, forbidden):
    paradigm = adjective_paradigm(root, "môj")
    assert paradigm["muž", "živ", "sg", "nom"] == citation
    forms = set(paradigm.values())
    assert required <= forms
    assert not forbidden & forms


def test_nas_and_vas_oblique_genitive_and_dative():
    for root, gen, dat in [("naš", "nášho", "nášmu"), ("vaš", "vášho", "vášmu")]:
        # Unlike našej/naším, the masculine genitive and dative keep a long á.
        paradigm = adjective_paradigm(root, "môj")
        assert paradigm["muž", "živ", "sg", "gen"] == gen
        assert paradigm["muž", "živ", "sg", "dat"] == dat


def test_closed_class_claims_do_not_require_a_false_unaccented_lemma():
    for lemma in ("náš", "váš", "môj", "ten", "tento", "tamten"):
        corpus = set(closed_class_paradigms()[lemma])
        result = inventory(induce(corpus, corpus))
        assert any(a["pos"] == "pron" and a["lemma"] == lemma for a in result["analyses"])
        assert not result["first_members"]


def test_both_numeral_competes_with_false_ob_noun():
    corpus = {"ob", "oba", "obe", "obaja", "oboch", "obom", "oboma", "oby"}
    result = inventory(induce(corpus, corpus))
    assert "obo" not in result["first_members"]
    assert any(a["lemma"] == "oba" and a["pos"] == "pron" for a in result["analyses"])


@pytest.mark.parametrize(
    "stem,pattern,required",
    [
        (
            "prebud",
            "robiť",
            {
                "prebudený",
                "prebudenej",
                "prebudenou",
                "prebudeného",
                "prebudenú",
                "prebudených",
                "prebudeným",
                "prebudenými",
            },
        ),
        (
            "pracov",
            "pracovať",
            {
                "pracovaného",
                "pracovaným",
                "pracujúci",
                "pracujúceho",
                "pracujúcou",
                "pracujúcich",
                "pracujúcimi",
            },
        ),
        ("sia", "piť", {"siaty", "siateho", "siatym", "siatych"}),
    ],
)
def test_full_participial_inflection(stem, pattern, required):
    assert required <= set(verb_paradigm(stem, pattern).values())


@pytest.mark.parametrize(
    "word",
    [
        "novoprebudenej",
        "novoprebudenou",
        "novoprebudeného",
        "novoprebudenú",
        "novoprebudených",
        "novoprebudeným",
        "novoprebudenými",
    ],
)
def test_passive_paradigm_licenses_the_compound_seam(monkeypatch, word):
    engine = importlib.import_module("slabika.syllabify")
    forms = frozenset(verb_paradigm("prebud", "robiť").values())
    reading = Reading("verb", "robiť", "prebud", "prebudiť", forms, forms - {"prebudiť"})
    data = inventory([(reading, reading.support)])
    monkeypatch.setattr(engine, "_GENERATED_FIRST_MEMBERS", frozenset({"novo"}))
    monkeypatch.setattr(engine, "_INFERRED_FIRST_MEMBERS", frozenset())
    monkeypatch.setattr(engine, "_GENERATED_HEADS", data["heads"])
    monkeypatch.setattr(engine, "_GENERATED_HEAD_PARADIGMS", data["head_paradigms"])
    assert engine._generated_compositum(word) == ("novo", word[4:])
    assert engine._generated_compositum("novoprebudeneho") is None
