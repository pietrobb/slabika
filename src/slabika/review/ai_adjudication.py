# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Append-only dual-model evidence, separate from Human and normative PSP data.

Only persist_run writes. Readers neither create a database nor migrate its schema.
No provider/configuration files are opened; sources are transcript provenance only.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from html import escape
from pathlib import Path

MODELS = ("A", "B")
STAGES = ("independent", "cross_review", "reconciliation")
STATUSES = (
    "consensus_independent",
    "consensus_after_cross_review",
    "consensus_after_reconciliation",
    "unresolved_model_disagreement",
)
ADVISORY = "AI advisory evidence only — not a PSP verdict or Human decision."

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS ai_adjudication_runs (
        run_id TEXT PRIMARY KEY,
        transcript_sha256 TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        persisted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        transcript_json TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS ai_adjudication_items (
        run_id TEXT NOT NULL REFERENCES ai_adjudication_runs(run_id) ON DELETE RESTRICT,
        form TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN (
            'consensus_independent', 'consensus_after_cross_review',
            'consensus_after_reconciliation', 'unresolved_model_disagreement')),
        result_json TEXT NOT NULL,
        positions_json TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        rounds_json TEXT NOT NULL,
        PRIMARY KEY(run_id, form)
    ) WITHOUT ROWID""",
    """CREATE INDEX IF NOT EXISTS ai_adjudication_items_form
       ON ai_adjudication_items(form, status, run_id)""",
    *(
        f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
            BEFORE {operation} ON {table} BEGIN
                SELECT RAISE(ABORT, 'AI adjudication history is immutable');
            END"""
        for table in ("ai_adjudication_runs", "ai_adjudication_items")
        for operation in ("UPDATE", "DELETE")
    ),
)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _signature(verdict: dict) -> tuple:
    # Deliberately matches the producer's consensus scope, not reasons/confidence.
    return verdict["choice"], verdict["preferred"], tuple(sorted(verdict["permitted_variants"]))


def _validate_verdict(verdict: object, form: str, evidence: dict) -> None:
    _require(isinstance(verdict, dict), f"{form}: verdict must be an object")
    fields = (
        "choice", "preferred", "human_assessment", "engine_assessment", "psp_reference",
        "morphological_analysis", "pronunciation_assumption", "reason", "confidence",
    )
    _require(verdict.get("form") == form, f"{form}: verdict form mismatch")
    _require(all(_text(verdict.get(key)) for key in fields), f"{form}: missing verdict fields")
    choice = verdict["choice"]
    _require(choice in {"human", "engine", "both", "neither", "context_dependent"},
             f"{form}: invalid choice")
    assessments = {"correct", "incorrect", "partly_correct", "context_dependent"}
    _require(all(verdict[key] in assessments for key in ("human_assessment", "engine_assessment")),
             f"{form}: invalid assessment")
    _require(verdict["confidence"] in {"high", "medium", "low"}, f"{form}: invalid confidence")
    variants = verdict.get("permitted_variants")
    _require(isinstance(variants, list) and bool(variants) and all(_text(v) for v in variants),
             f"{form}: permitted_variants must be a nonempty string list")
    _require(len(set(variants)) == len(variants), f"{form}: duplicate variants")
    _require(verdict["preferred"] in variants, f"{form}: preferred is not permitted")
    for value in variants:
        _require(value.replace("·", "") == form and not value.startswith("·")
                 and not value.endswith("·") and "··" not in value,
                 f"{form}: invalid marked form")
    required_correct = {"human": ("human_assessment",), "engine": ("engine_assessment",),
                        "both": ("human_assessment", "engine_assessment")}
    _require(all(verdict[key] == "correct" for key in required_correct.get(choice, ())),
             f"{form}: choice contradicts assessments")
    if choice == "neither":
        _require("correct" not in {verdict["human_assessment"], verdict["engine_assessment"]},
                 f"{form}: neither contradicts assessments")
    if choice == "context_dependent":
        _require(len(variants) >= 2, f"{form}: context_dependent needs multiple variants")
    human = evidence.get("human") or {}
    modes = evidence.get("engine_modes", {})
    _require(isinstance(human, dict) and isinstance(modes, dict), f"{form}: invalid evidence")
    human_value = human.get("expected_hyphenation")
    if human.get("action") == "confirm" and not human_value:
        human_value = human.get("engine_snapshot")
    _require(human_value is None or _text(human_value), f"{form}: invalid Human evidence")
    _require(all(_text(value) for value in modes.values()), f"{form}: invalid engine evidence")
    human_value = human_value.replace("|", "·") if human_value else None
    engine_values = {value.replace("|", "·") for value in modes.values()}
    if choice == "human" and human_value is not None:
        _require(verdict["preferred"] == human_value, f"{form}: human choice mismatches evidence")
    if choice == "engine" and engine_values:
        _require(verdict["preferred"] in engine_values, f"{form}: engine choice mismatches evidence")
    if choice == "both" and human_value is not None and engine_values:
        _require(human_value in variants and bool(engine_values.intersection(variants)),
                 f"{form}: both choice omits a voice")
    if choice == "neither":
        _require(verdict["preferred"] not in engine_values | {human_value},
                 f"{form}: neither reuses a supplied voice")


def _by_form(items: object, name: str) -> dict[str, dict]:
    _require(isinstance(items, list) and bool(items), f"{name} must be a nonempty list")
    result = {}
    for item in items:
        _require(isinstance(item, dict) and _text(item.get("form")), f"{name}: missing form")
        form = item["form"]
        _require(form not in result, f"{name}: duplicate form")
        result[form] = item
    return result


def _validate(result: object) -> list[dict]:
    _require(isinstance(result, dict), "result must be an object")
    _require(_text(result.get("created_at")), "created_at is required")
    try:
        stamp = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("created_at must be an ISO timestamp") from error
    _require(stamp.tzinfo is not None, "created_at must include a timezone")
    _require(isinstance(result.get("sources"), dict), "sources must be an object")
    models = result.get("models")
    _require(isinstance(models, dict) and set(models) == set(MODELS), "models must contain A/B")
    for model in models.values():
        _require(isinstance(model, dict) and _text(model.get("model"))
                 and _text(model.get("label")), "model ID and label are required")
    evidence = _by_form(result.get("evidence"), "evidence")
    consensus = _by_form(result.get("consensus"), "consensus")
    _require(set(evidence) == set(consensus), "consensus/evidence forms differ")
    if "evidence_sha256" in result:
        _require(result["evidence_sha256"] == _hash(_json(result["evidence"])),
                 "evidence_sha256 mismatch")
    rounds = result.get("rounds")
    _require(isinstance(rounds, dict) and "independent" in rounds
             and set(rounds).issubset(STAGES), "invalid rounds")
    pending = set(evidence)
    resolved = {}
    histories = {form: {} for form in evidence}
    for stage, status in zip(STAGES, STATUSES):
        if not pending:
            _require(stage not in rounds, f"unexpected {stage} round")
            continue
        round_ = rounds.get(stage)
        _require(isinstance(round_, dict) and set(round_) == set(MODELS),
                 f"{stage}: A/B round required")
        for key in MODELS:
            positions = round_[key]
            _require(isinstance(positions, dict) and set(positions) == pending,
                     f"{stage}/{key}: forms do not match outstanding disputes")
            for form, verdict in positions.items():
                _validate_verdict(verdict, form, evidence[form])
        next_pending = set()
        for form in pending:
            positions = {key: round_[key][form] for key in MODELS}
            histories[form][stage] = positions
            agreed = _signature(positions["A"]) == _signature(positions["B"])
            if agreed:
                resolved[form] = (status, positions["A"], positions)
            else:
                next_pending.add(form)
                if stage == "reconciliation":
                    resolved[form] = (STATUSES[-1], None, positions)
        pending = next_pending
    items = []
    counts = dict.fromkeys(STATUSES, 0)
    for form, item in consensus.items():
        status, verdict, positions = resolved[form]
        expected = {
            "status": status, "verdict": verdict,
            "supporting_model_verdicts": positions if verdict is not None else None,
            "final_model_positions": positions if verdict is None else None,
        }
        _require(all(key in item and item[key] == value for key, value in expected.items()),
                 f"{form}: consensus contradicts model rounds")
        counts[status] += 1
        items.append({"form": form, "status": status, "result": item,
                      "positions": positions, "evidence": evidence[form],
                      "rounds": histories[form]})
    summary = result.get("summary")
    expected_counts = {"forms": len(items), **counts}
    _require(isinstance(summary, dict) and all(type(summary.get(key)) is int
             and summary[key] == value for key, value in expected_counts.items()),
             "summary contradicts consensus")
    return items


def persist_run(db_path: Path, result: dict) -> str:
    """Validate and atomically append a full adjudicator result; return its SHA-256 ID.

    The hash covers the entire canonical JSON transcript, including created_at and
    sources. Key order/formatting do not matter; a changed transcript is a new run.
    Invalid input raises ValueError before connecting. Only AI tables are created.
    """
    try:
        transcript = _json(result)
        snapshot = json.loads(transcript)
    except (TypeError, ValueError) as error:
        raise ValueError("result must be finite JSON data") from error
    items = _validate(snapshot)
    run_id = _hash(transcript)
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        # execute(), not executescript(): schema creation participates in rollback.
        for statement in _SCHEMA:
            connection.execute(statement)
        if connection.execute(
            "SELECT 1 FROM ai_adjudication_runs WHERE transcript_sha256 = ?", (run_id,)
        ).fetchone():
            return run_id
        connection.execute(
            """INSERT INTO ai_adjudication_runs
               (run_id, transcript_sha256, created_at, transcript_json) VALUES (?, ?, ?, ?)""",
            (run_id, run_id, snapshot["created_at"], transcript),
        )
        connection.executemany(
            """INSERT INTO ai_adjudication_items
               (run_id, form, status, result_json, positions_json, evidence_json, rounds_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(run_id, item["form"], item["status"], _json(item["result"]),
              _json(item["positions"]), _json(item["evidence"]), _json(item["rounds"]))
             for item in items],
        )
    return run_id


def get_form_history(db_path: Path, form: str) -> list[dict]:
    """Return exact-form history, newest insertion first, with all applicable rounds.

    Each entry includes run_id, timestamps, models, sources, summary, consensus,
    final positions and the input evidence snapshot. Missing DB/schema returns [].
    This opens SQLite in mode=ro and never creates tables or changes Human/PSP rows.
    """
    _require(_text(form), "form must be a nonempty string")
    if not db_path.is_file():
        return []
    with closing(sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
            "('ai_adjudication_runs', 'ai_adjudication_items')"
        )}
        if len(tables) != 2:
            return []
        rows = connection.execute(
            """SELECT r.*, i.status, i.result_json, i.positions_json, i.evidence_json, i.rounds_json
               FROM ai_adjudication_items AS i JOIN ai_adjudication_runs AS r USING (run_id)
               WHERE i.form = ? ORDER BY r.rowid DESC""", (form,),
        )
        history = []
        for row in rows:
            transcript = json.loads(row["transcript_json"])
            history.append({
                "run_id": row["run_id"], "transcript_sha256": row["transcript_sha256"],
                "created_at": row["created_at"], "persisted_at": row["persisted_at"],
                "advisory": ADVISORY, "form": form, "status": row["status"],
                "models": transcript["models"], "sources": transcript["sources"],
                "summary": transcript["summary"],
                "consensus": json.loads(row["result_json"]),
                "positions": json.loads(row["positions_json"]),
                "evidence": json.loads(row["evidence_json"]),
                "rounds": json.loads(row["rounds_json"]),
            })
        return history


def form_history_html(db_path: Path, form: str) -> str:
    """Render a read-only item detail section; every transcript value is escaped."""
    history = get_form_history(db_path, form)
    out = [f'<details class="ai-adjudication"><summary>AI adjudikácia — {escape(form)} ({len(history)})'
           f'</summary><p>{escape(ADVISORY)}</p>']
    if not history:
        out.append("<p>Bez uložených AI posúdení.</p>")
    for run in history:
        out.append(f'<details><summary>{escape(run["created_at"])} — '
                   f'{escape(run["status"])}</summary><p>Run: {escape(run["run_id"])}</p>')
        for stage in STAGES:
            if stage not in run["rounds"]:
                continue
            out.append(f"<h4>{escape(stage)}</h4>")
            for key in MODELS:
                model = run["models"][key]
                verdict = run["rounds"][stage][key]
                out.append(f'<p><b>{key}: {escape(model["label"])} / '
                           f'{escape(model["model"])}</b></p><dl>')
                for field, value in verdict.items():
                    text = " / ".join(value) if isinstance(value, list) else str(value)
                    out.append(f"<dt>{escape(field)}</dt><dd>{escape(text)}</dd>")
                out.append("</dl>")
        for label, value in (("Consensus / unresolved", run["consensus"]),
                             ("Vstupná evidencia", run["evidence"]),
                             ("Zdroje a súhrn behu", {"sources": run["sources"],
                                                     "summary": run["summary"]})):
            text = json.dumps(value, ensure_ascii=False, indent=2)
            out.append(f"<details><summary>{label}</summary>"
                       f'<pre style="white-space:pre-wrap;overflow-wrap:anywhere">'
                       f"{escape(text)}</pre></details>")
        out.append("</details>")
    out.append("</details>")
    return "".join(out)
