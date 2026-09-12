# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Snapshot/compare production divisions without modifying either review database."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

from slabika import break_points

ROOT = Path(__file__).resolve().parents[1]
INPUTS = [ROOT / "tests/data" / name for name in (
    "translatemaster_hyphenation_working.sqlite", "review_decisions.sqlite"
)]


def read_inputs():
    with sqlite3.connect(INPUTS[0].as_uri() + "?mode=ro", uri=True) as db:
        inventory = {row[0] for row in db.execute("SELECT form FROM forms")}
    with sqlite3.connect(INPUTS[1].as_uri() + "?mode=ro", uri=True) as db:
        human = dict(db.execute(
            "SELECT form, expected_hyphenation FROM decisions "
            "WHERE COALESCE(is_deleted, 0) = 0 AND COALESCE(action, '') != 'invalid' "
            "AND COALESCE(row_action, '') != 'invalid'"
        ))
    return inventory, human


def render(word, points):
    return "".join(("·" if i in points else "") + c for i, c in enumerate(word))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    inventory, human = read_inputs()
    modes = ((False, False), (True, False), (False, True), (True, True))
    rows = {w: [break_points(w, a, c) for a, c in modes] for w in sorted(inventory | human.keys())}
    report = {"input_hashes": before, "inventory_count": len(inventory),
              "scanned": len(rows), "modes": modes, "rows": rows}
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        assert before == baseline["input_hashes"], "Inputs differ from baseline"
        assert rows.keys() == baseline["rows"].keys(), "Vocabulary differs from baseline"
        changes = []
        for word, points in rows.items():
            old = baseline["rows"][word]
            if old == points:
                continue
            wanted = human.get(word)
            changes.append({"form": word, "old": render(word, old[0]),
                            "new": render(word, points[0]), "human": wanted,
                            "old_points": old, "new_points": points,
                            "gained_human": bool(wanted and render(word, points[0]).lower()
                                                 == wanted.lower() != render(word, old[0]).lower()),
                            "lost_human": bool(wanted and render(word, old[0]).lower()
                                                == wanted.lower() != render(word, points[0]).lower())})
        report.pop("rows")
        report.update(changes=changes, changed=len(changes),
                      gained_human=sum(r["gained_human"] for r in changes),
                      lost_human=sum(r["lost_human"] for r in changes),
                      metric_note="Human agreement is diagnostic, not PSP adjudication")
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    assert before == after, "Input database changed"
    report["inputs_unchanged"] = True
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "changes")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
