# Where the 1992 Slovak patterns came from

`tex/hyph-sk.tex` — the file TeX distributions still ship as the Slovak
hyphenation table — is dated 24 April 1992 and signed by Jana Chlebíková of the
Department of Informatics Education at Comenius University in Bratislava. This
document reconstructs how it was built, because that history explains the shape
of every difference this project measures against it, and because it is the
clearest available argument for why the approach taken here is different in
kind rather than merely newer.

The reconstruction is not guesswork. The author described her own method in
print, and the pattern file independently corroborates the description.

## The primary source

> Jana Chlebíková. *Ako rozdeliť (slovo) Československo.* Zpravodaj
> Československého sdružení uživatelů TeXu, vol. 1 (1991), no. 4, pp. 10–13.
> DOI [10.5300/1991-4/10](https://doi.org/10.5300/1991-4/10),
> persistent URL <http://dml.cz/dmlcz/148815>.

The article is freely readable in the Czech Digital Mathematics Library. It
predates the shipped file by a year and describes the work in progress; the
1992 file is the finished result of exactly the procedure it lays out.

## What the author says she did

The decisive sentence contrasts her method with Liang's:

> „Na rozdiel od Lianga, ktorý základ svojich vzorov vyrobil z obrovského
> množstva slov […] (k dispozícii mal Webster's Pocket Dictionary v
> elektronickej forme — zhruba 50 000 slov), použitá metóda je založená priamo
> na prepise gramatických pravidiel na rozdeľovanie slov."

*Unlike Liang, who built his patterns from a huge set of words — he had
Webster's Pocket Dictionary in electronic form, roughly 50,000 entries — the
method used here is based directly on transcribing the grammatical rules of
word division.*

There was no training corpus and no PATGEN run. The patterns are a hand
transcription of the rules of Slovak orthography, written in Liang's notation
because that is what TeX consumes. The article then names four phases, in
order:

1. **Mechanical division.** Suppress breaks inside the digraphs `ch`, `dz`,
   `dž` and the diphthongs `ia`, `ie`, `iu`; give every vowel an odd value so a
   vowel opens a syllable; then write out `2b1b`, `2b1t`, `2b1č` … *for every
   possible consonant pair*, striking out `2c1h`, `2d1z`, `2d1ž` by hand
   because those are digraphs.
2. **Consonant clusters.** Add selected triples such as `s3t2r` (*ses-tra*),
   `n3d2r` (*han-dra*), `n3s2k` (*pán-sky*), then quadruples, quintuples and so
   on. The author flags this as the hard step and explains why: adding `t3ĺ2k`
   would destroy the already-correct division of *otlkať*, because syllabic
   `l`, `ĺ`, `r`, `ŕ` behave as vowels.
3. **Prefixes and compound-word elements.** `.do3k4r`, `.bez5`, `5viac3h4`,
   `.štvor3r` … Each prefix must carry a fragment of the stem after it,
   otherwise the pattern would license *do-ktor*.
4. **Suffixes, then foreign words and a hand-written exception list.**

The article closes on the question in its title: *Čes-ko-slo-ven-sko*.

## What the file independently confirms

Three properties of `tex/hyph-sk.tex` corroborate the account, and none of them
is consistent with machine generation.

**It has chapter headings.** Eighteen Slovak comments partition the 2,467
patterns into exactly the phases the article describes:

| patterns | comment | examples |
| ---: | --- | --- |
| 22 | `% samohlásky` | `a1 á1 ä1 e1` |
| 713 | `% dvojice spoluhlások` | `2b1b 2b1c 2b1č 2b1d` |
| 24 | `% 2 samohlásky` | `a1í2 a1o2 e1á2` |
| 264 | `% 3 spoluhlásky` | `b2l3b 3b2l3k` |
| 183 | `% 4 spoluhlásky` | `3b2l4č3n 3b2r4b3l` |
| 31 | `% 5 spoluhlások` | `3c4v4r4č3k 3č4ŕ4s3t4v` |
| 3 | `% 6 spoluhlások` | `3c4v4r4n3g4n 3š4k4v4r4k3n` |
| 129 | `% koncovka -ný` | `k4č3ný. k4č3ného.` |
| 34 | `% koncovky -ka` | `l2t3k2a. l2t3k2ou.` |
| 1 | `% koncovka -ty` | `5p4r4s3t` |
| 24 | `% koncovka -ský,-sky` | `b3s4k d3s4k ľ3s4k` |
| 3 | `% koncovky -ština,-čina` | `n2d3č r4z3š2t2` |
| 15 | `% koncovky -stvo` | `b3s4t4v ľ3s4t4v` |
| 658 | `% predpony` | `.bez5 .dvoj5 .cudzo5s4` |
| 279 | `% slovné základy` | `5alkohol 5b4lesk` |
| 57 | `% začiatky slov` | `.cv6 .ch6 .sp6 .st6` |
| 21 | `% koncovky` | `8c4h. 8d4z. 4j4s4ť.` |
| 6 | `% cudzie slová` | `akci3a2 gymnázi3um le2u3kémia` |

PATGEN emits a flat sorted list with no comments at all. A table of contents in
grammatical categories is something only a person writes.

**It contains patterns no corpus could supply.** A pattern learned from data
must be a substring of some training word. Testing all 2,467 patterns against
the 193,119-word vocabulary shipped in this repository, **362 of them describe
a letter sequence that occurs in no Slovak word at all** — `2ď1ď`, `2č1č`,
`2b1w`, `2b1x`, `2f1ť`. The `% dvojice spoluhlások` block is close to the full
Cartesian product of the Slovak consonant inventory: someone walked the
alphabet against itself and wrote down the rule "between two consonants there
is a break", including the pairs the language never realises.

**It ends with a hand-written exception list.** `\hyphenation{}` carries five
entries — `dosť`, `me-tó-da`, `me-tó-dy`, `ne-do-stat-ka-mi`, `sep-tem-bra` —
words that did not come out right and were fixed one at a time.

Two smaller details also fit. The file uses priority levels 1 through 8, where
generated pattern sets normally need four; Petr Sojka noted the same and
attributed it to hand authoring. And the 1991 article sets both hyphenation
minima to 2, while the 1992 file declares `left: 2, right: 3` — the parameter
was revised between the article and the release.

## The bottleneck the author names herself

The article does not merely omit a corpus; it identifies the absence as the
limiting factor. On consonant triples:

> „Problém sa teda sústreďuje na získanie zoznamu všetkých možných trojíc
> spoluhlások, vyskytujúcich sa v slovenských slovách. Nejaké štatistické
> výsledky možno nájsť v [3], rozhodne však nie sú uspokojivé."

*The problem therefore comes down to obtaining a list of all possible consonant
triples occurring in Slovak words. Some statistics can be found in [3], but
they are certainly not satisfactory.*

Reference [3] is Mistrík's 1985 frequency dictionary — a printed book. The
grammar came from Oravec and Laca's 1976 school handbook of Slovak orthography.
Both are authoritative and neither is machine-readable. The work was rule-bound
because in 1991 in Bratislava there was nothing else to be bound to.

The author was explicit about the standing of the result:

> „Možno niekomu poslúži ako inšpirácia na vytvorenie dokonalejšej verzie […]
> alebo ako ukážka toho, kadiaľ cesta nevedie."

*Perhaps it will serve someone as inspiration for a more perfect version, or as
a demonstration of where the road does not lead.*

Of the foreign-word rules and exception list she wrote: *"this part has not
been given much attention so far."* The file has six foreign-word patterns and
five exceptions. Thirty-four years later, it still does.

## The 2004 verdict, and why it did not stick

Petr Sojka revisited the problem in *Slovenské vzory dělení slov: čas pro
změnu?* (SLT 2004, pp. 67–72). His diagnosis of the 1992 file matches the one
above and reaches the obvious conclusion:

> „Lze si ale těžko představit, že by se tímto způsobem podařilo zachytit
> několik miliónů slovních tvarů, které ve slovenštině existují. Na švech
> předpon a složených slov jsou mnohé výjimky, které jdou proti základnímu
> slabičnému principu. Těch jsou ale tisíce, či desetitisíce."

*It is hard to imagine capturing this way the several million word forms that
exist in Slovak. At prefix and compound seams there are many exceptions running
against the basic syllabic principle — and there are thousands or tens of
thousands of them.*

He did what the technology asks for: collected close to a million Slovak words,
ran PATGEN, iterated by bootstrapping, and reported patterns that handled
irregularity far better. He recommended replacing the 1992 file.

That did not happen. Distributions still ship Chlebíková 1992. One reason is
recorded in a footnote of his own paper:

> „Bohužel výslednou množinu slov nelze volně šířit. Volně přístupný seznam
> slov by umožnil ještě mnohem flexibilnější vytváření variant dělicích vzorů
> optimalizovaných pro konkrétní projekty."

*Unfortunately the resulting word set cannot be freely distributed. A freely
available word list would allow far more flexible creation of pattern variants
optimised for specific projects.*

Better patterns existed and could not be reproduced by anyone else, because the
data behind them could not be shared. A pattern file whose inputs are
unavailable is, for every purpose except immediate use, as opaque as a hand-made
one — it cannot be audited, corrected, or regenerated after a rule changes.

## What this project does differently

Three approaches, three bottlenecks:

| | Chlebíková 1992 | Sojka 2004 | this project |
| --- | --- | --- | --- |
| division decided by | hand-written rules | a private word list | a rule engine, in the repository |
| morphology | a finite list of 994 lines | learned from data | computed by analysis |
| training corpus | none | ~10<sup>6</sup> words, undistributable | 195,767 forms, `CC0-1.0 OR MIT` |
| reproducible by a third party | not applicable | no | yes, one command |
| effect of a rule change | edit by hand, hope nothing else breaks | unavailable | rerun the pipeline |

The point is not that the patterns here score better against their own target —
that number measures fidelity to this engine and proves nothing about
correctness. The point is what happens next time.

The 1992 file cannot be developed further without repeating the original labour.
Its morphology is a lookup table: 658 prefixes, 279 stems, 57 word-initial
strings — 994 lines, enumerated by hand. Adding a prefix means hand-authoring
its interaction with every cluster rule already present, which is precisely the
`t3ĺ2k` / *otlkať* trap the author documented in 1991. There is no test suite to
tell you when you have sprung it.

Here, a rule lives in one place. When the treatment of compound seams was
corrected in this engine, the entire pattern set was regenerated from the
corrected rule in about sixty seconds, and the 606-test suite reported what
moved. Nothing was hand-edited, and the resulting `.tex` file is byte-stable:
the same inventory yields the same SHA-256. The chain — vocabulary, engine,
split, PATGEN invocation, evaluation, report — is in this repository under
licences that let anyone rerun it and get the identical file.

That is the difference Sojka's footnote asked for, twenty years late.

## What it explains about the measured differences

Against the held-out evaluation, the 1992 patterns reproduce this engine's
division on 89.62% of whole words. The origin story predicts the exact shape of
the remaining 10.61%, and the measurement bears it out:

- **The errors travel in families, not at random.** The morphological layer is a
  finite list. A word whose prefix or stem appears in those 994 lines is divided
  correctly; a word whose prefix does not appear falls through to the
  phonotactic layer and the seam vanishes. Whole paradigms therefore fail
  together.
- **The dominant failure is a break offered inside a morpheme** — `be-zodkladne`,
  `na-júspešnejší`, `tro-juholník`. That is layer 1 winning because layer 3 has
  no entry for that word. 7.27% of held-out words carry at least one such break.
- **Foreign words are barely covered**, exactly as the author stated: six
  patterns for the entire category.

None of this is a defect of the author's craft. It is the ceiling of the method
she chose, under the constraint she named, in the year she worked. The file did
its job for thirty-four years, which is more than most software achieves.

## References

1. Jana Chlebíková. *Ako rozdeliť (slovo) Československo.* Zpravodaj CSTUG,
   1(4):10–13, 1991. <http://dml.cz/dmlcz/148815>
2. Jana Chlebíková. *Hyphenation patterns for Slovak*, version 2.0, 24 April
   1992. Bundled here as [`tex/hyph-sk.tex`](../tex/hyph-sk.tex) under the MIT
   licence; distributed in `hyph-utf8`, and as `skhyphen` in `csplain` for IL2.
3. Petr Sojka. *Slovenské vzory dělení slov: čas pro změnu?* SLT 2004, pp.
   67–72. <https://www.fi.muni.cz/usr/sojka/papers/skhyp.pdf>
4. Franklin M. Liang. *Word Hy-phen-a-tion by Com-put-er.* PhD thesis, Stanford
   University, 1983.
5. Ján Oravec, Vincent Laca. *Príručka slovenského pravopisu pre školy.* SPN,
   Bratislava, 1976. — the grammar source cited by Chlebíková.
6. Jozef Mistrík. *Frekvencia tvarov a konštrukcií v slovenčine.* VEDA,
   Bratislava, 1985. — the statistical source she found insufficient.
