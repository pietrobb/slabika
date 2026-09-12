# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT

from dataclasses import replace
from importlib import import_module

import pytest

from slabika import break_points, english_evidence, french_evidence, german_evidence, hyphenate
from slabika.foreign import _inventory, foreign_reading, reading_candidates


@pytest.mark.parametrize(("word", "expected"), [
    ("Frankenstein", "Fran·ken·stein"),
    ("Frankensteinovi", "Fran·ken·stei·no·vi"),
    ("Frankensteinov", "Fran·ken·stei·nov"),
    ("Stein", "Stein"),
    ("Steinovi", "Stei·no·vi"),
    ("Teufelsstein", "Teu·fels·stein"),
    ("Bernhardsberg", "Bern·hards·berg"),
    ("Schloßbergu", "Schloß·ber·gu"),
    ("Schlossbergu", "Schloss·ber·gu"),
    ("Heidelberg", "Hei·del·berg"),
    ("Sternwood", "Stern·wood"),
    ("Sternwoodovi", "Stern·woo·do·vi"),
    ("Sternwoodovcov", "Stern·woo·dov·cov"),
    ("hollywoodskými", "hol·ly·wood·ský·mi"),
    ("hollywoodskych", "hol·ly·wood·skych"),
    ("Beaurevoiru", "Beau·re·voi·ru"),
    ("Beauvais", "Beau·vais"),
    ("Beaupère", "Beau·père"),
    ("Molièrovi", "Mo·liè·ro·vi"),
    ("Marloweovi", "Mar·lowe·o·vi"),
    ("STERNWOODOVI", "STERN·WOO·DO·VI"),
])
def test_profile_routes_reading_through_slovak_psp(word, expected):
    # PSP V: preserve single-nucleus groups; resyllabify vowel-initial Slovak
    # inflections; keep consonant-initial suffixes and transparent compounds apart.
    assert foreign_reading(word) is not None
    assert hyphenate(word) == expected
    assert hyphenate(word, separator="-") == expected.replace("·", "-")


def test_inflection_evidence_explains_the_scored_base_or_member():
    for word, scorer, base, ending, unit in [
        ("Sternwoodovi", english_evidence, "sternwood", "ovi", "wood"),
        ("Marloweovi", english_evidence, "marlowe", "ovi", "marlowe"),
        ("Molièrovi", french_evidence, "molièr", "ovi", "molièr"),
        ("Frankensteinovi", german_evidence, "frankenstein", "ovi", "frankenstein"),
    ]:
        evidence = scorer(word)
        assert (evidence.stem, evidence.ending, evidence.scored_unit) == (base, ending, unit)


@pytest.mark.parametrize("word", [
    "slovenčina", "schopný", "sused", "tajomný", "dôverovali", "xxsteinovi",
    "Unknownwoodovi", "Špicbergoch", "people", "français", "Bourlemontu",
    "Sternwood-ovi", "Molie\u0300rovi", "İsteinovi", "", "42", "Young", "Youngovi", "Youngom",
])
def test_unknown_or_unsupported_readings_do_not_acquire_guessed_points(word):
    assert foreign_reading(word) is None


def test_bare_known_spelling_is_not_mistaken_for_a_slovak_inflection():
    assert [(r.stem, r.ending) for r in reading_candidates("molière")] == [("molière", "")]
    assert [(r.stem, r.ending) for r in reading_candidates("molièrovi")] == [("molièr", "ovi")]


def clear_evidence_caches():
    current = import_module("slabika.language")  # The blind audit reloads the package.
    for fn in (english_evidence, french_evidence, german_evidence, foreign_reading,
               current.english_evidence, current.french_evidence, current.german_evidence):
        fn.cache_clear()
    return current


def test_reading_membership_never_bypasses_corpus_gate(monkeypatch):
    language = clear_evidence_caches()
    with monkeypatch.context() as patch:
        patch.setattr(language, "_unit_evidence", lambda *args: (-100.0, 0, 0.0))
        for word in ("Sternwoodovi", "Frankensteinovi", "Molièrovi"):
            assert foreign_reading(word) is None
    clear_evidence_caches()


def test_competing_profiles_abstain_instead_of_comparing_uncalibrated_scores(monkeypatch):
    language = clear_evidence_caches()
    german = german_evidence("Sternwoodovi")
    with monkeypatch.context() as patch:
        patch.setattr(language, "german_evidence", lambda word: replace(german, is_german=True))
        assert foreign_reading("Sternwoodovi") is None
    clear_evidence_caches()


def test_reading_inventory_and_all_inflections_preserve_spelling_offsets():
    stems, endings = _inventory()
    routed = 0
    for stem, (_, parts, inflect) in stems.items():
        assert all(len(symbol) == 1 for part in parts for _, symbol in part)
        for ending in ("", *sorted(endings)) if inflect else ("",):
            word = stem + ending
            reading = foreign_reading(word)
            if reading is None:
                continue
            routed += 1
            protected = set()
            offset = 0
            for part in reading.parts:
                for spelling, _ in part:
                    protected.update(range(offset + 1, offset + len(spelling)))
                    offset += len(spelling)
            for all_points, contextual in ((False, False), (True, False), (False, True), (True, True)):
                points = break_points(word, all_points, contextual)
                assert points == sorted(set(points))
                assert not protected.intersection(points), (word, points, protected)
                assert all(0 < p < len(word) - 1 for p in points), (word, points)
                assert hyphenate(word, all_points=all_points, contextual=contextual).replace(
                    "·", ""
                ) == word
    assert routed > 1000
