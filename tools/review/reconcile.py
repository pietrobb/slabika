# SPDX-FileCopyrightText: 2026 slabika contributors
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Reconcile manual review decisions, blind audit decisions and engine output.

Read-only: never writes to the review or audit databases. Produces a JSON
report describing where the three sources agree and where they diverge.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from slabika import hyphenate  # noqa: E402

MARK = "\u00b7"


def _variants(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {v.replace("|", MARK).lower() for v in json.loads(raw)}


def load_manual(path: Path) -> dict[str, dict]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    out = {}
    query = """
        SELECT form, action, hyphenation_action, expected_hyphenation,
               is_foreign_word, is_proper_name, is_abbreviation, is_deleted,
               engine_hyphenation
        FROM decisions
    """
    for row in con.execute(query):
        form, action, hyph_action, expected, foreign, proper, abbrev, deleted, prior = row
        if deleted:
            continue
        out[form] = {
            "action": hyph_action or action,
            "expected": expected.lower() if expected else None,
            "prior": prior.lower() if prior else None,
            "foreign": bool(foreign),
            "proper": bool(proper),
            "abbrev": bool(abbrev),
        }
    con.close()
    return out


def load_blind(path: Path) -> dict[str, dict]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    out = {}
    query = """
        SELECT form, assessment, expected_variants_json, confidence, reason, batch_id
        FROM decisions
    """
    for form, assessment, variants, confidence, reason, batch in con.execute(query):
        out[form] = {
            "assessment": assessment,
            "variants": _variants(variants),
            "confidence": confidence,
            "reason": reason,
            "batch": batch,
        }
    con.close()
    return out


def load_psp_adjudication(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for group in payload["groups"]:
        for form in group["forms"]:
            if form in out:
                raise ValueError(f"duplicate PSP adjudication for {form!r}")
            out[form] = {
                "status": group["status"],
                "rule": group["rule"],
                "reason": group["reason"],
            }
    return out


def reconcile(manual: dict[str, dict], blind: dict[str, dict]) -> dict:
    engine_cache: dict[str, str] = {}

    def engine(form: str) -> str:
        if form not in engine_cache:
            engine_cache[form] = hyphenate(form).lower()
        return engine_cache[form]

    def manual_match_mode(form: str, target: str | None) -> str | None:
        if target is None:
            return None
        candidates = (
            ("preferred", engine(form)),
            ("permissive", hyphenate(form, all_points=True).lower()),
            ("contextual", hyphenate(form, contextual=True).lower()),
            (
                "permissive_contextual",
                hyphenate(form, all_points=True, contextual=True).lower(),
            ),
        )
        return next((mode for mode, output in candidates if output == target), None)

    buckets: dict[str, list] = {
        "blind_vs_engine_conflict": [],
        "manual_correction_open": [],
        "manual_confirm_regression": [],
        "manual_vs_blind_conflict": [],
        "manual_and_blind_agree_against_engine": [],
        "blind_uncertain": [],
        "blind_invalid": [],
    }
    stats = Counter()

    for form, info in sorted(blind.items()):
        eng = engine(form)
        if info["assessment"] == "uncertain":
            stats["blind_uncertain"] += 1
            buckets["blind_uncertain"].append(
                {"form": form, "engine": eng, "reason": info["reason"], "batch": info["batch"]}
            )
            continue
        if info["assessment"] == "invalid":
            stats["blind_invalid"] += 1
            buckets["blind_invalid"].append(
                {"form": form, "engine": eng, "reason": info["reason"], "batch": info["batch"]}
            )
            continue
        stats["blind_resolved"] += 1
        if eng in info["variants"]:
            stats["blind_agrees_engine"] += 1
        else:
            stats["blind_conflicts_engine"] += 1
            buckets["blind_vs_engine_conflict"].append(
                {
                    "form": form,
                    "engine": eng,
                    "blind": sorted(info["variants"]),
                    "confidence": info["confidence"],
                    "reason": info["reason"],
                    "batch": info["batch"],
                }
            )

    for form, info in sorted(manual.items()):
        eng = engine(form)
        action = info["action"]
        if action == "correct" and info["expected"]:
            stats["manual_correct"] += 1
            match_mode = manual_match_mode(form, info["expected"])
            if match_mode is None:
                stats["manual_correction_open"] += 1
                buckets["manual_correction_open"].append(
                    {"form": form, "engine": eng, "manual": info["expected"]}
                )
            else:
                stats[f"manual_matches_{match_mode}"] += 1
        elif action == "confirm":
            stats["manual_confirm"] += 1
            target = info["expected"] or info["prior"]
            match_mode = manual_match_mode(form, target)
            if target and match_mode is None:
                stats["manual_confirm_regression"] += 1
                buckets["manual_confirm_regression"].append(
                    {"form": form, "engine": eng, "manual": target}
                )
            elif match_mode is not None:
                stats[f"manual_matches_{match_mode}"] += 1

    overlap = sorted(set(manual) & set(blind))
    stats["overlap"] = len(overlap)
    for form in overlap:
        m, b = manual[form], blind[form]
        eng = engine(form)
        if b["assessment"] != "resolved":
            continue
        manual_target = (
            m["expected"]
            if m["action"] == "correct" and m["expected"]
            else m["expected"] or m["prior"] or eng
        )
        if manual_target in b["variants"]:
            stats["overlap_agree"] += 1
            if manual_match_mode(form, manual_target) is None:
                buckets["manual_and_blind_agree_against_engine"].append(
                    {"form": form, "engine": eng, "consensus": manual_target}
                )
        else:
            stats["overlap_conflict"] += 1
            buckets["manual_vs_blind_conflict"].append(
                {
                    "form": form,
                    "engine": eng,
                    "manual": manual_target,
                    "manual_action": m["action"],
                    "blind": sorted(b["variants"]),
                    "confidence": b["confidence"],
                    "reason": b["reason"],
                }
            )

    return {"stats": dict(stats), "buckets": buckets}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--review-db", default="tests/data/review_decisions.sqlite", type=Path
    )
    parser.add_argument(
        "--run-dir", default="tests/data/blind_word_division_5000_v1", type=Path
    )
    parser.add_argument(
        "--psp-adjudication",
        default="tests/data/manual_psp_adjudication.json",
        type=Path,
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    manual = load_manual(args.review_db)
    blind = load_blind(args.run_dir / "results.sqlite")
    result = reconcile(manual, blind)
    psp = load_psp_adjudication(args.psp_adjudication)
    current_manual_conflicts = {
        item["form"]
        for bucket in ("manual_correction_open", "manual_confirm_regression")
        for item in result["buckets"][bucket]
    }
    result["psp_adjudication"] = {
        "status_counts": dict(Counter(item["status"] for item in psp.values())),
        "current_manual_conflicts": len(current_manual_conflicts),
        "classified_current": len(current_manual_conflicts & psp.keys()),
        "unclassified_current": sorted(current_manual_conflicts - psp.keys()),
        "no_longer_conflicting": sorted(psp.keys() - current_manual_conflicts),
    }
    result["sources"] = {
        "review_db": str(args.review_db),
        "run_dir": str(args.run_dir),
        "psp_adjudication": str(args.psp_adjudication),
        "manual_forms": len(manual),
        "blind_forms": len(blind),
    }

    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    summary = {
        "sources": result["sources"],
        "stats": result["stats"],
        "bucket_sizes": {k: len(v) for k, v in result["buckets"].items()},
        "psp_adjudication": result["psp_adjudication"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
