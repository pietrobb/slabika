# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Syllabification (slabikovanie) of Slovak words.

A Slovak syllable has exactly one nucleus: a vowel, a diphthong, or a syllabic
consonant (ŕ, ĺ always; r, l when standing between consonants — vlk, prst).

The boundary falls where sonority stops falling and starts rising again. A
syllable takes as its onset every consonant that still rises towards the
nucleus and can open a Slovak word — A·bra·ham, o·kno, do·bre — and closes on
whatever is left, which is why ses·tra and mat·ka divide where they do: st and
tk do not rise, so they cannot both belong to the onset.

A morpheme boundary (prefix, derivational suffix, compound seam) overrides the
phonotactics: pod·ze·mie, roz·de·ľo·va·nie, ze·me·pis·ný.

This module produces the linguistic syllable analysis. :mod:`slabika.typo`
shares its phoneme layout and morpheme analysis, but independently applies the
PSP rules for written-word division; it does not derive its break points from
the syllable boundaries returned here.
"""

from .phonology import (
    ALL_VOWELS,
    DIPHTHONGS,
    LONG_VOWELS,
    ANALYSABLE_LETTERS,
    ONSET_CLUSTERS,
    PRONOUNCED_FOREIGN_VOWELS,
    SONORY,
    is_consonant,
    native_spelling,
    split_into_phonemes,
)


# Slovak productive prefixes — longest first (order matters for matching)
_SK_PREFIXES = [
    # 5+ letter
    'medzi', 'proti', 'predo', 'trans',
    # 4 letter
    'pred', 'bezo', 'nado', 'podo', 'vzo', 'arci',
    # 3 letter — productive Slovak prefixes
    'naj', 'nad', 'pod', 'pre', 'pri', 'pro', 'roz', 'bez', 'odo', 'pra', 'sú', 'syn',
    # zne- is the prefix that makes a verb out of an adjective or a noun
    # (zne·hodnotiť, zne·možniť, zne·užiť). It is listed in its own right and not
    # as z + ne-, because the negative ne- is not what is in these words.
    'zne',
    # 2 letter
    'do', 'dô', 'na', 'ne', 'ob', 'od', 'po', 'so', 'vo', 'vy', 'vý', 'za', 'zo',
]

# Foreign prefixes are recognised only when their written boundary is familiar
# enough to be useful in Slovak text. This is morphology, not a language profile.
_FOREIGN_PREFIXES = ['auf']
_PREFIXES = [*_SK_PREFIXES, *_FOREIGN_PREFIXES]


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


_PREFIXES_BY_LEN = _by_length(_PREFIXES)

_LEXICAL_PREFIX_ROOTS = (
    ('porno', ('graf',)),
    ('rozo', ('br', 'ber')),   # rozo·brať, rozo·berať — not roz·ob·rať
    ('o', ('hra', 'hrá')),
    ('in', ('štruk',)),
    ('šéf', ('lekár',)),
    ('pa', ('kľúč',)),
    ('para', ('fráz', 'graf')),
    # po·drobiť (rozdrobiť) against pod·robiť (podmaniť) — the two are spelled
    # alike and only the sense tells them apart. PSP prints po-drobný, and the
    # adjective and its adverbs are the frequent reading of the string.
    ('po', ('drob', 'druh')),
    ('u', ('krát',)),
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
    'predo': ('vš', 'mn', 'str'),   # predovšetkým, predo mnou, predo·strieť
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
    'stiev',  # spoločen·stiev — the genitive plural of ·stvo
    'ština',  # francúz·ština
    'ných', 'ného', 'nému',
    # 3 chars
    'stv',    # priateľ·stvo, kráľov·stvá
    'ctv',    # baní·ctvo, zdravotní·ctvo
    'cia',    # funk·cia, ak·cia, polí·cia — the borrowed -tio suffix
    'ník', 'níc', 'nil', 'kár',   # dl·žník, robot·ní·ci, účast·nil, tajnost·kár
    'ným', 'nej', 'nou', 'nom',   # ohrad·ným — the rest of the ·ný paradigm
    'dlo',    # mera·dlo
    # No 'tva'. It is not a suffix — pas·tva is section 4.3 doing its job,
    # because tv- opens tvoj and the point never has to move. Listed here it
    # outranked the real suffix in ·stva (mužs|tva for muž|stva) and overrode
    # 4.2 in words where tv is the whole cluster (bri|tva for brit|va).
    # 2 chars
    'sk',     # slo·ven·ský, Benát·ska, Holand·sko
    'ný', 'ná', 'né', 'nú', 'ní',   # ze·me·pis·ný, pís·om·ný, mast·nú, počest·ní
    'ňa',
]

_SUFFIXES_BY_LEN = _by_length(_SK_SUFFIXES_CONS)

_DLO_INFLECTIONS = ('dlami', 'dlách', 'dlom', 'dlám', 'diel', 'dla', 'dle', 'dlu', 'dlá')
_DLO_PARADIGM_STEMS = frozenset({'páči'})

# Short grammatical suffixes are boundaries only after consonant-final stems.
# Keep these separate from derivational suffixes to avoid treating every final
# -mi, -me, or -te sequence as morphology.
_SK_GRAMMATICAL_SUFFIXES_CONS = ('mi', 'me', 'te', 'ne')

# The nominal suffix ·k· cannot be listed above, because the vowel that follows
# it belongs to the ending, not to the suffix: klient·ka, klient·ky, klient·kou.
# It is therefore matched as the single letter k plus one of the endings of the
# paradigms it derives — the žena/ulica type, the mesto type, ·kyňa and ·kový.
_SK_K_SUFFIX_ENDINGS = frozenset({
    'a', 'y', 'e', 'u', 'ou', 'ám', 'ách', 'ami', 'am',        # klient·ka
    'o', 'i', 'om', 'ov', 'och', 'ovi', 'ovia',                # Robert·ko, líst·kov
    'yňa', 'yne', 'yňu',                                       # vešt·kyňa
    'ová', 'ové', 'ový', 'ovú', 'ovej', 'ovom', 'ovým',        # poist·ková
})

# Compositional first-parts that act as hard split boundaries (troj·uholník, viac·hlasný...)
_SK_COMPOSITA = [
    'deväťdesiat', 'osemdesiat', 'sedemdesiat', 'šesťdesiat', 'päťdesiat',
    'štyridsať', 'tridsať', 'dvadsať',
    'devätnásť', 'osemnásť', 'sedemnásť', 'šestnásť', 'pätnásť',
    'štrnásť', 'trinásť', 'dvanásť', 'jedenásť',
    'video', 'deväť', 'sedem', 'osem', 'šesť', 'šest', 'päť', 'zeme', 'vrti',
    'troj', 'tri', 'dve', 'štyri', 'sto', 'viac', 'geo', 'teo', 'bio', 'foto', 'auto', 'euro',
    'agro', 'agri', 'astro', 'aero', 'anti', 'archi', 'arch',
    'hydro', 'termo', 'elektro', 'mikro', 'makro', 'mono', 'neuro', 'poly',
    'pseudo', 'semi', 'kvazi', 'inter', 'intra', 'extra', 'ultra',
    'super', 'hyper', 'meta', 'multi', 'mini', 'maxi',
    # Slovak-specific composita
    'modlo', 'rodo', 'jedno', 'stredo', 'brati', 'mäso', 'mast', 'krátko', 'krato',
    'veľ',   # veľ·kňaz, veľ·kolepý, veľ·mocný
    'seba',  # seba·vedomie, seba·kritika, seba·určenie
    # First parts that are only recognisable in front of a vowel — see
    # _VOWEL_SEAM_COMPOSITA.
    'bystro', 'dlho', 'hore', 'mnoho', 'mravo', 'novo', 'no', 'polo', 'viero',
    'vše', 'vysoko',
]

_CARDINAL_UNITS = ('jeden', 'dva', 'tri', 'štyri', 'päť', 'šesť', 'sedem', 'osem', 'deväť')
_CARDINAL_TEENS = (
    'desať', 'jedenásť', 'dvanásť', 'trinásť', 'štrnásť',
    'pätnásť', 'šestnásť', 'sedemnásť', 'osemnásť', 'devätnásť',
)
_CARDINAL_TENS = (
    'dvadsať', 'tridsať', 'štyridsať', 'päťdesiat',
    'šesťdesiat', 'sedemdesiat', 'osemdesiat', 'deväťdesiat',
)
_HUNDRED_MULTIPLIERS = ('dve', 'tri', 'štyri', 'päť', 'sedem', 'osem', 'deväť')

# A compositional first part ending in the linking vowel of section 3.4 is not
# always one: hore·kovanie is no compound of hore, and vše·tkého no compound of
# vše. In front of a vowel it always is (hore·uvedený, vše·obecný,
# viero·uka) — and that is also the only environment where the seam decides
# anything, because it is what tells viero|uka from vie·rou·ka.
_VOWEL_SEAM_COMPOSITA = frozenset({
    'bystro', 'dlho', 'hore', 'mnoho', 'mravo', 'novo', 'polo', 'viero',
    'vše', 'vysoko',
})

# Compositional second-parts. A multiplicative numeral is a compound of the
# counting word and krát (dva·krát, koľko·krát, desať·sto·krát), so section 3.4
# puts the break at that seam and not where the consonant count would fall
# (dvak·rát). The seam is found before any prefix or first-part is stripped:
# without that, ob· and veľ· match first and swallow the numeral's own vowel.
_SK_COMPOUND_TAILS = ('krát',)

# Bound compositional second members. Section 3.4 divides a compound at its
# seam and 3.5 makes recognisability the test, not etymology: a Slovak reader
# sees the seam in demo|krat because the same member alternates in front of him
# — demokrat/demokracia, aristokrat/aristokracia, byrokrat/byrokracia. The -o-
# before it is the linking vowel of 3.4 and stays with the first part. The
# member is bound, so it is searched inside the form and not at its end
# (aristokratickými), and it needs a first part of its own: the s- of Sokrates
# is not one, and neither is the word-initial krat- of kratochvíľa.
_SK_BOUND_SECOND_MEMBERS = ('krat', 'krac', 'hned', 'naut')
_LINKING_VOWEL = 'o'

# These cited bound forms remain intact when a compositional boundary is made.
_BOUND_COMPOSITA = frozenset({'geo', 'teo', 'video'})

_COMPOSITA_BY_LEN = _by_length(_SK_COMPOSITA)

# Word-initial clusters that license a prefix boundary before a consonant that
# is not followed by a vowel (vz·nik, roz·str·hnúť). Includes the digraph ch.
# A cluster is listed because a Slovak word is written with it: vžd- is here
# because vždy is one, which is what makes na·vždy a prefix seam and not the
# consonant count of section 4.3 (nav·ždy).
_VALID_ONSETS = frozenset({
    'bl', 'br', 'bz', 'ch', 'dr', 'fl', 'fr', 'gl', 'gr', 'kl', 'kr',
    'db', 'hľ', 'hv', 'mk', 'mn', 'pl', 'pr', 'sl', 'sm', 'sn', 'sp', 'sr', 'st',
    'sv', 'sk', 'tr', 'tl', 'vn', 'vr', 'vl', 'vz', 'zb', 'zl',
    'zm', 'zn', 'zr', 'zv', 'šk', 'šp', 'št', 'šť', 'šv', 'žd',
    'pch', 'sch', 'vzd', 'vst', 'str', 'spr', 'skr', 'vžd',
})

# What is written as a vowel: the vowel graphemes, plus the diphthongs that are
# written as a single letter (ô). Derived from the inventory rather than spelled
# out, so that adding a grapheme to data/phonology.json is enough to teach the
# whole package about it.
_VOWEL_LETTERS = (
    ALL_VOWELS | PRONOUNCED_FOREIGN_VOWELS
    | {d for d in DIPHTHONGS if len(d) == 1}
)

# What can be a nucleus at all — the above plus the syllabic consonants, used to
# check that a remainder is pronounceable. A root beginning with r- or l- still
# begins with a consonant however syllabic that consonant may become, which is
# why the two sets are distinct: testing prefixes against this one cost
# ne·roz·lú·čiť its prefix.
_VOWELS_SK = _VOWEL_LETTERS | SONORY

# No Slovak morpheme begins with these graphemes, so a prefix candidate that
# leaves one of them at the head of the remainder has not found a seam but a
# spelling accident: ob·ývať cut the b off bývať because ý looked like a root.
# ô is deliberately absent — ôsmy exists.
_NEVER_INITIAL = set('äýĺŕ')

#: The vowel sequences that are written as two letters and read as one nucleus.
#: Slovak phonology counts four diphthongs and none of these is among them, but
#: word division is about the written syllable, and PSP §4.4 asks for the
#: decision to be made before a point is placed between the letters: the pair is
#: one nucleus wherever no morpheme seam runs through it (pau·za, pneu·ma·ti·ka,
#: ru·kou) and two where one does (po|učiť, zne|užiť).
_FALLING_DIPHTHONGS = frozenset({'au', 'eu', 'ou'})


def _starts_like_a_word(rem: str) -> bool:
    """True when *rem* opens with a cluster some Slovak word opens with.

    A compound seam is only a seam if what follows it could stand alone: agri·
    matches the opening of Agrippa, but no word begins pp-, so the boundary is
    the table's accident and not the word's.
    """
    onset = []
    for phoneme in split_into_phonemes(rem):
        if any(char in _VOWELS_SK for char in phoneme):
            break
        onset.append(phoneme)
    if len(onset) < 2:
        return True
    return ''.join(onset) in ONSET_CLUSTERS or ''.join(onset) in _VALID_ONSETS


def _licenses_compositum(comp: str, rem: str) -> bool:
    reml = rem.lower()
    if comp in _VOWEL_SEAM_COMPOSITA and reml[0] not in _VOWEL_LETTERS:
        return False
    if comp == 'mäso' and not reml.startswith('žrav'):
        return False
    if comp in _HUNDRED_MULTIPLIERS and not reml.startswith('sto'):
        return False
    if comp in _CARDINAL_TENS and not reml.startswith(_CARDINAL_UNITS + ('tisíc',)):
        return False
    if comp == 'šest' and not reml.startswith('nás'):
        return False
    if comp == 'mast':
        return reml.startswith('no')
    if comp == 'no':
        return reml.startswith('ksicht')
    if comp == 'sto' and not reml.startswith(
        _CARDINAL_UNITS + _CARDINAL_TEENS + _CARDINAL_TENS + ('tisíc',)
    ):
        return False
    if comp == 'arch' and not reml.startswith(('anjel', 'ae')):
        return False
    if comp == 'neuro' and not reml.startswith(('lóg', 'log', 'tic', 'tič')):
        return False
    # krátk-osti/-ostí is an inflected -osť noun, not krátko + a second member.
    if comp == 'krátko' and reml in ('sti', 'stí'):
        return False
    return any(c in _VOWELS_SK for c in reml) and _starts_like_a_word(reml)


def _is_vowel_seam(pfx: str, reml: str) -> bool:
    """True when a vowel-initial remainder is a root and not the rest of a stem.

    A prefix ending in a vowel in front of a vowel-initial remainder is not
    decidable from the spelling: pri|ateľstvo would be a seam by the letters and
    is not one, so the default is to reject the split. Two environments overturn
    it — a remainder that itself opens with a lexically listed prefix and root,
    and a remainder beginning with u.

    The u is the case section 4.4 is about. Every other vowel pair stays two
    nuclei whatever the analysis says, so the morphology changes nothing there;
    au, eu and ou are read as one nucleus, and only the seam tells po|učiť from
    pau·za.
    """
    if any(
        reml.startswith(inner_pfx + root)
        for inner_pfx, roots in _LEXICAL_PREFIX_ROOTS
        for root in roots
    ):
        return True
    return pfx == 'arci' or reml[0] == 'u'


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

    # A longer recognised first part outranks a shorter prefix lookalike:
    # neuro·lóg is not ne·urológ and polo·vodič is not po·lovodič.
    for length, group in _COMPOSITA_BY_LEN:
        comp = wl[:length]
        if comp in group and len(w) == length:
            return None, None
        if comp in group and len(w) > length + 2:
            rem = w[length:]
            if _licenses_compositum(comp, rem):
                return None, None

    # The learned stem nauti- (nautika, nautilus) only looks like na|u-.
    # Its au is one nucleus; native na|utešovať remains a genuine prefix form.
    if wl.startswith('nauti'):
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
            # posl- is a root family (posol, poslať, poslúchať), not po- + sl-.
            if pfx == 'po' and reml.startswith('sl'):
                continue
            # dôstoj- is a lexicalized stem, not the productive prefix dô- plus
            # stoj-. PSP therefore applies its syllabic st division: dôs·toj-.
            if pfx == 'dô' and reml.startswith('stoj'):
                continue
            licensed = _VOCALIZED_ONLY_BEFORE.get(pfx)
            if licensed is not None and not reml.startswith(licensed):
                continue
            if not any(c in _VOWELS_SK for c in reml):
                continue
            if reml[0] in _NEVER_INITIAL:
                continue
            if licensed is not None:
                return w[:length], rem
            # Remainder must start with a vowel, or with a consonant followed
            # immediately by a vowel (CV start) — blocks 'dpo', 'tvo'→ok, 'dp'→bad
            if reml[0] in _VOWEL_LETTERS:
                # starts with vowel — only accept if prefix ends with consonant
                # (prevents 'pri' + 'atelstvo' splitting 'priateľstvo')
                if pfx[-1] in _VOWEL_LETTERS and not _is_vowel_seam(pfx, reml):
                    continue  # vowel+vowel boundary — skip, not a real prefix split
                return w[:length], rem
            else:
                # starts with consonant — next char must be vowel-like (CV)
                if len(reml) >= 2 and reml[1] in _VOWELS_SK:
                    return w[:length], rem
                # or it's a valid onset cluster (incl. digraph ch)
                if (reml[:2] in _VALID_ONSETS or reml[:3] in _VALID_ONSETS
                        or reml[:2] in ONSET_CLUSTERS or reml[:3] in ONSET_CLUSTERS):
                    return w[:length], rem
                # invalid onset after prefix — not a real prefix boundary
                continue
    return None, None


#: An inflectional ending is short, and every one that follows a derivational
#: suffix begins with a vowel except the instrumental -mi. That is what lets a
#: suffix be found inside a word form and not only at its end: without it
#: chod·ník keeps its boundary but chod·ní·ky loses it.
_MAX_INFLECTION = 4
_CONSONANT_INITIAL_INFLECTIONS = ('mi',)


def _is_inflection(tail: str) -> bool:
    """True when *tail* can be what is left of a word after its last suffix."""
    if not tail:
        return True
    if len(tail) > _MAX_INFLECTION:
        return False
    return tail[0] in _VOWELS_SK or tail in _CONSONANT_INITIAL_INFLECTIONS


def _final_sonorant_needs_following_context(stem: str, following: str) -> bool:
    """Whether short stem-final r/l is syllabic before the next morpheme."""
    return (
        len(stem) >= 2
        and stem[-1].casefold() in ('r', 'l')
        and is_consonant(stem[-2])
        and bool(following)
        and is_consonant(following[0])
    )


def _strip_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Return (stem, rest) if w carries a known consonant-initial suffix and
    the split produces a valid morpheme boundary. Else (None, None).

    Valid boundary: stem ≥3 chars and contains a vowel. A consonant-initial
    suffix remains a morpheme boundary even when the stem ends in a consonant
    cluster (ohyzd·ný, vlast·ný).
    """
    wl = w.lower()
    for suffix in _DLO_INFLECTIONS:
        if wl.endswith(suffix) and wl[:-len(suffix)] in _DLO_PARADIGM_STEMS:
            start = len(w) - len(suffix)
            return w[:start], w[start:]

    for length, group in _SUFFIXES_BY_LEN:
        for tail_length in range(_MAX_INFLECTION + 1):
            start = len(w) - length - tail_length
            if start < 3 or wl[start:start + length] not in group:
                continue
            if not _is_inflection(wl[start + length:]):
                continue
            steml = wl[:start]
            if wl[start:start + length] == 'kár' and not steml.endswith('st'):
                continue
            if not any(c in _VOWELS_SK for c in steml):
                continue
            # -sk- attaches to a consonant-final stem (Benát·ska, voj·sko). On
            # a vowel-final one the s belongs to the stem, not to a suffix:
            # mis·ka, bles·ky, po·ris·ko.
            # mis·ka, bles·ky, po·ris·ko. The one vowel-final stem that keeps
            # the boundary is one ending in a hiatus: no suffix begins with a
            # vowel sequence, so lao·ský cannot be read any other way.
            if length == 2 and (steml[-1] in ALL_VOWELS or steml[-1] == 'ô'):
                if not (len(steml) >= 2 and steml[-2] in ALL_VOWELS):
                    continue
            return w[:start], w[start:]
    return _strip_k_suffix(w)


def _strip_k_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Split the nominal suffix ·k· off a consonant-final stem.

    Without it a three-consonant cluster ending in tk is handed to section 4.3,
    which moves the point left of the whole tk- because tk- does open a Slovak
    word (tkáč): klien|tka. The suffix is a recognised morpheme boundary, so
    section 3 decides first and the result is klient|ka.

    A stem ending in a sibilant is left alone: there the k belongs to the ·sk·
    suffix already listed above (Benát·ska, Vlaš·sko), and reading it as ·k·
    would strand the s (Benáts·ka).
    """
    wl = w.lower()
    for tail_length in range(1, _MAX_INFLECTION + 1):
        start = len(w) - 1 - tail_length
        if start < 3 or wl[start] != 'k':
            continue
        if wl[start + 1:] not in _SK_K_SUFFIX_ENDINGS:
            continue
        steml = wl[:start]
        if steml[-1] in ALL_VOWELS or steml[-1] in ('ô', 's', 'š', 'z', 'ž'):
            continue
        # A stem ending in a syllabic r or l ends in a nucleus, not in a coda,
        # and the k opens its own syllable already: ja·bl·ko, not jabl·ko.
        if steml[-1] in ('r', 'l') and steml[-2:-1] and steml[-2] not in _VOWELS_SK:
            continue
        if not any(c in _VOWELS_SK for c in steml):
            continue
        return w[:start], w[start:]
    return None, None


def _split_compound_tail(w: str) -> tuple[str, str] | None:
    """Split a known compositional second part off the end of *w*."""
    wl = w.lower()
    for tail in _SK_COMPOUND_TAILS:
        head = wl[:-len(tail)]
        if wl.endswith(tail) and len(head) >= 2 and any(c in _VOWELS_SK for c in head):
            return w[:len(head)], w[len(head):]
    return None


def _split_bound_second_member(w: str) -> tuple[str, str] | None:
    """Split a bound Greek second member out of the middle of *w*."""
    wl = w.lower()
    for member in _SK_BOUND_SECOND_MEMBERS:
        seam = wl.find(member)
        if seam < 3 or wl[seam - 1] != _LINKING_VOWEL:
            continue
        if any(c in _VOWELS_SK for c in wl[:seam - 1]):
            return w[:seam], w[seam:]
    return None


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


def get_morpheme_parts(word: str) -> list[str]:
    """Return the morphological units whose seams override phonotactics.

    Typographic hyphenation needs the same analysis as syllabification, but it
    applies a different rule inside each unit. Keeping the units explicit stops
    the PSP consonant-cluster rule from pulling a prefix-final consonant across
    a real morpheme boundary (``roz|ísť``, not ``ro|zísť``).
    """
    wl = word.lower()
    second = _split_compound_tail(word)
    if second is not None:
        first, tail = second
        return [*get_morpheme_parts(first), tail]

    bound = _split_bound_second_member(word)
    if bound is not None:
        first, rest = bound
        if rest.casefold().startswith('naut'):
            return [*get_morpheme_parts(first), rest]
        return [*get_morpheme_parts(first), *get_morpheme_parts(rest)]

    if wl.startswith('naj') and 'tejš' in wl[3:]:
        return [word[:3], *get_morpheme_parts(word[3:])]

    comparative_n = wl.find('nejš')
    if comparative_n > 0:
        return [*get_morpheme_parts(word[:comparative_n]), word[comparative_n:]]

    comparative_t = wl.find('tejš')
    if comparative_t > 0:
        return [*get_morpheme_parts(word[:comparative_t]), word[comparative_t:]]

    pfx, rem = _strip_prefix(word)
    if pfx is not None:
        return [pfx, *get_morpheme_parts(rem)]

    stem, sfx = _strip_grammatical_suffix(word)
    if stem is not None:
        return [*get_morpheme_parts(stem), sfx]

    for length, group in _COMPOSITA_BY_LEN:
        comp = wl[:length]
        if comp in group and len(word) > length + 2:
            rem = word[length:]
            if _licenses_compositum(comp, rem):
                return [word[:length], *get_morpheme_parts(rem)]

    stem, sfx = _strip_suffix(word)
    if stem is not None:
        return [*get_morpheme_parts(stem), sfx]

    return [word]


def get_syllables(word: str) -> list[str]:
    """
    Return linguistic syllable units, without typographic line-break filtering.
    Slovak syllabification: each syllable has one vowel nucleus.
    Syllabic consonants: ŕ, ĺ always; r, l only between consonants (vlk, prst).

    Morpheme-aware: known Slovak prefixes and derivational suffixes form hard
    boundaries that override onset maximization
    (e.g. pod·ze·mie, roz·de·ľo·va·nie, ze·me·pis·ný, pas·tva).

    Rule: the next syllable claims the longest cluster that can open a Slovak
    word (:data:`slabika.phonology.ONSET_CLUSTERS`); the rest closes the
    syllable before it. A known morpheme boundary overrides this.

    :raises ValueError: if *word* contains a letter outside the Slovak writing
        system. Such a word is spelled in a foreign orthography whose sound
        values these rules may not assume, and answering anyway would be a
        guess: měsíc used to come back as a single syllable because ě was read
        as a consonant. :func:`slabika.hyphenate` returns such words untouched.
    """
    wl = word.lower()
    foreign = {char for char in wl if char.isalpha() and char not in ANALYSABLE_LETTERS}
    if foreign:
        raise ValueError(
            f"{word!r} is not spelled in Slovak: {''.join(sorted(foreign))}. "
            "Slovak syllabification cannot be applied to a foreign spelling "
            "without knowing its pronunciation (PSP §5.4)."
        )

    bound = _split_bound_second_member(word)
    if bound is not None and bound[1].casefold().startswith('naut'):
        return _syllabify_simple(word)

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
            if _licenses_compositum(comp, rem):
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
        if _final_sonorant_needs_following_context(stem, sfx):
            stem_syllables = get_syllables(stem + sfx[0])
            stem_syllables[-1] = stem_syllables[-1][:-1]
        else:
            stem_syllables = get_syllables(stem)
        return stem_syllables + _syllabify_simple(sfx)

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
_NUCLEI = ALL_VOWELS | PRONOUNCED_FOREIGN_VOWELS | DIPHTHONGS | {'ŕ', 'ĺ'}

#: Latin -eum and -eus decline a stem that ends in e, so their u opens a
#: syllable of its own: mú·ze·um, li·no·le·um, Or·fe·us. It is the -ium of
#: :func:`_resolve_hiatus` in the neuter and the masculine.
_LATIN_HIATUS_TAILS = ('eum', 'eus')

#: Written vowel graphemes, including the ones that are not phonological
#: diphthongs (ô is written as one grapheme; au, eu, ou are read as one).
_VOWEL_LIKE = (
    ALL_VOWELS | PRONOUNCED_FOREIGN_VOWELS | DIPHTHONGS | {'ô'} | _FALLING_DIPHTHONGS
)

#: No Slovak syllable opens with more than three consonants (vzdych, štvrť).
_MAX_ONSET = 3


def _resolve_hiatus(phonemes: list[str]) -> list[str]:
    """Split a written ia/ie/iu that is two nuclei rather than one diphthong.

    Slovak spelling writes the diphthongs ia, ie, iu exactly like the hiatus of
    a learned loan, and the difference is etymological rather than phonotactic
    (pia·tok but Má·ri·a). Two environments are decidable without a lexicon:

    * ``-ium`` in absolute final position — no native Slovak ending has this
      shape, so the i is always a separate nucleus (akvá·ri·um, štú·di·um);
    * learned final ``-iakum``, whose ``i`` and ``a`` are separate nuclei;
    * the learned ``miliard-`` family, whose ``i`` and ``a`` are separate nuclei;
    * instrumental plural ``-ciami``, where ``-ami`` begins after the ``i``;
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
            learned_iakum = (
                ph == 'ia'
                and phonemes[i + 1:] == ['k', 'u', 'm']
            )
            learned_milliard = (
                ph == 'ia'
                and phonemes[max(0, i - 3):i] == ['m', 'i', 'l']
                and phonemes[i + 1:i + 3] == ['r', 'd']
            )
            cia_instrumental = (
                ph == 'ia'
                and i > 0
                and phonemes[i - 1] == 'c'
                and phonemes[i + 1:] == ['m', 'i']
            )
            if (
                latin_neuter or after_long or learned_iakum
                or learned_milliard or cia_instrumental
            ):
                out.extend([ph[0], ph[1]])
                continue
        out.append(ph)
    return out


def _merge_latin_qu(phonemes: list[str]) -> list[str]:
    """Read qu as one onset grapheme: a·li·quid, not a·li·qu·id.

    Slovak writes the sound as kv and keeps qu only in unassimilated Latin,
    where the u is never a nucleus of its own.
    """
    if 'q' not in phonemes:
        return phonemes
    out: list[str] = []
    skip = False
    for i, ph in enumerate(phonemes):
        if skip:
            skip = False
            continue
        if ph == 'q' and i + 1 < len(phonemes) and phonemes[i + 1] == 'u':
            out.append('qu')
            skip = True
        else:
            out.append(ph)
    return out


def phoneme_layout(word: str) -> tuple[list[str], list[int], list[int]]:
    """Return the phonemes of *word*, their character offsets, and the indices
    of those that carry a syllable nucleus.

    The three lists are what any layer above needs in order to talk about
    positions in the original string: the phonemes never split a digraph or a
    diphthong, and the offsets are exact because every transformation here
    preserves the spelling.

    >>> phoneme_layout("dcéra")
    (['d', 'c', 'é', 'r', 'a'], [0, 1, 2, 3, 4], [2, 4])
    """
    phonemes = _phonemes(word)
    offsets, pos = [], 0
    for phoneme in phonemes:
        offsets.append(pos)
        pos += len(phoneme)
    return phonemes, offsets, _nuclei(phonemes)


def _seam_offsets(word: str) -> frozenset[int]:
    """Character offsets in *word* at which a morpheme unit begins."""
    offsets, position = set(), 0
    for part in get_morpheme_parts(word)[:-1]:
        position += len(part)
        offsets.add(position)
    return frozenset(offsets)


def _merge_falling_diphthongs(word: str, phonemes: list[str]) -> list[str]:
    """Read au, eu, ou as one nucleus except where a morpheme seam divides them.

    Two adjacent vowel letters are not by themselves two syllables (PSP §4.4).
    Slovak writes these three both ways: as one nucleus in a loan or in the
    instrumental (pau·za, pneu·ma·ti·ka, ru·kou) and as two across a seam
    (po|učiť, zne|užiť, tro|j·uholník). The morphology decides, so the seams are
    taken from :func:`get_morpheme_parts` and the sequence is merged everywhere
    else; the Latin endings of :data:`_LATIN_HIATUS_TAILS` are the one hiatus no
    seam marks.
    """
    wl = word.lower()
    if not any(pair in wl for pair in _FALLING_DIPHTHONGS):
        return phonemes

    seams = _seam_offsets(word)
    out: list[str] = []
    offset = index = 0
    while index < len(phonemes):
        phoneme = phonemes[index]
        following = phonemes[index + 1] if index + 1 < len(phonemes) else ''
        pair = phoneme + following
        if (
            pair in _FALLING_DIPHTHONGS
            and offset + len(phoneme) not in seams
            and not wl.endswith(_LATIN_HIATUS_TAILS, offset)
        ):
            out.append(pair)
            offset += len(pair)
            index += 2
            continue
        out.append(phoneme)
        offset += len(phoneme)
        index += 1
    return out


def _phonemes(word: str) -> list[str]:
    phonemes = _merge_latin_qu(_resolve_hiatus(split_into_phonemes(word)))
    return _merge_falling_diphthongs(word, phonemes)


def _nuclei(phonemes: list[str]) -> list[int]:
    n = len(phonemes)

    def is_nucleus(idx: int) -> bool:
        ph = phonemes[idx]
        if ph in _VOWEL_LIKE or ph in ('ŕ', 'ĺ'):
            return True
        if ph in ('r', 'l'):
            # Short r and l are nuclei only where no vowel can be one: between
            # consonants, as in vlk and prst. At the end of a word they are the
            # coda of the syllable before — An·na·mierl, not An·na·mie·rl.
            prev_ok = idx == 0 or phonemes[idx - 1] not in _VOWEL_LIKE
            next_ok = idx < n - 1 and phonemes[idx + 1] not in _VOWEL_LIKE
            return prev_ok and next_ok
        return False

    return [i for i in range(n) if is_nucleus(i)]


def _syllabify_simple(word: str) -> list[str]:
    """Core syllabification without prefix awareness."""
    phonemes = _phonemes(word)
    n = len(phonemes)
    nuclei = _nuclei(phonemes)

    if not nuclei:
        return [word]

    def _best_split(cons_indices: list[int]) -> int:
        """Return the index at which the next syllable's onset begins.

        The onset is the longest run of the cluster that can open a Slovak word
        — it rises in sonority and is attested word-initially. Everything to its
        left closes the syllable before. A single intervocalic consonant is
        always an onset; a cluster that cannot rise (mat·ka, ses·tra, ag·rip·pa)
        gives up all but its last consonant. Explicit morpheme boundaries are
        handled before this phonotactic fallback.
        """
        for size in range(min(_MAX_ONSET, len(cons_indices)), 1, -1):
            cluster = native_spelling(''.join(phonemes[i] for i in cons_indices[-size:]))
            if cluster in ONSET_CLUSTERS:
                return cons_indices[-size]
        return cons_indices[-1]

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
