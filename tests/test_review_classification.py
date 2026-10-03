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


@pytest.mark.parametrize('legacy', [False, True])
def test_language_selection_persists_recalculates_and_undoes(tmp_path, legacy):
    inventory = tmp_path / 'inventory.sqlite'
    decisions = tmp_path / 'decisions.sqlite'
    _inventory(inventory)
    with sqlite3.connect(inventory) as connection:
        connection.executemany('INSERT INTO forms VALUES (?, ?, ?)', [
            ('Pierre', 'resolved', None), ('Saint-Denis', 'resolved', None),
        ])
    if legacy:
        _old_store(decisions)
    corpus = server.Corpus(inventory, decisions)
    try:
        assert corpus._engine_hyphenation('Pierre') == 'Pierre'
        corpus._tex_disagreements = frozenset({'Pierre'})
        item = corpus.decide({'form': 'Pierre', 'action': 'classify', 'language': 'fr'})['item']
        assert item['language'] == 'french'
        assert item['hyphenation'] == 'Pierre'
        assert item['my_classification']
        assert item['my_hyphenation_action'] is None
        assert item['my_syllabification_action'] is None
        assert corpus._engine_hyphenation('Pierre') == 'Pierre'
        assert corpus._tex_disagreements is None
        assert corpus.store.execute('SELECT language FROM decision_log ORDER BY entry_id DESC').fetchone()[0] == 'french'
        corpus.decide({'form': 'Pierre', 'action': 'confirm', 'field': 'hyphenation'})
        item = corpus.decide({'form': 'Pierre', 'action': 'classify', 'flags': {'proper': True}})['item']
        assert item['language'] == 'french'
        assert item['my_expected'] == 'Pierre'
        assert item['my_hyphenation_match_mode'] == 'preferred'
        assert not item['my_disagrees']
        item = corpus.decide({'form': 'Pierre', 'action': 'classify', 'language': 'sk'})['item']
        assert item['hyphenation'] == 'Pier·re'
        assert item['my_disagrees']
        assert corpus.undo_last()['item']['language'] == 'french'
        assert corpus.clear({'form': 'Pierre'})['item']['language'] is None
        assert corpus._engine_hyphenation('Pierre') == 'Pierre'
        assert corpus.undo_last()['item']['hyphenation'] == 'Pierre'
        item = corpus.decide({'form': 'Saint-Denis', 'action': 'classify', 'language': 'fr'})['item']
        assert item['hyphenation'] == 'Saint-·De·nis'
        item = corpus.decide({'form': 'Saint-Denis', 'action': 'confirm', 'text': 'Saint--De-nis'})['item']
        assert item['my_expected'] == 'Saint-·De·nis'
        assert not item['my_disagrees']
        corpus.inventory.close()
        corpus.store.close()
        corpus = server.Corpus(inventory, decisions)
        assert corpus._fresh('Pierre')['language'] == 'french'
        assert corpus._fresh('Saint-Denis')['language'] == 'french'
        assert corpus.store.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    finally:
        corpus.inventory.close()
        corpus.store.close()


@pytest.mark.parametrize('language', ['spanish', '', 1, False, ['fr']])
def test_invalid_language_does_not_save(tmp_path, language):
    inventory = tmp_path / 'inventory.sqlite'
    _inventory(inventory)
    corpus = server.Corpus(inventory, tmp_path / 'decisions.sqlite')
    try:
        with pytest.raises(ValueError, match='language'):
            corpus.decide({'form': 'Aaah', 'action': 'classify', 'language': language})
        assert corpus.store.execute('SELECT COUNT(*) FROM decisions').fetchone()[0] == 0
        assert corpus.store.execute('SELECT COUNT(*) FROM decision_log').fetchone()[0] == 0
    finally:
        corpus.inventory.close()
        corpus.store.close()


def test_ui_has_manual_language_control():
    html = server.UI_PATH.read_text(encoding='utf-8')
    assert 'class="word-language"' in html
    for language in ('english', 'german', 'french', 'slovak'):
        assert f'<option value="{language}">' in html
    assert 'action: "classify", language:' in html
