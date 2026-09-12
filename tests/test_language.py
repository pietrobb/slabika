# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT

import json
from pathlib import Path

from slabika import (
    english_evidence,
    french_evidence,
    german_evidence,
    is_english,
    is_french,
    is_german,
)

ROOT = Path(__file__).resolve().parent.parent
GERMAN_PROFILE = ROOT / "src/slabika/data/german_profile.json"
FRENCH_PROFILE = ROOT / "src/slabika/data/french_profile.json"
ENGLISH_PROFILE = ROOT / "src/slabika/data/english_profile.json"


def test_german_corpus_profile_routes_known_german_forms():
    assert is_german("Teufelsstein")
    assert is_german("Frankensteinov")
    assert german_evidence("Steinovi").stem == "stein"
    assert german_evidence("Steinovi").ending == "ovi"


def test_german_corpus_profile_abstains_on_slovak_and_synthetic_forms():
    assert not is_german("slovenčina")
    assert not is_german("schopný")
    assert not is_german("xxsteinovi")
    assert not is_german("Špicbergoch")


def test_german_detection_is_normalized_and_rejects_non_words():
    assert german_evidence("GRU\u0308NEN") == german_evidence("grünen")
    assert not is_german("Teufels-Stein")
    assert not is_german("de")


def test_distributed_profile_contains_aggregated_weights_not_source_words():
    profile = json.loads(GERMAN_PROFILE.read_text(encoding="utf-8"))
    assert profile["training"]["german_types_total"] == 131_150
    assert len(profile["weights"]) == 59_707
    assert all(isinstance(weight, float) for weight in profile["weights"].values())
    assert "teufelsstein" not in profile["weights"]
    assert profile["test"]["proxy_precision"] > 0.98


def test_french_corpus_profile_routes_known_french_forms():
    assert is_french("français")
    assert is_french("naufragés")
    assert is_french("monsieur")
    assert is_french("cœur")


def test_french_corpus_profile_abstains_on_slovak_forms():
    assert not is_french("slovenčina")
    assert not is_french("tajomný")
    assert not is_french("stroskotanci")
    assert not is_french("vzduch")


def test_french_detection_is_normalized_and_rejects_non_words():
    assert french_evidence("FRANC\u0327AIS") == french_evidence("français")
    assert not is_french("aujourd'hui")
    assert not is_french("de")


def test_distributed_french_profile_contains_only_aggregated_weights():
    profile = json.loads(FRENCH_PROFILE.read_text(encoding="utf-8"))
    assert profile["training"]["french_types_total"] == 35_552
    assert len(profile["weights"]) == 56_370
    assert all(isinstance(weight, float) for weight in profile["weights"].values())
    assert "français" not in profile["weights"]
    assert profile["test"]["proxy_recall"] > 0.68
    assert profile["test"]["proxy_precision"] > 0.98


def test_english_corpus_profile_routes_known_english_forms():
    assert is_english("thought")
    assert is_english("daughter")
    assert is_english("whispered")
    assert is_english("download")
    assert is_english("browser")
    assert is_english("Marlowe")
    assert is_english("playback")
    assert is_english("paperback")
    assert is_english("western")


def test_english_corpus_profile_abstains_on_slovak_forms():
    assert not is_english("slovenčina")
    assert not is_english("tajomný")
    assert not is_english("stroskotanci")
    assert not is_english("vzduch")
    assert not is_english("sused")


def test_english_detection_is_normalized_and_rejects_non_words():
    assert english_evidence("THOUGHT") == english_evidence("thought")
    assert not is_english("sea-wolf")
    assert not is_english("of")


def test_distributed_english_profile_contains_only_aggregated_weights():
    profile = json.loads(ENGLISH_PROFILE.read_text(encoding="utf-8"))
    training = profile["training"]
    assert training["english_types_total"] == 55_638
    assert training["gutenberg_types_total"] == 53_149
    assert training["chandler_types_total"] == 15_136
    assert len(training["sources"]) == 73
    gutenberg_sources = [
        source for source in training["sources"] if source["source_kind"] == "project_gutenberg"
    ]
    chandler_sources = [
        source
        for source in training["sources"]
        if source["source_kind"] == "local_translate_master"
    ]
    source_ids = {source["gutenberg_ebook_id"] for source in gutenberg_sources}
    assert len(gutenberg_sources) == 66
    assert {12_336, 21_970, 31_422, 55_948}.isdisjoint(source_ids)
    assert {source["project"] for source in chandler_sources} == {
        "Chandler Big Sleep",
        "Chandler Farewell My Lovely",
        "Chandler High Window",
        "Chandler Lady in the Lake",
        "Chandler Little Sister",
        "Chandler Long Goodbye",
        "Chandler Playback",
    }
    assert sum(source["paragraphs"] for source in chandler_sources) == 17_733
    assert all("source_text" not in source for source in training["sources"])
    assert len(profile["weights"]) == 69_670
    assert all(isinstance(weight, float) for weight in profile["weights"].values())
    assert "thought" not in profile["weights"]
    assert profile["test"]["proxy_recall"] > 0.57
    assert profile["test"]["proxy_precision"] > 0.98
