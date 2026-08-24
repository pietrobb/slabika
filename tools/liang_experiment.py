# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Generate Liang patterns from the current engine and compare them to 1992 TeX patterns."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from slabika import break_points as engine_break_points  # noqa: E402
from slabika.phonology import HYPHENATABLE_LETTERS  # noqa: E402
from tools.review.tex_patterns import break_points, load_tex  # noqa: E402

SPLIT_SALT = "slabika-liang-v1"
PROFILE = (
    (1, 1, 3, 1, 5, 1),
    (2, 1, 3, 1, 5, 1),
    (3, 2, 6, 1, 3, 1),
    (4, 2, 7, 1, 3, 1),
)
_DIGIT = re.compile(r"\d")
ENGINE_MODES = {
    "preferred": {"all_points": False, "contextual": False},
    "permissive": {"all_points": True, "contextual": True},
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _split_is_test(word: str) -> bool:
    digest = hashlib.sha256(f"{SPLIT_SALT}\0{word}".encode()).digest()
    return digest[0] < 51  # 51 / 256 = 19.92 percent.


def _engine_points(word: str, mode: str) -> set[int]:
    options = ENGINE_MODES[mode]
    return set(engine_break_points(word, **options))


def _hyphenated(word: str, mode: str) -> str:
    points = _engine_points(word, mode)
    return "".join(("-" if index in points else "") + char for index, char in enumerate(word))


def load_words(database: Path) -> tuple[list[str], dict[str, int]]:
    with sqlite3.connect(database) as connection:
        source = [
            row[0]
            for row in connection.execute(
                "SELECT form FROM forms WHERE casing_status = 'resolved' ORDER BY form"
            )
        ]

    accepted: set[str] = set()
    rejected_non_alpha = 0
    rejected_alphabet = 0
    rejected_long = 0
    for form in source:
        word = form.casefold()
        if not word.isalpha():
            rejected_non_alpha += 1
        elif len(word) > 50:
            rejected_long += 1
        elif any(char not in HYPHENATABLE_LETTERS for char in word):
            rejected_alphabet += 1
        else:
            accepted.add(word)

    words = sorted(accepted)
    stats = {
        "resolved_source_rows": len(source),
        "accepted_unique_words": len(words),
        "duplicates_after_casefold": len(source)
        - rejected_non_alpha
        - rejected_alphabet
        - rejected_long
        - len(words),
        "rejected_non_alpha": rejected_non_alpha,
        "rejected_outside_engine_alphabet": rejected_alphabet,
        "rejected_over_50_characters": rejected_long,
    }
    return words, stats


def load_training_words(dictionary: Path) -> list[str]:
    return sorted(
        {
            line.strip().replace("-", "")
            for line in dictionary.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    )


def write_training_files(
    train: list[str], directory: Path, mode: str
) -> tuple[Path, Path, Path]:
    dictionary = directory / "train.dic"
    initial = directory / "patterns.0"
    translate = directory / "slovak.tra"

    dictionary.write_text(
        "\n".join(_hyphenated(word, mode) for word in train) + "\n", encoding="utf-8"
    )
    initial.write_text("", encoding="utf-8")

    alphabet = sorted(set("".join(train)))
    translation_lines = [" 2 3"]
    for char in alphabet:
        upper = char.upper()
        representations = f"/{char}/"
        if upper != char:
            representations += f"{upper}/"
        translation_lines.append(representations + "/")
    translate.write_text("\n".join(translation_lines) + "\n", encoding="utf-8")
    return dictionary, initial, translate


def run_patgen(
    executable: str, dictionary: Path, initial: Path, translate: Path, directory: Path
) -> tuple[Path, float]:
    raw_patterns = directory / "patterns.raw"
    answers = ["1 4"]
    for _level, pat_start, pat_finish, good, bad, threshold in PROFILE:
        answers.extend((f"{pat_start} {pat_finish}", f"{good} {bad} {threshold}"))
    answers.append("n")

    started = time.perf_counter()
    result = subprocess.run(
        [executable, str(dictionary), str(initial), str(raw_patterns), str(translate)],
        cwd=directory,
        input="\n".join(answers) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    elapsed = time.perf_counter() - started
    (directory / "patgen.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0 or not raw_patterns.exists():
        raise RuntimeError(f"patgen failed with exit code {result.returncode}; see patgen.log")
    return raw_patterns, elapsed


def write_tex_patterns(raw_patterns: Path, output: Path, mode: str) -> int:
    tokens = raw_patterns.read_text(encoding="utf-8").split()
    lines = [
        "% SPDX-FileCopyrightText: 2026 Peter Bezemek",
        "% SPDX-License-" "Identifier: CC0-1.0 OR MIT",
        "% EXPERIMENTAL / WORK IN PROGRESS — not the project's final released patterns.",
        "% Generated from the current slabika engine by tools/liang_experiment.py.",
        f"% Engine mode: {mode}.",
        "% This reproduces engine output; it is not an independently verified PSP gold set.",
        "% left_hyphen_min = 2, right_hyphen_min = 3",
        "\\patterns{",
        *tokens,
        "}",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    return len(tokens)


def _metrics(targets: dict[str, set[int]], predictions: dict[str, set[int]]) -> dict[str, object]:
    good = bad = missed = exact = 0
    examples = []
    for word, expected in targets.items():
        actual = predictions[word]
        good += len(expected & actual)
        bad += len(actual - expected)
        missed += len(expected - actual)
        if actual == expected:
            exact += 1
        elif len(examples) < 30:
            examples.append(
                {
                    "word": word,
                    "engine": sorted(expected),
                    "predicted": sorted(actual),
                    "extra": sorted(actual - expected),
                    "missing": sorted(expected - actual),
                }
            )

    precision = good / (good + bad) if good + bad else 1.0
    recall = good / (good + missed) if good + missed else 1.0
    beta = 1 / 7
    f_beta = (
        (1 + beta * beta) * precision * recall / (beta * beta * precision + recall)
        if precision or recall
        else 0.0
    )
    return {
        "words": len(targets),
        "exact_words": exact,
        "exact_word_rate": exact / len(targets),
        "good_points": good,
        "bad_points": bad,
        "missed_points": missed,
        "precision": precision,
        "recall": recall,
        "f_beta_1_over_7": f_beta,
        "first_30_non_exact": examples,
    }


def evaluate(
    test: list[str], generated_tex: Path, original_tex: Path, mode: str
) -> dict[str, object]:
    generated_patterns, generated_exceptions = load_tex(generated_tex)
    original_patterns, original_exceptions = load_tex(original_tex)
    raw_targets = {word: _engine_points(word, mode) for word in test}
    targets = {
        word: {point for point in points if 2 <= point <= len(word) - 3}
        for word, points in raw_targets.items()
    }
    generated = {
        word: set(break_points(word, generated_patterns, generated_exceptions, 2, 3))
        for word in test
    }
    original = {
        word: set(break_points(word, original_patterns, original_exceptions, 2, 3))
        for word in test
    }
    return {
        "generated_from_current_engine": _metrics(targets, generated),
        "jana_chlebikova_1992": _metrics(targets, original),
        "test_engine_points_before_tex_mins": sum(map(len, raw_targets.values())),
        "test_target_points_after_tex_mins": sum(map(len, targets.values())),
        "engine_points_removed_by_tex_mins": sum(
            len(raw_targets[word] - targets[word]) for word in test
        ),
        "original_pattern_count": len(original_patterns),
        "original_exception_count": len(original_exceptions),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "tests" / "data" / "translatemaster_hyphenation_working.sqlite",
    )
    parser.add_argument("--original", type=Path, default=ROOT / "tex" / "hyph-sk.tex")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "scratch" / "liang-experiment")
    parser.add_argument("--mode", choices=ENGINE_MODES, default="preferred")
    parser.add_argument(
        "--training-dictionary",
        type=Path,
        help="Reuse the words from an existing PATGEN dictionary and relabel them.",
    )
    parser.add_argument("--patgen", default="patgen")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    words, corpus_stats = load_words(args.database)
    base_train = [word for word in words if not _split_is_test(word)]
    test = [word for word in words if _split_is_test(word)]
    train = (
        load_training_words(args.training_dictionary)
        if args.training_dictionary
        else base_train
    )
    test_words = set(test)
    train = [word for word in train if word not in test_words]

    dictionary, initial, translate = write_training_files(train, output_dir, args.mode)
    raw_patterns, seconds = run_patgen(args.patgen, dictionary, initial, translate, output_dir)
    generated_tex = output_dir / f"hyph-sk-slabika-{args.mode}.tex"
    generated_pattern_count = write_tex_patterns(raw_patterns, generated_tex, args.mode)
    evaluation = evaluate(test, generated_tex, args.original, args.mode)

    report = {
        "warning": "Engine output is the replication target, not an independent PSP gold set.",
        "split": {
            "method": "SHA-256 salted word hash; first byte < 51 is test",
            "salt": SPLIT_SALT,
            "train_words": len(train),
            "test_words": len(test),
        },
        "corpus": corpus_stats,
        "engine_mode": {
            "name": args.mode,
            "call": (
                "slabika.break_points(word)"
                if args.mode == "preferred"
                else "slabika.break_points(word, all_points=True, contextual=True)"
            ),
        },
        "common_tex_hyphen_mins_applied_to_targets_and_both_matchers": {"left": 2, "right": 3},
        "profile_name": "cshyphen (Metelka and Sojka, Hyph-bench 2025, Table 4)",
        "profile": [
            {
                "level": level,
                "pat_start": start,
                "pat_finish": finish,
                "good_weight": good,
                "bad_weight": bad,
                "threshold": threshold,
            }
            for level, start, finish, good, bad, threshold in PROFILE
        ],
        "patgen_seconds": seconds,
        "generated_pattern_count": generated_pattern_count,
        "files": {
            "database": str(args.database.resolve()),
            "database_sha256": _sha256(args.database),
            "training_word_source": (
                str(args.training_dictionary.resolve())
                if args.training_dictionary
                else str(args.database.resolve())
            ),
            "training_word_source_sha256": (
                _sha256(args.training_dictionary)
                if args.training_dictionary
                else _sha256(args.database)
            ),
            "original_patterns": str(args.original.resolve()),
            "original_patterns_sha256": _sha256(args.original),
            "training_dictionary_sha256": _sha256(dictionary),
            "generated_patterns": str(generated_tex),
            "generated_patterns_sha256": _sha256(generated_tex),
        },
        "evaluation": evaluation,
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for name, metrics in evaluation.items():
        if not isinstance(metrics, dict) or "precision" not in metrics:
            continue
        print(
            f"{name}: patterns={evaluation.get('original_pattern_count') if name == 'jana_chlebikova_1992' else generated_pattern_count} "
            f"exact={metrics['exact_word_rate']:.4%} precision={metrics['precision']:.4%} "
            f"recall={metrics['recall']:.4%} F1/7={metrics['f_beta_1_over_7']:.6f}"
        )
    print(f"report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
