# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Read-only audit of recurring candidate morpheme boundaries.

SAPFO and Morfessor are evidence sources, not normative authorities. The report
only groups candidates for subsequent adjudication against PSP; it never changes
an engine rule or an audit database.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from slabika import hyphenate  # noqa: E402
from slabika.morphology import get_morphology  # noqa: E402
from slabika.syllabify import get_morpheme_parts  # noqa: E402

DEFAULT_INVENTORY = ROOT / "tests/data/translatemaster_hyphenation_working.sqlite"
DEFAULT_REVIEW = ROOT / "tests/data/review_decisions.sqlite"
DEFAULT_SAPFO_ROOT = ROOT.parent / "Sapfo"
DEFAULT_SAPFO_DB = DEFAULT_SAPFO_ROOT / "sapfo/data/sapfo_lexicon.db"
DEFAULT_TARGETS = ("hrad", "hľad")
DEFAULT_DISCOVERY_LIMIT = 100
DEFAULT_MIN_TARGET_LENGTH = 4
DEFAULT_MIN_SUPPORTED_FORMS = 3
DEFAULT_MIN_UNCOVERED_FORMS = 2


def _open_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        )
    }


def load_all_forms(path: Path) -> list[str]:
    with _open_readonly(path) as connection:
        rows = connection.execute("SELECT form FROM forms ORDER BY form")
        forms = {
            unicodedata.normalize("NFC", row[0])
            for row in rows
            if row[0].islower() and row[0].isalpha()
        }
    return sorted(forms, key=str.casefold)


def load_forms(path: Path, targets: tuple[str, ...]) -> list[str]:
    return [
        form
        for form in load_all_forms(path)
        if any(target in form.casefold() for target in targets)
    ]


def _part_spans(parts: list[str]) -> list[tuple[int, int, str]]:
    spans = []
    start = 0
    for part in parts:
        end = start + len(part)
        spans.append((start, end, part))
        start = end
    return spans


def _seams(parts: list[str]) -> set[int]:
    positions = set()
    position = 0
    for part in parts[:-1]:
        position += len(part)
        positions.add(position)
    return positions


def load_sapfo_candidate_members(
    path: Path, min_target_length: int
) -> dict[str, list[str]]:
    sources: dict[str, set[str]] = defaultdict(set)

    def add(value: object, source: str) -> None:
        member = unicodedata.normalize("NFC", str(value).replace("*", "").casefold())
        if len(member) >= min_target_length and member.isalpha():
            sources[member].add(source)

    with _open_readonly(path) as connection:
        available = _tables(connection)
        columns = (
            ("nouns", "word", "noun_lexeme"),
            ("adjectives", "root", "adjective_root"),
            ("verbs", "inf_stem", "verb_inf_stem"),
            ("verbs", "pres_stem", "verb_pres_stem"),
        )
        for table, column, source in columns:
            if table not in available:
                continue
            for row in connection.execute(
                f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL"
            ):
                add(row[0], source)

        if "word_roots" in available:
            for row in connection.execute(
                "SELECT roots FROM word_roots WHERE roots IS NOT NULL"
            ):
                try:
                    roots = json.loads(row[0])
                except (TypeError, json.JSONDecodeError):
                    continue
                if isinstance(roots, list):
                    for root in roots:
                        add(root, "derivation_root")

        if "pales_kmen" in available:
            for row in connection.execute(
                "SELECT derived_from_lemma FROM pales_kmen "
                "WHERE derived_from_lemma IS NOT NULL"
            ):
                add(row[0], "derivation_base")

    return {
        member: sorted(member_sources)
        for member, member_sources in sorted(sources.items())
    }


def discover_candidates(
    forms: list[str],
    sapfo_members: dict[str, list[str]],
    *,
    min_supported_forms: int = DEFAULT_MIN_SUPPORTED_FORMS,
    min_uncovered_forms: int = DEFAULT_MIN_UNCOVERED_FORMS,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> list[dict[str, object]]:
    if min_supported_forms < 1 or min_uncovered_forms < 1 or limit < 1:
        raise ValueError("discovery thresholds and limit must be positive")

    parsed = []
    supported: dict[str, set[str]] = defaultdict(set)
    for form in forms:
        parts = get_morpheme_parts(form)
        hyphenation_breaks = _seams(hyphenate(form).split("·"))
        parsed.append((form, parts, hyphenation_breaks))
        for part in parts:
            member = part.casefold()
            if member in sapfo_members:
                supported[member].add(form.casefold())

    candidates = {
        member
        for member, member_forms in supported.items()
        if len(member_forms) >= min_supported_forms
    }
    lengths_by_initial: dict[str, set[int]] = defaultdict(set)
    for member in candidates:
        lengths_by_initial[member[0]].add(len(member))

    covered_forms: dict[str, set[str]] = defaultdict(set)
    uncovered_forms: dict[str, set[str]] = defaultdict(set)
    uncovered_contexts: dict[str, set[str]] = defaultdict(set)
    uncovered_occurrences = Counter()
    missing_break_forms: dict[str, set[str]] = defaultdict(set)
    missing_break_contexts: dict[str, set[str]] = defaultdict(set)
    missing_break_occurrences = Counter()
    for form, parts, hyphenation_breaks in parsed:
        folded = form.casefold()
        seams = _seams(parts)
        for offset in range(1, len(folded)):
            for length in lengths_by_initial.get(folded[offset], ()):
                member = folded[offset : offset + length]
                if len(member) != length or member not in candidates:
                    continue
                if offset in seams:
                    covered_forms[member].add(folded)
                else:
                    uncovered_forms[member].add(folded)
                    uncovered_contexts[member].add(folded[:offset])
                    uncovered_occurrences[member] += 1
                    if offset not in hyphenation_breaks:
                        missing_break_forms[member].add(folded)
                        missing_break_contexts[member].add(folded[:offset])
                        missing_break_occurrences[member] += 1

    reports = []
    for member in candidates:
        support_count = len(supported[member])
        uncovered_count = len(uncovered_forms[member])
        missing_break_count = len(missing_break_forms[member])
        if missing_break_count < min_uncovered_forms:
            continue
        priority = (
            2 * support_count * missing_break_count / (support_count + missing_break_count)
        )
        reports.append(
            {
                "target": member,
                "priority_score": round(priority, 3),
                "sapfo_sources": sapfo_members[member],
                "engine_supported_forms": support_count,
                "covered_noninitial_forms": len(covered_forms[member]),
                "uncovered_forms": uncovered_count,
                "uncovered_occurrences": uncovered_occurrences[member],
                "distinct_uncovered_left_contexts": len(uncovered_contexts[member]),
                "missing_output_break_forms": missing_break_count,
                "missing_output_break_occurrences": missing_break_occurrences[member],
                "distinct_missing_output_break_left_contexts": len(
                    missing_break_contexts[member]
                ),
                "engine_support_examples": sorted(supported[member])[:20],
                "uncovered_examples": sorted(uncovered_forms[member])[:20],
                "uncovered_left_context_examples": sorted(uncovered_contexts[member])[:20],
                "missing_output_break_examples": sorted(missing_break_forms[member])[:20],
                "missing_output_break_left_context_examples": sorted(
                    missing_break_contexts[member]
                )[:20],
            }
        )

    reports.sort(
        key=lambda item: (
            -float(item["priority_score"]),
            -int(item["uncovered_forms"]),
            -int(item["engine_supported_forms"]),
            str(item["target"]),
        )
    )
    return reports[:limit]


def _family_key(
    form: str,
    member: str,
    offset: int,
    engine_parts: list[str],
    morphessor_parts: tuple[str, ...],
) -> str:
    end = offset + len(member)
    candidates = []
    for source, parts in (("engine", engine_parts), ("morfessor", list(morphessor_parts))):
        for start, stop, part in _part_spans(parts):
            if start <= offset and end <= stop:
                family = member if start == offset else part.casefold()
                candidates.append((len(family), start, source, family))
    if not candidates:
        return form[offset:end].casefold()
    return min(candidates)[3]


def load_review_evidence(
    inventory_path: Path, review_path: Path | None, targets: tuple[str, ...]
) -> dict[str, list[dict[str, object]]]:
    evidence: dict[str, list[dict[str, object]]] = defaultdict(list)
    clauses = " OR ".join("lower(form) LIKE ?" for _ in targets)
    parameters = tuple(f"%{target.casefold()}%" for target in targets)

    with _open_readonly(inventory_path) as connection:
        if "adjudications" in _tables(connection):
            for row in connection.execute(
                f"""SELECT form, review_status, expected_hyphenation, reason, source
                    FROM adjudications WHERE {clauses}""",
                parameters,
            ):
                evidence[row["form"].casefold()].append(
                    {
                        "source": "inventory_adjudication",
                        "status": row["review_status"],
                        "expected_hyphenation": row["expected_hyphenation"],
                        "reason": row["reason"],
                        "provenance": row["source"],
                    }
                )

    if review_path is not None and review_path.is_file():
        with _open_readonly(review_path) as connection:
            if "decisions" in _tables(connection):
                columns = {row[1] for row in connection.execute("PRAGMA table_info(decisions)")}
                select = ["form", "action", "expected_hyphenation", "reason"]
                for optional in ("hyphenation_action", "is_deleted"):
                    if optional in columns:
                        select.append(optional)
                for row in connection.execute(
                    f"SELECT {', '.join(select)} FROM decisions WHERE {clauses}", parameters
                ):
                    if "is_deleted" in row.keys() and row["is_deleted"]:
                        continue
                    evidence[row["form"].casefold()].append(
                        {
                            "source": "human_review",
                            "status": (
                                row["hyphenation_action"]
                                if "hyphenation_action" in row.keys()
                                and row["hyphenation_action"]
                                else row["action"]
                            ),
                            "expected_hyphenation": row["expected_hyphenation"],
                            "reason": row["reason"],
                        }
                    )
    return dict(evidence)


def load_sapfo_database_evidence(
    path: Path, targets: tuple[str, ...], forms: set[str]
) -> dict[str, object]:
    patterns = tuple(f"%{target.casefold()}%" for target in targets)
    two_columns = " OR ".join("lower(wordform) LIKE ?" for _ in targets)
    by_form: dict[str, list[dict[str, str]]] = defaultdict(list)
    inventory: list[dict[str, object]] = []
    derivations: list[dict[str, object]] = []

    with _open_readonly(path) as connection:
        available = _tables(connection)
        if "snk_forms" in available:
            for row in connection.execute(
                f"SELECT wordform, lemma, pos FROM snk_forms WHERE {two_columns}", patterns
            ):
                folded = row["wordform"].casefold()
                if folded in forms:
                    item = {"lemma": row["lemma"], "pos": row["pos"]}
                    if item not in by_form[folded]:
                        by_form[folded].append(item)

        lexicon_queries = {
            "nouns": (
                "word",
                "SELECT word AS lexeme, word AS root, pattern, source FROM nouns "
                "WHERE lower(word) LIKE ?",
            ),
            "proper_names": (
                "name",
                "SELECT name AS lexeme, name AS root, pattern, '' AS source "
                "FROM proper_names WHERE lower(name) LIKE ?",
            ),
            "adjectives": (
                "root",
                "SELECT coalesce(nullif(lemma, ''), root) AS lexeme, root, pattern, source "
                "FROM adjectives WHERE lower(root) LIKE ? OR lower(lemma) LIKE ?",
            ),
            "verbs": (
                "inf_stem",
                "SELECT coalesce(nullif(lemma, ''), inf_stem) AS lexeme, inf_stem AS root, "
                "pattern, source FROM verbs WHERE lower(inf_stem) LIKE ? "
                "OR lower(pres_stem) LIKE ? OR lower(lemma) LIKE ?",
            ),
        }
        for table, (_, query) in lexicon_queries.items():
            if table not in available:
                continue
            repeats = query.count("?")
            for target in targets:
                for row in connection.execute(query, (f"%{target.casefold()}%",) * repeats):
                    item = {"table": table, **dict(row)}
                    if item not in inventory:
                        inventory.append(item)

        if "word_roots" in available:
            query = (
                "SELECT word AS lemma, roots AS derived_from, prefix, suffix, "
                "is_compound, 'word_roots' AS table_name FROM word_roots "
                "WHERE lower(word) LIKE ? OR lower(roots) LIKE ?"
            )
            for target in targets:
                for row in connection.execute(query, (f"%{target}%", f"%{target}%")):
                    item = dict(row)
                    if item not in derivations:
                        derivations.append(item)

        if "pales_kmen" in available:
            query = (
                "SELECT lemma, coalesce(derived_from_lemma, '') AS derived_from, prefix, suffix, "
                "0 AS is_compound, 'pales_kmen' AS table_name FROM pales_kmen "
                "WHERE lower(lemma) LIKE ? OR lower(derived_from_lemma) LIKE ?"
            )
            for target in targets:
                for row in connection.execute(query, (f"%{target}%", f"%{target}%")):
                    item = dict(row)
                    if item not in derivations:
                        derivations.append(item)

    for values in by_form.values():
        values.sort(key=lambda item: (item["lemma"].casefold(), item["pos"]))
    inventory.sort(key=lambda item: (str(item["table"]), str(item["lexeme"]).casefold()))
    derivations.sort(key=lambda item: (str(item["lemma"]).casefold(), str(item["table_name"])))
    return {"snk_by_form": dict(by_form), "lexicon": inventory, "derivations": derivations}


def load_sapfo_runtime_evidence(
    sapfo_root: Path, forms: list[str]
) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, object]]]:
    if not sapfo_root.is_dir():
        raise FileNotFoundError(sapfo_root)
    sys.path.insert(0, str(sapfo_root))
    from sapfo.core.morphology import analyzuj  # noqa: PLC0415
    from sapfo.tools.paradigm import paradigm  # noqa: PLC0415

    analyses: dict[str, list[dict[str, str]]] = {}
    lemmas = set()
    for form in forms:
        readings = []
        for result in analyzuj(form):
            pos = result.pos.value if hasattr(result.pos, "value") else str(result.pos)
            item = {
                "lemma": result.lemma,
                "pos": pos,
                "root": result.root,
                "pattern": result.pattern,
            }
            if item not in readings:
                readings.append(item)
                lemmas.add(result.lemma)
        if readings:
            analyses[form.casefold()] = readings

    roundtrips = {}
    for lemma in sorted(lemmas, key=str.casefold):
        report = paradigm(lemma)
        readings = []
        for reading in report.readings:
            pos = reading.pos.value if hasattr(reading.pos, "value") else str(reading.pos)
            readings.append(
                {
                    "pos": pos,
                    "root": reading.root,
                    "pattern": reading.pattern,
                    "generated": len(reading.cells),
                    "roundtrip_ok": sum(cell.ok for cell in reading.cells),
                    "snk_attested": len(reading.snk_forms),
                }
            )
        roundtrips[lemma] = {"readings": readings}
    return analyses, roundtrips


def _matching_inventory(
    family: str, entries: list[dict[str, object]], fields: tuple[str, ...]
) -> list[dict[str, object]]:
    folded = family.casefold()
    return [
        entry
        for entry in entries
        if any(folded in str(entry.get(field, "")).casefold() for field in fields)
    ]


def build_report(
    forms: list[str],
    targets: tuple[str, ...],
    review: dict[str, list[dict[str, object]]],
    sapfo_db: dict[str, object],
    sapfo_runtime: dict[str, list[dict[str, str]]],
    roundtrips: dict[str, dict[str, object]],
) -> dict[str, object]:
    morphology = get_morphology()
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    totals = Counter()
    snk_by_form = sapfo_db["snk_by_form"]

    for form in forms:
        folded = form.casefold()
        engine_parts = get_morpheme_parts(form)
        engine_seams = _seams(engine_parts)
        morphessor_parts = morphology.parse(form)
        for member in targets:
            offset = 0
            while True:
                offset = folded.find(member, offset)
                if offset < 0:
                    break
                if offset == 0:
                    status = "word_initial"
                elif offset in engine_seams:
                    status = "engine_seam"
                else:
                    status = "inside_engine_morpheme"
                family = _family_key(
                    form, member, offset, engine_parts, morphessor_parts
                )
                item = {
                    "form": form,
                    "member": member,
                    "offset": offset,
                    "left_context": form[:offset],
                    "status": status,
                    "engine_hyphenation": hyphenate(form),
                    "engine_morphemes": engine_parts,
                    "morfessor_parse": list(morphessor_parts),
                    "morfessor_has_boundary": (
                        offset > 0 and morphology.has_boundary(form, offset)
                    ),
                    "morfessor_prefers_boundary": (
                        offset > 0 and morphology.prefers_boundary(form, offset)
                    ),
                    "sapfo_snk": snk_by_form.get(folded, []),
                    "sapfo_analysis": sapfo_runtime.get(folded, []),
                    "review_evidence": review.get(folded, []),
                }
                groups[(member, family)].append(item)
                totals[status] += 1
                offset += 1

    family_reports = []
    for (member, family), occurrences in sorted(groups.items()):
        statuses = Counter(item["status"] for item in occurrences)
        analyses = {
            (reading["lemma"], reading["pos"], reading["root"], reading["pattern"])
            for item in occurrences
            for reading in item["sapfo_analysis"]
        }
        snk_readings = {
            (reading["lemma"], reading["pos"])
            for item in occurrences
            for reading in item["sapfo_snk"]
        }
        family_reports.append(
            {
                "member": member,
                "family": family,
                "status": (
                    "has_uncovered_occurrences"
                    if statuses["inside_engine_morpheme"]
                    else "engine_covers_noninitial_occurrences"
                ),
                "counts": dict(sorted(statuses.items())),
                "distinct_forms": len({item["form"].casefold() for item in occurrences}),
                "distinct_left_contexts": sorted(
                    {item["left_context"].casefold() for item in occurrences}
                ),
                "morfessor_boundary_forms": sum(
                    bool(item["morfessor_has_boundary"]) for item in occurrences
                ),
                "sapfo_snk_readings": [
                    {"lemma": lemma, "pos": pos}
                    for lemma, pos in sorted(
                        snk_readings, key=lambda value: (value[0].casefold(), value[1])
                    )
                ],
                "sapfo_analyses": [
                    {"lemma": lemma, "pos": pos, "root": root, "pattern": pattern}
                    for lemma, pos, root, pattern in sorted(
                        analyses, key=lambda value: (value[0].casefold(), value[1])
                    )
                ],
                "sapfo_lexicon_evidence": _matching_inventory(
                    family, sapfo_db["lexicon"], ("lexeme", "root")
                ),
                "sapfo_derivation_evidence": _matching_inventory(
                    family, sapfo_db["derivations"], ("lemma", "derived_from")
                ),
                "occurrences": sorted(
                    occurrences, key=lambda item: (item["status"], item["form"].casefold())
                ),
            }
        )

    return {
        "contract": (
            "Candidate evidence only. SAPFO, SNK, Morfessor and prior reviews are not PSP "
            "verdicts; no runtime rule or source database was modified."
        ),
        "targets": list(targets),
        "summary": {
            "forms": len(forms),
            "occurrences": sum(totals.values()),
            "families": len(family_reports),
            "status_counts": dict(sorted(totals.items())),
            "families_with_uncovered_occurrences": sum(
                family["status"] == "has_uncovered_occurrences"
                for family in family_reports
            ),
            "sapfo_runtime_analyzed_forms": len(sapfo_runtime),
            "sapfo_roundtrip_lemmas": len(roundtrips),
        },
        "families": family_reports,
        "sapfo_roundtrips": roundtrips,
        "sapfo_inventory": {
            "lexicon": sapfo_db["lexicon"],
            "derivations": sapfo_db["derivations"],
        },
    }


def generate_report(
    inventory: Path,
    review_db: Path | None,
    sapfo_db_path: Path,
    sapfo_root: Path,
    targets: tuple[str, ...] = DEFAULT_TARGETS,
    use_sapfo_api: bool = True,
) -> dict[str, object]:
    normalized_targets = tuple(
        dict.fromkeys(unicodedata.normalize("NFC", target.casefold()) for target in targets)
    )
    if not normalized_targets or any(not target.isalpha() for target in normalized_targets):
        raise ValueError("targets must be non-empty alphabetic strings")
    forms = load_forms(inventory, normalized_targets)
    folded_forms = {form.casefold() for form in forms}
    review = load_review_evidence(inventory, review_db, normalized_targets)
    sapfo_db = load_sapfo_database_evidence(
        sapfo_db_path, normalized_targets, folded_forms
    )
    runtime, roundtrips = ({}, {})
    if use_sapfo_api:
        runtime, roundtrips = load_sapfo_runtime_evidence(sapfo_root, forms)
    report = build_report(
        forms, normalized_targets, review, sapfo_db, runtime, roundtrips
    )
    report["sources"] = {
        "inventory": str(inventory.resolve()),
        "review_db": str(review_db.resolve()) if review_db is not None else None,
        "sapfo_db": str(sapfo_db_path.resolve()),
        "sapfo_api": str(sapfo_root.resolve()) if use_sapfo_api else None,
    }
    return report


def generate_discovery_report(
    inventory: Path,
    sapfo_db_path: Path,
    *,
    min_target_length: int = DEFAULT_MIN_TARGET_LENGTH,
    min_supported_forms: int = DEFAULT_MIN_SUPPORTED_FORMS,
    min_uncovered_forms: int = DEFAULT_MIN_UNCOVERED_FORMS,
    limit: int = DEFAULT_DISCOVERY_LIMIT,
) -> dict[str, object]:
    if min_target_length < 1:
        raise ValueError("minimum target length must be positive")
    forms = load_all_forms(inventory)
    sapfo_members = load_sapfo_candidate_members(sapfo_db_path, min_target_length)
    candidates = discover_candidates(
        forms,
        sapfo_members,
        min_supported_forms=min_supported_forms,
        min_uncovered_forms=min_uncovered_forms,
        limit=limit,
    )
    return {
        "contract": (
            "Discovery evidence only. Candidate rank is not a morphology or PSP verdict; "
            "no runtime rule or source database was modified."
        ),
        "parameters": {
            "min_target_length": min_target_length,
            "min_supported_forms": min_supported_forms,
            "min_uncovered_forms": min_uncovered_forms,
            "limit": limit,
        },
        "sources": {
            "inventory": str(inventory.resolve()),
            "sapfo_db": str(sapfo_db_path.resolve()),
        },
        "summary": {
            "corpus_forms": len(forms),
            "sapfo_candidate_members": len(sapfo_members),
            "returned_candidates": len(candidates),
        },
        "candidates": candidates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="rank recurring Sapfo-backed members whose seams are inconsistently covered",
    )
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--review-db", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--sapfo-db", type=Path, default=DEFAULT_SAPFO_DB)
    parser.add_argument("--sapfo-root", type=Path, default=DEFAULT_SAPFO_ROOT)
    parser.add_argument("--no-sapfo-api", action="store_true")
    parser.add_argument(
        "--min-target-length", type=int, default=DEFAULT_MIN_TARGET_LENGTH
    )
    parser.add_argument(
        "--min-supported-forms", type=int, default=DEFAULT_MIN_SUPPORTED_FORMS
    )
    parser.add_argument(
        "--min-uncovered-forms", type=int, default=DEFAULT_MIN_UNCOVERED_FORMS
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_DISCOVERY_LIMIT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.discover and args.targets:
        parser.error("explicit targets cannot be combined with --discover")
    if args.discover:
        report = generate_discovery_report(
            args.inventory,
            args.sapfo_db,
            min_target_length=args.min_target_length,
            min_supported_forms=args.min_supported_forms,
            min_uncovered_forms=args.min_uncovered_forms,
            limit=args.limit,
        )
    else:
        report = generate_report(
            args.inventory,
            args.review_db,
            args.sapfo_db,
            args.sapfo_root,
            tuple(args.targets) or DEFAULT_TARGETS,
            not args.no_sapfo_api,
        )
    if args.output:
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if args.output:
        print(f"report: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
