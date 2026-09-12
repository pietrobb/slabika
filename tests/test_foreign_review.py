# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Foreign consoles reuse human review without Slovak voices or shared decisions."""

import hashlib
import sqlite3

import pytest

from slabika.review import server
from slabika.review.foreign import ForeignCorpus


def inventory(path, language="de"):
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE corpus_metadata(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE forms(form TEXT PRIMARY KEY, casing_status TEXT DEFAULT 'resolved', proposed_canonical_form TEXT);
            CREATE TABLE adjudications(form TEXT PRIMARY KEY, review_status TEXT DEFAULT 'pending',
                expected_syllabification TEXT, expected_hyphenation TEXT, is_foreign_word INTEGER,
                is_proper_name INTEGER, is_likely_invalid INTEGER, is_abbreviation INTEGER,
                reason TEXT DEFAULT '', source TEXT DEFAULT '');
            CREATE TABLE foreign_evidence(form TEXT PRIMARY KEY, language TEXT,
                proposed_hyphenation TEXT, ipa TEXT, raw_phones TEXT, spans_json TEXT,
                g2p_score REAL, pronunciation_status TEXT, proposal_status TEXT,
                proposal_source TEXT, model_json TEXT, error TEXT, updated_at TEXT);
        """)
        db.execute("INSERT INTO corpus_metadata VALUES ('language', ?)", (language,))
        for form, proposal, ipa in [("wasser", "was·ser", "vasɐ"), ("mother", "mo·ther", "mʌðɚ"), ("pending", None, None)]:
            db.execute("INSERT INTO forms(form) VALUES (?)", (form,))
            db.execute("INSERT INTO adjudications(form) VALUES (?)", (form,))
            db.execute("INSERT INTO foreign_evidence(form,language,proposed_hyphenation,ipa,pronunciation_status,proposal_status) VALUES (?,?,?,?,?,?)",
                       (form, language, proposal, ipa, "generated" if ipa else "pending", "candidate" if proposal else "pending"))


@pytest.fixture
def corpus(tmp_path):
    source = tmp_path / "de.sqlite"
    inventory(source)
    corpus = ForeignCorpus(source, tmp_path / "de_decisions.sqlite", "de")
    yield corpus
    corpus.inventory.close()
    corpus.store.close()


def test_no_slovak_engine_or_chlebikova(corpus, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Slovak computation must not run in foreign review")
    for name in ("_engine", "tex_hyphenate", "hyphenate", "is_german", "is_french", "is_english"):
        monkeypatch.setattr(server, name, forbidden)
    page = corpus.page("mother", "exact", "all", 0, 20)
    row = page["items"][0]
    assert page["corpus_language"] == "de"
    assert row["hyphenation"] == "mo·ther"
    assert row["pronunciation"]["ipa"] == "mʌðɚ"
    assert row["tex"] is None and row["engine_tex"] == row["hyphenation"]
    assert row["ai_expected"] is None and row["my_action"] is None
    assert not row["syllabification_unsupported"]
    corpus.decide({"form": "mother", "action": "correct", "text": "moth-er"})
    assert corpus.page("", "prefix", "engine_disagree", 0, 20)["total"] == 1
    exported = corpus.export_corrections()
    assert exported["corpus_language"] == "de"
    assert exported["corrections"][0]["suggested_hyphenation"] == "moth·er"
    assert corpus.page("", "prefix", "all", 0, 20, tex_diff=True)["total"] == 0


def test_corrections_persist_audit_undo_and_inventory_unchanged(corpus):
    before = hashlib.sha256(corpus.inventory_path.read_bytes()).hexdigest()
    corpus.decide({"form": "wasser", "action": "confirm"})
    corpus.decide({"form": "wasser", "action": "correct", "text": "wa-sser"})
    fresh = sqlite3.connect(corpus.decisions_path)
    assert fresh.execute("SELECT expected_hyphenation FROM decisions").fetchone()[0] == "wa·sser"
    assert fresh.execute("SELECT count(*) FROM decision_log").fetchone()[0] == 2
    fresh.close()
    corpus.undo_last()
    assert corpus._fresh("wasser")["my_expected"] == "was·ser"
    corpus.decide({"form": "wasser", "action": "classify", "flags": {"proper": True}, "corrected_form": "Wasser"})
    assert corpus._fresh("wasser")["flags"]["proper"] == 1
    assert corpus._fresh("wasser")["my_expected"] == "was·ser"
    corpus.clear({"form": "wasser"})
    assert corpus._fresh("wasser")["my_expected"] is None
    corpus.undo_last()
    assert corpus._fresh("wasser")["my_expected"] == "was·ser"
    assert hashlib.sha256(corpus.inventory_path.read_bytes()).hexdigest() == before
    reopened = ForeignCorpus(corpus.inventory_path, corpus.decisions_path, "de")
    try:
        assert reopened._fresh("wasser")["my_expected"] == "was·ser"
    finally:
        reopened.inventory.close()
        reopened.store.close()


def test_bulk_does_not_require_slovak_syllables_or_confirm_pending(corpus):
    result = corpus.decide_many({"entries": [
        {"form": form, "action": "confirm", "bulk": True}
        for form in ("wasser", "mother", "pending")
    ]})
    assert len(result["items"]) == 2
    assert result["failed"][0]["form"] == "pending"
    assert corpus.stats()["confirm"] == 2
    with pytest.raises(ValueError):
        corpus.decide({"form": "wasser", "action": "correct", "text": "vasser"})
    with pytest.raises(ValueError):
        corpus.decide({"form": "wasser", "action": "confirm", "field": "syllabification"})
    with pytest.raises(ValueError):
        corpus.freeze_psp_audit("x", "y", "z")


def test_read_live_generated_evidence_without_stale_cache(corpus):
    assert corpus._engine_hyphenation("pending") == "pending"
    with sqlite3.connect(corpus.inventory_path) as db:
        db.execute("UPDATE foreign_evidence SET proposed_hyphenation='pen·ding', ipa='pɛndɪŋ' WHERE form='pending'")
    assert corpus._engine_hyphenation("pending") == "pen·ding"
    assert corpus._fresh("pending")["pronunciation"]["ipa"] == "pɛndɪŋ"


def test_wrong_language_and_slovak_store_refused_before_writes(corpus, tmp_path):
    with pytest.raises(ValueError, match="Inventory language"):
        ForeignCorpus(corpus.inventory_path, tmp_path / "wrong.sqlite", "fr")
    with pytest.raises(ValueError, match="separate"):
        ForeignCorpus(corpus.inventory_path, corpus.inventory_path, "de")
    slovak = tmp_path / "sk_decisions.sqlite"
    with sqlite3.connect(slovak) as db:
        db.execute("CREATE TABLE decisions(form TEXT)")
        db.execute("INSERT INTO decisions VALUES ('maslo')")
    before = slovak.read_bytes()
    with pytest.raises(ValueError, match="non-foreign"):
        ForeignCorpus(corpus.inventory_path, slovak, "de")
    assert slovak.read_bytes() == before


def test_same_word_in_three_languages_has_independent_decisions(tmp_path):
    corpora = []
    try:
        for language in ("de", "fr", "en"):
            source = tmp_path / f"{language}.sqlite"
            inventory(source, language)
            corpora.append(ForeignCorpus(source, tmp_path / f"{language}_decisions.sqlite", language))
        corpora[0].decide({"form": "mother", "action": "correct", "text": "moth-er"})
        assert corpora[0]._fresh("mother")["my_expected"] == "moth·er"
        assert all(c._fresh("mother")["my_expected"] is None for c in corpora[1:])
        with pytest.raises(ValueError, match="another language"):
            ForeignCorpus(corpora[1].inventory_path, corpora[0].decisions_path, "fr")
    finally:
        for corpus in corpora:
            corpus.inventory.close()
            corpus.store.close()


@pytest.mark.parametrize("action", ["confirm", "correct"])
def test_pending_manual_correction_requires_explicit_text(corpus, action):
    with pytest.raises(ValueError):
        corpus.decide({"form": "pending", "action": action})
    assert corpus._fresh("pending")["my_action"] is None
    saved = corpus.decide({"form": "pending", "action": action, "text": "pen-ding"})
    assert saved["item"]["my_expected"] == "pen·ding"
    assert saved["item"]["my_hyphenation_action"] == "correct"


def test_slovak_inventory_cannot_open_foreign_decisions(corpus, tmp_path):
    source = tmp_path / "sk.sqlite"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE forms(form TEXT)")
    before = corpus.decisions_path.read_bytes()
    with pytest.raises(ValueError, match="Foreign decision store"):
        server.Corpus(source, corpus.decisions_path)
    assert corpus.decisions_path.read_bytes() == before


def test_foreign_inventory_cannot_fall_back_to_slovak_console(corpus, tmp_path):
    decisions = tmp_path / "must-not-create.sqlite"
    with pytest.raises(ValueError, match="requires --language"):
        server.Corpus(corpus.inventory_path, decisions)
    assert not decisions.exists()


def test_uploaded_forms_stay_pending_until_generated(corpus):
    corpus.load_worklist("neuheit", "more.txt")
    assert corpus.add_worklist_forms()["added"] == 1
    assert corpus._fresh("neuheit")["engine_error"]
    assert corpus._fresh("neuheit")["pronunciation"] == {}
    with pytest.raises(ValueError):
        corpus.decide({"form": "neuheit", "action": "confirm"})
