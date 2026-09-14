# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A shared head spelling must preserve each POS's exact runtime permissions."""

import importlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import compare_composita as comparison  # noqa: E402
from sapfo_grammar.induction import Reading, inventory  # noqa: E402
from sapfo_grammar.synth import adjective_paradigm, noun_paradigm, verb_paradigm  # noqa: E402

engine = importlib.import_module("slabika.syllabify")


@pytest.fixture(autouse=True)
def current_engine(monkeypatch):
    monkeypatch.setitem(globals(), "engine", importlib.import_module("slabika.syllabify"))


@pytest.fixture
def roles(monkeypatch):
    survivors = []
    for pos, pattern, root, lemma, synth in [
        ("adj", "pekný", "rozhodn", "rozhodný", adjective_paradigm),
        ("verb", "hynúť", "rozhodn", "rozhodnúť", verb_paradigm),
        ("adj", "pekný", "zhodn", "zhodný", adjective_paradigm),
        ("sub", "dub", "stan", "stan", noun_paradigm),
        ("verb", "robiť", "stan", "staniť", verb_paradigm),
        ("sub", "žena", "liečb", "liečba", noun_paradigm),
        ("sub", "chlap", "sob", "sob", noun_paradigm),
        ("adj", "pekný", "osobn", "osobný", adjective_paradigm),
        ("sub", "žena", "osob", "osoba", noun_paradigm),
    ]:
        forms = frozenset(synth(root, pattern).values())
        reading = Reading(pos, pattern, root, lemma, forms, forms - {lemma})
        survivors.append((reading, reading.support))
    data = inventory(survivors)
    monkeypatch.setattr(engine, "_GENERATED_HEADS", data["heads"])
    monkeypatch.setattr(engine, "_GENERATED_HEAD_PARADIGMS", data["head_paradigms"])
    monkeypatch.setattr(engine, "_GENERATED_HEAD_FORMS", None)
    return data


def test_adjective_is_not_erased_by_homographic_verb(roles):
    assert roles["heads"]["rozhodn"] == "verb"
    assert engine._heads_a_compositum("rozhodný")
    assert engine._heads_a_compositum("rozhodný", inferred_first=True)
    assert engine._heads_a_compositum("rozhodnutý")
    assert not engine._heads_a_compositum("rozhodnutý", inferred_first=True)


def test_verb_does_not_borrow_homographic_noun_permission(roles):
    assert roles["heads"]["stan"] == "lemma"
    assert engine._heads_a_compositum("stanu", inferred_first=True)
    assert engine._heads_a_compositum("staniť")
    assert not engine._heads_a_compositum("staniť", inferred_first=True)
    assert not engine._heads_a_compositum("stanxyz")


def test_empty_paradigms_fail_closed_even_with_legacy_fallback(roles, monkeypatch):
    monkeypatch.setattr(engine, "_GENERATED_HEAD_PARADIGMS", {})
    monkeypatch.setattr(engine, "_GENERATED_HEAD_FORMS", {"stan": ["stan", "stanu"]})
    assert not engine._heads_a_compositum("stan")
    assert not engine._heads_a_compositum("stanu")


def test_attested_prefix_base_beats_an_inferred_compound(roles, monkeypatch):
    monkeypatch.setattr(engine, "_GENERATED_FIRST_MEMBERS", frozenset({"nero", "vodo", "nado"}))
    monkeypatch.setattr(engine, "_INFERRED_FIRST_MEMBERS", frozenset({"nero", "vodo", "nado"}))
    assert engine._generated_compositum("nerozhodný") is None
    assert engine._generated_compositum("vodoliečba") == ("vodo", "liečba")
    # Suffix stripping must not resurrect nado|sob over the attested osob- stem.
    assert engine._generated_compositum("nadosob") is None
    assert importlib.import_module("slabika").hyphenate("nadosobného") == "nad·osob·né·ho"


@pytest.mark.parametrize("fail_api", [False, True])
def test_schema_three_snapshot_installs_and_restores_roles(tmp_path, monkeypatch, roles, fail_api):
    corpus = tmp_path / "corpus.sqlite"
    with sqlite3.connect(corpus) as db:
        db.execute("create table forms(form text)")
        db.execute("insert into forms values ('nerozhodný')")
    candidate = tmp_path / "inventory.json"
    candidate.write_text(json.dumps(roles), encoding="utf8")
    sentinel = object()
    monkeypatch.setattr(engine, "_GENERATED_HEAD_PARADIGMS", sentinel)
    original, prefix = comparison.public_output, engine._strip_prefix

    def observe(api, form):
        assert (
            engine._strip_prefix is not prefix
            and engine._GENERATED_HEAD_PARADIGMS == roles["head_paradigms"]
        )
        if fail_api:
            raise ValueError("simulated API error")
        return original(api, form)

    monkeypatch.setattr(comparison, "public_output", observe)
    if fail_api:
        with pytest.raises(ValueError, match="simulated API error"):
            comparison.snapshot(corpus, candidate)
    else:
        result = comparison.snapshot(corpus, candidate)
        assert "head_paradigms" not in result["inventory_metadata"]
    assert engine._strip_prefix is prefix and engine._GENERATED_HEAD_PARADIGMS is sentinel


def test_schema_three_requires_explicit_paradigms(tmp_path):
    candidate = tmp_path / "bad.json"
    candidate.write_text(json.dumps({"schema_version": 3, "first_members": {}, "heads": {}}))
    with pytest.raises(KeyError, match="head_paradigms"):
        comparison.snapshot(tmp_path / "absent.sqlite", candidate)
