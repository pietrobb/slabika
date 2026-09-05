# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Persistent advisory history never rewrites Human or PSP authority."""

import copy
import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pytest

from slabika.review import ai_adjudication as AI
from slabika.review import server as REVIEW


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _verdict(form, preferred, choice, reason):
    return {
        "form": form, "choice": choice, "preferred": preferred,
        "permitted_variants": [preferred], "human_assessment": (
            "correct" if choice == "human" else "incorrect"),
        "engine_assessment": "correct" if choice == "engine" else "incorrect",
        "psp_reference": "PSP V.1", "morphological_analysis": "Test morphology",
        "pronunciation_assumption": "Test pronunciation", "reason": reason,
        "confidence": "high",
    }


@pytest.fixture
def result():
    # The external adjudication runner is deliberately not part of this repository, so
    # the transcript shape it emits is rebuilt here: one form per resolution outcome.
    divisions = {
        "maslo": ("ma·slo", "mas·lo"), "okno": ("o·kno", "ok·no"),
        "vesta": ("ve·sta", "ves·ta"), "lopta": ("lo·pta", "lop·ta"),
    }
    agreed_at = {"maslo": "independent", "okno": "cross_review",
                 "vesta": "reconciliation", "lopta": None}
    evidence = [{
        "form": form,
        "human": {"action": "correct", "expected_hyphenation": human,
                  "quoted_human_reason": "Historical Human reason"},
        "engine_modes": {"preferred": engine}, "existing_psp_evidence": None,
        "engine_morphemes": [], "induced_morphology": {"parts": [form]},
        "rmss_exact_entries": [], "sapfo_snk_analyses": [], "sapfo_runtime_analyses": [],
    } for form, (human, engine) in divisions.items()]

    rounds, disputed = {}, list(divisions)
    for stage in AI.STAGES:
        if not disputed:
            break
        # Only outstanding disputes reach a later round; B concedes at its agreement stage.
        rounds[stage] = {key: {form: _verdict(
            form, divisions[form][0 if key == "A" or agreed_at[form] == stage else 1],
            "human" if key == "A" or agreed_at[form] == stage else "engine",
            f"{key} reason in {stage} for {form}") for form in disputed} for key in AI.MODELS}
        disputed = [form for form in disputed if agreed_at[form] != stage]

    consensus = []
    for form in divisions:
        stage = agreed_at[form] or AI.STAGES[-1]
        # Consensus reuses the round verdict objects, exactly as the runner emits them.
        positions = {key: rounds[stage][key][form] for key in AI.MODELS}
        verdict = positions["A"] if agreed_at[form] else None
        consensus.append({
            "form": form,
            "status": AI.STATUSES[AI.STAGES.index(stage) if agreed_at[form] else -1],
            "verdict": verdict,
            "supporting_model_verdicts": positions if verdict is not None else None,
            "final_model_positions": positions if verdict is None else None})

    return {
        "contract": "Model consensus is advisory evidence, not a PSP verdict.",
        "system_contract": "Offline test contract", "rules_text": "Offline test rules",
        "consensus_scope": "choice + preferred + complete permitted-variant set",
        "models": {key: {"label": "Reviewer " + key, "model": "model-" + key}
                   for key in AI.MODELS},
        "rounds": rounds, "consensus": consensus,
        "summary": {"forms": len(divisions), **{status: sum(
            item["status"] == status for item in consensus) for status in AI.STATUSES}},
        "created_at": "2026-08-25T12:30:00+00:00", "evidence": evidence,
        "evidence_sha256": _digest(evidence), "sources": {"rules_sha256": "abc123"}}


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "review_decisions.sqlite"
    with sqlite3.connect(path) as connection:
        connection.executescript(REVIEW.DECISION_SCHEMA)
        connection.execute("""INSERT INTO decisions
            (form, action, expected_hyphenation, engine_hyphenation, engine_syllabification,
             reason, engine_version, decided_at)
            VALUES ('maslo', 'correct', 'ma·slo', 'mas·lo', 'mas·lo', 'Human only', '1', 'old')""")
        connection.execute("""INSERT INTO decision_log
            (form, operation, engine_version, logged_at) VALUES ('maslo', 'decide', '1', 'old')""")
        psp = {row[1]: (2 if row[2] == "INTEGER" else "preserve")
               for row in connection.execute("PRAGMA table_info(psp_comparisons)")}
        psp.update(form="maslo", audit_id="psp-test", psp_variants='["mas·lo"]',
                   engine_current_verdict="correct", chlebikova_verdict="correct",
                   comparison_outcome="both_correct", verdict="both_match_psp")
        columns = ",".join(psp)
        connection.execute(f"INSERT INTO psp_comparisons ({columns}) VALUES "
                           f"({','.join('?' for _ in psp)})", list(psp.values()))
        connection.execute("""INSERT INTO psp_comparison_log
            (form, audit_id, operation, previous_json, supersession_reason, replaced_at)
            VALUES ('maslo', 'psp-test', 'replace', '{}', 'PSP only', 'old')""")
        connection.execute("""INSERT INTO psp_unresolved_classifications VALUES
            ('maslo', 'psp-test', 'foreign_pronunciation', 'Keep classification', 'old')""")
        connection.execute("""INSERT INTO psp_audit_runs VALUES
            ('psp-test', 'engine-ref', 'tex-ref', 2, 3, 100, 1, 'building', 'old')""")
        connection.execute("""INSERT INTO psp_audit_items VALUES
            ('psp-test', 1, 'maslo', 'ma·slo', 'ma·slo', 'mas·lo')""")
        connection.execute("UPDATE psp_audit_runs SET status='frozen'")
    return path


def _normative_snapshot(db):
    with sqlite3.connect(db) as connection:
        tables = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'ai_%'")]
        return {table: connection.execute(f'SELECT * FROM "{table}"').fetchall()
                for table in tables}


def test_persist_full_transcript_idempotency_and_unchanged_normative_rows(db, result):
    before = _normative_snapshot(db)
    run_id = AI.persist_run(db, result)
    assert run_id == _digest(result)
    reordered = dict(reversed(list(result.items())))
    assert AI.persist_run(db, reordered) == run_id
    assert _normative_snapshot(db) == before
    with sqlite3.connect(db) as connection:
        transcript, = connection.execute(
            "SELECT transcript_json FROM ai_adjudication_runs").fetchone()
        assert json.loads(transcript) == result
        assert connection.execute("SELECT count(*) FROM ai_adjudication_items").fetchone() == (4,)
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert "ai_adjudication_items_form" in str(connection.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM ai_adjudication_items WHERE form='maslo'").fetchall())


def test_readonly_history_contains_both_positions_and_all_applicable_rounds(db, result):
    AI.persist_run(db, result)
    before = db.read_bytes()
    for form, status, stages in (
        ("maslo", AI.STATUSES[0], AI.STAGES[:1]),
        ("okno", AI.STATUSES[1], AI.STAGES[:2]),
        ("vesta", AI.STATUSES[2], AI.STAGES),
        ("lopta", AI.STATUSES[3], AI.STAGES),
    ):
        run, = AI.get_form_history(db, form)
        assert run["status"] == status
        assert set(run["rounds"]) == set(stages)
        assert run["models"] == result["models"]
        assert run["sources"] == result["sources"]
        for stage in stages:
            for key in AI.MODELS:
                assert run["rounds"][stage][key] == result["rounds"][stage][key][form]
        assert set(run["positions"]) == {"A", "B"}
        if form == "lopta":
            assert run["consensus"]["verdict"] is None
            assert run["positions"]["A"]["choice"] == "human"
            assert run["positions"]["B"]["choice"] == "engine"
    assert AI.get_form_history(db, "MASLO") == []  # no silent recasing of evidence
    assert AI.get_form_history(db, "' OR 1=1 --") == []
    assert db.read_bytes() == before


def test_changed_transcript_appends_without_replacing_history(db, result):
    first = AI.persist_run(db, result)
    updated = copy.deepcopy(result)
    updated["created_at"] = "2026-08-25T12:31:00+00:00"
    second = AI.persist_run(db, updated)
    assert first != second
    assert AI.persist_run(db, result) == first
    assert [run["run_id"] for run in AI.get_form_history(db, "maslo")] == [second, first]


@pytest.mark.parametrize("table", ["ai_adjudication_runs", "ai_adjudication_items"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_sql_history_is_immutable(db, result, table, operation):
    AI.persist_run(db, result)
    with sqlite3.connect(db) as connection:
        sql = f"DELETE FROM {table}" if operation == "DELETE" else f"UPDATE {table} SET run_id='x'"
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(sql)
    assert len(AI.get_form_history(db, "maslo")) == 1


def test_readers_do_not_create_database_or_schema(tmp_path, db):
    missing = tmp_path / "missing.sqlite"
    assert AI.get_form_history(missing, "maslo") == []
    assert not missing.exists()
    before = db.read_bytes()
    assert AI.get_form_history(db, "maslo") == []
    assert "Bez uložených" in AI.form_history_html(db, "maslo")
    assert db.read_bytes() == before


@pytest.mark.parametrize("damage", [
    "missing_models", "missing_evidence", "missing_sources", "missing_created_at",
    "bad_timestamp", "bad_model", "duplicate_evidence", "bad_evidence_hash",
    "missing_round", "extra_round_form", "missing_reason", "bad_preferred",
    "bad_assessment", "consensus_status", "consensus_reason", "consensus_positions",
    "false_resolution", "bad_summary", "nonfinite",
])
def test_invalid_transcripts_are_rejected_before_database_creation(tmp_path, result, damage):
    value = copy.deepcopy(result)
    if damage.startswith("missing_") and damage.split("missing_", 1)[1] in value:
        del value[damage.split("missing_", 1)[1]]
    elif damage == "bad_timestamp":
        value["created_at"] = "not a timestamp"
    elif damage == "bad_model":
        value["models"]["B"]["model"] = ""
    elif damage == "duplicate_evidence":
        value["evidence"].append(value["evidence"][0])
    elif damage == "bad_evidence_hash":
        value["evidence_sha256"] = "tampered"
    elif damage == "missing_round":
        del value["rounds"]["cross_review"]
    elif damage == "extra_round_form":
        value["rounds"]["reconciliation"]["B"]["maslo"] = value["rounds"]["independent"]["B"]["maslo"]
    elif damage in {"missing_reason", "bad_preferred", "bad_assessment"}:
        field, replacement = {"missing_reason": ("reason", ""),
                              "bad_preferred": ("preferred", "wrong"),
                              "bad_assessment": ("human_assessment", "incorrect")}[damage]
        value["rounds"]["independent"]["A"]["maslo"][field] = replacement
    elif damage == "consensus_status":
        value["consensus"][0]["status"] = AI.STATUSES[-1]
    elif damage == "consensus_reason":
        value["consensus"][0]["verdict"] = {**value["consensus"][0]["verdict"], "reason": "fake"}
    elif damage == "consensus_positions":
        value["consensus"][0]["supporting_model_verdicts"] = None
    elif damage == "false_resolution":
        value["consensus"][-1]["verdict"] = value["rounds"]["reconciliation"]["A"]["lopta"]
    elif damage == "bad_summary":
        value["summary"]["forms"] += 1
    elif damage == "nonfinite":
        value["sources"]["invalid"] = float("nan")
    path = tmp_path / "must-not-create.sqlite"
    with pytest.raises(ValueError):
        AI.persist_run(path, value)
    assert not path.exists()


@pytest.mark.parametrize("existing", [False, True])
def test_item_failure_rolls_back_entire_run_and_new_schema(db, result, monkeypatch, existing):
    if existing:
        AI.persist_run(db, result)
        result["created_at"] = "2026-08-25T12:32:00+00:00"
    before = _normative_snapshot(db)
    monkeypatch.setattr(AI, "_SCHEMA", AI._SCHEMA + (
        """CREATE TRIGGER fail_item BEFORE INSERT ON ai_adjudication_items
           WHEN NEW.form='vesta' BEGIN SELECT RAISE(ABORT, 'injected failure'); END""",))
    with pytest.raises(sqlite3.IntegrityError, match="injected failure"):
        AI.persist_run(db, result)
    assert _normative_snapshot(db) == before
    with sqlite3.connect(db) as connection:
        if existing:
            assert connection.execute("SELECT count(*) FROM ai_adjudication_runs").fetchone() == (1,)
            assert connection.execute("SELECT count(*) FROM ai_adjudication_items").fetchone() == (4,)
        else:
            assert connection.execute(
                "SELECT name FROM sqlite_master WHERE name LIKE 'ai_adjudication_%'").fetchall() == []
        assert not connection.execute("SELECT 1 FROM sqlite_master WHERE name='fail_item'").fetchall()


def test_concurrent_identical_imports_are_idempotent(db, result):
    with ThreadPoolExecutor(max_workers=4) as executor:
        ids = list(executor.map(lambda _: AI.persist_run(db, result), range(4)))
    assert len(set(ids)) == 1
    assert len(AI.get_form_history(db, "lopta")) == 1


class _HTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, attrs))

    def handle_data(self, data):
        self.text.append(data)


def test_ui_full_round_visibility_and_escaping(db, result):
    attack = '<img src=x onerror="alert(1)"><script>alert(2)</script>&'
    result["models"]["B"]["model"] = attack
    result["models"]["A"]["label"] = attack
    # Deepcopy retains the producer's shared final verdict references.
    for stage in result["rounds"].values():
        for positions in stage.values():
            for verdict in positions.values():
                verdict["reason"] += attack
    result["evidence"][0]["human"]["quoted_human_reason"] = attack
    result["evidence_sha256"] = _digest(result["evidence"])
    result["sources"]["quoted_source"] = attack
    AI.persist_run(db, result)
    html = AI.form_history_html(db, "lopta") + AI.form_history_html(db, "maslo")
    parsed = _HTML()
    parsed.feed(html)
    text = "".join(parsed.text)
    assert attack in text
    assert attack not in html
    assert not {tag for tag, _ in parsed.tags} & {"img", "script", "button", "input", "a"}
    assert all(not name.startswith("on") for _, attrs in parsed.tags for name, _ in attrs)
    assert AI.ADVISORY in text
    assert "unresolved_model_disagreement" in text
    for stage in AI.STAGES:
        assert stage in text
        for key in AI.MODELS:
            assert f"{key} reason in {stage} for lopta" in text
    assert "consensus_independent" in text
    ui = REVIEW.UI_PATH.read_text(encoding="utf-8")
    assert 'const parts = [it.ai_adjudication_html || ""];' in ui
    assert 'row.querySelector(".state").innerHTML = parts.join' in ui
    assert '.ai-adjudication { white-space: normal; overflow-wrap: anywhere; }' in ui

def test_get_api_is_readonly_and_post_is_not_supported(db, result, monkeypatch):
    AI.persist_run(db, result)
    before = db.read_bytes()
    monkeypatch.setattr(REVIEW.Handler, "corpus", SimpleNamespace(decisions_path=db), raising=False)
    server = REVIEW.ReviewHTTPServer(("127.0.0.1", 0), REVIEW.Handler)
    base = f"http://127.0.0.1:{server.server_address[1]}/api/ai-adjudication"
    with ThreadPoolExecutor(max_workers=1) as executor:
        serving = executor.submit(server.serve_forever)
        try:
            with urlopen(base + "?" + urlencode({"form": "lopta"}), timeout=5) as response:
                assert response.headers["Cache-Control"] == "no-store"
                payload = json.load(response)
            assert payload["history"] == AI.get_form_history(db, "lopta")
            with urlopen(base + "?form=absent", timeout=5) as response:
                assert json.load(response) == {"history": []}
            with pytest.raises(HTTPError) as error:
                urlopen(base, timeout=5)
            assert error.value.code == 400
            request = Request(base, data=b'{}', headers={"Content-Type": "application/json"})
            with pytest.raises(HTTPError) as error:
                urlopen(request, timeout=5)
            assert error.value.code == 404
        finally:
            server.shutdown()
            serving.result()
            server.server_close()
    assert db.read_bytes() == before


def test_review_item_shows_exact_alias_histories_without_unrelated_forms(db, result, tmp_path):
    inventory = tmp_path / "inventory.sqlite"
    with sqlite3.connect(inventory) as connection:
        connection.executescript("""CREATE TABLE forms (form TEXT PRIMARY KEY);
            INSERT INTO forms VALUES ('maslo'), ('Maslo'), ('okno');
            CREATE TABLE adjudications (form TEXT PRIMARY KEY, review_status TEXT);""")
    corpus = REVIEW.Corpus(inventory, db)
    try:
        AI.persist_run(db, result)
        capitalized = json.loads(json.dumps(result, ensure_ascii=False).replace("mas", "Mas").replace("ma·", "Ma·"))
        capitalized["evidence_sha256"] = _digest(capitalized["evidence"])
        AI.persist_run(db, capitalized)
        before = db.read_bytes()
        html = corpus.item("maslo", None, None)["ai_adjudication_html"]
        assert all(html.count(f'<summary>AI adjudikácia — {form} (1)</summary>') == 1 for form in ("maslo", "Maslo"))
        assert html.count('class="ai-adjudication"') == 2 and "okno" not in html and db.read_bytes() == before
    finally:
        corpus.inventory.close()
        corpus.store.close()
