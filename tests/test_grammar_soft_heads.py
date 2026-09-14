# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Orthographic stem alternation must preserve exact head licensing."""
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from sapfo_grammar.induction import Reading, induce, inventory, readings  # noqa: E402
from sapfo_grammar.synth import noun_paradigm  # noqa: E402


@pytest.mark.parametrize('root,pattern,oblique,head', [
    ('prítomnosť', 'kosť', 'prítomnosti', 'prítomnost'),
    ('hosť', 'hosť', 'hostia', 'host'),
    ('dlaň', 'dlaň', 'dlane', 'dlan'),
])
def test_soft_head_keeps_all_paradigm_forms(root, pattern, oblique, head):
    forms = frozenset(noun_paradigm(root, pattern).values())
    reading = Reading('sub', pattern, root, root, forms, forms - {root})
    data = inventory([(reading, reading.support)])
    assert oblique in data['head_paradigms'][head]['lemma']
    licensed = {f for roles in data['head_paradigms'].values() for fs in roles.values() for f in fs}
    assert licensed == forms


def test_abstract_ost_nouns_do_not_take_dlan_plural():
    corpus = set(noun_paradigm('prítomnosť', 'kosť').values())
    assert {r.pattern for r in readings('prítomnosť', corpus) if r.pos == 'sub'} == {'kosť'}
    data = inventory(induce(corpus, corpus))
    assert any(a['lemma'] == 'prítomnosť' and a['pattern'] == 'kosť' for a in data['analyses'])
    assert 'prítomnoste' not in {f for a in data['analyses'] for f in a['forms']}
    assert 'prítomnosti' in data['head_paradigms']['prítomnost']['lemma']


def test_short_host_is_not_an_abstract_ost_noun():
    corpus = set(noun_paradigm('hosť', 'hosť').values())
    assert any(r.pattern == 'hosť' for r in readings('hosť', corpus))


def test_runtime_recognizes_inflected_soft_head(monkeypatch):
    corpus = set(noun_paradigm('prítomnosť', 'kosť').values())
    data = inventory(induce(corpus, corpus))
    engine = importlib.import_module('slabika.syllabify')
    monkeypatch.setattr(engine, '_GENERATED_FIRST_MEMBERS', frozenset({'všade', 'vše'}))
    monkeypatch.setattr(engine, '_INFERRED_FIRST_MEMBERS', frozenset())
    monkeypatch.setattr(engine, '_GENERATED_HEADS', data['heads'])
    monkeypatch.setattr(engine, '_GENERATED_HEAD_PARADIGMS', data['head_paradigms'])
    for name in ('_generated_compositum', '_heads_a_compositum', '_strip_prefix'):
        func = getattr(engine, name)
        monkeypatch.setattr(engine, name, getattr(func, '__wrapped__', func))
    assert engine._heads_a_compositum('prítomnosti')
    assert not engine._heads_a_compositum('prítomnoste')
    assert importlib.import_module('slabika').hyphenate('všadeprítomnosti') == 'vša·de·prí·tom·nos·ti'
