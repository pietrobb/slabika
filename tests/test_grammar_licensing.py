# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Grammatical eligibility and exact runtime licensing for candidate inventories."""
import importlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import build_composita_grammar as builder  # noqa: E402
from sapfo_grammar.induction import (  # noqa: E402
    Reading,
    adjective_admissible,
    induce,
    inventory,
    readings,
)
from sapfo_grammar.synth import adjective_paradigm, noun_paradigm  # noqa: E402

engine = importlib.import_module('slabika.syllabify')


@pytest.mark.parametrize('root,pattern,allowed', [
    ('ne', 'otcov', False), ('otcov', 'otcov', True), ('matkin', 'otcov', True),
    ('naš', 'rýdzi', False), ('rýdz', 'rýdzi', True), ('cudz', 'cudzí', True),
    ('krásn', 'krásny', True), ('pekn', 'krásny', False),
    ('biel', 'krásny', True), ('mŕtv', 'krásny', True), ('dlh', 'krásny', False),
    ('ne', 'môj', False), ('naš', 'môj', True),
])
def test_pattern_eligibility(root, pattern, allowed):
    assert adjective_admissible(root, pattern) is allowed


def test_shortened_adjective_does_not_reintroduce_pronoun_member():
    corpus = set(adjective_paradigm('naš', 'môj').values())
    corpus |= set(adjective_paradigm('naš', 'rýdzi').values())
    assert not any(r.pattern == 'rýdzi' for r in readings('naši', corpus))
    assert 'naše' not in inventory(induce(corpus, corpus))['first_members']


def test_possessive_can_compete_but_does_not_generate_a_compound_part():
    corpus = set(adjective_paradigm('otcov', 'otcov').values())
    r = next(r for r in readings('otcov', corpus) if r.pattern == 'otcov')
    assert r.pos == 'poss'
    result = inventory([(r, r.support)])
    assert result['analyses']
    assert result['heads'] == result['first_members'] == {}


@pytest.mark.parametrize('root,pattern', [('as', 'anaxagoras'), ('um', 'fórum')])
def test_noun_contraction_cannot_consume_the_entire_root(root, pattern):
    corpus = set(noun_paradigm(root, pattern).values())
    assert not any(r.pattern == pattern for r in readings(root, corpus))
    assert inventory(induce(corpus, corpus))['schema_version'] == 3


def test_mobile_vowel_uses_oblique_stem_and_exact_forms():
    forms = frozenset(noun_paradigm('vietor', 'vietor').values())
    reading = Reading('sub', 'vietor', 'vietor', 'vietor', forms, forms - {'vietor'})
    result = inventory([(reading, reading.support)])
    assert 'vetro' in result['first_members']
    assert 'vietoro' not in result['first_members']
    assert 'vetra' in result['head_paradigms']['vetr']['lemma']
    assert 'vietor' in result['head_paradigms']['vietor']['lemma']
    assert 'vietora' not in result['head_paradigms']['vietor']['lemma']


def test_exact_head_forms_do_not_borrow_universal_endings(monkeypatch):
    monkeypatch.setattr(engine, '_GENERATED_HEAD_PARADIGMS', None)
    monkeypatch.setattr(engine, '_GENERATED_HEADS', {'vin': 'verb', 'vod': 'lemma'})
    monkeypatch.setattr(engine, '_GENERATED_HEAD_FORMS', {
        'vin': frozenset({'vinúť', 'vinul'}), 'vod': frozenset({'voda', 'vody'}),
    })
    assert engine._heads_a_compositum('vinul')
    assert not engine._heads_a_compositum('vinu')
    assert not engine._heads_a_compositum('vin')
    assert not engine._heads_a_compositum('vinul', inferred_first=True)
    assert engine._heads_a_compositum('vody', inferred_first=True)
    assert not engine._heads_a_compositum('vodovi')


def test_missing_head_forms_fail_closed(monkeypatch):
    monkeypatch.setattr(engine, '_GENERATED_HEAD_PARADIGMS', None)
    monkeypatch.setattr(engine, '_GENERATED_HEADS', {'vod': 'lemma'})
    monkeypatch.setattr(engine, '_GENERATED_HEAD_FORMS', {})
    assert not engine._heads_a_compositum('voda')


def test_participle_branch_must_also_obey_exact_forms(monkeypatch):
    monkeypatch.setattr(engine, '_GENERATED_HEAD_PARADIGMS', None)
    monkeypatch.setattr(engine, '_GENERATED_FIRST_MEMBERS', frozenset({'novo'}))
    monkeypatch.setattr(engine, '_INFERRED_FIRST_MEMBERS', frozenset())
    monkeypatch.setattr(engine, '_GENERATED_HEADS', {'bud': 'verb'})
    monkeypatch.setattr(engine, '_GENERATED_HEAD_FORMS', {})
    assert engine._generated_compositum('novobudený') is None


def test_export_does_not_merge_verb_forms_into_a_noun_permission():
    verb = Reading('verb', 'robiť', 'stan', 'staniť',
                   frozenset({'staniť', 'stanil'}), frozenset({'stanil'}))
    noun = Reading('sub', 'dub', 'stan', 'stan',
                   frozenset({'stan', 'stanu'}), frozenset({'stanu'}))
    result = inventory([(verb, verb.support), (noun, noun.support)])
    assert result['heads']['stan'] == 'lemma'
    assert result['head_paradigms']['stan'] == {'lemma': ['stan', 'stanu'], 'verb': ['stanil', 'staniť']}


def test_build_rejects_source_changes_during_generation(monkeypatch):
    hashes = iter([builder.LOADED_SOURCES, {}])
    monkeypatch.setattr(builder, 'source_hashes', lambda: next(hashes))
    with pytest.raises(RuntimeError, match='during generation'):
        builder.build({'voda'})


def test_compact_candidate_and_cli_path_protection(tmp_path):
    corpus = tmp_path / 'corpus.sqlite'
    with sqlite3.connect(corpus) as db:
        db.execute('create table forms(form text)')
        db.executemany('insert into forms values (?)',
                       [(f,) for f in noun_paradigm('vod', 'žena').values()])
    audit, runtime = tmp_path / 'audit.json', tmp_path / 'runtime.json'
    command = [sys.executable, str(ROOT / 'tools/build_composita_grammar.py'),
               '--corpus', str(corpus), '--output', str(audit), '--runtime-output']
    assert subprocess.run(command + [str(audit)], capture_output=True).returncode != 0
    assert not audit.exists()
    subprocess.run(command + [str(runtime)], check=True, capture_output=True)
    full = json.loads(audit.read_text(encoding='utf8'))
    compact = json.loads(runtime.read_text(encoding='utf8'))
    assert compact == builder.runtime_inventory(full)
    assert 'analyses' not in compact
    assert compact['schema_version'] == 3
    assert compact['input']['surface_forms_sha256'] == full['input']['surface_forms_sha256']
