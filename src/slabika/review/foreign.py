# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Language-isolated review of stored foreign proposals and generated IPA."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .server import Corpus, _parse_marked

LANGUAGES = {"de": "german", "fr": "french", "en": "english"}


class ForeignCorpus(Corpus):
    require_syllabification = False

    def __init__(self, inventory: Path, decisions: Path, language: str) -> None:
        if language not in LANGUAGES:
            raise ValueError("language must be de/fr/en")
        inventory, decisions = inventory.resolve(), decisions.resolve()
        if inventory == decisions:
            raise ValueError("Inventory and human decisions must be separate files")
        with closing(sqlite3.connect(f"{inventory.as_uri()}?mode=ro", uri=True)) as source:
            metadata = dict(source.execute("SELECT key, value FROM corpus_metadata"))
            if metadata.get("language") != language:
                raise ValueError("Inventory language does not match --language")
            source.execute("SELECT form, ipa, proposed_hyphenation FROM foreign_evidence LIMIT 1")
        if decisions.exists():
            with closing(sqlite3.connect(f"{decisions.as_uri()}?mode=ro", uri=True)) as store:
                tables = {row[0] for row in store.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if tables:
                    if "foreign_review_metadata" not in tables:
                        raise ValueError("Refusing a non-foreign decision store; choose a separate file")
                    saved = dict(store.execute("SELECT key, value FROM foreign_review_metadata"))
                    if saved.get("language") != language or saved.get("inventory") != str(inventory):
                        raise ValueError("Decision store belongs to another language or inventory")
        self.language = language
        self.metadata = metadata
        super().__init__(inventory, decisions, blind=[])
        with self.store:
            self.store.execute("CREATE TABLE IF NOT EXISTS foreign_review_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self.store.executemany(
                "INSERT OR IGNORE INTO foreign_review_metadata VALUES (?, ?)",
                [("language", language), ("inventory", str(inventory))],
            )

    def _evidence(self, form: str) -> dict:
        row = self.inventory.execute(
            "SELECT * FROM foreign_evidence WHERE form = ?", (form,)
        ).fetchone()
        return dict(row) if row else {}

    def _engine(self, form: str) -> tuple[str, str, str | None]:
        evidence = self._evidence(form)
        proposal = evidence.get("proposed_hyphenation")
        error = evidence.get("error") or (None if proposal else "Návrh ešte nie je vygenerovaný")
        return proposal or form, "", error

    def _engine_hyphenation(self, review_form: str) -> str:
        # The builder may finish more rows while the console remains open.
        return self._engine(review_form)[0]

    def _match_mode(self, form: str, expected: str | None, preferred: str) -> str | None:
        return "preferred" if expected is not None and expected.casefold() == preferred.casefold() else None

    def _tex(self, form: str) -> None:
        return None

    def _profiles(self, form: str) -> dict[str, bool]:
        return {name: name == LANGUAGES[self.language] for name in LANGUAGES.values()}

    def _forms_for_language(self, language: str) -> frozenset[str]:
        return frozenset(self.forms) if language == LANGUAGES[self.language] else frozenset()

    def precompute_voice_filters(self) -> None:
        self._tex_disagreements = frozenset()

    def item(self, form, ai, mine, psp=None) -> dict:
        result = super().item(form, ai, mine)
        evidence = self._evidence(self.review_forms[form])
        return result | {
            "corpus_language": self.language,
            "ai_adjudication_html": "",
            "engine_tex": result["hyphenation"],
            "syllabification_unsupported": False,
            "pronunciation": evidence,
        }

    def page(self, *args, **kwargs) -> dict:
        return super().page(*args, **kwargs) | {"corpus_language": self.language}

    def stats(self) -> dict:
        counts = dict(self.inventory.execute(
            "SELECT pronunciation_status, count(*) FROM foreign_evidence GROUP BY pronunciation_status"
        ))
        return super().stats() | {"corpus_language": self.language, "pronunciation_counts": counts}

    def decide(self, payload: dict) -> dict:
        if payload.get("field", "hyphenation") != "hyphenation":
            raise ValueError("Foreign review edits written division, not phonetic syllables")
        if payload.get("action") in ("confirm", "correct"):
            form = payload.get("form", "")
            evidence = self._evidence(form)
            if not evidence.get("proposed_hyphenation"):
                text = payload.get("text")
                if not isinstance(text, str) or not text.strip() or (
                    payload["action"] == "confirm" and _parse_marked(form, text) == form
                ):
                    raise ValueError("Chýbajúci návrh nemožno potvrdiť; zadajte vlastnú opravu")
        return super().decide(payload)

    def export_corrections(self) -> dict:
        result = super().export_corrections()
        for row in result["corrections"]:
            row["pronunciation"] = self._evidence(row["form"])
        return result | {"corpus_language": self.language, "corpus_metadata": self.metadata}

    def freeze_psp_audit(self, *args, **kwargs):
        raise ValueError("Chlebíková is not used for foreign corpora")

    def adjudicate_psp(self, payload):
        raise ValueError("Chlebíková is not used for foreign corpora")
