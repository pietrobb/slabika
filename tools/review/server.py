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

    python tools/review/server.py --db path/to/inventory.sqlite
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import threading
import unicodedata
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from slabika import __version__ as ENGINE_VERSION  # noqa: E402
from slabika import hyphenate, syllables  # noqa: E402

UI_PATH = Path(__file__).resolve().parent / "ui.html"

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


def _engine(form: str) -> tuple[str, str, str | None]:
    try:
        return hyphenate(form), _recase(syllables(form), form), None
    except Exception as error:  # noqa: BLE001 - shown to the reviewer
        return form, form, f"{type(error).__name__}: {error}"


class Corpus:
    """Read-only view of the inventory plus a writable decision store."""

    def __init__(self, inventory: Path, decisions: Path) -> None:
        self.lock = threading.Lock()
        self.inventory_path = inventory
        self.decisions_path = decisions

        self.inventory = sqlite3.connect(
            f"file:{inventory.as_posix()}?mode=ro", uri=True, check_same_thread=False
        )
        self.inventory.row_factory = sqlite3.Row

        self.store = sqlite3.connect(decisions, check_same_thread=False)
        self.store.row_factory = sqlite3.Row
        self.store.executescript(DECISION_SCHEMA)
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

    def item(self, form: str, ai: sqlite3.Row | None, mine: sqlite3.Row | None) -> dict:
        review_form = self.review_forms[form]
        hyphenation, syllabification, error = _engine(review_form)
        ai_expected = _recase_marked(
            ai["expected_hyphenation"] if ai else None, review_form
        )
        ai_syllabification = _recase_marked(
            ai["expected_syllabification"] if ai else None, review_form
        )
        my_expected = _recase_marked(
            mine["expected_hyphenation"] if mine else None, review_form
        )
        my_hyphenation_action = mine["hyphenation_action"] if mine else None
        my_syllabification_action = mine["syllabification_action"] if mine else None

        def flag(field: str) -> int | None:
            if mine and mine[field] is not None:
                return mine[field]
            return ai[field] if ai else None

        return {
            "form": form,
            "review_form": review_form,
            "hyphenation": hyphenation,
            "syllabification": syllabification,
            "engine_error": error,
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
            "my_syllabification": _recase_marked(
                mine["expected_syllabification"] if mine else None, review_form
            ),
            "my_disagrees": bool(my_expected) and my_expected != hyphenation,
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
                and _recase_marked(rows[form]["expected_hyphenation"], form)
                != _engine(form)[0]
            ]
        if status == "engine_error":
            return [form for form in forms if _engine(form)[2] is not None]
        rows = self._ai_rows(forms)
        return [
            form
            for form in forms
            if form in rows and rows[form]["review_status"] == status
        ]

    def page(self, query: str, mode: str, status: str, offset: int, limit: int) -> dict:
        candidate = self._filter_status(self.matches(query, mode), status)
        window = candidate[offset : offset + limit]
        ai = self._ai_rows(window)
        mine = self._decision_rows(window)
        return {
            "total": len(candidate),
            "offset": offset,
            "items": [self.item(form, ai.get(form), mine.get(form)) for form in window],
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
            "decisions_path": str(self.decisions_path),
            "engine_version": ENGINE_VERSION,
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
        return self.item(form, ai, mine)


class Handler(BaseHTTPRequestHandler):
    corpus: Corpus

    def log_message(self, *args: object) -> None:  # keep the console quiet
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
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
                    )
                )
            except Exception as error:  # noqa: BLE001
                self._json({"error": str(error)}, 400)
            return
        if parsed.path == "/api/stats":
            self._json(self.corpus.stats())
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
        except Exception as error:  # noqa: BLE001
            self._json({"error": f"{type(error).__name__}: {error}"}, 400)
            return
        self._json({"error": "not found"}, 404)


def main() -> int:
    parser = argparse.ArgumentParser(description="slabika review console")
    parser.add_argument("--db", type=Path, required=True, help="inventory sqlite (read-only)")
    parser.add_argument("--decisions", type=Path, help="decision store (default: next to --db)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    if not arguments.db.exists():
        parser.error(f"inventory not found: {arguments.db}")
    decisions = arguments.decisions or arguments.db.with_name("review_decisions.sqlite")

    Handler.corpus = Corpus(arguments.db, decisions)
    server = ThreadingHTTPServer(("127.0.0.1", arguments.port), Handler)
    url = f"http://127.0.0.1:{arguments.port}/"
    print(f"inventory  {arguments.db}  ({len(Handler.corpus.forms)} forms, read-only)")
    print(f"decisions  {decisions}  ({len(Handler.corpus.decided)} already decided)")
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
