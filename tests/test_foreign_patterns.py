# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""PSP mechanism regressions, not a held-out estimate of linguistic accuracy."""

import hashlib
import unicodedata
from pathlib import Path

import pytest

from slabika import adapt_foreign_word, foreign_hyphenate


@pytest.mark.parametrize(
    "word, expected",
    [
        ("Wasser", "Was·ser"),
        ("Mutter", "Mut·ter"),
        ("Fenster", "Fen·ster"),
        ("Fensterbank", "Fen·ster·bank"),
        ("Katze", "Ka·tze"),
        ("sitzen", "si·tzen"),
        ("Hitze", "Hi·tze"),
        ("sitzende", "si·tzen·de"),
        ("Schwester", "Schwes·ter"),
        ("Kasten", "Kas·ten"),
        ("Entschuldigung", "Ent·schul·di·gung"),
        ("Deutschland", "Deutsch·land"),
        ("Gesundheit", "Ge·sund·heit"),
        ("Krankheit", "Krank·heit"),
        ("Freundschaft", "Freund·schaft"),
        ("Geburtstag", "Ge·burts·tag"),
        ("Krankenhaus", "Kran·ken·haus"),
        ("verstehen", "ver·ste·hen"),
        ("Zucker", "Zu·cker"),
        ("Bücher", "Bü·cher"),
        ("Haus", "Haus"),
        ("entziehen", "ent·zie·hen"),
        ("achtzig", "acht·zig"),
        ("Atzen", "Atzen"),
    ],
)
def test_german(word, expected):
    assert foreign_hyphenate(word, "de") == expected


@pytest.mark.parametrize(
    "word, expected",
    [
        ("bonjour", "bon·jour"),
        ("maison", "mai·son"),
        ("beaucoup", "beau·coup"),
        ("monsieur", "mon·sieur"),
        ("bouteille", "bou·teille"),
        ("montagne", "mon·tagne"),
        ("théâtre", "thé·âtre"),
        ("théâtres", "thé·âtres"),
        ("poésie", "po·é·sie"),
        ("poétique", "po·é·tique"),
        ("création", "cré·a·tion"),
        ("patrie", "pat·rie"),
        ("secret", "sec·ret"),
        ("secrète", "sec·rète"),
        ("afrique", "af·rique"),
        ("table", "table"),
        ("femme", "femme"),
        ("homme", "homme"),
        ("langue", "langue"),
        ("fille", "fille"),
        ("année", "an·née"),
        ("journée", "jour·née"),
        ("oiseau", "oi·seau"),
        ("aujourd’hui", "au·jour·d’hui"),
        ("patience", "pa·tience"),
        ("offrir", "of·frir"),
        ("reprendre", "re·prendre"),
        ("déplacer", "dé·pla·cer"),
        ("ocre", "ocre"),
        ("âpre", "âpre"),
    ],
)
def test_french(word, expected):
    assert foreign_hyphenate(word, "fr") == expected


def test_verified_morphemes_override_local_rules():
    # A t|z compound seam is not the single affricate in Katze.
    assert foreign_hyphenate("Mitzeit", "de", morpheme_points=(3,)) == "Mit·zeit"
    assert foreign_hyphenate("reprendre", "fr", morpheme_points=(2,)) == "re·prendre"
    assert foreign_hyphenate("déplacer", "fr", morpheme_points=(2,)) == "dé·pla·cer"


def test_diagnostics_expose_native_and_changed_points():
    result = adapt_foreign_word("Katze", "german")
    assert result.native_points == (3,)
    assert result.points == (2,)
    assert [(c.before, c.after, c.rule) for c in result.changes] == [
        (3, 2, "de_tz_single_affricate")
    ]
    assert result.render("-") == "Ka-tze"


@pytest.mark.parametrize("word, language", [("BÜCHER", "de"), ("THÉÂTRE", "fr")])
def test_original_unicode_spelling_and_offsets(word, language):
    nfd = unicodedata.normalize("NFD", word)
    output = foreign_hyphenate(nfd, language)
    assert output.replace("·", "") == nfd
    assert unicodedata.normalize("NFC", output) == foreign_hyphenate(word, language)


@pytest.mark.parametrize("word, language", [("", "de"), ("a", "fr"), ("eau", "fr")])
def test_short_words(word, language):
    assert foreign_hyphenate(word, language) == word


@pytest.mark.parametrize(
    "word, language", [("hello", "en"), ("a b", "de"), ("abc1", "fr"), ("İabc", "de")]
)
def test_reject_unsupported_inputs(word, language):
    with pytest.raises(ValueError):
        foreign_hyphenate(word, language)


@pytest.mark.parametrize("point", [0, 8, -1, 2.5, True])
def test_invalid_morpheme_offset(point):
    with pytest.raises(ValueError):
        adapt_foreign_word("théâtre", "fr", morpheme_points=(point,))


def test_verbatim_mit_pattern_resources():
    root = Path(__file__).resolve().parents[1] / "src/slabika/patterns/foreign"
    for filename, sha in {
        "hyph-de-1996.tex": "374ad1ce3263f8a2791ec070ef9b516c532dae64456f3fb656e617e8ae53a9d3",
        "hyph-fr.tex": "526cad6fe8f52fcd3caa3fcaf667cb1740cfc14bca198680e00dc343a84594de",
    }.items():
        path = root / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
        assert "Permission is hereby granted" in path.read_text(encoding="utf-8")
        assert "SPDX-" + "License-Identifier: MIT" in path.with_suffix(".tex.license").read_text()
