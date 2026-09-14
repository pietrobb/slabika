# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Snapshot public hyphenation in a fresh CLI process; never modify runtime data.

python tools/compare_composita.py --output scratch/before.json
python tools/compare_composita.py --inventory scratch/grammar.json \
    --baseline scratch/before.json --output scratch/after.json --check

Engine/runtime changes require --allow-engine-changes. Corpus additions/removals
require --allow-corpus-changes. Neither flag approves output changes: --check
exits 1 unless every change matches an exact JSON allowlist entry with precisely
{form, before, after}. Copy reviewed entries from the report's changes array;
null denotes an absent form. Stale approvals also fail. No allowlist means [].
Exit 2 means invalid/incomparable input. Legacy string snapshots remain usable
with compare(), but cannot establish full-API release readiness in the CLI.
"""

from __future__ import annotations
from functools import lru_cache
import argparse
import hashlib
import importlib
import json
import platform
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SCHEMA_VERSION = 2
INVENTORY_KEY = "src/slabika/data/composita.json"
MODES = {
    "preferred": {},
    "all_points": {"all_points": True},
    "contextual": {"contextual": True},
    "all_contextual": {"all_points": True, "contextual": True},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def logical_hash(value) -> str:
    return digest(canonical(value).encode("utf-8"))


def runtime_files() -> dict[str, str]:
    """Fingerprint the entire package, not just syllabify.py (ignore bytecode)."""
    paths = [ROOT / "pyproject.toml"]
    paths.extend(
        p
        for p in (ROOT / "src/slabika").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}
    )
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(paths)}


def engine_files(files: dict) -> dict:
    # Only this inventory may vary without the engine/runtime opt-in.
    return {k: v for k, v in files.items() if k != INVENTORY_KEY}


def public_output(api, form: str) -> dict:
    return {
        **{
            mode: {
                "hyphenate": api.hyphenate(form, **flags),
                "break_points": api.break_points(form, **flags),
            }
            for mode, flags in MODES.items()
        },
        "divisions": api.divisions(form),
    }


def snapshot(corpus: Path, inventory: Path | None = None):
    """Use a fresh process for each engine revision; restore candidate globals."""
    files = runtime_files()
    engine = importlib.import_module("slabika.syllabify")
    api = importlib.import_module("slabika")
    source = inventory or ROOT / INVENTORY_KEY
    raw = source.read_bytes()
    data = json.loads(raw)
    replacements = {
        "_GENERATED_FIRST_MEMBERS": frozenset(
            m for m, kind in data["first_members"].items() if kind != "cited"
        ),
        "_INFERRED_FIRST_MEMBERS": frozenset(
            m for m, kind in data["first_members"].items() if kind == "noun stem"
        ),
        "_GENERATED_HEADS": dict(data["heads"]),
        **{
            name: lru_cache(maxsize=4096)(getattr(engine, name))
            for name in ("_strip_prefix", "_generated_compositum", "_heads_a_compositum")
        },
        "_GENERATED_HEAD_FORMS": (
            {k: frozenset(v) for k, v in data["head_forms"].items()}
            if data.get("schema_version") == 2 or "head_forms" in data
            else None
        ),
        "_GENERATED_HEAD_PARADIGMS": data["head_paradigms"]
        if data.get("schema_version") == 3
        else None,
    }
    missing = object()
    originals = {k: getattr(engine, k, missing) for k in replacements}
    db = sqlite3.connect(corpus.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        forms = [r[0] for r in db.execute("select form from forms order by form")]
    finally:
        db.close()
    if (
        not forms
        or any(not isinstance(f, str) or not f for f in forms)
        or len(forms) != len(set(forms))
    ):
        raise ValueError("corpus must contain unique nonempty string forms and not be empty")
    try:
        for key, value in replacements.items():
            setattr(engine, key, value)
        outputs = {form: public_output(api, form) for form in forms}
    finally:
        for key, value in originals.items():
            if value is missing:
                delattr(engine, key)
            else:
                setattr(engine, key, value)
    if files != runtime_files() or raw != source.read_bytes():
        raise ValueError("runtime or inventory changed during snapshot; retry in a fresh process")
    return {
        "schema_version": SCHEMA_VERSION,
        "engine_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        # Retain the old field, but never use it alone to guard engine changes.
        "engine_sha256": digest(Path(engine.__file__).read_bytes()),
        "runtime_files": files,
        "runtime_sha256": logical_hash(engine_files(files)),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "comparison_tool_sha256": digest(Path(__file__).read_bytes()),
        "inventory_sha256": digest(raw),
        "inventory_path": str(source.resolve()),
        "inventory_metadata": {
            k: v
            for k, v in data.items()
            if k not in {"first_members", "heads", "head_forms", "head_paradigms", "analyses"}
        },
        "corpus_path": str(corpus.resolve()),
        "corpus_sha256": logical_hash(sorted(forms)),
        "corpus_count": len(forms),
        "forms": {f: value["preferred"]["hyphenate"] for f, value in outputs.items()},
        "outputs": outputs,
    }


def validate_snapshot(value: dict) -> None:
    """Refuse incomplete evidence, including old preferred-string-only snapshots."""
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("full-API schema_version 2 snapshot required; regenerate the baseline")
    forms, outputs, files = value.get("forms"), value.get("outputs"), value.get("runtime_files")
    if (
        not isinstance(forms, dict)
        or not forms
        or not isinstance(outputs, dict)
        or forms.keys() != outputs.keys()
        or not isinstance(files, dict)
        or not files
    ):
        raise ValueError("snapshot is missing complete forms, outputs or runtime metadata")
    required_files = {
        "src/slabika/__init__.py",
        "src/slabika/syllabify.py",
        "src/slabika/typo.py",
        INVENTORY_KEY,
        "pyproject.toml",
    }
    if not required_files <= files.keys() or any(
        not isinstance(k, str)
        or not isinstance(v, str)
        or len(v) != 64
        or any(c not in "0123456789abcdef" for c in v)
        for k, v in files.items()
    ):
        raise ValueError("invalid runtime file manifest")
    if (
        value.get("runtime_sha256") != logical_hash(engine_files(files))
        or value.get("corpus_sha256") != logical_hash(sorted(forms))
        or value.get("corpus_count") != len(forms)
    ):
        raise ValueError("snapshot runtime/corpus metadata does not match its contents")
    for form, output in outputs.items():
        if not isinstance(form, str) or not form or not isinstance(output, dict):
            raise ValueError("invalid form/output record")
        if output.keys() != {*MODES, "divisions"}:
            raise ValueError(f"incomplete or unknown public output fields for {form!r}")
        for mode in MODES:
            result = output[mode]
            if (
                not isinstance(result, dict)
                or result.keys() != {"hyphenate", "break_points"}
                or not isinstance(result["hyphenate"], str)
                or not isinstance(result["break_points"], list)
            ):
                raise ValueError(f"invalid {mode} output for {form!r}")
            points = result["break_points"]
            if any(type(p) is not int or not 0 < p < len(form) for p in points) or points != sorted(
                set(points)
            ):
                raise ValueError(f"invalid breakpoints for {form!r}")
        if (
            forms[form] != output["preferred"]["hyphenate"]
            or not isinstance(output["divisions"], list)
            or any(not isinstance(d, str) for d in output["divisions"])
        ):
            raise ValueError(f"invalid preferred/divisions output for {form!r}")


def corpus_changes(before: dict, after: dict) -> dict:
    return {
        "added_forms": sorted(after["forms"].keys() - before["forms"].keys()),
        "removed_forms": sorted(before["forms"].keys() - after["forms"].keys()),
    }


def compare(before: dict, after: dict, *, allow_corpus_changes: bool = False):
    delta = corpus_changes(before, after)
    if any(delta.values()) and not allow_corpus_changes:
        raise ValueError(
            "baseline and candidate must cover exactly the same corpus forms; " + canonical(delta)
        )
    if ("outputs" in before) != ("outputs" in after):
        raise ValueError("cannot compare full-API and legacy string snapshots")
    if "outputs" in before:
        validate_snapshot(before)
        validate_snapshot(after)
    old = before.get("outputs", before["forms"])
    new = after.get("outputs", after["forms"])
    return [
        {"form": form, "before": old.get(form), "after": new.get(form)}
        for form in sorted(old.keys() | new.keys())
        if old.get(form) != new.get(form)
    ]


def check_changes(changes: list[dict], allowlist) -> dict:
    """No word-wide exemptions, partial outputs, duplicates or stale approvals."""
    if not isinstance(allowlist, list):
        raise ValueError("allowlist must be a JSON array of exact form/before/after entries")
    for entry in allowlist:
        if (
            not isinstance(entry, dict)
            or entry.keys() != {"form", "before", "after"}
            or not isinstance(entry["form"], str)
            or not entry["form"]
            or entry["before"] == entry["after"]
        ):
            raise ValueError("allowlist entries must contain exactly form, before and after")
    approvals = {canonical(entry) for entry in allowlist}
    if len(approvals) != len(allowlist):
        raise ValueError("duplicate allowlist entries")
    actual = {canonical(entry) for entry in changes}
    unapproved = [entry for entry in changes if canonical(entry) not in approvals]
    unused = [entry for entry in allowlist if canonical(entry) not in actual]
    return {
        "passed": not unapproved and not unused,
        "unapproved_changes": unapproved,
        "unused_approvals": unused,
    }


def load_json(path: Path):
    # Duplicate keys can otherwise hide an unapproved change or corrupt evidence.
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    raw = path.read_bytes()
    return json.loads(raw, object_pairs_hook=unique), digest(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "tests/data/translatemaster_hyphenation_working.sqlite",
    )
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-engine-changes", action="store_true")
    parser.add_argument("--allow-corpus-changes", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--allowlist",
        type=Path,
        help="JSON array of exact reviewed entries from the changes report",
    )
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output already exists; choose a new path")
    if (
        args.check or args.allowlist or args.allow_engine_changes or args.allow_corpus_changes
    ) and not args.baseline:
        parser.error("comparison/check options require --baseline")
    if args.allowlist and not args.check:
        parser.error("--allowlist requires --check")
    try:
        before, baseline_hash = load_json(args.baseline) if args.baseline else (None, None)
        if before is not None:
            validate_snapshot(before)
        allowlist, allowlist_hash = load_json(args.allowlist) if args.allowlist else ([], None)
        check_changes([], allowlist)  # Validate approvals before an expensive corpus run.
        result = snapshot(args.corpus, args.inventory)
        validate_snapshot(result)
        refused = []
        if before is not None:
            delta = corpus_changes(before, result)
            old_files, new_files = (
                engine_files(before["runtime_files"]),
                engine_files(result["runtime_files"]),
            )
            changed_files = sorted(
                k
                for k in old_files.keys() | new_files.keys()
                if old_files.get(k) != new_files.get(k)
            )
            result["runtime_changes"] = [
                {"path": k, "before": old_files.get(k), "after": new_files.get(k)}
                for k in changed_files
            ]
            result["environment_changed"] = before.get("environment") != result["environment"]
            if (changed_files or result["environment_changed"]) and not args.allow_engine_changes:
                refused.append("engine/runtime changed since baseline; use --allow-engine-changes")
            if any(delta.values()) and not args.allow_corpus_changes:
                refused.append("different corpus forms; use --allow-corpus-changes")
            result.update(delta)
            # Always persist the complete diff, even when comparison is refused.
            result["changes"] = compare(before, result, allow_corpus_changes=True)
            result["baseline_sha256"] = baseline_hash
            result["comparison"] = {
                "allow_engine_changes": args.allow_engine_changes,
                "allow_corpus_changes": args.allow_corpus_changes,
                "refused": refused,
            }
            if args.check:
                result["check"] = check_changes(result["changes"], allowlist)
                result["check"]["passed"] &= not refused
                result["allowlist_sha256"] = allowlist_hash
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, sort_keys=True)
    except (
        ValueError,
        KeyError,
        TypeError,
        OSError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as exc:
        parser.error(str(exc))
    print(
        f"forms {len(result['forms'])}; changes {len(result.get('changes', []))}; "
        f"added {len(result.get('added_forms', []))}; "
        f"removed {len(result.get('removed_forms', []))}; output {args.output}"
    )
    if refused:
        print("; ".join(refused), file=sys.stderr)
        return 2
    if args.check:
        print(
            f"check {'PASS' if result['check']['passed'] else 'FAIL'}; "
            f"unapproved {len(result['check']['unapproved_changes'])}; "
            f"unused approvals {len(result['check']['unused_approvals'])}"
        )
        return 0 if result["check"]["passed"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
