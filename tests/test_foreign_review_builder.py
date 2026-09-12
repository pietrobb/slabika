# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Foreign inventory contract, token conversion, error and resume regressions."""

import importlib.util
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

PATH = Path(__file__).resolve().parents[1] / "tools/build_foreign_review.py"
SPEC = importlib.util.spec_from_file_location("foreign_review_builder", PATH)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def fake_pronounce(word, language):
    return SimpleNamespace(word=word, language=language, phones="m a m a", score=1.25,
                           spans=((word[:1], ("m",)), (word[1:2], ("a",)),
                                  (word[2:3], ("m",)), (word[3:], ("a",))))


def english_pronounce(word, language):
    return SimpleNamespace(word=word, language=language, phones="m æ m æ", score=1.25,
                           spans=((word[:1], ("m",)), (word[1:2], ("æ",)),
                                  (word[2:3], ("m",)), (word[3:], ("æ",))))


@pytest.fixture
def db(tmp_path):
    connection = builder.initialize_inventory(tmp_path / "de.sqlite", "de")
    yield connection
    connection.close()


@pytest.mark.parametrize("language", ["de", "fr", "en"])
def test_exact_contract_and_empty_decisions(tmp_path, language):
    db = builder.initialize_inventory(tmp_path / f"{language}.sqlite", language)
    try:
        builder.populate_forms(db, language, {"mama", "same"})
        assert db.execute("SELECT * FROM adjudications WHERE form='mama'").fetchone() == (
            "mama", "pending", None, None, None, None, None, None, "", "")
        assert db.execute("SELECT * FROM forms WHERE form='mama'").fetchone() == (
            "mama", "resolved", None)
        assert [r[1] for r in db.execute("PRAGMA table_info(foreign_evidence)")] == [
            "form", "language", "proposed_hyphenation", "ipa", "raw_phones", "spans_json",
            "g2p_score", "pronunciation_status", "proposal_status", "proposal_source",
            "model_json", "error", "updated_at"]
        assert builder.verify_inventory(db, language, {"mama", "same"})["forms"] == 2
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO foreign_evidence(form,language) VALUES ('orphan',?)", (language,))
    finally:
        db.close()


@pytest.mark.parametrize("language, raw, ipa", [
    ("en", "ow aj ej aw ɔj oj", "oʊaɪeɪaʊɔɪɔɪ"),
    ("en", "ɑ j w dʒ tʃ", "ɑjwd͡ʒt͡ʃ"),
    ("de", "aj aw ɔʏ ts pf", "aɪaʊɔʏt͡sp͡f"),
    ("fr", "ɑ̃ ɛ̃ ɔ̃ ʁ ɥ", "ɑ̃ɛ̃ɔ̃ʁɥ"),
])
def test_actual_ipa_whole_tokens(language, raw, ipa):
    assert builder.phones_to_ipa(raw, language) == ipa


@pytest.mark.parametrize("raw", ["", "<eps>", "UNKNOWN", "owaj", "AH0"])
def test_unknown_phones_are_errors(raw):
    with pytest.raises(ValueError):
        builder.phones_to_ipa(raw, "en")


def test_resume_preserves_humans_and_successful_evidence(db):
    builder.populate_forms(db, "de", {"mama", "extra"})
    with db:
        db.execute("UPDATE adjudications SET review_status='verified', expected_hyphenation='hu·man', "
                   "expected_syllabification='human', reason='review', source='person' WHERE form='mama'")
        db.execute("UPDATE forms SET casing_status='unresolved', proposed_canonical_form='Mama' "
                   "WHERE form='mama'")
    human = db.execute("SELECT * FROM adjudications").fetchall()
    forms = db.execute("SELECT * FROM forms").fetchall()
    model = {"sha256": "original-model", "ipa_description": builder.IPA_NOTE}
    assert builder.populate_evidence(db, "de", model, pronounce=fake_pronounce) == 2
    evidence = db.execute("SELECT * FROM foreign_evidence").fetchall()
    builder.populate_forms(db, "de", {"mama"})
    assert builder.populate_evidence(db, "de", {}, pronounce=lambda *a: pytest.fail("rerun")) == 0
    assert db.execute("SELECT * FROM foreign_evidence").fetchall() == evidence
    assert db.execute("SELECT * FROM forms").fetchall() == forms
    assert db.execute("SELECT * FROM adjudications").fetchall() == human
    assert json.loads(evidence[0][10])["sha256"] == "original-model"


def test_errors_explicit_and_retried(db):
    builder.populate_forms(db, "de", {"mama"})

    def fail(*args):
        raise RuntimeError("model unavailable")

    builder.populate_evidence(db, "de", {}, pronounce=fail)
    assert db.execute("SELECT ipa,pronunciation_status,proposal_status,error FROM foreign_evidence").fetchone() == (
        None, "error", "candidate", "pronunciation: RuntimeError: model unavailable")
    assert builder.populate_evidence(db, "de", {"sha256": "new"}, pronounce=fake_pronounce) == 1
    assert db.execute("SELECT ipa,pronunciation_status,error FROM foreign_evidence").fetchone() == (
        "mama", "generated", "")
    builder.verify_inventory(db, "de", {"mama"})


def test_english_experimental_and_incomplete(tmp_path, monkeypatch):
    import evaluate_foreign_corpora

    db = builder.initialize_inventory(tmp_path / "en.sqlite", "en")
    try:
        builder.populate_forms(db, "en", {"mama", "meme"})
        builder.populate_evidence(db, "en", {}, pronounce=english_pronounce, limit=1)
        assert db.execute("SELECT proposal_status FROM foreign_evidence WHERE form='mama'").fetchone() == (
            "experimental",)
        monkeypatch.setattr(evaluate_foreign_corpora, "project_psp_points", lambda p: ((2,), False))
        builder.populate_evidence(db, "en", {}, pronounce=english_pronounce)
        assert db.execute("SELECT proposed_hyphenation,proposal_status FROM foreign_evidence "
                          "WHERE form='meme'").fetchone() == ("me·me", "incomplete")
        assert db.execute("SELECT count(*) FROM adjudications WHERE expected_hyphenation IS NOT NULL "
                          "OR expected_syllabification IS NOT NULL").fetchone() == (0,)
    finally:
        db.close()


def test_bad_ipa_keeps_raw_evidence(db):
    builder.populate_forms(db, "de", {"mama"})

    def invalid(word, language):
        result = fake_pronounce(word, language)
        result.phones = "UNKNOWN"
        result.spans = ((word, ("UNKNOWN",)),)
        return result

    builder.populate_evidence(db, "de", {"sha256": "retained"}, pronounce=invalid)
    row = db.execute("SELECT raw_phones,ipa,pronunciation_status,error FROM foreign_evidence").fetchone()
    assert row[:3] == ("UNKNOWN", None, "error")
    assert "unsupported MFA phones" in row[3]


def test_wrong_language_and_schema_refused_without_writes(tmp_path):
    path = tmp_path / "inventory.sqlite"
    connection = builder.initialize_inventory(path, "de")
    connection.close()
    before = path.read_bytes()
    with pytest.raises(ValueError, match="language"):
        builder.initialize_inventory(path, "fr")
    assert path.read_bytes() == before
    with sqlite3.connect(path) as connection:
        connection.execute("ALTER TABLE forms ADD COLUMN unexpected TEXT")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="schema"):
        builder.initialize_inventory(path, "de")
    assert path.read_bytes() == before
    with pytest.raises(ValueError):
        builder.initialize_inventory(tmp_path / "sk.sqlite", "sk")
    assert not (tmp_path / "sk.sqlite").exists()


def test_batches_limit_and_interruption_resume(db):
    words = {f"word{i:04d}" for i in range(1001)}
    commits = []
    db.set_trace_callback(lambda sql: commits.append(sql) if sql == "COMMIT" else None)
    builder.populate_forms(db, "de", words)
    assert len(commits) == 3
    with pytest.raises(ValueError):
        builder.populate_forms(db, "de", words, batch_size=501)
    builder.populate_forms(db, "de", {"mama", "meme", "mimi"})
    with pytest.raises(KeyboardInterrupt):
        builder.populate_evidence(db, "de", {}, forms={"mama", "meme", "mimi"},
                                  pronounce=fake_pronounce, batch_size=1,
                                  progress=lambda *args: (_ for _ in ()).throw(KeyboardInterrupt()))
    assert db.execute("SELECT count(*) FROM foreign_evidence WHERE pronunciation_status='generated'").fetchone() == (1,)
    assert builder.populate_evidence(db, "de", {}, forms={"mama", "meme", "mimi"},
                                     pronounce=fake_pronounce, limit=1) == 1
    assert builder.populate_evidence(db, "de", {}, forms={"mama", "meme", "mimi"},
                                     pronounce=fake_pronounce) == 1


def test_resume_includes_uploaded_forms_outside_loader_corpus(db):
    builder.populate_forms(db, "de", {"mama"})
    with db:
        db.execute("INSERT INTO forms(form) VALUES ('neuheit')")
        db.execute("INSERT INTO adjudications(form,reason,source) VALUES ('neuheit','keep','review_console:upload')")
    builder.populate_forms(db, "de", {"mama"})
    assert builder.populate_evidence(db, "de", {}, pronounce=fake_pronounce) == 2
    assert db.execute("SELECT pronunciation_status FROM foreign_evidence WHERE form='neuheit'").fetchone() == ("generated",)
    assert db.execute("SELECT reason,source FROM adjudications WHERE form='neuheit'").fetchone() == ("keep", "review_console:upload")


def test_loaders_keep_full_types_and_homographs(monkeypatch, tmp_path):
    import build_english_profile as english
    import build_french_profile as french
    import build_german_profile as german

    monkeypatch.setattr(english, "load_english_types", lambda base: ({"same", "english"}, [{"a": 1}]))
    monkeypatch.setattr(english, "load_chandler_types", lambda base: ({"same", "chandler"}, [{"b": 2}]))
    monkeypatch.setattr(french, "load_french_types", lambda base: ({"same", "french"}, []))
    monkeypatch.setattr(german, "load_german_types", lambda base: ({"same", "german"}, []))
    assert builder.load_corpus("en", tmp_path) == ({"same", "english", "chandler"}, [{"a": 1}, {"b": 2}])
    assert "same" in builder.load_corpus("de", tmp_path)[0]
    assert "same" in builder.load_corpus("fr", tmp_path)[0]


def test_live_runtime_if_available():
    pytest.importorskip("slabika_pronunciation")
    for language, word in (("de", "wasser"), ("fr", "bonjour"), ("en", "hello")):
        info = builder.runtime_model_info(language)
        row = builder.generate_evidence(word, language, info)
        assert row["pronunciation_status"] == "generated", row["error"]
        assert row["proposal_status"] == ("experimental" if language == "en" else "candidate")
        assert len(info["sha256"]) == 64
        assert len(info["phones_sym_sha256"]) == 64
        assert "not human verified" in info["ipa_description"]
