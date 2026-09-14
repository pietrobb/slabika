"""Generate the compositional first-member inventory from the Sapfo lexicon.

The inventory of first members of Slovak determinative compounds used to be a
hand-written list of 176 items inside ``syllabify.py``. A hand-written list can
only ever divide the compounds somebody remembered to type in: ``hnedo`` was
there but ``modro`` was not, so ``bledo|modrý`` was analysed and ``modro|sivý``
was not, although the two are built by the same rule.

The first member of such a compound is the adverbial stem of the first word:
``modro``, ``sivo``, ``žlto`` — the very form the ``adverbs`` table of the
lexicon already stores as ``root + positive_suffix``. Adjective roots supply the
same stem for the adjectives whose adverb the lexicon has not recorded, and noun
lemmas in ``-o`` supply the ones that are nouns to begin with (``slovo·tvorný``,
``zlato·hnedý``, ``striebro·biely``). Entries marked ``source = 'snk'`` are
excluded: the distributed artifact is built only from the project's manual and
independently classified lexicon entries plus the curated lists below.

So the inventory is generated, and the only hand-written part left is the
residue the lexicon cannot know: the international prefixoids (``geo``, ``hydro``,
``pseudo``) and the numerals (``troj``, ``tisíc``), which are not Slovak adverbs.

Run:  python tools/build_composita.py
Out:  src/slabika/data/composita.json
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

LEXICON = Path(__file__).resolve().parents[2] / "Sapfo/sapfo/data/sapfo_lexicon.db"
CORPUS = (
    Path(__file__).resolve().parents[1]
    / "tests/data/translatemaster_hyphenation_working.sqlite"
)
OUT = Path(__file__).resolve().parents[1] / "src/slabika/data/composita.json"

# Soft consonants after which the linking vowel is -e, not -o (srdce·rvúci).
SOFT_FINALS = frozenset("cčšžďťňjľ")

# First members no Slovak paradigm can generate, so they stay written out.
#
# They fall into two kinds, and the kinds behave differently. A numeral or a
# borrowed prefixoid is a short cited string that turns up inside words it has
# nothing to do with — mini in minister, tri in roztriešti — so it may only
# divide the compounds somebody vouched for, which is what the guards in
# syllabify.py do. A native bound stem (samo, boja, matko) is an ordinary
# Slovak first member that the lexicon merely fails to list as an adverb, and
# it carries no such risk.
CURATED_NUMERALS = [
    # numerals and quantifiers
    'deväťdesiat', 'osemdesiat', 'sedemdesiat', 'šesťdesiat', 'päťdesiat',
    'štyridsať', 'tridsať', 'dvadsať',
    'devätnásť', 'osemnásť', 'sedemnásť', 'šestnásť', 'pätnásť',
    'štrnásť', 'trinásť', 'dvanásť', 'jedenásť',
    'niekoľko', 'deväť', 'sedem', 'osem', 'šesť', 'šest', 'päť',
    'troj', 'tri', 'dve', 'štyri', 'sto', 'tisíc', 'viac', 'veľa', 'veľko', 'veľ',
    # international prefixoids
    'video', 'geo', 'teo', 'bio', 'foto', 'auto', 'euro', 'etyl', 'steto',
    'agro', 'agri', 'astro', 'aero', 'anti', 'archi',
    'hydro', 'termo', 'elektro', 'mikro', 'makro', 'mono', 'neuro', 'orto',
    'poly', 'pseudo', 'semi', 'hemi', 'kvazi', 'inter', 'intra', 'extra',
    'ultra', 'super', 'hyper', 'meta', 'multi', 'mini', 'maxi', 'gramo',
    'choreo', 'kozmo', 'leuko', 'mili', 'stereo', 'rádio',
]

CURATED_NATIVE = [
    # bound native stems that are not free words
    'seba', 'zeme', 'vrti', 'brati', 'krvi', 'bohu', 'boja', 'bože', 'ducha',
    'kníh', 'mast', 'kvart', 'krato',
    # oblique noun stems: the lexicon stores the lemma (matka, mravec, viera),
    # the compound is built on the stem plus the linking vowel (matko·vrah)
    'blesko', 'boho', 'brato', 'chorobo', 'chválo', 'hromo', 'hrôzo', 'juho',
    'krepo', 'krvo', 'krížo', 'kušo', 'luko', 'lyro', 'medo', 'melo', 'modlo',
    'mravo', 'mrcho', 'mrkvo', 'pravdo', 'rodo', 'rudo', 'stredo', 'viero',
    'ľano', 'ľubo', 'ľudo', 'fajn',
    'formo', 'matko', 'miero', 'obrazo', 'otco', 'samo', 'slabiko', 'tóno',
    'vzducho', 'všetko', 'zemo', 'zázrako', 'čino', 'žlčo',
    'svetlozlato', 'tmavozlato',
]

# Productive seams attested by this project's own corpus. Human-confirmed
# families and unchanged legacy behavior are kept as a small explicit residue;
# unlabelled surface forms are never treated as if they determined morphology.
CURATED_CORPUS_FIRST_MEMBERS = {
    'biblio': 'noun stem',
    'cito': 'noun stem',
    'demo': 'noun',
    'denno': 'adjective',
    'horno': 'adjective',
    'karto': 'noun stem',
    'kilo': 'noun',
    'krypto': 'noun stem',
    'latinsko': 'adjective',
    'lexiko': 'noun stem',
    'logo': 'noun',
    'mimo': 'adverb',
    'nízko': 'adverb',
    'oceáno': 'noun stem',
    'paro': 'noun stem',
    'potravinársko': 'adjective',
    'rovno': 'adverb',
    'scéno': 'noun stem',
    'sedmo': 'noun stem',
    'severo': 'noun stem',
    'sírovo': 'adjective',
    'sväto': 'adverb',
    'tmavo': 'adverb',
    'tučno': 'adjective',
    'vnútro': 'noun',
    'vše': 'adverb',
    'žlto': 'adverb',
}

# The value is the runtime evidence kind, not the provenance. Every item below
# is backed by this project's corpus and preserves a tested or unchanged family;
# none is copied from an external lexical inventory.
CURATED_CORPUS_HEADS = {
    'americk': 'root',
    'bdel': 'root',
    'chcen': 'root',
    'chlad': 'lemma',
    'chvost': 'lemma',
    'egyptsk': 'root',
    'frekvenčn': 'root',
    'graf': 'lemma',
    'gram': 'lemma',
    'hriešn': 'root',
    'kmeň': 'lemma',
    'kmeňov': 'root',
    'krádež': 'lemma',
    'kráska': 'lemma',
    'kvalitn': 'root',
    'oranžov': 'root',
    'plavba': 'lemma',
    'plavebn': 'root',
    'pluk': 'lemma',
    'prebud': 'verb',
    'priemyseln': 'root',
    'prítomn': 'root',
    'slovce': 'lemma',
    'smern': 'root',
    'spokojn': 'root',
    'statn': 'root',
    'strann': 'root',
    'stroj': 'lemma',
    'stvárn': 'verb',
    'triedn': 'root',
    'tropick': 'root',
    'tvár': 'lemma',
    'ušn': 'root',
    'zbožn': 'root',
    'zrod': 'lemma',
    'zvol': 'verb',
    'ázijsk': 'root',
    'éterick': 'root',
    'éterov': 'root',
    'štajersk': 'root',
    'šľacht': 'verb',
    'šľachtic': 'lemma',
    'šľachtick': 'root',
}


# ---------------------------------------------------------------- own corpus
# The Sapfo branch above can only see what the lexicon records. The project's
# own word list is the other witness, and the only one whose provenance is
# entirely ours, so the same inventory is derived from it a second time — from
# surface forms alone, by asking which paradigm the corpus actually attests.
#
# The evidence has to be paradigmatic rather than a suffix match, because a
# suffix match reads doba as an adjective root dob- and osla as a lemma of its
# own. Each branch therefore demands the endings that only its own paradigm
# produces, and the noun branch additionally demands endings no feminine
# paradigm has, or every genitive plural (škár of škára) becomes a lemma.

#: Endings no other part of speech carries, so their presence identifies an
#: adjective root rather than a noun that happens to end in -ý.
_ADJECTIVE_WITNESSES = ('ého', 'ému', 'ých', 'ými', 'ejší', 'ejšia', 'ejšie')

#: What an infinitive is allowed to end in. A bare -ť is not enough: niť and
#: sieť end in it and are nouns.
_INFINITIVE_SUFFIXES = (
    'ovať', 'núť', 'ieť', 'ať', 'iť', 'yť', 'úť', 'sť', 'zť', 'cť',
)

#: Case endings of the masculine and neuter paradigms. A consonant-final string
#: is only a lemma if the corpus attests two of these: škár takes škára, škáry,
#: škáre — all forms of the feminine škára, none of them evidence of a lemma
#: škár, and without this the inventory heads svätoškár·sku with the genitive
#: plural of a crack.
_MASCULINE_WITNESSES = frozenset({'om', 'ovi', 'och', 'ov', 'mi', 'u'})

#: Homographs the evidence cannot settle, because the collision is not with
#: another analysis of the same word but with a different word:
#:   oslo-  is a legitimate first member of osla, and every word it divides is
#:          a form of osloviť, where the o- is a prefix (oslo·vi·la, PSP: a
#:          single letter may not be left behind).
#:   naše-  is the possessive pronoun. Pronouns are a closed class; the noun
#:          branch reads naša as a lemma and na·še·tre·né follows.
_CORPUS_FIRST_MEMBER_COLLISIONS = frozenset({'oslo', 'naše'})

_VOWEL_LETTERS = frozenset('aáäeéiíoóuúyýô')


def _corpus_forms() -> set[str]:
    """Every lowercase alphabetic form in the project's own corpus."""
    db = sqlite3.connect(f"file:{CORPUS.as_posix()}?mode=ro", uri=True)
    forms = {
        word.lower()
        for (word,) in db.execute("select form from forms")
        if word.isalpha() and word[0].islower()
    }
    db.close()
    return forms


def _noun_paradigm(word: str, corpus: set[str]) -> tuple[str, bool]:
    """Return (stem, is_a_lemma) for *word* read as a noun."""
    if word.endswith('a'):
        stem, endings, required = word[:-1], ('y', 'e', 'i', 'u', 'ou', 'ách', 'ám', 'ami'), None
    elif word.endswith('o'):
        stem, endings, required = word[:-1], ('a', 'u', 'e', 'om', 'á', 'ám', 'ách', 'ami'), None
    elif word.endswith('e'):
        stem, endings, required = word[:-1], ('a', 'u', 'om', 'ia', 'iam', 'iach', 'ami'), None
    elif word[-1] not in _VOWEL_LETTERS:
        stem = word
        endings = ('a', 'u', 'e', 'om', 'ovi', 'y', 'i', 'och', 'ov', 'ami', 'mi')
        required = _MASCULINE_WITNESSES
    else:
        return '', False
    attested = {ending for ending in endings if stem + ending in corpus}
    enough = len(attested) >= 3 and (
        required is None or len(attested & required) >= 2
    )
    return stem, enough


def corpus_inventory() -> tuple[dict[str, str], dict[str, str]]:
    """Derive first members and heads from this project's own corpus alone."""
    corpus = _corpus_forms()

    adjective_roots = {
        word[:-1]
        for word in corpus
        if word.endswith(('ý', 'í')) and len(word) >= 4 and len(word) - 1 >= 3
        and any(word[:-1] + witness in corpus for witness in _ADJECTIVE_WITNESSES)
    }
    verb_stems = {
        word[:-1]
        for word in corpus
        if word.endswith('ť') and len(word) >= 5
        and word.endswith(_INFINITIVE_SUFFIXES)
        and any(word[:-1] + tail in corpus for tail in ('l', 'la', 'li'))
    }
    noun_lemmas: dict[str, str] = {}
    for word in corpus:
        # An adjective form is not a noun lemma (krásne is not a thing), and
        # neither is an l-participle (viedol is not a lemma of viedl-).
        if len(word) < 4 or word[:-1] in adjective_roots:
            continue
        if word in verb_stems or word[:-1] in verb_stems:
            continue
        stem, is_lemma = _noun_paradigm(word, corpus)
        if is_lemma and len(stem) >= 3:
            noun_lemmas[word] = stem

    first: dict[str, str] = {}

    def put(member: str, source: str) -> None:
        if (
            len(member) >= 3
            and member.isalpha()
            and member not in _CORPUS_FIRST_MEMBER_COLLISIONS
        ):
            first.setdefault(member, source)

    for root in sorted(adjective_roots):
        put(root + 'o', 'adjective')
        if root[-1] in SOFT_FINALS:
            put(root + 'e', 'adjective')
    for word in sorted(corpus):
        if len(word) >= 4 and word[-1] in 'oe' and word[:-1] in adjective_roots:
            put(word, 'adverb')
    for stem in sorted(noun_lemmas.values()):
        # The -o- of otravo·val is not a linking vowel but the -ova- of
        # otravovať, and the corpus says so: where the stem forms a verb in
        # -ovať, every word the member would divide is that verb's paradigm
        # (kormidlo·val, komando|vali), so the member is refused outright.
        if stem + 'ovať' in corpus:
            continue
        put(stem + ('e' if stem[-1] in SOFT_FINALS else 'o'), 'noun stem')

    heads: dict[str, str] = {}
    for root in adjective_roots:
        if len(root) >= 3:
            heads[root] = 'root'
    for stem in verb_stems:
        if len(stem) >= 4:
            heads[stem] = 'verb'
    for lemma in noun_lemmas:
        if len(lemma) >= 4:
            heads[lemma] = 'lemma'
    return first, heads


def build() -> dict:
    db = sqlite3.connect(f"file:{LEXICON.as_posix()}?mode=ro", uri=True)

    first: dict[str, str] = {}

    def put(stem: str, source: str) -> None:
        if len(stem) >= 3 and stem.isalpha():
            first.setdefault(stem.lower(), source)

    # 1. attested adverbs — the canonical shape of a first member
    for root, suffix in db.execute(
        "select root, positive_suffix from adverbs "
        "where root <> '' and source <> 'snk'"
    ):
        if suffix in ("o", "e"):
            put(root + suffix, "adverb")
        elif not suffix and root[-1:] in ("o", "e"):
            put(root, "adverb")

    # 2. adjective roots — the adverb the lexicon has not recorded is still
    #    formed the same way, and this is what makes the rule generative
    for (root,) in db.execute(
        "select root from adjectives where root <> '' and source <> 'snk'"
    ):
        put(root + "o", "adjective")
        if root[-1] in SOFT_FINALS:
            put(root + "e", "adjective")

    # 3. noun lemmas that already end in the linking vowel
    for (word,) in db.execute(
        "select word from nouns where word <> '' and source <> 'snk'"
    ):
        if word[-1:] in ("o", "e") and len(word) >= 4 and word[0].islower():
            put(word, "noun")

    # 4. every other noun lemma, through its stem and the linking vowel. A
    #    compound is not built on the lemma but on the stem: voda gives vodo-,
    #    ruka ruko-, srdce srdce-. Without this branch the inventory knew žlto
    #    (from the adjective žltý) and not vodo, so which compounds divided
    #    depended on whether the first word happened to be an adjective.
    for (word,) in db.execute(
        "select word from nouns where word <> '' and source <> 'snk'"
    ):
        if len(word) < 3 or not word.isalpha() or not word[0].islower():
            continue
        stem = word[:-1] if word[-1] in "aáoe" else word
        if len(stem) < 3:
            continue
        put(stem + ("e" if stem[-1] in SOFT_FINALS else "o"), "noun stem")

    for stem in CURATED_NATIVE:
        put(stem, "native")
    for stem, kind in CURATED_CORPUS_FIRST_MEMBERS.items():
        put(stem, kind)
    for stem in CURATED_NUMERALS:
        put(stem, "cited")

    # ------------------------------------------------------------------ heads
    # A second member has to be headed by a real lemma; an inflectional tail
    # such as -vých or -valo is not a second member (jahodo|vých is no compound).
    # An adjective or adverb root is the canonical second member of a
    # determinative compound, and the shortest ones are the commonest words in
    # the language: siv-, žlt-, biel-. They stay at three letters.
    # A verb stem of the same length is not a second member but an ending in
    # disguise -- -ľnú is ľnúť and -kli is kliať, which is what makes
    # nepohnute|ľnú and zase|kli look like compounds. Those need four.
    # A root and a lemma are not the same kind of evidence. A lemma is a word
    # and may stand as the whole second member (samo·vrah, žlto·chvost); a root
    # never appears bare -- siv is not a word, sivý is -- so a bare root is an
    # ending in disguise, which is what makes kormidlo·val look like a compound.
    # Lemma wins when a string is both.
    heads: dict[str, str] = {}
    for query, floor, kind in (
        ("select root from adjectives where root <> '' and source <> 'snk'", 3, "root"),
        ("select root from adverbs where root <> '' and source <> 'snk'", 3, "root"),
        ("select word from nouns where word <> '' and source <> 'snk'", 4, "lemma"),
        ("select lemma from pales_kmen where lemma <> ''", 4, "lemma"),
        ("select inf_stem from verbs where inf_stem <> '' and source <> 'snk'", 4, "verb"),
    ):
        for (w,) in db.execute(query):
            # A proper name is not a second member of a determinative
            # compound; without this, Brit makes cele|brite out of celebrita.
            if len(w) < floor or not w.isalpha() or not w[0].islower():
                continue
            if kind == "verb":
                # A verb stem carries a lemma's weight -- daktylo·skop, samo·-
                # zvolený -- but it is not a word of its own, so it is recorded
                # as its own kind. Only a word already known as a lemma outranks
                # it; a bare root does not.
                if heads.get(w.lower()) != "lemma":
                    heads[w.lower()] = kind
            elif kind == "lemma" or w.lower() not in heads:
                heads[w.lower()] = kind

    for head, kind in CURATED_CORPUS_HEADS.items():
        if kind == "lemma" or head not in heads:
            heads[head] = kind

    # The corpus branch runs last and never overrules the lexicon: a first
    # member the lexicon already classified keeps its own source label, because
    # the label is what the runtime reads to decide how much a member may
    # license. A lemma is the one exception — a string the corpus attests as a
    # whole word is a word, whichever table guessed at a root before it.
    corpus_first, corpus_heads = corpus_inventory()
    for member, source in corpus_first.items():
        put(member, source)
    for head, kind in corpus_heads.items():
        if kind == "lemma" or head not in heads:
            heads[head] = kind

    db.close()
    return {
        "note": "generated from non-SNK Sapfo entries and the local project corpus",
        "corpus_first_members": sorted(
            set(CURATED_CORPUS_FIRST_MEMBERS) | (set(corpus_first) & set(first))
        ),
        "corpus_heads": sorted(
            set(CURATED_CORPUS_HEADS) | (set(corpus_heads) & set(heads))
        ),
        "first_members": {k: first[k] for k in sorted(first)},
        "heads": {k: heads[k] for k in sorted(heads)},
    }


def main() -> None:
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    counts: dict[str, int] = {}
    for source in data["first_members"].values():
        counts[source] = counts.get(source, 0) + 1
    print(f"first members {len(data['first_members'])}  {counts}")
    print(f"heads         {len(data['heads'])}")
    print(f"written       {OUT}  ({OUT.stat().st_size / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
