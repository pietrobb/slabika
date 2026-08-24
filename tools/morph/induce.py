# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Induce the morph lexicon from the corpus by minimum description length.

Build-time tool. Reads the working corpus and writes src/slabika/data/morphs.json,
which is the only morphological data the package ships: a list of morphs with
the number of times the corpus needs each one. Nothing in it is written by hand
and nothing in it comes from a foreign dictionary, so the result carries the
licence of our own corpus.

Why description length and not a rule: every local test for a morpheme boundary
can be satisfied by accident, because in 179 000 forms every short string is the
beginning of something. Description length cannot be satisfied by accident. The
model pays for each morph it keeps and for each morph it emits, so a boundary is
drawn only where the pieces earn back what they cost across the whole corpus.
po|uc|ka is drawn because po-, uc- and -ka are each reused thousands of times;
no cut inside Bordurom pays for itself, so none is drawn.

Morfessor Baseline (Creutz & Lagus, 2002; 2007) with greedy split search. The
segmentation is a shared graph -- a node is a string, its count is how many
words reach it, and restructuring a node moves that count through the graph.

Usage:
    python tools/morph/induce.py [--alpha 2.0] [--epochs 4] [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests/data/translatemaster_hyphenation_working.sqlite"
DEFAULT_OUT = ROOT / "src/slabika/data/morphs.json"


class Model:
    """A lexicon of morphs and the segmentation graph over the corpus."""

    def __init__(self, alphabet: int, alpha: float) -> None:
        self.log_a = math.log(alphabet + 1)
        self.alpha = alpha
        self.count: Counter[str] = Counter()   # node -> how many words reach it
        self.children: dict[str, tuple[str, str]] = {}
        self.tcount: Counter[str] = Counter()  # morph -> tokens emitted
        self.tokens = 0
        self.sum_n_log_n = 0.0
        self.lex_cost = 0.0

    # -- description length ---------------------------------------------
    def _touch(self, morph: str, delta: int) -> None:
        """Move *delta* tokens of a morph, keeping both costs current."""
        n = self.tcount[morph]
        if n:
            self.sum_n_log_n -= n * math.log(n)
        else:
            self.lex_cost += (len(morph) + 1) * self.log_a
        n += delta
        if n > 0:
            self.sum_n_log_n += n * math.log(n)
            self.tcount[morph] = n
        else:
            self.lex_cost -= (len(morph) + 1) * self.log_a
            del self.tcount[morph]
        self.tokens += delta

    def cost(self) -> float:
        if not self.tokens:
            return self.lex_cost
        corpus = self.tokens * math.log(self.tokens) - self.sum_n_log_n
        return self.lex_cost + self.alpha * corpus

    # -- segmentation graph ----------------------------------------------
    def inc(self, node: str, delta: int) -> None:
        new = self.count[node] + delta
        if new:
            self.count[node] = new
        else:
            del self.count[node]
        kids = self.children.get(node)
        if kids is None:
            self._touch(node, delta)
        else:
            if not new:
                del self.children[node]
            self.inc(kids[0], delta)
            self.inc(kids[1], delta)

    def do_split(self, node: str, cut: tuple[str, str]) -> None:
        c = self.count[node]
        self._touch(node, -c)
        self.children[node] = cut
        self.inc(cut[0], c)
        self.inc(cut[1], c)

    def undo_split(self, node: str) -> None:
        c = self.count[node]
        left, right = self.children.pop(node)
        self.inc(left, -c)
        self.inc(right, -c)
        self._touch(node, c)

    # -- search ------------------------------------------------------------
    def optimize(self, node: str, depth: int = 0) -> None:
        """Re-decide the cheapest binary split of *node*, then recurse into it."""
        if node in self.children:
            self.undo_split(node)
        if len(node) < 2 or depth > 8:
            return
        best_cost, best_cut = self.cost(), None
        for i in range(1, len(node)):
            cut = (node[:i], node[i:])
            self.do_split(node, cut)
            c = self.cost()
            self.undo_split(node)
            if c < best_cost:
                best_cost, best_cut = c, cut
        if best_cut is None:
            return
        self.do_split(node, best_cut)
        for part in best_cut:
            self.optimize(part, depth + 1)


def load_corpus() -> list[str]:
    con = sqlite3.connect(CORPUS)
    return sorted({r[0].lower() for r in con.execute("SELECT form FROM forms") if r[0]})


def train(words: list[str], alpha: float, epochs: int, seed: int = 0) -> Model:
    alphabet = len({ch for w in words for ch in w})
    model = Model(alphabet, alpha)
    for w in words:
        model.inc(w, 1)
    order = list(words)
    rng = random.Random(seed)
    for epoch in range(epochs):
        rng.shuffle(order)
        started = time.time()
        for w in order:
            model.optimize(w)
        print(
            f"epoch {epoch}: cost {model.cost():,.0f}  morphs {len(model.tcount):,}"
            f"  {time.time() - started:.0f}s",
            flush=True,
        )
    return model


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--alpha", type=float, default=2.0)
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    words = load_corpus()
    print(f"{len(words):,} forms", flush=True)
    model = train(words, args.alpha, args.epochs)

    payload = {
        "note": "Induced from the project corpus by tools/morph/induce.py. "
                "No hand-written entries, no foreign dictionary.",
        "alpha": args.alpha,
        "epochs": args.epochs,
        "forms": len(words),
        "tokens": model.tokens,
        "morphs": dict(sorted(model.tcount.items(), key=lambda kv: (-kv[1], kv[0]))),
    }
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(f"wrote {len(model.tcount):,} morphs -> {args.out}")


if __name__ == "__main__":
    main()
