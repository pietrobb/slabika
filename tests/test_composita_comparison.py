# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Release comparison gates use exact, complete public outputs, never word waivers."""
from __future__ import annotations

import copy
import importlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import compare_composita as comparison  # noqa: E402


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / 'corpus.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('create table forms (form text)')
        db.executemany('insert into forms values (?)', [('lietadlo',), ('ideál',), ('voda',)])
    return path


@pytest.fixture
def baseline(corpus):
    return comparison.snapshot(corpus)


def write_json(tmp_path, name, value):
    path = tmp_path / name
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return path


def changed_snapshot(baseline, mode='all_points'):
    candidate = copy.deepcopy(baseline)
    # Variant-only regression: the preferred string remains unchanged.
    candidate['outputs']['lietadlo'][mode]['break_points'] = [3, 5]
    candidate['outputs']['lietadlo'][mode]['hyphenate'] = 'lie·ta·dlo'
    return candidate


def test_snapshot_captures_all_public_modes_and_provenance(baseline):
    import slabika

    comparison.validate_snapshot(baseline)
    for form, output in baseline['outputs'].items():
        assert output == comparison.public_output(slabika, form)
        assert baseline['forms'][form] == slabika.hyphenate(form)
    assert baseline['outputs']['lietadlo']['all_points']['break_points'] == [3, 5, 6]
    assert baseline['outputs']['ideál']['contextual']['break_points'] == [1, 3]
    assert baseline['corpus_count'] == 3
    assert baseline['corpus_sha256'] == comparison.logical_hash(sorted(baseline['forms']))
    for path in ['src/slabika/typo.py', 'src/slabika/phonology.py',
                 'src/slabika/data/phonology.json', 'src/slabika/__init__.py',
                 'src/slabika/patterns/foreign/hyph-fr.tex', 'pyproject.toml']:
        assert path in baseline['runtime_files']
    assert baseline['inventory_path'] == str((ROOT / comparison.INVENTORY_KEY).resolve())
    assert baseline['comparison_tool_sha256']
    assert baseline['environment']['python'] == sys.version


@pytest.mark.parametrize('head_forms', [None, {}, {'vod': ['voda', 'vody']}])
def test_candidate_head_forms_are_installed_and_restored(corpus, tmp_path, monkeypatch, head_forms):
    engine = importlib.import_module('slabika.syllabify')
    sentinel = object()
    monkeypatch.setattr(engine, '_GENERATED_HEAD_FORMS', sentinel, raising=False)
    data = {'first_members': {}, 'heads': {}, 'input': {'grammar_sha256': {'synth.py': 'abc'}}}
    if head_forms is not None:
        data['head_forms'] = head_forms
    inventory = write_json(tmp_path, 'inventory.json', data)
    expected = None if head_forms is None else {k: frozenset(v) for k, v in head_forms.items()}
    original = comparison.public_output

    def observe(api, form):
        assert engine._GENERATED_HEAD_FORMS == expected
        return original(api, form)

    monkeypatch.setattr(comparison, 'public_output', observe)
    source_before = (ROOT / comparison.INVENTORY_KEY).read_bytes()
    corpus_before = corpus.read_bytes()
    result = comparison.snapshot(corpus, inventory)
    assert engine._GENERATED_HEAD_FORMS is sentinel
    assert result['inventory_metadata']['input'] == data['input']
    assert result['inventory_sha256'] == comparison.digest(inventory.read_bytes())
    assert (ROOT / comparison.INVENTORY_KEY).read_bytes() == source_before
    assert corpus.read_bytes() == corpus_before


def test_schema_two_candidate_cannot_fall_back_to_universal_endings(corpus, tmp_path):
    path = write_json(tmp_path, 'invalid-inventory.json', {
        'schema_version': 2, 'first_members': {}, 'heads': {'vod': 'lemma'},
    })
    with pytest.raises(KeyError, match='head_forms'):
        comparison.snapshot(corpus, path)


def test_candidate_restored_on_api_failure(corpus, monkeypatch):
    engine = importlib.import_module('slabika.syllabify')
    originals = {k: getattr(engine, k, None) for k in (
        '_GENERATED_FIRST_MEMBERS', '_INFERRED_FIRST_MEMBERS', '_GENERATED_HEADS',
        '_GENERATED_HEAD_FORMS')}

    def fail(*args):
        raise ValueError('API failed')

    monkeypatch.setattr(comparison, 'public_output', fail)
    with pytest.raises(ValueError, match='API failed'):
        comparison.snapshot(corpus)
    for key, value in originals.items():
        assert getattr(engine, key, None) is value


def test_runtime_manifest_covers_added_removed_and_non_python_files(tmp_path, monkeypatch):
    monkeypatch.setattr(comparison, 'ROOT', tmp_path)
    package = tmp_path / 'src/slabika'
    package.mkdir(parents=True)
    (tmp_path / 'pyproject.toml').write_text('project', encoding='utf-8')
    resource = package / 'runtime.bin'
    resource.write_bytes(b'one')
    (package / '__pycache__').mkdir()
    (package / '__pycache__/module.pyc').write_bytes(b'ignored')
    before = comparison.runtime_files()
    resource.write_bytes(b'two')
    assert comparison.runtime_files() != before
    resource.unlink()
    assert comparison.runtime_files().keys() != before.keys()
    assert not any('__pycache__' in key for key in before)


def test_legacy_compare_remains_compatible():
    assert comparison.compare({'forms': {'voda': 'vo·da'}}, {'forms': {'voda': 'voda'}}) == [
        {'form': 'voda', 'before': 'vo·da', 'after': 'voda'}]
    with pytest.raises(ValueError, match='same corpus'):
        comparison.compare({'forms': {'voda': 'vo·da'}}, {'forms': {}})


@pytest.mark.parametrize('mode', ['all_points', 'all_contextual'])
def test_full_api_detects_nonpreferred_changes(baseline, mode):
    candidate = changed_snapshot(baseline, mode)
    assert baseline['forms'] == candidate['forms']
    changes = comparison.compare(baseline, candidate)
    assert len(changes) == 1
    assert changes[0] == {'form': 'lietadlo', 'before': baseline['outputs']['lietadlo'],
                          'after': candidate['outputs']['lietadlo']}
    assert not comparison.check_changes(changes, [])['passed']
    assert comparison.check_changes(changes, changes)['passed']
    partial = [{'form': 'lietadlo', 'before': 'lie·ta·dlo', 'after': 'lie·ta·dlo!'}]
    assert not comparison.check_changes(changes, partial)['passed']
    stale = copy.deepcopy(changes)
    stale[0]['after']['preferred']['hyphenate'] = 'different'
    assert not comparison.check_changes(changes, stale)['passed']


def test_contextual_and_divisions_only_changes_are_detected(baseline):
    for field in ['contextual', 'divisions']:
        candidate = copy.deepcopy(baseline)
        if field == 'contextual':
            candidate['outputs']['ideál'][field]['break_points'] = [3]
        else:
            candidate['outputs']['ideál'][field] = []
        assert [x['form'] for x in comparison.compare(baseline, candidate)] == ['ideál']


def test_added_removed_forms_are_explicit_and_require_exact_approval():
    old = {'forms': {'removed': 're·moved', 'stable': 'stable'}}
    new = {'forms': {'added': 'added', 'stable': 'stable'}}
    with pytest.raises(ValueError, match='added_forms.*added.*removed_forms.*removed'):
        comparison.compare(old, new)
    changes = comparison.compare(old, new, allow_corpus_changes=True)
    assert changes == [{'form': 'added', 'before': None, 'after': 'added'},
                       {'form': 'removed', 'before': 're·moved', 'after': None}]
    assert not comparison.check_changes(changes, changes[:1])['passed']
    assert comparison.check_changes(changes, changes)['passed']


@pytest.mark.parametrize('allowlist', [None, {}, ['voda'], [{'form': 'voda'}],
                                     [{'form': 'voda', 'before': None, 'after': None}],
                                     [{'form': 'voda', 'before': 'a', 'after': 'b', 'reason': 'x'}]])
def test_malformed_or_broad_approvals_refused(allowlist):
    with pytest.raises(ValueError, match='allowlist'):
        comparison.check_changes([], allowlist)


def test_duplicate_and_unused_approvals_fail():
    entry = {'form': 'voda', 'before': 'voda', 'after': 'vo·da'}
    with pytest.raises(ValueError, match='duplicate'):
        comparison.check_changes([entry], [entry, entry])
    assert comparison.check_changes([], [entry]) == {
        'passed': False, 'unapproved_changes': [], 'unused_approvals': [entry]}


@pytest.mark.parametrize('field', ['schema_version', 'outputs', 'runtime_files', 'corpus_sha256'])
def test_incomplete_snapshot_rejected(baseline, field):
    del baseline[field]
    with pytest.raises(ValueError):
        comparison.validate_snapshot(baseline)


def test_duplicate_json_keys_rejected(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{"forms": {}, "forms": {"voda": "voda"}}', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate JSON key'):
        comparison.load_json(path)


def run_main(tmp_path, monkeypatch, baseline, candidate, *flags):
    source = write_json(tmp_path, 'baseline.json', baseline)
    output = tmp_path / 'output.json'
    monkeypatch.setattr(comparison, 'snapshot', lambda *args: candidate)
    code = comparison.main(['--baseline', str(source), '--output', str(output), *flags])
    return code, json.loads(output.read_text(encoding='utf-8'))


def test_check_exit_status_and_exact_allowlist(tmp_path, monkeypatch, baseline):
    candidate = changed_snapshot(baseline)
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate, '--check')
    assert code == 1
    assert result['check']['unapproved_changes'] == result['changes']
    (tmp_path / 'output.json').unlink()
    allowlist = write_json(tmp_path, 'approved.json', result['changes'])
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate,
                            '--check', '--allowlist', str(allowlist))
    assert code == 0
    assert result['check']['passed']
    assert result['allowlist_sha256'] == comparison.digest(allowlist.read_bytes())


@pytest.mark.parametrize('path', ['src/slabika/typo.py', 'src/slabika/data/phonology.json',
                                 'src/slabika/new_engine.py', 'src/slabika/phonology.py'])
def test_runtime_changes_require_opt_in(tmp_path, monkeypatch, baseline, path):
    candidate = copy.deepcopy(baseline)
    if path.endswith('/phonology.py'):
        del candidate['runtime_files'][path]
    else:
        candidate['runtime_files'][path] = 'a' * 64
    candidate['runtime_sha256'] = comparison.logical_hash(
        comparison.engine_files(candidate['runtime_files']))
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate, '--check')
    assert code == 2 and not result['check']['passed']
    assert result['runtime_changes'][0]['path'] == path
    (tmp_path / 'output.json').unlink()
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate,
                            '--check', '--allow-engine-changes')
    assert code == 0 and result['check']['passed']


def test_engine_opt_in_does_not_approve_output_changes(tmp_path, monkeypatch, baseline):
    candidate = changed_snapshot(baseline)
    candidate['runtime_files']['src/slabika/typo.py'] = 'a' * 64
    candidate['runtime_sha256'] = comparison.logical_hash(
        comparison.engine_files(candidate['runtime_files']))
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate,
                            '--check', '--allow-engine-changes')
    assert code == 1 and not result['check']['passed']


def test_corpus_mismatch_report_persisted_and_opt_in_not_approval(tmp_path, monkeypatch, baseline):
    candidate = copy.deepcopy(baseline)
    del candidate['forms']['voda']
    del candidate['outputs']['voda']
    candidate['corpus_count'] -= 1
    candidate['corpus_sha256'] = comparison.logical_hash(sorted(candidate['forms']))
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate, '--check')
    assert code == 2
    assert result['removed_forms'] == ['voda'] and result['added_forms'] == []
    assert result['changes'][0]['after'] is None
    (tmp_path / 'output.json').unlink()
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate,
                            '--check', '--allow-corpus-changes')
    assert code == 1 and not result['check']['passed']
    (tmp_path / 'output.json').unlink()
    allowlist = write_json(tmp_path, 'approved.json', result['changes'])
    code, result = run_main(tmp_path, monkeypatch, baseline, candidate,
                            '--check', '--allow-corpus-changes', '--allowlist', str(allowlist))
    assert code == 0 and result['check']['passed']


@pytest.mark.parametrize('flags', [['--check'], ['--allow-engine-changes'], ['--allow-corpus-changes'],
                                  ['--allowlist', 'approvals.json']])
def test_check_requires_baseline(tmp_path, flags):
    with pytest.raises(SystemExit) as exc:
        comparison.main(['--output', str(tmp_path / 'out.json'), *flags])
    assert exc.value.code == 2
    assert not (tmp_path / 'out.json').exists()


def test_cli_fresh_process_no_changes_and_no_overwrite(corpus, tmp_path):
    baseline = tmp_path / 'before.json'
    candidate = tmp_path / 'after.json'
    cmd = [sys.executable, str(ROOT / 'tools/compare_composita.py'), '--corpus', str(corpus)]
    corpus_before = corpus.read_bytes()
    first = subprocess.run([*cmd, '--output', str(baseline)], cwd=tmp_path,
                           capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    second = subprocess.run([*cmd, '--baseline', str(baseline), '--output', str(candidate), '--check'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert second.returncode == 0, second.stderr
    result = json.loads(candidate.read_text(encoding='utf-8'))
    assert result['changes'] == [] and result['check']['passed']
    saved = candidate.read_bytes()
    again = subprocess.run([*cmd, '--output', str(candidate)], cwd=tmp_path,
                           capture_output=True, text=True)
    assert again.returncode == 2 and 'already exists' in again.stderr
    assert candidate.read_bytes() == saved
    assert corpus.read_bytes() == corpus_before


@pytest.mark.parametrize('rows', [[], [('voda',), ('voda',)], [(None,)], [('',)]])
def test_invalid_corpus_fails_closed(corpus, rows):
    with sqlite3.connect(corpus) as db:
        db.execute('delete from forms')
        db.executemany('insert into forms values (?)', rows)
    with pytest.raises(ValueError, match='unique nonempty'):
        comparison.snapshot(corpus)
