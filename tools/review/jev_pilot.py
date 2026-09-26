# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Read-only, reproducible Jev pilot for preferred Slovak word divisions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from slabika import hyphenate  # noqa: E402
from slabika.morphology import get_morphology  # noqa: E402
from slabika.syllabify import _lexical_znovu_compound, _strip_prefix  # noqa: E402

# Same TypeSafe SystemOne endpoint and model pin as Object Repertory.
API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"

SEED = 20260926
OUT = ROOT / "scratch" / "jev_pilot_20260926"
RULES = ROOT / "docs" / "pravidla-delenia-slov.md"
CORPUS = ROOT / "tests" / "data" / "translatemaster_hyphenation_working.sqlite"
REVIEW = ROOT / "tests" / "data" / "review_decisions.sqlite"
TASK = (
    "Audit Slovak TYPOGRAPHIC word division at the end of a line, not spoken syllabification. "
    "For each candidate, decide whether ALL and ONLY its marked preferred breakpoints "
    "are appropriate under the supplied project paraphrase of PSP. A legal but "
    "non-preferred/contextual break does not satisfy preferred output. A single "
    "consonant may not be left alone at the beginning of a line. Inspect the actual "
    "word and its morphemes; do not assume an output is correct because a computer made it. "
    "If pronunciation, etymology or morphology is unclear, avoid a confident verdict. "
    "Each case is independent; do not infer validity from the other cases."
)


def resolve_api_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if key or sys.platform != "win32":
        return key
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
            value, _ = winreg.QueryValueEx(env, "TYPESAFE_API_KEY")
    except FileNotFoundError:
        return None
    return value if isinstance(value, str) and value else None


def call_api(payload, key, timeout):
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"TypeSafe API HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc
    if not isinstance(result.get("answers"), dict):
        raise ValueError("TypeSafe response has no answers map")
    return result


def make_cases():
    with sqlite3.connect(f"file:{CORPUS.as_posix()}?mode=ro", uri=True) as db:
        forms = sorted({row[0] for row in db.execute("SELECT form FROM forms")
                        if row[0].islower() and row[0].isalpha() and 6 <= len(row[0]) <= 20})
    rng = random.Random(SEED)
    words = rng.sample(forms, 100)
    controls = set(rng.sample([word for word in words if word[0].lower() not in "aáäeéiíoóôuúyý"], 20))
    cases = []
    for word in words:
        preferred = hyphenate(word, separator="·")
        cases.append({"word": word, "candidate": preferred, "kind": "engine"})
        if word in controls:
            cases.append({"word": word, "candidate": word[0] + "·" + word[1:],
                          "kind": "invalid_control", "paired_engine": preferred})
    rng.shuffle(cases)
    for index, case in enumerate(cases, 1):
        case["id"] = f"Q{index:03d}"
    return cases


def make_family_cases():
    with sqlite3.connect(f"file:{REVIEW.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute(
            "SELECT form, expected_hyphenation, engine_hyphenation FROM decisions "
            "WHERE COALESCE(is_deleted, 0) = 0 AND expected_hyphenation IS NOT NULL"
        )
        family = sorted((form, expected, prior) for form, expected, prior in rows
                        if form.lower().startswith("znovuz"))
    cases = []
    for form, expected, prior in family:
        preferred = hyphenate(form, separator="·")
        if preferred.lower() != expected.replace("|", "·").lower():
            raise ValueError(f"current engine differs from human review: {form}")
        cases.append({"id": f"Q{len(cases) + 1:03d}", "word": form,
                      "candidate": preferred, "kind": "repaired", "human": expected})
    for form, expected, prior in family:
        if prior and prior.lower() != expected.lower():
            cases.append({"id": f"Q{len(cases) + 1:03d}", "word": form,
                          "candidate": prior.replace("|", "·"), "kind": "prior",
                          "human": expected})
    return cases


def request(cases, rules, with_morphology=False):
    state_cases = {case["id"]: {"word": case["word"], "division": case["candidate"]}
                   for case in cases}
    if with_morphology:
        for case in cases:
            state_cases[case["id"]]["morphology_hypotheses"] = case["hypotheses"]
    return {
        "model": MODEL,
        "state": {"task": TASK, "psp_paraphrase": rules,
                  "cases": state_cases,
                  **({"hypotheses_note": "Morphological analyses are fallible proposals, NOT verdicts or prescribed division points. Compare them critically against PSP and the word; the same proposals are shown for every division of the same word."} if with_morphology else {})},
        "questions": {
            case["id"]: {"type": "noul",
                         "instructions": f"Is cases.{case['id']}.division a correct complete PREFERRED typographic division of cases.{case['id']}.word under psp_paraphrase?",
                         "criteria": {
                             "true": "Exactly the appropriate preferred breakpoints are marked, with no incorrect or missing preferred breakpoints.",
                             "false": "At least one marked breakpoint is wrong, or a preferred breakpoint is missing; a merely contextual variant is not preferred."}}
            for case in cases},
    }


def run(out, batch_size=10, family=False):
    if batch_size < 1 or batch_size > 20:
        raise ValueError("batch_size must be 1..20")
    cases = make_family_cases() if family else make_cases()
    rules = RULES.read_text(encoding="utf-8")
    source = REVIEW if family else CORPUS
    manifest = {"seed": SEED, "model": MODEL, "rules_sha256": hashlib.sha256(rules.encode()).hexdigest(),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "task": TASK, "cases": cases}
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("pilot sample, rules, model or corpus changed; refusing to mix results")
    else:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result_path = out / "results.jsonl"
    completed = {}
    if result_path.exists():
        for line in result_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["id"] in completed or row["id"] not in {case["id"] for case in cases}:
                raise ValueError("duplicate or unknown saved result")
            completed[row["id"]] = row
    pending = [case for case in cases if case["id"] not in completed]
    if not pending:
        print("Pilot already complete")
        return
    key = resolve_api_key()
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is not configured")
    with result_path.open("a", encoding="utf-8") as output:
        for start in range(0, len(pending), batch_size):
            batch = pending[start:start + batch_size]
            answer = call_api(request(batch, rules), key, timeout=180)
            if answer.get("model") != MODEL or set(answer["answers"]) != {case["id"] for case in batch}:
                raise ValueError("unexpected Jev model or question ids")
            rows = []
            for case in batch:
                score = float(answer["answers"][case["id"]]["noul"])
                if not 0 <= score <= 1:
                    raise ValueError("score outside [0, 1]")
                rows.append({"id": case["id"], "score_correct": score,
                             "usage": answer.get("usage")})
            for row in rows:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            print(f"{len(completed) + start + len(batch)}/{len(cases)}", flush=True)


def run_prompt_experiment(out):
    """Compare independent single-case prompts against PSP-adjudicated divisions."""
    prompts = {
        "baseline": TASK,
        "checklist": (
            "Judge the PREFERRED Slovak typographic division, not spoken syllables. "
            "Independently check every marked boundary and look for missing preferred boundaries. "
            "Apply relevant rules from the supplied PSP paraphrase, including morphology only "
            "when justified by the word itself. Do not mistake a merely permissible variant "
            "for the preferred one. If evidence is insufficient, be uncertain."
        ),
        "counterfactual": (
            "Judge the PREFERRED Slovak typographic division, not spoken syllables. "
            "First independently consider how you would divide this word under the supplied "
            "PSP paraphrase; then compare your division with the candidate, checking for both "
            "extra and missing breakpoints. Do not assume the candidate is the engine output "
            "or infer correctness from its formatting. If several divisions remain plausible "
            "and preference is unclear, be uncertain."
        ),
    }
    with sqlite3.connect(f"file:{REVIEW.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute(
            "SELECT form, family, psp_hyphenation, chlebikova_hyphenation, psp_reference "
            "FROM psp_comparisons WHERE engine_current_verdict = 'correct' "
            "AND chlebikova_verdict = 'incorrect' AND form = lower(form)"
        ).fetchall()
    rng = random.Random(20260926)
    rng.shuffle(rows)
    cases, families = [], set()
    for word, family, correct, incorrect, reference in rows:
        if family in families or not 7 <= len(word) <= 20:
            continue
        truth = len(cases) % 2 == 0
        candidate = correct if truth else incorrect
        if candidate.replace("·", "").lower() != word.lower():
            continue
        families.add(family)
        cases.append({"id": f"P{len(cases) + 1:03d}", "word": word,
                      "candidate": candidate, "expected_correct": truth,
                      "psp_reference": reference, "family": family})
        if len(cases) == 20:
            break
    if len(cases) != 20:
        raise ValueError("fewer than 20 distinct PSP-adjudicated families")
    rules = RULES.read_text(encoding="utf-8")
    manifest = {"seed": 20260926, "model": MODEL, "rules_sha256": hashlib.sha256(rules.encode()).hexdigest(),
                "review_sha256": hashlib.sha256(REVIEW.read_bytes()).hexdigest(),
                "prompts": prompts, "cases": cases}
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("prompt experiment inputs changed; refusing to mix results")
    else:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result_path = out / "results.jsonl"
    completed = {}
    if result_path.exists():
        for line in result_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            pair = row["arm"], row["id"]
            if pair in completed or row["arm"] not in prompts or row["id"] not in {c["id"] for c in cases}:
                raise ValueError("duplicate or unknown saved result")
            completed[pair] = row
    pending = [(arm, case) for case in cases for arm in prompts if (arm, case["id"]) not in completed]
    if not pending:
        print("Prompt experiment already complete")
        return
    key = resolve_api_key()
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is not configured")
    with result_path.open("a", encoding="utf-8") as output:
        for index, (arm, case) in enumerate(pending, len(completed) + 1):
            payload = request([case], rules)
            payload["state"]["task"] = prompts[arm]
            answer = call_api(payload, key, timeout=180)
            if answer.get("model") != MODEL or set(answer["answers"]) != {case["id"]}:
                raise ValueError("unexpected Jev model or question ids")
            score = float(answer["answers"][case["id"]]["noul"])
            if not 0 <= score <= 1:
                raise ValueError("score outside [0, 1]")
            output.write(json.dumps({"arm": arm, "id": case["id"], "score_correct": score,
                                     "usage": answer.get("usage")}, ensure_ascii=False) + "\n")
            output.flush()
            print(f"{index}/60 {arm} {case['id']}", flush=True)


def run_morph_experiment(out, batch_size=8):
    """Paired A/B on fixed plausible errors; never modifies human review or engine."""
    if not 1 <= batch_size <= 20:
        raise ValueError("batch_size must be 1..20")
    family = json.loads((ROOT / "scratch" / "jev_znovuz_20260926" / "manifest.json").read_text(encoding="utf-8"))
    repaired = {case["word"]: case for case in family["cases"] if case["kind"] == "repaired"}
    prior = {case["word"]: case for case in family["cases"] if case["kind"] == "prior"}
    rng = random.Random(20260926)
    stems = set()
    pairs = []
    for word in rng.sample(sorted(prior), len(prior)):
        if word.lower() == "znovuzoslaný":  # disputed, not a gold positive
            continue
        stem = word.lower()[5:9]
        if stem in stems:
            continue
        stems.add(stem)
        pairs.append((word, repaired[word]["candidate"], prior[word]["candidate"], "human_provisional"))
        if len(pairs) == 5:
            break
    with sqlite3.connect(f"file:{REVIEW.as_posix()}?mode=ro", uri=True) as db:
        for word in ("mahagónovohneda", "podruhýkrát", "archeológ", "afrodiziakum"):
            expected, old = db.execute(
                "SELECT expected_hyphenation, engine_hyphenation FROM decisions WHERE form = ?", (word,)
            ).fetchone()
            current = hyphenate(word, separator="·")
            if current.lower() != expected.replace("|", "·").lower() or old.lower() == expected.lower():
                raise ValueError(f"PSP pair no longer valid: {word}")
            pairs.append((word, current, old.replace("|", "·"), "psp_adjudicated"))
    morphology = get_morphology()
    cases = []
    for word, correct, incorrect, gold in pairs:
        hypotheses = ["Undivided lexical whole (no morphological seam asserted)",
                      "Corpus-induced morphs: " + " | ".join(morphology.parse(word))]
        compound = _lexical_znovu_compound(word)
        if compound:
            first, second = compound
            hypotheses.append("Attested compound head: " + first + " | " + second)
            prefix, remainder = _strip_prefix(second)
            if prefix:
                hypotheses.append("Possible nested prefix: " + first + " | " + prefix + " | " + remainder)
        else:
            prefix, remainder = _strip_prefix(word)
            if prefix:
                hypotheses.append("Prefix candidate: " + prefix + " | " + remainder)
        for candidate, truth in ((correct, True), (incorrect, False)):
            cases.append({"word": word, "candidate": candidate, "expected_correct": truth,
                          "gold": gold, "hypotheses": hypotheses})
    rng.shuffle(cases)
    for index, case in enumerate(cases, 1):
        case["id"] = f"M{index:03d}"
    rules = RULES.read_text(encoding="utf-8")
    manifest = {"seed": 20260926, "model": MODEL, "task": TASK,
                "rules_sha256": hashlib.sha256(rules.encode()).hexdigest(),
                "family_sha256": hashlib.sha256((ROOT / "scratch" / "jev_znovuz_20260926" / "manifest.json").read_bytes()).hexdigest(),
                "review_sha256": hashlib.sha256(REVIEW.read_bytes()).hexdigest(),
                "morphs_sha256": hashlib.sha256((ROOT / "src" / "slabika" / "data" / "morphs.json").read_bytes()).hexdigest(),
                "cases": cases}
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("experimental inputs changed; refusing to mix results")
    else:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result_path = out / "results.jsonl"
    completed = {}
    if result_path.exists():
        for line in result_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            key = (row["arm"], row["id"])
            if key in completed or row["id"] not in {case["id"] for case in cases}:
                raise ValueError("duplicate or unknown experimental result")
            completed[key] = row
    pending = [(arm, cases[i:i + batch_size]) for i in range(0, len(cases), batch_size)
               for arm in ("baseline", "morphology")
               if any((arm, case["id"]) not in completed for case in cases[i:i + batch_size])]
    if not pending:
        print("Experiment already complete")
        return
    key = resolve_api_key()
    if not key:
        raise RuntimeError("TYPESAFE_API_KEY is not configured")
    with result_path.open("a", encoding="utf-8") as output:
        for arm, batch in pending:
            batch = [case for case in batch if (arm, case["id"]) not in completed]
            answer = call_api(request(batch, rules, arm == "morphology"), key, timeout=180)
            if answer.get("model") != MODEL or set(answer["answers"]) != {case["id"] for case in batch}:
                raise ValueError("unexpected Jev model or question ids")
            rows = []
            for case in batch:
                score = float(answer["answers"][case["id"]]["noul"])
                if not 0 <= score <= 1:
                    raise ValueError("score outside [0, 1]")
                rows.append({"arm": arm, "id": case["id"], "score_correct": score,
                             "usage": answer.get("usage")})
            for row in rows:
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            print(f"{arm}: {len(batch)} answers", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUT)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--family-znovuz", action="store_true")
    parser.add_argument("--morph-experiment", action="store_true")
    parser.add_argument("--prompt-experiment", action="store_true")
    args = parser.parse_args()
    if args.prompt_experiment:
        experiment_out = ROOT / "scratch" / "jev_prompts_20260926" if args.output_dir == OUT else args.output_dir
        run_prompt_experiment(experiment_out)
    elif args.morph_experiment:
        experiment_out = ROOT / "scratch" / "jev_morph_ab_20260926" if args.output_dir == OUT else args.output_dir
        run_morph_experiment(experiment_out, args.batch_size)
    else:
        run(args.output_dir, args.batch_size, args.family_znovuz)
