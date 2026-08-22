# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Regression tests for independent review of both engine outputs."""

import importlib.util
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "slabika_review_server", ROOT / "tools" / "review" / "server.py"
)
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)

OLD_DECISION_SCHEMA = """
CREATE TABLE decisions (
    form TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    expected_hyphenation TEXT,
    expected_syllabification TEXT,
    engine_hyphenation TEXT NOT NULL,
    engine_syllabification TEXT NOT NULL,
    is_foreign_word INTEGER,
    is_proper_name INTEGER,
    is_abbreviation INTEGER,
    reason TEXT NOT NULL DEFAULT '',
    engine_version TEXT NOT NULL,
    decided_at TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE decision_log (
    entry_id INTEGER PRIMARY KEY,
    form TEXT NOT NULL,
    operation TEXT NOT NULL,
    action TEXT,
    expected_hyphenation TEXT,
    expected_syllabification TEXT,
    engine_hyphenation TEXT,
    previous_json TEXT,
    engine_version TEXT NOT NULL,
    logged_at TEXT NOT NULL
);
"""


def _inventory(path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE forms (
            form TEXT PRIMARY KEY,
            casing_status TEXT NOT NULL,
            proposed_canonical_form TEXT
        ) WITHOUT ROWID;
        CREATE TABLE adjudications (
            form TEXT PRIMARY KEY,
            review_status TEXT NOT NULL,
            expected_syllabification TEXT,
            expected_hyphenation TEXT,
            is_foreign_word INTEGER,
            is_proper_name INTEGER,
            is_likely_invalid INTEGER,
            is_abbreviation INTEGER,
            reason TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT ''
        ) WITHOUT ROWID;
        """
    )
    for form, casing_status, canonical in (
        ("maslo", "resolved", None),
        ("MASLO", "needs_review", "maslo"),
        ("Aaah", "inferred", None),
        ("iPhone", "resolved", None),
        ("iphone", "resolved", None),
        ("okno", "resolved", None),
    ):
        connection.execute("INSERT INTO forms VALUES (?, ?, ?)", (form, casing_status, canonical))
        connection.execute(
            "INSERT INTO adjudications VALUES (?, 'pending', NULL, NULL, NULL, NULL, NULL, NULL, '', '')",
            (form,),
        )
    connection.execute(
        "UPDATE adjudications SET is_proper_name = 0 WHERE form = 'Aaah'"
    )
    connection.commit()
    connection.close()


def _old_store(path):
    connection = sqlite3.connect(path)
    connection.executescript(OLD_DECISION_SCHEMA)
    connection.execute(
        """INSERT INTO decisions VALUES
           ('maslo', 'confirm', NULL, 'ma·slo', 'mas·lo', 'old·snapshot',
            NULL, NULL, NULL, '', '0.0', '2026-01-01T00:00:00+00:00')"""
    )
    connection.commit()
    connection.close()


@pytest.fixture
def corpus(tmp_path):
    inventory = tmp_path / "inventory.sqlite"
    decisions = tmp_path / "decisions.sqlite"
    _inventory(inventory)
    _old_store(decisions)
    value = REVIEW.Corpus(inventory, decisions)
    yield value
    value.inventory.close()
    value.store.close()


def test_marked_output_may_only_change_boundaries():
    assert REVIEW._parse_marked("maslo", "ma-slo") == "ma·slo"
    assert REVIEW._parse_marked("maslo", " mas--lo ") == "mas·lo"
    with pytest.raises(ValueError, match="musí zostať presne ten tvar"):
        REVIEW._parse_marked("maslo", "ma-x-slo")


def test_ui_reviews_only_typographic_word_division():
    html = REVIEW.UI_PATH.read_text(encoding="utf-8")
    assert html.count('<input class="edit"') == 1
    assert 'data-field="h"' in html
    assert 'data-field="s"' not in html
    assert "slabiky (výslovnosť)" not in html
    for label in ("Meno", "Cudzie", "Skratka", "Opraviť", "Vymazať"):
        assert f">{label}</button>" in html


def test_ui_uses_editable_correction_dialog_and_ignores_stale_filter_results():
    html = REVIEW.UI_PATH.read_text(encoding="utf-8")
    assert 'id="correction-dialog"' in html
    assert 'id="correction-input"' in html
    assert '<button type="button" id="correction-cancel">' in html
    assert '<button value="save">Uložiť opravu</button>' in html
    assert "prompt(" not in html
    load_source = html.split("async function load", 1)[1].split("async function stats", 1)[0]
    assert load_source.index("const version = ++S.loadVersion") < load_source.index("if (S.pending)")
    assert "if (version !== S.loadVersion) return" in load_source
    assert load_source.index("if (version !== S.loadVersion) return") < load_source.index(
        "if (hasDirty() || S.pending)"
    )
    assert "restoreAppliedFilters()" in load_source
    assert "input.value = input._committed" in load_source
    assert "if (value) ++S.loadVersion" in html
    assert 'document.querySelectorAll(".edit").forEach(input => { input.disabled = value; });' in html
    assert '$("q").addEventListener("input", () => {\n  ++S.loadVersion;' in html
    assert "setPending(true);\n    const corrected = await askCorrection(item)" in html


def test_uppercase_variant_is_hidden_only_when_lowercase_form_exists(corpus):
    assert corpus._fresh("Aaah")["review_form"] == "Aaah"
    assert "Aaah" in corpus.forms
    assert "maslo" in corpus.forms
    assert "MASLO" not in corpus.forms
    assert "iPhone" in corpus.forms
    assert "iphone" in corpus.forms
    assert sum(corpus.review_forms[form] == "maslo" for form in corpus.forms) == 1

    item = corpus._fresh("MASLO")
    assert item["form"] == "MASLO"
    assert item["review_form"] == "maslo"
    assert item["hyphenation"] == "mas·lo"

    saved = corpus.decide(
        {
            "form": "MASLO",
            "action": "confirm",
            "field": "hyphenation",
            "text": "mas-lo",
        }
    )["item"]
    row = corpus.store.execute("SELECT * FROM decisions WHERE form = 'maslo'").fetchone()
    assert corpus.store.execute(
        "SELECT * FROM decisions WHERE form = 'MASLO'"
    ).fetchone() is None
    assert row["expected_hyphenation"] == "mas·lo"
    assert saved["form"] == "maslo"
    assert saved["my_expected"] == "mas·lo"
    assert "maslo" in corpus._filter_status(corpus.forms, "mine")
    assert corpus.page("maslo", "exact", "all", 0, 10)["items"][0]["my_expected"] == "mas·lo"
    assert corpus.stats()["reviewed"] == 1
    assert corpus.stats()["confirm"] == 1

    alias = dict(row)
    alias.update(
        form="MASLO",
        action="correct",
        hyphenation_action="correct",
        expected_hyphenation="MA·SLO",
        decision_seq=row["decision_seq"] + 1,
    )
    columns = ", ".join(alias)
    placeholders = ", ".join("?" * len(alias))
    corpus.store.execute(
        f"INSERT INTO decisions({columns}) VALUES ({placeholders})", tuple(alias.values())
    )
    corpus.store.commit()
    corpus.decided["MASLO"] = "correct"
    assert corpus.page("maslo", "exact", "all", 0, 10)["items"][0]["my_expected"] == "ma·slo"

    corpus.decide(
        {
            "form": "maslo",
            "action": "confirm",
            "field": "hyphenation",
            "text": "mas-lo",
        }
    )
    assert corpus.page("maslo", "exact", "all", 0, 10)["items"][0]["my_expected"] == "mas·lo"
    assert corpus.stats()["confirm"] == 1
    assert corpus.stats()["correct"] == 0


def test_clear_and_undo_cover_a_hidden_uppercase_alias(corpus):
    corpus.decide(
        {
            "form": "maslo",
            "action": "confirm",
            "field": "hyphenation",
            "text": "mas-lo",
        }
    )
    row = dict(
        corpus.store.execute("SELECT * FROM decisions WHERE form = 'maslo'").fetchone()
    )
    row.update(
        form="MASLO",
        expected_hyphenation="MAS·LO",
        expected_syllabification="MA·SLO",
        engine_hyphenation="MAS·LO",
        engine_syllabification="MA·SLO",
    )
    corpus.store.execute("DELETE FROM decisions WHERE form = 'maslo'")
    columns = ", ".join(row)
    placeholders = ", ".join("?" * len(row))
    corpus.store.execute(
        f"INSERT INTO decisions({columns}) VALUES ({placeholders})", tuple(row.values())
    )
    corpus.store.commit()
    corpus.decided.pop("maslo")
    corpus.decided["MASLO"] = "confirm"

    assert corpus.page("maslo", "exact", "all", 0, 10)["items"][0]["my_expected"] == "mas·lo"
    assert corpus.clear({"form": "maslo"})["item"]["my_hyphenation_action"] is None
    assert "maslo" in corpus._filter_status(corpus.forms, "undecided")
    assert corpus.stats()["reviewed"] == 0

    undone = corpus.undo_last()
    assert undone["form"] == "maslo"
    assert undone["item"]["my_hyphenation_action"] == "confirm"
    assert corpus.store.execute(
        "SELECT hyphenation_action FROM decisions WHERE form = 'MASLO'"
    ).fetchone()[0] == "confirm"


def test_hyphenation_filters_ignore_legacy_syllable_only_decisions(corpus):
    assert "maslo" in corpus._filter_status(corpus.forms, "undecided")
    assert "maslo" not in corpus._filter_status(corpus.forms, "mine")

    corpus.decide({"form": "okno", "action": "flag", "reason": "wrong"})
    assert "okno" not in corpus._filter_status(corpus.forms, "undecided")
    assert corpus.stats()["reviewed"] == 1


def test_migration_and_second_output_preserve_first_output(corpus):
    migrated = corpus.store.execute(
        "SELECT * FROM decisions WHERE form = 'maslo'"
    ).fetchone()
    assert migrated["syllabification_action"] == "confirm"
    assert migrated["hyphenation_action"] is None

    corpus.decide(
        {
            "form": "maslo",
            "action": "confirm",
            "field": "hyphenation",
            "text": "mas-lo",
        }
    )
    row = corpus.store.execute("SELECT * FROM decisions WHERE form = 'maslo'").fetchone()
    assert row["expected_syllabification"] == "ma·slo"
    assert row["expected_hyphenation"] == "mas·lo"
    assert row["syllabification_action"] == "confirm"
    assert row["hyphenation_action"] == "confirm"
    assert row["engine_syllabification"] == "old·snapshot"
    assert corpus._fresh("maslo")["stale_s"] is True

    corpus.decide({"form": "maslo", "action": "flag", "reason": "needs review"})
    corpus.decide(
        {
            "form": "maslo",
            "action": "confirm",
            "field": "syllabification",
            "text": "ma-slo",
        }
    )
    row = corpus.store.execute("SELECT * FROM decisions WHERE form = 'maslo'").fetchone()
    assert row["row_action"] == "flag"
    assert row["action"] == "flag"
    assert row["reason"] == "needs review"


def test_clear_removes_only_visible_review_and_undo_restores_it(corpus):
    corpus.decide(
        {
            "form": "maslo",
            "action": "confirm",
            "field": "hyphenation",
            "text": "mas-lo",
        }
    )
    corpus.decide({"form": "maslo", "action": "flag", "reason": "wrong"})

    assert corpus.clear({"form": "maslo"})["ok"] is True
    cleared = corpus.store.execute(
        "SELECT * FROM decisions WHERE form = 'maslo'"
    ).fetchone()
    assert cleared["hyphenation_action"] is None
    assert cleared["row_action"] is None
    assert cleared["expected_hyphenation"] is None
    assert cleared["syllabification_action"] == "confirm"
    assert cleared["expected_syllabification"] == "ma·slo"

    corpus.undo_last()
    restored = corpus.store.execute(
        "SELECT * FROM decisions WHERE form = 'maslo'"
    ).fetchone()
    assert restored["hyphenation_action"] == "confirm"
    assert restored["row_action"] == "flag"


def test_concurrent_field_saves_do_not_erase_each_other(corpus):
    entries = (
        {"form": "okno", "action": "confirm", "field": "syllabification", "text": "o-kno"},
        {"form": "okno", "action": "confirm", "field": "hyphenation", "text": "ok-no"},
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(corpus.decide, entries))

    row = corpus.store.execute("SELECT * FROM decisions WHERE form = 'okno'").fetchone()
    assert row["expected_syllabification"] == "o·kno"
    assert row["expected_hyphenation"] == "ok·no"
    assert row["syllabification_action"] == "confirm"
    assert row["hyphenation_action"] == "confirm"


def test_undo_migrates_a_legacy_audit_snapshot(corpus):
    old_row = {
        "form": "okno",
        "action": "correct",
        "expected_hyphenation": "o·kno",
        "expected_syllabification": None,
        "engine_hyphenation": "ok·no",
        "engine_syllabification": "o·kno",
        "is_foreign_word": None,
        "is_proper_name": None,
        "is_abbreviation": None,
        "reason": "",
        "engine_version": "0.0",
        "decided_at": "2026-01-01T00:00:00+00:00",
    }
    corpus.store.execute(
        """INSERT INTO decision_log(
               form, operation, action, previous_json, engine_version, logged_at
           ) VALUES ('okno', 'decide', 'confirm', ?, '0.0', '2026-01-01T00:00:01+00:00')""",
        (json.dumps(old_row),),
    )
    corpus.store.commit()

    corpus.undo_last()
    restored = corpus.store.execute("SELECT * FROM decisions WHERE form = 'okno'").fetchone()
    assert restored["hyphenation_action"] == "correct"
    assert restored["syllabification_action"] is None
    assert restored["row_action"] is None
    assert restored["decision_seq"] == 0


def test_classification_preserves_existing_reviews_and_supports_filters(corpus):
    corpus.decide(
        {
            "form": "maslo",
            "action": "confirm",
            "field": "hyphenation",
            "text": "mas-lo",
        }
    )
    classified = corpus.decide(
        {
            "form": "maslo",
            "action": "classify",
            "flags": {"proper": True, "foreign": True, "abbreviation": True},
            "corrected_form": "máslo",
        }
    )["item"]

    assert classified["my_hyphenation_action"] == "confirm"
    assert classified["my_syllabification_action"] == "confirm"
    assert classified["flags"]["proper"] == 1
    assert classified["flags"]["foreign"] == 1
    assert classified["flags"]["abbreviation"] == 1
    assert classified["corrected_form"] == "máslo"
    assert "maslo" in corpus._filter_status(corpus.forms, "proper")
    assert "maslo" in corpus._filter_status(corpus.forms, "foreign")
    assert "maslo" in corpus._filter_status(corpus.forms, "abbreviation")
    assert "maslo" in corpus._filter_status(corpus.forms, "corrected_form")
    assert corpus.stats()["proper"] == 1
    assert corpus.stats()["foreign"] == 1
    assert corpus.stats()["abbreviation"] == 1
    assert corpus.stats()["corrected_form"] == 1

    unclassified = corpus.decide(
        {
            "form": "maslo",
            "action": "classify",
            "flags": {"proper": False, "foreign": False, "abbreviation": False},
            "corrected_form": "maslo",
        }
    )["item"]
    assert unclassified["flags"]["proper"] == 0
    assert unclassified["my_flags"]["proper"] == 0
    assert unclassified["my_classification"] is True
    assert unclassified["corrected_form"] is None
    assert "maslo" not in corpus._filter_status(corpus.forms, "proper")
    assert "maslo" not in corpus._filter_status(corpus.forms, "corrected_form")
    assert "maslo" in corpus._filter_status(corpus.forms, "mine")
    assert "maslo" not in corpus._filter_status(corpus.forms, "undecided")


def test_bulk_confirmation_rejects_an_engine_error(corpus, monkeypatch):
    monkeypatch.setattr(REVIEW, "_engine", lambda form: (form, form, "engine failed"))
    with pytest.raises(ValueError, match="nemožno hromadne potvrdiť"):
        corpus.decide(
            {
                "form": "okno",
                "action": "confirm",
                "field": "hyphenation",
                "text": "okno",
                "bulk": True,
            }
        )


def test_corrected_form_must_be_one_word(corpus):
    with pytest.raises(ValueError, match="jedno neprázdne slovo"):
        corpus.decide(
            {"form": "okno", "action": "classify", "corrected_form": "dve slová"}
        )


def test_soft_delete_clear_and_undo_are_auditable(corpus):
    deleted = corpus.decide(
        {"form": "okno", "action": "classify", "flags": {"deleted": True}}
    )["item"]
    assert deleted["flags"]["deleted"] == 1
    assert "okno" in corpus._filter_status(corpus.forms, "deleted")
    assert "okno" in corpus._filter_status(corpus.forms, "mine")
    assert "okno" not in corpus._filter_status(corpus.forms, "undecided")
    assert corpus.stats()["deleted"] == 1
    audit = corpus.store.execute(
        "SELECT action, is_deleted FROM decision_log WHERE form = 'okno' "
        "ORDER BY entry_id DESC LIMIT 1"
    ).fetchone()
    assert tuple(audit) == ("classify", 1)

    assert corpus.clear({"form": "okno"})["item"]["flags"]["deleted"] is None
    restored = corpus.undo_last()["item"]
    assert restored["flags"]["deleted"] == 1
    assert corpus.store.execute(
        "SELECT COUNT(*) FROM decision_log WHERE form = 'okno'"
    ).fetchone()[0] == 3
