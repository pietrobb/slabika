# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Offline consensus/cache tests: no model credentials or network calls."""
import asyncio
import copy
import importlib.util
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from slabika.review import ai_division as AI


def analysis(form, preferred, vote="propose"):
    parts = preferred.split("·")
    boundaries = [{"basis": "syllabic",
                   "rule": "Offline rule"} for _ in parts[1:]]
    return {"form": form, "vote": vote, "preferred": preferred,
            "boundaries": boundaries, "identified_root": None,
            "morphological_analysis": "No verified stem", "language_assumption": "Slovak",
            "pronunciation_assumption": "Test pronunciation", "rejected_variants": [],
            "reason": "Offline explanation", "confidence": "high"}


class Engine:
    def __init__(self, key, responses):
        self.model, self.label, self.cache_namespace = "model-" + key, key, "test-v1"
        self.responses = copy.deepcopy(responses)
        self.calls, self.history = [], []

    def state(self):
        return copy.deepcopy(self.history)

    def restore(self, state):
        self.history = copy.deepcopy(state)

    async def call(self, prompt, schema, system=None):
        self.calls.append((prompt, copy.deepcopy(schema), system))
        if not self.responses:
            raise AssertionError("unexpected model call")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        self.history.append({"prompt": prompt, "response": copy.deepcopy(response)})
        return response


def response(*rows):
    return {"items": list(rows)}


def run(evidence, engines, cache=None, **kwargs):
    return asyncio.run(AI.run_batch(evidence, engines, "PSP rules", "Division contract",
                                   cache, **kwargs))


def independent_pair():
    return {key: Engine(key, [response(analysis("maslo", "mas·lo"))]) for key in ("A", "B")}


def counterproposal_pair():
    return {
        "A": Engine("A", [response(analysis("maslo", "ma·slo")),
                          response(analysis("maslo", "mas·lo", "accept"))]),
        "B": Engine("B", [response(analysis("maslo", "mas·lo")),
                          response(analysis("maslo", "mas·lo", "modify"))]),
    }


def test_blind_independence_stable_schema_and_own_conversations():
    engines = counterproposal_pair()
    report = run([{"form": "maslo", "language": {"detected": "slovak"}}], engines)
    assert report["consensus"][0]["status"] == "agreed_after_review"
    assert report["consensus"][0]["review_turn"] == 2
    assert report["consensus"][0]["preferred"] == "mas·lo"
    for engine in engines.values():
        initial = json.loads(engine.calls[0][0].split(AI.CACHE_BREAK)[1])
        assert initial == {"stage": "independent", "forms": ["maslo"]}
        assert engine.calls[0][1] == engine.calls[1][1] == AI.SCHEMA
        assert engine.calls[0][2] == engine.calls[1][2]
        assert engine.calls[0][0].split(AI.CACHE_BREAK)[0] == (
            engine.calls[1][0].split(AI.CACHE_BREAK)[0])
        assert len(engine.history) == 2
    assert [call["model"] for call in report["calls"]] == ["A", "B", "B", "A"]


def test_exact_independent_agreement_keeps_different_explanations():
    engines = independent_pair()
    engines["B"].responses[0]["items"][0]["reason"] = "Different justification"
    report = run([{"form": "maslo"}], engines)
    row, = report["consensus"]
    assert row["status"] == "agreed_independent"
    assert row["positions"]["A"]["reason"] != row["positions"]["B"]["reason"]
    assert len(report["calls"]) == 2


def test_typographic_only_contract_keeps_explanations_without_numeric_positions():
    fields = AI.SCHEMA["input_schema"]["properties"]["items"]["items"]["properties"]
    assert "syllabification" not in fields
    assert set(fields["boundaries"]["items"]["properties"]) == {"basis", "rule"}
    row = analysis("kazateľská", "ka·za·teľ·ská")
    row["identified_root"] = "kaz"
    row["morphological_analysis"] = "kaz-a-teľ-sk-á"
    assert AI._marked(row["preferred"], row["form"]) == [2, 4, 7]
    assert AI.validate(response(row), [row["form"]], "independent")[row["form"]] == {
        **row, "division_basis": "syllabic"}
    prompt = (Path(__file__).resolve().parents[1] /
              "tools/review/ai_division_prompt.txt").read_text(encoding="utf-8")
    assert "syllabification" not in prompt
    assert "offset" not in prompt
    assert "division_basis" not in prompt
    assert "Slabikovanie nevracaj" in prompt


def test_schema_puts_analysis_before_division_and_vote():
    order = list(AI.SCHEMA["input_schema"]["properties"]["items"]["items"]["properties"])
    assert "division_basis" not in order
    assert order.index("morphological_analysis") < order.index("boundaries") < (
        order.index("preferred")) < order.index("reason") < order.index("vote")


def test_model_facing_text_omits_licence_metadata_and_engine_examples():
    root = Path(__file__).resolve().parents[1]
    rules = AI.model_rules((root / "docs/pravidla-delenia-slov.md").read_text(encoding="utf-8"))
    assert "### 9.1" not in rules and "hyphenate(" not in rules and "break_points(" not in rules
    assert "## 9. Normatívna sila pravidiel" in rules and "## 10. Zdroj" in rules
    contract = AI.model_text((root / "tools/review/ai_division_prompt.txt")
                             .read_text(encoding="utf-8"))
    assert "SPDX" not in contract and contract.startswith("Si nezávislý")


def test_only_disputed_forms_are_reviewed():
    engines = {
        "A": Engine("A", [response(analysis("maslo", "mas·lo"), analysis("okno", "o·kno")),
                          response(analysis("okno", "ok·no", "accept"))]),
        "B": Engine("B", [response(analysis("maslo", "mas·lo"), analysis("okno", "ok·no"))]),
    }
    report = run([{"form": "maslo"}, {"form": "okno"}], engines)
    assert report["calls"][-1]["forms"] == ["okno"]
    assert len(report["calls"]) == 3
    assert all(row["preferred"] is not None for row in report["consensus"])


def test_swapping_candidates_is_not_agreement_and_budget_is_bounded():
    engines = counterproposal_pair()
    engines["A"].responses[1] = response(analysis("maslo", "ma·slo", "modify"))
    engines["B"].responses.append(response(analysis("maslo", "mas·lo", "modify")))
    report = run([{"form": "maslo"}], engines)
    assert report["consensus"][0]["status"] == "unresolved_disagreement"
    assert report["consensus"][0]["preferred"] is None
    assert len(report["calls"]) == 5


def test_uncertain_same_text_never_becomes_consensus():
    engines = independent_pair()
    engines["B"].responses[0]["items"][0]["vote"] = "uncertain"
    report = run([{"form": "maslo"}], engines)
    assert report["consensus"][0]["status"] == "uncertain"
    assert report["consensus"][0]["preferred"] is None


def test_invalid_acceptance_and_provider_failure_fail_closed(tmp_path):
    engines = counterproposal_pair()
    engines["B"].responses[1]["items"][0]["vote"] = "accept"  # Different from A's candidate.
    cache = AI.ResponseCache(tmp_path / "cache.sqlite")
    report = run([{"form": "maslo"}], engines, cache)
    assert report["consensus"][0]["status"] == "invalid_response"
    assert "acceptance changed" in report["calls"][-1]["error"]
    with sqlite3.connect(cache.path) as db:
        assert db.execute("SELECT count(*) FROM division_responses").fetchone() == (2,)
    engines = independent_pair()
    engines["B"].responses = [RuntimeError("provider unavailable")]
    report = run([{"form": "maslo"}], engines)
    assert report["consensus"][0]["status"] == "invalid_response"
    assert "provider unavailable" in report["calls"][-1]["error"]


def test_exact_request_cache_replays_conversation_without_model_calls(tmp_path):
    cache = AI.ResponseCache(tmp_path / "cache.sqlite")
    first = run([{"form": "maslo"}], counterproposal_pair(), cache)
    engines = {key: Engine(key, []) for key in ("A", "B")}
    second = run([{"form": "maslo"}], engines, cache)
    assert second["consensus"] == first["consensus"]
    assert second["cache"] == {"hits": 4, "requests": 4}
    assert not any(engine.calls for engine in engines.values())
    assert all(len(engine.history) == 2 for engine in engines.values())
    with sqlite3.connect(cache.path) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("DELETE FROM division_responses")


def test_resume_after_initial_calls_uses_cached_state(tmp_path):
    cache = AI.ResponseCache(tmp_path / "cache.sqlite")
    failed = counterproposal_pair()
    failed["B"].responses[1] = RuntimeError("interruption")
    run([{"form": "maslo"}], failed, cache)
    engines = counterproposal_pair()
    for engine in engines.values():
        engine.responses.pop(0)
    report = run([{"form": "maslo"}], engines, cache)
    assert report["cache"] == {"hits": 2, "requests": 4}
    assert report["consensus"][0]["status"] == "agreed_after_review"


@pytest.mark.parametrize("changed", ["rules", "contract", "schema", "model", "namespace", "evidence"])
def test_changed_inputs_cannot_reuse_stale_cache(tmp_path, monkeypatch, changed):
    cache = AI.ResponseCache(tmp_path / "cache.sqlite")
    run([{"form": "maslo"}], independent_pair(), cache)
    engines, evidence = independent_pair(), [{"form": "maslo"}]
    rules, contract = "PSP rules", "Division contract"
    if changed == "rules":
        rules += " changed"
    elif changed == "contract":
        contract += " changed"
    elif changed == "schema":
        schema = copy.deepcopy(AI.SCHEMA)
        schema["description"] += " changed"
        monkeypatch.setattr(AI, "SCHEMA", schema)
    elif changed == "evidence":
        evidence[0]["language"] = {"detected": "english"}
    elif changed == "model":
        engines["A"].model += " changed"
    else:
        engines["A"].cache_namespace += " changed"
    result = asyncio.run(AI.run_batch(evidence, engines, rules, contract, cache))
    assert result["cache"]["hits"] == (1 if changed in {"model", "namespace"} else 0)


@pytest.mark.parametrize("bad", ["spelling", "edge", "duplicate", "missing", "boundary_count",
                                  "boundary_rule", "basis", "reason", "vote", "stem", "confidence",
                                  "rejected_text", "rejected_status"])
def test_untrusted_batch_validation(bad):
    row = analysis("maslo", "mas·lo")
    data = response(row)
    if bad == "spelling":
        row["preferred"] = "ma·sloo"
    elif bad == "edge":
        row["preferred"] = "·maslo"
    elif bad == "duplicate":
        data["items"].append(copy.deepcopy(row))
    elif bad == "missing":
        del row["morphological_analysis"]
    elif bad == "boundary_count":
        row["boundaries"] = []
    elif bad == "boundary_rule":
        row["boundaries"][0]["rule"] = " "
    elif bad == "basis":
        row["division_basis"] = "morphemic"  # program-derived; model must not supply it
    elif bad == "reason":
        row["reason"] = " "
    elif bad == "vote":
        row["vote"] = "accept"
    elif bad == "stem":
        row["identified_root"] = []
    elif bad == "rejected_text":
        row["rejected_variants"] = "žiadne"
    elif bad == "rejected_status":
        row["rejected_variants"] = [{"variant": "ma·slo", "status": "maybe", "rule": "§4.2"}]
    else:
        row["confidence"] = ["high"]
    with pytest.raises(ValueError):
        AI.validate(data, ["maslo"], "independent")


def test_bad_rejected_variant_is_dropped_not_the_batch():
    # Operator 2026-10-01: a typo in a rejected variant drops only that variant.
    row = analysis("maslo", "mas·lo")
    good = {"variant": "ma·slo", "status": "forbidden", "rule": "§4.2"}
    row["rejected_variants"] = [
        good, dict(good), {"variant": "mas·lo", "status": "forbidden", "rule": "§4.2"},
        {"variant": "ma·sla", "status": "forbidden", "rule": "§4.2"}]
    result = AI.validate(response(row), ["maslo"], "independent")["maslo"]
    assert result["rejected_variants"] == [good]
    assert [d["variant"] for d in result["dropped_variants"]] == ["ma·slo", "mas·lo", "ma·sla"]
    assert result["preferred"] == "mas·lo"


def test_monoyllabic_and_mixed_boundaries():
    AI.validate(response(analysis("vlk", "vlk")), ["vlk"], "independent")
    row = analysis("neuplynul", "ne·uply·nul")
    row["boundaries"][0]["basis"] = "morphemic"
    row["rejected_variants"] = [
        {"variant": "neup·ly·nul", "status": "dispreferred", "rule": "§4.2"},
        {"variant": "neu·ply·nul", "status": "forbidden", "rule": "§3.1"},
        {"variant": "ne·uplynul", "status": "forbidden", "rule": "missing point"}]
    assert AI.validate(response(row), ["neuplynul"], "independent")["neuplynul"] == {
        **row, "division_basis": "mixed"}


def test_distinct_models_and_duplicate_inputs_are_rejected():
    engines = independent_pair()
    engines["B"].model = engines["A"].model
    with pytest.raises(ValueError, match="distinct"):
        run([{"form": "maslo"}], engines)
    with pytest.raises(ValueError, match="unique"):
        run([{"form": "maslo"}, {"form": "maslo"}], independent_pair())


def test_language_and_pronunciation_are_evidence_not_engine_division(monkeypatch):
    from slabika import foreign, language

    @dataclass
    class Reading:
        word: str
        language: str
        phones: str
        score: float
        spans: tuple

    monkeypatch.setattr(language, "language_scores", lambda _: (
        language.LanguageScore("english", 12.0), language.LanguageScore("slovak", 4.0)))
    monkeypatch.setattr(foreign, "reading_candidates", lambda _: ())
    evidence, = AI.collect_evidence(["people"], lambda form, lang: Reading(
        form, lang, "p i p l", 1.0, ((form, ("p", "i", "p", "l")),)))
    assert evidence["language"]["detected"] == "english"
    assert evidence["pronunciation"]["g2p"]["phones"] == "p i p l"
    assert evidence["pronunciation"]["g2p_status"] == "available"
    assert not {"engine_division", "morphology", "roots"}.intersection(evidence)
    evidence, = AI.collect_evidence(["people"], lambda *_: Reading(
        "wrong", "english", "p", 1.0, ()))
    assert evidence["pronunciation"]["g2p"] is None
    assert evidence["pronunciation"]["g2p_status"] == "unavailable"


@pytest.fixture
def cli():
    path = Path(__file__).resolve().parents[1] / "tools/review/ai_division.py"
    spec = importlib.util.spec_from_file_location("division_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def args(tmp_path):
    forms = tmp_path / "forms.json"
    rules = tmp_path / "rules.txt"
    prompt = tmp_path / "prompt.txt"
    forms.write_text('["maslo"]', encoding="utf-8")
    rules.write_text("PSP rules", encoding="utf-8")
    prompt.write_text("Division contract", encoding="utf-8")
    return SimpleNamespace(forms_file=forms, evidence_file=None, rules=rules, prompt=prompt,
                           adapter=tmp_path / "external_adapter.py",
                           model_a=None, model_b=None, batch_size=10, max_votes=3,
                           cache=tmp_path / "cache.sqlite", g2p=False, execute=False,
                           output=tmp_path / "output.json")


def test_prepare_cli_needs_no_provider_config_and_cannot_overwrite(cli, tmp_path, monkeypatch):
    options = args(tmp_path)
    monkeypatch.setattr(cli, "collect_evidence", lambda forms, _: [{"form": f} for f in forms])
    monkeypatch.setattr(cli, "load_factory", lambda *_: pytest.fail("provider loaded during prepare"))
    result = asyncio.run(cli.run(options))
    assert result["mode"] == "prepare"
    assert json.loads(options.output.read_text(encoding="utf-8")) == result
    assert not options.cache.exists()
    with pytest.raises(FileExistsError):
        asyncio.run(cli.run(options))
    options.output = options.forms_file
    with pytest.raises(ValueError, match="distinct"):
        asyncio.run(cli.run(options))


def test_cli_execute_uses_separate_batch_sessions_and_cache(cli, tmp_path, monkeypatch):
    options = args(tmp_path)
    options.execute = True
    monkeypatch.setattr(cli, "collect_evidence", lambda forms, _: [{"form": f} for f in forms])
    monkeypatch.setattr(cli, "load_factory", lambda *_: independent_pair)
    result = asyncio.run(cli.run(options))
    assert result["batches"][0]["consensus"][0]["status"] == "agreed_independent"
    options.output = tmp_path / "repeated.json"
    monkeypatch.setattr(cli, "load_factory", lambda *_: lambda: {
        key: Engine(key, []) for key in ("A", "B")})
    result = asyncio.run(cli.run(options))
    assert result["batches"][0]["cache"]["hits"] == 2


def test_external_adapter_receives_only_pipeline_parameters(cli, tmp_path):
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "def create_factory(*, system, model_a, model_b):\n"
        "    return lambda: (system, model_a, model_b)\n", encoding="utf-8")
    factory = cli.load_factory(adapter, "model-A", "model-B", "static")
    assert factory() == ("static", "model-A", "model-B")


def test_adapter_inside_repository_is_rejected_before_import(cli, tmp_path):
    options = args(tmp_path)
    options.execute = True
    options.adapter = cli.ROOT / "tools/review/ai_division.py"
    with pytest.raises(ValueError, match="outside the repository"):
        asyncio.run(cli.run(options))
    with pytest.raises(ValueError, match="outside the repository"):
        cli.load_factory(options.adapter, None, None, "static")
    assert not options.output.exists()
    assert not options.cache.exists()


def test_execute_requires_external_adapter(cli, tmp_path):
    options = args(tmp_path)
    options.execute, options.adapter = True, None
    with pytest.raises(ValueError, match="requires an external --adapter"):
        asyncio.run(cli.run(options))
    assert not options.output.exists()
