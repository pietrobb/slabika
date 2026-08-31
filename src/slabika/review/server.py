# SPDX-FileCopyrightText: 2026 Peter Bezemek <peter.bezemek@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Local review console for a Slovak word-division corpus.

Serves a keyboard-driven browser interface over an inventory database so a
human can confirm, correct or flag the engine's division of every form.

The inventory database is opened READ-ONLY.  Every human decision is written
to a separate decision store, so a slip of a finger can always be undone and
the audited inventory artifact is never touched by the console.

Standard library only:

    slabika-review
"""

from __future__ import annotations

import argparse
import errno
import json
import re
import sqlite3
import threading
import unicodedata
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from slabika import __version__ as ENGINE_VERSION
from slabika import hyphenate, syllables

from .tex_patterns import tex_hyphenate

_PACKAGE_DIR = Path(__file__).resolve().parent
_SOURCE_ROOT = _PACKAGE_DIR.parents[2]
_SOURCE_DATA = _SOURCE_ROOT / "tests" / "data"
_PACKAGE_DATA = _PACKAGE_DIR / "data"
UI_PATH = _PACKAGE_DIR / "ui.html"


def _data_path(source: Path, packaged_name: str) -> Path:
    return source if source.exists() else _PACKAGE_DATA / packaged_name


DEFAULT_INVENTORY = _data_path(
    _SOURCE_DATA / "translatemaster_hyphenation_working.sqlite", "inventory.sqlite"
)
DEFAULT_BLIND = [
    _data_path(
        _SOURCE_DATA / "blind_word_division_5000_v1" / "results.sqlite",
        "blind-word-division-5000.sqlite",
    ),
    _data_path(
        _SOURCE_DATA / "blind_human_recheck_100_v1" / "results.sqlite",
        "blind-human-recheck-100.sqlite",
    ),
    _data_path(
        _SOURCE_DATA / "blind_human_recheck_1000_v2" / "results.sqlite",
        "blind-human-recheck-1000.sqlite",
    ),
    _data_path(
        _SOURCE_DATA / "blind_human_recheck_2000_v3" / "results.sqlite",
        "blind-human-recheck-2000.sqlite",
    ),
]

OUTPUT_ACTIONS = ("confirm", "correct")
ROW_ACTIONS = ("flag", "uncertain", "invalid")
ACTIONS = OUTPUT_ACTIONS + ROW_ACTIONS + ("classify",)

DECISION_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    form TEXT PRIMARY KEY,
    action TEXT NOT NULL CHECK(action IN
        ('confirm', 'correct', 'flag', 'uncertain', 'invalid', 'classify')),
    row_action TEXT CHECK(row_action IN ('flag', 'uncertain', 'invalid')),
    hyphenation_action TEXT CHECK(hyphenation_action IN ('confirm', 'correct')),
    syllabification_action TEXT CHECK(syllabification_action IN ('confirm', 'correct')),
    expected_hyphenation TEXT,
    expected_syllabification TEXT,
    engine_hyphenation TEXT NOT NULL,
    engine_syllabification TEXT NOT NULL,
    hyphenation_engine_version TEXT,
    syllabification_engine_version TEXT,
    is_foreign_word INTEGER CHECK(is_foreign_word IN (0, 1)),
    is_proper_name INTEGER CHECK(is_proper_name IN (0, 1)),
    is_abbreviation INTEGER CHECK(is_abbreviation IN (0, 1)),
    corrected_form TEXT,
    is_deleted INTEGER CHECK(is_deleted IN (0, 1)),
    reason TEXT NOT NULL DEFAULT '',
    engine_version TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    decision_seq INTEGER NOT NULL DEFAULT 0,
    CHECK(expected_hyphenation IS NULL
          OR replace(expected_hyphenation, '·', '') = form)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS decision_log (
    entry_id INTEGER PRIMARY KEY,
    form TEXT NOT NULL,
    operation TEXT NOT NULL CHECK(operation IN ('decide', 'undo')),
    action TEXT,
    expected_hyphenation TEXT,
    expected_syllabification TEXT,
    engine_hyphenation TEXT,
    is_foreign_word INTEGER,
    is_proper_name INTEGER,
    is_abbreviation INTEGER,
    corrected_form TEXT,
    is_deleted INTEGER,
    previous_json TEXT,
    engine_version TEXT NOT NULL,
    logged_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS decisions_action ON decisions(action);

CREATE TABLE IF NOT EXISTS psp_comparisons (
    form TEXT NOT NULL,
    audit_id TEXT NOT NULL,
    family TEXT NOT NULL,
    chlebikova_hyphenation TEXT NOT NULL,
    engine_before_hyphenation TEXT NOT NULL,
    engine_after_hyphenation TEXT NOT NULL,
    engine_tex_before_hyphenation TEXT NOT NULL,
    engine_tex_after_hyphenation TEXT NOT NULL,
    psp_hyphenation TEXT NOT NULL,
    psp_tex_hyphenation TEXT NOT NULL,
    psp_variants TEXT NOT NULL DEFAULT '[]',
    engine_current_verdict TEXT NOT NULL CHECK(engine_current_verdict IN
        ('correct', 'incorrect', 'unresolved')),
    chlebikova_verdict TEXT NOT NULL CHECK(chlebikova_verdict IN
        ('correct', 'incorrect', 'unresolved')),
    comparison_outcome TEXT NOT NULL CHECK(comparison_outcome IN
        ('both_correct', 'engine_only', 'chlebikova_only',
         'both_incorrect', 'unresolved')),
    verdict TEXT NOT NULL CHECK(verdict IN
        ('engine_corrected', 'engine_matches_psp', 'chlebikova_matches_psp',
         'both_match_psp', 'unresolved')),
    psp_reference TEXT NOT NULL,
    reason TEXT NOT NULL,
    comparison_note TEXT NOT NULL DEFAULT '',
    left_min INTEGER NOT NULL,
    right_min INTEGER NOT NULL,
    engine_before_ref TEXT NOT NULL,
    engine_after_ref TEXT NOT NULL,
    audited_at TEXT NOT NULL,
    PRIMARY KEY(form, audit_id),
    CHECK(reason <> ''),
    CHECK(psp_reference <> '')
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS psp_comparisons_form ON psp_comparisons(form);

CREATE TABLE IF NOT EXISTS psp_comparison_log (
    entry_id INTEGER PRIMARY KEY,
    form TEXT NOT NULL,
    audit_id TEXT NOT NULL,
    operation TEXT NOT NULL CHECK(operation = 'replace'),
    previous_json TEXT NOT NULL,
    supersession_reason TEXT NOT NULL CHECK(supersession_reason <> ''),
    replaced_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS psp_comparison_log_form
ON psp_comparison_log(form, audit_id);

CREATE TABLE IF NOT EXISTS psp_unresolved_classifications (
    form TEXT NOT NULL,
    audit_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN
        ('foreign_pronunciation', 'damaged_form', 'other_evidence_limited')),
    note TEXT NOT NULL,
    classified_at TEXT NOT NULL,
    PRIMARY KEY(form, audit_id),
    FOREIGN KEY(form, audit_id) REFERENCES psp_comparisons(form, audit_id)
        ON DELETE CASCADE
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS psp_unresolved_kind
ON psp_unresolved_classifications(kind);

CREATE TABLE IF NOT EXISTS psp_audit_runs (
    audit_id TEXT PRIMARY KEY,
    engine_ref TEXT NOT NULL,
    chlebikova_ref TEXT NOT NULL,
    left_min INTEGER NOT NULL,
    right_min INTEGER NOT NULL,
    batch_size INTEGER NOT NULL CHECK(batch_size = 100),
    total_items INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('building', 'frozen')),
    frozen_at TEXT NOT NULL
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS psp_audit_items (
    audit_id TEXT NOT NULL REFERENCES psp_audit_runs(audit_id) ON DELETE RESTRICT,
    position INTEGER NOT NULL CHECK(position >= 1),
    form TEXT NOT NULL,
    engine_hyphenation TEXT NOT NULL,
    engine_tex_hyphenation TEXT NOT NULL,
    chlebikova_hyphenation TEXT NOT NULL,
    PRIMARY KEY(audit_id, position),
    UNIQUE(audit_id, form),
    CHECK(engine_tex_hyphenation <> chlebikova_hyphenation)
) WITHOUT ROWID;

CREATE TRIGGER IF NOT EXISTS psp_audit_items_insert_only_while_building
BEFORE INSERT ON psp_audit_items
WHEN COALESCE((SELECT status FROM psp_audit_runs WHERE audit_id = NEW.audit_id), '') <> 'building'
BEGIN
    SELECT RAISE(ABORT, 'PSP audit is frozen');
END;

CREATE TRIGGER IF NOT EXISTS psp_audit_items_no_update
BEFORE UPDATE ON psp_audit_items
BEGIN
    SELECT RAISE(ABORT, 'PSP audit snapshot is immutable');
END;

CREATE TRIGGER IF NOT EXISTS psp_audit_items_no_delete
BEFORE DELETE ON psp_audit_items
BEGIN
    SELECT RAISE(ABORT, 'PSP audit snapshot is immutable');
END;

CREATE TRIGGER IF NOT EXISTS psp_audit_runs_no_reopen
BEFORE UPDATE OF status ON psp_audit_runs
WHEN OLD.status = 'frozen'
BEGIN
    SELECT RAISE(ABORT, 'PSP audit is frozen');
END;

CREATE TRIGGER IF NOT EXISTS psp_audit_runs_no_update_when_frozen
BEFORE UPDATE ON psp_audit_runs
WHEN OLD.status = 'frozen'
BEGIN
    SELECT RAISE(ABORT, 'PSP audit snapshot is immutable');
END;

CREATE TRIGGER IF NOT EXISTS psp_audit_runs_no_delete
BEFORE DELETE ON psp_audit_runs
BEGIN
    SELECT RAISE(ABORT, 'PSP audit snapshot is immutable');
END;
"""


def _fold(value: str) -> str:
    """Casefold and strip diacritics, so filters match the way people type."""
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _parse_marked(form: str, text: str) -> str:
    """Read a reviewer-typed division back into the canonical dot form.

    The reviewer types hyphens because that is what a keyboard has.  Runs of
    separators collapse and edge separators are dropped, so a stray dash does
    not become a rejected submission; what must hold exactly is the letters.
    """
    normalised = re.sub(r"[-·\u2010-\u2015\s]+", "·", text.strip()).strip("·")
    if normalised.replace("·", "") != form:
        raise ValueError(
            f"{text!r} nie je {form!r} — po odstránení pomlčiek musí zostať presne ten tvar"
        )
    return normalised


def _recase(parts: list[str], form: str) -> str:
    """Restore the form's own casing onto engine output, which is lowercased."""
    out, at = [], 0
    for part in parts:
        out.append(form[at:at + len(part)])
        at += len(part)
    return "·".join(out) if at == len(form) else "·".join(parts)


def _recase_marked(text: str | None, form: str) -> str | None:
    return _recase(text.split("·"), form) if text is not None else None


def _tex_mode(marked: str, form: str, left_min: int = 2, right_min: int = 3) -> str:
    """Apply TeX edge minima to an already hyphenated engine result."""
    parts = marked.split("·")
    offsets = []
    offset = 0
    for part in parts[:-1]:
        offset += len(part)
        if left_min <= offset <= len(form) - right_min:
            offsets.append(offset)

    out = []
    previous = 0
    for offset in offsets:
        out.append(form[previous:offset])
        previous = offset
    out.append(form[previous:])
    return "·".join(out)


def _engine(form: str) -> tuple[str, str, str | None]:
    try:
        return hyphenate(form), _recase(syllables(form), form), None
    except Exception as error:  # noqa: BLE001 - shown to the reviewer
        return form, form, f"{type(error).__name__}: {error}"


def _hyphenation_match_mode(
    form: str, expected: str | None, preferred: str | None = None
) -> str | None:
    if expected is None:
        return None
    candidates = (
        ("preferred", preferred if preferred is not None else hyphenate(form)),
        ("permissive", hyphenate(form, all_points=True)),
        ("contextual", hyphenate(form, contextual=True)),
        ("permissive_contextual", hyphenate(form, all_points=True, contextual=True)),
    )
    target = expected.casefold()
    return next((mode for mode, output in candidates if output.casefold() == target), None)


_DAMAGED_UNRESOLVED = re.compile(
    r"fragment|poškoden|neúpl|odtrhn|preklep|zliat|chybne spojen|"
    r"riadkov(?:ého|ý|o|om|ú)? (?:delen|zalomen|odtrh)|nedokončen|"
    r"skráten(?:ý|á|é) (?:tvar|zápis)|odseknut",
    re.IGNORECASE,
)
_FOREIGN_UNRESOLVED = re.compile(
    r"cudz|foreign|výslov|§5\.4|V\.4|latinsk|anglick|nemeck|francúz|"
    r"gréck|\bmeno\b|proper",
    re.IGNORECASE,
)


def classify_unresolved_evidence(
    family: str, psp_reference: str, reason: str, comparison_note: str = ""
) -> str:
    evidence = " ".join((family, psp_reference, reason, comparison_note))
    if _DAMAGED_UNRESOLVED.search(evidence):
        return "damaged_form"
    if _FOREIGN_UNRESOLVED.search(evidence):
        return "foreign_pronunciation"
    return "other_evidence_limited"


def _load_blind(paths: Path | list[Path] | tuple[Path, ...] | None) -> dict[str, dict]:
    """Verdicts of independent blind audits, keyed by lowercase form."""
    if isinstance(paths, Path):
        paths = (paths,)
    verdicts = {}
    for path in paths or ():
        if not path.exists():
            continue
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        rows = connection.execute(
            "SELECT form, assessment, expected_variants_json, confidence FROM decisions"
        ).fetchall()
        connection.close()
        verdicts.update({
            form: {
                "assessment": assessment,
                "variants": [v.replace("|", "·") for v in json.loads(variants or "[]")],
                "confidence": confidence,
            }
            for form, assessment, variants, confidence in rows
        })
    return verdicts


class Corpus:
    """Read-only view of the inventory plus a writable decision store."""

    def __init__(
        self,
        inventory: Path,
        decisions: Path,
        blind: Path | list[Path] | tuple[Path, ...] | None = None,
    ) -> None:
        self.lock = threading.Lock()
        self.inventory_path = inventory
        self.decisions_path = decisions
        self.blind = _load_blind(blind)

        self.inventory = sqlite3.connect(
            f"file:{inventory.as_posix()}?mode=ro", uri=True, check_same_thread=False
        )
        self.inventory.row_factory = sqlite3.Row

        self.store = sqlite3.connect(decisions, check_same_thread=False)
        self.store.row_factory = sqlite3.Row
        self.store.executescript(DECISION_SCHEMA)
        psp_columns = {
            row[1] for row in self.store.execute("PRAGMA table_info(psp_comparisons)")
        }
        if "psp_variants" not in psp_columns:
            self.store.execute(
                "ALTER TABLE psp_comparisons ADD COLUMN "
                "psp_variants TEXT NOT NULL DEFAULT '[]'"
            )
            rows = self.store.execute(
                """SELECT form, audit_id, psp_hyphenation
                   FROM psp_comparisons
                   WHERE engine_current_verdict <> 'unresolved'"""
            ).fetchall()
            self.store.executemany(
                """UPDATE psp_comparisons SET psp_variants = ?
                   WHERE form = ? AND audit_id = ?""",
                [
                    (json.dumps([row["psp_hyphenation"]], ensure_ascii=False),
                     row["form"], row["audit_id"])
                    for row in rows
                ],
            )
        if "comparison_outcome" not in psp_columns:
            self.store.execute(
                """ALTER TABLE psp_comparisons ADD COLUMN comparison_outcome TEXT
                   NOT NULL DEFAULT 'unresolved' CHECK(comparison_outcome IN
                   ('both_correct', 'engine_only', 'chlebikova_only',
                    'both_incorrect', 'unresolved'))"""
            )
            self.store.execute(
                """UPDATE psp_comparisons SET comparison_outcome = CASE
                       WHEN engine_current_verdict = 'unresolved'
                         OR chlebikova_verdict = 'unresolved' THEN 'unresolved'
                       WHEN engine_current_verdict = 'correct'
                         AND chlebikova_verdict = 'correct' THEN 'both_correct'
                       WHEN engine_current_verdict = 'correct' THEN 'engine_only'
                       WHEN chlebikova_verdict = 'correct' THEN 'chlebikova_only'
                       ELSE 'both_incorrect'
                   END"""
            )
        columns = {row[1] for row in self.store.execute("PRAGMA table_info(decisions)")}
        for column in (
            "row_action",
            "hyphenation_action",
            "syllabification_action",
            "hyphenation_engine_version",
            "syllabification_engine_version",
        ):
            if column not in columns:
                self.store.execute(f"ALTER TABLE decisions ADD COLUMN {column} TEXT")
        if "decision_seq" not in columns:
            self.store.execute(
                "ALTER TABLE decisions ADD COLUMN decision_seq INTEGER NOT NULL DEFAULT 0"
            )
        if "corrected_form" not in columns:
            self.store.execute("ALTER TABLE decisions ADD COLUMN corrected_form TEXT")
        if "is_deleted" not in columns:
            self.store.execute(
                "ALTER TABLE decisions ADD COLUMN is_deleted INTEGER "
                "CHECK(is_deleted IN (0, 1))"
            )
        log_columns = {
            row[1] for row in self.store.execute("PRAGMA table_info(decision_log)")
        }
        for column, definition in (
            ("is_foreign_word", "INTEGER"),
            ("is_proper_name", "INTEGER"),
            ("is_abbreviation", "INTEGER"),
            ("corrected_form", "TEXT"),
            ("is_deleted", "INTEGER"),
        ):
            if column not in log_columns:
                self.store.execute(
                    f"ALTER TABLE decision_log ADD COLUMN {column} {definition}"
                )
        self.store.execute(
            """UPDATE decisions SET row_action = action
               WHERE action IN ('flag', 'uncertain', 'invalid') AND row_action IS NULL"""
        )
        self.store.execute(
            """UPDATE decisions SET hyphenation_action = action
               WHERE expected_hyphenation IS NOT NULL
                 AND action IN ('confirm', 'correct')
                 AND hyphenation_action IS NULL"""
        )
        self.store.execute(
            """UPDATE decisions SET syllabification_action = action
               WHERE expected_syllabification IS NOT NULL
                 AND action IN ('confirm', 'correct')
                 AND syllabification_action IS NULL"""
        )
        self.store.execute(
            """UPDATE decisions SET hyphenation_engine_version = engine_version
               WHERE hyphenation_action IS NOT NULL
                 AND hyphenation_engine_version IS NULL"""
        )
        self.store.execute(
            """UPDATE decisions SET syllabification_engine_version = engine_version
               WHERE syllabification_action IS NOT NULL
                 AND syllabification_engine_version IS NULL"""
        )
        self.store.commit()

        form_rows = list(
            self.inventory.execute(
                """SELECT f.form, a.review_status
                   FROM forms AS f
                   LEFT JOIN adjudications AS a USING (form)"""
            )
        )
        inventory_forms = {row["form"] for row in form_rows}
        self.review_forms: dict[str, str] = {
            row["form"]: (
                row["form"].lower()
                if row["form"][:1].isupper()
                and row["form"].lower() in inventory_forms
                else row["form"]
            )
            for row in form_rows
        }
        decision_rows = list(self.store.execute("SELECT form, action FROM decisions"))
        self.decided: dict[str, str] = {row["form"]: row["action"] for row in decision_rows}
        self.ai: dict[str, str] = {
            row["form"]: row["review_status"] for row in form_rows
        }
        alias_groups: dict[str, list[str]] = {}
        for form, review_form in self.review_forms.items():
            alias_groups.setdefault(review_form, []).append(form)
        self.aliases: dict[str, tuple[str, ...]] = {
            review_form: tuple(sorted(forms))
            for review_form, forms in alias_groups.items()
        }
        self.representative_for_form: dict[str, str] = {
            form: review_form
            for review_form, forms in self.aliases.items()
            for form in forms
        }
        self.forms: list[str] = sorted(
            self.aliases,
            key=lambda form: (_fold(form), form),
        )
        self.folded: list[str] = [_fold(form) for form in self.forms]
        self.form_set: set[str] = set(self.review_forms)
        self._tex_disagreements: frozenset[str] | None = None

    # -- reading ---------------------------------------------------------

    def matches(self, query: str, mode: str) -> list[str]:
        if not query:
            return self.forms
        if mode == "regex":
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as error:
                raise ValueError(f"zlý regex: {error}") from error
            return [
                form for form in self.forms
                if pattern.search(self.review_forms[form])
            ]
        needle = _fold(query)
        if mode == "prefix":
            test = str.startswith
        elif mode == "suffix":
            test = str.endswith
        elif mode == "exact":
            test = str.__eq__
        else:
            test = str.__contains__
        return [self.forms[i] for i, folded in enumerate(self.folded) if test(folded, needle)]

    def _alias_forms(self, form: str) -> tuple[str, ...]:
        representative = self.representative_for_form.get(form, form)
        return self.aliases.get(representative, (form,))

    def _ai_row_groups(self, forms: list[str]) -> dict[str, list[sqlite3.Row]]:
        source_forms = sorted({alias for form in forms for alias in self._alias_forms(form)})
        source_rows: dict[str, sqlite3.Row] = {}
        for start in range(0, len(source_forms), 800):
            chunk = source_forms[start : start + 800]
            placeholders = ",".join("?" * len(chunk))
            for row in self.inventory.execute(
                f"SELECT * FROM adjudications WHERE form IN ({placeholders})", chunk
            ):
                source_rows[row["form"]] = row
        return {
            form: [source_rows[alias] for alias in self._alias_forms(form) if alias in source_rows]
            for form in forms
        }

    def _ai_rows(self, forms: list[str]) -> dict[str, sqlite3.Row]:
        rank = {"invalid": 0, "human_review": 1, "verified": 2, "ai_agrees": 3, "pending": 4}
        return {
            form: min(
                rows,
                key=lambda row: (
                    rank.get(row["review_status"], 4),
                    row["form"] != form,
                    row["form"],
                ),
            )
            for form, rows in self._ai_row_groups(forms).items()
            if rows
        }

    def _decision_row_groups(self, forms: list[str]) -> dict[str, list[sqlite3.Row]]:
        source_forms = sorted(
            {
                alias
                for form in forms
                for alias in self._alias_forms(form)
                if alias in self.decided
            }
        )
        source_rows: dict[str, sqlite3.Row] = {}
        for start in range(0, len(source_forms), 800):
            chunk = source_forms[start : start + 800]
            placeholders = ",".join("?" * len(chunk))
            for row in self.store.execute(
                f"SELECT * FROM decisions WHERE form IN ({placeholders})", chunk
            ):
                source_rows[row["form"]] = row
        return {
            form: [source_rows[alias] for alias in self._alias_forms(form) if alias in source_rows]
            for form in forms
        }

    def _decision_rows(self, forms: list[str]) -> dict[str, sqlite3.Row]:
        return {
            form: max(
                rows,
                key=lambda row: (
                    row["decision_seq"],
                    row["decided_at"],
                    row["form"] == self.representative_for_form.get(form, form),
                ),
            )
            for form, rows in self._decision_row_groups(forms).items()
            if rows
        }

    def _psp_rows(self, forms: list[str]) -> dict[str, sqlite3.Row]:
        source_forms = sorted({alias for form in forms for alias in self._alias_forms(form)})
        source_rows: dict[str, sqlite3.Row] = {}
        for start in range(0, len(source_forms), 800):
            chunk = source_forms[start : start + 800]
            placeholders = ",".join("?" * len(chunk))
            for row in self.store.execute(
                f"""SELECT c.*, u.kind AS unresolved_kind,
                           u.note AS unresolved_note
                    FROM psp_comparisons AS c
                    LEFT JOIN psp_unresolved_classifications AS u
                      ON u.form = c.form AND u.audit_id = c.audit_id
                    WHERE c.form IN ({placeholders})
                    ORDER BY c.audited_at, c.audit_id""",
                chunk,
            ):
                source_rows[row["form"]] = row
        return {
            form: max(
                (source_rows[alias] for alias in self._alias_forms(form) if alias in source_rows),
                key=lambda row: (row["audited_at"], row["audit_id"]),
            )
            for form in forms
            if any(alias in source_rows for alias in self._alias_forms(form))
        }

    def item(
        self,
        form: str,
        ai: sqlite3.Row | None,
        mine: sqlite3.Row | None,
        psp: sqlite3.Row | None = None,
    ) -> dict:
        review_form = self.review_forms[form]
        hyphenation, syllabification, error = _engine(review_form)
        engine_tex = _tex_mode(hyphenation, review_form)
        ai_expected = _recase_marked(
            ai["expected_hyphenation"] if ai else None, review_form
        )
        ai_syllabification = _recase_marked(
            ai["expected_syllabification"] if ai else None, review_form
        )
        my_expected = _recase_marked(
            mine["expected_hyphenation"] if mine else None, review_form
        )
        my_match_mode = _hyphenation_match_mode(review_form, my_expected, hyphenation)
        my_hyphenation_action = mine["hyphenation_action"] if mine else None
        my_syllabification_action = mine["syllabification_action"] if mine else None

        def flag(field: str) -> int | None:
            if mine and mine[field] is not None:
                return mine[field]
            return ai[field] if ai else None

        blind = self.blind.get(review_form.lower(), {})
        blind_variants = [
            _recase_marked(variant, review_form) for variant in blind.get("variants", [])
        ]
        try:
            tex = _recase_marked(tex_hyphenate(review_form.lower()), review_form)
        except Exception:  # noqa: BLE001 - an advisory voice must never break a row
            tex = None
        psp_comparison = None
        if psp:
            psp_variants = [
                _recase_marked(variant, review_form)
                for variant in json.loads(psp["psp_variants"])
            ]
            psp_comparison = {
                "audit_id": psp["audit_id"],
                "family": psp["family"],
                "chlebikova": _recase_marked(
                    psp["chlebikova_hyphenation"], review_form
                ),
                "engine_before": _recase_marked(
                    psp["engine_before_hyphenation"], review_form
                ),
                "engine_after": _recase_marked(
                    psp["engine_after_hyphenation"], review_form
                ),
                "engine_tex_before": _recase_marked(
                    psp["engine_tex_before_hyphenation"], review_form
                ),
                "engine_tex_after": _recase_marked(
                    psp["engine_tex_after_hyphenation"], review_form
                ),
                "psp": _recase_marked(psp["psp_hyphenation"], review_form),
                "psp_tex": _recase_marked(psp["psp_tex_hyphenation"], review_form),
                "psp_variants": psp_variants,
                "psp_tex_variants": [
                    _tex_mode(variant, review_form) for variant in psp_variants
                ],
                "engine_current_verdict": psp["engine_current_verdict"],
                "chlebikova_verdict": psp["chlebikova_verdict"],
                "comparison_outcome": psp["comparison_outcome"],
                "unresolved_kind": psp["unresolved_kind"],
                "unresolved_note": psp["unresolved_note"],
                "verdict": psp["verdict"],
                "psp_reference": psp["psp_reference"],
                "reason": psp["reason"],
                "comparison_note": psp["comparison_note"],
                "left_min": psp["left_min"],
                "right_min": psp["right_min"],
                "engine_before_ref": psp["engine_before_ref"],
                "engine_after_ref": psp["engine_after_ref"],
                "audited_at": psp["audited_at"],
            }

        return {
            "form": form,
            "review_form": review_form,
            "hyphenation": hyphenation,
            "engine_tex": engine_tex,
            "syllabification": syllabification,
            "engine_error": error,
            "tex": tex,
            "tex_disagrees": bool(tex) and tex != engine_tex,
            "psp_comparison": psp_comparison,
            "blind_assessment": blind.get("assessment"),
            "blind_variants": blind_variants,
            "blind_disagrees": bool(blind_variants) and hyphenation not in blind_variants,
            "ai_status": ai["review_status"] if ai else "pending",
            "ai_expected": ai_expected,
            "ai_reason": ai["reason"] if ai else "",
            "ai_disagrees": bool(ai_expected) and ai_expected != hyphenation,
            "ai_syllabification": ai_syllabification,
            "ai_disagrees_syl": (
                bool(ai_syllabification)
                and ai_syllabification.lower() != syllabification.lower()
            ),
            "my_action": mine["action"] if mine else None,
            "my_row_action": mine["row_action"] if mine else None,
            "my_hyphenation_action": my_hyphenation_action,
            "my_syllabification_action": my_syllabification_action,
            "my_classification": bool(mine) and any(
                mine[field] is not None
                for field in (
                    "is_foreign_word",
                    "is_proper_name",
                    "is_abbreviation",
                    "corrected_form",
                    "is_deleted",
                )
            ),
            "my_flags": {
                "foreign": mine["is_foreign_word"] if mine else None,
                "proper": mine["is_proper_name"] if mine else None,
                "abbreviation": mine["is_abbreviation"] if mine else None,
                "deleted": mine["is_deleted"] if mine else None,
            },
            "my_expected": my_expected,
            "my_hyphenation_match_mode": my_match_mode,
            "my_syllabification": _recase_marked(
                mine["expected_syllabification"] if mine else None, review_form
            ),
            "my_disagrees": bool(my_expected) and my_match_mode is None,
            "stale_h": (
                bool(my_hyphenation_action)
                and (mine["engine_hyphenation"] or "").lower() != hyphenation.lower()
            ),
            "stale_s": (
                bool(my_syllabification_action)
                and (mine["engine_syllabification"] or "").lower()
                != syllabification.lower()
            ),
            "stale": (
                bool(my_hyphenation_action)
                and (mine["engine_hyphenation"] or "").lower() != hyphenation.lower()
            ) or (
                bool(my_syllabification_action)
                and (mine["engine_syllabification"] or "").lower()
                != syllabification.lower()
            ),
            "decided_at": mine["decided_at"] if mine else None,
            "corrected_form": mine["corrected_form"] if mine else None,
            "flags": {
                "foreign": flag("is_foreign_word"),
                "proper": flag("is_proper_name"),
                "abbreviation": flag("is_abbreviation"),
                "deleted": mine["is_deleted"] if mine else None,
            },
        }

    @staticmethod
    def _is_reviewed(row: sqlite3.Row) -> bool:
        return any(
            row[field] is not None
            for field in (
                "hyphenation_action",
                "row_action",
                "is_foreign_word",
                "is_proper_name",
                "is_abbreviation",
                "corrected_form",
                "is_deleted",
            )
        )

    def _filter_status(self, forms: list[str], status: str) -> list[str]:
        if status in ("", "all"):
            return forms
        if status in ("undecided", "incomplete"):
            rows = self._decision_rows(forms)
            return [
                form
                for form in forms
                if form not in rows or not self._is_reviewed(rows[form])
            ]
        if status in OUTPUT_ACTIONS + ROW_ACTIONS:
            rows = self._decision_rows(forms)
            field = "row_action" if status in ROW_ACTIONS else "hyphenation_action"
            return [form for form in forms if form in rows and rows[form][field] == status]
        if status in ("foreign", "proper", "abbreviation", "deleted", "corrected_form"):
            rows = self._decision_rows(forms)
            field = {
                "foreign": "is_foreign_word",
                "proper": "is_proper_name",
                "abbreviation": "is_abbreviation",
                "deleted": "is_deleted",
                "corrected_form": "corrected_form",
            }[status]
            return [form for form in forms if form in rows and rows[form][field]]
        if status == "psp_comparison":
            rows = self._psp_rows(forms)
            return [form for form in forms if form in rows]
        if status == "mine":
            rows = self._decision_rows(forms)
            return [form for form in forms if form in rows and self._is_reviewed(rows[form])]
        if status in ("ai_disagree", "ai_disagree_syl"):
            rows = self._ai_rows(forms)
            field = (
                "expected_hyphenation"
                if status == "ai_disagree"
                else "expected_syllabification"
            )
            engine_index = 0 if status == "ai_disagree" else 1
            return [
                form
                for form in forms
                if form in rows
                and rows[form][field]
                and rows[form][field].lower() != _engine(form)[engine_index].lower()
            ]
        if status == "engine_disagree":
            rows = self._decision_rows(forms)
            return [
                form
                for form in forms
                if form in rows
                and _recase_marked(rows[form]["expected_hyphenation"], form)
                and _hyphenation_match_mode(
                    form,
                    _recase_marked(rows[form]["expected_hyphenation"], form),
                    _engine(form)[0],
                ) is None
            ]
        if status == "engine_error":
            return [form for form in forms if _engine(form)[2] is not None]
        rows = self._ai_rows(forms)
        return [
            form
            for form in forms
            if form in rows and rows[form]["review_status"] == status
        ]

    def precompute_voice_filters(self) -> None:
        if self._tex_disagreements is not None:
            return
        matching = set()
        for form in self.forms:
            review_form = self.review_forms[form]
            try:
                tex = _recase_marked(tex_hyphenate(review_form.lower()), review_form)
            except Exception:  # noqa: BLE001 - an unavailable voice is not a disagreement
                continue
            engine_tex = _tex_mode(_engine(review_form)[0], review_form)
            if tex != engine_tex:
                matching.add(form)
        self._tex_disagreements = frozenset(matching)

    def freeze_psp_audit(
        self,
        audit_id: str,
        engine_ref: str,
        chlebikova_ref: str,
    ) -> dict:
        """Freeze every alphabetic Engine–Chlebíková difference in batches of 100."""
        if not audit_id or not engine_ref or not chlebikova_ref:
            raise ValueError("audit_id, engine_ref a chlebikova_ref sú povinné")
        if self.store.execute(
            "SELECT 1 FROM psp_audit_runs WHERE audit_id = ?", (audit_id,)
        ).fetchone():
            raise ValueError(f"PSP audit {audit_id!r} už existuje")

        rows = []
        forms = sorted(
            (form for form in self.form_set if form.isalpha()),
            key=lambda form: (_fold(form), form),
        )
        for form in forms:
            engine_hyphenation, _, engine_error = _engine(form)
            if engine_error:
                raise RuntimeError(
                    f"engine zlyhal pri zmrazovaní PSP auditu pre {form!r}: "
                    f"{engine_error}"
                )
            engine_hyphenation = _recase_marked(engine_hyphenation, form)
            engine_tex = _tex_mode(engine_hyphenation, form)
            try:
                chlebikova = _recase_marked(tex_hyphenate(form.lower()), form)
            except Exception:  # noqa: BLE001 - unavailable advice is not a difference
                continue
            if engine_tex != chlebikova:
                rows.append((audit_id, len(rows) + 1, form, engine_hyphenation,
                             engine_tex, chlebikova))

        frozen_at = _now()
        with self.lock:
            self.store.execute("BEGIN IMMEDIATE")
            try:
                self.store.execute(
                    """INSERT INTO psp_audit_runs
                       (audit_id, engine_ref, chlebikova_ref, left_min, right_min,
                        batch_size, total_items, status, frozen_at)
                       VALUES (?, ?, ?, 2, 3, 100, 0, 'building', ?)""",
                    (audit_id, engine_ref, chlebikova_ref, frozen_at),
                )
                self.store.executemany(
                    """INSERT INTO psp_audit_items
                       (audit_id, position, form, engine_hyphenation,
                        engine_tex_hyphenation, chlebikova_hyphenation)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    rows,
                )
                self.store.execute(
                    """UPDATE psp_audit_runs
                       SET total_items = ?, status = 'frozen'
                       WHERE audit_id = ?""",
                    (len(rows), audit_id),
                )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
        return self.psp_audit_progress(audit_id)

    def psp_audit_progress(self, audit_id: str | None = None) -> dict | None:
        if audit_id is None:
            run = self.store.execute(
                """SELECT * FROM psp_audit_runs
                   WHERE status = 'frozen'
                   ORDER BY frozen_at DESC, audit_id DESC LIMIT 1"""
            ).fetchone()
        else:
            run = self.store.execute(
                "SELECT * FROM psp_audit_runs WHERE audit_id = ?", (audit_id,)
            ).fetchone()
        if run is None:
            return None

        counts = self.store.execute(
            """SELECT
                   COUNT(c.form) AS adjudicated,
                   SUM(c.engine_current_verdict = 'correct'
                       AND c.chlebikova_verdict = 'correct') AS both_correct,
                   SUM(c.engine_current_verdict = 'correct'
                       AND c.chlebikova_verdict = 'incorrect') AS engine_only,
                   SUM(c.engine_current_verdict = 'incorrect'
                       AND c.chlebikova_verdict = 'correct') AS chlebikova_only,
                   SUM(c.engine_current_verdict = 'incorrect'
                       AND c.chlebikova_verdict = 'incorrect') AS both_incorrect,
                   SUM(c.engine_current_verdict = 'unresolved'
                       OR c.chlebikova_verdict = 'unresolved') AS unresolved
               FROM psp_audit_items AS i
               LEFT JOIN psp_comparisons AS c
                 ON c.audit_id = i.audit_id AND c.form = i.form
               WHERE i.audit_id = ?""",
            (run["audit_id"],),
        ).fetchone()
        unresolved_categories = dict(self.store.execute(
            """SELECT u.kind, COUNT(*)
               FROM psp_unresolved_classifications AS u
               JOIN psp_comparisons AS c
                 ON c.form = u.form AND c.audit_id = u.audit_id
               WHERE u.audit_id = ? AND c.comparison_outcome = 'unresolved'
               GROUP BY u.kind ORDER BY u.kind""",
            (run["audit_id"],),
        ))
        next_row = self.store.execute(
            """SELECT MIN(i.position)
               FROM psp_audit_items AS i
               LEFT JOIN psp_comparisons AS c
                 ON c.audit_id = i.audit_id AND c.form = i.form
               WHERE i.audit_id = ? AND c.form IS NULL""",
            (run["audit_id"],),
        ).fetchone()
        next_position = next_row[0]
        total = run["total_items"]
        batch_size = run["batch_size"]
        return {
            "audit_id": run["audit_id"],
            "engine_ref": run["engine_ref"],
            "chlebikova_ref": run["chlebikova_ref"],
            "left_min": run["left_min"],
            "right_min": run["right_min"],
            "batch_size": batch_size,
            "total": total,
            "batches": (total + batch_size - 1) // batch_size,
            "adjudicated": counts["adjudicated"],
            "both_correct": counts["both_correct"] or 0,
            "engine_only": counts["engine_only"] or 0,
            "chlebikova_only": counts["chlebikova_only"] or 0,
            "both_incorrect": counts["both_incorrect"] or 0,
            "unresolved": counts["unresolved"] or 0,
            "unresolved_categories": unresolved_categories,
            "next_batch": (
                (next_position - 1) // batch_size + 1
                if next_position is not None else None
            ),
            "frozen_at": run["frozen_at"],
        }

    def psp_audit_batch(self, audit_id: str, batch: int) -> dict:
        progress = self.psp_audit_progress(audit_id)
        if progress is None:
            raise ValueError(f"neznámy PSP audit {audit_id!r}")
        if batch < 1 or batch > progress["batches"]:
            raise ValueError(f"dávka musí byť od 1 do {progress['batches']}")
        start = (batch - 1) * progress["batch_size"] + 1
        stop = start + progress["batch_size"]
        rows = self.store.execute(
            """SELECT i.*, c.psp_hyphenation, c.psp_tex_hyphenation,
                      c.psp_variants, c.engine_current_verdict, c.chlebikova_verdict,
                      c.comparison_outcome, c.psp_reference, c.reason,
                      c.comparison_note, c.audited_at
               FROM psp_audit_items AS i
               LEFT JOIN psp_comparisons AS c
                 ON c.audit_id = i.audit_id AND c.form = i.form
               WHERE i.audit_id = ? AND i.position >= ? AND i.position < ?
               ORDER BY i.position""",
            (audit_id, start, stop),
        ).fetchall()
        return {
            "progress": progress,
            "batch": batch,
            "items": [dict(row) for row in rows],
        }

    def adjudicate_psp(self, payload: dict) -> dict:
        audit_id = payload.get("audit_id")
        form = payload.get("form")
        item = self.store.execute(
            """SELECT i.*, r.engine_ref, r.batch_size
               FROM psp_audit_items AS i
               JOIN psp_audit_runs AS r USING (audit_id)
               WHERE i.audit_id = ? AND i.form = ? AND r.status = 'frozen'""",
            (audit_id, form),
        ).fetchone()
        if item is None:
            raise ValueError("tvar nie je v zmrazenom PSP audite")
        psp_reference = (payload.get("psp_reference") or "").strip()
        reason = (payload.get("reason") or "").strip()
        if not psp_reference or not reason:
            raise ValueError("PSP odkaz a stručný dôvod sú povinné")

        psp_input = payload.get("psp_hyphenation")
        unresolved = psp_input is None
        raw_variants = payload.get("psp_variants") or []
        if not isinstance(raw_variants, list):
            raise ValueError("PSP varianty musia byť zoznam")
        if unresolved and raw_variants:
            raise ValueError("nerozhodnutá položka nemôže mať PSP varianty")
        psp_hyphenation = form if unresolved else _parse_marked(form, psp_input)
        psp_variants = [] if unresolved else list(dict.fromkeys([
            psp_hyphenation,
            *(_parse_marked(form, variant) for variant in raw_variants),
        ]))
        psp_tex = _tex_mode(psp_hyphenation, form)
        psp_tex_variants = {_tex_mode(variant, form) for variant in psp_variants}
        engine_after, _, engine_error = _engine(form)
        if engine_error and not unresolved:
            raise RuntimeError(
                f"engine zlyhal pri PSP rozhodovaní pre {form!r}: {engine_error}"
            )
        engine_after = _recase_marked(engine_after, form)
        engine_tex_after = _tex_mode(engine_after, form)
        existing = self.store.execute(
            "SELECT * FROM psp_comparisons WHERE form = ? AND audit_id = ?",
            (form, audit_id),
        ).fetchone()
        replace = bool(payload.get("replace"))
        supersession_reason = (payload.get("supersession_reason") or "").strip()
        comparison_note = payload.get("comparison_note") or ""
        if replace:
            if existing is None:
                raise ValueError("nahrádzaný PSP rozsudok neexistuje")
            if not supersession_reason:
                raise ValueError("dôvod nahradenia skoršieho PSP rozsudku je povinný")
            comparison_note = (
                f"{comparison_note}\nNahrádza rozsudok z {existing['audited_at']}: "
                f"{supersession_reason}"
            ).strip()
        if engine_error:
            comparison_note = (
                f"{comparison_note}\nAktuálny engine zlyhal: {engine_error}"
            ).strip()
        if unresolved:
            engine_verdict = chlebikova_verdict = "unresolved"
            outcome = "unresolved"
            verdict = "unresolved"
        else:
            engine_verdict = (
                "correct" if engine_tex_after in psp_tex_variants else "incorrect"
            )
            chlebikova_verdict = (
                "correct"
                if item["chlebikova_hyphenation"] in psp_tex_variants
                else "incorrect"
            )
            if engine_verdict == chlebikova_verdict == "correct":
                outcome = "both_correct"
                verdict = "both_match_psp"
            elif engine_verdict == "correct":
                outcome = "engine_only"
                verdict = "engine_matches_psp"
            elif chlebikova_verdict == "correct":
                outcome = "chlebikova_only"
                verdict = "chlebikova_matches_psp"
            else:
                outcome = "both_incorrect"
                verdict = "unresolved"

        values = (
            form,
            audit_id,
            payload.get("family") or form,
            item["chlebikova_hyphenation"],
            item["engine_hyphenation"],
            engine_after,
            item["engine_tex_hyphenation"],
            engine_tex_after,
            psp_hyphenation,
            psp_tex,
            json.dumps(psp_variants, ensure_ascii=False),
            engine_verdict,
            chlebikova_verdict,
            outcome,
            verdict,
            psp_reference,
            reason,
            comparison_note,
            2,
            3,
            item["engine_ref"],
            payload.get("engine_after_ref") or f"slabika {ENGINE_VERSION}",
            _now(),
        )
        with self.lock:
            self.store.execute("BEGIN IMMEDIATE")
            try:
                if replace:
                    current = self.store.execute(
                        "SELECT * FROM psp_comparisons WHERE form = ? AND audit_id = ?",
                        (form, audit_id),
                    ).fetchone()
                    if current is None or dict(current) != dict(existing):
                        raise RuntimeError(
                            "PSP rozsudok sa počas nahrádzania zmenil; načítajte ho znova"
                        )
                    self.store.execute(
                        """INSERT INTO psp_comparison_log
                           (form, audit_id, operation, previous_json,
                            supersession_reason, replaced_at)
                           VALUES (?, ?, 'replace', ?, ?, ?)""",
                        (
                            form,
                            audit_id,
                            json.dumps(dict(existing), ensure_ascii=False),
                            supersession_reason,
                            _now(),
                        ),
                    )
                    self.store.execute(
                        "DELETE FROM psp_comparisons WHERE form = ? AND audit_id = ?",
                        (form, audit_id),
                    )
                self.store.execute(
                    """INSERT INTO psp_comparisons
                       (form, audit_id, family, chlebikova_hyphenation,
                        engine_before_hyphenation, engine_after_hyphenation,
                        engine_tex_before_hyphenation, engine_tex_after_hyphenation,
                        psp_hyphenation, psp_tex_hyphenation, psp_variants,
                        engine_current_verdict, chlebikova_verdict,
                        comparison_outcome, verdict, psp_reference, reason,
                        comparison_note, left_min, right_min, engine_before_ref,
                        engine_after_ref, audited_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                               ?, ?, ?, ?, ?, ?)""",
                    values,
                )
                if not unresolved:
                    self.store.execute(
                        """DELETE FROM psp_unresolved_classifications
                           WHERE form = ? AND audit_id = ?""",
                        (form, audit_id),
                    )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
        return self.psp_audit_batch(
            audit_id,
            (item["position"] - 1) // item["batch_size"] + 1,
        )

    def _filter_voice_disagreements(
        self, forms: list[str], tex_diff: bool, blind_human_diff: bool
    ) -> list[str]:
        if tex_diff:
            self.precompute_voice_filters()
            forms = [form for form in forms if form in self._tex_disagreements]
        if blind_human_diff:
            forms = [
                form
                for form in forms
                if self.review_forms[form].lower() in self.blind
            ]
            rows = self._decision_rows(forms)
            matching = []
            for form in forms:
                review_form = self.review_forms[form]
                mine = rows.get(form)
                human = _recase_marked(
                    mine["expected_hyphenation"] if mine else None, review_form
                )
                blind = self.blind.get(review_form.lower(), {})
                variants = [
                    _recase_marked(variant, review_form)
                    for variant in blind.get("variants", [])
                ]
                if human and variants and human not in variants:
                    matching.append(form)
            forms = matching
        return forms

    def page(
        self,
        query: str,
        mode: str,
        status: str,
        offset: int,
        limit: int,
        tex_diff: bool = False,
        blind_human_diff: bool = False,
    ) -> dict:
        candidate = self._filter_status(self.matches(query, mode), status)
        candidate = self._filter_voice_disagreements(
            candidate, tex_diff, blind_human_diff
        )
        window = candidate[offset : offset + limit]
        ai = self._ai_rows(window)
        mine = self._decision_rows(window)
        psp = self._psp_rows(window)
        return {
            "total": len(candidate),
            "offset": offset,
            "items": [
                self.item(form, ai.get(form), mine.get(form), psp.get(form))
                for form in window
            ],
        }

    def stats(self) -> dict:
        decisions = list(self._decision_rows(self.forms).values())

        def count_decisions(field: str, value: str | int | None = None) -> int:
            return sum(
                row[field] is not None if value is None else row[field] == value
                for row in decisions
            )

        ai_rank = {
            "invalid": 0,
            "human_review": 1,
            "verified": 2,
            "ai_agrees": 3,
            "pending": 4,
        }
        ai_review_queue = sum(
            self.ai[
                min(
                    self.aliases[form],
                    key=lambda alias: (
                        ai_rank.get(self.ai.get(alias, "pending"), 4),
                        alias != form,
                        alias,
                    ),
                )
            ]
            == "human_review"
            for form in self.forms
        )
        reviewed = sum(self._is_reviewed(row) for row in decisions)
        return {
            "total": len(self.forms),
            "decided": reviewed,
            "confirm": count_decisions("hyphenation_action", "confirm"),
            "correct": count_decisions("hyphenation_action", "correct"),
            "flag": count_decisions("row_action", "flag"),
            "uncertain": count_decisions("row_action", "uncertain"),
            "invalid": count_decisions("row_action", "invalid"),
            "foreign": count_decisions("is_foreign_word", 1),
            "proper": count_decisions("is_proper_name", 1),
            "abbreviation": count_decisions("is_abbreviation", 1),
            "corrected_form": count_decisions("corrected_form"),
            "deleted": count_decisions("is_deleted", 1),
            "reviewed": reviewed,
            "reviewed_hyphenation": count_decisions("hyphenation_action"),
            "reviewed_syllabification": count_decisions("syllabification_action"),
            "reviewed_both": sum(
                row["hyphenation_action"] is not None
                and row["syllabification_action"] is not None
                for row in decisions
            ),
            "ai_review_queue": ai_review_queue,
            "psp_comparisons": len(self._psp_rows(self.forms)),
            "psp_audit": self.psp_audit_progress(),
            "decisions_path": str(self.decisions_path),
            "engine_version": ENGINE_VERSION,
        }

    def export_corrections(self) -> dict:
        """Return portable suggestions that still differ from the current engine."""
        decisions = self._decision_rows(self.forms)
        corrections = []
        for form in self.forms:
            row = decisions.get(form)
            if not row or not row["expected_hyphenation"]:
                continue
            review_form = self.review_forms[form]
            expected = _recase_marked(row["expected_hyphenation"], review_form)
            engine_hyphenation, _, engine_error = _engine(review_form)
            if _hyphenation_match_mode(review_form, expected, engine_hyphenation):
                continue
            corrections.append(
                {
                    "form": review_form,
                    "engine_hyphenation": engine_hyphenation,
                    "suggested_hyphenation": expected,
                    "engine_error": engine_error,
                    "review_action": row["hyphenation_action"],
                    "engine_hyphenation_when_reviewed": _recase_marked(
                        row["engine_hyphenation"], review_form
                    ),
                    "engine_version_when_reviewed": (
                        row["hyphenation_engine_version"] or row["engine_version"]
                    ),
                    "reviewed_at": row["decided_at"],
                    "reason": row["reason"],
                    "corrected_form": row["corrected_form"],
                    "flags": {
                        "foreign": row["is_foreign_word"],
                        "proper": row["is_proper_name"],
                        "abbreviation": row["is_abbreviation"],
                        "deleted": row["is_deleted"],
                    },
                }
            )
        return {
            "format": "slabika-corrections",
            "format_version": 1,
            "generated_at": _now(),
            "engine_version": ENGINE_VERSION,
            "correction_count": len(corrections),
            "corrections": corrections,
        }

    # -- writing ---------------------------------------------------------

    def decide(self, payload: dict) -> dict:
        form = payload["form"]
        action = payload["action"]
        if action not in ACTIONS:
            raise ValueError(f"neznáma akcia {action!r}")
        if form not in self.form_set:
            raise ValueError(f"neznámy tvar {form!r}")

        form = self.representative_for_form[form]
        review_form = form
        display_hyphenation, display_syllabification, engine_error = _engine(review_form)
        if payload.get("bulk") and engine_error:
            raise ValueError(f"výstup enginu nemožno hromadne potvrdiť: {engine_error}")
        hyphenation = _recase_marked(display_hyphenation, form)
        syllabification = _recase_marked(display_syllabification, form)
        field = None
        edited = None
        if action in ("confirm", "correct"):
            field = payload.get("field", "hyphenation")
            if field not in ("hyphenation", "syllabification"):
                raise ValueError(f"neznáme pole {field!r}")
            text = payload.get("text")
            current = syllabification if field == "syllabification" else hyphenation
            if text is None:
                edited = current
            else:
                display_edited = _parse_marked(review_form, text)
                edited = _recase_marked(display_edited, form)
        flags = payload.get("flags") or {}
        if not isinstance(flags, dict):
            raise ValueError("flags musí byť objekt")
        unknown_flags = set(flags) - {"foreign", "proper", "abbreviation", "deleted"}
        if unknown_flags:
            raise ValueError(f"neznáme príznaky: {', '.join(sorted(unknown_flags))}")
        if any(value not in (True, False, None) for value in flags.values()):
            raise ValueError("príznaky musia byť true, false alebo null")
        correction_supplied = "corrected_form" in payload
        corrected_form = payload.get("corrected_form")
        if corrected_form is not None:
            if not isinstance(corrected_form, str):
                raise ValueError("opravený tvar musí byť text")
            corrected_form = corrected_form.strip()
            if not corrected_form or any(char.isspace() for char in corrected_form):
                raise ValueError("opravený tvar musí byť jedno neprázdne slovo")
            if corrected_form == review_form:
                corrected_form = None
        payload_reason = payload.get("reason") or ""
        if not isinstance(payload_reason, str):
            raise ValueError("reason musí byť text")

        with self.lock:
            self.store.execute("BEGIN IMMEDIATE")
            previous = self.store.execute(
                "SELECT * FROM decisions WHERE form = ?", (form,)
            ).fetchone()
            effective = self._decision_rows([form]).get(form)
            expected_hyphenation = (
                _recase_marked(effective["expected_hyphenation"], form)
                if effective else None
            )
            expected_syllabification = (
                _recase_marked(effective["expected_syllabification"], form)
                if effective else None
            )
            hyphenation_action = effective["hyphenation_action"] if effective else None
            syllabification_action = effective["syllabification_action"] if effective else None
            row_action = effective["row_action"] if effective else None
            engine_hyphenation = (
                _recase_marked(effective["engine_hyphenation"], form)
                if effective else hyphenation
            )
            engine_syllabification = (
                _recase_marked(effective["engine_syllabification"], form)
                if effective else syllabification
            )
            hyphenation_engine_version = (
                effective["hyphenation_engine_version"] if effective else None
            )
            syllabification_engine_version = (
                effective["syllabification_engine_version"] if effective else None
            )
            reason = effective["reason"] if effective else ""
            is_foreign_word = flags.get(
                "foreign", effective["is_foreign_word"] if effective else None
            )
            is_proper_name = flags.get(
                "proper", effective["is_proper_name"] if effective else None
            )
            is_abbreviation = flags.get(
                "abbreviation", effective["is_abbreviation"] if effective else None
            )
            is_deleted = flags.get(
                "deleted", effective["is_deleted"] if effective else None
            )
            effective_corrected_form = effective["corrected_form"] if effective else None
            if correction_supplied:
                effective_corrected_form = corrected_form

            # Each output keeps its own verdict and engine snapshot. The lock
            # covers reading and writing, so concurrent requests cannot erase
            # the verdict already stored for the other output.
            if field == "syllabification":
                expected_syllabification = edited
                engine_syllabification = syllabification
                syllabification_engine_version = ENGINE_VERSION
                syllabification_action = (
                    "confirm" if edited.lower() == syllabification.lower() else "correct"
                )
            elif field == "hyphenation":
                expected_hyphenation = edited
                engine_hyphenation = hyphenation
                hyphenation_engine_version = ENGINE_VERSION
                hyphenation_action = (
                    "confirm" if edited.lower() == hyphenation.lower() else "correct"
                )
            elif action in ROW_ACTIONS:
                row_action = action
                reason = payload_reason.strip()
            elif action == "classify" and payload_reason:
                reason = payload_reason.strip()

            stored_action = row_action or (
                "correct"
                if "correct" in (hyphenation_action, syllabification_action)
                else "confirm"
                if "confirm" in (hyphenation_action, syllabification_action)
                else "confirm"
            )
            try:
                self.store.execute(
                    """
                    INSERT INTO decisions(
                        form, action, row_action,
                        hyphenation_action, syllabification_action,
                        expected_hyphenation, expected_syllabification,
                        engine_hyphenation, engine_syllabification,
                        hyphenation_engine_version, syllabification_engine_version,
                        is_foreign_word, is_proper_name, is_abbreviation,
                        corrected_form, is_deleted,
                        reason, engine_version, decided_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(form) DO UPDATE SET
                        action = excluded.action,
                        row_action = excluded.row_action,
                        hyphenation_action = excluded.hyphenation_action,
                        syllabification_action = excluded.syllabification_action,
                        expected_hyphenation = excluded.expected_hyphenation,
                        expected_syllabification = excluded.expected_syllabification,
                        engine_hyphenation = excluded.engine_hyphenation,
                        engine_syllabification = excluded.engine_syllabification,
                        hyphenation_engine_version = excluded.hyphenation_engine_version,
                        syllabification_engine_version = excluded.syllabification_engine_version,
                        is_foreign_word = excluded.is_foreign_word,
                        is_proper_name = excluded.is_proper_name,
                        is_abbreviation = excluded.is_abbreviation,
                        corrected_form = excluded.corrected_form,
                        is_deleted = excluded.is_deleted,
                        reason = excluded.reason,
                        engine_version = excluded.engine_version,
                        decided_at = excluded.decided_at
                    """,
                    (
                        form,
                        stored_action,
                        row_action,
                        hyphenation_action,
                        syllabification_action,
                        expected_hyphenation,
                        expected_syllabification,
                        engine_hyphenation,
                        engine_syllabification,
                        hyphenation_engine_version,
                        syllabification_engine_version,
                        is_foreign_word,
                        is_proper_name,
                        is_abbreviation,
                        effective_corrected_form,
                        is_deleted,
                        reason,
                        ENGINE_VERSION,
                        _now(),
                    ),
                )
                log_cursor = self.store.execute(
                    """
                    INSERT INTO decision_log(
                        form, operation, action, expected_hyphenation,
                        expected_syllabification, engine_hyphenation,
                        is_foreign_word, is_proper_name, is_abbreviation,
                        corrected_form, is_deleted,
                        previous_json, engine_version, logged_at
                    ) VALUES (?, 'decide', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        form,
                        "classify" if action == "classify" else stored_action,
                        expected_hyphenation,
                        expected_syllabification,
                        hyphenation,
                        is_foreign_word,
                        is_proper_name,
                        is_abbreviation,
                        effective_corrected_form,
                        is_deleted,
                        json.dumps(dict(previous), ensure_ascii=False) if previous else None,
                        ENGINE_VERSION,
                        _now(),
                    ),
                )
                self.store.execute(
                    "UPDATE decisions SET decision_seq = ? WHERE form = ?",
                    (log_cursor.lastrowid, form),
                )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
            self.decided[form] = stored_action
        return {"ok": True, "item": self._fresh(form)}

    def decide_many(self, payload: dict) -> dict:
        """Record one decision per entry, reporting failures without aborting."""
        results = []
        failed = []
        for entry in payload.get("entries") or []:
            try:
                results.append(self.decide(entry)["item"])
            except Exception as error:  # noqa: BLE001 - reported to the reviewer
                failed.append({"form": entry.get("form"), "error": str(error)})
        return {"ok": True, "items": results, "failed": failed}

    def clear(self, payload: dict) -> dict:
        """Withdraw visible review data without erasing legacy syllable decisions."""
        form = payload["form"]
        if form not in self.form_set:
            raise ValueError(f"neznámy tvar {form!r}")
        form = self.representative_for_form[form]
        with self.lock:
            self.store.execute("BEGIN IMMEDIATE")
            previous_rows = [
                row
                for row in self._decision_row_groups([form])[form]
                if self._is_reviewed(row)
            ]
            if not previous_rows:
                self.store.rollback()
                return {"ok": False, "message": "tento tvar nemá revízne rozhodnutie"}
            try:
                for previous in previous_rows:
                    source_form = previous["form"]
                    remaining_action = previous["syllabification_action"]
                    if remaining_action is None:
                        self.store.execute(
                            "DELETE FROM decisions WHERE form = ?", (source_form,)
                        )
                    else:
                        self.store.execute(
                            """UPDATE decisions
                               SET action = ?, row_action = NULL,
                                   hyphenation_action = NULL,
                                   expected_hyphenation = NULL,
                                   hyphenation_engine_version = NULL,
                                   is_foreign_word = NULL,
                                   is_proper_name = NULL,
                                   is_abbreviation = NULL,
                                   corrected_form = NULL,
                                   is_deleted = NULL,
                                   reason = '', engine_version = ?, decided_at = ?
                               WHERE form = ?""",
                            (remaining_action, ENGINE_VERSION, _now(), source_form),
                        )
                snapshot = {"alias_group": [dict(row) for row in previous_rows]}
                log_cursor = self.store.execute(
                    """
                    INSERT INTO decision_log(
                        form, operation, action, previous_json, engine_version, logged_at
                    ) VALUES (?, 'decide', NULL, ?, ?, ?)
                    """,
                    (
                        form,
                        json.dumps(snapshot, ensure_ascii=False),
                        ENGINE_VERSION,
                        _now(),
                    ),
                )
                for previous in previous_rows:
                    if previous["syllabification_action"] is not None:
                        self.store.execute(
                            "UPDATE decisions SET decision_seq = ? WHERE form = ?",
                            (log_cursor.lastrowid, previous["form"]),
                        )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
            for previous in previous_rows:
                source_form = previous["form"]
                if previous["syllabification_action"] is None:
                    self.decided.pop(source_form, None)
                else:
                    self.decided[source_form] = previous["syllabification_action"]
        return {"ok": True, "item": self._fresh(form)}

    def undo_last(self) -> dict:
        with self.lock:
            self.store.execute("BEGIN IMMEDIATE")
            row = None
            pending_undos = 0
            for candidate in self.store.execute(
                "SELECT * FROM decision_log ORDER BY entry_id DESC"
            ):
                if candidate["operation"] == "undo":
                    pending_undos += 1
                elif pending_undos:
                    pending_undos -= 1
                else:
                    row = candidate
                    break
            if row is None:
                self.store.rollback()
                return {"ok": False, "message": "niet čo vrátiť"}
            form = row["form"]
            previous = json.loads(row["previous_json"]) if row["previous_json"] else None
            group_previous = previous.get("alias_group") if previous else None
            if previous and group_previous is None:
                previous.setdefault(
                    "row_action",
                    previous["action"]
                    if previous["action"] in ("flag", "uncertain", "invalid")
                    else None,
                )
                previous.setdefault(
                    "hyphenation_action",
                    previous["action"]
                    if previous.get("expected_hyphenation") is not None
                    and previous["action"] in ("confirm", "correct")
                    else None,
                )
                previous.setdefault(
                    "syllabification_action",
                    previous["action"]
                    if previous.get("expected_syllabification") is not None
                    and previous["action"] in ("confirm", "correct")
                    else None,
                )
                previous.setdefault(
                    "hyphenation_engine_version",
                    previous.get("engine_version")
                    if previous["hyphenation_action"] is not None
                    else None,
                )
                previous.setdefault(
                    "syllabification_engine_version",
                    previous.get("engine_version")
                    if previous["syllabification_action"] is not None
                    else None,
                )
            try:
                if group_previous is not None:
                    for snapshot in group_previous:
                        source_form = snapshot["form"]
                        self.store.execute(
                            "DELETE FROM decisions WHERE form = ?", (source_form,)
                        )
                        columns = ", ".join(snapshot)
                        placeholders = ", ".join("?" * len(snapshot))
                        self.store.execute(
                            f"INSERT INTO decisions({columns}) VALUES ({placeholders})",
                            tuple(snapshot.values()),
                        )
                else:
                    self.store.execute("DELETE FROM decisions WHERE form = ?", (form,))
                    if previous:
                        columns = ", ".join(previous)
                        placeholders = ", ".join("?" * len(previous))
                        self.store.execute(
                            f"INSERT INTO decisions({columns}) VALUES ({placeholders})",
                            tuple(previous.values()),
                        )
                self.store.execute(
                    """
                    INSERT INTO decision_log(form, operation, engine_version, logged_at)
                    VALUES (?, 'undo', ?, ?)
                    """,
                    (form, ENGINE_VERSION, _now()),
                )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
            if group_previous is not None:
                for snapshot in group_previous:
                    self.decided[snapshot["form"]] = snapshot["action"]
            elif previous:
                self.decided[form] = previous["action"]
            else:
                self.decided.pop(form, None)
        visible_form = self.representative_for_form.get(form, form)
        return {"ok": True, "form": visible_form, "item": self._fresh(visible_form)}

    def _fresh(self, form: str) -> dict:
        ai = self._ai_rows([form]).get(form)
        mine = self._decision_rows([form]).get(form)
        psp = self._psp_rows([form]).get(form)
        return self.item(form, ai, mine, psp)


class ReviewHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False


class Handler(BaseHTTPRequestHandler):
    corpus: Corpus

    def log_message(self, *args: object) -> None:  # keep the console quiet
        return

    def _send(
        self,
        status: int,
        body: bytes,
        content_type: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, UI_PATH.read_bytes(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/list":
            query = parse_qs(parsed.query)
            try:
                self._json(
                    self.corpus.page(
                        query.get("q", [""])[0],
                        query.get("mode", ["prefix"])[0],
                        query.get("status", ["all"])[0],
                        int(query.get("offset", ["0"])[0]),
                        min(int(query.get("limit", ["500"])[0]), 2000),
                        query.get("tex_diff", ["0"])[0] == "1",
                        query.get("blind_human_diff", ["0"])[0] == "1",
                    )
                )
            except Exception as error:  # noqa: BLE001
                self._json({"error": str(error)}, 400)
            return
        if parsed.path == "/api/stats":
            self._json(self.corpus.stats())
            return
        if parsed.path == "/api/export/corrections":
            payload = self.corpus.export_corrections()
            body = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            self._send(
                200,
                body,
                "application/json; charset=utf-8",
                {"Content-Disposition": (
                    f'attachment; filename="slabika-corrections-{stamp}.json"'
                )},
            )
            return
        if parsed.path == "/api/psp-audit/batch":
            query = parse_qs(parsed.query)
            try:
                self._json(
                    self.corpus.psp_audit_batch(
                        query.get("audit_id", [""])[0],
                        int(query.get("batch", ["1"])[0]),
                    )
                )
            except Exception as error:  # noqa: BLE001
                self._json({"error": str(error)}, 400)
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        content_type = self.headers.get("Content-Type", "").partition(";")[0].strip().lower()
        if content_type != "application/json":
            self._json({"error": "Content-Type musí byť application/json"}, 415)
            return
        port = self.server.server_address[1]
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        allowed_origins = {None, *(f"http://{value}" for value in allowed_hosts)}
        if host not in allowed_hosts or origin not in allowed_origins:
            self._json({"error": "cudzí pôvod požiadavky"}, 403)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        try:
            if parsed.path == "/api/decide":
                self._json(self.corpus.decide(payload))
                return
            if parsed.path == "/api/decide_many":
                self._json(self.corpus.decide_many(payload))
                return
            if parsed.path == "/api/clear":
                self._json(self.corpus.clear(payload))
                return
            if parsed.path == "/api/undo":
                self._json(self.corpus.undo_last())
                return
            if parsed.path == "/api/psp-audit/freeze":
                self._json(
                    self.corpus.freeze_psp_audit(
                        payload.get("audit_id", ""),
                        payload.get("engine_ref", ""),
                        payload.get("chlebikova_ref", ""),
                    )
                )
                return
            if parsed.path == "/api/psp-audit/adjudicate":
                self._json(self.corpus.adjudicate_psp(payload))
                return
        except Exception as error:  # noqa: BLE001
            self._json({"error": f"{type(error).__name__}: {error}"}, 400)
            return
        self._json({"error": "not found"}, 404)


def _bind_server(port: int) -> ThreadingHTTPServer:
    try:
        return ReviewHTTPServer(("127.0.0.1", port), Handler)
    except OSError as error:
        if port == 0 or error.errno != errno.EADDRINUSE:
            raise
        print(f"port      {port} is already in use; using a free local port")
        return ReviewHTTPServer(("127.0.0.1", 0), Handler)


def main() -> int:
    parser = argparse.ArgumentParser(description="slabika review console")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_INVENTORY,
        help="inventory sqlite (default: inventory bundled with slabika)",
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        help="decision store (default: review_decisions.sqlite in the current directory)",
    )
    parser.add_argument(
        "--blind",
        type=Path,
        action="append",
        help="blind audit results; repeat to merge multiple read-only audits",
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    if not arguments.db.exists():
        parser.error(f"inventory not found: {arguments.db}")
    decisions = arguments.decisions or Path.cwd() / "review_decisions.sqlite"
    blind = arguments.blind or DEFAULT_BLIND

    Handler.corpus = Corpus(arguments.db, decisions, blind)
    server = _bind_server(arguments.port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"inventory  {arguments.db}  ({len(Handler.corpus.forms)} forms, read-only)")
    print(f"decisions  {decisions}  ({len(Handler.corpus.decided)} already decided)")
    print(f"blind      {', '.join(map(str, blind))}  ({len(Handler.corpus.blind)} audited)")
    print(f"engine     slabika {ENGINE_VERSION}")
    print(f"console    {url}   (Ctrl+C to stop)")
    if not arguments.no_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
