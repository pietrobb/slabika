# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Materialize exact comparison approvals from separately authored PSP decisions.

Only the specified breakpoint transition is approved, in every public API mode.
The comparison gate still rejects every unlisted or unexpectedly changed output.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from compare_composita import MODES, load_json, validate_snapshot


def render(form: str, points: list[int]) -> str:
    cuts = [0, *points, len(form)]
    return "·".join(form[a:b] for a, b in zip(cuts, cuts[1:]))


def reviewed_changes(changes: list[dict], review: dict) -> tuple[list, list]:
    if (
        review.get("schema_version") != 1
        or not review.get("reviewer")
        or not review.get("authority")
    ):
        raise ValueError("review needs a version, reviewer and authority")
    decisions = {}
    for group in review["groups"]:
        if not group.get("reason"):
            raise ValueError("each review group needs a reason")
        for form in group["forms"]:
            if form in decisions:
                raise ValueError(f"duplicate review for {form}")
            for key in ("remove", "add", "contextual_remove"):
                points = group.get(key, group["remove"])
                if any(
                    type(p) is not int or not 0 < p < len(form) for p in points
                ) or points != sorted(set(points)):
                    raise ValueError(f"invalid {key} breakpoints for {form}")
            if (set(group["remove"]) | set(group.get("contextual_remove", []))) & set(group["add"]):
                raise ValueError("removed and added breakpoints must be disjoint")
            decisions[form] = group
    approvals, pending = [], []
    for change in changes:
        form = change["form"]
        group = decisions.get(form)
        if group is None:
            pending.append({"form": form, "reason": "not reviewed"})
            continue
        expected = copy.deepcopy(change["before"])
        if expected is None or change["after"] is None:
            pending.append(
                {"form": form, "reason": "corpus addition/removal is not a breakpoint approval"}
            )
            continue
        valid = True
        for mode in MODES:
            if group.get("preserve_contextual") and mode in {"contextual", "all_contextual"}:
                continue
            before = set(expected[mode]["break_points"])
            removed, added = (
                set(
                    group.get("contextual_remove", group["remove"])
                    if mode in {"contextual", "all_contextual"}
                    else group["remove"]
                ),
                set(group["add"]),
            )
            valid &= removed <= before and not before & added
            points = sorted(before - removed | added)
            expected[mode] = {"break_points": points, "hyphenate": render(form, points)}
        expected["divisions"] = [
            form[:p] + "-" + form[p:] for p in expected["preferred"]["break_points"]
        ]
        if valid and expected == change["after"]:
            approvals.append(change)
        else:
            pending.append(
                {"form": form, "reason": "full API transition differs from the reviewed decision"}
            )
    return approvals, pending


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.report, args.reviews, args.allowlist, args.audit_output]
    if len({p.resolve() for p in paths}) != len(paths):
        parser.error("inputs and outputs must be distinct")
    if args.allowlist.exists() or args.audit_output.exists():
        parser.error("outputs already exist; choose new paths")
    report, report_hash = load_json(args.report)
    review, review_hash = load_json(args.reviews)
    validate_snapshot(report)
    approvals, pending = reviewed_changes(report["changes"], review)
    raw = (json.dumps(approvals, ensure_ascii=False, sort_keys=True) + "\n").encode("utf8")
    audit = {
        "report_sha256": report_hash,
        "reviews_sha256": review_hash,
        "allowlist_sha256": hashlib.sha256(raw).hexdigest(),
        "approved": len(approvals),
        "pending": pending,
        "reviewer": review["reviewer"],
    }
    args.allowlist.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    with args.allowlist.open("xb") as out:
        out.write(raw)
    with args.audit_output.open("x", encoding="utf8") as out:
        json.dump(audit, out, ensure_ascii=False, indent=2)
    print(f"reviewed approvals {len(approvals)}; pending {len(pending)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
