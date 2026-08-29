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
    'naj', 'nad', 'pod', 'pre', 'pri', 'pro', 'roz', 'bez', 'obo', 'odo', 'pra', 'sú', 'syn',
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

_DOBR_INFLECTIONS = frozenset({
    'a', 'ami', 'e', 'ej', 'o', 'om', 'ou', 'u',
    'á', 'ách', 'ám', 'é', 'ého', 'ému', 'í', 'ú', 'ý', 'ých', 'ým', 'ými',
})
_NECHT_INFLECTIONS = frozenset({'', 'a', 'ami', 'e', 'mi', 'och', 'om', 'ov', 'u', 'y'})
_NEGER_CONTRACTED_INFLECTIONS = frozenset({'a', 'ami', 'i', 'och', 'om', 'ov', 'ovi'})
_POSLAT_SUPPLETIVE_INFLECTIONS = frozenset({
    'a', 'e', 'em', 'eme', 'eš', 'ete', 'i', 'ime', 'ite', 'o', 'ú',
})
_POSTIT_INFLECTIONS = frozenset({
    'i', 'iac', 'ia', 'il', 'ila', 'ili', 'ilo', 'ime', 'ite', 'iť',
    'í', 'ím', 'íme', 'íš', 'íte',
})
_POSTA_INFLECTIONS = frozenset({
    'a', 'e', 'ou', 'u', 'y', 'ovú', 'ovej', 'ovom', 'ovou', 'ová', 'ové',
    'ového', 'oví', 'ový', 'ových', 'ár', 'ára', 'árov',
})
_NOVOCAIN_INFLECTIONS = frozenset({'', 'a', 'e', 'om', 'u'})
_OBAL_INFLECTIONS = frozenset({
    '', 'e', 'enej', 'enia', 'ená', 'ené', 'eného', 'ením', 'ený', 'enými',
    'ia', 'il', 'ila', 'iť', 'mi', 'och', 'om', 'ov', 'ovou', 'ová', 'ové',
    'ovú', 'ových', 'ovými', 'u', 'y', 'í',
})
_OBER_INFLECTIONS = frozenset({
    'al', 'ali', 'ač', 'ači', 'ačku', 'ačky', 'ajú', 'ajúcej', 'ajúcom', 'ať',
    'ie', 'iem', 'ieme', 'te', 'á', 'ám', 'áte', 'ú',
})
_OBVYKL_INFLECTIONS = frozenset({
    'a', 'e', 'ej', 'ejšia', 'ejšie', 'ejšieho', 'ejšiemu', 'ejších', 'ejší',
    'ejším', 'ejšími', 'om', 'ou', 'á', 'é', 'ého', 'ému', 'í', 'ú', 'ý', 'ých',
    'ým', 'ými',
})
_VYKN_INFLECTIONS = frozenset({
    'e', 'em', 'eme', 'ete', 'eš', 'i', 'ime', 'ite', 'ú', 'úc', 'úť',
})
_ODIAT_SUPPLETIVE_FORMS = frozenset({
    'odej', 'odeje', 'odejte', 'odejú', 'odel', 'odela', 'odeli',
})
_ODEN_INFLECTIONS = frozenset({
    'á', 'é', 'ého', 'ej', 'ému', 'í', 'om', 'ou', 'ú', 'ý', 'ých', 'ým', 'ými',
})
_ODET_INFLECTIONS = frozenset({
    'ie', 'á', 'é', 'ého', 'ej', 'ejšia', 'ejšie', 'ejšieho', 'ejšiemu', 'ejších',
    'ejší', 'ejším', 'ejšími', 'ému', 'í', 'om', 'ou', 'ú', 'ý', 'ých', 'ým', 'ými',
})
_ODEV_INFLECTIONS = frozenset({
    '', 'e', 'mi', 'ná', 'né', 'ného', 'nej', 'nému', 'ní', 'nom', 'nou', 'nú',
    'ný', 'ných', 'ným', 'nými', 'och', 'om', 'ov', 'u', 'y',
})
_ZOHNUT_INFLECTIONS = frozenset({
    'hla', 'hli', 'hlo', 'hol', 'hne', 'hnem', 'hneme', 'hneš', 'hnete', 'hni',
    'hnime', 'hnite', 'hnú', 'hnúť',
})

_LEXICAL_PREFIX_ROOTS = (
    ('de', ('flog', 'flor', 'grad')),
    ('hoci', ('ktor',)),
    ('hvezdo', ('prav',)),
    ('hrozo', ('straš',)),
    ('miesto', ('kráľ',)),
    ('mimo', ('priestor',)),
    ('zimo', ('mrav',)),
    ('zvero', ('kruh',)),
    ('kde', ('ktor',)),
    ('ni', ('kde', 'kdy', 'kto')),
    ('nie', ('kde', 'kto', 'ktor')),
    ('non', ('plusultra',)),
    ('north', ('rup',)),
    ('plus', ('ultra',)),
    ('post', ('gradu',)),
    ('kladko', ('stroj',)),
    ('nanebo', ('vstúp',)),
    ('naozaj', ('stn',)),
    ('ob', ('oznám',)),
    ('obo', ('hn',)),
    ('od', ('opier', 'tn', 'umier')),
    ('odo', ('hráv',)),
    ('ohňo', ('stroj', 'vzdor', 'žrút')),
    ('okolo', ('stoj',)),
    ('oro', ('graf',)),
    ('steno', ('graf',)),
    ('sto', ('stop',)),
    ('tele', ('graf',)),
    ('telo', ('cvik',)),
    ('topo', ('graf',)),
    ('typo', ('graf',)),
    ('práce', ('schop',)),
    ('sväto', ('pravdiv',)),
    ('vydaja', ('schop',)),
    ('vďaky', ('vzdan',)),
    ('života', ('schop',)),
    ('životo', ('správ',)),
    ('časo', ('priestor',)),
    ('činu', ('schop',)),
    ('človeko', ('zviera',)),
    ('dva', ('uhol',)),
    ('dvoj', ('uch',)),
    ('päť', ('uhol',)),
    ('sedem', ('uhol',)),
    ('štvor', ('uhol',)),
    ('porno', ('graf',)),
    ('prvo', ('tlač', 'tried')),
    ('rozo', ('br', 'ber', 'smej', 'sta', 'strel', 'stret', 'stup', 'stúp', 'zvo', 'zvu', 'zna', 'zná', 'žer', 'žier', 'žr')),  # rozo·staviť, rozo·znať — not roz·os-
    ('zo', ('žn',)),
    ('samo', ('hlás', 'spravod', 'stvoriteľ', 'svet', 'sviet', 'vlád', 'vrav', 'vytvor', 'zrej')),
    ('sedmo', ('spáč',)),
    ('slovo', ('sled',)),
    ('polo', (
        'bláz', 'brat', 'človek', 'francúz', 'hlas', 'hmot', 'plášť', 'pleš',
        'pravdiv', 'prázd', 'prizn', 'prorok', 'slep', 'slov', 'smr', 'spán',
        'spoloč', 'svet', 'tm', 'zdivoč', 'zhnit', 'zrel', 'zren', 'zviera', 'štrbin',
    )),
    ('pohano', ('kresťan',)),
    ('pomsty', ('chtiv',)),
    ('písmeno', ('žrút',)),
    ('pre', ('diabol', 'dier', 'duchov')),
    ('pol', ('libr', 'liter', 'litr', 'ostrov', 'roč', 'rok', 'rúr')),
    ('plno', ('zvuč',)),
    ('rovno', ('zvuč',)),
    ('spolu', ('blíž', 'brat', 'hlás', 'hráč', 'kráľ', 'kresťan', 'kňaz', 'plod', 'posvät', 'prac', 'prežív', 'sláv', 'slúž', 'sprav', 'správ', 'stolov', 'tvor', 'vlast', 'vlád', 'vzruš', 'zľutov', 'znič', 'zvuč')),
    ('staro', ('sláv', 'svet', 'zná')),
    ('sveta', ('skúsen',)),
    ('sveto', ('slep', 'vlád', 'zná')),
    ('sväto', ('svät',)),
    ('tisíc', ('hlas',)),
    ('tisíco', ('hlas',)),
    ('veľko', ('kráľ',)),
    ('vice', ('kráľ',)),
    ('uza', ('vrel',)),
    ('vele', ('zrad',)),
    ('víťazo', ('sláv',)),
    ('vlasti', ('zrad',)),
    ('vše', ('spravod', 'svet', 'svät', 'vlád', 'zľutov', 'žrút')),
    ('znovu', ('navrát', 'stret')),
    ('žalo', ('spev',)),
    ('žido', ('kresťan',)),
    ('o', (
        'hra', 'hrá', 'hroz', 'slab', 'slad', 'sláv', 'slep', 'slob', 'slov',
        'plach', 'plách', 'plak', 'plat', 'plášt', 'pleš', 'plet', 'plod', 'plot', 'pľu', 'pľú',
        'prac', 'prad', 'praď', 'pral', 'pras', 'praš', 'práš', 'prať',
        'pre', 'pri', 'pros', 'prot',
        'podstat', 'prav', 'práv', 'pust', 'sln', 'smel', 'spev', 'spra', 'streľ',
        'strih', 'strieľ', 'sved', 'svet', 'svie', 'svoj', 'sídl', 'tlač', 'tlak',
        'tras', 'trh', 'tup', 'vplyv', 'zbroj', 'živ',
    )),
    ('in', ('štruk',)),
    ('šéf', ('lekár',)),
    ('pa', ('kľúč',)),
    ('para', ('fráz', 'graf')),
    ('pra', ('arch',)),
    ('prie', ('hľad', 'hrad', 'klep', 'strel', 'stup', 'svit', 'zrač')),
    ('prí', ('klad', 'krat', 'plat', 'prav', 'slov', 'sluš', 'sľub', 'spev', 'stav', 'stup', 'tlač', 'tvrd', 'vlast', 'znak', 'zvuk')),
    ('naj', ('všestran',)),
    ('ne', ('scudzolož', 'sčerv', 'sťah', 'sťaž', 'včas', 'vchádz', 'včlen', 'včleň', 'vdých', 'vdych', 'vhod', 'vklad', 'vkrad', 'vkrád', 'vkroč', 'vkus', 'vľúd', 'vmieš', 'vpad', 'vpál', 'vpi', 'vpláv', 'vplýv', 'vpust', 'vpúšť', 'vsad', 'vsádz', 'všed', 'všim', 'vším', 'vštep', 'vťah', 'vďač', 'vďak', 'zhas', 'zhod')),
    ('novo', ('povst', 'prij', 'stan', 'stvor', 'vzbud', 'vznik', 'vysvät', 'zdol', 'zhotov', 'zjav', 'zrod', 'zvol')),
    ('ono', ('svet',)),
    ('na', (
        'dan', 'darm', 'dáv', 'del', 'deľ', 'dikt', 'divok', 'dobr',
        'dobud', 'dobúd', 'doďak', 'doj', 'dopov', 'doraz', 'dostač',
        'drob', 'duj', 'dul', 'dur', 'dut', 'dúv', 'jal', 'jat', 'jav', 'jazd',
        'jedia', 'jedl', 'jedo', 'jedz', 'jeme', 'jemn', 'jesť', 'jež', 'jím', 'stup', 'sťah',
        'zhromažd', 'žgrl',
    )),
    ('nade', ('všet',)),
    ('ná', ('cvik', 'dvor', 'hľad', 'hrad', 'hrob', 'klad', 'klaď', 'prav', 'skok', 'sten', 'stup', 'tlak', 'vnad', 'vrat', 'znak')),
    ('sprí', ('stup',)),
    ('spo', ('plat', 'zná')),
    # po·drobiť (rozdrobiť) against pod·robiť (podmaniť) — the two are spelled
    # alike and only the sense tells them apart. PSP prints po-drobný, and the
    # adjective and its adverbs are the frequent reading of the string.
    ('pod', ('oblas',)),
    # čakať has the prefixed allomorph -čkať (do·čkať, po·čkať, pre·čkať, vy·čkať).
    ('do', ('čk',)),
    ('po', ('čk', 'daj', 'dal', 'dan', 'dateľ', 'dať', 'dá', 'dar', 'dej', 'del', 'delen', 'deli', 'delí', 'deľ', 'die', 'diel', 'dier', 'diev', 'dieľ', 'dív', 'div', 'dob', 'doj', 'dom', 'dotk', 'dotý', 'dozr', 'drážd', 'drep', 'driemk', 'drob', 'druh', 'slúž', 'sluš', 'sťaž', 'vďač', 'vďak', 'vklad', 'všim', 'zdrav', 'zhas')),
    ('pre', ('čk', 'daj', 'dal', 'dan', 'dať', 'dáv', 'vďač')),
    ('u', ('hrad', 'krát', 'pokoj', 'rod', 'spokoj', 'sporiad', 'šľacht', 'taj', 'tláč')),
    ('vy', ('čk', 'chlad')),
    ('za', ('obíd', 'obiš', 'vďač')),
    ('zá', ('blesk', 'chvat', 'hrad', 'hrob', 'klad', 'plat', 'prah', 'skok', 'stup')),
    ('ú', ('hrad', 'kryt', 'plat', 'stup')),
)

_NEGATED_NONSYLLABIC_PREFIX_ROOTS = (
    ('z', ('hlt', 'hrab', 'hrdz', 'hreš', 'hrn', 'hromaž', 'hroz', 'hust')),
)

_NESTED_PREFIX_ROOTS = (
    ('do', ('tkn',)),
    ('o', ('brús', 'chlad', 'chrán', 'chrom', 'hlas', 'hlás', 'hluch', 'hmat', 'hnu', 'hol', 'hryz', 'klam', 'krídl', 'mdliev', 'slav', 'strih', 'toč', 'táč', 'vplyv', 'zbroj', 'šklb')),
    ('ob', ('íd', 'išiel', 'išl', 'ísť', 'omkn', 'oznám', 'ozret')),
    ('obo', ('p',)),
    ('od', ('íd', 'išiel', 'išl', 'ísť', 'opier', 'tiah', 'umier', 'umr', 'vih', 'zrkadľ', 'ži')),
    ('odo', ('ber', 'hnal', 'hrá', 'hral', 'hráv', 'mkn', 'prel', 'pri', 'vzd', 'žen')),
    ('po', ('hl', 'hn', 'klon')),
    ('pod', ('uj',)),
    ('pri', ('klon',)),
    ('roz', ('oh',)),
    ('u', ('chrán', 'chvát', 'drž', 'hlad', 'hryz', 'klad', 'krad', 'mlč', 'mĺk', 'mŕtv', 'pad', 'plat', 'sporad', 'trp', 'tvrd', 'tŕž', 'vrh', 'zdrav', 'zn')),
    ('za', ('obíd', 'obiš', 'tkn', 'čn', 'hl', 'hn', 'mk', 'žn')),
    ('vy', ('hne', 'kla', 'sch', 'zne')),
    ('zo', ('žn',)),
)

# Vocalized prefix variants (bezo-, nado-, obo-, podo-, predo-) exist only in
# licensed environments: obo- before the p-roots below, otherwise mainly the
# pronoun stems mn- and vš-: bezo mňa, podo
# mnou, nadovšetko, predovšetkým. Everywhere else the -o- belongs to the root,
# and the consonant-final base prefix is the correct analysis: bez·ohľadný,
# pod·oblasť, nad·oblačný, pred·obraz. Without this restriction the longer
# variant matches first and swallows the root's initial vowel.
_VOCALIZED_ONLY_BEFORE = {
    'bezo': ('mn',),
    'nado': ('vš', 'mn'),
    'obo': ('p',),
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
    'tina',   # kazaš·tina in language names; miliard·tina as a numeral fraction
    'ných', 'ného', 'nému',
    # 3 chars
    'stv',    # priateľ·stvo, kráľov·stvá
    'ctv',    # baní·ctvo, zdravotní·ctvo
    'cia',    # funk·cia, ak·cia, polí·cia — the borrowed -tio suffix
    'ník', 'níc', 'nik', 'nic', 'nil', 'kár',  # dl·žník, dážd·nik, účast·nil
    'ným', 'nej', 'nou', 'nom',   # ohrad·ným — the rest of the ·ný paradigm
    'dlo',    # mera·dlo
    'liv',    # hanb·livý, kost·livec
    'núť', 'nuť', 'nut',  # dotk·núť, písk·nuť; mľask·nutie
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
_RHYTHMIC_SHORT_NIK = frozenset({'nik', 'nic'})
_RHYTHMIC_SHORT_NY_SUFFIXES = (
    'neho', 'nemu', 'nych', 'nymi', 'nym', 'ny', 'na', 'ne', 'nu', 'ni',
)
_RHYTHMIC_SHORT_NY_STEMS = frozenset({'hviezd'})
_RHYTHMIC_LONG_NUCLEI = LONG_VOWELS | DIPHTHONGS | {'ŕ', 'ĺ'}

_DLO_INFLECTIONS = ('dlami', 'dlách', 'dlom', 'dlám', 'diel', 'dla', 'dle', 'dlu', 'dlá')
_DLO_PARADIGM_STEMS = frozenset({'páči'})
_DLO_PAST_PREFIXES = frozenset({'', 'do', 'na', 'od', 'o', 'po', 'pre', 'pri', 'roz', 's', 'u', 'v', 'vy', 'za'})
_D_FINAL_PAST_ROOTS = ('krad', 'pad')
_D_FINAL_PAST_STEMS = frozenset({'zjed'})
_TINA_INFLECTIONS = ('tinami', 'tinách', 'tinám', 'tinou', 'tine', 'tinu', 'tiny')
_TINA_NUMERAL_STEMS = frozenset({'miliard'})
_SKNUT_FINITE_SUFFIXES = ('neme', 'nete', 'nem', 'neš', 'ni')

# Short grammatical suffixes are boundaries only after consonant-final stems.
# Keep these separate from derivational suffixes to avoid treating every final
# -mi, -me, or -te sequence as morphology.
_SK_GRAMMATICAL_SUFFIXES_CONS = ('mi', 'me', 'te', 'ne', 'la', 'li', 'lo')
_SHORT_COMPARATIVE_INFLECTIONS = (
    'šieho', 'šiemu', 'šími', 'šej', 'ších', 'šia', 'šie', 'ším', 'šiu', 'šom', 'šou', 'ší',
)

# The nominal suffix ·k· cannot be listed above, because the vowel that follows
# it belongs to the ending, not to the suffix: klient·ka, klient·ky, klient·kou.
# It is therefore matched as the single letter k plus one of the endings of the
# paradigms it derives — the žena/ulica type, the mesto type, ·kyňa and ·kový.
_SK_K_SUFFIX_ENDINGS = frozenset({
    'a', 'y', 'e', 'u', 'ou', 'ám', 'ách', 'ami', 'am',        # klient·ka
    'o', 'i', 'om', 'ov', 'och', 'ovi', 'ovia',                # Robert·ko, líst·kov
    'yňa', 'yne', 'yňu',                                       # vešt·kyňa
    'ová', 'ové', 'ový', 'ovú', 'ovej', 'ovom', 'ovým',        # poist·ková
    'ovejšie',                                                  # moment·kovejšie
})
_K_SUFFIX_ENDING_LENGTHS = tuple(sorted({len(ending) for ending in _SK_K_SUFFIX_ENDINGS}))

# Compositional first-parts that act as hard split boundaries (troj·uholník, viac·hlasný...)
_SK_COMPOSITA = [
    'deväťdesiat', 'osemdesiat', 'sedemdesiat', 'šesťdesiat', 'päťdesiat',
    'štyridsať', 'tridsať', 'dvadsať',
    'devätnásť', 'osemnásť', 'sedemnásť', 'šestnásť', 'pätnásť',
    'štrnásť', 'trinásť', 'dvanásť', 'jedenásť',
    'video', 'niekoľko', 'deväť', 'sedem', 'osem', 'šesť', 'šest', 'päť', 'zeme', 'vrti',
    'troj', 'tri', 'dve', 'štyri', 'sto', 'tisíc', 'viac', 'geo', 'teo', 'bio', 'foto', 'auto', 'euro', 'etyl',
    'agro', 'agri', 'astro', 'aero', 'anti', 'archi', 'arch',
    'hydro', 'termo', 'elektro', 'mikro', 'makro', 'mono', 'neuro', 'poly',
    'pseudo', 'semi', 'hemi', 'kvazi', 'inter', 'intra', 'extra', 'ultra',
    'super', 'hyper', 'meta', 'multi', 'mini', 'maxi',
    # Slovak-specific composita
    'modlo', 'rodo', 'jedno', 'stredo', 'brati', 'mäso', 'mast', 'krátko', 'krato', 'dobro', 'tvrdo', 'plno', 'právo', 'rovno',
    'bielo', 'bledo', 'blaho', 'boho', 'bohu', 'boja', 'bože', 'brato', 'čaro', 'blesko',
    'celo', 'choreo', 'chorobo', 'chválo', 'čierno', 'červeno',
    'cudzo', 'ďaleko', 'darmo', 'delo', 'divo', 'drevo', 'drobno', 'duto', 'fajn', 'gramo',
    'hnedo', 'holo', 'hromo', 'hrôzo', 'hrubo', 'ino', 'jasno', 'jedino', 'jemno', 'juho', 'prirodzeno',
    'koso', 'kozmo', 'krepo', 'krivo', 'krížo', 'kruto', 'krvi', 'krvo', 'kučeravo', 'kušo', 'kvart', 'ľano', 'ostro', 'pravdo',
    'leto', 'leuko', 'ľubo', 'ľúbo', 'ľudo', 'luko', 'lyko', 'lyro', 'málo', 'márno', 'medeno', 'medo', 'melo', 'mili', 'mimo', 'more', 'mrcho', 'mrkvo', 'svetsko',
    'veľa', 'veľko', 'veľ',   # veľa·vravný; veľko·vláda; veľ·kňaz, veľ·kolepý, veľ·mocný
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
    'bystro', 'hore', 'mnoho', 'mravo', 'novo', 'polo', 'viero',
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
# sees the seam in vino|hrad or demo|krat because the same member recurs in front
# of him — demokrat/demokracia, aristokrat/aristokracia, byrokrat/byrokracia.
# Most members follow linking -o-; the fixed first part Bele- also licenses hrad.
# The member is searched inside the form
# (aristokratickými), and it needs a first part of its own: the s- of Sokrates
# is not one, and neither is the word-initial krat- of kratochvíľa.
_SK_BOUND_SECOND_MEMBERS = ('krat', 'krac', 'hrad', 'hned', 'naut', 'tvor', 'plav', 'vrah', 'zlat', 'zvyk', 'zver', 'znič', 'vlas')
_BOUND_SECOND_MEMBER_HEADS = {
    'vlas': frozenset({
        'ohnivo', 'plamenno', 'plavo', 'prosto', 'sivo', 'striebro', 'tmavo', 'žlto',
    }),
    'vrah': frozenset({'matko', 'otco', 'samo'}),
    'zlat': frozenset({
        'bledozeleno', 'ryšavo', 'svetlo', 'tmavo', 'trávovo', 'zelenkasto',
        'zeleno',
    }),
    'zvyk': frozenset({'zlo'}),
    'zver': frozenset({'novo', 'polo'}),
    'znič': frozenset({'polo'}),
    'plav': frozenset({
        'pieskovo', 'ryšavo', 'sivo', 'svetlo', 'svetlozlato', 'tmavo',
        'tmavozlato', 'vzducho', 'zlato', 'špinavo',
    }),
    'tvor': frozenset({
        'formo', 'miero', 'novo', 'obrazo', 'samo', 'tóno', 'všetko', 'zemo',
        'zázrako', 'čino', 'žlčo',
    }),
}
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
    'db', 'hľ', 'hv', 'kd', 'kt', 'mk', 'mn', 'pl', 'pr', 'sf', 'sl', 'sm', 'sn', 'sp', 'sr', 'st',
    'sv', 'sk', 'tk', 'tr', 'tl', 'lž', 'vn', 'vr', 'vl', 'vt', 'vz', 'zb', 'zd', 'zl',
    'zm', 'zn', 'zr', 'zv', 'šk', 'šp', 'št', 'šť', 'šv', 'žd',
    'pch', 'sch', 'vzd', 'vst', 'str', 'spr', 'skr', 'štv', 'vžd',
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
_NEVER_INITIAL = set('äyýĺŕ')

#: The vowel sequences that are written as two letters and read as one nucleus.
#: Slovak phonology counts four diphthongs and none of these is among them, but
#: word division is about the written syllable, and PSP §4.4 asks for the
#: decision to be made before a point is placed between the letters: the pair is
#: one nucleus wherever no morpheme seam runs through it (pau·za, pneu·ma·ti·ka,
#: ru·kou) and two where one does (po|učiť, zne|užiť). Foreign ai is one
#: nucleus before l (kok·tail, de·tail), but remains a hiatus elsewhere (na·ivný).
_FALLING_DIPHTHONGS = frozenset({'ai', 'au', 'eu', 'ou'})


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
        consonant_composita = {
            'bystro': ('sluch', 'zrak'),
            'novo': ('nastup', 'postav', 'stav', 'vytvor'),
            'polo': (
                'bláz', 'človek', 'francúz', 'hmot', 'krot', 'plášť', 'pleš',
                'prázd', 'prie', 'prizn', 'prorok', 'slov', 'smr', 'spán',
                'spoloč', 'tmav', 'vyprah', 'štrbin',
            ),
            'vše': ('stran', 'stred'),
            'vysoko': ('postav', 'škol'),
            'mnoho': (
                'hlav', 'hran', 'skúsen', 'sľub', 'štít', 'stran', 'strom',
                'tlam', 'tvár', 'vlád', 'vrav', 'žrút',
            ),
        }
        if not reml.startswith(consonant_composita.get(comp, ())):
            return False
    if comp == 'mäso' and not reml.startswith('žrav'):
        return False
    if comp == 'gramo' and not reml.startswith('plat'):
        return False
    if comp == 'kvart' and not reml.startswith('sext'):
        return False
    guarded_compounds = {
        'niekoľko': ('dň',),
        'leto': ('kruh',),
        'leuko': ('plast',),
        'ľubo': ('zvu',),
        'ľúbo': ('zvu',),
        'ľudo': ('op', 'prázd', 'žrút'),
        'luko': ('stre',),
        'lyko': ('žrút',),
        'lyro': ('chvost',),
        'málo': ('kde', 'kto', 'ktor', 'vrav'),
        'márno': ('trat',),
        'medeno': ('plav',),
        'medo': ('slad',),
        'melo': ('dram',),
        'mili': ('gram',),
        'mimo': ('hmot',),
        'more': ('plav',),
        'mrcho': ('žrút',),
        'mrkvo': ('vlas',),
        'plno': ('plat', 'práv'),
        'prirodzeno': ('práv',),
        'právo': ('plat',),
        'rovno': ('stup', 'práv', 'znač'),
        'svetsko': ('práv',),
        'veľa': ('dôstoj', 'sľub', 'vrav'),
        'veľko': ('slúž', 'špekulant', 'vlád', 'zvuč'),
    }
    if comp in guarded_compounds and not reml.startswith(guarded_compounds[comp]):
        return False
    if comp == 'mini' and reml.startswith(('eme', 'ete', 'ster', 'str', 'štr')):
        return False
    if comp == 'čaro' and not reml.startswith('krás'):
        return False
    if comp in {'celo', 'červeno', 'duto', 'hnedo', 'holo', 'hrubo'} and reml.startswith(('sť', 'sti', 'stn')):
        return False
    consonant_final_quantity_before_vowel = (
        comp in _CARDINAL_UNITS
        and comp[-1] not in _VOWEL_LETTERS
        and reml[0] in _VOWEL_LETTERS
    )
    if (
        comp in _HUNDRED_MULTIPLIERS
        and not reml.startswith(('sto', 'tisíc'))
        and not consonant_final_quantity_before_vowel
    ):
        return False
    nested_compositum = any(
        reml.startswith(inner)
        and len(rem) > len(inner) + 2
        and _licenses_compositum(inner, rem[len(inner):])
        for _, group in _COMPOSITA_BY_LEN
        for inner in group
    )
    if (
        comp in _CARDINAL_TENS
        and not reml.startswith(_CARDINAL_UNITS + ('tisíc',))
        and not nested_compositum
    ):
        return False
    if comp == 'šest' and not reml.startswith('nás'):
        return False
    if comp == 'mast':
        return reml.startswith('no')
    if comp == 'no':
        return reml.startswith('ksicht')
    if comp == 'sto' and not reml.startswith(
        _CARDINAL_UNITS + _CARDINAL_TEENS + _CARDINAL_TENS + ('tisíc', 'člen')
    ):
        return False
    if comp == 'tisíc' and not reml.startswith(
        _CARDINAL_UNITS + _CARDINAL_TEENS + _CARDINAL_TENS
    ):
        return False
    if comp == 'arch' and not reml.startswith(('anjel', 'ae')):
        return False
    if comp == 'neuro' and not reml.startswith(('lóg', 'log', 'tic', 'tič')):
        return False
    if comp == 'ostro' and not reml.startswith(('chvost', 'hran', 'streľ', 'vtip', 'zrak')):
        return False
    if comp == 'pravdo' and not reml.startswith('vrav'):
        return False
    if comp == 'inter' and reml.startswith(('es', 'iér')):
        return False
    # krátk-osti/-ostí and tvrd-osti are inflected -osť nouns, not compounds
    # whose first parts happen to end in -o.
    if comp == 'krátko' and reml in ('sti', 'stí'):
        return False
    if comp in {'drobno', 'tvrdo'} and reml in (
        'sť', 'sti', 'stí', 'stiam', 'stiach', 'sťami', 'sťou',
    ):
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
        for inner_pfx, roots in (*_LEXICAL_PREFIX_ROOTS, *_NESTED_PREFIX_ROOTS)
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

    if wl.startswith('veľkokráľ'):
        return w[:5], w[5:]
    if wl.startswith('predobr') and wl[7:] in _DOBR_INFLECTIONS:
        return w[:3], w[3:]
    if any(
        wl.startswith('ne' + nested_pfx + root)
        for nested_pfx, roots in _NESTED_PREFIX_ROOTS
        for root in roots
    ) or any(
        wl.startswith('ne' + nested_pfx + root)
        for nested_pfx, roots in _NEGATED_NONSYLLABIC_PREFIX_ROOTS
        for root in roots
    ):
        return w[:2], w[2:]

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
    if wl.startswith('necht') and wl[5:] in _NECHT_INFLECTIONS:
        return None, None
    if wl.startswith('obuš'):
        return None, None
    # Nefrit-, nezbed- and nežn- are lexical stems, not ne- forms.
    if wl.startswith(('nefrit', 'nezbed', 'nežn')) or wl == 'neger' or (
        wl.startswith('negr') and wl[4:] in _NEGER_CONTRACTED_INFLECTIONS
    ):
        return None, None

    if wl.startswith('ostrihom'):
        return None, None
    for pfx, roots in _LEXICAL_PREFIX_ROOTS:
        if any(wl.startswith(pfx + root) for root in roots):
            return w[:len(pfx)], w[len(pfx):]
    if wl.startswith('predá') and wl[5:] in ('', 'm', 'me', 'š', 'te'):
        return w[:3], w[3:]

    for length, group in _PREFIXES_BY_LEN:
        pfx = wl[:length]
        if pfx in group:
            rem = w[length:]
            reml = rem.lower()
            if len(rem) < 3:
                continue
            # In z-obraz-, z-ohľad-, z-ohnúť, z-ostať and z-otroč- the o belongs
            # to the vowel-initial base; keep genuine zo- forms such as zo-brať intact.
            if pfx == 'zo' and (
                reml.startswith((
                    'braz', 'hľad', 'hnut', 'stať', 'stal', 'staň', 'stan',
                    'stáv', 'stat', 'troč',
                ))
                or reml in _ZOHNUT_INFLECTIONS
                or reml == 'sta'
            ):
                continue
            # posl- and the suppletive pošl- forms of poslať are lexical roots,
            # unlike transparent po-|slúžiť and po-|šliapať.
            if pfx == 'po' and (
                reml.startswith('sl')
                or (
                    reml.startswith('šl')
                    and reml[2:] in _POSLAT_SUPPLETIVE_INFLECTIONS
                )
            ):
                continue
            # Pospas-, pospol-, podl-, pohreb-, popruh-, postul-, pošv-, potk-,
            # povodn-/povodň-, povraz- and potreb- are lexical stems,
            # not productive po- forms.
            if pfx == 'po' and (
                wl.startswith((
                    'podl', 'pohreb', 'poplach', 'popruh', 'postul', 'pošv', 'potk',
                    'povodn', 'povodň', 'povraz',
                ))
                or reml.startswith(('spas', 'spol', 'treb'))
            ):
                continue
            # postiť is derived from pôst; only its closed inflectional paradigm
            # is protected because po-|st- remains productive elsewhere.
            if pfx == 'po' and reml.startswith('st') and reml[2:] in _POSTIT_INFLECTIONS:
                continue
            # Pošta and its derivatives have the lexical stem pošt-, unlike
            # po-|štekliť, po-|štípať and the other productive po- verbs.
            if pfx == 'po' and reml.startswith('št') and reml[2:] in _POSTA_INFLECTIONS:
                continue
            # Posteľ-/postel-/postieľ- is one lexical stem, not po- plus st-.
            if pfx == 'po' and wl.startswith(('posteľ', 'postel', 'postieľ')):
                continue
            # Prakt- is borrowed; prask- and prahn- are lexical stems. None
            # contains the Slovak ancestor prefix pra-.
            if pfx == 'pra' and reml.startswith(('hn', 'kt', 'sk')):
                continue
            # dobr- is the lexical base of dobrý, dobro and dobrota, not do- +
            # br-. Keep genuine prefixed verbs such as do·brať and do·brúsiť.
            if pfx == 'do' and reml.startswith('br'):
                dobr_tail = reml[2:]
                if (
                    dobr_tail in _DOBR_INFLECTIONS
                    or dobr_tail.startswith(('ák', 'ác', 'ot'))
                ):
                    continue
            # domn- is the base of domnelý/domnienka/domnievať, and domkár is
            # derived from dom. Neither is the prefix do- plus an m-initial root.
            if pfx == 'do' and reml.startswith(('mkár', 'mn')):
                continue
            # Došv- is the lexical stem inside podošva, not do- plus šv-.
            if pfx == 'do' and wl.startswith('došv'):
                continue
            # doška/doštička are lexical stems, unlike do·škriabať.
            if pfx == 'do' and (reml == 'šky' or reml.startswith('štič')):
                continue
            # dôstoj- is a lexicalized stem, not the productive prefix dô- plus
            # stoj-. PSP therefore applies its syllabic st division: dôs·toj-.
            if pfx == 'dô' and reml.startswith('stoj'):
                continue
            # Problém and the prost- family have lexical stems, not the prefix pro-.
            if pfx == 'pro' and reml.startswith(('blém', 'st')):
                continue
            # Rozum- is the lexical stem of rozumieť, not roz- plus umieť.
            if pfx == 'roz' and reml.startswith('um'):
                continue
            # Nadácia is a borrowed lexical stem, not nad- plus ácia.
            if pfx == 'nad' and reml.startswith('áci'):
                continue
            # Podest- and podošv- are lexical stems, not pod- plus a vowel-initial root.
            if pfx == 'pod' and wl.startswith(('podest', 'podošv')):
                continue
            # Poden-/podenk- is the lexical stem of podenka, not pod- plus an e-initial root.
            if pfx == 'pod' and wl.startswith('poden'):
                continue
            # Odieť has suppletive odej-/odel-/oden-/odet- forms, and odev- is
            # their lexical nominal stem; none contains the productive prefix od-.
            if pfx == 'od' and (
                wl in _ODIAT_SUPPLETIVE_FORMS
                or (wl.startswith('oden') and wl[4:] in _ODEN_INFLECTIONS)
                or (wl.startswith('odet') and wl[4:] in _ODET_INFLECTIONS)
                or (wl.startswith('odev') and wl[4:] in _ODEV_INFLECTIONS)
            ):
                continue
            # Odolať/odolný, odôvodniť, oduševniť and the odut- forms of
            # oduť have lexical stems rather than the productive prefix od-.
            if pfx == 'od' and (
                wl == 'odol'
                or wl.startswith((
                    'odola', 'odolá', 'odoln', 'odôvod', 'odušev', 'odut',
                ))
            ):
                continue
            # Vyknúť has the lexical stem vykn-/vyk-, not the prefix vy-.
            if (
                pfx == 'vy'
                and wl.startswith('vykn')
                and wl[4:] in _VYKN_INFLECTIONS
            ):
                continue
            # Listed ob-/obo- lookalikes are lexical stems, not the prefix ob-;
            # obrús- instead has the one-letter prefix o- before brúsiť.
            if pfx == 'ob' and (
                reml.startswith(('av', 'áv', 'rús', 'úch'))
                or wl.startswith((
                    'obadiáš', 'obaj', 'obalamut', 'obál', 'obaľ', 'obec',
                    'obed', 'obeh', 'obel', 'obes', 'obeš', 'obet', 'obeť',
                    'obéz', 'obež', 'obidv', 'obiel', 'obiet', 'obieh', 'obieľ',
                    'obil', 'obit', 'oblúd', 'oboch', 'obol', 'oboč', 'obohac',
                    'obohat', 'obohať', 'oboj', 'obor',
                ))
                or wl in ('obom', 'oboma')
                or (wl.startswith('obal') and wl[4:] in _OBAL_INFLECTIONS)
                or (wl.startswith('ober') and wl[4:] in _OBER_INFLECTIONS)
            ):
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


def _strip_nested_prefix(
    w: str, outer_prefix: str | None = None
) -> tuple[str, str] | tuple[None, None]:
    wl = w.casefold()
    for pfx, roots in _NESTED_PREFIX_ROOTS:
        if pfx == 'do' and outer_prefix != 'ne':
            continue
        if any(wl.startswith(pfx + root) for root in roots):
            return w[:len(pfx)], w[len(pfx):]
    return None, None


#: An inflectional ending is short, and every one that follows a derivational
#: suffix begins with a vowel except the instrumental -mi. That is what lets a
#: suffix be found inside a word form and not only at its end: without it
#: chod·ník keeps its boundary but chod·ní·ky loses it.
_MAX_INFLECTION = 4
_CONSONANT_INITIAL_INFLECTIONS = ('mi',)
_NIK_DIMINUTIVE_INFLECTIONS = frozenset({
    'ek', 'ka', 'kami', 'koch', 'kom', 'kov', 'kovia', 'kovi', 'ku', 'ky',
})
_NIK_ADJECTIVE_INFLECTIONS = frozenset({
    'ka', 'ke', 'keho', 'kej', 'kemu', 'ki', 'kom', 'kou', 'ku', 'ky', 'kych',
    'kym', 'kymi',
})


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


def _is_prefixed_zna_verb(word: str) -> bool:
    """Whether prefixes reduce *word* to the finite ``zná`` form of znať."""
    remainder = word
    found_prefix = False
    while True:
        prefix, next_remainder = _strip_prefix(remainder)
        if prefix is None:
            return found_prefix and remainder.casefold() == 'zná'
        found_prefix = True
        remainder = next_remainder


def _is_d_final_past(word: str) -> bool:
    """Whether *word* is a d-final verb's past form, not a ``-dlo`` noun."""
    folded = word.casefold()
    if folded.startswith('ne'):
        folded = folded[2:]
    if not folded.endswith('lo'):
        return False
    stem = folded[:-2]
    return stem in _D_FINAL_PAST_STEMS or any(
        stem.endswith(root) and stem[:-len(root)] in _DLO_PAST_PREFIXES
        for root in _D_FINAL_PAST_ROOTS
    )


def _strip_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Return (stem, rest) if w carries a known consonant-initial suffix and
    the split produces a valid morpheme boundary. Else (None, None).

    Valid boundary: stem ≥3 chars and contains a vowel. A consonant-initial
    suffix remains a morpheme boundary even when the stem ends in a consonant
    cluster (ohyzd·ný, vlast·ný).
    """
    wl = w.lower()
    if wl.startswith('novocain') and wl[len('novocain'):] in _NOVOCAIN_INFLECTIONS:
        return None, None
    for suffix in _DLO_INFLECTIONS:
        if wl.endswith(suffix) and wl[:-len(suffix)] in _DLO_PARADIGM_STEMS:
            start = len(w) - len(suffix)
            return w[:start], w[start:]

    for suffix in _TINA_INFLECTIONS:
        if wl.endswith(suffix) and wl[:-len(suffix)] in _TINA_NUMERAL_STEMS:
            start = len(w) - len(suffix)
            return w[:start], w[start:]

    for suffix in _RHYTHMIC_SHORT_NY_SUFFIXES:
        if wl.endswith(suffix) and wl[:-len(suffix)] in _RHYTHMIC_SHORT_NY_STEMS:
            start = len(w) - len(suffix)
            return w[:start], w[start:]

    for suffix in _SHORT_COMPARATIVE_INFLECTIONS:
        stem = wl[:-len(suffix)]
        if wl.endswith(suffix) and stem.endswith('st') and any(c in _VOWELS_SK for c in stem):
            start = len(w) - len(suffix)
            return w[:start], w[start:]

    for suffix in _SKNUT_FINITE_SUFFIXES:
        stem = wl[:-len(suffix)]
        if wl.endswith(suffix) and stem.endswith(('sk', 'tk')) and any(c in _VOWELS_SK for c in stem):
            start = len(w) - len(suffix)
            return w[:start], w[start:]

    for alternant, endings in (
        ('níč', _NIK_DIMINUTIVE_INFLECTIONS),
        ('níc', _NIK_ADJECTIVE_INFLECTIONS),
    ):
        for tail in endings:
            marker = alternant + tail
            if wl.endswith(marker):
                start = len(w) - len(marker)
                stem = wl[:start]
                word_pfx = _strip_prefix(w)[0]
                stem_pfx = _strip_prefix(stem)[0]
                if (
                    len(stem) >= 3
                    and any(c in _VOWELS_SK for c in stem)
                    and (word_pfx is None or stem_pfx == word_pfx)
                ):
                    return w[:start], w[start:]

    for length, group in _SUFFIXES_BY_LEN:
        for tail_length in range(_MAX_INFLECTION + 1):
            start = len(w) - length - tail_length
            if start < 3 or wl[start:start + length] not in group:
                continue
            tail = wl[start + length:]
            matched = wl[start:start + length]
            if not _is_inflection(tail) and not (
                matched == 'liv' and tail.startswith('c') and _is_inflection(tail[1:])
            ):
                continue
            steml = wl[:start]
            if matched == 'ná' and _is_prefixed_zna_verb(w):
                continue
            if matched in _RHYTHMIC_SHORT_NIK:
                last_nucleus = next(
                    (
                        phoneme
                        for phoneme in reversed(split_into_phonemes(steml))
                        if phoneme in ALL_VOWELS
                        or phoneme in DIPHTHONGS
                        or phoneme in {'ŕ', 'ĺ'}
                    ),
                    None,
                )
                if last_nucleus not in _RHYTHMIC_LONG_NUCLEI:
                    continue
            if matched == 'stv' and steml[-1] in _VOWEL_LETTERS:
                continue
            if matched == 'ština' and steml[-1] in _VOWEL_LETTERS:
                continue
            if matched == 'tina' and not (steml.endswith('š') or steml in _TINA_NUMERAL_STEMS):
                continue
            if matched == 'dlo' and (
                steml.endswith('vie')
                or wl.startswith(('vychladlo', 'nevychladlo'))
                or _is_d_final_past(w)
            ):
                continue
            if wl[start:start + length] == 'kár' and not steml.endswith('st'):
                continue
            if wl[start:start + length] == 'liv' and steml == 'ošk':
                continue
            if not any(c in _VOWELS_SK for c in steml):
                continue
            # -sk- attaches to a consonant-final stem (Benát·ska, voj·sko). On
            # a vowel-final one the s belongs to the stem, not to a suffix:
            # mis·ka, bles·ky, po·ris·ko.
            # mis·ka, bles·ky, po·ris·ko. The one vowel-final stem that keeps
            # the boundary is one ending in a genuine hiatus: no suffix begins
            # with a vowel sequence, so lao·ský cannot be read any other way.
            if length == 2 and (steml[-1] in ALL_VOWELS or steml[-1] == 'ô'):
                genuine_hiatus = (
                    len(steml) >= 2
                    and steml[-2] in ALL_VOWELS
                    and steml[-2:] not in DIPHTHONGS
                )
                if not genuine_hiatus:
                    continue
            return w[:start], w[start:]
    return _strip_k_suffix(w)


def _strip_k_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Split the nominal suffix ·k· off a consonant-final stem.

    Without it a three-consonant cluster ending in tk is handed to section 4.3,
    which moves the point left of the whole tk- because tk- does open a Slovak
    word (tkáč): klien|tka. The suffix is a recognised morpheme boundary, so
    section 3 decides first and the result is klient|ka.

    A real ·sk· suffix is consumed by :func:`_strip_suffix` first. If that parse
    was rejected, ·k· may follow a sibilant-final noun stem (kolies·ko); its seam
    coincides with the regular two-consonant division in lookalikes such as bles·ky.
    """
    wl = w.lower()
    for tail_length in _K_SUFFIX_ENDING_LENGTHS:
        start = len(w) - 1 - tail_length
        if start < 3 or wl[start] != 'k':
            continue
        if wl[start + 1:] not in _SK_K_SUFFIX_ENDINGS:
            continue
        steml = wl[:start]
        if steml[-1] in ALL_VOWELS or steml[-1] == 'ô':
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
    """Split a bound compositional second member out of the middle of *w*."""
    wl = w.lower()
    for member in _SK_BOUND_SECOND_MEMBERS:
        seam = wl.find(member)
        if member in _BOUND_SECOND_MEMBER_HEADS and wl[:seam] not in _BOUND_SECOND_MEMBER_HEADS[member]:
            continue
        if seam < 3 or (
            wl[seam - 1] != _LINKING_VOWEL
            and not (member == 'hrad' and wl[:seam] == 'bele')
        ):
            continue
        if any(c in _VOWELS_SK for c in wl[:seam - 1]):
            return w[:seam], w[seam:]
    return None


def _strip_grammatical_suffix(w: str) -> tuple[str, str] | tuple[None, None]:
    """Split consonant-initial endings only from a consonant-final stem."""
    wl = w.lower()
    for sfx in _SK_GRAMMATICAL_SUFFIXES_CONS:
        if not wl.endswith(sfx) or len(w) <= len(sfx) + 1:
            continue
        stem = w[:-len(sfx)]
        steml = stem.lower()
        if (
            sfx in ('la', 'li', 'lo')
            and _strip_prefix(stem)[0] is None
            and not steml.endswith(('st', 'sk'))
            and not _is_d_final_past(w)
        ):
            continue
        if sfx == 'me' and steml.endswith('st'):
            continue
        # pomst-e is the dative/locative of pomsta, not an imperative poms-te.
        if sfx == 'te' and wl == 'pomste':
            continue
        if is_consonant(steml[-1]) and any(c in _VOWELS_SK for c in steml):
            return stem, w[-len(sfx):]
    return None, None


def _suffix_keeps_prefix(word: str, stem: str) -> bool:
    """Whether a suffix split keeps the outer and nested superlative prefixes."""
    word_pfx, word_rem = _strip_prefix(word)
    stem_pfx, stem_rem = _strip_prefix(stem)
    if word_pfx is None or stem_pfx != word_pfx:
        return False
    if word_pfx != 'naj':
        return True
    inner_pfx = _strip_prefix(word_rem)[0]
    return (
        inner_pfx is None
        or (stem_rem is not None and _strip_prefix(stem_rem)[0] == inner_pfx)
    )


def _is_nested_suppletive_ist_past(word: str) -> bool:
    """Whether two prefixes precede the past-tense šl-/išl- stem of ísť."""
    _, outer_rem = _strip_prefix(word)
    if outer_rem is None:
        return False
    inner_pfx, inner_rem = _strip_prefix(outer_rem)
    return (
        inner_pfx is not None
        and inner_rem.casefold() in {'šla', 'šli', 'šlo', 'išla', 'išli', 'išlo'}
    )


def get_morpheme_parts(word: str) -> list[str]:
    """Return the morphological units whose seams override phonotactics.

    Typographic hyphenation needs the same analysis as syllabification, but it
    applies a different rule inside each unit. Keeping the units explicit stops
    the PSP consonant-cluster rule from pulling a prefix-final consonant across
    a real morpheme boundary (``roz|ísť``, not ``ro|zísť``).
    """
    wl = word.lower()
    if wl.startswith('obvykl') and wl[6:] in _OBVYKL_INFLECTIONS:
        return [word[:2], word[2:5], word[5:]]

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

    if wl.startswith('naj') and any(part in wl[3:] for part in ('nejš', 'tejš')):
        return [word[:3], *get_morpheme_parts(word[3:])]

    comparative_n = wl.find('nejš')
    if comparative_n > 0:
        return [*get_morpheme_parts(word[:comparative_n]), word[comparative_n:]]

    comparative_t = wl.find('tejš')
    if comparative_t > 0:
        return [*get_morpheme_parts(word[:comparative_t]), word[comparative_t:]]

    stem, sfx = _strip_suffix(word)
    pfx, rem = _strip_prefix(word)
    suffix_keeps_prefix = (
        stem is not None
        and _suffix_keeps_prefix(word, stem)
        and (rem is None or _strip_nested_prefix(rem, pfx)[0] is None)
    )
    if stem is not None and (
        sfx.casefold().startswith(('ník', 'níc')) or suffix_keeps_prefix
    ):
        return [*get_morpheme_parts(stem), sfx]

    grammatical_stem, grammatical_sfx = _strip_grammatical_suffix(word)
    grammatical_suffix_keeps_prefix = (
        grammatical_stem is not None
        and _suffix_keeps_prefix(word, grammatical_stem)
        and not _is_nested_suppletive_ist_past(word)
        and (rem is None or _strip_nested_prefix(rem, pfx)[0] is None)
    )
    if grammatical_suffix_keeps_prefix:
        return [*get_morpheme_parts(grammatical_stem), grammatical_sfx]

    if pfx is not None:
        # The lexicalized po-|dotk- family keeps its outer seam in the contracted
        # masculine past without turning the remainder back into do-|tkol.
        if pfx == 'po' and rem.casefold() == 'dotkol':
            return [pfx, rem]
        nested_pfx, nested_rem = _strip_nested_prefix(rem, pfx)
        if nested_pfx is not None:
            return [pfx, nested_pfx, *get_morpheme_parts(nested_rem)]
        return [pfx, *get_morpheme_parts(rem)]

    if grammatical_stem is not None:
        return [*get_morpheme_parts(grammatical_stem), grammatical_sfx]

    for length, group in _COMPOSITA_BY_LEN:
        comp = wl[:length]
        if comp in group and len(word) > length + 2:
            rem = word[length:]
            if _licenses_compositum(comp, rem):
                return [
                    *get_morpheme_parts(word[:length]),
                    *get_morpheme_parts(rem),
                ]

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
    if wl.startswith('naj') and any(part in wl[3:] for part in ('nejš', 'tejš')):
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

    stem, sfx = _strip_suffix(word)
    pfx, rem = _strip_prefix(word)
    suffix_keeps_prefix = (
        stem is not None
        and _suffix_keeps_prefix(word, stem)
        and (rem is None or _strip_nested_prefix(rem, pfx)[0] is None)
    )
    if stem is not None and (
        sfx.casefold().startswith(('ník', 'níc')) or suffix_keeps_prefix
    ):
        return get_syllables(stem) + _syllabify_simple(sfx)

    grammatical_stem, grammatical_sfx = _strip_grammatical_suffix(word)
    grammatical_suffix_keeps_prefix = (
        grammatical_stem is not None
        and _suffix_keeps_prefix(word, grammatical_stem)
        and not _is_nested_suppletive_ist_past(word)
        and (rem is None or _strip_nested_prefix(rem, pfx)[0] is None)
    )
    if grammatical_suffix_keeps_prefix:
        return get_syllables(grammatical_stem) + _syllabify_simple(grammatical_sfx)

    # Prefix-aware split: recursively strip prefixes and syllabify remainder
    if pfx is not None:
        pfx_syls = _syllabify_simple(pfx)
        nested_pfx, nested_rem = _strip_nested_prefix(rem, pfx)
        if nested_pfx is not None:
            return pfx_syls + _syllabify_simple(nested_pfx) + get_syllables(nested_rem)
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

# The ethnonym Aleut and its derivatives pronounce e-u as two syllables.  It is
# the lexical exception to the otherwise reliable eu nucleus in learned loans.
_LEXICAL_FALLING_HIATUS = ('aleut',)
_LEXICAL_FALLING_DIPHTHONGS = (
    ('oppenheimer', 'ei'),
    ('sieur', 'ieu'),  # French [sjœʁ]: i is a glide, not a second nucleus.
)
_LEXICAL_FALLING_NUCLEI = frozenset(pair for _, pair in _LEXICAL_FALLING_DIPHTHONGS)

#: Written vowel graphemes, including the ones that are not phonological
#: diphthongs (ô is written as one grapheme; au, eu, ou are read as one).
_VOWEL_LIKE = (
    ALL_VOWELS | PRONOUNCED_FOREIGN_VOWELS | DIPHTHONGS | {'ô'}
    | _FALLING_DIPHTHONGS | _LEXICAL_FALLING_NUCLEI
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
            learned_ient = ph == 'ie' and phonemes[i + 1:i + 3] == ['n', 't']
            native_ieho = ph == 'ie' and phonemes[i + 1:] == ['h', 'o']
            if (
                not native_ieho
                and (
                    latin_neuter or after_long or learned_iakum
                    or learned_milliard or cia_instrumental or learned_ient
                )
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
    """Read falling vowel groups as one nucleus where pronunciation supports it.

    Two adjacent vowel letters are not by themselves two syllables (PSP §4.4).
    Slovak writes these three both ways: as one nucleus in a loan or in the
    instrumental (pau·za, pneu·ma·ti·ka, ru·kou) and as two across a seam
    (po|učiť, zne|užiť, tro|j·uholník). The morphology decides, so the seams are
    taken from :func:`get_morpheme_parts` and the sequence is merged everywhere
    else; the Latin endings of :data:`_LATIN_HIATUS_TAILS` are the one hiatus no
    seam marks.
    """
    wl = word.lower()
    falling_diphthongs = _FALLING_DIPHTHONGS | {
        pair for stem, pair in _LEXICAL_FALLING_DIPHTHONGS if wl.startswith(stem)
    }
    if not any(pair in wl for pair in falling_diphthongs):
        return phonemes

    seams = _seam_offsets(word)
    out: list[str] = []
    offset = index = 0
    while index < len(phonemes):
        phoneme = phonemes[index]
        following = phonemes[index + 1] if index + 1 < len(phonemes) else ''
        pair = phoneme + following
        if (
            pair in falling_diphthongs
            and (
                pair != 'ai'
                or phonemes[index + 2:index + 3] == ['l']
                or (wl.startswith('novocain') and offset == 5)
            )
            and offset + len(phoneme) not in seams
            and not wl.endswith(_LATIN_HIATUS_TAILS, offset)
            and not (
                pair == 'eu'
                and offset == 2
                and wl.startswith(_LEXICAL_FALLING_HIATUS)
            )
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
