# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: MIT

import hashlib
from importlib.resources import files

import pytest

from slabika_pronunciation import (
    available_languages,
    detect_language,
    model_info,
    pronounce,
    pronounce_auto,
)


@pytest.mark.parametrize("language", ["english", "german", "french"])
def test_bundled_archive_matches_pinned_upstream_hash(language):
    info = model_info(language)
    archive = files("slabika_pronunciation").joinpath("models", info["archive"]).read_bytes()
    assert hashlib.sha256(archive).hexdigest() == info["sha256"]
    assert info["license"] == "CC-BY-4.0"
    assert info["modified"] is False


@pytest.mark.parametrize(("language", "word", "phones"), [
    ("english", "Bradshaw", "bɹædʃɒː"),
    ("german", "Frankenstein", "fʁaŋkʰənʃtajn"),
    ("french", "Molière", "mɔʎɛʁ"),
])
def test_known_pronunciations(language, word, phones):
    result = pronounce(word, language)
    assert result.word == word
    assert result.phones == phones
    assert "".join(spelling for spelling, _ in result.spans) == word.lower()
    assert result.score > 0


def test_unseen_words_are_supported():
    assert pronounce("unknownword", "english").phones == "ɐnownwɚd"
    assert pronounce("unbekannteswort", "german").phones == "ʊnbəkʰantʰəsvɔʁt"
    assert pronounce("inconnue", "french").phones == "ɛ̃kɔny"


def test_isolated_words_are_routed_to_g2p_automatically():
    assert pronounce_auto("Abdrushin").language == "english"
    assert pronounce_auto("Bradshaw").phones == "bɹædʃɒː"
    assert pronounce_auto("unbekannteswort").language == "german"
    assert pronounce_auto("inconnue").language == "french"
    assert pronounce_auto("slovenčina") is None
    ranking = detect_language("Abdrushin")
    assert [result.language for result in ranking] == ["english", "german", "french", "slovak"]


def test_invalid_input_and_language_are_rejected():
    assert available_languages() == ("english", "french", "german")
    with pytest.raises(ValueError):
        pronounce("word", "latin")
    with pytest.raises(ValueError):
        pronounce("two words", "english")
