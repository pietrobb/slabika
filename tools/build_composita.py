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
``zlato·hnedý``, ``striebro·biely``).

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


def build() -> dict:
    db = sqlite3.connect(f"file:{LEXICON.as_posix()}?mode=ro", uri=True)

    first: dict[str, str] = {}

    def put(stem: str, source: str) -> None:
        if len(stem) >= 3 and stem.isalpha():
            first.setdefault(stem.lower(), source)

    # 1. attested adverbs — the canonical shape of a first member
    for root, suffix in db.execute(
        "select root, positive_suffix from adverbs where root <> ''"
    ):
        if suffix in ("o", "e"):
            put(root + suffix, "adverb")
        elif not suffix and root[-1:] in ("o", "e"):
            put(root, "adverb")

    # 2. adjective roots — the adverb the lexicon has not recorded is still
    #    formed the same way, and this is what makes the rule generative
    for (root,) in db.execute("select root from adjectives where root <> ''"):
        put(root + "o", "adjective")
        if root[-1] in SOFT_FINALS:
            put(root + "e", "adjective")

    # 3. noun lemmas that already end in the linking vowel
    for (word,) in db.execute("select word from nouns where word <> ''"):
        if word[-1:] in ("o", "e") and len(word) >= 4 and word[0].islower():
            put(word, "noun")

    # 4. every other noun lemma, through its stem and the linking vowel. A
    #    compound is not built on the lemma but on the stem: voda gives vodo-,
    #    ruka ruko-, srdce srdce-. Without this branch the inventory knew žlto
    #    (from the adjective žltý) and not vodo, so which compounds divided
    #    depended on whether the first word happened to be an adjective.
    for (word,) in db.execute("select word from nouns where word <> ''"):
        if len(word) < 3 or not word.isalpha() or not word[0].islower():
            continue
        stem = word[:-1] if word[-1] in "aáoe" else word
        if len(stem) < 3:
            continue
        put(stem + ("e" if stem[-1] in SOFT_FINALS else "o"), "noun stem")

    for stem in CURATED_NATIVE:
        put(stem, "native")
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
        ("select root from adjectives where root <> ''", 3, "root"),
        ("select root from adverbs where root <> ''", 3, "root"),
        ("select word from nouns where word <> ''", 4, "lemma"),
        ("select lemma from pales_kmen where lemma <> ''", 4, "lemma"),
        ("select inf_stem from verbs where inf_stem <> ''", 4, "verb"),
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

    db.close()
    return {
        "note": "generated by tools/build_composita.py from the Sapfo lexicon",
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
