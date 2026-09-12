# SPDX-FileCopyrightText: 2026 slabika contributors
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Case corrections must never imply approval of engine output."""

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from slabika.review import server
from slabika.review.schema import allow_classification_action
from test_review_console import _inventory, _old_store


@pytest.mark.parametrize('legacy', [False, True])
def test_case_only_edit_is_not_confirmation(tmp_path, legacy):
    inventory = tmp_path / 'inventory.sqlite'
    decisions = tmp_path / 'decisions.sqlite'
    _inventory(inventory)
    if legacy:
        _old_store(decisions)
    corpus = server.Corpus(inventory, decisions)
    try:
        corpus.decide({'form': 'Aaah', 'action': 'classify', 'corrected_form': 'aaah'})
        row = dict(corpus.store.execute(
            "SELECT * FROM decisions WHERE form='Aaah'"
        ).fetchone())
        assert row['action'] == 'classify'
        assert row['corrected_form'] == 'aaah'
        for column in ('hyphenation_action', 'syllabification_action',
                       'expected_hyphenation', 'expected_syllabification'):
            assert row[column] is None
        corpus.decide({'form': 'Aaah', 'action': 'confirm', 'field': 'hyphenation'})
        corpus.decide({'form': 'Aaah', 'action': 'classify', 'flags': {'proper': False}})
        row = corpus.store.execute("SELECT * FROM decisions WHERE form='Aaah'").fetchone()
        assert row['action'] == row['hyphenation_action'] == 'confirm'
        assert row['syllabification_action'] is None
    finally:
        corpus.inventory.close()
        corpus.store.close()


def test_legacy_constraint_migration_preserves_data_indexes_and_rollback():
    store = sqlite3.connect(':memory:')
    store.executescript(server.DECISION_SCHEMA.replace(
        "'invalid', 'classify'", "'invalid'"
    ))
    store.execute("""INSERT INTO decisions(form, action, engine_hyphenation,
        engine_syllabification, engine_version, decided_at)
        VALUES ('Aaah', 'confirm', 'Aaah', 'Aaah', 'old', 'old')""")
    store.commit()
    before = store.execute('SELECT * FROM decisions').fetchall()
    indexes = store.execute("SELECT name, sql FROM sqlite_master WHERE type='index' ORDER BY name").fetchall()
    store.execute('BEGIN IMMEDIATE')
    allow_classification_action(store)
    assert store.execute('SELECT * FROM decisions').fetchall() == before
    assert store.execute("SELECT name, sql FROM sqlite_master WHERE type='index' ORDER BY name").fetchall() == indexes
    store.execute("UPDATE decisions SET action='classify'")
    store.rollback()
    assert store.execute('SELECT * FROM decisions').fetchall() == before
    with pytest.raises(sqlite3.IntegrityError):
        store.execute("UPDATE decisions SET action='classify'")
    store.rollback()
    allow_classification_action(store)
    allow_classification_action(store)
    store.execute("UPDATE decisions SET action='classify'")
    assert store.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    store.close()


def test_reconcile_requires_hyphenation_evidence(tmp_path):
    path = tmp_path / 'reviews.sqlite'
    store = sqlite3.connect(path)
    store.executescript(server.DECISION_SCHEMA)
    for form, action, hyph, expected in (
        ('case-only', 'confirm', None, None),
        ('syllables-only', 'confirm', None, None),
        ('classified', 'classify', None, None),
        ('legacy-confirmed', 'confirm', None, 'legacy-confirmed'),
        ('confirmed', 'confirm', 'confirm', 'confirmed'),
        ('corrected', 'correct', 'correct', 'corrected'),
    ):
        store.execute("""INSERT INTO decisions(form, action, hyphenation_action,
            expected_hyphenation, engine_hyphenation, engine_syllabification,
            engine_version, decided_at) VALUES (?, ?, ?, ?, ?, ?, 'old', 'old')""",
                      (form, action, hyph, expected, form, form))
    store.execute("UPDATE decisions SET syllabification_action='confirm' "
                  "WHERE form='syllables-only'")
    store.commit()
    store.close()
    spec = importlib.util.spec_from_file_location(
        'reconcile_classification_test',
        Path(__file__).resolve().parents[1] / 'tools/review/reconcile.py'
    )
    reconcile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reconcile)
    manual = reconcile.load_manual(path)
    assert {form for form, row in manual.items() if row['action'] == 'confirm'} == {
        'legacy-confirmed', 'confirmed'
    }
    assert manual['corrected']['action'] == 'correct'
    for form in ('case-only', 'syllables-only', 'classified'):
        assert manual[form]['action'] is None
