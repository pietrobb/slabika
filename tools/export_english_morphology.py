# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Export corpus membership for routing/morphology, never IPA or human decisions."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(inventory, output):
    db = sqlite3.connect(Path(inventory).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        words = {r[0] for r in db.execute(
            "SELECT form FROM foreign_evidence WHERE language='en' "
            "AND pronunciation_status='generated'"
        )}
    finally:
        db.close()
    payload = {
        "description": "Corpus membership for experimental English routing/morphology; no gold breaks.",
        "source": "English foreign review generated-form inventory",
        "source_forms": len(words),
        "source_forms_sha256": hashlib.sha256("\n".join(sorted(words)).encode()).hexdigest(),
        "members": sorted(words),
    }
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    return len(words)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path,
                        default=ROOT / "tests/data/foreign_review/en.sqlite")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "src/slabika/data/english_morphology_members.json")
    args = parser.parse_args()
    print(f"Exported {export(args.inventory, args.output)} corpus members")
