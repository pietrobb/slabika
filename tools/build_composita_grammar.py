# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build compound candidates from local grammar and corpus, without a lexicon.

python tools/build_composita_grammar.py --sample 15000 --output scratch/grammar.json
Omit --sample for all forms. Add --runtime-output for a compact runtime candidate.
Neither path may overwrite the production artifact or the input corpus.
The standard corpus includes the separately attributed grammar_supplement.json;
custom corpora use only their own forms unless --supplement is explicitly given.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path

from sapfo_grammar.induction import induce, inventory
from sapfo_grammar.supplement import load_supplement, supplement_inventory

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'tests/data/translatemaster_hyphenation_working.sqlite'
SUPPLEMENT = ROOT / 'tests/data/grammar_supplement.json'
PRODUCTION = ROOT / 'src/slabika/data/composita.json'


def load_corpus(path: Path) -> set[str]:
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        return {word.lower() for (word,) in db.execute('select form from forms')
                if word.isalpha()}
    finally:
        db.close()


def corpus_hash(corpus: set[str]) -> str:
    """Hash exactly the sorted, lowercase surface-form input of this builder."""
    return hashlib.sha256(('\n'.join(sorted(corpus)) + '\n').encode()).hexdigest()


def source_hashes():
    return {
        'grammar_sha256': {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / 'tools/sapfo_grammar').glob('*.py'))
        },
        'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


LOADED_SOURCES = source_hashes()


def build(corpus: set[str], sample: int = 0, supplement: dict | None = None) -> dict:
    if source_hashes() != LOADED_SOURCES:
        raise RuntimeError('grammar or builder changed; restart in a fresh process')
    supplement = supplement or {}
    combined = corpus | set(supplement.get('surface_forms', []))
    ordered = sorted(combined)
    step = max(1, len(ordered) // sample) if sample else 1
    candidates = ordered[::step][:sample] if sample else ordered
    result = supplement_inventory(inventory(induce(candidates, combined)), supplement, corpus)
    if source_hashes() != LOADED_SOURCES:
        raise RuntimeError('grammar or builder changed during generation; result rejected')
    result['input'] = {
        'corpus_forms': len(combined), 'candidates': len(candidates),
        'surface_forms_sha256': corpus_hash(combined),
        'original_corpus_forms': len(corpus), 'original_corpus_sha256': corpus_hash(corpus),
        'authored_additions': sorted(combined - corpus),
        'supplement_sha256': supplement.get('sha256'),
        'supplement_source': supplement.get('source'),
        'sample_size': sample, 'min_support': 3,
        **LOADED_SOURCES,
    }
    return result


def runtime_inventory(audit: dict) -> dict:
    """Keep runtime rules and provenance, not full lexical evidence in the wheel."""
    return {key: audit[key] for key in (
        'note', 'schema_version', 'first_members', 'heads', 'head_paradigms', 'input',
    )}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=CORPUS)
    parser.add_argument('--supplement', type=Path)
    parser.add_argument('--sample', type=int, default=0)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime-output', type=Path)
    args = parser.parse_args()
    if args.sample < 0:
        parser.error('--sample must be non-negative')
    supplement_path = args.supplement or (SUPPLEMENT if args.corpus.resolve() == CORPUS.resolve() else None)
    supplement = load_supplement(supplement_path) if supplement_path else None
    paths = [args.output] + ([args.runtime_output] if args.runtime_output else [])
    if len({p.resolve() for p in paths}) != len(paths):
        parser.error('audit and runtime outputs must be different paths')
    protected = {PRODUCTION.resolve(), args.corpus.resolve()}
    if supplement_path:
        protected.add(supplement_path.resolve())
    for path in paths:
        if path.resolve() in protected:
            parser.error('output must not overwrite production data or an input')
        if path.exists():
            parser.error('output already exists; choose a new path')
    start = time.monotonic()
    result = build(load_corpus(args.corpus), args.sample, supplement)
    if supplement_path and load_supplement(supplement_path) != supplement:
        raise RuntimeError('supplement changed during generation; result rejected')
    for path, data in zip(paths, (result, runtime_inventory(result))):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as out:
            json.dump(data, out, ensure_ascii=False, sort_keys=True)
    print(json.dumps({
        'candidates': result['input']['candidates'],
        'lexemes': len(result['analyses']),
        'pos': dict(Counter(r['pos'] for r in result['analyses'])),
        'first_members': len(result['first_members']), 'heads': len(result['heads']),
        'authored_additions': len(result['input']['authored_additions']),
        'seconds': round(time.monotonic() - start, 1), 'output': str(args.output),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
