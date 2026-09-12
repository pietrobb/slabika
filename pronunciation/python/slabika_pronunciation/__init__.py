# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: MIT
"""Optional, model-backed pronunciation for words handled by slabika."""

from __future__ import annotations

import hashlib
import json
import unicodedata
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from io import BytesIO

from slabika import language_scores as _language_scores

from ._native import Model


@dataclass(frozen=True)
class LanguagePrediction:
    language: str
    score: float


@dataclass(frozen=True)
class Pronunciation:
    language: str
    word: str
    phones: str
    score: float
    spans: tuple[tuple[str, tuple[str, ...]], ...]


@lru_cache(maxsize=1)
def _manifest() -> dict[str, dict[str, object]]:
    resource = files(__package__).joinpath("model_manifest.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def available_languages() -> tuple[str, ...]:
    return tuple(sorted(_manifest()))


def model_info(language: str) -> dict[str, object]:
    try:
        return dict(_manifest()[language])
    except KeyError as error:
        raise ValueError(f"unsupported language: {language!r}") from error


def _normalize_word(word: str) -> str:
    normalized = unicodedata.normalize("NFC", word).lower()
    if not normalized or any(not (char.isalpha() or char in "'-") for char in normalized):
        raise ValueError("word must contain letters, apostrophes or hyphens only")
    return normalized


@lru_cache(maxsize=1)
def _model(language: str) -> Model:
    info = model_info(language)
    resource = files(__package__).joinpath("models", str(info["archive"]))
    archive = resource.read_bytes()
    digest = hashlib.sha256(archive).hexdigest()
    if digest != info["sha256"]:
        raise RuntimeError(f"checksum mismatch for {info['archive']}")
    with zipfile.ZipFile(BytesIO(archive)) as source:
        model = source.read(str(info["member"]))
    return Model(model)


def pronounce(word: str, language: str) -> Pronunciation:
    """Return the best model pronunciation and spelling-to-phone spans."""
    if language not in _manifest():
        raise ValueError(f"unsupported language: {language!r}")
    normalized = _normalize_word(word)
    score, phones, spans = _model(language).phonemize(normalized)
    return Pronunciation(
        language=language,
        word=word,
        phones=phones,
        score=score,
        spans=tuple((spelling, tuple(values)) for spelling, values in spans),
    )


def detect_language(word: str) -> tuple[LanguagePrediction, ...]:
    """Rank the supported G2P languages plus Slovak from the isolated word."""
    ranking = _language_scores(_normalize_word(word))
    if not ranking:
        raise ValueError("language cannot be inferred from this word")
    return tuple(LanguagePrediction(result.language, result.score) for result in ranking)


def pronounce_auto(word: str) -> Pronunciation | None:
    """Infer the language from the isolated word and run its G2P model."""
    language = detect_language(word)[0].language
    return None if language == "slovak" else pronounce(word, language)


__all__ = [
    "LanguagePrediction",
    "Pronunciation",
    "available_languages",
    "detect_language",
    "model_info",
    "pronounce",
    "pronounce_auto",
]
