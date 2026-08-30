# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT

import importlib.util
import sqlite3
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "tools/morph/rmss_index.py"
SPEC = importlib.util.spec_from_file_location("rmss_index", MODULE_PATH)
rmss = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(rmss)


def test_rmss_notation_preserves_only_explicit_morpheme_boundaries():
    assert rmss.notation_to_surface("o-chran-c-a") == "ochranca"
    assert rmss.explicit_morphemes("o-chran-c-a") == ["o", "chran", "c", "a"]
    assert rmss.notation_to_surface("bab-ič:k-a") == "babička"


def test_rmss_entry_parser_skips_aspect_partner_and_reflexive_marker():
    parsed = rmss.parse_entry_tokens(
        ["0", "M", "{pre-vies-ť}", "(sa)", "s-pro-stred-k-ov-a:ť", "V18"]
    )
    assert parsed["parse_status"] == "parsed"
    assert parsed["variants"] == ["s-pro-stred-k-ov-a:ť"]
    assert parsed["flex_code"] == "V18"


def test_rmss_entry_parser_keeps_variants_and_marks_incomplete_rows():
    parsed = rmss.parse_entry_tokens(["1", "N", "čač:a«", "/", "čač-a", "Snx"])
    assert parsed["variants"] == ["čač:a«", "čač-a"]
    partial = rmss.parse_entry_tokens(["0", "N", "{hrab-a:ť}"])
    assert partial["parse_status"] == "partial"
    assert partial["analysis"] == "{hrab-a:ť}"


def test_rmss_font_roles_preserve_bold_roots_and_italic_grammar():
    assert rmss.font_role("Cambria-Bold", 20) == "root"
    assert rmss.font_role("Cambria-Italic", 6) == "grammatical"
    assert rmss.font_role("Cambria-BoldItalic", 22) == "root_grammatical"
    assert rmss.font_role("Cambria", 4) == "other"


def test_rmss_analysis_style_spans_clip_metadata_around_analysis():
    spans = [
        {"text": "0  M  ", "font": "Cambria", "flags": 4},
        {"text": "hno", "font": "Cambria-Bold", "flags": 20},
        {"text": ":j-iv-ov-", "font": "Cambria", "flags": 4},
        {"text": "ý", "font": "Cambria-Italic", "flags": 6},
        {"text": "\t A1", "font": "Cambria", "flags": 4},
    ]

    styled = rmss.analysis_style_spans(spans)

    assert [(span["text"], span["role"]) for span in styled] == [
        ("hno", "root"),
        (":j-iv-ov-", "other"),
        ("ý", "grammatical"),
    ]


def test_rmss_analysis_style_spans_keep_partial_wrapped_entries():
    spans = [
        {"text": "0  N  ", "font": "Cambria", "flags": 4},
        {"text": "chran", "font": "Cambria-Bold", "flags": 20},
        {"text": "-", "font": "Cambria", "flags": 4},
    ]

    assert rmss.analysis_style_spans(spans)[0]["role"] == "root"


def test_rmss_root_audit_helpers_mark_only_requested_seams():
    assert rmss._seams(["pre", "kvap", "enie"]) == {3, 7}
    assert rmss._marked("doktor", {3}) == "dok·tor"


def test_rmss_root_audit_classifies_existing_psp_mismatch(tmp_path, monkeypatch):
    from slabika import syllabify, typo

    monkeypatch.setattr(typo, "break_points", lambda _word: [2])
    monkeypatch.setattr(typo, "hyphenate", lambda _word: "do·ktor")
    monkeypatch.setattr(typo, "_psp_points", lambda _word: [3])
    monkeypatch.setattr(syllabify, "get_morpheme_parts", lambda _word: ["do", "ktor"])

    index_path = tmp_path / "rmss.sqlite"
    with sqlite3.connect(index_path) as connection:
        connection.executescript(
            """
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY, analysis TEXT, printed_page INTEGER,
                parse_status TEXT
            );
            CREATE TABLE entry_variants (
                entry_id INTEGER, variant_no INTEGER, notation TEXT, surface TEXT
            );
            CREATE TABLE entry_style_spans (
                entry_id INTEGER, position INTEGER, surface TEXT, role TEXT
            );
            INSERT INTO entries VALUES (1, 'dokt-or-ø', 216, 'parsed');
            INSERT INTO entry_variants VALUES (1, 1, 'dokt-or-ø', 'doktor');
            INSERT INTO entry_style_spans VALUES (1, 1, 'dokt', 'root');
            INSERT INTO entry_style_spans VALUES (1, 2, 'or', 'other');
            """
        )

    inventory_path = tmp_path / "inventory.sqlite"
    with sqlite3.connect(inventory_path) as connection:
        connection.executescript(
            """
            CREATE TABLE forms (form TEXT, casing_status TEXT);
            INSERT INTO forms VALUES ('doktor', 'resolved');
            """
        )

    review_path = tmp_path / "review.sqlite"
    with sqlite3.connect(review_path) as connection:
        connection.executescript(
            """
            CREATE TABLE psp_comparisons (
                form TEXT, psp_hyphenation TEXT, psp_variants TEXT,
                engine_current_verdict TEXT, psp_reference TEXT,
                reason TEXT, audited_at TEXT
            );
            INSERT INTO psp_comparisons VALUES (
                'doktor', 'dok·tor', '["dok·tor"]', 'correct',
                'PSP V.2.b', 'Dvojica kt sa delí medzi spoluhláskami.',
                '2026-08-25T20:55:04+00:00'
            );
            """
        )

    report = rmss.audit_root_conflicts(index_path, inventory_path, review_path, 10)

    assert report["status_counts"] == {"confirmed_current_mismatch": 1}
    assert report["items"][0]["form"] == "doktor"
    assert report["items"][0]["rmss_root"] == "dokt"
    assert report["items"][0]["syllabic_fallback"] == "dok·tor"
