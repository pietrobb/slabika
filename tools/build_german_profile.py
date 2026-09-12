# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build the distributable German n-gram profile from approved local corpora."""

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
DEFAULT_OUTPUT = ROOT / "src/slabika/data/german_profile.json"
DEFAULT_AUDIT = ROOT / "scratch/_german_language_inventory_flags.json"
CORPUS_RELATIVE_PATHS = (
    Path("lorber_nz.db"),
    Path("databases/mayerhofer.db"),
    Path("databases/dudde.db"),
    Path("databases/Gralsbotschaft.db"),
)
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
GERMAN_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzäöüß")
GRAM_SIZES = (3, 4)
LANGUAGES = ("de", "sk")
THRESHOLD = 1.75
STRIPPED_STEM_THRESHOLD = 3.0
MIN_SUPPORT = 2
MIN_COVERAGE = 0.6
SLOVAK_ENDINGS = frozenset(
    "om och ovi ov ova ovu ove ovej ovou ová ové ovú ovým ovci ovcom ovcov "
    "ovská ovskej ovské ska ske skeho skej ski skom skou sky skych skym skymi ský".split()
)


def normalize(word: str) -> str:
    return unicodedata.normalize("NFC", word).lower()


def family_bucket(word: str) -> str:
    key = "".join(
        char
        for char in unicodedata.normalize("NFD", word)
        if not unicodedata.combining(char)
    )[:5]
    number = int(hashlib.sha256(("german-language-v1:" + key).encode()).hexdigest()[:8], 16)
    return "train" if number % 100 < 70 else "calibration" if number % 100 < 85 else "test"


def features(word: str, letters: frozenset[str]) -> set[str]:
    return {
        word[index : index + size]
        for size in GRAM_SIZES
        for index in range(len(word) - size + 1)
    } | (set(word) & letters)


def load_german_types(base: Path) -> tuple[set[str], list[dict[str, object]]]:
    words: set[str] = set()
    sources = []
    for relative in CORPUS_RELATIVE_PATHS:
        path = base / relative
        digest = hashlib.sha256()
        local: set[str] = set()
        paragraphs = tokens = 0
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as database:
            projects = [row[0] for row in database.execute("SELECT name FROM projects ORDER BY id")]
            for (text,) in database.execute(
                "SELECT source_text FROM paragraphs WHERE source_text IS NOT NULL ORDER BY id"
            ):
                paragraphs += 1
                digest.update(text.encode("utf-8"))
                digest.update(b"\0")
                accepted = [
                    normalize(word)
                    for word in WORD_RE.findall(text)
                    if len(word) >= 3 and set(normalize(word)) <= GERMAN_LETTERS
                ]
                tokens += len(accepted)
                local.update(accepted)
        words.update(local)
        sources.append(
            {
                "file": relative.as_posix(),
                "projects": projects,
                "paragraphs": paragraphs,
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


def split_types(german: set[str], slovak: set[str]) -> tuple[dict[str, dict[str, set[str]]], int]:
    overlap = german & slovak
    unique = {"de": german - overlap, "sk": slovak - overlap}
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
    for letter in set(counts["de"]) | set(counts["sk"]):
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
    vocabulary = set(counts["de"]) | set(counts["sk"])
    weights = {
        gram: round(
            math.log((counts["de"][gram] + 0.5) / (sizes["de"] + 1))
            - math.log((counts["sk"][gram] + 0.5) / (sizes["sk"] + 1)),
            6,
        )
        for gram in vocabulary
        if counts["de"][gram] + counts["sk"][gram] >= 3
    }
    return letters, weights


def unit_evidence(
    word: str, letters: frozenset[str], weights: dict[str, float]
) -> tuple[float, int, float]:
    word_features = features(word, letters)
    known = word_features & weights.keys()
    score = (
        sum(weights[gram] for gram in sorted(known)) / len(known) if known else -100.0
    )
    return score, len(known), len(known) / max(1, len(word_features))


def evidence(
    word: str, letters: frozenset[str], weights: dict[str, float]
) -> tuple[float, int, float, str, str]:
    normalized = normalize(word)
    score, support, coverage = unit_evidence(normalized, letters, weights)
    best = (score, support, coverage, normalized, "")
    for ending in sorted(SLOVAK_ENDINGS, key=lambda item: (-len(item), item)):
        if not normalized.endswith(ending) or len(normalized) - len(ending) < 4:
            continue
        stem = normalized[: -len(ending)]
        stem_score, stem_support, stem_coverage = unit_evidence(stem, letters, weights)
        if (
            stem_score >= STRIPPED_STEM_THRESHOLD
            and stem_support >= MIN_SUPPORT
            and stem_coverage >= MIN_COVERAGE
            and stem_score > best[0]
        ):
            best = (stem_score, stem_support, stem_coverage, stem, ending)
    return best


def is_german(score: float, support: int, coverage: float) -> bool:
    return support >= MIN_SUPPORT and coverage >= MIN_COVERAGE and score >= THRESHOLD


def evaluate(
    partition: dict[str, set[str]], letters: frozenset[str], weights: dict[str, float]
) -> dict[str, object]:
    calls = Counter()
    for language in LANGUAGES:
        for word in partition[language]:
            score, support, coverage, _, _ = evidence(word, letters, weights)
            calls[language] += is_german(score, support, coverage)
    true_positive = calls["de"]
    false_positive = calls["sk"]
    return {
        "german_types": len(partition["de"]),
        "slovak_types": len(partition["sk"]),
        "german_detected": true_positive,
        "slovak_flagged": false_positive,
        "proxy_recall": true_positive / len(partition["de"]),
        "proxy_precision": true_positive / max(1, true_positive + false_positive),
        "slovak_flag_rate": false_positive / len(partition["sk"]),
    }


def write_audit(
    path: Path,
    inventory: set[str],
    german: set[str],
    letters: frozenset[str],
    weights: dict[str, float],
) -> int:
    rows = []
    for word in sorted(inventory):
        score, support, coverage, stem, ending = evidence(word, letters, weights)
        if is_german(score, support, coverage):
            rows.append(
                {
                    "form": word,
                    "score": round(score, 6),
                    "support": support,
                    "coverage": round(coverage, 6),
                    "stem": stem,
                    "slovak_ending": ending,
                    "attested_in_german_corpus": word in german,
                }
            )
    report = {
        "warning": "Automatic candidates, not independently adjudicated language labels.",
        "inventory_forms": len(inventory),
        "flagged_german": len(rows),
        "threshold": THRESHOLD,
        "stripped_stem_threshold": STRIPPED_STEM_THRESHOLD,
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

    source_hash = hashlib.sha256(args.inventory.read_bytes()).hexdigest()
    german, sources = load_german_types(args.translate_master)
    inventory = load_inventory(args.inventory)
    partitions, overlap = split_types(german, inventory)
    letters, weights = fit(partitions["train"])
    payload = {
        "version": 1,
        "method": "type-weighted binary German-vs-Slovak log-odds over character n-grams",
        "warning": "Validation labels are corpus-source proxies, not independent language truth.",
        "threshold": THRESHOLD,
        "stripped_stem_threshold": STRIPPED_STEM_THRESHOLD,
        "slovak_endings": sorted(SLOVAK_ENDINGS),
        "minimum_support": MIN_SUPPORT,
        "minimum_coverage": MIN_COVERAGE,
        "gram_sizes": list(GRAM_SIZES),
        "informative_letters": "".join(sorted(letters)),
        "weights": dict(sorted(weights.items())),
        "training": {
            "german_types_total": len(german),
            "slovak_types_total": len(inventory),
            "shared_spellings_excluded": overlap,
            "partitions": {
                split: {language: len(words) for language, words in by_language.items()}
                for split, by_language in partitions.items()
            },
            "sources": sources,
            "inventory_sha256": source_hash,
        },
        "calibration": evaluate(partitions["calibration"], letters, weights),
        "test": evaluate(partitions["test"], letters, weights),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    flagged = write_audit(args.audit_output, inventory, german, letters, weights)
    assert hashlib.sha256(args.inventory.read_bytes()).hexdigest() == source_hash
    print(f"Wrote {len(weights)} weights to {args.output}")
    print(f"Flagged {flagged} of {len(inventory)} inventory forms; audit: {args.audit_output}")
    print(json.dumps(payload["test"], ensure_ascii=False))


if __name__ == "__main__":
    main()
