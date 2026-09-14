# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Vendored from the sibling Sapfo project (sapfo/dictionaries/verb_patterns.py) for build-time use
# by tools/build_composita.py only. Not part of the distributed package.
"""
Časovacie vzory slovies - All 24 verb conjugation patterns.

Each pattern is defined by 7 key morphemes (sedmica kľúčových morfém):
  infinitive suffix, l-participle suffix, n/t-participle suffix,
  v-participle suffix, present stem suffix, imperative suffix, transgressive suffix

These 7 forms, together with the infinitive stem and present stem,
provide enough information to generate all ~247 verb forms.

Source: Emil Páleš, Sapfo (1994), p. 45
"""

# Verb conjugation patterns
# Format: pattern_name -> (inf_suffix, l_part, v_part, nt_part, pres_stem, imper, transgr)
# The 7 key morphemes define each pattern
# Note: v_part and nt_part are at indices 2 and 3 respectively
VERB_PATTERNS = {
    'chytať':   ('a', 'a', 'av', 'an', 'á', 'aj', 'ajú'),
    'klaňať':   ('a', 'a', 'av', 'an', 'ia', 'aj', 'ajú'),
    'čítať':    ('a', 'a', 'av', 'an', 'a', 'aj', 'ajú'),
    'rozumieť': ('ie', 'e', 'ev', 'en', 'ie', 'ej', 'ejú'),
    'niesť':    ('', 'o', '', 'en', 'ie', '', 'ú'),
    'viesť':    ('', 'o', '', 'en', 'ie', '', 'ú'),
    'hynúť':    ('ú', 'u', 'uv', 'ut', 'ie', '', 'ú'),
    'pracovať': ('a', 'a', 'av', 'an', 'e', '', 'ú'),
    'robiť':    ('i', 'i', 'iv', 'en', 'í', '', 'ia'),
    'kúpiť':    ('i', 'i', 'iv', 'en', 'i', '', 'ia'),
    'vidieť':   ('ie', 'e', 'iv', 'en', 'í', '', 'ia'),
    'kričať':   ('a', 'a', 'av', 'an', 'í', '', 'ia'),
    'trieť':    ('ie', 'e', 'ev', 'et', 'ie', 'i', 'ú'),
    'brať':     ('a', 'a', 'av', 'an', 'ie', '', 'ú'),
    'česať':    ('a', 'a', 'av', 'an', 'e', '', 'ú'),
    'chudnúť':  ('ú', 'o', 'uv', 'ut', 'e', 'i', 'ú'),
    'vládnuť':  ('u', 'o', 'uv', 'ut', 'e', 'i', 'u'),
    'žuť':      ('', '', 'v', 't', 'e', '', 'ú'),
    'kliať':    ('', '', 'v', 't', 'e', '', 'ú'),
    'piť':      ('', '', 'v', 't', 'e', '', 'ú'),
    'žať':      ('a', 'a', 'av', 'at', 'e', 'i', 'ú'),
    'päť':      ('ä', 'ä', 'äv', 'ät', 'e', 'i', 'ú'),
    'kresliť':  ('i', 'i', 'iv', 'en', 'í', 'i', 'ia'),
    'krášliť':  ('i', 'i', 'iv', 'en', 'i', 'i', 'ia'),
}

# Verb stem alternation types (A1-A7)
VERB_ALTERNATIONS = {
    'chytať':   [],
    'klaňať':   ['A5'],
    'čítať':    [],
    'rozumieť': ['≥'],  # skrátenie
    'niesť':    ['A6'],
    'viesť':    ['A2', 'A5', 'A6'],
    'hynúť':    ['A5'],
    'pracovať': [],
    'robiť':    [],
    'kúpiť':    [],
    'vidieť':   ['A5'],
    'kričať':   [],
    'trieť':    ['A5'],
    'brať':     ['A5'],
    'česať':    ['A1', 'A7'],
    'chudnúť':  ['A3'],
    'vládnuť':  ['A3'],
    'žuť':      [],
    'kliať':    [],
    'piť':      ['A4'],
    'žať':      [],
    'päť':      [],
    'kresliť':  [],
    'krášliť':  [],
}

# Verb stem alternation definitions
STEM_ALTERNATION_RULES = {
    # A1: inf.stem/pres.stem consonant alternation
    'A1': {
        'description': 'inf.kmeň/préz.kmeň consonant alternation',
        'pairs': {
            't': 'c', 'c': 't',
            'd': 'dz', 'dz': 'd',
            'k': 'č', 'č': 'k',
            's': 'š', 'š': 's',
            'z': 'ž', 'ž': 'z',
            'ch': 'š',
            'sl': 'šľ',
        },
        'examples': ['česať/češe', 'plakať/plače', 'blikotať/blikoce'],
    },
    # A2: inf.stem/pres.stem/l-participle alternation
    'A2': {
        'description': 'inf.kmeň/préz.kmeň/l-príčastie alternation',
        'pairs': {
            's': 'd', 'd': 's',
            's': 'ť', 'ť': 's',
            'c': 'č', 'č': 'c',  # c/č/k
            'c': 'k', 'k': 'c',
            'z': 'ž', 'ž': 'z',  # ž/h
            'z': 'h', 'h': 'z',
        },
        'examples': ['tĺcť/tlčie/tĺkol', 'húsť/hudie/húdol'],
    },
    # A3: deletion of derivational morpheme -n- in l-participle
    'A3': {
        'description': 'Vypustenie derivačnej morfémy -n- v l-príčastí',
        'change': 'n/ø',
        'examples': ['chudnúť/chudol', 'vládnuť/vládol'],
    },
    # A4: deletion of interfixed morpheme -j- in imperative
    'A4': {
        'description': 'Vypustenie interfigovanej morfémy -j- v imperatíve',
        'change': 'j/ø',
        'examples': ['pijeť/pi'],
    },
    # A5: change of dorsal consonant to lingual
    'A5': {
        'description': 'Zmena dorzálnej konsonanty na lingválnu',
        'pairs': {
            'd': 'ď', 'ď': 'd',
            't': 'ť', 'ť': 't',
            'n': 'ň', 'ň': 'n',
            'l': 'ľ', 'ľ': 'l',
        },
        'examples': ['hynúť/hyň'],
    },
    # A6: formation of gerund and l/t-participle from present stem
    'A6': {
        'description': 'Tvorenie gerundia, l- a t-príčastia od préz. kmeňa',
        'examples': ['niesť/nesúc/nesený'],
    },
    # A7: formation of transgressive from both stems
    'A7': {
        'description': 'Tvorenie prechodníka od oboch kmeňov',
        'examples': [],
    },
}

# Reflexivity options
REFLEXIVITY = {'#': 'nezvratné', 'sa': 'zvratné_sa', 'si': 'zvratné_si'}

# Aspect options
ASPECT = {'dok': 'dokonavé', 'nedok': 'nedokonavé', 'oboj': 'obojvidové'}

# Verb form types and their stem requirements
VERB_FORMS = {
    'infinitív':    'inf_kmeň',
    'l-príčastie':  'inf_kmeň',
    'nt-príčastie': 'inf_kmeň',
    'v-príčastie':  'préz_kmeň',
    'préz_indikatív': 'préz_kmeň',
    'imperatív':    'préz_kmeň',
    'prechodník':   'préz_kmeň',
    'gerundium':    'inf_kmeň',
    'c-príčastie':  'préz_kmeň',
}

# Present indicative suffixes by person/number
PRESENT_SUFFIXES = {
    # Pattern groups based on 3rd person plural ending
    'ajú': {  # Type 1: chytať, klaňať, čítať
        (1, 'sg'): 'ám', (2, 'sg'): 'áš', (3, 'sg'): 'á',
        (1, 'pl'): 'áme', (2, 'pl'): 'áte', (3, 'pl'): 'ajú',
    },
    'ejú': {  # Type 2: rozumieť
        (1, 'sg'): 'iem', (2, 'sg'): 'ieš', (3, 'sg'): 'ie',
        (1, 'pl'): 'ieme', (2, 'pl'): 'iete', (3, 'pl'): 'ejú',
    },
    'ú': {  # Type 3: niesť, viesť, brať, česať, etc.
        (1, 'sg'): 'iem', (2, 'sg'): 'ieš', (3, 'sg'): 'ie',
        (1, 'pl'): 'ieme', (2, 'pl'): 'iete', (3, 'pl'): 'ú',
    },
    'ia': {  # Type 4: robiť, kúpiť, vidieť, kričať
        (1, 'sg'): 'ím', (2, 'sg'): 'íš', (3, 'sg'): 'í',
        (1, 'pl'): 'íme', (2, 'pl'): 'íte', (3, 'pl'): 'ia',
    },
    'ujú': {  # Type 5: pracovať (pres_stem ends in -uj)
        (1, 'sg'): 'em', (2, 'sg'): 'eš', (3, 'sg'): 'e',
        (1, 'pl'): 'eme', (2, 'pl'): 'ete', (3, 'pl'): 'ú',
    },
}

# L-participle suffixes (for past tense)
L_PARTICIPLE_SUFFIXES = {
    ('muž', 'sg'): '',     # robil
    ('žen', 'sg'): 'a',    # robila
    ('str', 'sg'): 'o',    # robilo
    ('muž', 'pl'): 'i',    # robili
    ('žen', 'pl'): 'i',    # robili (same as masc pl in modern Slovak)
    ('str', 'pl'): 'i',    # robili
}

# Imperative suffixes
IMPERATIVE_SUFFIXES = {
    (2, 'sg'): '',          # rob! / chytaj!
    (1, 'pl'): 'me',        # robme! / chytajme!
    (2, 'pl'): 'te',        # robte! / chytajte!
}
