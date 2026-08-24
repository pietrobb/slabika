# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Liangov pattern matcher nad TeX súbormi hyph-*.tex.

Nezávislý poradný hlas: patterny vytvorili ľudia (Chlebíková 1992 pre sk),
nevedia nič o našom engine ani o revíznych rozhodnutiach. Slúžia len ako
tretí hlas v zmierovaní, nie ako autorita — autoritou sú PSP.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_PATTERN_LINE = re.compile(r"^[^%]*")


def load_tex(path: str | Path) -> tuple[dict[str, str], dict[str, list[int]]]:
    """Vráti (patterns, exceptions) z hyph-*.tex."""
    text = Path(path).read_text(encoding="utf-8")
    patterns: dict[str, str] = {}
    exceptions: dict[str, list[int]] = {}

    section = None
    for raw in text.splitlines():
        line = _PATTERN_LINE.match(raw).group(0).strip()
        if not line:
            continue
        if line.startswith("\\patterns"):
            section = "patterns"
            line = line.split("{", 1)[-1]
        elif line.startswith("\\hyphenation"):
            section = "exceptions"
            line = line.split("{", 1)[-1]
        if section is None:
            continue
        closing = "}" in line
        line = line.replace("}", " ").replace("{", " ")
        for token in line.split():
            if section == "patterns":
                key = re.sub(r"\d", "", token)
                if key:
                    patterns[key] = token
            else:
                word = token.replace("-", "")
                exceptions[word] = [
                    i for i, ch in enumerate(token) if ch == "-"
                ] and _exception_points(token)
        if closing:
            section = None
    return patterns, exceptions


def _exception_points(token: str) -> list[int]:
    points: list[int] = []
    plain_index = 0
    for ch in token:
        if ch == "-":
            points.append(plain_index)
        else:
            plain_index += 1
    return points


def break_points(
    word: str,
    patterns: dict[str, str],
    exceptions: dict[str, list[int]] | None = None,
    left_min: int = 2,
    right_min: int = 3,
) -> list[int]:
    """Vráti pozície (index znaku, pred ktorý patrí deliaci bod)."""
    lower = word.lower()
    if exceptions and lower in exceptions:
        return [p for p in exceptions[lower] if left_min <= p <= len(word) - right_min]

    padded = "." + lower + "."
    values = [0] * (len(padded) + 1)

    for i in range(len(padded)):
        for j in range(i + 1, len(padded) + 1):
            frag = padded[i:j]
            pattern = patterns.get(frag)
            if pattern is None:
                continue
            offset = 0
            for k, ch in enumerate(pattern):
                if ch.isdigit():
                    slot = i + k - offset
                    values[slot] = max(values[slot], int(ch))
                    offset += 1

    points = []
    for pos in range(1, len(word)):
        # values index: padded[0]='.', takže pozícia pred word[pos] je values[pos+1]
        if values[pos + 1] % 2 == 1:
            points.append(pos)
    return [p for p in points if left_min <= p <= len(word) - right_min]


def hyphenate(
    word: str,
    patterns: dict[str, str],
    exceptions: dict[str, list[int]] | None = None,
    marker: str = "\u00b7",
    left_min: int = 2,
    right_min: int = 3,
) -> str:
    points = break_points(word, patterns, exceptions, left_min, right_min)
    out = []
    for i, ch in enumerate(word):
        if i in points:
            out.append(marker)
        out.append(ch)
    return "".join(out)


_CACHE: dict[str, tuple[dict[str, str], dict[str, list[int]]]] = {}


def for_language(lang: str = "sk"):
    if lang not in _CACHE:
        root = Path(__file__).resolve().parents[2]
        _CACHE[lang] = load_tex(root / "tex" / f"hyph-{lang}.tex")
    return _CACHE[lang]


def tex_hyphenate(word: str, lang: str = "sk", marker: str = "\u00b7") -> str:
    patterns, exceptions = for_language(lang)
    right_min = 3 if lang == "sk" else 3
    return hyphenate(word, patterns, exceptions, marker, 2, right_min)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for w in sys.argv[1:]:
        print(w, tex_hyphenate(w))
