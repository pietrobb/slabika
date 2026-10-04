# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Versioned, append-only storage of dual-model word-division runs.

Every verdict points to the run that produced it, and every run points to the
exact rules text, prompt, response schema, both models and the engine build it
was compared with. A changed rules text is a new rule set, never an edit.
AI verdicts are advisory evidence; they never overwrite Human decisions.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import zlib
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .ai_division import digest

STATUSES = ("agreed_independent", "agreed_after_review", "uncertain",
            "unresolved_disagreement", "invalid_response")
AGREED = ("agreed_independent", "agreed_after_review")
TABLES = ("ai_rule_sets", "ai_prompts", "ai_schemas", "ai_models", "engine_versions",
          "ai_runs", "ai_verdicts", "ai_model_answers")

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS ai_rule_sets (
        rule_set_id INTEGER PRIMARY KEY,
        version TEXT NOT NULL UNIQUE,
        sha256 TEXT NOT NULL UNIQUE,
        text TEXT NOT NULL,
        source TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS ai_prompts (
        prompt_id INTEGER PRIMARY KEY,
        version TEXT NOT NULL UNIQUE,
        sha256 TEXT NOT NULL UNIQUE,
        text TEXT NOT NULL,
        source TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS ai_schemas (
        schema_id INTEGER PRIMARY KEY,
        version TEXT NOT NULL UNIQUE,
        sha256 TEXT NOT NULL UNIQUE,
        schema_json TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS ai_models (
        model_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        provider TEXT NOT NULL,
        model TEXT NOT NULL,
        options TEXT NOT NULL DEFAULT '',
        note TEXT NOT NULL DEFAULT '')""",
    """CREATE TABLE IF NOT EXISTS engine_versions (
        engine_version_id INTEGER PRIMARY KEY,
        package_version TEXT NOT NULL,
        git_commit TEXT NOT NULL,
        git_dirty INTEGER NOT NULL CHECK(git_dirty IN (0, 1)),
        tree_sha256 TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '',
        UNIQUE(package_version, git_commit, git_dirty, tree_sha256))""",
    """CREATE TABLE IF NOT EXISTS ai_runs (
        run_id TEXT PRIMARY KEY,
        rule_set_id INTEGER NOT NULL REFERENCES ai_rule_sets(rule_set_id),
        prompt_id INTEGER NOT NULL REFERENCES ai_prompts(prompt_id),
        schema_id INTEGER NOT NULL REFERENCES ai_schemas(schema_id),
        model_a_id INTEGER NOT NULL REFERENCES ai_models(model_id),
        model_b_id INTEGER NOT NULL REFERENCES ai_models(model_id),
        engine_version_id INTEGER NOT NULL REFERENCES engine_versions(engine_version_id),
        selection TEXT NOT NULL,
        seed INTEGER,
        forms_sha256 TEXT NOT NULL,
        source_sha256 TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT NOT NULL,
        summary_json TEXT NOT NULL,
        transcript_sha256 TEXT NOT NULL UNIQUE,
        transcript_zlib BLOB NOT NULL,
        retry_archive_zlib BLOB,
        note TEXT NOT NULL DEFAULT '',
        imported_at TEXT NOT NULL,
        CHECK(model_a_id <> model_b_id))""",
    """CREATE TABLE IF NOT EXISTS ai_verdicts (
        run_id TEXT NOT NULL REFERENCES ai_runs(run_id),
        form TEXT NOT NULL,
        batch INTEGER NOT NULL CHECK(batch >= 1),
        status TEXT NOT NULL CHECK(status IN ('agreed_independent', 'agreed_after_review',
            'uncertain', 'unresolved_disagreement', 'invalid_response')),
        preferred TEXT,
        review_turn INTEGER,
        engine_hyphenation TEXT NOT NULL,
        PRIMARY KEY(run_id, form),
        CHECK((preferred IS NOT NULL) = (status IN ('agreed_independent', 'agreed_after_review'))),
        CHECK(preferred IS NULL OR replace(preferred, '·', '') = form)
    ) WITHOUT ROWID""",
    "CREATE INDEX IF NOT EXISTS ai_verdicts_form ON ai_verdicts(form, run_id)",
    """CREATE TABLE IF NOT EXISTS ai_model_answers (
        run_id TEXT NOT NULL,
        form TEXT NOT NULL,
        model_id INTEGER NOT NULL REFERENCES ai_models(model_id),
        stage TEXT NOT NULL,
        preferred TEXT,
        vote TEXT,
        confidence TEXT,
        answer_json TEXT,
        error TEXT,
        UNIQUE(run_id, form, model_id, stage),
        FOREIGN KEY(run_id, form) REFERENCES ai_verdicts(run_id, form),
        CHECK(answer_json IS NOT NULL OR error IS NOT NULL))""",
    *(f"""CREATE TRIGGER IF NOT EXISTS {table}_no_{operation.lower()}
          BEFORE {operation} ON {table} BEGIN
              SELECT RAISE(ABORT, 'AI run history is immutable');
          END"""
      for table in TABLES for operation in ("UPDATE", "DELETE")),
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_schema(connection):
    for statement in _SCHEMA:
        connection.execute(statement)


def parse_model_name(name):
    """'gpt-6.1-sol[sub][high]' -> ('openai', 'gpt-6.1-sol', 'sub,high')."""
    model, _, rest = name.partition("[")
    options = ",".join(part.strip("[]") for part in ("[" + rest).split("][") if rest)
    provider = ("anthropic" if model.startswith("claude") else
                "openai" if model.startswith(("gpt", "o1", "o3", "o4")) else "unknown")
    return provider, model, options


def engine_version(root):
    """Package version, Git commit, dirty flag and content hash of the engine.

    The engine is src/slabika without the review console, which cannot change
    any division.
    """
    root = Path(root)
    package = root / "src" / "slabika"

    def git(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                              check=True).stdout.strip()

    lines = []
    for path in sorted(package.rglob("*")):
        if (path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
                and not path.is_relative_to(package / "review")):
            data_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{path.relative_to(root).as_posix()}\t{data_hash}")
    version = next(line.split("=", 1)[1].strip().strip("\"'") for line in
                   (root / "src/slabika/__init__.py").read_text(encoding="utf-8").splitlines()
                   if line.startswith("__version__"))
    return {"package_version": version, "git_commit": git("rev-parse", "HEAD"),
            "git_dirty": int(bool(git("status", "--porcelain", "--", "src/slabika",
                                      ":(exclude)src/slabika/review"))),
            "tree_sha256": sha256_text("\n".join(lines) + "\n")}


def _get_or_create(connection, table, key, version, sha, values):
    row = connection.execute(f"SELECT {key}, version FROM {table} WHERE sha256 = ?",
                             (sha,)).fetchone()
    if row is not None:
        if row[1] != version:
            raise ValueError(f"{table}: identical text already stored as {row[1]!r}")
        return row[0]
    if connection.execute(f"SELECT 1 FROM {table} WHERE version = ?", (version,)).fetchone():
        raise ValueError(f"{table}: version {version!r} already names a different text")
    columns = ", ".join(values)
    marks = ", ".join("?" * len(values))
    return connection.execute(f"INSERT INTO {table} ({columns}) VALUES ({marks})",
                              tuple(values.values())).lastrowid


def _model_id(connection, name):
    row = connection.execute("SELECT model_id FROM ai_models WHERE name = ?", (name,)).fetchone()
    if row is not None:
        return row[0]
    provider, model, options = parse_model_name(name)
    return connection.execute(
        "INSERT INTO ai_models (name, provider, model, options) VALUES (?, ?, ?, ?)",
        (name, provider, model, options)).lastrowid


def _engine_id(connection, engine):
    keys = ("package_version", "git_commit", "git_dirty", "tree_sha256")
    row = connection.execute(
        "SELECT engine_version_id FROM engine_versions WHERE package_version = ? AND "
        "git_commit = ? AND git_dirty = ? AND tree_sha256 = ?",
        tuple(engine[key] for key in keys)).fetchone()
    if row is not None:
        return row[0]
    return connection.execute(
        "INSERT INTO engine_versions (package_version, git_commit, git_dirty, tree_sha256, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (*(engine[key] for key in keys), engine.get("note", ""))).lastrowid


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def import_run(db_path, run_dir, *, run_id, rules_version, prompt_version, schema_version,
               engine, rules_source, prompt_source, rules_note="", prompt_note="",
               schema_note="", note="", relabel_note=""):
    """Validate a finished private run directory and append it atomically.

    The transcript's per-batch hashes must match the stored rules, prompt and
    schema texts, so a run can never be filed under a text it did not use.
    A version label differing from the one the run declared is accepted only
    with ``relabel_note`` explaining why; the note is kept in the run note.
    """
    run_dir = Path(run_dir)
    transcript = _read(run_dir / "transcript.json")
    comparison = _read(run_dir / "comparison.json")
    summary = _read(run_dir / "summary.json")
    archive_path = run_dir / "invalid_batches_archive.json"
    rules, prompt, schema = (transcript["rules_text"], transcript["system_contract"],
                             transcript["schema"])
    batches = transcript["batches"]
    models = batches[0]["models"]
    for batch in batches:
        if (batch["rules_sha256"], batch["prompt_sha256"], batch["schema_sha256"]) != (
                digest(rules), digest(prompt), digest(schema)):
            raise ValueError("a batch was produced with different rules, prompt or schema")
        if {key: value["model"] for key, value in batch["models"].items()} != {
                key: value["model"] for key, value in models.items()}:
            raise ValueError("a batch was produced with different models")
    engine_rows = {row["form"]: row for row in comparison}
    consensus = [(number, row) for number, batch in enumerate(batches, 1)
                 for row in batch["consensus"]]
    if [row["form"] for _, row in consensus] != [row["form"] for row in comparison]:
        raise ValueError("comparison does not cover the transcript forms in order")
    if summary["manifest"]["forms_sha256"] != digest([row["form"] for _, row in consensus]):
        raise ValueError("forms do not match the run manifest")
    blob = json.dumps(transcript, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    manifest = summary["manifest"]
    declared = manifest.get("versions") or {}
    for key, version in (("rules", rules_version), ("prompt", prompt_version),
                         ("schema", schema_version)):
        if declared.get(key) not in (None, version) and not relabel_note:
            raise ValueError(f"run declared {key} {declared[key]!r}, not {version!r}")
    if relabel_note:
        note = f"{note} Relabelled: {relabel_note}".strip()
    with closing(sqlite3.connect(db_path)) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        ensure_schema(connection)
        now = _now()
        rule_set_id = _get_or_create(connection, "ai_rule_sets", "rule_set_id", rules_version,
                                     sha256_text(rules), {
            "version": rules_version, "sha256": sha256_text(rules), "text": rules,
            "source": rules_source, "note": rules_note, "created_at": now})
        prompt_id = _get_or_create(connection, "ai_prompts", "prompt_id", prompt_version,
                                   sha256_text(prompt), {
            "version": prompt_version, "sha256": sha256_text(prompt), "text": prompt,
            "source": prompt_source, "note": prompt_note, "created_at": now})
        schema_text = json.dumps(schema, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"))
        schema_id = _get_or_create(connection, "ai_schemas", "schema_id", schema_version,
                                   sha256_text(schema_text), {
            "version": schema_version, "sha256": sha256_text(schema_text),
            "schema_json": schema_text, "note": schema_note, "created_at": now})
        model_ids = {key: _model_id(connection, models[key]["model"]) for key in ("A", "B")}
        connection.execute(
            """INSERT INTO ai_runs (run_id, rule_set_id, prompt_id, schema_id, model_a_id,
                   model_b_id, engine_version_id, selection, seed, forms_sha256, source_sha256,
                   started_at, finished_at, summary_json, transcript_sha256, transcript_zlib,
                   retry_archive_zlib, note, imported_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, rule_set_id, prompt_id, schema_id, model_ids["A"], model_ids["B"],
             _engine_id(connection, engine), manifest["selection"], manifest.get("seed"),
             manifest["forms_sha256"], manifest["source_sha256"], manifest["started_at"],
             summary["finished_at"], json.dumps(summary, ensure_ascii=False, sort_keys=True),
             hashlib.sha256(blob).hexdigest(), zlib.compress(blob, 9),
             zlib.compress(archive_path.read_bytes(), 9) if archive_path.exists() else None,
             note, now))
        connection.executemany(
            "INSERT INTO ai_verdicts VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(run_id, row["form"], number, row["status"], row["preferred"],
              row.get("review_turn"), engine_rows[row["form"]]["engine_after_run"])
             for number, row in consensus])
        answers = []
        for batch in batches:
            for call in batch["calls"]:
                items = (call.get("response") or {}).get("items")
                rows = {}
                for item in items if isinstance(items, list) else ():
                    if isinstance(item, dict) and isinstance(item.get("form"), str):
                        rows.setdefault(item["form"], item)
                for form in call["forms"]:
                    item = rows.get(form)
                    answers.append((
                        run_id, form, model_ids[call["model"]], call["stage"],
                        item.get("preferred") if item else None,
                        item.get("vote") if item else None,
                        item.get("confidence") if item else None,
                        json.dumps(item, ensure_ascii=False) if item else None,
                        call.get("error")))
        connection.executemany(
            "INSERT INTO ai_model_answers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", answers)
    return {"run_id": run_id, "verdicts": len(consensus), "answers": len(answers)}


def _has_tables(connection):
    names = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    return set(TABLES) <= names


def latest_verdicts(connection, forms):
    """Newest run's verdict per form, with the versions it was produced under."""
    if not forms or not _has_tables(connection):
        return {}
    result = {}
    latest_rules = connection.execute("SELECT MAX(rule_set_id) FROM ai_rule_sets").fetchone()[0]
    latest_prompt = connection.execute("SELECT MAX(prompt_id) FROM ai_prompts").fetchone()[0]
    forms = sorted(set(forms))
    for start in range(0, len(forms), 800):
        chunk = forms[start:start + 800]
        rows = connection.execute(
            f"""SELECT v.*, r.started_at, r.finished_at, r.rule_set_id, r.prompt_id,
                       r.model_a_id, r.model_b_id,
                       rs.version AS rules_version, p.version AS prompt_version,
                       s.version AS schema_version, ma.name AS model_a, mb.name AS model_b,
                       e.package_version, e.git_commit, e.git_dirty, e.tree_sha256
                FROM ai_verdicts AS v
                JOIN ai_runs AS r USING (run_id)
                JOIN ai_rule_sets AS rs ON rs.rule_set_id = r.rule_set_id
                JOIN ai_prompts AS p ON p.prompt_id = r.prompt_id
                JOIN ai_schemas AS s ON s.schema_id = r.schema_id
                JOIN ai_models AS ma ON ma.model_id = r.model_a_id
                JOIN ai_models AS mb ON mb.model_id = r.model_b_id
                JOIN engine_versions AS e ON e.engine_version_id = r.engine_version_id
                WHERE v.form IN ({",".join("?" * len(chunk))})
                ORDER BY r.started_at, r.run_id""", chunk)
        for row in rows:
            result[row["form"]] = dict(row) | {
                "rules_latest": row["rule_set_id"] == latest_rules,
                "prompt_latest": row["prompt_id"] == latest_prompt,
                "proposals": []}
    for verdict in result.values():
        if verdict["status"] in ("uncertain", "unresolved_disagreement"):
            verdict["proposals"] = _final_proposals(connection, verdict)
    return result


def _final_proposals(connection, verdict):
    """Each model's last valid division when the two did not settle on one."""
    rows = connection.execute(
        """SELECT a.model_id, m.name AS model, a.stage, a.preferred, a.vote, a.confidence
           FROM ai_model_answers AS a JOIN ai_models AS m USING (model_id)
           WHERE a.run_id = ? AND a.form = ? AND a.preferred IS NOT NULL AND a.error IS NULL""",
        (verdict["run_id"], verdict["form"])).fetchall()
    turn = lambda stage: 0 if stage == "independent" else int(stage.rsplit("_", 1)[1])  # noqa: E731
    last = {}
    for row in sorted(rows, key=lambda row: turn(row["stage"])):
        last[row["model_id"]] = row
    order = [verdict["model_a_id"], verdict["model_b_id"]]
    return [{"model": last[model]["model"], "preferred": last[model]["preferred"],
             "vote": last[model]["vote"], "confidence": last[model]["confidence"]}
            for model in order if model in last]


def model_answers(connection, run_id, form):
    if not _has_tables(connection):
        return []
    rows = connection.execute(
        """SELECT m.name AS model, a.stage, a.preferred, a.vote, a.confidence,
                  a.answer_json, a.error
           FROM ai_model_answers AS a JOIN ai_models AS m USING (model_id)
           WHERE a.run_id = ? AND a.form = ?
           ORDER BY a.stage <> 'independent', a.stage, a.model_id""", (run_id, form))
    answers = []
    for row in rows:
        answer = json.loads(row["answer_json"]) if row["answer_json"] else {}
        # Schema s1 named single points (excluded_points), s2 names whole variants.
        rejected = answer.get("rejected_variants") or [
            {"variant": item.get("point"), "status": item.get("status"), "rule": item.get("rule")}
            for item in answer.get("excluded_points") or [] if isinstance(item, dict)]
        answers.append({"model": row["model"], "stage": row["stage"],
                        "preferred": row["preferred"], "vote": row["vote"],
                        "confidence": row["confidence"], "reason": answer.get("reason"),
                        "language": answer.get("language_assumption"),
                        "pronunciation": answer.get("pronunciation_assumption"),
                        "root": answer.get("identified_root"),
                        "morphology": answer.get("morphological_analysis"),
                        "boundaries": answer.get("boundaries") or [],
                        "rejected": rejected,
                        "error": row["error"]})
    return answers
