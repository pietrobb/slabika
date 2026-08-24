# slabika

Slovak syllabification and typographic word division — two distinct results
built on a shared phonological and morphological analysis, not on a guessed
pattern table.

```python
>>> import slabika
>>> slabika.syllables("najneuveriteľnejšími")
['naj', 'ne', 'u', 've', 'ri', 'teľ', 'nej', 'ší', 'mi']
>>> slabika.hyphenate("Prekladateľský", separator="-")
'Pre-kla-da-teľ-ský'
>>> slabika.break_points("Prekladateľský")
[3, 6, 8, 11]
```

> 🇸🇰 Po slovensky: [README.sk.md](README.sk.md)

## Why

Slovak is not without its own hyphenation work: Jana Chlebíková published Slovak
TeX patterns in 1992. This project therefore makes no claim to being the first;
it addresses a narrower problem: producing a modern, testable rule engine and
deriving an openly reusable pattern set from one consistent analysis.

The Liang/`patgen` algorithm is not the disputed part. Pattern quality is bounded
by the quality and consistency of the labelled words used for training; source
lists with conflicting divisions can propagate those inconsistencies into the
patterns.

This project attacks the input instead. The current Python engine computes
syllables and typographic break points from an explicit model of vowel and
diphthong nuclei, syllabic `ŕ`, `ĺ`, `r`, `l`, consonant clusters and recognised
morpheme seams. The experimental Liang patterns are then trained on forms
labelled by that engine; the labels are not collected from existing hyphenation
sources. This makes them internally consistent with the engine; it does **not** make
them automatically correct under PSP. Existing text is used only to decide
which vocabulary has to be covered; see [`LICENSING.md`](LICENSING.md) §3.

## Architecture

The package has a shared foundation and two distinct outputs:

| module | what it is |
| --- | --- |
| `slabika.phonology` | shared phoneme inventory: quantity, voicing, place, manner, palatalization |
| `slabika.syllabify` | phonotactic division of the spoken word into syllables |
| `slabika.typo` | written-word break points under the project's interpretation of PSP and typographic constraints |
| `slabika.phonotactics` | well-formedness, rhythmic law, preposition vocalization |

`slabika.syllabify` and `slabika.typo` are not a pipeline in which the latter
merely filters the former's output. Both use the shared phonological and
morphological analysis, then make separate decisions under different rules. A
word may therefore syllabify as `ma·slo` while allowing the typographic break
`mas|lo`. The boundaries often coincide, but the two results are not
interchangeable.

## Current status

`slabika` is an **alpha** (`0.1.0`) Python package for Python 3.10 and newer. It
has no runtime dependencies and can be installed from a checkout with
`python -m pip install -e .`.

What the published repository currently contains — and does not contain:

| component | current state |
| --- | --- |
| rule-based Python engine | **present** — syllabification and typographic division are implemented and tested separately |
| public API | **present** — `syllables`, `break_points`, `divisions` and `hyphenate` |
| output levels in the project's PSP interpretation | **present** — preferred points by default, codified doublets with `all_points=True`, discouraged-but-legal points with `contextual=True` |
| whole-word exception dictionary | **absent by design** — representative known unresolved cases remain failing `xfail` specifications until a rule can account for them |
| working word/review data | **present** — the SQLite snapshots in `tests/data/` contain isolated forms and review state, not running text |
| review console | **partial** — the server and UI are tracked, but their TeX comparison helper is not published yet, so a clean checkout cannot run the complete console |
| source prose corpus | **not published** — no sentences, word order or source-text structure are shipped |
| experimental Liang patterns | **present** — `patterns/hyph-sk-slabika.tex`, explicitly marked work in progress |
| complete input and pipeline for the published pattern set | **not published yet** — the repository alone cannot regenerate the 702,438-form experiment |
| use of Liang patterns by the Python package | **not implemented** — the package runs the rule engine directly |
| independent PSP gold benchmark or certified overall accuracy | **not available yet** |
| final TeX release and integrations for browsers, office suites or typesetters | **not available yet** |

The tracked engine and provenance tests cover the language rules, boundary
classes, public API and licensing constraints. Review-console tests are also
tracked, but a clean checkout cannot currently collect them because the helper
noted above is missing. Known unresolved language cases stay visible as strict
expected failures instead of being hidden in a word list. The 179,537-form
working inventory has also been used for
corpus-scale robustness checks, but most of those forms have not been
independently adjudicated. A run without exceptions is evidence of robustness,
not evidence that every division is correct. The project therefore makes no
overall accuracy claim for the rule engine today.

### Known limits of the Python engine

- Spelling alone does not always reveal word identity or pronunciation. Apparent
  prefixes that have lexicalised, borrowed vowel sequences and unadapted foreign
  names still include known unresolved cases.
- There is deliberately no table of whole-word overrides. A missing linguistic
  distinction remains an explicit regression until it can be expressed as a
  rule or as a justified future language-data layer.
- `hyphenate` leaves unsupported spellings untouched, while `syllables` raises
  `ValueError` for alphabetic characters outside the analysable inventory. An
  empty `break_points` result does not distinguish an unsupported spelling from
  a supported word with no legal break.
- The engine's morpheme analysis is rule-based and intentionally incomplete; it
  is not a general Slovak morphological analyser and it does not know the
  language or pronunciation of an arbitrary foreign word.

### Experimental Liang patterns

[`patterns/hyph-sk-slabika.tex`](patterns/hyph-sk-slabika.tex) is the first
published **work-in-progress** pattern set. It contains 6,376 patterns and no
whole-word exceptions. PATGEN learned it from 702,438 forms labelled with the
preferred points of the current `slabika` engine; the fixed test set was excluded
from training.

On 33,734 held-out words, with the same TeX left/right minima of 2/3 applied to
both competitors and to the target, the result was:

| patterns | exact whole words | point precision | point recall |
| --- | ---: | ---: | ---: |
| **slabika WIP (6,376 patterns)** | **98.7075%** (33,298/33,734) | **99.8194%** | **99.4032%** |
| Jana Chlebíková 1992 | 86.7997% | 94.7457% | 93.6176% |

This is a benchmark of **fidelity to the current rule engine**, not an
independent PSP correctness benchmark. Engine points outside the common TeX
minima were excluded from scoring. The file is useful for testing and downstream
experiments, but it is not a final pattern release, is not yet wired into the
Python package, and cannot yet be regenerated from the published repository
alone.

The `.tex` suffix describes the source syntax, not the only environment in which
the patterns can be used. The payload is standard Liang pattern data: it can be
loaded by TeX-compatible tooling, repackaged as a libhyphen/Hunspell-style
hyphenation dictionary for applications such as LibreOffice, OpenOffice,
Scribus or Pyphen, or converted to the pattern format of a JavaScript Liang
engine such as Hyphenopoly. Each target still needs its own encoding and minima
metadata, wrapper or compiled format, language registration and testing; merely
copying this repository file into an application or a website does not install
it. Browsers do not expose a web API for loading an arbitrary custom pattern
file into CSS `hyphens: auto`.

The patterns perform one task only: predicting typographic break points in
words. They do not expose the rule engine's linguistic syllables, morpheme
analysis, three output levels, or its distinction between an unsupported
spelling and a supported word with no available break.

## Licensing

Deliberately split so that no downstream project is ever blocked from using it:

| layer | licence |
| --- | --- |
| source code | `Apache-2.0 OR MIT` — your choice |
| language data | `CC0-1.0 OR MIT` — your choice |
| generated hyphenation patterns | `CC0-1.0 OR MIT` — your choice |
| documentation | `CC0-1.0 OR MIT` — your choice |

Apache-2.0 carries a patent grant and passes corporate legal review, but it is
incompatible with GPL-2.0-only, and MPL-1.1 lacks the Apache-2.0 compatibility
provisions later added in MPL-2.0 — terms that a good deal of
existing typesetting and dictionary code sits under. Offering the code under
MIT as well removes that barrier for downstream projects that are genuinely on
that side of the line: take the patent grant if you want it, take MIT if Apache
is the thing standing in your way.

The same logic runs through the other layers. Data, patterns and documentation
can be taken under `CC0-1.0` with no licence conditions at all — or under MIT,
for compliance tooling that expects a conventional OSI licence. **Every layer
of this project is therefore also offered under MIT**, if that is easier than
explaining CC0 to a review board. MIT itself does not expressly address the EU
`sui generis` database right; the `CC0-1.0` dedication does, and that dedication
applies independently of which alternative a downstream compliance inventory
records. Writing MIT in your inventory does not opt out of it.

See [`LICENSING.md`](LICENSING.md) for the full statement, including data
provenance and how CC0-1.0 disposes of the EU `sui generis` database right. Per-file
licensing follows [REUSE 3.3](https://reuse.software/) and is declared in
`REUSE.toml`. There is deliberately no Apache `NOTICE` file, so no extra notice
text has to travel with your redistribution.

**`CC0-1.0` itself imposes no attribution requirement.** This does not affect
any moral or personality right that cannot be waived under applicable law — for
the documentation, which is authored prose, that reservation is not theoretical.
CC0-1.0 waives what it can waive, to the fullest extent the applicable law
allows, and does not purport to reach further. The code carries no
advertising or acknowledgement requirement either, but redistributing it does
mean keeping the notices required by whichever licence you pick, MIT or
Apache-2.0.

## Conformance

Output is intended to conform to the rules of Slovak orthography codified in
*Pravidlá slovenského pravopisu* (JÚĽŠ SAV), chapter **V. Rozdeľovanie slov**.
PSP is used as a statement of what the correct answer is — not as a source of
data. The project's independent Slovak-language restatement is in
[`docs/pravidla-delenia-slov.md`](docs/pravidla-delenia-slov.md); test vocabulary
comes from this project's own word material. This project is not affiliated
with, nor endorsed by, JÚĽŠ SAV.

## Author and contact

Created and maintained by **Peter Bezemek** — <peter.bezemek@gmail.com>,
[@pietrobb](https://github.com/pietrobb).

The implementation, the syllabification and hyphenation algorithms and the
underlying Slovak word material are his own work. Questions about the rules, the
data, or about relicensing for a specific downstream project go to him directly.

## Acknowledgements

The phoneme classification this library is built on comes from **Emil Páleš**,
*Sapfo — parafrázovač slovenčiny: počítačový nástroj na modelovanie v jazykovede*
(VEDA, vydavateľstvo Slovenskej akadémie vied, Bratislava, 1994,
ISBN 80-224-0109-9), chapter 2
*Fonológia*. That book makes the case this project rests on: that a formal model
of a language has to start from its sound system, and that morphology cannot be
done correctly without consulting phonology. The classification given there —
vowel quantity and resonance, hardness, voicing pairs, place and manner of
articulation, syllabic consonants, the rhythmic law — is what `slabika.phonology`
encodes. Páleš in turn credits **J. Dvončová** (1980) and **J. Horecký** (1977)
for the classification itself.

The algorithms above that layer — syllabification, morpheme-seam handling and
the typographic convention — are this project's own work; Páleš's book does not
address hyphenation.

The benchmarking methodology and the case for treating word-list quality as the
real bottleneck follow O. Metelka and P. Sojka, *Hyph-bench: Benchmark Dataset of
Hyphenated Words for Generating Hyphenation Patterns*, RASLAN 2025.
