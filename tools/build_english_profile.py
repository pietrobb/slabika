# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Build the distributable English n-gram profile from public-domain prose."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import time
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "scratch/_english_public_domain"
DEFAULT_TRANSLATE_MASTER = Path(r"C:\Users\peter\PycharmProjects\TranslateMaster")
DEFAULT_INVENTORY = ROOT / "tests/data/translatemaster_hyphenation_working.sqlite"
DEFAULT_OUTPUT = ROOT / "src/slabika/data/english_profile.json"
DEFAULT_AUDIT = ROOT / "scratch/_english_language_inventory_flags.json"
GUTENBERG_URL = "https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt"
LONDON_IDS = (
    215,
    310,
    318,
    710,
    746,
    788,
    910,
    1029,
    1056,
    1074,
    1075,
    1089,
    1096,
    1160,
    1161,
    1163,
    1164,
    1187,
    1208,
    1449,
    1655,
    1669,
    1688,
    1730,
    2377,
    2415,
    2416,
    2429,
    2512,
    2545,
    4953,
    5737,
    6455,
    10736,
    11051,
    14449,
    14654,
    14658,
    16257,
    18062,
    21936,
    21971,
    22104,
    28693,
    48474,
    54068,
)
OTHER_EBOOKS = {
    11: "Lewis Carroll",
    35: "H. G. Wells",
    36: "H. G. Wells",
    55: "L. Frank Baum",
    74: "Mark Twain",
    76: "Mark Twain",
    84: "Mary Wollstonecraft Shelley",
    110: "Thomas Hardy",
    158: "Jane Austen",
    174: "Oscar Wilde",
    209: "Henry James",
    345: "Bram Stoker",
    730: "Charles Dickens",
    1342: "Jane Austen",
    1400: "Charles Dickens",
    1661: "Arthur Conan Doyle",
    2701: "Herman Melville",
    2852: "Arthur Conan Doyle",
    5230: "H. G. Wells",
    17396: "Frances Hodgson Burnett",
}
EBOOKS = {**dict.fromkeys(LONDON_IDS, "Jack London"), **OTHER_EBOOKS}
CHANDLER_DB = Path("databases/chandler.db")
CHANDLER_PROJECTS = (
    "Chandler Big Sleep",
    "Chandler Farewell My Lovely",
    "Chandler High Window",
    "Chandler Lady in the Lake",
    "Chandler Little Sister",
    "Chandler Long Goodbye",
    "Chandler Playback",
)
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
START_RE = re.compile(
    r"(?mi)^\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*\s*$"
)
END_RE = re.compile(
    r"(?mi)^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*\s*$"
)
ENGLISH_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyz")
GRAM_SIZES = (3, 4)
LANGUAGES = ("en", "sk")
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
    number = int(hashlib.sha256(("english-language-v1:" + key).encode()).hexdigest()[:8], 16)
    return "train" if number % 100 < 70 else "calibration" if number % 100 < 85 else "test"


def features(word: str, letters: frozenset[str]) -> set[str]:
    marked = f"^{word}$"
    return {
        marked[index : index + size]
        for size in GRAM_SIZES
        for index in range(len(marked) - size + 1)
    } | (set(word) & letters)


def download_sources(corpus: Path) -> None:
    corpus.mkdir(parents=True, exist_ok=True)
    for ebook_id in sorted(EBOOKS):
        path = corpus / f"pg{ebook_id}.txt"
        if path.exists():
            continue
        request = Request(
            GUTENBERG_URL.format(ebook_id=ebook_id),
            headers={
                "User-Agent": "slabika-language-profile-research/1.0 "
                "(single local corpus build)"
            },
        )
        with urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
        time.sleep(0.2)


def metadata_field(header: str, name: str) -> str:
    match = re.search(rf"(?mi)^{name}:\s*(.+?)\s*$", header)
    return match.group(1).strip() if match else ""


def ebook_body(raw: str, ebook_id: int) -> str:
    starts = list(START_RE.finditer(raw))
    ends = list(END_RE.finditer(raw))
    if len(starts) != 1 or len(ends) != 1 or ends[0].start() <= starts[0].end():
        raise ValueError(f"Invalid Project Gutenberg body markers in eBook {ebook_id}")
    return raw[starts[0].end() : ends[0].start()]


def load_english_types(corpus: Path) -> tuple[set[str], list[dict[str, object]]]:
    words: set[str] = set()
    sources = []
    for ebook_id, expected_author in sorted(EBOOKS.items()):
        path = corpus / f"pg{ebook_id}.txt"
        raw_bytes = path.read_bytes()
        raw = raw_bytes.decode("utf-8-sig")
        header = raw[:12_000]
        author = metadata_field(header, "Author")
        language = metadata_field(header, "Language")
        if author != expected_author or language != "English":
            raise ValueError(
                f"Unexpected metadata for eBook {ebook_id}: author={author!r}, "
                f"language={language!r}"
            )
        body = ebook_body(raw, ebook_id)
        accepted = [
            normalize(word)
            for word in WORD_RE.findall(body)
            if len(word) >= 3 and set(normalize(word)) <= ENGLISH_LETTERS
        ]
        local = set(accepted)
        words.update(local)
        sources.append(
            {
                "source_kind": "project_gutenberg",
                "gutenberg_ebook_id": ebook_id,
                "author": author,
                "characters": len(body),
                "accepted_tokens": len(accepted),
                "types": len(local),
                "source_file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            }
        )
    return words, sources


def load_chandler_types(base: Path) -> tuple[set[str], list[dict[str, object]]]:
    path = base / CHANDLER_DB
    words: set[str] = set()
    sources = []
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as database:
        projects = tuple(
            row[0] for row in database.execute("SELECT name FROM projects ORDER BY id")
        )
        if projects != CHANDLER_PROJECTS:
            raise ValueError(f"Unexpected Chandler projects in {path}: {projects!r}")
        for project_name in CHANDLER_PROJECTS:
            digest = hashlib.sha256()
            local: set[str] = set()
            paragraphs = characters = tokens = 0
            for (text,) in database.execute(
                """
                SELECT paragraph.source_text
                FROM paragraphs AS paragraph
                JOIN chapters AS chapter ON chapter.id = paragraph.chapter_id
                JOIN projects AS project ON project.id = chapter.project_id
                WHERE project.name = ? AND paragraph.source_text IS NOT NULL
                ORDER BY paragraph.id
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
                    if len(word) >= 3 and set(normalize(word)) <= ENGLISH_LETTERS
                ]
                tokens += len(accepted)
                local.update(accepted)
            if not paragraphs:
                raise ValueError(f"Empty Chandler source project {project_name!r} in {path}")
            words.update(local)
            sources.append(
                {
                    "source_kind": "local_translate_master",
                    "file": CHANDLER_DB.as_posix(),
                    "project": project_name,
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


def split_types(
    english: set[str], slovak: set[str]
) -> tuple[dict[str, dict[str, set[str]]], dict[str, set[str]], int]:
    overlap = english & slovak
    unique = {"en": english - overlap, "sk": slovak - overlap}
    partitions = {
        split: {
            language: {word for word in unique[language] if family_bucket(word) == split}
            for language in LANGUAGES
        }
        for split in ("train", "calibration", "test")
    }
    return partitions, unique, len(overlap)


def informative_letters(training: dict[str, set[str]]) -> frozenset[str]:
    counts = {language: Counter() for language in LANGUAGES}
    for language in LANGUAGES:
        for word in training[language]:
            counts[language].update(set(word))
    selected = set()
    for letter in set(counts["en"]) | set(counts["sk"]):
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
    vocabulary = set(counts["en"]) | set(counts["sk"])
    weights = {
        gram: round(
            math.log((counts["en"][gram] + 0.5) / (sizes["en"] + 1))
            - math.log((counts["sk"][gram] + 0.5) / (sizes["sk"] + 1)),
            6,
        )
        for gram in vocabulary
        if counts["en"][gram] + counts["sk"][gram] >= 3
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


def is_english(score: float, support: int, coverage: float) -> bool:
    return support >= MIN_SUPPORT and coverage >= MIN_COVERAGE and score >= THRESHOLD


def evaluate(
    partition: dict[str, set[str]], letters: frozenset[str], weights: dict[str, float]
) -> dict[str, object]:
    calls = Counter()
    for language in LANGUAGES:
        for word in partition[language]:
            calls[language] += is_english(*evidence(word, letters, weights))
    true_positive = calls["en"]
    false_positive = calls["sk"]
    return {
        "english_types": len(partition["en"]),
        "slovak_types": len(partition["sk"]),
        "english_detected": true_positive,
        "slovak_flagged": false_positive,
        "proxy_recall": true_positive / len(partition["en"]),
        "proxy_precision": true_positive / max(1, true_positive + false_positive),
        "slovak_flag_rate": false_positive / len(partition["sk"]),
    }


def write_audit(
    path: Path,
    inventory: set[str],
    gutenberg_english: set[str],
    chandler_english: set[str],
    letters: frozenset[str],
    weights: dict[str, float],
) -> int:
    english = gutenberg_english | chandler_english
    rows = []
    for word in sorted(inventory):
        score, support, coverage = evidence(word, letters, weights)
        if is_english(score, support, coverage):
            rows.append(
                {
                    "form": word,
                    "score": round(score, 6),
                    "support": support,
                    "coverage": round(coverage, 6),
                    "attested_in_english_corpus": word in english,
                    "attested_in_gutenberg_corpus": word in gutenberg_english,
                    "attested_in_chandler_corpus": word in chandler_english,
                }
            )
    report = {
        "warning": "Automatic candidates, not independently adjudicated language labels.",
        "inventory_forms": len(inventory),
        "flagged_english": len(rows),
        "threshold": THRESHOLD,
        "rows": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--translate-master", type=Path, default=DEFAULT_TRANSLATE_MASTER)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    if args.download:
        download_sources(args.corpus)
    inventory_hash = hashlib.sha256(args.inventory.read_bytes()).hexdigest()
    gutenberg_english, sources = load_english_types(args.corpus)
    chandler_english, chandler_sources = load_chandler_types(args.translate_master)
    english = gutenberg_english | chandler_english
    sources.extend(chandler_sources)
    inventory = load_inventory(args.inventory)
    partitions, unique, overlap = split_types(english, inventory)
    validation_letters, validation_weights = fit(partitions["train"])
    letters, weights = fit(unique)
    payload = {
        "version": 1,
        "method": "type-weighted binary English-vs-Slovak log-odds over boundary-aware character n-grams",
        "warning": "Validation labels are corpus-source proxies, not independent language truth.",
        "threshold": THRESHOLD,
        "minimum_support": MIN_SUPPORT,
        "minimum_coverage": MIN_COVERAGE,
        "gram_sizes": list(GRAM_SIZES),
        "boundary_markers": True,
        "informative_letters": "".join(sorted(letters)),
        "weights": dict(sorted(weights.items())),
        "training": {
            "english_types_total": len(english),
            "gutenberg_types_total": len(gutenberg_english),
            "chandler_types_total": len(chandler_english),
            "slovak_types_total": len(inventory),
            "shared_spellings_excluded": overlap,
            "final_fit": {language: len(words) for language, words in unique.items()},
            "partitions": {
                split: {language: len(words) for language, words in by_language.items()}
                for split, by_language in partitions.items()
            },
            "sources": sources,
            "inventory_sha256": inventory_hash,
        },
        "calibration": evaluate(
            partitions["calibration"], validation_letters, validation_weights
        ),
        "test": evaluate(partitions["test"], validation_letters, validation_weights),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    flagged = write_audit(
        args.audit_output,
        inventory,
        gutenberg_english,
        chandler_english,
        letters,
        weights,
    )
    assert hashlib.sha256(args.inventory.read_bytes()).hexdigest() == inventory_hash
    print(f"Wrote {len(weights)} weights to {args.output}")
    print(f"Flagged {flagged} of {len(inventory)} inventory forms; audit: {args.audit_output}")
    print(json.dumps(payload["test"], ensure_ascii=False))


if __name__ == "__main__":
    main()
