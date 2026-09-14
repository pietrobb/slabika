# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The experimental grammar builder must be independent and reproducible."""
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from build_composita_grammar import build, load_corpus  # noqa: E402
from compare_composita import compare  # noqa: E402
from sapfo_grammar.induction import Reading, induce, inventory, readings  # noqa: E402
from sapfo_grammar.synth import (  # noqa: E402
    adjective_paradigm,
    normalize_soft_consonants,
    noun_paradigm,
    verb_paradigm,
)


@pytest.mark.parametrize('word', ['oblasťi', 'hosťia', 'ľeďí', 'škára', 'ťieň'])
def test_normalization_optimization_preserves_original_rule(word):
    expected = word
    for soft, hard in {'ť': 't', 'ď': 'd', 'ň': 'n', 'ľ': 'l'}.items():
        for vowel in ('ia', 'ie', 'iu', 'í', 'i', 'é', 'e'):
            expected = expected.replace(soft + vowel, hard + vowel)
    assert normalize_soft_consonants(word) == expected


def test_no_lemma_from_self_evidence():
    assert induce(['voda'], {'voda'}) == []


def test_every_reading_round_trips_and_excludes_citation_support():
    corpus = set(noun_paradigm('škár', 'dáma').values())
    for probe in sorted(corpus):
        for reading in readings(probe, corpus):
            assert probe in reading.forms
            assert reading.lemma in corpus
            assert reading.lemma not in reading.support
            assert reading.support <= corpus


def test_stronger_paradigm_subsumes_false_lemma():
    corpus = set(noun_paradigm('škár', 'dáma').values()) | {'škár'}
    survivors = induce(corpus, corpus)
    assert any(r.lemma == 'škára' for r, _ in survivors)
    assert not any(r.lemma == 'škár' for r, _ in survivors)


def test_pronoun_competes_but_is_not_a_compound_member():
    corpus = set(adjective_paradigm('naš', 'môj').values())
    result = inventory(induce(corpus, corpus))
    assert any(a['pos'] == 'pron' for a in result['analyses'])
    assert 'naše' not in result['first_members']


def test_export_keeps_evidence_and_head_kind_without_external_residue():
    read = Reading('adj', 'pekný', 'pekn', 'pekný',
                   frozenset({'pekný', 'pekná'}), frozenset({'pekná'}))
    result = inventory([(read, frozenset({'pekná'}))])
    assert result['first_members'] == {'pekno': 'adjective'}
    assert result['heads'] == {'pekn': 'root'}
    assert result['analyses'][0]['owned'] == ['pekná']
    assert result['analyses'][0]['pattern'] == 'pekný'


def test_regular_ovat_present_stem():
    forms = verb_paradigm('pracov', 'pracovať')
    assert forms['inf'] == 'pracovať'
    assert 'pracujem' in forms.values()
    assert 'pracoval' in forms.values()


def test_corpus_loader_reads_only_surface_forms(tmp_path):
    path = tmp_path / 'corpus.sqlite'
    db = sqlite3.connect(path)
    db.execute('create table forms(form text)')
    db.executemany('insert into forms values (?)', [('Voda',), ('voda',), ('x-y',)])
    db.commit()
    db.close()
    assert load_corpus(path) == {'voda'}
    assert build(load_corpus(path))['analyses'] == []
    with pytest.raises(sqlite3.OperationalError):
        load_corpus(tmp_path / 'missing.sqlite')
    assert not (tmp_path / 'missing.sqlite').exists()


def test_reproducible_across_hash_seeds_and_input_order():
    code = (
        "import sys,json;sys.path.insert(0,'tools');"
        "from build_composita_grammar import build;"
        "from sapfo_grammar.synth import noun_paradigm;"
        "c=set(noun_paradigm('škár','dáma').values())|{'škár'};"
        "print(json.dumps(build(c),sort_keys=True))"
    )
    outputs = [subprocess.check_output(
        [sys.executable, '-c', code], cwd=ROOT,
        env={**os.environ, 'PYTHONHASHSEED': seed},
    ) for seed in ('1', '17')]
    assert outputs[0] == outputs[1]
    corpus = {'voda', 'vody', 'vode', 'vodu', 'vodou', 'vodách'}
    assert inventory(induce(sorted(corpus), corpus)) == inventory(
        induce(sorted(corpus, reverse=True), corpus))


def test_comparison_detects_changes_and_rejects_different_corpora():
    before = {'forms': {'voda': 'vo·da'}}
    after = {'forms': {'voda': 'voda'}}
    assert compare(before, after) == [{'form': 'voda', 'before': 'vo·da', 'after': 'voda'}]
    with pytest.raises(ValueError, match='same corpus'):
        compare(before, {'forms': {}})


def test_cli_works_without_sapfo_and_does_not_overwrite(tmp_path):
    db_path = tmp_path / 'input.sqlite'
    db = sqlite3.connect(db_path)
    db.execute('create table forms(form text)')
    db.executemany('insert into forms values (?)',
                   [(w,) for w in noun_paradigm('vod', 'žena').values()])
    db.commit()
    db.close()
    out = tmp_path / 'inventory.json'
    command = [sys.executable, str(ROOT / 'tools/build_composita_grammar.py'),
               '--corpus', str(db_path), '--output', str(out)]
    subprocess.run(command, cwd=tmp_path, check=True, capture_output=True)
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['analyses']
    digest = out.read_bytes()
    again = subprocess.run(command, cwd=tmp_path, capture_output=True)
    assert again.returncode != 0
    assert out.read_bytes() == digest
