# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Authored corpus additions must not masquerade as attested bound words."""
import importlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from build_composita_grammar import SUPPLEMENT, build  # noqa: E402
from sapfo_grammar.induction import inventory  # noqa: E402
from sapfo_grammar.supplement import load_supplement, supplement_inventory  # noqa: E402
from sapfo_grammar.synth import adjective_paradigm  # noqa: E402


def test_authored_forms_are_recorded_and_not_added_to_callers_corpus():
    corpus = {'gram'}
    original = set(corpus)
    supplement = load_supplement(SUPPLEMENT)
    result = build(corpus, supplement=supplement)
    assert corpus == original
    assert result['input']['supplement_sha256'] == supplement['sha256']
    assert 'AI-authored' in result['input']['supplement_source']
    assert set(result['input']['authored_additions']) == set(supplement['surface_forms']) - corpus
    assert result['input']['min_support'] == 3
    assert 'gramu' in result['head_paradigms']['gram']['lemma']
    assert 'grafovi' not in result['head_paradigms']['graf']['lemma']
    assert result['supplement_evidence'] == []
    assert not any(a['lemma'] == 'biblio' for a in result['analyses'])


def test_bound_head_uses_real_compounds_not_supplement_self_evidence():
    supplement = load_supplement(SUPPLEMENT)
    corpus = {'bibliograf', 'demograf'}
    result = supplement_inventory(inventory([]), supplement, corpus)
    assert result['first_members'] == {'biblio': 'bound', 'demo': 'bound'}
    assert 'grafovi' in result['head_paradigms']['graf']['lemma']
    assert result['analyses'] == []
    assert result['supplement_evidence'][-1]['attested_examples'] == sorted(corpus)
    sparse = supplement_inventory(inventory([]), supplement, {'bibliograf'})
    assert 'grafovi' in sparse['head_paradigms']['graf']['lemma']
    absent = supplement_inventory(inventory([]), supplement, set())
    assert absent['heads'] == absent['first_members'] == {}


def test_indeclinable_requires_standalone_attestation():
    supplement = load_supplement(SUPPLEMENT)
    result = supplement_inventory(inventory([]), supplement, {'všadeprítomný'})
    assert 'všade' not in result['first_members']
    result = supplement_inventory(inventory([]), supplement, {'všade', 'všadeprítomný'})
    assert result['first_members']['všade'] == 'indeclinable'


@pytest.mark.parametrize('field,value', [
    ('schema_version', 2), ('source', ''), ('surface_forms', ['x-y']),
    ('surface_forms', ['gram', 'gram']), ('surface_forms', ['Gram']),
    ('first_members', [{'form': 'bio', 'kind': 'guess', 'examples': ['biológ']}]),
    ('first_members', [{'form': 'bio', 'kind': 'bound', 'examples': ['graf']}]),
    ('bound_heads', [{'root': 'graf', 'pattern': 'missing', 'reason': 'test', 'examples': ['bibliograf']}]),
])
def test_invalid_supplement_rejected(tmp_path, field, value):
    data = json.loads(SUPPLEMENT.read_text(encoding='utf8'))
    data[field] = value
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps(data), encoding='utf8')
    with pytest.raises(ValueError):
        load_supplement(path)


def test_supplement_hash_changes_with_source(tmp_path):
    original = load_supplement(SUPPLEMENT)
    data = json.loads(SUPPLEMENT.read_text(encoding='utf8'))
    data['source'] += ' Updated.'
    path = tmp_path / 'changed.json'
    path.write_text(json.dumps(data), encoding='utf8')
    assert load_supplement(path)['sha256'] != original['sha256']


def test_candidate_runtime_licenses_animate_bound_head_and_indeclinable(monkeypatch):
    corpus = {'bibliograf', 'demograf', 'všade', 'všadeprítomný'}
    corpus |= set(adjective_paradigm('prítomn', 'pekný').values())
    data = build(corpus, supplement=load_supplement(SUPPLEMENT))
    engine = importlib.import_module('slabika.syllabify')
    monkeypatch.setattr(engine, '_GENERATED_FIRST_MEMBERS', frozenset(data['first_members']))
    monkeypatch.setattr(engine, '_INFERRED_FIRST_MEMBERS', frozenset(
        k for k, v in data['first_members'].items() if v == 'noun stem'))
    monkeypatch.setattr(engine, '_GENERATED_HEADS', data['heads'])
    monkeypatch.setattr(engine, '_GENERATED_HEAD_PARADIGMS', data['head_paradigms'])
    for name in ('_generated_compositum', '_heads_a_compositum', '_strip_prefix'):
        func = getattr(engine, name)
        monkeypatch.setattr(engine, name, getattr(func, '__wrapped__', func))
    api = importlib.import_module('slabika')
    assert api.hyphenate('bibliografovi') == 'bib·li·o·gra·fo·vi'
    assert api.hyphenate('všadeprítomný') == 'vša·de·prí·tom·ný'
    assert not engine._heads_a_compositum('grafujem')
