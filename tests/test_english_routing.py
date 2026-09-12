# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""English core routing uses the review projection without consulting human data."""

import importlib
import json
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def adapter():
    module = importlib.import_module("slabika.english")
    for fn in (module._runtime, module._pronunciation, module._project):
        fn.cache_clear()
    yield module
    for fn in (module._runtime, module._pronunciation, module._project):
        fn.cache_clear()


def result(word, spans):
    return SimpleNamespace(word=word, language="english", score=1.0, spans=spans,
                           phones=" ".join(p for _, ps in spans for p in ps))


@pytest.mark.parametrize("word", ["people", "People", "PEOPLE"])
def test_core_and_review_share_projection_preserve_case_and_modes(adapter, monkeypatch, word):
    calls = []

    def pronounce(normalized, language):
        calls.append((normalized, language))
        return result(normalized, (("pe", ("pʰ", "iː")), ("op", ("p",)),
                                   ("le", ("ə", "ɫ"))))

    monkeypatch.setattr(adapter, "_runtime", lambda: pronounce)
    typo = importlib.import_module("slabika.typo")
    expected = word[:3] + "·" + word[3:]
    for all_points in (False, True):
        for contextual in (False, True):
            assert typo.hyphenate(word, all_points=all_points, contextual=contextual) == expected
    assert typo.hyphenate(word, separator="-") == expected.replace("·", "-")
    server = importlib.import_module("slabika.review.server")
    assert server._engine(word)[0] == expected
    assert calls == [("people", "english")]


def test_missing_optional_runtime_falls_back(adapter, monkeypatch):
    monkeypatch.setitem(sys.modules, "slabika_pronunciation", None)
    assert adapter.english_points("people") is None
    assert importlib.import_module("slabika.typo").hyphenate("people") == "pe·op·le"


@pytest.mark.parametrize("bad", ["failure", "spelling", "score", "empty", "phones", "incomplete"])
def test_bad_model_evidence_abstains(adapter, monkeypatch, bad):
    def pronounce(word, language):
        if bad == "failure":
            raise RuntimeError("native error")
        p = result(word, (("pe", ("pʰ", "iː")), ("op", ("p",)), ("le", ("ə", "ɫ"))))
        if bad == "spelling":
            p.spans = (("other", ("ə",)),)
        elif bad == "score":
            p.score = float("nan")
        elif bad == "empty":
            p.spans = ((word, ()),)
            p.phones = ""
        elif bad == "phones":
            p.phones = "wrong"
        elif bad == "incomplete":
            p = result(word, (("p", ("iː",)), ("eople", ("p", "ə", "ɫ"))))
        return p

    monkeypatch.setattr(adapter, "_runtime", lambda: pronounce)
    assert adapter.english_points("people") is None


@pytest.mark.parametrize("word", ["slovenčina", "Peopleovská", "people-people", "İpeople", "",
                                  "polceste", "gangster", "miliarda", "abeundi"])
def test_local_and_unsupported_words_do_not_call_model(adapter, monkeypatch, word):
    def unexpected(*args):
        pytest.fail(f"unexpected model call: {args}")

    monkeypatch.setattr(adapter, "_pronunciation", unexpected)
    assert adapter.english_points(word) is None


def test_verified_reading_precedes_new_model(adapter, monkeypatch):
    def unexpected(*args):
        pytest.fail(f"verified reading sent to model: {args}")

    monkeypatch.setattr(adapter, "_pronunciation", unexpected)
    assert importlib.import_module("slabika.typo").hyphenate("Sternwoodovi") == "Stern·woo·do·vi"


@pytest.mark.parametrize("word,expected", [
    ("pepper", "pep·per"), ("people", "peo·ple"), ("penny", "pen·ny"),
    ("penknife", "pen·knife"), ("modestly", "mo·dest·ly"), ("penthouse", "pent·house"),
])
def test_installed_native_model_matches_review_examples(adapter, word, expected):
    pytest.importorskip("slabika_pronunciation")
    assert adapter._runtime() is not None
    typo = importlib.import_module("slabika.typo")
    assert typo.hyphenate(word) == expected


@pytest.mark.parametrize("word,expected", [
    ("Arbeitsunfähigkeitsbescheinigung", "Ar·beits·un·fä·hig·keits·be·schei·ni·gung"),
    ("Arbeitsunfähigkeitsbescheinigungovská", "Ar·beits·un·fä·hig·keits·be·schei·ni·gu·ngov·ská"),
])
def test_english_integration_preserves_existing_german_outputs(word, expected):
    assert importlib.import_module("slabika.typo").hyphenate(word) == expected


def test_membership_export_does_not_read_human_decisions(tmp_path):
    import sqlite3
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    from export_english_morphology import export

    inventory = tmp_path / "source.sqlite"
    with sqlite3.connect(inventory) as db:
        db.execute("CREATE TABLE foreign_evidence(form, language, pronunciation_status)")
        db.executemany("INSERT INTO foreign_evidence VALUES (?, 'en', 'generated')",
                       [(w,) for w in ("pen", "knife", "penknife", "modest", "modestly", "people")])
    output = tmp_path / "members.json"
    assert export(inventory, output) == 6
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["members"] == ["knife", "modest", "modestly", "pen", "penknife", "people"]
    assert payload["source_forms"] == 6
