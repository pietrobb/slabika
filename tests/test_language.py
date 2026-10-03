# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT

import json
import runpy
import sqlite3
from pathlib import Path

import pytest

from slabika import (
    break_points,
    detect_language,
    divisions,
    english_evidence,
    hyphenate,
    french_evidence,
    german_evidence,
    is_english,
    is_french,
    is_german,
    language_scores,
)

ROOT = Path(__file__).resolve().parent.parent
GERMAN_PROFILE = ROOT / "src/slabika/data/german_profile.json"
FRENCH_PROFILE = ROOT / "src/slabika/data/french_profile.json"
ENGLISH_PROFILE = ROOT / "src/slabika/data/english_profile.json"
ROUTER_PROFILE = ROOT / "src/slabika/data/language_router_profile.json"


def test_shared_router_classifies_isolated_words_without_manual_language_labels():
    expected = {
        "Abdrushin": "english",
        "Bradshaw": "english",
        "unknownword": "english",
        "Teufelsstein": "german",
        "unbekannteswort": "german",
        "Molière": "french",
        "inconnue": "french",
        "slovenčina": "slovak",
        "schopný": "slovak",
    }
    assert {word: detect_language(word) for word in expected} == expected


def test_shared_router_returns_comparable_ranked_scores_and_rejects_non_words():
    ranking = language_scores("Abdrushin")
    assert [result.language for result in ranking] == ["english", "german", "french", "slovak"]
    assert [result.score for result in ranking] == sorted(
        (result.score for result in ranking), reverse=True
    )
    assert language_scores("de") == ()
    assert detect_language("two words") is None


def test_distributed_router_profile_records_blind_family_split_metrics():
    profile = json.loads(ROUTER_PROFILE.read_text(encoding="utf-8"))
    assert profile["languages"] == ["english", "german", "french", "slovak"]
    assert len(profile["weights"]) == 149_280
    assert profile["test"]["macro_accuracy"] > 0.91
    assert min(profile["test"]["accuracy"].values()) > 0.85


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
    assert is_german("Teufels-Stein")
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
    assert is_english("sea-wolf")
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


@pytest.mark.parametrize("word,language", [
    ("Saint-Denis", "french"), ("procès-verbal", "french"),
    ("Teufels-Stein", "german"), ("sea-wolf", "english"),
    ("Côtes-du-Rhône", "french"), ("Saint‐Denis", "french"),
])
def test_hyphenated_language_scores(word, language):
    assert detect_language(word) == language
    assert language_scores(word)


@pytest.mark.parametrize("word", ["-Pierre", "Pierre-", "Saint--Denis", "Saint-123", "Saint Denis"])
def test_invalid_compounds_are_not_routed(word):
    assert detect_language(word) is None
    assert hyphenate(word, language="fr") == word


@pytest.mark.parametrize("language", ["fr", "french"])
def test_explicit_french_bypasses_profile_gate(language):
    assert not is_french("Pierre")
    assert hyphenate("Pierre", language=language) == "Pierre"
    assert break_points("Pierre", language=language) == []
    assert divisions("Pierre", language=language) == []
    assert hyphenate("Denis", language=language) == "De·nis"
    assert hyphenate("Saint-Denis", language=language) == "Saint-·De·nis"
    assert hyphenate("procès-verbal", language=language) == "pro·cès-·ver·bal"
    assert break_points("Saint-Denis", language=language, right_min=4) == [6]


def test_explicit_language_does_not_fall_back_to_another_language():
    assert hyphenate("Pierre", language="sk") == "Pier·re"
    assert hyphenate("slovenčina", language="fr") == "slovenčina"
    with pytest.raises(ValueError, match="language"):
        hyphenate("Pierre", language="spanish")


def test_hyphenated_automatic_route_keeps_member_evidence():
    assert hyphenate("Saint-Denis") == hyphenate("Saint") + "-·" + hyphenate("Denis")
    assert hyphenate("modro-biely").replace("·", "") == "modro-biely"


def test_packaged_languages_route_without_review_database():
    assert hyphenate("Dauphin") == "Dau·phin"
    assert hyphenate("DAUPHIN") == "DAU·PHIN"
    assert break_points("Dauphin") == [3]
    assert divisions("Dauphin") == ["Dau-phin"]
    assert hyphenate("Pierre") == "Pierre"
    assert hyphenate("Dauphin", language="sk") == "Daup·hin"
    assert hyphenate("Pierre", language="sk") == "Pier·re"


def test_reviewed_languages_are_exact_normalized_forms(monkeypatch):
    import slabika.language as language
    from slabika import hyphenate

    monkeypatch.setattr(language, "_word_languages", lambda: {"trémouille": "french"})
    assert language.reviewed_language("TRE\u0301MOUILLE") == "french"
    assert language.reviewed_language("Trémouilleovi") is None
    assert language.reviewed_language("unreviewed") is None
    monkeypatch.setattr(language, "_word_languages", lambda: {})
    assert hyphenate("Pierre") == "Pier·re"


def test_compound_label_takes_priority_over_member_labels(monkeypatch):
    import slabika.language as language
    from slabika import hyphenate

    monkeypatch.setattr(language, "_word_languages", lambda: {
        "pierre": "slovak", "pierre-denis": "french",
    })
    assert hyphenate("Pierre") == "Pier·re"
    assert language.reviewed_language("Pierre‐Denis") == "french"
    assert hyphenate("Pierre-Denis") == "Pierre-·De·nis"
    assert hyphenate("Pierre-Denis", language="sk") == "Pier·re-·De·nis"
    monkeypatch.setattr(language, "_word_languages", lambda: {"pierre": "french"})
    assert hyphenate("Pierre-Denis") == "Pierre-·De·nis"


def test_language_export_rebuilds_only_explicit_live_labels(tmp_path):
    export = runpy.run_path(str(ROOT / "tools/review/export_word_languages.py"))["export_word_languages"]
    database = tmp_path / "review.sqlite"
    output = tmp_path / "word_languages.json"
    with sqlite3.connect(database) as con:
        con.execute("CREATE TABLE decisions (form TEXT, language TEXT, is_deleted INTEGER)")
        con.executemany("INSERT INTO decisions VALUES (?, ?, ?)", [
            ("Pierre", "fr", None), ("PIERRE", "french", 0),
            ("Slovo", "sk", 0), ("deleted", "english", 1),
            ("automatic", None, 0), ("Saint‐Denis", "fr", 0),
        ])
    labels = export(database, output)
    assert labels == {"pierre": "french", "saint-denis": "french", "slovo": "slovak"}
    assert json.loads(output.read_text(encoding="utf-8")) == labels
    first = output.read_bytes()
    assert export(database, output) == labels
    assert output.read_bytes() == first
    with sqlite3.connect(database) as con:
        assert con.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 6
        con.execute("UPDATE decisions SET language = NULL WHERE form IN ('Pierre', 'PIERRE')")
    assert "pierre" not in export(database, output)


@pytest.mark.parametrize("rows", [
    [("Pierre", "french", 0), ("PIERRE", "english", 0)],
    [("Pierre", "spanish", 0)],
])
def test_language_export_rejects_conflicts_and_unknown_languages(tmp_path, rows):
    export = runpy.run_path(str(ROOT / "tools/review/export_word_languages.py"))["export_word_languages"]
    database = tmp_path / "review.sqlite"
    output = tmp_path / "word_languages.json"
    output.write_text("{}\n", encoding="utf-8")
    with sqlite3.connect(database) as con:
        con.execute("CREATE TABLE decisions (form TEXT, language TEXT, is_deleted INTEGER)")
        con.executemany("INSERT INTO decisions VALUES (?, ?, ?)", rows)
    with pytest.raises(ValueError):
        export(database, output)
    assert output.read_text(encoding="utf-8") == "{}\n"


@pytest.mark.parametrize("bonus,margin,expected", [
    (0, 0, "slovak"), (2, 0, None), (5, 0, "french"),
    (5, 3, "french"), (5, 5, None),
])
def test_name_prior_experiment_abstains_on_ties_and_small_margins(bonus, margin, expected):
    from types import SimpleNamespace

    candidate = runpy.run_path(str(ROOT / "tools/review/experiment_name_routing.py"))[
        "candidate_language"
    ]
    ranking = tuple(SimpleNamespace(language=language, score=score) for language, score in [
        ("slovak", 10), ("french", 8), ("english", 4), ("german", 0),
    ])
    assert candidate(ranking, bonus, margin) == expected
    assert candidate((), bonus, margin) is None


def test_name_experiment_is_read_only_and_does_not_claim_calibration(tmp_path):
    experiment = runpy.run_path(str(ROOT / "tools/review/experiment_name_routing.py"))["experiment"]
    inventory = tmp_path / "inventory.sqlite"
    decisions = tmp_path / "decisions.sqlite"
    with sqlite3.connect(inventory) as con:
        con.execute("CREATE TABLE forms (form TEXT)")
        con.executemany("INSERT INTO forms VALUES (?)", [("Pierre",), ("Sused",), ("slovo",)])
    with sqlite3.connect(decisions) as con:
        con.execute("CREATE TABLE decisions (form TEXT, is_proper_name INTEGER, "
                    "language TEXT, is_deleted INTEGER)")
        con.executemany("INSERT INTO decisions VALUES (?, ?, ?, ?)", [
            ("Pierre", 1, "fr", 0), ("Jeanne", 1, None, 0),
            ("Deleted", 1, "en", 1), ("foreign", None, "en", 0), ("Sused", None, "fr", 0),
        ])
    before = (inventory.read_bytes(), decisions.read_bytes())
    result = experiment(inventory, decisions)
    assert (inventory.read_bytes(), decisions.read_bytes()) == before
    assert result["confirmed_labelled_names"] == {"Pierre": "french"}
    assert result["independent_calibration_available"] is False
    assert all(row["form"] not in {"Pierre", "Sused"}
               for row in result["forced_top_language_division_changes"])
    assert len(result["candidates"]) == 16
    for candidate in result["candidates"]:
        groups = candidate["groups"]
        assert groups["confirmed_names"]["size"] == 2
        assert groups["all_capitalized_inventory"]["size"] == 2
        assert groups["lowercase_inventory_titlecased_proxy"]["size"] == 1
        assert sum(candidate["review_label_diagnostic"].values()) == 1
        for group in groups.values():
            assert sum(group["predictions"].values()) == group["size"]
