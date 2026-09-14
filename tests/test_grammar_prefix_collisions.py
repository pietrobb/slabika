# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A generated compound cannot revive a rejected prefix or vocalize before a vowel."""

import importlib

import pytest


@pytest.fixture
def candidate(monkeypatch):
    engine = importlib.import_module("slabika.syllabify")
    monkeypatch.setattr(engine, "_GENERATED_FIRST_MEMBERS", frozenset({"pro", "rozo", "vodo"}))
    monkeypatch.setattr(engine, "_INFERRED_FIRST_MEMBERS", frozenset({"rozo", "vodo"}))
    monkeypatch.setattr(
        engine, "_GENERATED_HEADS", {"gram": "lemma", "ran": "root", "vod": "lemma"}
    )
    monkeypatch.setattr(
        engine,
        "_GENERATED_HEAD_PARADIGMS",
        {
            "gram": {"lemma": ["gram", "gramu", "gramom"]},
            "ran": {"root": ["raný", "raného", "ranej"]},
            "vod": {"lemma": ["vod"]},
        },
    )
    for name in ("_generated_compositum", "_heads_a_compositum", "_strip_prefix"):
        func = getattr(engine, name)
        monkeypatch.setattr(engine, name, getattr(func, "__wrapped__", func))
    return engine


@pytest.mark.parametrize(
    "word,expected",
    [
        ("program", "prog·ram"),
        ("programu", "prog·ra·mu"),
        ("podprogram", "pod·prog·ram"),
        ("hyperprogram", "hy·per·prog·ram"),
        ("rozoraný", "roz·ora·ný"),
        ("rozoranej", "roz·ora·nej"),
    ],
)
def test_prefix_analysis_cannot_be_bypassed_by_generated_member(candidate, word, expected):
    assert candidate._generated_compositum(word) is None
    assert importlib.import_module("slabika").hyphenate(word) == expected


def test_productive_compound_still_works(candidate):
    assert candidate._generated_compositum("vodovod") == ("vodo", "vod")


def test_participle_fallback_cannot_revive_prefix_member(candidate, monkeypatch):
    monkeypatch.setattr(candidate, "_GENERATED_HEADS", {"bud": "verb"})
    monkeypatch.setattr(candidate, "_GENERATED_HEAD_PARADIGMS", {"bud": {"verb": ["budený"]}})
    assert candidate._generated_compositum("probudený") is None


def test_legacy_inventory_keeps_previous_behavior(candidate, monkeypatch):
    monkeypatch.setattr(candidate, "_GENERATED_HEAD_PARADIGMS", None)
    monkeypatch.setattr(candidate, "_GENERATED_HEAD_FORMS", None)
    assert candidate._generated_compositum("program") == ("pro", "gram")


@pytest.mark.parametrize(
    "word,expected,contextual",
    [
        ("oslovila", "oslo·vi·la", "o·slo·vi·la"),
        ("neoslovila", "ne·oslo·vi·la", "ne·o·slo·vi·la"),
        ("oslobodenej", "oslo·bo·de·nej", "o·slo·bo·de·nej"),
    ],
)
def test_prefixed_verb_does_not_need_a_standalone_unprefixed_lemma(
    candidate, monkeypatch, word, expected, contextual
):
    monkeypatch.setattr(candidate, "_GENERATED_FIRST_MEMBERS", frozenset({"oslo"}))
    monkeypatch.setattr(
        candidate,
        "_GENERATED_HEADS",
        {"vil": "lemma", "boden": "root", "oslov": "verb", "oslobod": "verb"},
    )
    monkeypatch.setattr(
        candidate,
        "_GENERATED_HEAD_PARADIGMS",
        {
            "vil": {"lemma": ["vila"]},
            "boden": {"root": ["bodenej"]},
            "oslov": {"verb": ["oslovila"]},
            "oslobod": {"verb": ["oslobodenej"]},
        },
    )
    api = importlib.import_module("slabika")
    assert api.hyphenate(word) == expected
    assert api.hyphenate(word, contextual=True) == contextual
