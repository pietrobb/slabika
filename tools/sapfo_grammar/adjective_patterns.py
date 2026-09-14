# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
# Vendored from the sibling Sapfo project (sapfo/dictionaries/adjective_patterns.py) for build-time use
# by tools/build_composita.py only. Not part of the distributed package.
"""
Skloňovacie vzory adjektív - All 7 adjective declension patterns.

Each pattern has 7 paradigm rows × 6 case columns = 42 suffixes:
  Row 1: masculine animate (nom,gen,dat,acc,loc,ins) sg
  Row 2: masculine inanimate (nom,gen,dat,acc,loc,ins) sg
  Row 3: feminine (nom,gen,dat,acc,loc,ins) sg
  Row 4: neuter (nom,gen,dat,acc,loc,ins) sg
  Row 5: masculine animate plural (nom,gen,dat,acc,loc,ins)
  Row 6: masculine inanimate / feminine / neuter plural (nom,gen,dat,acc,loc,ins)
  Row 7: variant of row 6 (sometimes same)

Comparison patterns (stupňovacie vzory) for adjectives and adverbs: 7 patterns.

Source: Emil Páleš, Sapfo (1994), pp. 46-47
"""

# Adjective declension patterns
# Each pattern is a dict mapping (gender, animacy, number) -> 6 case suffixes
# Cases: nom, gen, dat, acc, loc, ins

ADJECTIVE_PATTERNS = {
    'pekný': {
        # Masculine animate singular
        ('muž', 'živ', 'sg'): ('ý', 'ého', 'ému', 'ého', 'om', 'ým'),
        # Masculine inanimate singular
        ('muž', 'neživ', 'sg'): ('ý', 'ého', 'ému', 'ý', 'om', 'ým'),
        # Feminine singular
        ('žen', None, 'sg'): ('á', 'ej', 'ej', 'ú', 'ej', 'ou'),
        # Neuter singular
        ('str', None, 'sg'): ('é', 'ého', 'ému', 'é', 'om', 'ým'),
        # Masculine animate plural
        ('muž', 'živ', 'pl'): ('í', 'ých', 'ým', 'ých', 'ých', 'ými'),
        # Masculine inanimate / Feminine / Neuter plural
        ('muž', 'neživ', 'pl'): ('é', 'ých', 'ým', 'é', 'ých', 'ými'),
        ('žen', None, 'pl'): ('é', 'ých', 'ým', 'é', 'ých', 'ými'),
        ('str', None, 'pl'): ('é', 'ých', 'ým', 'é', 'ých', 'ými'),
    },
    'krásny': {
        ('muž', 'živ', 'sg'): ('y', 'eho', 'emu', 'eho', 'om', 'ym'),
        ('muž', 'neživ', 'sg'): ('y', 'eho', 'emu', 'y', 'om', 'ym'),
        ('žen', None, 'sg'): ('a', 'ej', 'ej', 'u', 'ej', 'ou'),
        ('str', None, 'sg'): ('e', 'eho', 'emu', 'e', 'om', 'ym'),
        ('muž', 'živ', 'pl'): ('i', 'ych', 'ym', 'ych', 'ych', 'ymi'),
        ('muž', 'neživ', 'pl'): ('e', 'ych', 'ym', 'e', 'ych', 'ymi'),
        ('žen', None, 'pl'): ('e', 'ych', 'ym', 'e', 'ych', 'ymi'),
        ('str', None, 'pl'): ('e', 'ych', 'ym', 'e', 'ych', 'ymi'),
    },
    'cudzí': {
        ('muž', 'živ', 'sg'): ('í', 'ieho', 'iemu', 'ieho', 'om', 'ím'),
        ('muž', 'neživ', 'sg'): ('í', 'ieho', 'iemu', 'í', 'om', 'ím'),
        ('žen', None, 'sg'): ('ia', 'ej', 'ej', 'iu', 'ej', 'ou'),
        ('str', None, 'sg'): ('ie', 'ieho', 'iemu', 'ie', 'om', 'ím'),
        ('muž', 'živ', 'pl'): ('í', 'ích', 'ím', 'ích', 'ích', 'ími'),
        ('muž', 'neživ', 'pl'): ('ie', 'ích', 'ím', 'ie', 'ích', 'ími'),
        ('žen', None, 'pl'): ('ie', 'ích', 'ím', 'ie', 'ích', 'ími'),
        ('str', None, 'pl'): ('ie', 'ích', 'ím', 'ie', 'ích', 'ími'),
    },
    'rýdzi': {
        ('muž', 'živ', 'sg'): ('i', 'eho', 'emu', 'eho', 'om', 'im'),
        ('muž', 'neživ', 'sg'): ('i', 'eho', 'emu', 'i', 'om', 'im'),
        ('žen', None, 'sg'): ('a', 'ej', 'ej', 'u', 'ej', 'ou'),
        ('str', None, 'sg'): ('e', 'eho', 'emu', 'e', 'om', 'im'),
        ('muž', 'živ', 'pl'): ('i', 'ich', 'im', 'ich', 'ich', 'imi'),
        ('muž', 'neživ', 'pl'): ('e', 'ich', 'im', 'e', 'ich', 'imi'),
        ('žen', None, 'pl'): ('e', 'ich', 'im', 'e', 'ich', 'imi'),
        ('str', None, 'pl'): ('e', 'ich', 'im', 'e', 'ich', 'imi'),
    },
    'otcov': {
        ('muž', 'živ', 'sg'): ('', 'ho', 'mu', 'ho', 'om', 'ým'),
        ('muž', 'neživ', 'sg'): ('', 'ho', 'mu', '', 'om', 'ým'),
        ('žen', None, 'sg'): ('a', 'ej', 'ej', 'u', 'ej', 'ou'),
        ('str', None, 'sg'): ('o', 'ho', 'mu', 'o', 'om', 'ým'),
        ('muž', 'živ', 'pl'): ('i', 'ých', 'ým', 'ých', 'ých', 'ými'),
        ('muž', 'neživ', 'pl'): ('e', 'ých', 'ým', 'e', 'ých', 'ými'),
        ('žen', None, 'pl'): ('e', 'ých', 'ým', 'e', 'ých', 'ými'),
        ('str', None, 'pl'): ('e', 'ých', 'ým', 'e', 'ých', 'ými'),
    },
    'papagájí': {
        ('muž', 'živ', 'sg'): ('í', 'eho', 'emu', 'eho', 'om', 'im'),
        ('muž', 'neživ', 'sg'): ('í', 'eho', 'emu', 'í', 'om', 'im'),
        ('žen', None, 'sg'): ('a', 'ej', 'ej', 'u', 'ej', 'ou'),
        ('str', None, 'sg'): ('e', 'eho', 'emu', 'e', 'om', 'im'),
        ('muž', 'živ', 'pl'): ('í', 'ích', 'ím', 'ich', 'ich', 'imi'),
        ('muž', 'neživ', 'pl'): ('e', 'ích', 'ím', 'e', 'ich', 'imi'),
        ('žen', None, 'pl'): ('e', 'ích', 'ím', 'e', 'ich', 'imi'),
        ('str', None, 'pl'): ('e', 'ích', 'ím', 'e', 'ich', 'imi'),
    },
    'môj': {
        ('muž', 'živ', 'sg'): ('', 'ho', 'mu', 'ho', 'om', 'ím'),
        ('muž', 'neživ', 'sg'): ('', 'ho', 'mu', '', 'om', 'ím'),
        ('žen', None, 'sg'): ('a', 'ej', 'ej', 'u', 'ej', 'ou'),
        ('str', None, 'sg'): ('e', 'ho', 'mu', 'e', 'om', 'ím'),
        ('muž', 'živ', 'pl'): ('i', 'ich', 'im', 'ich', 'ich', 'imi'),
        ('muž', 'neživ', 'pl'): ('e', 'ich', 'im', 'e', 'ich', 'imi'),
        ('žen', None, 'pl'): ('e', 'ich', 'im', 'e', 'ich', 'imi'),
        ('str', None, 'pl'): ('e', 'ich', 'im', 'e', 'ich', 'imi'),
    },
}

# Comparison patterns for adjectives and adverbs (stupňovacie vzory)
# Format: pattern_name -> alternations applied to form comparative
COMPARISON_PATTERNS = {
    'nový': {
        'alternations': [],
        'comparative_suffix': 'ší',  # nový -> novší -> ... actually novší is wrong
        'description': 'basic comparison, no alternation',
    },
    'krátky': {
        'alternations': ['-k', '≥'],  # remove -k, shorten vowel
        'description': 'remove -k, shorten: krátky -> kratší',
    },
    'vysoký': {
        'alternations': ['-ok', 's/š', 'z/ž'],
        'description': 'remove -ok, consonant change: vysoký -> vyšší',
    },
    'ďaleký': {
        'alternations': ['-ek'],
        'description': 'remove -ek: ďaleký -> ďalší',
    },
    'biely': {
        'alternations': ['≥'],  # shorten vowel
        'description': 'shorten: biely -> belší',
    },
    'belasý': {
        'alternations': ['+ej'],
        'description': 'add -ej: belasý -> belasejší (adjectival comparison via -ejší)',
    },
    'supletívne': {
        'alternations': [],
        'description': 'supletive comparison (dobrý->lepší, zlý->horší, veľký->väčší)',
    },
}

# Supletive comparison forms
SUPLETIVE_COMPARISONS = {
    'dobrý': ('lepší', 'najlepší'),
    'zlý': ('horší', 'najhorší'),
    'veľký': ('väčší', 'najväčší'),
    'malý': ('menší', 'najmenší'),
    'pekný': ('krajší', 'najkrajší'),
    'vysoký': ('vyšší', 'najvyšší'),
    'nízky': ('nižší', 'najnižší'),
    'dlhý': ('dlhší', 'najdlhší'),
    'široký': ('širší', 'najširší'),
    'úzky': ('užší', 'najužší'),
    'hlboký': ('hlbší', 'najhlbší'),
    'blízky': ('bližší', 'najbližší'),
    'krátky': ('kratší', 'najkratší'),
    'tenký': ('tenší', 'najtenší'),
}

# Adverb formation: adjective root + adverb suffix
# The adverb positive is formed by adding a suffix to the adjective root
ADVERB_POSITIVE_SUFFIXES = {
    'pekný': 'e',    # pekn + e = pekne
    'krásny': 'e',   # krásn + e = krásne
    'cudzí': 'o',    # cudz + o = cudzo (approximately)
}

# Patterns that palatalize root-final consonant (d→ď, t→ť, n→ň, l→ľ)
# before back-vowel suffixes (-om loc.sg, -ou ins.sg.fem).
# Applies to possessive adjective patterns derived from nouns.
ADJ_PALATALIZATION_PATTERNS = {'cudzí', 'rýdzi', 'papagájí'}

# Adjective case names
ADJ_CASES = ['nom', 'gen', 'dat', 'acc', 'loc', 'ins']
