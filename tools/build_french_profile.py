# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build the distributable French n-gram profile from approved local corpora."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRANSLATE_MASTER = Path(r"C:\Users\peter\PycharmProjects\TranslateMaster")
DEFAULT_INVENTORY = ROOT / "tests/data/translatemaster_hyphenation_working.sqlite"
DEFAULT_OUTPUT = ROOT / "src/slabika/data/french_profile.json"
DEFAULT_AUDIT = ROOT / "scratch/_french_language_inventory_flags.json"
CORPUS_SOURCES = (
    (Path("databases/casanova_fr.db"), "casanova_fr"),
    (Path("translation_project.db"), "tajomny-ostrov"),
)
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
FRENCH_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzàâäæçéèêëîïôöœùûüÿ")
GRAM_SIZES = (3, 4)
LANGUAGES = ("fr", "sk")
THRESHOLD = 2.25
MIN_SUPPORT = 2
MIN_COVERAGE = 0.5


def normalize(word: str) -> str:
    return unicodedata.normalize("NFC", word).lower()


def family_bucket(word: str) -> str:
    key = "".join(
        char
        for char in unicodedata.normalize("NFD", word)
        if not unicodedata.combining(char)
    )[:5]
    number = int(hashlib.sha256(("french-language-v1:" + key).encode()).hexdigest()[:8], 16)
    return "train" if number % 100 < 70 else "calibration" if number % 100 < 85 else "test"


def features(word: str, letters: frozenset[str]) -> set[str]:
    marked = f"^{word}$"
    return {
        marked[index : index + size]
        for size in GRAM_SIZES
        for index in range(len(marked) - size + 1)
    } | (set(word) & letters)


def load_french_types(base: Path) -> tuple[set[str], list[dict[str, object]]]:
    words: set[str] = set()
    sources = []
    for relative, project_name in CORPUS_SOURCES:
        path = base / relative
        digest = hashlib.sha256()
        local: set[str] = set()
        paragraphs = tokens = characters = 0
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as database:
            projects = [
                row[0]
                for row in database.execute(
                    "SELECT name FROM projects WHERE name = ? ORDER BY id", (project_name,)
                )
            ]
            if projects != [project_name]:
                raise ValueError(f"Missing French source project {project_name!r} in {path}")
            for (text,) in database.execute(
                """
                SELECT p.source_text
                FROM paragraphs AS p
                JOIN chapters AS c ON c.id = p.chapter_id
                JOIN projects AS project ON project.id = c.project_id
                WHERE project.name = ? AND p.source_text IS NOT NULL
                ORDER BY p.id
                """,
                (project_name,),
            ):
                paragraphs += 1
                characters += len(text)
                digest.update(text.encode("utf-8"))
                digest.update(b"\0")
                accepted = [
                    normalize(word)
                    for word in WORD_RE.findall(text)
                    if len(word) >= 3 and set(normalize(word)) <= FRENCH_LETTERS
                ]
                tokens += len(accepted)
                local.update(accepted)
        words.update(local)
        sources.append(
            {
                "file": relative.as_posix(),
                "projects": projects,
                "paragraphs": paragraphs,
                "characters": characters,
                "accepted_tokens": tokens,
                "types": len(local),
                "source_text_sha256": digest.hexdigest(),
            }
        )
    return words, sources


def load_inventory(path: Path) -> set[str]:
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as database:
        return {
            normalize(row[0])
            for row in database.execute("SELECT form FROM forms")
            if len(row[0]) >= 3 and row[0].isalpha()
        }


def split_types(french: set[str], slovak: set[str]) -> tuple[dict[str, dict[str, set[str]]], int]:
    overlap = french & slovak
    unique = {"fr": french - overlap, "sk": slovak - overlap}
    partitions = {
        split: {
            language: {word for word in unique[language] if family_bucket(word) == split}
            for language in LANGUAGES
        }
        for split in ("train", "calibration", "test")
    }
    return partitions, len(overlap)


def informative_letters(training: dict[str, set[str]]) -> frozenset[str]:
    counts = {language: Counter() for language in LANGUAGES}
    for language in LANGUAGES:
        for word in training[language]:
            counts[language].update(set(word))
    selected = set()
    for letter in set(counts["fr"]) | set(counts["sk"]):
        rates = {
            language: counts[language][letter] / len(training[language])
            for language in LANGUAGES
        }
        first, second = sorted(LANGUAGES, key=rates.get, reverse=True)
        ratio = rates[first] / rates[second] if rates[second] else math.inf
        if counts[first][letter] >= 10 and ratio >= 5:
            selected.add(letter)
    return frozenset(selected)


def fit(training: dict[str, set[str]]) -> tuple[frozenset[str], dict[str, float]]:
    letters = informative_letters(training)
    counts = {language: Counter() for language in LANGUAGES}
    sizes = {language: len(training[language]) for language in LANGUAGES}
    for language in LANGUAGES:
        for word in sorted(training[language]):
            counts[language].update(features(word, letters))
    vocabulary = set(counts["fr"]) | set(counts["sk"])
    weights = {
        gram: round(
            math.log((counts["fr"][gram] + 0.5) / (sizes["fr"] + 1))
            - math.log((counts["sk"][gram] + 0.5) / (sizes["sk"] + 1)),
            6,
        )
        for gram in vocabulary
        if counts["fr"][gram] + counts["sk"][gram] >= 3
    }
    return letters, weights


def evidence(
    word: str, letters: frozenset[str], weights: dict[str, float]
) -> tuple[float, int, float]:
    word_features = features(normalize(word), letters)
    known = word_features & weights.keys()
    score = (
        sum(weights[gram] for gram in sorted(known)) / len(known) if known else -100.0
    )
    return score, len(known), len(known) / max(1, len(word_features))


def is_french(score: float, support: int, coverage: float) -> bool:
    return support >= MIN_SUPPORT and coverage >= MIN_COVERAGE and score >= THRESHOLD


def evaluate(
    partition: dict[str, set[str]], letters: frozenset[str], weights: dict[str, float]
) -> dict[str, object]:
    calls = Counter()
    for language in LANGUAGES:
        for word in partition[language]:
            calls[language] += is_french(*evidence(word, letters, weights))
    true_positive = calls["fr"]
    false_positive = calls["sk"]
    return {
        "french_types": len(partition["fr"]),
        "slovak_types": len(partition["sk"]),
        "french_detected": true_positive,
        "slovak_flagged": false_positive,
        "proxy_recall": true_positive / len(partition["fr"]),
        "proxy_precision": true_positive / max(1, true_positive + false_positive),
        "slovak_flag_rate": false_positive / len(partition["sk"]),
    }


def write_audit(
    path: Path,
    inventory: set[str],
    french: set[str],
    letters: frozenset[str],
    weights: dict[str, float],
) -> int:
    rows = []
    for word in sorted(inventory):
        score, support, coverage = evidence(word, letters, weights)
        if is_french(score, support, coverage):
            rows.append(
                {
                    "form": word,
                    "score": round(score, 6),
                    "support": support,
                    "coverage": round(coverage, 6),
                    "attested_in_french_corpus": word in french,
                }
            )
    report = {
        "warning": "Automatic candidates, not independently adjudicated language labels.",
        "inventory_forms": len(inventory),
        "flagged_french": len(rows),
        "threshold": THRESHOLD,
        "rows": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translate-master", type=Path, default=DEFAULT_TRANSLATE_MASTER)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()

    inventory_hash = hashlib.sha256(args.inventory.read_bytes()).hexdigest()
    french, sources = load_french_types(args.translate_master)
    inventory = load_inventory(args.inventory)
    partitions, overlap = split_types(french, inventory)
    letters, weights = fit(partitions["train"])
    payload = {
        "version": 1,
        "method": "type-weighted binary French-vs-Slovak log-odds over boundary-aware character n-grams",
        "warning": "Validation labels are corpus-source proxies, not independent language truth.",
        "threshold": THRESHOLD,
        "minimum_support": MIN_SUPPORT,
        "minimum_coverage": MIN_COVERAGE,
        "gram_sizes": list(GRAM_SIZES),
        "boundary_markers": True,
        "informative_letters": "".join(sorted(letters)),
        "weights": dict(sorted(weights.items())),
        "training": {
            "french_types_total": len(french),
            "slovak_types_total": len(inventory),
            "shared_spellings_excluded": overlap,
            "partitions": {
                split: {language: len(words) for language, words in by_language.items()}
                for split, by_language in partitions.items()
            },
            "sources": sources,
            "inventory_sha256": inventory_hash,
        },
        "calibration": evaluate(partitions["calibration"], letters, weights),
        "test": evaluate(partitions["test"], letters, weights),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    flagged = write_audit(args.audit_output, inventory, french, letters, weights)
    assert hashlib.sha256(args.inventory.read_bytes()).hexdigest() == inventory_hash
    print(f"Wrote {len(weights)} weights to {args.output}")
    print(f"Flagged {flagged} of {len(inventory)} inventory forms; audit: {args.audit_output}")
    print(json.dumps(payload["test"], ensure_ascii=False))


if __name__ == "__main__":
    main()
