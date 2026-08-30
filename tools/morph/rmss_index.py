# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build and query a local index of the Retrográdny morfematický slovník.

The source publication and the generated database stay under ``corpora/rmss/``,
which is ignored by Git.  They retain the source copyright and are evidence,
not redistributable project language data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "corpora/rmss"
DEFAULT_PDF = SOURCE_DIR / "retrogradny-morfematicky-slovnik-slovenčiny-2020.pdf"
DEFAULT_DB = SOURCE_DIR / "rmss.sqlite"
DEFAULT_INVENTORY = ROOT / "tests/data/translatemaster_hyphenation_working.sqlite"
DEFAULT_REVIEW = ROOT / "tests/data/review_decisions.sqlite"
DICTIONARY_FIRST_PDF_PAGE = 45
PRINTED_PAGE_OFFSET = -4

_ORIGIN_RE = re.compile(r"^\d(?:,\d)*(?:\*)?$")
_S_CODE = r"S[A-Za-z]*\d*(?:/(?:S[A-Za-z]*\d*|[A-Za-z]*\d+|[xy]))*"
_CODE_ATOM = rf"(?:{_S_CODE}|V(?:\d+|x|y)(?:/[A-Za-z0-9]+)*|A(?:\d+|x|y)|P(?:\d+|x|y)|N(?:\d+|x|y)|[A-Z]{{1,3}})"
_CODE_RE = re.compile(rf"^{_CODE_ATOM}(?:(?:\+|–){_CODE_ATOM})*$")
_REFLEXIVES = {"sa", "si", "(sa)", "(si)", "(sa,", "(si,", "sa)", "si)"}


def _plain(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )


def notation_to_surface(notation: str) -> str:
    text = notation.replace("ø", "").replace("«", "")
    text = text.replace("[", "").replace("]", "").replace(":", "")
    text = text.replace("-", "").replace("–", "-")
    return " ".join(text.split())


def explicit_morphemes(notation: str) -> list[str]:
    return [part for part in notation.replace("–", "").split("-") if part]


def font_role(font: str, flags: int) -> str:
    font_lower = font.casefold()
    is_bold = bool(flags & 16) or "bold" in font_lower
    is_italic = (
        bool(flags & 2)
        or "italic" in font_lower
        or "boldit" in font_lower
        or font_lower.endswith("-it")
    )
    if is_bold and is_italic:
        return "root_grammatical"
    if is_bold:
        return "root"
    if is_italic:
        return "grammatical"
    return "other"


def analysis_style_spans(spans: list[dict[str, object]]) -> list[dict[str, object]]:
    full_text = "".join(str(span["text"]) for span in spans)
    token_matches = list(re.finditer(r"\S+", full_text))
    tokens = [match.group() for match in token_matches]
    if len(tokens) < 3:
        return []
    code_at = next((i for i, token in enumerate(tokens[3:], 3) if _CODE_RE.fullmatch(token)), None)
    analysis_start = token_matches[2].start()
    analysis_stop = (
        token_matches[-1].end() if code_at is None else token_matches[code_at - 1].end()
    )
    result: list[dict[str, object]] = []
    span_start = 0
    for span in spans:
        text = str(span["text"])
        span_stop = span_start + len(text)
        start = max(span_start, analysis_start)
        stop = min(span_stop, analysis_stop)
        if start < stop:
            fragment = text[start - span_start:stop - span_start]
            if fragment:
                flags = int(span["flags"])
                font = str(span["font"])
                result.append(
                    {
                        "text": fragment,
                        "font": font,
                        "flags": flags,
                        "role": font_role(font, flags),
                    }
                )
        span_start = span_stop
    return result


def _without_aspect_partner(tokens: list[str]) -> list[str]:
    result: list[str] = []
    inside = False
    for token in tokens:
        if not inside and token.startswith("{"):
            inside = not token.endswith("}")
            continue
        if inside:
            inside = not token.endswith("}")
            continue
        result.append(token)
    return result


def extract_variants(tokens: list[str]) -> list[str]:
    tokens = _without_aspect_partner(tokens)
    tokens = [token for token in tokens if token not in _REFLEXIVES]
    variants: list[list[str]] = [[]]
    for token in tokens:
        if token == "/":
            if variants[-1]:
                variants.append([])
        else:
            variants[-1].append(token)
    return [" ".join(parts) for parts in variants if parts]


def parse_entry_tokens(tokens: list[str]) -> dict[str, object]:
    raw_text = " ".join(tokens)
    if len(tokens) < 3 or not _ORIGIN_RE.fullmatch(tokens[0]) or tokens[1] not in {"M", "N", "P"}:
        return {"raw_text": raw_text, "parse_status": "not_entry"}

    code_at = next((i for i, token in enumerate(tokens[3:], 3) if _CODE_RE.fullmatch(token)), None)
    if code_at is None:
        return {
            "origin_index": tokens[0],
            "motivation": tokens[1],
            "analysis": " ".join(tokens[2:]),
            "raw_text": raw_text,
            "parse_status": "partial",
        }

    analysis_tokens = tokens[2:code_at]
    variants = extract_variants(analysis_tokens)
    return {
        "origin_index": tokens[0],
        "motivation": tokens[1],
        "analysis": " ".join(analysis_tokens),
        "flex_code": tokens[code_at],
        "raw_text": raw_text,
        "parse_status": "parsed" if variants else "partial",
        "variants": variants,
    }


def iter_entry_chunks(tsv_path: Path):
    pages: dict[int, list[dict[str, str]]] = defaultdict(list)
    with tsv_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row["level"] == "5":
                pages[int(row["page_num"])].append(row)

    for page, words in sorted(pages.items()):
        clusters: list[tuple[float, list[dict[str, str]]]] = []
        for row in sorted(words, key=lambda item: float(item["top"])):
            top = float(row["top"])
            if not clusters or top - clusters[-1][0] > 2.0:
                clusters.append((top, [row]))
            else:
                clusters[-1][1].append(row)

        for top, rows in clusters:
            rows.sort(key=lambda item: float(item["left"]))
            tokens = [row["text"] for row in rows]
            starts = [
                i for i in range(len(tokens) - 1)
                if _ORIGIN_RE.fullmatch(tokens[i]) and tokens[i + 1] in {"M", "N", "P"}
            ]
            for position, start in enumerate(starts):
                stop = starts[position + 1] if position + 1 < len(starts) else len(tokens)
                yield page, top, tokens[start:stop]


def iter_styled_entry_chunks(pdf_path: Path):
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("Building the styled RMSS index requires PyMuPDF") from error

    entry_start = re.compile(r"^\d(?:,\d)*(?:\*)?\s+[MNP]\s+")
    with fitz.open(pdf_path) as document:
        for page_index in range(DICTIONARY_FIRST_PDF_PAGE - 1, document.page_count):
            page = document[page_index]
            lines: list[tuple[float, float, list[str], list[dict[str, object]]]] = []
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    text = "".join(str(span["text"]) for span in spans).strip()
                    if entry_start.match(text):
                        lines.append(
                            (
                                float(line["bbox"][1]),
                                float(line["bbox"][0]),
                                text.split(),
                                analysis_style_spans(spans),
                            )
                        )

            clusters: list[tuple[float, list[tuple[float, float, list, list]]]] = []
            for line in sorted(lines):
                if not clusters or line[0] - clusters[-1][0] > 2.0:
                    clusters.append((line[0], [line]))
                else:
                    clusters[-1][1].append(line)
            for _, cluster in clusters:
                for top, _, tokens, styles in sorted(cluster, key=lambda item: item[1]):
                    yield page_index + 1, top, tokens, styles


def build_index(pdf_path: Path, db_path: Path, tsv_path: Path | None = None) -> dict[str, int]:
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if tsv_path is None:
        chunks = iter_styled_entry_chunks(pdf_path)
        typography_source = "embedded PDF font spans extracted by PyMuPDF"
    else:
        chunks = ((page, top, tokens, []) for page, top, tokens in iter_entry_chunks(tsv_path))
        typography_source = "not available: external TSV input has no font information"

    connection = sqlite3.connect(db_path)
    with connection:
        connection.executescript(
            """
            PRAGMA journal_mode = DELETE;
            DROP TABLE IF EXISTS metadata;
            DROP TABLE IF EXISTS entry_style_spans;
            DROP TABLE IF EXISTS entry_morphemes;
            DROP TABLE IF EXISTS entry_variants;
            DROP TABLE IF EXISTS entries;
            DROP TABLE IF EXISTS entries_fts;
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE entries (
                id INTEGER PRIMARY KEY,
                pdf_page INTEGER NOT NULL,
                printed_page INTEGER NOT NULL,
                top REAL NOT NULL,
                origin_index TEXT,
                motivation TEXT,
                analysis TEXT,
                flex_code TEXT,
                raw_text TEXT NOT NULL,
                parse_status TEXT NOT NULL
            );
            CREATE TABLE entry_variants (
                id INTEGER PRIMARY KEY,
                entry_id INTEGER NOT NULL REFERENCES entries(id),
                variant_no INTEGER NOT NULL,
                notation TEXT NOT NULL,
                surface TEXT NOT NULL,
                surface_key TEXT NOT NULL,
                UNIQUE(entry_id, variant_no)
            );
            CREATE TABLE entry_morphemes (
                variant_id INTEGER NOT NULL REFERENCES entry_variants(id),
                position INTEGER NOT NULL,
                notation TEXT NOT NULL,
                surface TEXT NOT NULL,
                surface_key TEXT NOT NULL,
                PRIMARY KEY(variant_id, position)
            );
            CREATE TABLE entry_style_spans (
                entry_id INTEGER NOT NULL REFERENCES entries(id),
                position INTEGER NOT NULL,
                text TEXT NOT NULL,
                surface TEXT NOT NULL,
                surface_key TEXT NOT NULL,
                font TEXT NOT NULL,
                font_flags INTEGER NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('root', 'grammatical', 'root_grammatical', 'other')
                ),
                PRIMARY KEY(entry_id, position)
            );
            CREATE INDEX variants_surface_key ON entry_variants(surface_key);
            CREATE INDEX morphemes_surface_key ON entry_morphemes(surface_key);
            CREATE INDEX style_spans_role_key ON entry_style_spans(role, surface_key);
            CREATE VIRTUAL TABLE entries_fts USING fts5(
                surface, notation, morphemes, content='', tokenize='unicode61 remove_diacritics 2'
            );
            """
        )
        metadata = {
            "title": "Retrográdny morfematický slovník slovenčiny",
            "authors": "Martin Ološtiak; Ján Genči; Soňa Rešovská",
            "publisher": "Prešovská univerzita v Prešove",
            "edition": "2020 online",
            "isbn": "978-80-555-2480-1",
            "source_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
            "typography_source": typography_source,
            "typography_roles": "bold=root; italic=grammatical; bold+italic=root_grammatical",
            "rights": "Source rights retained by Prešovská univerzita and the authors; local research index only",
        }
        connection.executemany("INSERT INTO metadata VALUES (?, ?)", metadata.items())

        stats = {
            "entries": 0,
            "parsed": 0,
            "partial": 0,
            "variants": 0,
            "morphemes": 0,
            "style_spans": 0,
            "root_spans": 0,
            "grammatical_spans": 0,
        }
        for page, top, tokens, style_spans in chunks:
            parsed = parse_entry_tokens(tokens)
            cursor = connection.execute(
                """INSERT INTO entries
                   (pdf_page, printed_page, top, origin_index, motivation, analysis,
                    flex_code, raw_text, parse_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    page, page + PRINTED_PAGE_OFFSET, top, parsed.get("origin_index"),
                    parsed.get("motivation"), parsed.get("analysis"), parsed.get("flex_code"),
                    parsed["raw_text"], parsed["parse_status"],
                ),
            )
            entry_id = cursor.lastrowid
            stats["entries"] += 1
            stats[parsed["parse_status"]] += 1
            for position, span in enumerate(style_spans, 1):
                text = str(span["text"])
                surface = notation_to_surface(text)
                role = str(span["role"])
                connection.execute(
                    "INSERT INTO entry_style_spans VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        entry_id, position, text, surface, _plain(surface), span["font"],
                        span["flags"], role,
                    ),
                )
                stats["style_spans"] += 1
                stats["root_spans"] += role in {"root", "root_grammatical"}
                stats["grammatical_spans"] += role in {"grammatical", "root_grammatical"}
            for number, notation in enumerate(parsed.get("variants", []), 1):
                surface = notation_to_surface(notation)
                variant = connection.execute(
                    """INSERT INTO entry_variants
                       (entry_id, variant_no, notation, surface, surface_key)
                       VALUES (?, ?, ?, ?, ?)""",
                    (entry_id, number, notation, surface, _plain(surface)),
                )
                morphs = explicit_morphemes(notation)
                for position, morph in enumerate(morphs, 1):
                    morph_surface = notation_to_surface(morph)
                    connection.execute(
                        "INSERT INTO entry_morphemes VALUES (?, ?, ?, ?, ?)",
                        (variant.lastrowid, position, morph, morph_surface, _plain(morph_surface)),
                    )
                connection.execute(
                    "INSERT INTO entries_fts(rowid, surface, notation, morphemes) VALUES (?, ?, ?, ?)",
                    (variant.lastrowid, surface, notation, " ".join(morphs)),
                )
                stats["variants"] += 1
                stats["morphemes"] += len(morphs)
    connection.close()
    return stats


def query(db_path: Path, term: str, limit: int) -> list[sqlite3.Row]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """SELECT v.surface, v.notation, e.flex_code, e.printed_page, e.parse_status,
                  (SELECT group_concat(text, ' + ') FROM (
                       SELECT text FROM entry_style_spans s
                       WHERE s.entry_id = e.id AND s.role IN ('root', 'root_grammatical')
                       ORDER BY s.position
                   )) AS roots,
                  (SELECT group_concat(text, ' + ') FROM (
                       SELECT text FROM entry_style_spans s
                       WHERE s.entry_id = e.id AND s.role IN ('grammatical', 'root_grammatical')
                       ORDER BY s.position
                   )) AS grammatical
           FROM entry_variants v JOIN entries e ON e.id = v.entry_id
           WHERE v.surface_key = ? OR v.id IN (
               SELECT rowid FROM entries_fts WHERE entries_fts MATCH ?
           )
           ORDER BY (v.surface_key = ?) DESC, v.surface, e.printed_page
           LIMIT ?""",
        (_plain(term), f'"{term.replace(chr(34), chr(34) * 2)}"', _plain(term), limit),
    ).fetchall()
    connection.close()
    return rows


def query_role(db_path: Path, term: str, role: str, limit: int) -> list[sqlite3.Row]:
    role_values = {
        "root": ("root", "root_grammatical"),
        "grammatical": ("grammatical", "root_grammatical"),
    }
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """SELECT DISTINCT v.surface, v.notation, e.analysis, s.text AS matched_span,
                          e.flex_code, e.printed_page, e.parse_status
           FROM entry_style_spans s
           JOIN entries e ON e.id = s.entry_id
           LEFT JOIN entry_variants v ON v.entry_id = e.id
           WHERE s.surface_key = ? AND s.role IN (?, ?)
           ORDER BY v.surface, e.printed_page
           LIMIT ?""",
        (_plain(term), *role_values[role], limit),
    ).fetchall()
    connection.close()
    return rows


def _seams(parts: list[str]) -> set[int]:
    positions = set()
    position = 0
    for part in parts[:-1]:
        position += len(part)
        positions.add(position)
    return positions


def _marked(word: str, points: set[int] | list[int]) -> str:
    result = []
    previous = 0
    for point in sorted(points):
        result.append(word[previous:point])
        previous = point
    result.append(word[previous:])
    return "·".join(result)


def _open_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def audit_root_conflicts(
    db_path: Path,
    inventory_path: Path | None,
    review_path: Path | None,
    limit: int,
) -> dict[str, object]:
    """Find engine morpheme seams that cut through an RMSS bold root.

    This is deliberately a candidate detector, not a source of gold decisions.
    A candidate is retained only when the engine-created seam is an actual
    preferred break and differs from the whole-word PSP syllabic fallback.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from slabika.typo import _psp_points, break_points, hyphenate
    from slabika.syllabify import get_morpheme_parts

    corpus: set[str] | None = None
    if inventory_path is not None:
        with closing(_open_readonly(inventory_path)) as inventory:
            corpus = {
                unicodedata.normalize("NFC", row[0]).casefold()
                for row in inventory.execute(
                    "SELECT form FROM forms WHERE casing_status = 'resolved' ORDER BY form"
                )
                if row[0].islower() and row[0].isalpha()
            }

    with closing(_open_readonly(db_path)) as connection:
        spans_by_entry: dict[int, list[sqlite3.Row]] = defaultdict(list)
        for span in connection.execute(
            """SELECT entry_id, position, surface, role
               FROM entry_style_spans ORDER BY entry_id, position"""
        ):
            spans_by_entry[span["entry_id"]].append(span)

        aligned = []
        root_support: defaultdict[str, int] = defaultdict(int)
        for row in connection.execute(
            """SELECT e.id AS entry_id, e.analysis, e.printed_page,
                      v.notation, v.surface
               FROM entries e JOIN entry_variants v ON v.entry_id = e.id
               WHERE e.parse_status = 'parsed'
               ORDER BY e.id, v.variant_no"""
        ):
            word = row["surface"]
            if (
                not word.isalpha()
                or " " in word
                or notation_to_surface(row["analysis"]) != word
                or notation_to_surface(row["notation"]) != word
                or (corpus is not None and word.casefold() not in corpus)
            ):
                continue
            spans = spans_by_entry[row["entry_id"]]
            if "".join(span["surface"] for span in spans) != word:
                continue
            roots = []
            offset = 0
            for span in spans:
                end = offset + len(span["surface"])
                if span["role"] in {"root", "root_grammatical"} and span["surface"]:
                    root = span["surface"]
                    roots.append((offset, end, root))
                    root_support[_plain(root)] += 1
                offset = end
            if roots:
                aligned.append((row, roots))

    candidates: dict[tuple[str, int, int, str], dict[str, object]] = {}
    for row, roots in aligned:
        word = row["surface"]
        parts = get_morpheme_parts(word)
        engine_points = set(break_points(word))
        fallback_points = set(_psp_points(word))
        engine_seams = _seams(parts)
        for start, end, root in roots:
            forced = sorted(
                point
                for point in engine_seams & engine_points - fallback_points
                if start < point < end
            )
            if not forced:
                continue
            key = (word.casefold(), start, end, _plain(root))
            candidates[key] = {
                "form": word,
                "engine_hyphenation": hyphenate(word),
                "syllabic_fallback": _marked(word, fallback_points),
                "engine_morphemes": parts,
                "rmss_analysis": row["analysis"],
                "rmss_root": root,
                "root_span": [start, end],
                "forced_points_inside_root": forced,
                "root_support": root_support[_plain(root)],
                "rmss_printed_page": row["printed_page"],
            }

    evidence: dict[str, sqlite3.Row] = {}
    if review_path is not None and candidates:
        forms = sorted({candidate["form"] for candidate in candidates.values()})
        placeholders = ",".join("?" for _ in forms)
        with closing(_open_readonly(review_path)) as review:
            rows = review.execute(
                f"""SELECT form, psp_hyphenation, psp_variants,
                            engine_current_verdict, psp_reference, reason, audited_at
                     FROM psp_comparisons
                     WHERE form IN ({placeholders})
                     ORDER BY audited_at DESC""",
                forms,
            )
            for row in rows:
                evidence.setdefault(row["form"].casefold(), row)

    counts: defaultdict[str, int] = defaultdict(int)
    items = []
    for key, candidate in candidates.items():
        row = evidence.get(key[0])
        if row is None:
            status = "needs_psp_review"
        elif row["engine_current_verdict"] == "unresolved":
            status = "psp_unresolved"
        else:
            variants = set(json.loads(row["psp_variants"] or "[]"))
            variants.add(row["psp_hyphenation"])
            status = (
                "psp_supported"
                if candidate["engine_hyphenation"] in variants
                else "confirmed_current_mismatch"
            )
        counts[status] += 1
        candidate["status"] = status
        if row is not None:
            candidate["psp_hyphenation"] = row["psp_hyphenation"]
            candidate["psp_reference"] = row["psp_reference"]
            candidate["psp_reason"] = row["reason"]
        items.append(candidate)

    priority = {
        "confirmed_current_mismatch": 0,
        "needs_psp_review": 1,
        "psp_unresolved": 2,
        "psp_supported": 3,
    }
    items.sort(
        key=lambda item: (
            priority[item["status"]],
            -item["root_support"],
            item["form"].casefold(),
        )
    )
    return {
        "method": (
            "engine morpheme seam strictly inside an aligned RMSS bold root, "
            "used as a preferred break, and absent from whole-word PSP syllabic fallback"
        ),
        "authority_warning": "RMSS is evidence and candidate generation only; PSP decides correctness.",
        "corpus_only": inventory_path is not None,
        "aligned_entries": len(aligned),
        "candidate_count": len(items),
        "status_counts": dict(sorted(counts.items())),
        "items": items[:limit],
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    build.add_argument("--db", type=Path, default=DEFAULT_DB)
    build.add_argument("--tsv", type=Path)
    search = subparsers.add_parser("query")
    search.add_argument("term")
    search.add_argument("--db", type=Path, default=DEFAULT_DB)
    search.add_argument("--limit", type=int, default=20)
    role_search = subparsers.add_parser("query-role")
    role_search.add_argument("role", choices=("root", "grammatical"))
    role_search.add_argument("term")
    role_search.add_argument("--db", type=Path, default=DEFAULT_DB)
    role_search.add_argument("--limit", type=int, default=20)
    root_audit = subparsers.add_parser("audit-roots")
    root_audit.add_argument("--db", type=Path, default=DEFAULT_DB)
    root_audit.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    root_audit.add_argument("--review-db", type=Path, default=DEFAULT_REVIEW)
    root_audit.add_argument("--all-rmss", action="store_true")
    root_audit.add_argument("--without-review", action="store_true")
    root_audit.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    if args.command == "build":
        print(json.dumps(build_index(args.pdf, args.db, args.tsv), ensure_ascii=False, indent=2))
    elif args.command == "query":
        for row in query(args.db, args.term, args.limit):
            print(
                f"{row['surface']}\t{row['notation']}\tkorene={row['roots'] or '-'}\t"
                f"gram={row['grammatical'] or '-'}\t{row['flex_code']}\ts. {row['printed_page']}"
            )
    elif args.command == "query-role":
        for row in query_role(args.db, args.term, args.role, args.limit):
            print(
                f"{row['surface'] or '-'}\t{row['notation'] or row['analysis']}\t"
                f"{args.role}={row['matched_span']}\t{row['flex_code'] or '-'}\t"
                f"s. {row['printed_page']}"
            )
    else:
        report = audit_root_conflicts(
            args.db,
            None if args.all_rmss else args.inventory,
            None if args.without_review else args.review_db,
            args.limit,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
