# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Tests for the read-only recurring-morpheme family audit."""

import hashlib
import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "slabika_family_audit", ROOT / "tools" / "review" / "family_audit.py"
)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inventory(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE forms (form TEXT PRIMARY KEY) WITHOUT ROWID;
            CREATE TABLE adjudications (
                form TEXT PRIMARY KEY,
                review_status TEXT NOT NULL,
                expected_hyphenation TEXT,
                reason TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT ''
            ) WITHOUT ROWID;
            """
        )
        connection.executemany(
            "INSERT INTO forms VALUES (?)",
            [
                ("bezohľadný",),
                ("chradnúť",),
                ("hrad",),
                ("priehrada",),
                ("vychradli",),
                ("nesúvisiace",),
            ],
        )
        connection.execute(
            "INSERT INTO adjudications VALUES (?, ?, ?, ?, ?)",
            ("priehrada", "verified", "prie·hra·da", "fixture", "test"),
        )


def _review(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE decisions (
                   form TEXT PRIMARY KEY,
                   action TEXT NOT NULL,
                   expected_hyphenation TEXT,
                   reason TEXT NOT NULL,
                   hyphenation_action TEXT,
                   is_deleted INTEGER DEFAULT 0
               ) WITHOUT ROWID"""
        )
        connection.execute(
            "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?)",
            ("chradnúť", "confirm", "chrad·núť", "negative control", None, 0),
        )


def _sapfo(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE snk_forms (
                wordform TEXT, lemma TEXT, pos TEXT, gram TEXT DEFAULT '{}'
            );
            CREATE TABLE nouns (
                word TEXT, pattern TEXT, source TEXT
            );
            CREATE TABLE proper_names (
                name TEXT, pattern TEXT, gender TEXT
            );
            CREATE TABLE adjectives (
                root TEXT, lemma TEXT, pattern TEXT, source TEXT
            );
            CREATE TABLE verbs (
                inf_stem TEXT, pres_stem TEXT, lemma TEXT, pattern TEXT, source TEXT
            );
            CREATE TABLE word_roots (
                word TEXT, roots TEXT, prefix TEXT, suffix TEXT, is_compound INTEGER
            );
            CREATE TABLE pales_kmen (
                lemma TEXT, derived_from_lemma TEXT, prefix TEXT, suffix TEXT
            );
            """
        )
        connection.executemany(
            "INSERT INTO snk_forms(wordform, lemma, pos) VALUES (?, ?, ?)",
            [
                ("bezohľadný", "bezohľadný", "adj"),
                ("chradnúť", "chradnúť", "inf"),
                ("priehrada", "priehrada", "sub"),
                ("priehrada", "priehrada", "adj"),
                ("vychradli", "vychradnúť", "lpar"),
            ],
        )
        connection.executemany(
            "INSERT INTO nouns VALUES (?, ?, ?)",
            [("hrad", "med", "manual"), ("priehrada", "žena", "snk")],
        )
        connection.execute(
            "INSERT INTO adjectives VALUES (?, ?, ?, ?)",
            ("bezohľadn", "bezohľadný", "pekný", "snk"),
        )
        connection.execute(
            "INSERT INTO verbs VALUES (?, ?, ?, ?, ?)",
            ("chradn", "chradn", "chradnúť", "chudnúť", "snk"),
        )
        connection.executemany(
            "INSERT INTO pales_kmen VALUES (?, ?, ?, ?)",
            [("hrad", "", "", ""), ("priehrad", "hrad", "prie", "")],
        )


def test_pilot_groups_families_and_keeps_all_sources_read_only(tmp_path):
    inventory = tmp_path / "inventory.sqlite"
    review = tmp_path / "review.sqlite"
    sapfo = tmp_path / "sapfo.sqlite"
    _inventory(inventory)
    _review(review)
    _sapfo(sapfo)
    before = {path: _digest(path) for path in (inventory, review, sapfo)}

    report = AUDIT.generate_report(
        inventory,
        review,
        sapfo,
        tmp_path / "unused-sapfo-root",
        ("hrad", "hľad"),
        use_sapfo_api=False,
    )

    assert report["summary"] == {
        "forms": 5,
        "occurrences": 5,
        "families": 3,
        "status_counts": {
            "engine_seam": 1,
            "inside_engine_morpheme": 3,
            "word_initial": 1,
        },
        "families_with_uncovered_occurrences": 2,
        "sapfo_runtime_analyzed_forms": 0,
        "sapfo_roundtrip_lemmas": 0,
    }
    families = {
        (family["member"], family["family"]): family for family in report["families"]
    }
    assert families[("hrad", "chrad")]["distinct_forms"] == 2
    assert families[("hľad", "ohľad")]["counts"] == {"inside_engine_morpheme": 1}
    assert families[("hrad", "hrad")]["counts"] == {
        "engine_seam": 1,
        "word_initial": 1,
    }
    priehrada = next(
        item
        for item in families[("hrad", "hrad")]["occurrences"]
        if item["form"] == "priehrada"
    )
    assert priehrada["review_evidence"][0]["status"] == "verified"
    assert priehrada["sapfo_snk"] == [
        {"lemma": "priehrada", "pos": "adj"},
        {"lemma": "priehrada", "pos": "sub"},
    ]
    chradnut = next(
        item
        for item in families[("hrad", "chrad")]["occurrences"]
        if item["form"] == "chradnúť"
    )
    assert chradnut["review_evidence"][0]["source"] == "human_review"
    assert "not PSP verdicts" in report["contract"]
    assert {path: _digest(path) for path in before} == before


def test_discovery_ranks_sapfo_backed_members_without_writing_sources(tmp_path):
    inventory = tmp_path / "inventory.sqlite"
    sapfo = tmp_path / "sapfo.sqlite"
    _inventory(inventory)
    _sapfo(sapfo)
    before = {path: _digest(path) for path in (inventory, sapfo)}

    report = AUDIT.generate_discovery_report(
        inventory,
        sapfo,
        min_target_length=4,
        min_supported_forms=1,
        min_uncovered_forms=2,
        limit=10,
    )

    assert report["summary"] == {
        "corpus_forms": 6,
        "sapfo_candidate_members": 4,
        "returned_candidates": 1,
    }
    assert report["candidates"] == [
        {
            "target": "hrad",
            "priority_score": 1.333,
            "sapfo_sources": ["derivation_base", "noun_lexeme"],
            "engine_supported_forms": 1,
            "covered_noninitial_forms": 1,
            "uncovered_forms": 2,
            "uncovered_occurrences": 2,
            "distinct_uncovered_left_contexts": 2,
            "missing_output_break_forms": 2,
            "missing_output_break_occurrences": 2,
            "distinct_missing_output_break_left_contexts": 2,
            "engine_support_examples": ["hrad"],
            "uncovered_examples": ["chradnúť", "vychradli"],
            "uncovered_left_context_examples": ["c", "vyc"],
            "missing_output_break_examples": ["chradnúť", "vychradli"],
            "missing_output_break_left_context_examples": ["c", "vyc"],
        }
    ]
    assert "not a morphology or PSP verdict" in report["contract"]
    assert {path: _digest(path) for path in before} == before


def test_targets_must_be_alphabetic(tmp_path):
    try:
        AUDIT.generate_report(
            tmp_path / "missing.sqlite",
            None,
            tmp_path / "missing-sapfo.sqlite",
            tmp_path,
            ("hrad%",),
            use_sapfo_api=False,
        )
    except ValueError as error:
        assert str(error) == "targets must be non-empty alphabetic strings"
    else:
        raise AssertionError("invalid target was accepted")


def test_discovery_ignores_a_missing_seam_when_output_already_has_the_break(monkeypatch):
    monkeypatch.setattr(AUDIT, "get_morpheme_parts", lambda form: [form])
    monkeypatch.setattr(
        AUDIT,
        "hyphenate",
        lambda form: "pre·root" if form == "preroot" else form,
    )

    candidates = AUDIT.discover_candidates(
        ["root", "preroot"],
        {"root": ["noun_lexeme"]},
        min_supported_forms=1,
        min_uncovered_forms=1,
        limit=10,
    )

    assert candidates == []
