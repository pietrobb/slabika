# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Regression tests for the isolated blind word-division audit."""

import argparse
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "slabika_blind_audit", ROOT / "tools" / "review" / "blind_audit.py"
)
BLIND = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BLIND)
RECONCILE_SPEC = importlib.util.spec_from_file_location(
    "slabika_reconcile", ROOT / "tools" / "review" / "reconcile.py"
)
RECONCILE = importlib.util.module_from_spec(RECONCILE_SPEC)
RECONCILE_SPEC.loader.exec_module(RECONCILE)


def _inventory(path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE forms (form TEXT PRIMARY KEY) WITHOUT ROWID;
        CREATE TABLE adjudications (
            form TEXT PRIMARY KEY,
            review_status TEXT NOT NULL,
            expected_hyphenation TEXT
        ) WITHOUT ROWID;
        CREATE TABLE review_batch_items (batch_id INTEGER, position INTEGER, form TEXT);
        CREATE TABLE review_events (event_id INTEGER PRIMARY KEY, form TEXT);
        """
    )
    forms = (
        "abeceda", "bicykel", "citrón", "dážďovka", "elektrina", "fujara",
        "gitara", "hodiny", "ihličie", "jahoda", "kvetina", "lopata",
        "motyka", "nedeľa", "Reviewed", "foo-bar", "poznané", "udalosť",
    )
    for form in forms:
        status = "verified" if form == "poznané" else "pending"
        connection.execute("INSERT INTO forms VALUES (?)", (form,))
        connection.execute("INSERT INTO adjudications VALUES (?, ?, NULL)", (form, status))
    connection.execute("INSERT INTO review_events(form) VALUES ('udalosť')")
    connection.commit()
    connection.close()


def _prior_decisions(path):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE decisions (form TEXT PRIMARY KEY) WITHOUT ROWID")
    connection.execute("INSERT INTO decisions VALUES ('jahoda')")
    connection.commit()
    connection.close()


def test_manual_psp_adjudication_is_complete_and_unique():
    adjudication = RECONCILE.load_psp_adjudication(
        ROOT / "tests" / "data" / "manual_psp_adjudication.json"
    )
    statuses = [item["status"] for item in adjudication.values()]

    assert len(adjudication) == 144
    assert {status: statuses.count(status) for status in set(statuses)} == {
        "human_matches_psp": 30,
        "engine_matches_psp": 26,
        "neither_matches_psp": 1,
        "both_psp_different_modes": 6,
        "psp_requires_pronunciation": 81,
    }


def _prepare(tmp_path, run_name):
    inventory = tmp_path / "inventory.sqlite"
    decisions = tmp_path / "decisions.sqlite"
    if not inventory.exists():
        _inventory(inventory)
        _prior_decisions(decisions)
    args = argparse.Namespace(
        inventory=inventory,
        prior_decisions=decisions,
        run_dir=tmp_path / run_name,
        seed="fixed-seed",
        count=8,
        batch_size=4,
    )
    return args, BLIND.prepare(args)


def _submission(batch):
    return {
        "claim_token": batch["claim_token"],
        "items": [
            {
                "position": item["position"],
                "form": item["form"],
                "assessment": "resolved",
                "expected": [item["form"]],
                "confidence": "medium",
                "reason": "blind test fixture",
            }
            for item in batch["items"]
        ]
    }


def test_prepare_is_reproducible_diverse_and_blind(tmp_path, monkeypatch):
    monkeypatch.setattr(BLIND, "_git_commit", lambda: "abc123")
    first_args, first = _prepare(tmp_path, "first")
    second_args, second = _prepare(tmp_path, "second")

    assert first["selected"] == 8
    assert first["batches"] == 2
    assert first["git_commit"] == second["git_commit"] == "abc123"

    with sqlite3.connect(first_args.run_dir / "manifest.sqlite") as connection:
        rows = connection.execute("SELECT form FROM items ORDER BY batch_id, position").fetchall()
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
    with sqlite3.connect(second_args.run_dir / "manifest.sqlite") as connection:
        second_rows = connection.execute(
            "SELECT form FROM items ORDER BY batch_id, position"
        ).fetchall()
    forms = [row[0] for row in rows]
    assert forms == [row[0] for row in second_rows]
    assert len(forms) == len(set(forms)) == 8
    assert all(form.isalpha() and not form[:1].isupper() for form in forms)
    assert {"jahoda", "poznané", "udalosť"}.isdisjoint(forms)
    assert metadata["blind_contract"].startswith("forms-only")
    with sqlite3.connect(first_args.run_dir / "results.sqlite") as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "comparisons" not in tables

    first_batch = BLIND.next_batch(argparse.Namespace(run_dir=first_args.run_dir))
    encoded = json.dumps(first_batch, ensure_ascii=False)
    assert first_batch["batch_id"] == 1
    assert len(first_batch["items"]) == 4
    for forbidden in ("engine", "adjudication", "verdict", "prior_decision"):
        assert forbidden not in encoded


def test_manifest_hash_and_exact_result_membership_are_enforced(tmp_path, monkeypatch):
    monkeypatch.setattr(BLIND, "_git_commit", lambda: "abc123")
    args, _ = _prepare(tmp_path, "tampered-result")
    with sqlite3.connect(args.run_dir / "results.sqlite") as connection:
        connection.execute(
            """INSERT INTO decisions VALUES
               (99, 1, 'podvrh', 'resolved', '[\"podvrh\"]', 'low',
                'tamper', 'test', '2026-01-01T00:00:00+00:00')"""
        )
        connection.execute(
            """INSERT INTO decision_log(
                   batch_id, position, form, assessment, expected_variants_json,
                   confidence, reason, reviewer, logged_at)
               VALUES
               (99, 1, 'podvrh', 'resolved', '[\"podvrh\"]', 'low',
                'tamper', 'test', '2026-01-01T00:00:00+00:00')"""
        )
        connection.commit()
    with pytest.raises(ValueError, match="mimo presného manifestu"):
        BLIND.status(argparse.Namespace(run_dir=args.run_dir))

    clean_args, _ = _prepare(tmp_path, "tampered-manifest")
    with sqlite3.connect(clean_args.run_dir / "manifest.sqlite") as connection:
        connection.execute("UPDATE items SET form = 'podvrh' WHERE batch_id = 1 AND position = 1")
        connection.commit()
    with pytest.raises(ValueError, match="obsahový odtlačok"):
        BLIND.status(argparse.Namespace(run_dir=clean_args.run_dir))

    metadata_args, _ = _prepare(tmp_path, "tampered-metadata")
    with sqlite3.connect(metadata_args.run_dir / "manifest.sqlite") as connection:
        connection.execute(
            "UPDATE metadata SET value = 'other' WHERE key = 'created_at'"
        )
        connection.commit()
    with pytest.raises(ValueError, match="metadata results|obsahový odtlačok"):
        BLIND.status(argparse.Namespace(run_dir=metadata_args.run_dir))


def test_engine_hash_includes_non_python_package_data(tmp_path, monkeypatch):
    package = tmp_path / "src" / "slabika" / "data"
    package.mkdir(parents=True)
    source = package.parent / "engine.py"
    data = package / "rules.json"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    data.write_text('{"value": 1}\n', encoding="utf-8")
    monkeypatch.setattr(BLIND, "ROOT", tmp_path)
    before = BLIND._engine_tree_sha256()
    data.write_text('{"value": 2}\n', encoding="utf-8")
    assert BLIND._engine_tree_sha256() != before


def test_audit_script_is_immutable_after_prepare(tmp_path, monkeypatch):
    monkeypatch.setattr(BLIND, "_git_commit", lambda: "abc123")
    args, _ = _prepare(tmp_path, "changed-script")
    original = BLIND._sha256_file
    script_path = Path(BLIND.__file__)
    monkeypatch.setattr(
        BLIND,
        "_sha256_file",
        lambda path: "changed" if path == script_path else original(path),
    )
    with pytest.raises(ValueError, match="audítorský skript"):
        BLIND.status(argparse.Namespace(run_dir=args.run_dir))


def test_decision_content_must_match_audit_log(tmp_path, monkeypatch):
    monkeypatch.setattr(BLIND, "_git_commit", lambda: "abc123")
    args, _ = _prepare(tmp_path, "tampered-audit")
    batch = BLIND.next_batch(argparse.Namespace(run_dir=args.run_dir))
    submission_path = tmp_path / "audit-batch.json"
    submission_path.write_text(
        json.dumps(_submission(batch), ensure_ascii=False), encoding="utf-8"
    )
    BLIND.submit(
        argparse.Namespace(
            run_dir=args.run_dir,
            batch=1,
            input=submission_path,
            reviewer="test",
        )
    )
    with sqlite3.connect(args.run_dir / "results.sqlite") as connection:
        connection.execute(
            "UPDATE decisions SET reason = 'tampered' WHERE batch_id = 1 AND position = 1"
        )
        connection.commit()
    with pytest.raises(ValueError, match="auditný log"):
        BLIND.status(argparse.Namespace(run_dir=args.run_dir))


def test_submit_is_atomic_backed_up_and_report_stays_sealed_until_complete(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(BLIND, "_git_commit", lambda: "abc123")
    args, _ = _prepare(tmp_path, "run")
    batch = BLIND.next_batch(argparse.Namespace(run_dir=args.run_dir))
    second_batch = BLIND.next_batch(argparse.Namespace(run_dir=args.run_dir))
    assert second_batch["batch_id"] == 2

    incomplete = _submission(batch)
    incomplete["items"].pop()
    incomplete_path = tmp_path / "incomplete.json"
    incomplete_path.write_text(json.dumps(incomplete, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="presne pozície"):
        BLIND.submit(
            argparse.Namespace(
                run_dir=args.run_dir,
                batch=1,
                input=incomplete_path,
                reviewer="test",
            )
        )
    with sqlite3.connect(args.run_dir / "results.sqlite") as connection:
        assert connection.execute("SELECT count(*) FROM decisions").fetchone()[0] == 0

    for batch_id in (1, 2):
        current = batch if batch_id == 1 else second_batch
        submission_path = tmp_path / f"batch-{batch_id}.json"
        submission_path.write_text(
            json.dumps(_submission(current), ensure_ascii=False), encoding="utf-8"
        )
        result = BLIND.submit(
            argparse.Namespace(
                run_dir=args.run_dir,
                batch=batch_id,
                input=submission_path,
                reviewer="test",
            )
        )
        assert result["saved_items"] == 4
        assert result["idempotent"] is False
        assert Path(result["backup"]).exists()
        repeated = BLIND.submit(
            argparse.Namespace(
                run_dir=args.run_dir,
                batch=batch_id,
                input=submission_path,
                reviewer="test",
            )
        )
        assert repeated["idempotent"] is True
        assert repeated["total_saved"] == batch_id * 4
        if batch_id == 1:
            with pytest.raises(ValueError, match="kým nie je blind audit úplný"):
                BLIND.report(argparse.Namespace(run_dir=args.run_dir))

    current_status = BLIND.status(argparse.Namespace(run_dir=args.run_dir))
    assert current_status == {
        "batches_completed": 2,
        "batches_total": 2,
        "items_saved": 8,
        "items_total": 8,
        "complete": True,
    }
    assert BLIND.next_batch(argparse.Namespace(run_dir=args.run_dir))["complete"] is True

    with sqlite3.connect(args.run_dir / "manifest.sqlite") as connection:
        prepared_tree = connection.execute(
            "SELECT value FROM metadata WHERE key = 'engine_tree_sha256'"
        ).fetchone()[0]
    monkeypatch.setattr(BLIND, "_git_commit", lambda: "later456")
    monkeypatch.setattr(BLIND, "_engine_tree_sha256", lambda: "later-tree")
    summary = BLIND.report(argparse.Namespace(run_dir=args.run_dir))
    assert summary["prepared_git_commit"] == "abc123"
    assert summary["git_commit"] == "later456"
    assert summary["prepared_engine_tree_sha256"] == prepared_tree
    assert summary["current_engine_tree_sha256"] == "later-tree"
    assert summary["match"] + summary["mismatch"] + summary["unscored"] == 8
    report = json.loads((args.run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["summary"] == summary
    assert len(report["mismatches"]) == summary["mismatch"]
    assert not (args.run_dir / "mismatches.jsonl").exists()
