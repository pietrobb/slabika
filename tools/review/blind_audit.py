# SPDX-FileCopyrightText: 2026 Peter Bezemek <peter.bezemek@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Prepare and persist a blind audit of typographic Slovak word division."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SELECTION_VERSION = "diverse-sha256-ngrams-v1"
ASSESSMENTS = {"resolved", "uncertain", "invalid"}
CONFIDENCES = {"high", "medium", "low"}
RESULT_METADATA_KEYS = (
    "created_at",
    "git_commit",
    "engine_tree_sha256",
    "item_count",
    "batch_count",
    "manifest_sha256",
)

MANIFEST_SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE batches (
    batch_id INTEGER PRIMARY KEY,
    batch_sha256 TEXT NOT NULL UNIQUE,
    item_count INTEGER NOT NULL CHECK(item_count > 0)
);
CREATE TABLE items (
    batch_id INTEGER NOT NULL REFERENCES batches(batch_id),
    position INTEGER NOT NULL,
    form TEXT NOT NULL UNIQUE,
    selection_tier INTEGER NOT NULL,
    PRIMARY KEY(batch_id, position)
) WITHOUT ROWID;
"""

RESULT_SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE decisions (
    batch_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    form TEXT NOT NULL UNIQUE,
    assessment TEXT NOT NULL CHECK(assessment IN ('resolved', 'uncertain', 'invalid')),
    expected_variants_json TEXT,
    confidence TEXT NOT NULL CHECK(confidence IN ('high', 'medium', 'low')),
    reason TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    PRIMARY KEY(batch_id, position)
) WITHOUT ROWID;
CREATE TABLE decision_log (
    entry_id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    form TEXT NOT NULL,
    assessment TEXT NOT NULL,
    expected_variants_json TEXT,
    confidence TEXT NOT NULL,
    reason TEXT NOT NULL,
    reviewer TEXT NOT NULL,
    logged_at TEXT NOT NULL
);
CREATE TABLE batch_claims (
    batch_id INTEGER PRIMARY KEY,
    claim_token TEXT NOT NULL UNIQUE,
    claimed_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _sha256_lines(lines: list[str]) -> str:
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _sha256_file(path: Path | None) -> str:
    if path is None:
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _engine_tree_sha256() -> str:
    lines = []
    for path in sorted((ROOT / "src" / "slabika").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            lines.append(f"{path.relative_to(ROOT).as_posix()}\t{_sha256_file(path)}")
    return _sha256_lines(lines)


def _atomic_write(path: Path, text: str) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _manifest_sha256(
    metadata: dict[str, str],
    batch_rows: list[tuple[int, str, int]],
    item_lines: list[str],
) -> str:
    lines = [
        f"metadata\t{key}\t{value}"
        for key, value in sorted(metadata.items())
        if key != "manifest_sha256"
    ]
    lines.extend(f"batch\t{batch_id}\t{batch_sha}\t{count}" for batch_id, batch_sha, count in batch_rows)
    lines.extend(f"item\t{line}" for line in item_lines)
    return _sha256_lines(lines)


def _stable_key(seed: str, namespace: str, form: str) -> bytes:
    return hashlib.sha256(f"{seed}\0{namespace}\0{form}".encode()).digest()


def _features(form: str) -> frozenset[str]:
    folded = unicodedata.normalize("NFC", form.casefold())
    features = {f"2:{folded[index:index + 2]}" for index in range(len(folded) - 1)}
    features.update(f"3:{folded[index:index + 3]}" for index in range(len(folded) - 2))
    return frozenset(features or {f"1:{folded}"})


def _similarity(left: frozenset[str], right: frozenset[str]) -> float:
    return len(left & right) / len(left | right)


def _excluded_forms(inventory: sqlite3.Connection, decisions_path: Path | None) -> set[str]:
    tables = {
        row[0]
        for row in inventory.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
    }
    excluded: set[str] = set()
    if "review_batch_items" in tables:
        excluded.update(row[0] for row in inventory.execute("SELECT form FROM review_batch_items"))
    if "review_events" in tables:
        excluded.update(row[0] for row in inventory.execute("SELECT form FROM review_events"))
    if "adjudications" in tables:
        excluded.update(
            row[0]
            for row in inventory.execute(
                """SELECT form FROM adjudications
                   WHERE review_status <> 'pending' OR expected_hyphenation IS NOT NULL"""
            )
        )
    if decisions_path is not None:
        with _open_readonly(decisions_path) as decisions:
            decision_tables = {
                row[0]
                for row in decisions.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            if "decisions" in decision_tables:
                excluded.update(row[0] for row in decisions.execute("SELECT form FROM decisions"))
    return excluded


def _select_diverse(candidates: list[str], count: int, seed: str) -> list[tuple[str, int]]:
    ordered = sorted(candidates, key=lambda form: _stable_key(seed, "candidate", form))
    tiers = (
        (0.34, 1, 2),
        (0.44, 2, 4),
        (0.56, 4, 8),
        (1.01, count, count),
    )
    selected: list[tuple[str, int]] = []
    selected_forms: set[str] = set()
    selected_features: list[frozenset[str]] = []
    inverted: dict[str, set[int]] = defaultdict(set)
    prefix_counts: Counter[str] = Counter()
    suffix_counts: Counter[str] = Counter()

    for tier_number, (threshold, prefix_limit, suffix_limit) in enumerate(tiers, start=1):
        for form in ordered:
            if form in selected_forms:
                continue
            folded = form.casefold()
            prefix = folded[:4]
            suffix = folded[-4:]
            if prefix_counts[prefix] >= prefix_limit or suffix_counts[suffix] >= suffix_limit:
                continue
            features = _features(form)
            possible: set[int] = set()
            for feature in features:
                possible.update(inverted[feature])
            if any(
                _similarity(features, selected_features[index]) >= threshold
                for index in possible
            ):
                continue
            index = len(selected)
            selected.append((form, tier_number))
            selected_forms.add(form)
            selected_features.append(features)
            prefix_counts[prefix] += 1
            suffix_counts[suffix] += 1
            for feature in features:
                inverted[feature].add(index)
            if len(selected) == count:
                return selected
    raise ValueError(f"z {len(candidates)} kandidátov sa nepodarilo vybrať {count} tvarov")


def _normalise_variants(form: str, values: object) -> list[str]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{form}: resolved položka musí mať neprázdne pole expected")
    variants: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise ValueError(f"{form}: každý expected variant musí byť text")
        marked = re.sub(r"[-|·\u2010-\u2015\s]+", "·", value.strip()).strip("·")
        if marked.replace("·", "") != form:
            raise ValueError(f"{form}: po odstránení hraníc z {value!r} nezostane pôvodný tvar")
        if marked not in variants:
            variants.append(marked)
    return variants


def prepare(args: argparse.Namespace) -> dict[str, object]:
    run_dir = args.run_dir.resolve()
    manifest_path = run_dir / "manifest.sqlite"
    results_path = run_dir / "results.sqlite"
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"cieľový priečinok nie je prázdny: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)

    with _open_readonly(args.inventory) as inventory:
        inventory.execute("BEGIN")
        excluded = _excluded_forms(inventory, args.prior_decisions)
        candidates = []
        seen: set[str] = set()
        for row in inventory.execute("SELECT form FROM forms ORDER BY form"):
            form = unicodedata.normalize("NFC", row[0])
            folded = form.casefold()
            if (
                form
                and form.isalpha()
                and not form[:1].isupper()
                and form not in excluded
                and folded not in seen
            ):
                candidates.append(form)
                seen.add(folded)

    selected = _select_diverse(candidates, args.count, args.seed)
    ordered = sorted(selected, key=lambda item: _stable_key(args.seed, "batch", item[0]))
    batches = [ordered[index:index + args.batch_size] for index in range(0, len(ordered), args.batch_size)]
    if any(len(batch) != args.batch_size for batch in batches):
        raise ValueError("count musí byť násobkom batch-size")

    commit = _git_commit()
    canonical = [
        f"{batch_id}\t{position}\t{form}\t{tier}"
        for batch_id, batch in enumerate(batches, start=1)
        for position, (form, tier) in enumerate(batch, start=1)
    ]
    batch_rows = []
    for batch_id, batch in enumerate(batches, start=1):
        batch_lines = [
            f"{position}\t{form}\t{tier}"
            for position, (form, tier) in enumerate(batch, 1)
        ]
        batch_rows.append((batch_id, _sha256_lines(batch_lines), len(batch)))
    tier_counts = Counter(tier for _, tier in selected)
    metadata = {
        "created_at": _now(),
        "seed": args.seed,
        "selection_version": SELECTION_VERSION,
        "git_commit": commit,
        "engine_tree_sha256": _engine_tree_sha256(),
        "audit_script_sha256": _sha256_file(Path(__file__)),
        "inventory_file_sha256": _sha256_file(args.inventory),
        "prior_decisions_file_sha256": _sha256_file(args.prior_decisions),
        "candidate_set_sha256": _sha256_lines(sorted(candidates)),
        "excluded_set_sha256": _sha256_lines(sorted(excluded)),
        "candidate_count": str(len(candidates)),
        "excluded_count": str(len(excluded)),
        "item_count": str(args.count),
        "batch_size": str(args.batch_size),
        "batch_count": str(len(batches)),
        "selection_tier_counts": json.dumps(tier_counts, sort_keys=True),
        "blind_contract": "forms-only; no engine output, adjudication, or prior decision in manifest",
    }
    manifest_sha = _manifest_sha256(metadata, batch_rows, canonical)
    metadata["manifest_sha256"] = manifest_sha

    manifest = sqlite3.connect(manifest_path)
    manifest.executescript(MANIFEST_SCHEMA)
    manifest.executemany("INSERT INTO metadata VALUES (?, ?)", metadata.items())
    for (batch_id, batch_sha, item_count), batch in zip(batch_rows, batches, strict=True):
        manifest.execute(
            "INSERT INTO batches VALUES (?, ?, ?)",
            (batch_id, batch_sha, item_count),
        )
        manifest.executemany(
            "INSERT INTO items VALUES (?, ?, ?, ?)",
            ((batch_id, position, form, tier) for position, (form, tier) in enumerate(batch, 1)),
        )
    manifest.commit()
    manifest.close()

    results = sqlite3.connect(results_path)
    results.executescript(RESULT_SCHEMA)
    results.executemany(
        "INSERT INTO metadata VALUES (?, ?)",
        ((key, metadata[key]) for key in RESULT_METADATA_KEYS),
    )
    results.commit()
    results.close()
    (run_dir / "backups").mkdir()
    return {
        "run_dir": str(run_dir),
        "candidates": len(candidates),
        "excluded": len(excluded),
        "selected": args.count,
        "batches": len(batches),
        "manifest_sha256": manifest_sha,
        "git_commit": commit,
    }


def _progress(run_dir: Path) -> tuple[sqlite3.Connection, sqlite3.Connection, dict[int, int]]:
    manifest = _open_readonly(run_dir / "manifest.sqlite")
    results = sqlite3.connect(run_dir / "results.sqlite")
    results.row_factory = sqlite3.Row
    results.execute("PRAGMA synchronous = FULL")
    results.execute(
        """CREATE TABLE IF NOT EXISTS batch_claims (
               batch_id INTEGER PRIMARY KEY,
               claim_token TEXT NOT NULL UNIQUE,
               claimed_at TEXT NOT NULL,
               expires_at TEXT NOT NULL
           )"""
    )
    expected_sha = manifest.execute(
        "SELECT value FROM metadata WHERE key = 'manifest_sha256'"
    ).fetchone()[0]
    actual_sha = results.execute(
        "SELECT value FROM metadata WHERE key = 'manifest_sha256'"
    ).fetchone()[0]
    metadata = dict(manifest.execute("SELECT key, value FROM metadata"))
    results_metadata = dict(results.execute("SELECT key, value FROM metadata"))
    expected_results_metadata = {key: metadata[key] for key in RESULT_METADATA_KEYS}
    if results_metadata != expected_results_metadata:
        manifest.close()
        results.close()
        raise ValueError("metadata results.sqlite sa nezhodujú s podpísaným manifestom")
    if _sha256_file(Path(__file__)) != metadata["audit_script_sha256"]:
        manifest.close()
        results.close()
        raise ValueError("audítorský skript sa od prípravy zmenil")
    batch_rows = [
        tuple(row)
        for row in manifest.execute(
            "SELECT batch_id, batch_sha256, item_count FROM batches ORDER BY batch_id"
        )
    ]
    canonical = [
        f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}"
        for row in manifest.execute(
            "SELECT batch_id, position, form, selection_tier FROM items ORDER BY batch_id, position"
        )
    ]
    if (
        expected_sha != actual_sha
        or _manifest_sha256(metadata, batch_rows, canonical) != expected_sha
    ):
        manifest.close()
        results.close()
        raise ValueError("manifest alebo results.sqlite má neplatný obsahový odtlačok")
    expected_items = {
        (row[0], row[1]): row[2]
        for row in manifest.execute("SELECT batch_id, position, form FROM items")
    }
    decision_rows = list(
        results.execute(
            """SELECT batch_id, position, form, assessment, expected_variants_json,
                      confidence, reason, reviewer, decided_at
               FROM decisions ORDER BY batch_id, position"""
        )
    )
    if any(expected_items.get((row[0], row[1])) != row[2] for row in decision_rows):
        manifest.close()
        results.close()
        raise ValueError("results.sqlite obsahuje rozhodnutie mimo presného manifestu")
    logged_rows = list(
        results.execute(
            """SELECT batch_id, position, form, assessment, expected_variants_json,
                      confidence, reason, reviewer, logged_at
               FROM decision_log ORDER BY batch_id, position, entry_id"""
        )
    )
    if [tuple(row) for row in logged_rows] != [tuple(row) for row in decision_rows]:
        manifest.close()
        results.close()
        raise ValueError("auditný log nie je v presnej zhode s rozhodnutiami")
    if results.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        manifest.close()
        results.close()
        raise ValueError("results.sqlite neprešiel quick_check")
    counts = Counter(row[0] for row in decision_rows)
    return manifest, results, dict(counts)


def next_batch(args: argparse.Namespace) -> dict[str, object]:
    manifest, results, _ = _progress(args.run_dir.resolve())
    try:
        now = datetime.now(timezone.utc)
        results.execute("BEGIN IMMEDIATE")
        results.execute("DELETE FROM batch_claims WHERE expires_at <= ?", (now.isoformat(),))
        busy_batches = []
        for row in manifest.execute(
            "SELECT batch_id, item_count, batch_sha256 FROM batches ORDER BY batch_id"
        ):
            saved = results.execute(
                "SELECT count(*) FROM decisions WHERE batch_id = ?", (row[0],)
            ).fetchone()[0]
            if saved == row[1]:
                results.execute("DELETE FROM batch_claims WHERE batch_id = ?", (row[0],))
                continue
            if saved:
                raise ValueError(f"dávka {row[0]} je uložená iba čiastočne")
            if saved < row[1]:
                existing = results.execute(
                    "SELECT expires_at FROM batch_claims WHERE batch_id = ?", (row[0],)
                ).fetchone()
                if existing is not None:
                    busy_batches.append({"batch_id": row[0], "claim_expires_at": existing[0]})
                    continue
                claim_token = secrets.token_urlsafe(24)
                expires_at = (now + timedelta(minutes=30)).isoformat()
                results.execute(
                    "INSERT INTO batch_claims VALUES (?, ?, ?, ?)",
                    (row[0], claim_token, now.isoformat(), expires_at),
                )
                results.commit()
                items = [
                    {"position": item[0], "form": item[1]}
                    for item in manifest.execute(
                        "SELECT position, form FROM items WHERE batch_id = ? ORDER BY position",
                        (row[0],),
                    )
                ]
                return {
                    "batch_id": row[0],
                    "batch_sha256": row[2],
                    "claim_token": claim_token,
                    "claim_expires_at": expires_at,
                    "instructions": {
                        "assessment": "resolved | uncertain | invalid",
                        "expected": "pri resolved zoznam všetkých prípustných variantov so znakom |",
                        "confidence": "high | medium | low",
                        "reason": "stručné nezávislé pravidlo; neporovnávať s enginom",
                    },
                    "items": items,
                }
        results.commit()
        if busy_batches:
            return {"busy": True, "claimed_batches": busy_batches}
        return {"complete": True, "message": "všetkých 50 dávok je uložených"}
    except Exception:
        results.rollback()
        raise
    finally:
        manifest.close()
        results.close()


def submit(args: argparse.Namespace) -> dict[str, object]:
    run_dir = args.run_dir.resolve()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    entries = payload.get("items") if isinstance(payload, dict) else None
    claim_token = payload.get("claim_token") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not isinstance(claim_token, str):
        raise ValueError("vstup musí mať polia claim_token a items")
    if not args.reviewer.strip():
        raise ValueError("reviewer nesmie byť prázdny")

    manifest, results, _ = _progress(run_dir)
    try:
        expected_rows = list(
            manifest.execute(
                "SELECT position, form FROM items WHERE batch_id = ? ORDER BY position",
                (args.batch,),
            )
        )
        if not expected_rows:
            raise ValueError(f"neexistujúca dávka {args.batch}")
        by_position = {entry.get("position"): entry for entry in entries if isinstance(entry, dict)}
        if len(entries) != len(expected_rows) or set(by_position) != {row[0] for row in expected_rows}:
            raise ValueError(f"dávka musí obsahovať presne pozície 1 až {len(expected_rows)}")

        validated = []
        timestamp = _now()
        for position, form in expected_rows:
            entry = by_position[position]
            if entry.get("form") != form:
                raise ValueError(f"pozícia {position}: očakáva sa tvar {form!r}")
            assessment = entry.get("assessment")
            confidence = entry.get("confidence")
            reason = entry.get("reason", "")
            if assessment not in ASSESSMENTS:
                raise ValueError(f"{form}: neplatný assessment")
            if confidence not in CONFIDENCES:
                raise ValueError(f"{form}: neplatná confidence")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"{form}: každé blind rozhodnutie vyžaduje stručný dôvod")
            variants = (
                _normalise_variants(form, entry.get("expected"))
                if assessment == "resolved"
                else None
            )
            if assessment != "resolved" and entry.get("expected") not in (None, []):
                raise ValueError(f"{form}: iba resolved položka môže mať expected")
            variants_json = (
                json.dumps(variants, ensure_ascii=False) if variants is not None else None
            )
            validated.append(
                (
                    args.batch,
                    position,
                    form,
                    assessment,
                    variants_json,
                    confidence,
                    reason.strip(),
                    args.reviewer.strip(),
                    timestamp,
                )
            )

        results.execute("BEGIN IMMEDIATE")
        existing = list(
            results.execute(
                """SELECT batch_id, position, form, assessment, expected_variants_json,
                          confidence, reason, reviewer
                   FROM decisions WHERE batch_id = ? ORDER BY position""",
                (args.batch,),
            )
        )
        comparable = [row[:-1] for row in validated]
        if existing:
            if [tuple(row) for row in existing] != comparable:
                raise ValueError(f"dávka {args.batch} už obsahuje iné výsledky")
            results.execute("DELETE FROM batch_claims WHERE batch_id = ?", (args.batch,))
            idempotent = True
        else:
            claim = results.execute(
                "SELECT claim_token, expires_at FROM batch_claims WHERE batch_id = ?",
                (args.batch,),
            ).fetchone()
            if claim is None or claim[0] != claim_token:
                raise ValueError(f"dávka {args.batch} nemá platný claim")
            if claim[1] <= datetime.now(timezone.utc).isoformat():
                raise ValueError(f"claim dávky {args.batch} vypršal")
            results.executemany(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", validated
            )
            results.executemany(
                """INSERT INTO decision_log(
                       batch_id, position, form, assessment, expected_variants_json,
                       confidence, reason, reviewer, logged_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                validated,
            )
            results.execute("DELETE FROM batch_claims WHERE batch_id = ?", (args.batch,))
            idempotent = False
        results.commit()

        backup_path = run_dir / "backups" / f"results-batch-{args.batch:03d}.sqlite"
        temporary_backup = backup_path.with_name(f".{backup_path.name}.tmp.sqlite")
        temporary_backup.unlink(missing_ok=True)
        backup = sqlite3.connect(temporary_backup)
        results.backup(backup)
        backup.close()
        os.replace(temporary_backup, backup_path)
        total = results.execute("SELECT count(*) FROM decisions").fetchone()[0]
        return {
            "saved_batch": args.batch,
            "saved_items": len(validated),
            "total_saved": total,
            "idempotent": idempotent,
            "backup": str(backup_path),
        }
    except Exception:
        results.rollback()
        raise
    finally:
        manifest.close()
        results.close()


def status(args: argparse.Namespace) -> dict[str, object]:
    manifest, results, counts = _progress(args.run_dir.resolve())
    try:
        batch_count = manifest.execute("SELECT count(*) FROM batches").fetchone()[0]
        item_count = manifest.execute("SELECT count(*) FROM items").fetchone()[0]
        saved = results.execute("SELECT count(*) FROM decisions").fetchone()[0]
        completed = sum(
            counts.get(row[0], 0) == row[1]
            for row in manifest.execute("SELECT batch_id, item_count FROM batches")
        )
        return {
            "batches_completed": completed,
            "batches_total": batch_count,
            "items_saved": saved,
            "items_total": item_count,
            "complete": completed == batch_count and saved == item_count,
        }
    finally:
        manifest.close()
        results.close()


def report(args: argparse.Namespace) -> dict[str, object]:
    run_dir = args.run_dir.resolve()
    current_status = status(argparse.Namespace(run_dir=run_dir))
    if not current_status["complete"]:
        raise ValueError("porovnanie s enginom je zakázané, kým nie je blind audit úplný")
    manifest, results, _ = _progress(run_dir)
    try:
        prepared_commit = manifest.execute(
            "SELECT value FROM metadata WHERE key = 'git_commit'"
        ).fetchone()[0]
        current_commit = _git_commit()
        prepared_tree = manifest.execute(
            "SELECT value FROM metadata WHERE key = 'engine_tree_sha256'"
        ).fetchone()[0]
        current_tree = _engine_tree_sha256()
        if current_commit != prepared_commit or current_tree != prepared_tree:
            raise ValueError(
                "engine sa od prípravy zmenil: nezhoduje sa commit alebo obsah src/slabika"
            )
        source_path = str(ROOT / "src")
        if source_path in sys.path:
            sys.path.remove(source_path)
        sys.path.insert(0, source_path)
        for module_name in tuple(sys.modules):
            if module_name == "slabika" or module_name.startswith("slabika."):
                del sys.modules[module_name]
        from slabika import __version__, hyphenate

        compared_at = _now()
        comparisons = []
        mismatches = []
        for row in results.execute(
            """SELECT batch_id, position, form, assessment, expected_variants_json,
                      confidence, reason
               FROM decisions ORDER BY batch_id, position"""
        ):
            engine = hyphenate(row[2])
            if row[3] != "resolved":
                outcome = "unscored"
                variants = None
            else:
                variants = json.loads(row[4])
                outcome = "match" if engine in variants else "mismatch"
            comparisons.append((row[0], row[1], row[2], engine, outcome, compared_at))
            if outcome == "mismatch":
                mismatches.append(
                    {
                        "batch_id": row[0],
                        "position": row[1],
                        "form": row[2],
                        "expected": variants,
                        "engine": engine,
                        "confidence": row[5],
                        "reason": row[6],
                    }
                )
        summary_counts = Counter(row[4] for row in comparisons)
        summary = {
            **current_status,
            "compared_at": compared_at,
            "engine_version": __version__,
            "git_commit": current_commit,
            "match": summary_counts["match"],
            "mismatch": summary_counts["mismatch"],
            "unscored": summary_counts["unscored"],
        }
        _atomic_write(
            run_dir / "report.json",
            json.dumps(
                {"summary": summary, "mismatches": mismatches},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        return summary
    except Exception:
        results.rollback()
        raise
    finally:
        manifest.close()
        results.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--inventory", type=Path, required=True)
    prepare_parser.add_argument("--prior-decisions", type=Path)
    prepare_parser.add_argument("--run-dir", type=Path, required=True)
    prepare_parser.add_argument("--seed", default="slabika-blind-5000-v1")
    prepare_parser.add_argument("--count", type=int, default=5000)
    prepare_parser.add_argument("--batch-size", type=int, default=100)
    prepare_parser.set_defaults(handler=prepare)

    for name, handler in (("next", next_batch), ("status", status), ("report", report)):
        command = commands.add_parser(name)
        command.add_argument("--run-dir", type=Path, required=True)
        command.set_defaults(handler=handler)

    submit_parser = commands.add_parser("submit")
    submit_parser.add_argument("--run-dir", type=Path, required=True)
    submit_parser.add_argument("--batch", type=int, required=True)
    submit_parser.add_argument("--input", type=Path, required=True)
    submit_parser.add_argument("--reviewer", default="cron-llm-psp-v1")
    submit_parser.set_defaults(handler=submit)
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        output = args.handler(args)
    except Exception as error:  # noqa: BLE001 - concise CLI failure
        raise SystemExit(f"error: {error}") from error
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
