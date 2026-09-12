# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build one comparable EN/DE/FR/SK word-language profile."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import build_english_profile as english
import build_french_profile as french
import build_german_profile as german

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src/slabika/data/language_router_profile.json"
LANGUAGES = ("english", "german", "french", "slovak")
GRAM_SIZES = (3, 4, 5)
ALPHA = 0.05
MIN_GLOBAL_COUNT = 5


def family_bucket(word: str) -> str:
    key = "".join(
        char
        for char in unicodedata.normalize("NFD", word)
        if not unicodedata.combining(char)
    )[:5]
    number = int(hashlib.sha256(("language-router-v1:" + key).encode()).hexdigest()[:8], 16)
    return "train" if number % 100 < 70 else "calibration" if number % 100 < 85 else "test"


def features(word: str) -> list[str]:
    marked = f"^{word}$"
    return [
        marked[index : index + size]
        for size in GRAM_SIZES
        for index in range(len(marked) - size + 1)
    ]


def split_unique(words: dict[str, set[str]]) -> tuple[dict[str, dict[str, set[str]]], int]:
    owners: dict[str, set[str]] = defaultdict(set)
    for language, forms in words.items():
        for form in forms:
            owners[form].add(language)
    unique = {
        language: {form for form in forms if len(owners[form]) == 1}
        for language, forms in words.items()
    }
    partitions = {
        split: {
            language: {form for form in unique[language] if family_bucket(form) == split}
            for language in LANGUAGES
        }
        for split in ("train", "calibration", "test")
    }
    return partitions, sum(len(languages) > 1 for languages in owners.values())


def fit(training: dict[str, set[str]]) -> dict[str, list[float]]:
    counts = {language: Counter() for language in LANGUAGES}
    for language, forms in training.items():
        for form in forms:
            counts[language].update(features(form))
    totals = {language: sum(counts[language].values()) for language in LANGUAGES}
    global_counts = Counter()
    for language_counts in counts.values():
        global_counts.update(language_counts)
    return {
        feature: [
            round(
                math.log(
                    (counts[language][feature] + ALPHA) / (totals[language] + 2 * ALPHA)
                ),
                6,
            )
            for language in LANGUAGES
        ]
        for feature, count in sorted(global_counts.items())
        if count >= MIN_GLOBAL_COUNT
    }


def scores(word: str, weights: dict[str, list[float]]) -> list[float]:
    result = [0.0] * len(LANGUAGES)
    for feature in features(word):
        values = weights.get(feature)
        if values is not None:
            for index, value in enumerate(values):
                result[index] += value
    return result


def evaluate(partition: dict[str, set[str]], weights: dict[str, list[float]]) -> dict:
    matrix = {language: Counter() for language in LANGUAGES}
    for actual, forms in partition.items():
        for form in forms:
            values = scores(form, weights)
            predicted = LANGUAGES[max(range(len(values)), key=values.__getitem__)]
            matrix[actual][predicted] += 1
    accuracy = {
        language: matrix[language][language] / sum(matrix[language].values())
        for language in LANGUAGES
    }
    return {
        "matrix": {
            actual: {predicted: matrix[actual][predicted] for predicted in LANGUAGES}
            for actual in LANGUAGES
        },
        "accuracy": accuracy,
        "macro_accuracy": sum(accuracy.values()) / len(accuracy),
    }


def main() -> None:
    inventory_hash = hashlib.sha256(english.DEFAULT_INVENTORY.read_bytes()).hexdigest()
    english_words, english_sources = english.load_english_types(english.DEFAULT_CORPUS)
    chandler_words, chandler_sources = english.load_chandler_types(english.DEFAULT_TRANSLATE_MASTER)
    german_words, german_sources = german.load_german_types(german.DEFAULT_TRANSLATE_MASTER)
    french_words, french_sources = french.load_french_types(french.DEFAULT_TRANSLATE_MASTER)
    slovak_words = english.load_inventory(english.DEFAULT_INVENTORY)
    words = {
        "english": english_words | chandler_words,
        "german": german_words,
        "french": french_words,
        "slovak": slovak_words,
    }
    partitions, shared = split_unique(words)
    weights = fit(partitions["train"])
    payload = {
        "version": 1,
        "method": "multiclass type-weighted character n-gram language model for isolated words",
        "warning": "Validation labels are corpus-source proxies, not independent language truth.",
        "languages": list(LANGUAGES),
        "gram_sizes": list(GRAM_SIZES),
        "alpha": ALPHA,
        "minimum_global_count": MIN_GLOBAL_COUNT,
        "weights": weights,
        "training": {
            "raw_types": {language: len(forms) for language, forms in words.items()},
            "shared_spellings_excluded": shared,
            "partitions": {
                split: {language: len(forms) for language, forms in by_language.items()}
                for split, by_language in partitions.items()
            },
            "inventory_sha256": inventory_hash,
            "sources": {
                "english": english_sources + chandler_sources,
                "german": german_sources,
                "french": french_sources,
            },
        },
        "calibration": evaluate(partitions["calibration"], weights),
        "test": evaluate(partitions["test"], weights),
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    assert hashlib.sha256(english.DEFAULT_INVENTORY.read_bytes()).hexdigest() == inventory_hash
    print(f"Wrote {len(weights)} weights to {OUTPUT}")
    print(json.dumps(payload["test"], ensure_ascii=False))


if __name__ == "__main__":
    main()
