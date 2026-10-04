# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Export explicit review language labels, never reviewed break points."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from slabika.language import _language_key, normalize_language  # noqa: E402
from slabika.review import packed  # noqa: E402


def export_word_languages(database: Path, output: Path) -> dict[str, str]:
    labels = {}
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as con:
        rows = con.execute(
            "SELECT form, language FROM decisions "
            "WHERE language IS NOT NULL AND COALESCE(is_deleted, 0) = 0 ORDER BY form"
        )
        for form, language in rows:
            key = _language_key(form)
            selected = normalize_language(language)
            if key in labels and labels[key] != selected:
                raise ValueError(f"Conflicting language labels for {form!r}")
            labels[key] = selected
    labels = dict(sorted(labels.items()))
    output.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return labels


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=ROOT / "tests/data/review_decisions.sqlite")
    parser.add_argument("--output", type=Path, default=ROOT / "src/slabika/data/word_languages.json")
    args = parser.parse_args()
    packed.ensure_unpacked(args.database)
    labels = export_word_languages(args.database, args.output)
    print(f"Exported {len(labels)} language labels to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
