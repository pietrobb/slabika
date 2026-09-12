# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Export full DE/FR type corpora and audit native-pattern PSP adaptations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from time import perf_counter

import build_french_profile as french
import build_german_profile as german
from slabika import adapt_foreign_word

ROOT = Path(__file__).resolve().parents[1]


def evaluate(output: Path, translate_master: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        "method": "Full loaded DE/FR unique types, explicit language, no G2P, no held-out filter",
        "warning": "Coverage and change counts are not PSP accuracy. Source-language labels may "
        "include foreign quotations, names and OCR. Local rules do not resolve all "
        "morpheme ambiguities. Full corpora must not be used as held-out router tests.",
        "languages": {},
    }
    profile = json.loads(
        (ROOT / "src/slabika/data/language_router_profile.json").read_text(encoding="utf-8")
    )
    for language, loader in (
        ("german", german.load_german_types),
        ("french", french.load_french_types),
    ):
        words, sources = loader(translate_master)
        counts = Counter()
        rules = Counter()
        digest = hashlib.sha256()
        started = perf_counter()
        with (output / f"{language}.tsv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t")
            writer.writerow(
                (
                    "word",
                    "language",
                    "native_division",
                    "adapted_division",
                    "native_points",
                    "adapted_points",
                    "changes",
                )
            )
            for word in sorted(words):
                result = adapt_foreign_word(word, language)
                native = "".join(
                    ("·" if i in result.native_points else "") + c for i, c in enumerate(word)
                )
                adapted = result.render()
                assert adapted.replace("·", "") == word
                assert result.points == tuple(sorted(set(result.points)))
                assert all(2 <= p <= len(word) - 2 for p in result.points)
                counts["types"] += 1
                counts["native_with_breaks"] += bool(result.native_points)
                counts["adapted_with_breaks"] += bool(result.points)
                counts["changed_words"] += result.points != result.native_points
                counts["added_points"] += len(set(result.points) - set(result.native_points))
                counts["removed_points"] += len(set(result.native_points) - set(result.points))
                rules.update(change.rule for change in result.changes)
                digest.update((word + "\n").encode("utf-8"))
                writer.writerow(
                    (
                        word,
                        language,
                        native,
                        adapted,
                        ",".join(map(str, result.native_points)),
                        ",".join(map(str, result.points)),
                        json.dumps([vars(c) for c in result.changes], ensure_ascii=False),
                    )
                )
        summary["languages"][language] = {
            **counts,
            "rule_applications": dict(rules),
            "source_metadata": sources,
            "accepted_occurrences": sum(s["accepted_tokens"] for s in sources),
            "types_sha256": digest.hexdigest(),
            "seconds_including_first_pattern_load": perf_counter() - started,
            "router_partitions": {
                split: counts_by_language[language]
                for split, counts_by_language in profile["training"]["partitions"].items()
            },
        }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "scratch/foreign-adapter-full")
    parser.add_argument("--translate-master", type=Path, default=german.DEFAULT_TRANSLATE_MASTER)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.output, args.translate_master), ensure_ascii=False, indent=2))
