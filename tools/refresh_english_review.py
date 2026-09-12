# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Reproject stored English pronunciations; dry-run by default, no G2P or human writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from build_foreign_review import validate_schema, verify_inventory
from slabika.english_projection import VERSION, EnglishMorphology
from evaluate_foreign_corpora import divided, project_psp_points

ROOT = Path(__file__).resolve().parents[1]


def source_rows(db):
    cursor = db.execute("SELECT form, spans_json, pronunciation_status, proposed_hyphenation, "
                        "proposal_status, proposal_source FROM foreign_evidence ORDER BY form")
    names = [c[0] for c in cursor.description]
    return [dict(zip(names, row)) for row in cursor]


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def plan(db):
    validate_schema(db, "en")
    rows = source_rows(db)
    pronunciations = {
        row["form"]: SimpleNamespace(word=row["form"], language="english",
                                     spans=json.loads(row["spans_json"]))
        for row in rows if row["pronunciation_status"] == "generated"
    }
    morphology = EnglishMorphology(pronunciations.values())
    changes, updates = [], []
    for row in rows:
        word = row["form"]
        if word not in pronunciations:
            continue
        pronunciation = pronunciations[word]
        points, complete = project_psp_points(pronunciation)
        refined = morphology.refine(pronunciation, points) if complete else points
        proposal = divided(word, refined)
        status = "experimental" if complete else "incomplete"
        if proposal != row["proposed_hyphenation"] or status != row["proposal_status"]:
            changes.append({"word": word, "before": row["proposed_hyphenation"], "after": proposal,
                            "status_before": row["proposal_status"], "status_after": status,
                            "morphology_changed": refined != points,
                            "morpheme_points": morphology.seams(pronunciation)})
        updates.append((proposal, status, VERSION, word))
    sources = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
               for name in ("src/slabika/english_projection.py", "tools/evaluate_foreign_corpora.py",
                            "tools/refresh_english_review.py")}
    return {"version": VERSION, "input_sha256": fingerprint(rows), "source_sha256": sources,
            "generated": len(pronunciations), "skipped": len(rows) - len(pronunciations),
            "division_changes": sum(c["before"] != c["after"] for c in changes),
            "morphology_changes": sum(c["morphology_changed"] for c in changes),
            "incomplete": sum(u[1] == "incomplete" for u in updates),
            "changes": changes}, updates


def apply(db, report, updates):
    """Caller makes the backup; one transaction touches only generated proposals."""
    db.execute("BEGIN IMMEDIATE")
    try:
        if fingerprint(source_rows(db)) != report["input_sha256"]:
            raise ValueError("English inventory changed since planning; re-run the dry-run")
        now = datetime.now(timezone.utc).isoformat()
        db.executemany("UPDATE foreign_evidence SET proposed_hyphenation=?, proposal_status=?, "
                       "proposal_source=?, updated_at=? WHERE form=?",
                       [(proposal, status, source, now, word)
                        for proposal, status, source, word in updates])
        metadata = {k: v for k, v in report.items() if k != "changes"}
        metadata["updated_at"] = now
        db.execute("INSERT OR REPLACE INTO corpus_metadata VALUES ('english_projection', ?)",
                   (json.dumps(metadata, ensure_ascii=False, sort_keys=True),))
        verify_inventory(db, "en")
        db.commit()
    except BaseException:
        db.rollback()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "tests/data/foreign_review/en.sqlite")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "scratch/english-projection")
    parser.add_argument("--apply", action="store_true", help="back up and replace generated proposals only")
    args = parser.parse_args(argv)
    mode = "rw" if args.apply else "ro"
    db = sqlite3.connect(f"{args.inventory.resolve().as_uri()}?mode={mode}", uri=True, timeout=60)
    try:
        report, updates = plan(db)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = args.output_dir / f"{stamp}.json"
        if args.apply:
            backup_path = args.output_dir / f"en-before-{stamp}.sqlite"
            backup = sqlite3.connect(backup_path)
            try:
                db.backup(backup)
            finally:
                backup.close()
            report["backup"] = str(backup_path.resolve())
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.apply:
            apply(db, report, updates)
        print(json.dumps({k: v for k, v in report.items() if k != "changes"}, ensure_ascii=False))
        print(f"{'Applied' if args.apply else 'Dry run'}; audit: {path.resolve()}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
