# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Frozen alignment and independently interpreted English morphology regressions."""

import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_foreign_review import initialize_inventory, populate_forms
from slabika.english_projection import EnglishMorphology, normalize_alignment
from evaluate_foreign_corpora import divided, project_psp_points
from refresh_english_review import apply, main, plan


def pronunciation(word, *spans, language="english"):
    return SimpleNamespace(word=word, language=language,
                           spans=tuple((s, tuple(p.split())) for s, p in spans))


CASES = [
    (pronunciation("pepper", ("pe", "pʰ ɛ"), ("pp", "p"), ("er", "ɚ")), "pep·per"),
    (pronunciation("penny", ("pe", "pʰ ɛ"), ("nn", "ɲ"), ("y", "i")), "pen·ny"),
    (pronunciation("abbey", ("a", "æ"), ("bb", "bʲ"), ("ey", "i")), "ab·bey"),
    (pronunciation("abba", ("a", "æ"), ("bb", "b"), ("a", "ə")), "ab·ba"),
    (pronunciation("peggy", ("pe", "pʰ"), ("g", "ɛ"), ("g", "ɟ"), ("y", "i")), "peg·gy"),
    (pronunciation("pegging", ("pe", "pʰ"), ("g", "ɛ"), ("gi", "ɟ ɪ"), ("ng", "ŋ")), "peg·ging"),
    (pronunciation("people", ("pe", "pʰ iː"), ("op", "p"), ("le", "ə ɫ")), "peo·ple"),
    (pronunciation("peopled", ("pe", "pʰ iː"), ("op", "p"), ("le", "ə ɫ"), ("d", "d")), "peo·pled"),
    (pronunciation("mocking", ("mo", "m ɑ"), ("ck", "c"), ("i", "ɪ"), ("ng", "ŋ")), "mo·cking"),
    (pronunciation("mottled", ("mo", "m ɑ"), ("tt", "t"), ("le", "ə ɫ"), ("d", "d")), "mo·ttled"),
    (pronunciation("add", ("a", "æ"), ("dd", "d")), "add"),
]


@pytest.mark.parametrize("p, expected", CASES, ids=[p.word for p, _ in CASES])
def test_projection(p, expected):
    original = p.spans
    points, complete = project_psp_points(p)
    assert divided(p.word, points) == expected
    assert complete
    normalized = normalize_alignment(p)
    assert "".join(s for s, _ in normalized) == p.word
    assert tuple(x for _, ps in normalized for x in ps) == tuple(x for _, ps in original for x in ps)
    assert p.spans == original
    assert all(1 < point < len(p.word) - 1 for point in points)


def test_unrepaired_vowel_on_consonant_is_not_complete():
    p = pronunciation("percussion", ("p", "pʰ"), ("er", "ɚ"), ("cu", "kʰ"),
                      ("s", "ɐ"), ("si", "ʃ"), ("on", "ə n"))
    assert project_psp_points(p)[1] is False


@pytest.mark.parametrize("language", ["german", "french"])
def test_repairs_are_english_only(language):
    p = pronunciation("penny", ("pe", "p ɛ"), ("nn", "n"), ("y", "i"), language=language)
    assert normalize_alignment(p) == p.spans
    assert divided(p.word, project_psp_points(p)[0]) == "pe·nny"


MODEST = pronunciation("modest", ("mo", "m ɑː"), ("de", "d ə"), ("st", "s t"))
MODESTLY = pronunciation("modestly", *[(s, " ".join(p)) for s, p in MODEST.spans], ("ly", "ʎ i"))
PEN = pronunciation("pen", ("pe", "pʰ ɛ"), ("n", "n"))
KNIFE = pronunciation("knife", ("kn", "n"), ("i", "aj"), ("f", "f"), ("e", ""))
PENKNIFE = pronunciation("penknife", ("pe", "pʰ ɛ"), ("n", "n"), ("kn", ""),
                         ("i", "aj"), ("f", "f"), ("e", ""))


@pytest.mark.parametrize("p,expected", [(MODESTLY, "mo·dest·ly"), (PENKNIFE, "pen·knife")])
def test_morpheme_seam_replaces_only_its_syllabic_gap(p, expected):
    morph = EnglishMorphology([MODEST, MODESTLY, PEN, KNIFE, PENKNIFE])
    assert divided(p.word, morph.refine(p, project_psp_points(p)[0])) == expected


def test_no_substring_only_morphology_or_arbitrary_corpus_concatenation():
    gent = pronunciation("gent", ("gent", "dʒ ɛ n t"))
    gently = pronunciation("gently", ("gent", "dʒ ɛ n t"), ("ly", "l i"))
    car = pronunciation("car", ("car", "k ɑ ɹ"))
    pet = pronunciation("pet", ("pet", "p ɪ t"))
    carpet = pronunciation("carpet", ("car", "k ɑ ɹ"), ("pet", "p ɪ t"))
    morph = EnglishMorphology([gent, gently, car, pet, carpet, MODESTLY, PENKNIFE])
    for p in (gently, carpet, MODESTLY, PENKNIFE):
        assert morph.seams(p) == ()


def test_ly_needs_independent_family_and_matching_phones():
    cold = pronunciation("cold", ("cold", "k ow l d"))
    coldness = pronunciation("coldness", ("cold", "k ow l d"), ("ness", "n ə s"))
    coldly = pronunciation("coldly", ("cold", "k ow l d"), ("ly", "l i"))
    morph = EnglishMorphology([cold, coldness, coldly])
    assert morph.seams(coldly) == (4,)
    wrong = pronunciation("coldly", ("cold", "k ɑ l d"), ("ly", "l i"))
    assert morph.seams(wrong) == ()


def seed(db):
    ps = [MODEST, MODESTLY, PEN, KNIFE, PENKNIFE, CASES[0][0]]
    populate_forms(db, "en", {p.word for p in ps} | {"failed"})
    with db:
        for p in ps:
            db.execute("UPDATE foreign_evidence SET pronunciation_status='generated', "
                       "proposed_hyphenation=?, proposal_status='experimental', ipa='unchanged', "
                       "raw_phones='unchanged', spans_json=?, model_json='{}' WHERE form=?",
                       (p.word, json.dumps(p.spans), p.word))
        db.execute("UPDATE foreign_evidence SET pronunciation_status='error', "
                   "proposal_status='error', error='keep model error' WHERE form='failed'")
        db.execute("UPDATE adjudications SET expected_hyphenation='mo·dest·ly', "
                   "review_status='verified', source='human', reason='keep' WHERE form='modestly'")


def test_refresh_preserves_human_and_raw_evidence_and_is_idempotent(tmp_path):
    db = initialize_inventory(tmp_path / "en.sqlite", "en")
    try:
        seed(db)
        human = db.execute("SELECT * FROM adjudications ORDER BY form").fetchall()
        raw_sql = "SELECT form,ipa,raw_phones,spans_json,model_json,pronunciation_status,error FROM foreign_evidence ORDER BY form"
        raw = db.execute(raw_sql).fetchall()
        forms = db.execute("SELECT * FROM forms ORDER BY form").fetchall()
        report, updates = plan(db)
        assert db.execute(raw_sql).fetchall() == raw
        apply(db, report, updates)
        assert db.execute("SELECT * FROM adjudications ORDER BY form").fetchall() == human
        assert db.execute("SELECT * FROM forms ORDER BY form").fetchall() == forms
        assert db.execute(raw_sql).fetchall() == raw
        assert db.execute("SELECT proposed_hyphenation FROM foreign_evidence WHERE form='modestly'").fetchone() == ("mo·dest·ly",)
        assert plan(db)[0]["changes"] == []
        report, updates = plan(db)
        with db:
            db.execute("UPDATE foreign_evidence SET proposed_hyphenation='different' WHERE form='pepper'")
        with pytest.raises(ValueError, match="changed since planning"):
            apply(db, report, updates)
        assert db.execute("SELECT proposed_hyphenation FROM foreign_evidence WHERE form='pepper'").fetchone() == ("different",)
    finally:
        db.close()


def test_cli_dry_run_then_backup_and_apply(tmp_path):
    path = tmp_path / "en.sqlite"
    db = initialize_inventory(path, "en")
    seed(db)
    db.close()
    args = ["--inventory", str(path), "--output-dir", str(tmp_path / "audit")]
    before = path.read_bytes()
    assert main(args) == 0
    assert path.read_bytes() == before
    assert main(args + ["--apply"]) == 0
    backup = next((tmp_path / "audit").glob("en-before-*.sqlite"))
    with sqlite3.connect(backup) as old:
        assert old.execute("SELECT proposed_hyphenation FROM foreign_evidence WHERE form='modestly'").fetchone() == ("modestly",)


def test_incomplete_projection_cannot_move_a_seam_across_a_missing_nucleus(tmp_path):
    db = initialize_inventory(tmp_path / "en.sqlite", "en")
    try:
        ps = [pronunciation("upright", ("u", "ɐ"), ("p", "p"), ("ri", "ɹ"),
                            ("gh", "aj"), ("t", "t"))]
        ps += [pronunciation("uprightness", ("upright", "ɐ p ɹ aj t"), ("ness", "n ə s")),
               pronunciation("uprightly", ("u", "ɐ"), ("p", "p"), ("ri", "ɹ"),
                             ("gh", "aj"), ("t", "t"), ("ly", "ʎ i"))]
        populate_forms(db, "en", {p.word for p in ps})
        with db:
            for p in ps:
                db.execute("UPDATE foreign_evidence SET pronunciation_status='generated', spans_json=? WHERE form=?",
                           (json.dumps(p.spans), p.word))
        _, updates = plan(db)
        row = next(u for u in updates if u[-1] == "uprightly")
        assert row[:2] == ("up·rightly", "incomplete")
    finally:
        db.close()
