# SPDX-FileCopyrightText: 2026 Peter Bezemek <peter.bezemek@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Local review console for a syllabification corpus.

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

ACTIONS = ("confirm", "correct", "flag", "uncertain", "invalid")

DECISION_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    form TEXT PRIMARY KEY,
    action TEXT NOT NULL CHECK(action IN
        ('confirm', 'correct', 'flag', 'uncertain', 'invalid')),
    expected_hyphenation TEXT,
    expected_syllabification TEXT,
    engine_hyphenation TEXT NOT NULL,
    engine_syllabification TEXT NOT NULL,
    is_foreign_word INTEGER CHECK(is_foreign_word IN (0, 1)),
    is_proper_name INTEGER CHECK(is_proper_name IN (0, 1)),
    is_abbreviation INTEGER CHECK(is_abbreviation IN (0, 1)),
    reason TEXT NOT NULL DEFAULT '',
    engine_version TEXT NOT NULL,
    decided_at TEXT NOT NULL,
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
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
        self.store.commit()

        self.forms: list[str] = [
            row[0] for row in self.inventory.execute("SELECT form FROM forms ORDER BY form")
        ]
        self.folded: list[str] = [_fold(form) for form in self.forms]
        self.form_set: set[str] = set(self.forms)
        self.decided: dict[str, str] = {
            row[0]: row[1] for row in self.store.execute("SELECT form, action FROM decisions")
        }
        self.ai: dict[str, str] = {
            row[0]: row[1]
            for row in self.inventory.execute("SELECT form, review_status FROM adjudications")
        }

    # -- reading ---------------------------------------------------------

    def matches(self, query: str, mode: str) -> list[str]:
        if not query:
            return self.forms
        if mode == "regex":
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as error:
                raise ValueError(f"zlý regex: {error}") from error
            return [form for form in self.forms if pattern.search(form)]
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

    def _ai_rows(self, forms: list[str]) -> dict[str, sqlite3.Row]:
        out: dict[str, sqlite3.Row] = {}
        for start in range(0, len(forms), 800):
            chunk = forms[start : start + 800]
            placeholders = ",".join("?" * len(chunk))
            for row in self.inventory.execute(
                f"SELECT * FROM adjudications WHERE form IN ({placeholders})", chunk
            ):
                out[row["form"]] = row
        return out

    def _decision_rows(self, forms: list[str]) -> dict[str, sqlite3.Row]:
        out: dict[str, sqlite3.Row] = {}
        for start in range(0, len(forms), 800):
            chunk = forms[start : start + 800]
            placeholders = ",".join("?" * len(chunk))
            for row in self.store.execute(
                f"SELECT * FROM decisions WHERE form IN ({placeholders})", chunk
            ):
                out[row["form"]] = row
        return out

    def item(self, form: str, ai: sqlite3.Row | None, mine: sqlite3.Row | None) -> dict:
        hyphenation, syllabification, error = _engine(form)
        ai_expected = ai["expected_hyphenation"] if ai else None
        ai_syllabification = ai["expected_syllabification"] if ai else None
        my_expected = mine["expected_hyphenation"] if mine else None
        return {
            "form": form,
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
            "my_expected": my_expected,
            "my_syllabification": mine["expected_syllabification"] if mine else None,
            "my_disagrees": bool(my_expected) and my_expected != hyphenation,
            "stale": (
                bool(mine)
                and (mine["engine_syllabification"] or "").lower()
                != syllabification.lower()
            ),
            "decided_at": mine["decided_at"] if mine else None,
            "flags": {
                "foreign": (mine or ai)["is_foreign_word"] if (mine or ai) else None,
                "proper": (mine or ai)["is_proper_name"] if (mine or ai) else None,
                "abbreviation": (mine or ai)["is_abbreviation"] if (mine or ai) else None,
            },
        }

    def _filter_status(self, forms: list[str], status: str) -> list[str]:
        if status in ("", "all"):
            return forms
        if status == "undecided":
            return [f for f in forms if f not in self.decided]
        if status in ACTIONS:
            return [f for f in forms if self.decided.get(f) == status]
        if status == "mine":
            return [f for f in forms if f in self.decided]
        if status == "ai_disagree":
            rows = self._ai_rows(forms)
            keep = []
            for form in forms:
                row = rows.get(form)
                expected = row["expected_hyphenation"] if row else None
                if expected and expected != _engine(form)[0]:
                    keep.append(form)
            return keep
        if status == "ai_disagree_syl":
            rows = self._ai_rows(forms)
            keep = []
            for form in forms:
                row = rows.get(form)
                expected = row["expected_syllabification"] if row else None
                if expected and expected.lower() != _engine(form)[1].lower():
                    keep.append(form)
            return keep
        if status == "engine_disagree":
            rows = self._decision_rows(forms)
            keep = []
            for form in forms:
                row = rows.get(form)
                if row is None:
                    continue
                engine_hyphenation, engine_syllabification, _ = _engine(form)
                if (row["expected_hyphenation"] or engine_hyphenation) != engine_hyphenation or (
                    row["expected_syllabification"] or engine_syllabification
                ) != engine_syllabification:
                    keep.append(form)
            return keep
        if status == "engine_error":
            return [f for f in forms if _engine(f)[2] is not None]
        return [f for f in forms if self.ai.get(f, "pending") == status]

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
        counts = dict(self.store.execute("SELECT action, COUNT(*) FROM decisions GROUP BY 1"))
        return {
            "total": len(self.forms),
            "decided": len(self.decided),
            "confirm": counts.get("confirm", 0),
            "correct": counts.get("correct", 0),
            "flag": counts.get("flag", 0),
            "uncertain": counts.get("uncertain", 0),
            "invalid": counts.get("invalid", 0),
            "ai_review_queue": sum(1 for v in self.ai.values() if v == "human_review"),
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

        hyphenation, syllabification, _ = _engine(form)
        flags = payload.get("flags") or {}
        if action in ("confirm", "correct"):
            field = payload.get("field", "syllabification")
            text = payload.get("text")
            if text is None:
                edited = syllabification if field == "syllabification" else hyphenation
            else:
                edited = _parse_marked(form, text)
            # Syllabification and hyphenation are separate outputs of shared
            # linguistic analysis. A verdict on one says nothing about the
            # other, so only the edited field is ever recorded.
            if field == "syllabification":
                expected_syllabification = edited
                expected_hyphenation = None
                action = "confirm" if edited == syllabification else "correct"
            else:
                expected_hyphenation = edited
                expected_syllabification = None
                action = "confirm" if edited == hyphenation else "correct"
        else:
            expected_hyphenation = None
            expected_syllabification = None

        with self.lock:
            previous = self.store.execute(
                "SELECT * FROM decisions WHERE form = ?", (form,)
            ).fetchone()
            self.store.execute("BEGIN IMMEDIATE")
            try:
                self.store.execute(
                    """
                    INSERT INTO decisions(
                        form, action, expected_hyphenation, expected_syllabification,
                        engine_hyphenation, engine_syllabification,
                        is_foreign_word, is_proper_name, is_abbreviation,
                        reason, engine_version, decided_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(form) DO UPDATE SET
                        action = excluded.action,
                        expected_hyphenation = excluded.expected_hyphenation,
                        expected_syllabification = excluded.expected_syllabification,
                        engine_hyphenation = excluded.engine_hyphenation,
                        engine_syllabification = excluded.engine_syllabification,
                        is_foreign_word = excluded.is_foreign_word,
                        is_proper_name = excluded.is_proper_name,
                        is_abbreviation = excluded.is_abbreviation,
                        reason = excluded.reason,
                        engine_version = excluded.engine_version,
                        decided_at = excluded.decided_at
                    """,
                    (
                        form,
                        action,
                        expected_hyphenation,
                        expected_syllabification,
                        hyphenation,
                        syllabification,
                        flags.get("foreign"),
                        flags.get("proper"),
                        flags.get("abbreviation"),
                        (payload.get("reason") or "").strip(),
                        ENGINE_VERSION,
                        _now(),
                    ),
                )
                self.store.execute(
                    """
                    INSERT INTO decision_log(
                        form, operation, action, expected_hyphenation,
                        expected_syllabification, engine_hyphenation,
                        previous_json, engine_version, logged_at
                    ) VALUES (?, 'decide', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        form,
                        action,
                        expected_hyphenation,
                        expected_syllabification,
                        hyphenation,
                        json.dumps(dict(previous), ensure_ascii=False) if previous else None,
                        ENGINE_VERSION,
                        _now(),
                    ),
                )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
            self.decided[form] = action
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
        """Withdraw one verdict, leaving the form undecided again.

        Logged as a decide-entry carrying no action, so the global undo stack
        can put the withdrawn verdict back exactly as it stood.
        """
        form = payload["form"]
        if form not in self.form_set:
            raise ValueError(f"neznámy tvar {form!r}")
        with self.lock:
            previous = self.store.execute(
                "SELECT * FROM decisions WHERE form = ?", (form,)
            ).fetchone()
            if previous is None:
                return {"ok": False, "message": "tento tvar nemá rozhodnutie"}
            self.store.execute("BEGIN IMMEDIATE")
            try:
                self.store.execute("DELETE FROM decisions WHERE form = ?", (form,))
                self.store.execute(
                    """
                    INSERT INTO decision_log(
                        form, operation, action, previous_json, engine_version, logged_at
                    ) VALUES (?, 'decide', NULL, ?, ?, ?)
                    """,
                    (
                        form,
                        json.dumps(dict(previous), ensure_ascii=False),
                        ENGINE_VERSION,
                        _now(),
                    ),
                )
                self.store.commit()
            except BaseException:
                self.store.rollback()
                raise
            self.decided.pop(form, None)
        return {"ok": True, "item": self._fresh(form)}

    def undo_last(self) -> dict:
        with self.lock:
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
                return {"ok": False, "message": "niet čo vrátiť"}
            form = row["form"]
            previous = json.loads(row["previous_json"]) if row["previous_json"] else None
            self.store.execute("BEGIN IMMEDIATE")
            try:
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
            if previous:
                self.decided[form] = previous["action"]
            else:
                self.decided.pop(form, None)
        return {"ok": True, "form": form, "item": self._fresh(form)}

    def _fresh(self, form: str) -> dict:
        ai = self.inventory.execute(
            "SELECT * FROM adjudications WHERE form = ?", (form,)
        ).fetchone()
        mine = self.store.execute("SELECT * FROM decisions WHERE form = ?", (form,)).fetchone()
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
