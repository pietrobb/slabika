# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build independent, resumable foreign evidence inventories, never gold decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
import zipfile
from datetime import datetime, timezone
from importlib import metadata
from importlib.resources import files
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
# Existing corpus/experimental tools use sibling imports, including when imported by tests.
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

LANGUAGES = {"de": "german", "fr": "french", "en": "english"}
EXPECTED_COUNTS = {"de": 131150, "fr": 35552, "en": 55638}
DEFAULT_OUTPUT = ROOT / "tests/data/foreign_review"
SCHEMA_VERSION = "1"
IPA_VERSION = "mfa-v3-whole-phone-broad-ipa-1"
IPA_NOTE = "Generated broad IPA transcription; not human verified; stress is not inferred."
# Inspected in the installed, unmodified MFA v3 archives' phones.sym. MFA documents
# its IPA-like phone set at https://mfa-models.readthedocs.io/en/latest/mfa_phone_set.html
# Convert whole tokens only: a separate /j/ or /w/ must remain a consonant.
PHONE_SETS = {
    "en": frozenset("ə d t ɪ m ɛ n ɫ ɚ ɹ ʔ s z ɐ v ej ɑː dʲ iː ɑ dʒ vʲ ɒː bʲ "
                    "tʃ æ b ow aj cʰ p pʰ k j ʊ kʰ ɒ ɡ l w f h ʉ ɲ pʲ i θ ʉː tʲ "
                    "ʃ c tʰ ʎ ŋ ʒ mʲ ç ɝ ɔj aw fʲ ɟ kʷ cʷ ð ɟʷ ɡʷ tʷ pʷ oj".split()),
    "de": frozenset("s a aː p b x ə n ɐ ʁ ɪ d eː ɔ f kʰ l tʰ k ç ŋ ɛ t ʃ œ m ɡ "
                    "aj h aw iː ts ʏ pf ʊ j oː v pʰ ɔʏ z c ɲ cʰ uː ɟ yː tʃ øː".split()),
    "fr": frozenset("a ɑ ɔ b ʁ d e i l ʎ n s tʃ f ɡ ʒ ɑ̃ ɛ z j t o ɲ ɛ̃ k m u y ʃ "
                    "ɔ̃ v ɥ w œ c ø ə p ts dʒ ŋ mʲ ɟ".split()),
}
IPA_REPLACEMENTS = {"aj": "aɪ", "ej": "eɪ", "aw": "aʊ", "ow": "oʊ",
                    "ɔj": "ɔɪ", "oj": "ɔɪ", "ts": "t͡s", "tʃ": "t͡ʃ",
                    "dʒ": "d͡ʒ", "pf": "p͡f"}
SCHEMA = (
    "CREATE TABLE forms(form TEXT PRIMARY KEY, casing_status TEXT DEFAULT 'resolved', "
    "proposed_canonical_form TEXT)",
    "CREATE TABLE adjudications(form TEXT PRIMARY KEY, review_status TEXT DEFAULT 'pending', "
    "expected_syllabification TEXT, expected_hyphenation TEXT, is_foreign_word INTEGER, "
    "is_proper_name INTEGER, is_likely_invalid INTEGER, is_abbreviation INTEGER, "
    "reason TEXT DEFAULT '', source TEXT DEFAULT '')",
    "CREATE TABLE foreign_evidence(form TEXT PRIMARY KEY REFERENCES forms(form), "
    "language TEXT CHECK(language IN ('en','de','fr')), proposed_hyphenation TEXT, ipa TEXT, "
    "raw_phones TEXT, spans_json TEXT, g2p_score REAL, pronunciation_status TEXT DEFAULT 'pending' "
    "CHECK(pronunciation_status IN ('pending','generated','error')), "
    "proposal_status TEXT DEFAULT 'pending' "
    "CHECK(proposal_status IN ('candidate','experimental','incomplete','error','pending')), "
    "proposal_source TEXT, model_json TEXT, error TEXT, updated_at TEXT)",
    "CREATE TABLE corpus_metadata(key TEXT PRIMARY KEY, value TEXT)",
)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _language(language):
    if language not in LANGUAGES:
        raise ValueError(f"language must be one of {tuple(LANGUAGES)}")
    return LANGUAGES[language]


def _schema_signature(db):
    tables = {row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    return {table: (db.execute(f'PRAGMA table_info("{table}")').fetchall(),
                    db.execute(f'PRAGMA foreign_key_list("{table}")').fetchall())
            for table in tables if table in {"forms", "adjudications", "foreign_evidence",
                                              "corpus_metadata"}}, tables


def validate_schema(db, language):
    _language(language)
    reference = sqlite3.connect(":memory:")
    try:
        for statement in SCHEMA:
            reference.execute(statement)
        if _schema_signature(db) != _schema_signature(reference):
            raise ValueError("wrong foreign inventory schema; refusing to modify database")
    finally:
        reference.close()
    values = dict(db.execute("SELECT key,value FROM corpus_metadata"))
    if values.get("language") != language or values.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("wrong inventory language or schema_version")
    if db.execute("SELECT 1 FROM foreign_evidence WHERE language IS NULL OR language != ? LIMIT 1",
                  (language,)).fetchone():
        raise ValueError("wrong language in existing evidence")


def initialize_inventory(path, language):
    """Open/create only this exact inventory schema; caller owns the connection."""
    _language(language)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=60)
    try:
        objects = db.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")
        if objects.fetchone() is None:
            with db:
                for statement in SCHEMA:
                    db.execute(statement)
                db.executemany("INSERT INTO corpus_metadata VALUES (?,?)", [
                    ("language", language), ("schema_version", SCHEMA_VERSION),
                    ("ipa_description", IPA_NOTE), ("ipa_version", IPA_VERSION),
                ])
        validate_schema(db, language)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        return db
    except BaseException:
        db.close()
        raise


def phones_to_ipa(raw_phones, language):
    """Render validated whole MFA phone tokens as generated broad IPA."""
    _language(language)
    tokens = raw_phones.split()
    unknown = set(tokens) - PHONE_SETS[language]
    if not tokens or unknown:
        raise ValueError(f"empty or unsupported MFA phones: {sorted(unknown)!r}")
    return "".join(IPA_REPLACEMENTS.get(token, token) for token in tokens)


def load_corpus(language, translate_master=None):
    """Full loader type sets: no training split and no cross-language subtraction."""
    import build_english_profile as english
    import build_french_profile as french
    import build_german_profile as german

    _language(language)
    base = Path(translate_master) if translate_master is not None else english.DEFAULT_TRANSLATE_MASTER
    if language == "de":
        return german.load_german_types(base)
    if language == "fr":
        return french.load_french_types(base)
    words, sources = english.load_english_types(english.DEFAULT_CORPUS)
    additional, additional_sources = english.load_chandler_types(base)
    return words | additional, sources + additional_sources


def runtime_model_info(language):
    """Keep upstream model_info intact, plus symbol/source hashes and IPA policy."""
    import slabika_pronunciation as runtime

    info = runtime.model_info(_language(language))
    resource = files(runtime).joinpath("models", info["archive"])
    with resource.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != info["sha256"]:
        raise ValueError("installed G2P archive checksum mismatch")
    with resource.open("rb") as stream, zipfile.ZipFile(stream) as archive:
        member = str(Path(info["member"]).with_name("phones.sym")).replace("\\", "/")
        symbols = archive.read(member)
        actual = {line.split()[0] for line in symbols.decode("utf-8").splitlines()} - {"<eps>"}
        if actual - PHONE_SETS[language]:
            raise ValueError("installed model phone inventory is unsupported")
    return {**info, "phones_sym_sha256": hashlib.sha256(symbols).hexdigest(),
            "runtime_sha256": hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest(),
            "ipa_version": IPA_VERSION, "ipa_description": IPA_NOTE,
            "ipa_token_replacements": IPA_REPLACEMENTS}


def _versions():
    versions = {"builder": SCHEMA_VERSION, "ipa": IPA_VERSION, "python": sys.version}
    for name in ("slabika", "slabika-pronunciation"):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "source checkout (see hashes)"
    versions["source_sha256"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__), ROOT / "tools/evaluate_foreign_corpora.py", ROOT / "src/slabika/english_projection.py",
                     ROOT / "src/slabika/foreign_patterns.py",
                     ROOT / "src/slabika/patterns/foreign/hyph-de-1996.tex",
                     ROOT / "src/slabika/patterns/foreign/hyph-fr.tex")
    }
    return versions


def _batch_size(size):
    if not 1 <= size <= 500:
        raise ValueError("batch_size must be between 1 and 500")


def populate_forms(db, language, forms, *, batch_size=500):
    """Seed rows without overwriting casing, adjudications, or existing evidence."""
    _batch_size(batch_size)
    validate_schema(db, language)
    words = sorted(set(forms) | {row[0] for row in db.execute("SELECT form FROM forms")})
    for start in range(0, len(words), batch_size):
        with db:
            for word in words[start:start + batch_size]:
                db.execute("INSERT OR IGNORE INTO forms(form) VALUES (?)", (word,))
                db.execute("INSERT OR IGNORE INTO adjudications(form) VALUES (?)", (word,))
                db.execute("INSERT OR IGNORE INTO foreign_evidence(form,language) VALUES (?,?)",
                           (word, language))
    return len(words)


def generate_evidence(word, language, model, *, pronounce=None, previous=None):
    """Failures remain explicit; independent DE/FR proposals can survive G2P errors."""
    from slabika import adapt_foreign_word
    from evaluate_foreign_corpora import divided, project_psp_points

    if pronounce is None:
        from slabika_pronunciation import pronounce
    row = dict(previous) if previous else {}
    row.update(form=word, language=language, updated_at=datetime.now(timezone.utc).isoformat())
    errors = []
    pronunciation = None
    if row.get("pronunciation_status") == "generated":
        pronunciation = SimpleNamespace(word=word, language=_language(language),
                                        phones=row["raw_phones"], score=row["g2p_score"],
                                        spans=json.loads(row["spans_json"]))
    else:
        row.update(ipa=None, raw_phones=None, spans_json=None, g2p_score=None,
                   pronunciation_status="error", model_json=json_text(model))
        try:
            pronunciation = pronounce(word, _language(language))
            row.update(raw_phones=pronunciation.phones, spans_json=json_text(pronunciation.spans),
                       g2p_score=pronunciation.score)
            if not math.isfinite(pronunciation.score):
                raise ValueError("non-finite G2P score")
            if pronunciation.word != word or pronunciation.language != _language(language):
                raise ValueError("G2P returned a different word or language")
            if "".join(p for _, ps in pronunciation.spans for p in ps) != pronunciation.phones.replace(" ", ""):
                raise ValueError("raw phones and alignment disagree")
            row["ipa"] = phones_to_ipa(" ".join(p for _, ps in pronunciation.spans for p in ps), language)
            row["pronunciation_status"] = "generated"
        except Exception as error:
            pronunciation = None
            errors.append(f"pronunciation: {type(error).__name__}: {error}")
    if row.get("proposal_status") not in {"candidate", "experimental", "incomplete"}:
        row.update(proposed_hyphenation=None, proposal_status="error",
                   proposal_source=("evaluate_foreign_corpora.project_psp_points" if language == "en"
                                    else "slabika.adapt_foreign_word"))
        try:
            if language == "en":
                if pronunciation is None:
                    raise ValueError("English projection requires generated pronunciation")
                points, complete = project_psp_points(pronunciation)
                row.update(proposed_hyphenation=divided(word, points),
                           proposal_status="experimental" if complete else "incomplete")
            else:
                row.update(proposed_hyphenation=adapt_foreign_word(word, language).render(),
                           proposal_status="candidate")
        except Exception as error:
            errors.append(f"proposal: {type(error).__name__}: {error}")
    row["error"] = "\n".join(errors)
    return row


def populate_evidence(db, language, model, *, forms=None, limit=None, batch_size=500,
                      pronounce=None, progress=None):
    """Retry pending/errors; preserve successful stages and all human-owned fields."""
    _batch_size(batch_size)
    validate_schema(db, language)
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative")
    allowed = set(forms) if forms is not None else None
    cursor = db.execute("SELECT * FROM foreign_evidence WHERE pronunciation_status != 'generated' "
                        "OR proposal_status IN ('pending','error') ORDER BY form")
    columns = [column[0] for column in cursor.description]
    pending = [dict(zip(columns, row)) for row in cursor.fetchall()
               if allowed is None or row[0] in allowed]
    if limit is not None:
        pending = pending[:limit]
    for start in range(0, len(pending), batch_size):
        # Decode outside the write transaction so reviewers are not blocked by G2P.
        rows = [generate_evidence(old["form"], language, model, pronounce=pronounce, previous=old)
                for old in pending[start:start + batch_size]]
        with db:
            for row in rows:
                db.execute("UPDATE foreign_evidence SET " +
                           ",".join(f"{column}=:{column}" for column in columns if column != "form") +
                           " WHERE form=:form", row)
        if progress:
            progress(min(start + batch_size, len(pending)), len(pending))
    return len(pending)


def verify_inventory(db, language, expected_forms=None):
    """Check SQLite/schema integrity and exact coverage of the requested corpus."""
    validate_schema(db, language)
    if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("inventory integrity_check failed")
    if db.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("inventory foreign_key_check failed")
    if expected_forms is not None:
        expected = set(expected_forms)
        for table in ("forms", "adjudications", "foreign_evidence"):
            present = {r[0] for r in db.execute(f"SELECT form FROM {table}")}
            if not expected <= present:
                raise ValueError(f"missing corpus forms in {table}: {len(expected - present)}")
    if db.execute("SELECT 1 FROM foreign_evidence WHERE "
                  "(pronunciation_status='generated' AND (ipa IS NULL OR ipa='' OR "
                  "raw_phones IS NULL OR spans_json IS NULL OR model_json IS NULL)) OR "
                  "(proposal_status IN ('candidate','experimental','incomplete') AND "
                  "proposed_hyphenation IS NULL) OR "
                  "((pronunciation_status='error' OR proposal_status='error') AND "
                  "(error IS NULL OR error='')) LIMIT 1").fetchone():
        raise ValueError("inconsistent evidence status/payload")
    return {"forms": db.execute("SELECT count(*) FROM forms").fetchone()[0],
            "pronunciation": dict(db.execute("SELECT pronunciation_status,count(*) "
                                             "FROM foreign_evidence GROUP BY pronunciation_status")),
            "proposals": dict(db.execute("SELECT proposal_status,count(*) "
                                         "FROM foreign_evidence GROUP BY proposal_status"))}


def main(argv=None):
    import build_english_profile as english

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=(*LANGUAGES, "all"), default="all")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--translate-master", type=Path, default=english.DEFAULT_TRANSLATE_MASTER)
    parser.add_argument("--limit", type=int, help="maximum pending evidence rows per language; all forms are seeded")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")
    errors = False
    for language in LANGUAGES if args.language == "all" else (args.language,):
        words, sources = load_corpus(language, args.translate_master)
        if args.translate_master == english.DEFAULT_TRANSLATE_MASTER and len(words) != EXPECTED_COUNTS[language]:
            raise ValueError(f"{language} full corpus drift: {len(words)} != {EXPECTED_COUNTS[language]}")
        model = runtime_model_info(language)
        versions = _versions()
        model["builder_versions"] = versions
        path = args.output_dir / f"{language}.sqlite"
        db = initialize_inventory(path, language)
        try:
            with db:
                db.executemany("INSERT OR IGNORE INTO corpus_metadata VALUES (?,?)", [
                    ("provenance", json_text({"sources": sources, "types": len(words),
                                             "selection": "full loader type set; no split or homograph removal",
                                             "translate_master": str(args.translate_master)})),
                    ("versions", json_text(versions)), ("model_info", json_text(model)),
                ])
            populate_forms(db, language, words)
            print(f"{language}: seeded {len(words)} corpus types in {path.resolve()}", flush=True)
            populate_evidence(db, language, model, limit=args.limit,
                              progress=lambda done, total: print(
                                  f"{language}: committed {done}/{total} evidence rows", flush=True))
            summary = verify_inventory(db, language, words)
            print(f"{language}: verified {json_text(summary)}", flush=True)
            errors |= bool(summary["pronunciation"].get("error") or summary["proposals"].get("error"))
        finally:
            db.close()
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
