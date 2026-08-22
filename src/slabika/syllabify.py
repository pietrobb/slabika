# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Syllabification (slabikovanie) of Slovak words.

A Slovak syllable has exactly one nucleus: a vowel, a diphthong, or a syllabic
consonant (ŕ, ĺ always; r, l when standing between consonants — vlk, prst).

Division follows the phonotactic fallback — a single intervocalic consonant
opens the next syllable, and in a cluster the first consonant closes the
preceding one — except where a morpheme boundary (prefix, derivational suffix,
compound seam) overrides it: pod·ze·mie, roz·de·ľo·va·nie, ze·me·pis·ný.

This layer is purely linguistic. Typographic line-breaking rules are applied on
top of it in :mod:`slabika.typo`.
"""

from .exceptions import LEXICAL_SYLLABIFICATIONS as _LEXICAL_SYLLABIFICATIONS
from .exceptions import LEXICALIZED_STEMS as _LEXICALIZED_STEMS
from .phonology import (
    ALL_VOWELS,
    DIPHTHONGS,
    LONG_VOWELS,
    is_consonant,
    split_into_phonemes,
)


# Slovak productive prefixes — longest first (order matters for matching)
_SK_PREFIXES = [
    # 5+ letter
    'medzi', 'proti', 'predo', 'trans',
    # 4 letter
    'pred', 'bezo', 'nado', 'podo', 'vzo',
    # 3 letter — productive Slovak prefixes
    'naj', 'nad', 'pod', 'pre', 'pri', 'pro', 'roz', 'bez', 'odo', 'pra', 'sú', 'syn',
    # 2 letter
    'do', 'dô', 'na', 'ne', 'ob', 'od', 'po', 'so', 'vo', 'vy', 'vý', 'za', 'zo',
]


def _by_length(forms):
    """Group fixed morpheme forms into (length, set) pairs, longest first.

    A word has exactly one prefix (or suffix) of any given length, so testing
    ``word[:n] in group`` once per distinct length is equivalent to walking the
    whole list with ``startswith`` — provided no shorter form is a prefix of a
    longer one, which would let it match first and shadow the longer form. The
    tables are checked for that; see ``test_no_fixed_form_shadows_a_longer_one``.
    """
    lengths = sorted({len(f) for f in forms}, reverse=True)
    return tuple((n, frozenset(f for f in forms if len(f) == n)) for n in lengths)


_PREFIXES_BY_LEN = _by_length(_SK_PREFIXES)

_LEXICAL_PREFIX_ROOTS = (
    ('porno', ('graf',)),
    ('rozo', ('br', 'ber')),   # rozo·brať, rozo·berať — not roz·ob·rať
    ('o', ('hra', 'hrá')),
)

# Vocalized prefix variants (bezo-, nado-, podo-, predo-) exist only to break up
# an unpronounceable seam before the pronoun stems mn- and vš-: bezo mňa, podo
# mnou, nadovšetko, predovšetkým. Everywhere else the -o- belongs to the root,
# and the consonant-final base prefix is the correct analysis: bez·ohľadný,
# pod·oblasť, nad·oblačný, pred·obraz. Without this restriction the longer
# variant matches first and swallows the root's initial vowel.
_VOCALIZED_ONLY_BEFORE = {
    'bezo': ('mn',),
    'nado': ('vš', 'mn'),
    'podo': ('mn',),
    'predo': ('vš', 'mn'),
}

# Derivational suffixes that start with a consonant — these form a morpheme boundary.
# Only include those that cause mis-syllabification without the boundary.
# Format: suffix string (no dash), longest first.
#
# A vowel-initial suffix (-ota, -oba, -ový, -atý) must never appear here: it
# contributes no consonant to redistribute, so the phonotactic fallback already
# places the stem-final consonant in its onset (oz·do·ba, dob·ro·ta). Listing
# one only strands the stem's final cluster (ozd·o·ba, dob·r·o·ta).
_SK_SUFFIXES_CONS = [
    # 4+ chars (longest first)
    'stvo',   # priateľ·stvo, nábo·žen·stvo
    'nými', 'ných', 'ného', 'nému',
    'nila', 'nilo', 'nili', 'nily',
    # 3 chars
    'ník', 'níc', 'nil',   # dl·žník, účast·nil
    'sko', 'dlo',   # Holand·sko, mera·dlo
    'ský', 'ská', 'ské',   # slo·ven·ský
    'tva',    # pas·tva
    # 2 chars
    'ný', 'ná', 'né',   # ze·me·pis·ný, pís·om·ný
    'ňa',
]

_SUFFIXES_BY_LEN = _by_length(_SK_SUFFIXES_CONS)

# Short grammatical suffixes are boundaries only after consonant-final stems.
# Keep these separate from derivational suffixes to avoid treating every final
# -mi, -me, or -te sequence as morphology.
_SK_GRAMMATICAL_SUFFIXES_CONS = ('mi', 'me', 'te')

# Compositional first-parts that act as hard split boundaries (troj·uholník, viac·hlasný...)
_SK_COMPOSITA = [
    'video', 'šesť', 'zeme', 'vrti',
    'troj', 'viac', 'geo', 'teo', 'bio', 'foto', 'auto', 'euro',
    'agro', 'agri', 'astro', 'aero', 'anti', 'archi', 'arch',
    'hydro', 'termo', 'elektro', 'mikro', 'makro', 'mono', 'poly',
    'pseudo', 'semi', 'kvazi', 'inter', 'intra', 'extra', 'ultra',
    'super', 'hyper', 'meta', 'multi', 'mini', 'maxi',
    # Slovak-specific composita
    'modlo', 'rodo',
    'veľ',   # veľ·kňaz, veľ·kolepý, veľ·mocný
]

# These cited bound forms remain intact when a compositional boundary is made.
_BOUND_COMPOSITA = frozenset({'geo', 'teo', 'video'})

_COMPOSITA_BY_LEN = _by_length(_SK_COMPOSITA)

# Word-initial clusters that license a prefix boundary before a consonant that
# is not followed by a vowel (vz·nik, roz·str·hnúť). Includes the digraph ch.
_VALID_ONSETS = frozenset({
    'bl', 'br', 'ch', 'dr', 'fl', 'fr', 'gl', 'gr', 'kl', 'kr',
    'db', 'hľ', 'hv', 'mk', 'mn', 'pl', 'pr', 'sl', 'sm', 'sn', 'sp', 'sr', 'st',
    'sv', 'sk', 'tr', 'tl', 'vn', 'vr', 'vl', 'vz', 'zb', 'zl',
    'zm', 'zn', 'zr', 'zv', 'šk', 'šp', 'št', 'šť', 'šv', 'žd',
    'pch', 'sch', 'vzd', 'vst', 'str', 'spr', 'skr',
})

# Minimum length of remainder after prefix stripping (must contain a vowel nucleus)
_VOWELS_SK = set('aáäeéiíoóôuúyýrŕlĺ')


def _strip_prefix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Also checks compositional first-parts (_SK_COMPOSITA)."""
    """Return (prefix, remainder) if w starts with a known Slovak prefix
    and remainder is a valid start of a Slovak word (begins with consonant
    or vowel, has ≥3 chars, contains a vowel). Else (None, None).

    Key constraint: remainder must NOT start with a consonant cluster that
    would be invalid as a word start (e.g. 'dp', 'tp') — this catches
    false-positive prefix matches like 'zo' in 'zodpovedajúci'.
    Also: remainder must start with a vowel OR a single consonant followed
    by a vowel-like character (to avoid 'pri' + 'atelstvo' → bad split).
    """
    wl = w.lower()
    if wl.startswith(_LEXICALIZED_STEMS):
        return None, None

    for pfx, roots in _LEXICAL_PREFIX_ROOTS:
        if any(wl.startswith(pfx + root) for root in roots):
            return w[:len(pfx)], w[len(pfx):]

    for length, group in _PREFIXES_BY_LEN:
        pfx = wl[:length]
        if pfx in group:
            rem = w[length:]
            reml = rem.lower()
            if len(rem) < 3:
                continue
            licensed = _VOCALIZED_ONLY_BEFORE.get(pfx)
            if licensed is not None and not reml.startswith(licensed):
                continue
            if not any(c in _VOWELS_SK for c in reml):
                continue
            # Remainder must start with a vowel, or with a consonant followed
            # immediately by a vowel (CV start) — blocks 'dpo', 'tvo'→ok, 'dp'→bad
            if reml[0] in _VOWELS_SK:
                # starts with vowel — only accept if prefix ends with consonant
                # (prevents 'pri' + 'atelstvo' splitting 'priateľstvo')
                if pfx[-1] in _VOWELS_SK and not any(
                    reml.startswith(inner_pfx + root)
                    for inner_pfx, roots in _LEXICAL_PREFIX_ROOTS
                    for root in roots
                ):
                    continue  # vowel+vowel boundary — skip, not a real prefix split
                return w[:length], rem
            else:
                # starts with consonant — next char must be vowel-like (CV)
                if len(reml) >= 2 and reml[1] in _VOWELS_SK:
                    return w[:length], rem
                # or it's a valid onset cluster (incl. digraph ch)
                if reml[:2] in _VALID_ONSETS or reml[:3] in _VALID_ONSETS:
                    return w[:length], rem
                # invalid onset after prefix — not a real prefix boundary
                continue
    return None, None


def _strip_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Return (stem, suffix) if w ends with a known consonant-initial suffix
    and the split produces a valid morpheme boundary. Else (None, None).

    Valid boundary: stem ≥2 chars and contains a vowel. A consonant-initial
    suffix remains a morpheme boundary even when the stem ends in a consonant
    cluster (ohyzd·ný, vlast·ný).
    """
    wl = w.lower()
    for length, group in _SUFFIXES_BY_LEN:
        sfx = wl[-length:]
        if sfx in group and len(w) > length + 2:
            stem = w[:-length]
            steml = stem.lower()
            if not any(c in _VOWELS_SK for c in steml):
                continue
            if sfx == 'sko' and steml[-1] in _VOWELS_SK:
                continue
            return stem, w[-length:]
    return None, None


def _strip_grammatical_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Split -mi, -me, or -te only from a consonant-final stem."""
    wl = w.lower()
    for sfx in _SK_GRAMMATICAL_SUFFIXES_CONS:
        if not wl.endswith(sfx) or len(w) <= len(sfx) + 1:
            continue
        stem = w[:-len(sfx)]
        steml = stem.lower()
        if is_consonant(steml[-1]) and any(c in _VOWELS_SK for c in steml):
            return stem, w[-len(sfx):]
    return None, None


def get_syllables(word: str) -> list[str]:
    """
    Return linguistic syllable units, without typographic line-break filtering.
    Slovak syllabification: each syllable has one vowel nucleus.
    Syllabic consonants: ŕ, ĺ always; r, l only between consonants (vlk, prst).

    Morpheme-aware: known Slovak prefixes and derivational suffixes form hard
    boundaries that override onset maximization
    (e.g. pod·ze·mie, roz·de·ľo·va·nie, ze·me·pis·ný, pas·tva).

    Rule: one consonant between nuclei starts the next syllable. With two or
    more consonants, the first closes the preceding syllable and the rest start
    the next syllable, unless a known morpheme boundary overrides this fallback.
    """
    wl = word.lower()
    lexical_syllables = _LEXICAL_SYLLABIFICATIONS.get(wl)
    if lexical_syllables is not None:
        return list(lexical_syllables)

    # Split superlative naj- before applying the comparative -stejší- boundary.
    if wl.startswith('naj') and 'tejš' in wl[3:]:
        return _syllabify_simple(word[:3]) + get_syllables(word[3:])

    # Comparative -nejš- is a consonant-initial suffix and keeps the adjective
    # stem intact (šťast·nej·ší), overriding the syllabic cluster fallback.
    comparative_n = wl.find('nejš')
    if comparative_n > 0:
        return get_syllables(word[:comparative_n]) + _syllabify_simple(word[comparative_n:])

    # Root-final -st- crosses the syllable boundary before comparative -ejší-.
    comparative_t = wl.find('tejš')
    if comparative_t > 0:
        return get_syllables(word[:comparative_t]) + _syllabify_simple(word[comparative_t:])

    # Prefix-aware split: recursively strip prefixes and syllabify remainder
    pfx, rem = _strip_prefix(word)
    if pfx is not None:
        pfx_syls = _syllabify_simple(pfx)
        rem_syls = get_syllables(rem)  # recursive — handles naj·ne·... stacks
        return pfx_syls + rem_syls

    # Compositional first-part check (troj·uholník, viac·hlasný, ...)
    wl = word.lower()
    for length, group in _COMPOSITA_BY_LEN:
        comp = wl[:length]
        if comp in group and len(word) > length + 2:
            rem = word[length:]
            reml = rem.lower()
            if any(c in _VOWELS_SK for c in reml):
                first_part = word[:length]
                first_syls = [first_part] if comp in _BOUND_COMPOSITA else _syllabify_simple(first_part)
                return first_syls + get_syllables(rem)

    # Grammatical -mi/-me/-te split only after a consonant-final stem.
    stem, sfx = _strip_grammatical_suffix(word)
    if stem is not None:
        return get_syllables(stem) + _syllabify_simple(sfx)

    # Suffix-aware split: strip known consonant-initial derivational suffixes
    stem, sfx = _strip_suffix(word)
    if stem is not None:
        return get_syllables(stem) + _syllabify_simple(sfx)

    return _syllabify_simple(word)


#: Consonants after which a long syllable is never followed by a native Slovak
#: diphthong. The palatals and the consonants that palatalize before i
#: (ť ď ň ľ č š ž c dz j t d n l s) carry the native endings that survive a long
#: stem — vrá·tia, chvá·lia, vtá·čia, hlá·sia — so they are excluded; what is
#: left takes the diphthong only in learned loans, where it is a hiatus.
_HIATUS_TRIGGERS = frozenset({'r', 'z', 'g', 'k', 'h', 'ch'})

_LONG_NUCLEI = LONG_VOWELS | DIPHTHONGS | {'ŕ', 'ĺ'}

#: Everything that can carry a syllable nucleus on its own, without depending on
#: what surrounds it — r and l are decided by context and are not in here.
_NUCLEI = ALL_VOWELS | DIPHTHONGS | {'ŕ', 'ĺ'}

#: Written vowel graphemes, including the ones that are not phonological
#: diphthongs (ô is written as one grapheme, ou is a nucleus only word-finally).
_VOWEL_LIKE = ALL_VOWELS | DIPHTHONGS | {'ô', 'ou'}


def _resolve_hiatus(phonemes: list[str]) -> list[str]:
    """Split a written ia/ie/iu that is two nuclei rather than one diphthong.

    Slovak spelling writes the diphthongs ia, ie, iu exactly like the hiatus of
    a learned loan, and the difference is etymological rather than phonotactic
    (pia·tok but Má·ri·a). Two environments are decidable without a lexicon:

    * ``-ium`` in absolute final position — no native Slovak ending has this
      shape, so the i is always a separate nucleus (akvá·ri·um, štú·di·um);
    * a diphthong standing after a long syllable and one of
      :data:`_HIATUS_TRIGGERS` — the rhythmic law bars a native diphthong there,
      so the word is a loan and the sequence is bisyllabic (Á·zi·a, bio·ló·gi·a).

    Everything else is left alone; a diphthong after a short syllable, or after a
    palatalizing consonant, stays one nucleus.
    """
    out: list[str] = []
    last = len(phonemes) - 1
    for i, ph in enumerate(phonemes):
        if ph in ('ia', 'ie', 'iu'):
            latin_neuter = ph == 'iu' and i == last - 1 and phonemes[last] == 'm'
            preceding = next(
                (p for p in reversed(phonemes[:i]) if p in _NUCLEI),
                None,
            )
            after_long = (
                preceding in _LONG_NUCLEI
                and i > 0
                and phonemes[i - 1] in _HIATUS_TRIGGERS
            )
            if latin_neuter or after_long:
                out.extend([ph[0], ph[1]])
                continue
        out.append(ph)
    return out


def _syllabify_simple(word: str) -> list[str]:
    """Core syllabification without prefix awareness."""
    phonemes = _resolve_hiatus(split_into_phonemes(word))
    # The feminine instrumental ending -ou is one syllabic nucleus, although
    # Slovak phonology does not classify ou among the four diphthongs.
    if len(phonemes) >= 2 and phonemes[-2:] == ['o', 'u']:
        phonemes[-2:] = ['ou']
    n = len(phonemes)

    def is_nucleus(idx: int) -> bool:
        ph = phonemes[idx]
        if ph in _VOWEL_LIKE or ph in ('ŕ', 'ĺ'):
            return True
        if ph in ('r', 'l'):
            prev_ok = idx == 0 or phonemes[idx - 1] not in _VOWEL_LIKE
            next_ok = idx == n - 1 or phonemes[idx + 1] not in _VOWEL_LIKE
            return prev_ok and next_ok
        return False

    # Find positions of all nuclei
    nuclei = [i for i in range(n) if is_nucleus(i)]

    if not nuclei:
        return [word]

    def _best_split(cons_indices: list[int]) -> int:
        """Return the next-syllable start required by PSP chapter V.

        One intervocalic consonant starts the next syllable. With two or more
        consonants, the first closes the preceding syllable and the rest start
        the next one; explicit morpheme boundaries are handled before this
        syllabic fallback.
        """
        if len(cons_indices) == 1:
            return cons_indices[0]
        return cons_indices[1]

    # Build syllable boundaries: each boundary is the index where a new syllable starts
    # Initial consonants before first nucleus belong to first syllable
    boundaries = [0]

    for k in range(len(nuclei) - 1):
        nuc_a = nuclei[k]
        nuc_b = nuclei[k + 1]
        # Consonants between nucleus A and nucleus B: indices nuc_a+1 .. nuc_b-1
        consonants_between = list(range(nuc_a + 1, nuc_b))
        if not consonants_between:
            # Two nuclei adjacent (adjacent vowels — next nucleus starts new syllable)
            boundaries.append(nuc_b)
        else:
            split_at = _best_split(consonants_between)
            boundaries.append(split_at)

    # Build syllables from boundaries; last syllable runs to end of word (includes trailing consonants)
    syllables = []
    for idx, start in enumerate(boundaries):
        end = boundaries[idx + 1] if idx + 1 < len(boundaries) else n
        syl = ''.join(phonemes[start:end])
        if syl:
            syllables.append(syl)

    return syllables if syllables else [word]
