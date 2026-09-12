# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""English alignment repairs and corpus-supported morphology, not gold decisions."""

VOWELS = frozenset("aeiouy")
IPA_VOWELS = frozenset("aeiouyæɑɒɐəɛɜɞɪɔœɘɵɤøɨʉɯɚɝʌʊɶ")
WRITTEN_VOWELS = frozenset("aeiouyàâäæéèêëîïôöœùûüÿ")
CONSONANTS = {
    "b": {"b", "bʲ"}, "d": {"d", "dʲ"}, "f": {"f", "fʲ"},
    "g": {"ɡ", "ɟ", "ɟʷ"}, "k": {"k", "kʰ", "c", "cʰ"},
    "l": {"l", "ɫ", "ʎ"}, "m": {"m", "mʲ"}, "n": {"n", "ɲ"},
    "p": {"p", "pʰ", "pʲ"}, "r": {"ɹ"}, "s": {"s", "z"},
    "t": {"t", "tʰ", "tʲ"}, "v": {"v", "vʲ"}, "z": {"z"},
}
VERSION = "english-alignment-morphology-2"
# Initial, independently interpreted morphemes from the English review audit.
# Corpus membership alone is NOT permission to split arbitrary concatenations.
COMPOUND_HEADS = frozenset({"knife", "knives", "house", "houses"})
LY_BASES = frozenset({"modest", "immodest"})


def is_vowel(phone):
    return any(c in IPA_VOWELS for c in phone) or "\u0329" in phone


def normalize_alignment(pronunciation):
    """Repair only locally evidenced shifts; keep raw stored model evidence intact."""
    spans = [(s, tuple(p)) for s, p in pronunciation.spans]
    if pronunciation.language != "english":
        return tuple(spans)
    for i in range(1, len(spans) - 1):
        before, bp = spans[i - 1]
        spelling, phones = spans[i]
        after, ap = spans[i + 1]
        # E.g. pe/p + g/ɛ + gy/ɟ,i -> pe/p,ɛ + ggy/ɟ,i.
        if (len(spelling) == 1 and spelling in CONSONANTS
                and len(phones) == 1 and is_vowel(phones[0])
                and before and before[-1] in VOWELS and bp
                and not any(map(is_vowel, bp)) and after.startswith(spelling)
                and ap and ap[0] in CONSONANTS[spelling]):
            spans[i - 1] = (before, bp + phones)
            spans[i] = ("", ())
            spans[i + 1] = (spelling + after, ap)
        # The eo spelling of /i:/ must not be split by an op/p alignment.
        elif (before.endswith("e") and bp and bp[-1] in {"i", "iː"}
              and len(spelling) == 2 and spelling[0] == "o"
              and len(phones) == 1 and phones[0] in CONSONANTS.get(spelling[1], ())):
            spans[i - 1] = (before + "o", bp)
            spans[i] = (spelling[1:], phones)
    result = []
    for spelling, phones in spans:
        if not spelling and not phones:
            continue
        if (len(spelling) > 2 and spelling[0] == spelling[1]
                and spelling[2] in VOWELS and len(phones) >= 2
                and phones[0] in CONSONANTS.get(spelling[0], ())
                and is_vowel(phones[1])):
            result.extend(((spelling[:2], phones[:1]), (spelling[2:], phones[1:])))
        else:
            result.append((spelling, phones))
    return tuple(result)


def alignment_complete(spans):
    return all(not any(map(is_vowel, p)) or bool(set(s) & VOWELS) for s, p in spans)


def doubled_points(pronunciation, spans, points, complete):
    if pronunciation.language != "english":
        return points, complete
    result = set(points)
    offset = 0
    for i, (spelling, phones) in enumerate(spans):
        if (len(spelling) == 2 and spelling[0] == spelling[1]
                and len(phones) == 1 and phones[0] in CONSONANTS.get(spelling[0], ())
                and 0 < i < len(spans) - 1 and spans[i - 1][1] and spans[i + 1][1]
                and is_vowel(spans[i - 1][1][-1]) and is_vowel(spans[i + 1][1][0])
                and spans[i + 1][0] and spans[i + 1][0][0] in VOWELS
                and 1 < offset + 1 < len(pronunciation.word) - 1):
            result.discard(offset)
            result.add(offset + 1)
        offset += len(spelling)
    return tuple(sorted(result)), complete


def _phone_boundary_offset(spans, span_offsets, left, right):
    left_span, _ = left
    right_span, right_phone = right
    if left_span != right_span:
        return span_offsets[right_span]
    spelling, phones = spans[right_span]
    if len(spelling) != len(phones):
        return None
    return span_offsets[right_span] + right_phone


def project_psp_points(pronunciation):
    """Conservatively project pronunciation nuclei to written PSP-style points."""
    spans = normalize_alignment(pronunciation)
    span_offsets = []
    offset = 0
    phones = []
    for span_index, (spelling, values) in enumerate(spans):
        span_offsets.append(offset)
        offset += len(spelling)
        phones.extend((phone, span_index, index) for index, phone in enumerate(values))

    nuclei = []
    for index, (phone, span_index, _) in enumerate(phones):
        spelling = spans[span_index][0]
        if not is_vowel(phone) or not (set(spelling) & WRITTEN_VOWELS):
            continue
        if nuclei and phones[nuclei[-1]][1] == span_index:
            continue
        nuclei.append(index)

    points = set()
    complete = pronunciation.language != "english" or alignment_complete(spans)
    for previous, following in zip(nuclei, nuclei[1:]):
        between = list(range(previous + 1, following))
        boundary = following if not between else between[0]
        if len(between) >= 2:
            boundary = between[0] + 1
        point = _phone_boundary_offset(
            spans,
            span_offsets,
            (phones[boundary - 1][1], phones[boundary - 1][2]),
            (phones[boundary][1], phones[boundary][2]),
        )
        if point is None:
            complete = False
        elif 1 < point < len(pronunciation.word) - 1:
            points.add(point)
    return doubled_points(pronunciation, spans, tuple(sorted(points)), complete)


def _phones(pronunciation):
    return tuple(p for _, ps in pronunciation.spans for p in ps)


class EnglishMorphology:
    """Conservative experimental seams, with no access to human decisions.

    Compounds need a recognized head plus two corpus constituents and compatible
    phones. -ly needs an audited adjective base or independent -ness family
    evidence, also pronunciation-matched. This is not a complete English parser.
    """

    def __init__(self, pronunciations):
        self.lexicon = {p.word: _phones(p) for p in pronunciations}

    def seams(self, pronunciation):
        word, phones = pronunciation.word, _phones(pronunciation)
        seams = []
        for head in COMPOUND_HEADS:
            if not word.endswith(head):
                continue
            left = word[:-len(head)]
            if left not in self.lexicon or head not in self.lexicon:
                continue
            lp, rp = self.lexicon[left], self.lexicon[head]
            if not any(map(is_vowel, lp)) or not any(map(is_vowel, rp)):
                continue
            joined = lp + rp
            coalesced = lp + rp[1:] if lp[-1] == rp[0] else joined
            if phones in (joined, coalesced):
                seams.append(len(left))
        if word.endswith("ly") and word[:-2] in self.lexicon:
            stem = word[:-2]
            base = self.lexicon[stem]
            ness = self.lexicon.get(stem + "ness", ())
            supported = stem in LY_BASES or ness in (base + ("n", "ə", "s"),
                                                    base + ("n", "ɪ", "s"))
            if (supported and phones[:len(base)] == base and len(phones) == len(base) + 2
                    and phones[-2] in {"l", "ɫ", "ʎ"} and phones[-1] in {"i", "iː"}):
                seams.append(len(stem))
        return tuple(sorted(set(seams)))

    def refine(self, pronunciation, points):
        spans = normalize_alignment(pronunciation)
        nuclei, protected = [], set()
        offset = 0
        for spelling, phones in spans:
            letters = [offset + i for i, c in enumerate(spelling) if c in VOWELS]
            if letters and any(map(is_vowel, phones)):
                nuclei.append((min(letters), max(letters) + 1))
            if len(phones) == 1:
                protected.update(range(offset + 1, offset + len(spelling)))
            offset += len(spelling)
        points = set(points)
        for (_, end), (start, _) in zip(nuclei, nuclei[1:]):
            seams = [c for c in self.seams(pronunciation)
                     if end <= c <= start and 1 < c < len(pronunciation.word) - 1
                     and c not in protected]
            if len(seams) == 1:
                points = {p for p in points if not end <= p <= start}
                points.add(seams[0])
        return tuple(sorted(points))
