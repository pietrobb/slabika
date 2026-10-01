# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""File a finished dual-model division run into the review database.

The rules text, prompt and schema are taken from the run's own transcript and
checked against every batch hash; the version labels name them in the database.
Runs that recorded their engine build use it; older runs need --engine-note
explaining why the current engine build may stand in for the one compared.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from slabika.review.ai_runs import engine_version, import_run  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--rules-version", required=True)
    parser.add_argument("--rules-source", required=True)
    parser.add_argument("--rules-note", default="")
    parser.add_argument("--prompt-version", required=True)
    parser.add_argument("--prompt-source", required=True)
    parser.add_argument("--prompt-note", default="")
    parser.add_argument("--schema-version", required=True)
    parser.add_argument("--schema-note", default="")
    parser.add_argument("--engine-note", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--db", type=Path, default=ROOT / "tests/data/review_decisions.sqlite")
    args = parser.parse_args()
    summary = json.loads((args.run_dir / "summary.json").read_text(encoding="utf-8"))
    engine = summary.get("engine")
    if engine is None:
        if not args.engine_note:
            parser.error("run did not record its engine build; --engine-note is required")
        engine = engine_version(ROOT)
    engine = dict(engine, note=args.engine_note or engine.get("note", ""))
    result = import_run(
        args.db, args.run_dir, run_id=args.run_id, engine=engine,
        rules_version=args.rules_version, rules_source=args.rules_source,
        rules_note=args.rules_note, prompt_version=args.prompt_version,
        prompt_source=args.prompt_source, prompt_note=args.prompt_note,
        schema_version=args.schema_version, schema_note=args.schema_note, note=args.note)
    print(json.dumps(result | {"engine": engine}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
