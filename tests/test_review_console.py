# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Regression tests for independent review of both engine outputs."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from slabika.review import server as REVIEW

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


def test_default_review_assets_are_available():
    assert REVIEW.DEFAULT_INVENTORY.exists()
    assert all(path.exists() for path in REVIEW.DEFAULT_BLIND)
    assert REVIEW.UI_PATH.exists()
    assert REVIEW.tex_hyphenate("maslo")


def test_server_uses_a_free_port_when_default_is_occupied():
    occupied = REVIEW.ThreadingHTTPServer(("127.0.0.1", 0), REVIEW.Handler)
    server = REVIEW._bind_server(occupied.server_address[1])
    try:
        assert server.server_address[1] != occupied.server_address[1]
    finally:
        server.server_close()
        occupied.server_close()


def test_marked_output_may_only_change_boundaries():
    assert REVIEW._parse_marked("maslo", "ma-slo") == "ma·slo"
    assert REVIEW._parse_marked("maslo", " mas--lo ") == "mas·lo"
    with pytest.raises(ValueError, match="musí zostať presne ten tvar"):
        REVIEW._parse_marked("maslo", "ma-x-slo")


def test_multiple_blind_audits_are_merged(tmp_path):
    paths = []
    for index, (form, marked) in enumerate((("maslo", "mas|lo"), ("okno", "ok|no"))):
        path = tmp_path / f"blind-{index}.sqlite"
        connection = sqlite3.connect(path)
        connection.execute(
            """CREATE TABLE decisions (
                   form TEXT, assessment TEXT, expected_variants_json TEXT, confidence TEXT
               )"""
        )
        connection.execute(
            "INSERT INTO decisions VALUES (?, 'resolved', ?, 'high')",
            (form, json.dumps([marked])),
        )
        connection.commit()
        connection.close()
        paths.append(path)

    assert REVIEW._load_blind(paths) == {
        "maslo": {"assessment": "resolved", "variants": ["mas·lo"], "confidence": "high"},
        "okno": {"assessment": "resolved", "variants": ["ok·no"], "confidence": "high"},
    }


def test_ui_reviews_only_typographic_word_division():
    html = REVIEW.UI_PATH.read_text(encoding="utf-8")
    assert html.count('<input class="edit"') == 1
    assert 'data-field="h"' in html
    assert 'data-field="s"' not in html
    assert "slabiky (výslovnosť)" not in html
    for label in ("Meno", "Cudzie", "Skratka", "Opraviť", "Vymazať"):
        assert f">{label}</button>" in html
    assert 'id="tex-diff"' in html
    assert 'id="blind-human-diff"' in html
    assert "Engine (TeX 2/3) ≠ Chlebíková" in html
    assert "Slepý AI ≠ človek" in html
    assert 'placeholder="hľadať tvar…  (/)"' in html
    assert '["engine (TeX 2/3)", dash(it.engine_tex), null]' in html
    assert '["Chlebíková teraz", it.tex, it.tex_disagrees]' in html
    assert 'value="psp_comparison"' in html
    assert '<details class="psp-audit">' in html
    assert "Aktuálny engine (" in html
    assert "Správne podľa PSP (" in html
    assert 'correct: "SPRÁVNE"' in html
    assert 'incorrect: "NESPRÁVNE"' in html


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


def test_voice_disagreement_filters_compose_with_query_and_status(corpus, monkeypatch):
    engine = {"maslo": "mas·lo", "okno": "ok·no"}
    tex = {"maslo": "ma·slo", "okno": "okno"}
    monkeypatch.setattr(
        REVIEW, "_engine", lambda form: (engine.get(form, form), form, None)
    )
    tex_calls = 0

    def tex_voice(form):
        nonlocal tex_calls
        tex_calls += 1
        return tex.get(form, form)

    monkeypatch.setattr(REVIEW, "tex_hyphenate", tex_voice)

    for form, marked in (("maslo", "mas-lo"), ("okno", "ok-no")):
        corpus.decide(
            {"form": form, "action": "confirm", "field": "hyphenation", "text": marked}
        )
    corpus.blind = {
        "maslo": {"assessment": "resolved", "variants": ["ma·slo"]},
        "okno": {"assessment": "resolved", "variants": ["ok·no"]},
        "iphone": {"assessment": "uncertain", "variants": []},
    }
    tex_calls = 0

    tex_page = corpus.page("m", "prefix", "confirm", 0, 10, tex_diff=True)
    assert tex_page["total"] == 1
    assert [item["review_form"] for item in tex_page["items"]] == ["maslo"]
    assert tex_page["items"][0]["engine_tex"] == "maslo"
    assert tex_page["items"][0]["tex_disagrees"] is True
    okno = corpus.page("okno", "exact", "confirm", 0, 10)["items"][0]
    assert okno["hyphenation"] == "ok·no"
    assert okno["engine_tex"] == okno["tex"] == "okno"
    assert okno["tex_disagrees"] is False
    cached_tex_calls = tex_calls
    assert cached_tex_calls == len(corpus.forms) + 2

    blind_page = corpus.page(
        "", "prefix", "confirm", 0, 10, blind_human_diff=True
    )
    assert blind_page["total"] == 1
    assert [item["review_form"] for item in blind_page["items"]] == ["maslo"]
    assert corpus.page(
        "ok", "prefix", "confirm", 0, 10, blind_human_diff=True
    )["total"] == 0

    combined = corpus.page(
        "m", "prefix", "confirm", 0, 10, tex_diff=True, blind_human_diff=True
    )
    assert [item["review_form"] for item in combined["items"]] == ["maslo"]
    assert tex_calls == cached_tex_calls + 2


def test_psp_comparison_is_persistent_filterable_and_separate_from_human_review(corpus):
    corpus.store.execute(
        """INSERT INTO psp_comparisons VALUES (
               'maslo', 'audit-2026-08-25', 'maslo family', 'ma·slo',
               'ma·slo', 'mas·lo', 'ma·slo', 'mas·lo', 'mas·lo',
               'mas·lo', '["mas·lo"]', 'correct', 'incorrect', 'engine_only',
               'engine_corrected', 'PSP V.2.b / §4.2',
               'Dve spoluhlásky sa delia medzi sebou.',
               'Chlebíková zostáva odlišná.', 2, 3,
               'old-ref', 'new-ref', '2026-08-25T16:00:00+00:00'
           )"""
    )
    corpus.store.commit()

    page = corpus.page("", "prefix", "psp_comparison", 0, 10)
    assert [item["review_form"] for item in page["items"]] == ["maslo"]
    comparison = page["items"][0]["psp_comparison"]
    assert comparison == {
        "audit_id": "audit-2026-08-25",
        "family": "maslo family",
        "chlebikova": "ma·slo",
        "engine_before": "ma·slo",
        "engine_after": "mas·lo",
        "engine_tex_before": "ma·slo",
        "engine_tex_after": "mas·lo",
        "psp": "mas·lo",
        "psp_tex": "mas·lo",
        "psp_variants": ["mas·lo"],
        "psp_tex_variants": ["maslo"],
        "engine_current_verdict": "correct",
        "chlebikova_verdict": "incorrect",
        "comparison_outcome": "engine_only",
        "verdict": "engine_corrected",
        "psp_reference": "PSP V.2.b / §4.2",
        "reason": "Dve spoluhlásky sa delia medzi sebou.",
        "comparison_note": "Chlebíková zostáva odlišná.",
        "left_min": 2,
        "right_min": 3,
        "engine_before_ref": "old-ref",
        "engine_after_ref": "new-ref",
        "audited_at": "2026-08-25T16:00:00+00:00",
    }
    assert page["items"][0]["my_expected"] is None
    assert corpus.stats()["psp_comparisons"] == 1
    assert corpus.store.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1


def test_psp_audit_freezes_every_difference_and_keeps_human_review_separate(
    corpus, monkeypatch
):
    engine = {
        "aaah": "Aa·ah",
        "iphone": "iph·one",
        "maslo": "mas·lo",
        "okno": "ok·no",
    }
    chlebikova = {
        "aaah": "Aaah",
        "iphone": "ip·hone",
        "maslo": "ma·slo",
        "okno": "okno",
    }

    def engine_voice(form):
        marked = REVIEW._recase_marked(engine[form.lower()], form)
        return marked, form, None

    def tex_voice(form):
        return chlebikova[form.lower()]

    monkeypatch.setattr(REVIEW, "_engine", engine_voice)
    monkeypatch.setattr(REVIEW, "tex_hyphenate", tex_voice)
    before_human = corpus.store.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    before_log = corpus.store.execute("SELECT COUNT(*) FROM decision_log").fetchone()[0]

    progress = corpus.freeze_psp_audit("audit-1", "engine-ref", "chlebikova-ref")

    assert progress["batch_size"] == 100
    assert progress["total"] == 4
    assert progress["batches"] == 1
    assert progress["adjudicated"] == 0
    assert progress["next_batch"] == 1
    batch = corpus.psp_audit_batch("audit-1", 1)
    assert [item["position"] for item in batch["items"]] == [1, 2, 3, 4]
    assert [item["form"] for item in batch["items"]] == [
        "iPhone", "iphone", "MASLO", "maslo"
    ]
    assert all(
        item["engine_tex_hyphenation"] != item["chlebikova_hyphenation"]
        for item in batch["items"]
    )

    monkeypatch.setattr(
        REVIEW, "_engine", lambda form: (form, form, None)
    )
    assert corpus.psp_audit_batch("audit-1", 1)["items"] == batch["items"]
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        corpus.store.execute(
            "UPDATE psp_audit_items SET form = 'zmena' WHERE audit_id = 'audit-1'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        corpus.store.execute(
            "DELETE FROM psp_audit_items WHERE audit_id = 'audit-1'"
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        corpus.store.execute(
            "UPDATE psp_audit_runs SET total_items = 999 WHERE audit_id = 'audit-1'"
        )
    corpus.store.rollback()

    monkeypatch.setattr(
        REVIEW, "_engine", lambda form: (form, form, "test engine failure")
    )
    with pytest.raises(RuntimeError, match="engine zlyhal"):
        corpus.adjudicate_psp(
            {
                "audit_id": "audit-1",
                "form": "maslo",
                "psp_hyphenation": "mas-lo",
                "psp_reference": "PSP V.2.b / §4.2",
                "reason": "Dve spoluhlásky medzi jadrami sa delia medzi sebou.",
            }
        )
    assert corpus.store.execute(
        "SELECT COUNT(*) FROM psp_comparisons WHERE audit_id = 'audit-1'"
    ).fetchone()[0] == 0
    monkeypatch.setattr(REVIEW, "_engine", lambda form: (form, form, None))

    result = corpus.adjudicate_psp(
        {
            "audit_id": "audit-1",
            "form": "maslo",
            "psp_hyphenation": "mas-lo",
            "psp_reference": "PSP V.2.b / §4.2",
            "reason": "Dve spoluhlásky medzi jadrami sa delia medzi sebou.",
        }
    )
    assert result["progress"]["adjudicated"] == 1
    comparison = corpus.store.execute(
        "SELECT * FROM psp_comparisons WHERE audit_id = 'audit-1' AND form = 'maslo'"
    ).fetchone()
    assert comparison["engine_current_verdict"] == "correct"
    assert comparison["chlebikova_verdict"] == "incorrect"
    assert comparison["comparison_outcome"] == "engine_only"

    corpus.adjudicate_psp(
        {
            "audit_id": "audit-1",
            "form": "maslo",
            "psp_hyphenation": "mas-lo",
            "psp_variants": ["ma-slo"],
            "psp_reference": "PSP V.3 / §3.5",
            "reason": "PSP pripúšťajú dva variantné body.",
            "replace": True,
        }
    )
    comparison = corpus.store.execute(
        "SELECT * FROM psp_comparisons WHERE audit_id = 'audit-1' AND form = 'maslo'"
    ).fetchone()
    assert comparison["comparison_outcome"] == "both_correct"
    assert json.loads(comparison["psp_variants"]) == ["mas·lo", "ma·slo"]

    monkeypatch.setattr(REVIEW, "_engine", engine_voice)
    corpus.adjudicate_psp(
        {
            "audit_id": "audit-1",
            "form": "iPhone",
            "psp_hyphenation": "i-Pho-ne",
            "psp_reference": "PSP V.4 / §5.4",
            "reason": "Test samostatného výsledku, pri ktorom nesedí ani jeden hlas.",
        }
    )
    assert corpus.store.execute(
        """SELECT comparison_outcome FROM psp_comparisons
           WHERE audit_id = 'audit-1' AND form = 'iPhone'"""
    ).fetchone()[0] == "both_incorrect"
    assert corpus.store.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == before_human
    assert corpus.store.execute("SELECT COUNT(*) FROM decision_log").fetchone()[0] == before_log


def test_psp_audit_can_store_unresolved_engine_failure(corpus, monkeypatch):
    corpus.store.execute(
        """INSERT INTO psp_audit_runs VALUES
           ('audit-foreign', 'engine', 'chlebikova', 2, 3, 100, 0,
            'building', '2026-08-25T19:00:00+00:00')"""
    )
    corpus.store.execute(
        """INSERT INTO psp_audit_items VALUES
           ('audit-foreign', 1, 'Español', 'Español', 'Español', 'Es·pañol')"""
    )
    corpus.store.execute(
        """UPDATE psp_audit_runs
           SET total_items = 1, status = 'frozen'
           WHERE audit_id = 'audit-foreign'"""
    )
    corpus.store.commit()
    monkeypatch.setattr(
        REVIEW,
        "_engine",
        lambda form: (form, form, "ValueError: neznáma cudzia graféma ñ"),
    )

    corpus.adjudicate_psp(
        {
            "audit_id": "audit-foreign",
            "form": "Español",
            "psp_hyphenation": None,
            "psp_reference": "PSP V.4 / §5.4",
            "reason": "Bez doloženej výslovnosti nemožno cudzie písanie rozhodnúť.",
        }
    )

    row = corpus.store.execute(
        """SELECT * FROM psp_comparisons
           WHERE audit_id = 'audit-foreign' AND form = 'Español'"""
    ).fetchone()
    assert row["engine_after_hyphenation"] == "Español"
    assert row["engine_current_verdict"] == "unresolved"
    assert "neznáma cudzia graféma ñ" in row["comparison_note"]


def test_psp_audit_batches_are_fixed_groups_of_one_hundred(corpus):
    corpus.store.execute(
        """INSERT INTO psp_audit_runs VALUES
           ('audit-205', 'engine', 'chlebikova', 2, 3, 100, 0,
            'building', '2026-08-25T19:00:00+00:00')"""
    )
    corpus.store.executemany(
        """INSERT INTO psp_audit_items VALUES
           ('audit-205', ?, ?, ?, ?, ?)""",
        [
            (position, f"slovo{position}", f"slo·vo{position}",
             f"slo·vo{position}", f"slov·o{position}")
            for position in range(1, 206)
        ],
    )
    corpus.store.execute(
        """UPDATE psp_audit_runs
           SET total_items = 205, status = 'frozen'
           WHERE audit_id = 'audit-205'"""
    )
    corpus.store.commit()

    progress = corpus.psp_audit_progress("audit-205")
    assert progress["batches"] == 3
    assert [
        len(corpus.psp_audit_batch("audit-205", batch)["items"])
        for batch in (1, 2, 3)
    ] == [100, 100, 5]
    assert corpus.psp_audit_batch("audit-205", 2)["items"][0]["position"] == 101
    assert corpus.psp_audit_batch("audit-205", 3)["items"][-1]["position"] == 205


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
