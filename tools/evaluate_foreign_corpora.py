# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Evaluate automatic language routing and G2P proposals on held-out foreign words."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import build_english_profile as english
import build_french_profile as french
import build_german_profile as german
import build_language_router_profile as router
from slabika import hyphenate, language_scores
from slabika.english_projection import project_psp_points

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "scratch/foreign-corpus-benchmark"
PROFILE = ROOT / "src/slabika/data/language_router_profile.json"
FOREIGN_LANGUAGES = ("english", "german", "french")


@dataclass(frozen=True)
class LanguageMetrics:
    types: int
    correct_language: int
    routed_to_foreign_g2p: int
    missed_as_slovak: int
    misrouted_to_other_foreign: int
    unresolved: int
    language_accuracy: float
    foreign_capture_rate: float


@dataclass(frozen=True)
class PronunciationMetrics:
    sampled: int
    correctly_routed: int
    not_sent_to_g2p: int
    g2p_outputs: int
    g2p_failures: int
    correctly_routed_g2p_outputs: int
    correctly_routed_proposals_with_breaks: int
    correctly_routed_complete_projections: int
    correctly_routed_matches_current_division: int
    correctly_routed_differs_from_current_division: int
    proposals_with_breaks: int
    complete_projections: int
    matches_current_division: int
    differs_from_current_division: int


def held_out_corpora(translate_master: Path) -> dict[str, set[str]]:
    """Recreate the router's test split without exposing train/calibration words."""
    english_words, _ = english.load_english_types(english.DEFAULT_CORPUS)
    chandler_words, _ = english.load_chandler_types(translate_master)
    german_words, _ = german.load_german_types(translate_master)
    french_words, _ = french.load_french_types(translate_master)
    slovak_words = english.load_inventory(english.DEFAULT_INVENTORY)
    partitions, _ = router.split_unique(
        {
            "english": english_words | chandler_words,
            "german": german_words,
            "french": french_words,
            "slovak": slovak_words,
        }
    )
    test = partitions["test"]
    expected = json.loads(PROFILE.read_text(encoding="utf-8"))["training"]["partitions"]["test"]
    observed = {language: len(forms) for language, forms in test.items()}
    if observed != expected:
        raise RuntimeError(f"held-out corpus drift: expected {expected}, observed {observed}")
    return {language: test[language] for language in FOREIGN_LANGUAGES}


def divided(word: str, points: tuple[int, ...]) -> str:
    pieces = []
    start = 0
    for point in points:
        pieces.append(word[start:point])
        start = point
    pieces.append(word[start:])
    return "·".join(pieces)


def _sample(forms: set[str], language: str, size: int) -> set[str]:
    if size == 0 or size >= len(forms):
        return set(forms)
    ranked = sorted(
        forms,
        key=lambda word: hashlib.sha256(
            f"foreign-corpus-benchmark-v1:{language}:{word}".encode()
        ).digest(),
    )
    return set(ranked[:size])


def evaluate(
    corpora: dict[str, set[str]], output: Path, g2p_sample_size: int
) -> dict[str, object]:
    try:
        from slabika_pronunciation import pronounce
    except ImportError as error:
        raise RuntimeError(
            "slabika-pronunciation must be installed to generate division proposals"
        ) from error

    output.mkdir(parents=True, exist_ok=True)
    language_summary = {}
    pronunciation_summary = {}
    fieldnames = (
        "word",
        "expected_language",
        "predicted_language",
        "language_correct",
        "english_score",
        "german_score",
        "french_score",
        "slovak_score",
        "sampled_for_g2p",
        "phones",
        "g2p_score",
        "projected_points",
        "proposed_division",
        "projection_complete",
        "current_slabika_division",
        "error",
    )

    for expected_language, forms in corpora.items():
        sample = _sample(forms, expected_language, g2p_sample_size)
        calls = Counter()
        pronunciation_calls = Counter()
        path = output / f"{expected_language}.tsv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for word in sorted(forms):
                ranking = language_scores(word)
                scores = {result.language: result.score for result in ranking}
                predicted = ranking[0].language if ranking else ""
                calls[predicted] += 1
                row: dict[str, object] = {
                    "word": word,
                    "expected_language": expected_language,
                    "predicted_language": predicted,
                    "language_correct": int(predicted == expected_language),
                    **{
                        f"{language}_score": round(scores.get(language, 0.0), 6)
                        for language in (*FOREIGN_LANGUAGES, "slovak")
                    },
                    "sampled_for_g2p": int(word in sample),
                    "phones": "",
                    "g2p_score": "",
                    "projected_points": "",
                    "proposed_division": "",
                    "projection_complete": "",
                    "current_slabika_division": "",
                    "error": "",
                }
                if word in sample:
                    pronunciation_calls["sampled"] += 1
                    if predicted == expected_language:
                        pronunciation_calls["correctly_routed"] += 1
                    if predicted in FOREIGN_LANGUAGES:
                        try:
                            result = pronounce(word, predicted)
                            points, complete = project_psp_points(result)
                            proposal = divided(word, points)
                            current = hyphenate(word)
                            pronunciation_calls["g2p_outputs"] += 1
                            correctly_routed = predicted == expected_language
                            pronunciation_calls["correctly_routed_g2p_outputs"] += correctly_routed
                            pronunciation_calls["correctly_routed_proposals_with_breaks"] += (
                                correctly_routed and bool(points)
                            )
                            pronunciation_calls["correctly_routed_complete_projections"] += (
                                correctly_routed and complete
                            )
                            pronunciation_calls["correctly_routed_matches_current_division"] += (
                                correctly_routed and proposal == current
                            )
                            pronunciation_calls[
                                "correctly_routed_differs_from_current_division"
                            ] += correctly_routed and proposal != current
                            pronunciation_calls["proposals_with_breaks"] += bool(points)
                            pronunciation_calls["complete_projections"] += complete
                            pronunciation_calls["matches_current_division"] += proposal == current
                            pronunciation_calls["differs_from_current_division"] += proposal != current
                            row.update(
                                phones=result.phones,
                                g2p_score=round(result.score, 6),
                                projected_points=",".join(map(str, points)),
                                proposed_division=proposal,
                                projection_complete=int(complete),
                                current_slabika_division=current,
                            )
                        except Exception as error:  # external model boundary
                            pronunciation_calls["g2p_failures"] += 1
                            row["error"] = f"{type(error).__name__}: {error}"
                    else:
                        pronunciation_calls["not_sent_to_g2p"] += 1
                writer.writerow(row)

        total = len(forms)
        correct = calls[expected_language]
        missed = calls["slovak"]
        unresolved = calls[""]
        routed = sum(calls[language] for language in FOREIGN_LANGUAGES)
        other = routed - correct
        language_summary[expected_language] = {
            **asdict(
                LanguageMetrics(
                    types=total,
                    correct_language=correct,
                    routed_to_foreign_g2p=routed,
                    missed_as_slovak=missed,
                    misrouted_to_other_foreign=other,
                    unresolved=unresolved,
                    language_accuracy=correct / total,
                    foreign_capture_rate=routed / total,
                )
            ),
            "prediction_counts": {
                language or "unresolved": count
                for language, count in sorted(calls.items())
            },
        }
        pronunciation_summary[expected_language] = asdict(
            PronunciationMetrics(
                sampled=pronunciation_calls["sampled"],
                correctly_routed=pronunciation_calls["correctly_routed"],
                not_sent_to_g2p=pronunciation_calls["not_sent_to_g2p"],
                g2p_outputs=pronunciation_calls["g2p_outputs"],
                g2p_failures=pronunciation_calls["g2p_failures"],
                correctly_routed_g2p_outputs=pronunciation_calls[
                    "correctly_routed_g2p_outputs"
                ],
                correctly_routed_proposals_with_breaks=pronunciation_calls[
                    "correctly_routed_proposals_with_breaks"
                ],
                correctly_routed_complete_projections=pronunciation_calls[
                    "correctly_routed_complete_projections"
                ],
                correctly_routed_matches_current_division=pronunciation_calls[
                    "correctly_routed_matches_current_division"
                ],
                correctly_routed_differs_from_current_division=pronunciation_calls[
                    "correctly_routed_differs_from_current_division"
                ],
                proposals_with_breaks=pronunciation_calls["proposals_with_breaks"],
                complete_projections=pronunciation_calls["complete_projections"],
                matches_current_division=pronunciation_calls["matches_current_division"],
                differs_from_current_division=pronunciation_calls[
                    "differs_from_current_division"
                ],
            )
        )

    summary: dict[str, object] = {
        "method": (
            "language routing on all held-out, cross-language-unique word families; "
            "G2P and conservative PSP projection on a deterministic sample"
        ),
        "warning": (
            "Corpus source is a proxy language label. Proposed divisions are candidates, "
            "not correctness scores, because the source corpora contain no gold PSP boundaries."
        ),
        "g2p_sample_size_per_language": g2p_sample_size,
        "language": language_summary,
        "pronunciation": pronunciation_summary,
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--translate-master", type=Path, default=english.DEFAULT_TRANSLATE_MASTER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--g2p-sample-size",
        type=int,
        default=100,
        help="deterministic sample per language; 0 means all held-out words",
    )
    args = parser.parse_args()
    if args.g2p_sample_size < 0:
        parser.error("--g2p-sample-size must be non-negative")
    summary = evaluate(
        held_out_corpora(args.translate_master), args.output, args.g2p_sample_size
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
