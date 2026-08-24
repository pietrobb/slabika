# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Zmeria dopad zmeny enginu na celý pracovný korpus."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_engine = ROOT / "src"
if "--engine" in sys.argv:
    _engine = Path(sys.argv[sys.argv.index("--engine") + 1]).resolve()
sys.path.insert(0, str(_engine))
sys.stdout.reconfigure(encoding="utf-8")

from slabika import hyphenate  # noqa: E402

con = sqlite3.connect(ROOT / "tests/data/translatemaster_hyphenation_working.sqlite")
forms = [r[0] for r in con.execute("select form from forms") if r[0].islower()]

out = {w: hyphenate(w) for w in forms}
target = Path(sys.argv[1])
if target.exists() and "--write" not in sys.argv:
    before = dict(
        line.split("\t", 1) for line in target.read_text(encoding="utf-8").splitlines()
    )
    changed = [(w, before[w].strip(), out[w]) for w in out if before.get(w, "").strip() != out[w]]
    print(f"zmenených tvarov: {len(changed)} / {len(out)}")
    for w, b, a in changed[:60]:
        print(f"  {w}\n    pred: {b}\n    po:   {a}")
else:
    target.write_text(
        "".join(f"{w}\t{h}\n" for w, h in out.items()), encoding="utf-8"
    )
    print(f"zapísaná snímka: {len(out)} tvarov -> {target}")
