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

## Why this exists

This did not start as a linguistics project. It started as a typesetting
problem: the author needed to set Slovak text automatically — to a measure,
justified, with correct hyphenation — without a person walking through the
output line by line. Word division is the part of that job a machine has to get
right, because a justified line is either broken in a legal place or it is
wrong, and the reader sees it immediately.

So the first step was to find something to use. What existed was a set of TeX
patterns from 1992, and nothing that could be inspected, corrected in a single
place and rebuilt: the word list those patterns were learned from was never
published, no open engine derived Slovak divisions from stated rules, and there
was no way to fix one wrong word without hand-patching a compiled table. A
pattern file that cannot be re-derived can only be replaced, never repaired.

The conclusion was that the missing piece was not another algorithm but the
input, and that it would have to be built. That is what this repository is:
first the vocabulary and the rules, then the patterns as a by-product.

## What a Liang pattern is

Most published hyphenation is done with the algorithm from Frank Liang's 1983
dissertation, the one built into TeX and, through it, into most typesetting and
word-processing software. It does not know any grammar. A pattern is a short
letter fragment carrying digits between the letters, for example `1ná2`: an odd
digit means a break is allowed at that spot, an even digit forbids it, all
patterns matching a word are overlaid, and the highest digit at each position
wins. A few thousand such fragments cover a whole language in a few kilobytes
and run instantly.

The patterns are not written by hand. A companion program, `patgen`, learns
them from a list of words in which the divisions are already marked, and then
keeps adding patterns until it reproduces that list closely enough. This is the
part worth understanding: **`patgen` reproduces its training list, so the entire
question of quality is the question of that list.** Whatever is inconsistent in
the input is generalised into the output, and it is generalised silently,
because a pattern file records no reason for anything. It cannot be reviewed by
reading it. That is why this project treats the word list, not the algorithm, as
the real work.

## What is different here

Slovak hyphenation patterns already exist: Jana Chlebíková published TeX
patterns for Slovak in 1992, and this project claims no priority for the idea.
What is new is that **the entire chain that produced the patterns in this
repository is in the repository**, under licences that let anyone rerun it:

| step | where it is | licence |
| --- | --- | --- |
| the vocabulary — 195,230 isolated word forms | [`tests/data/translatemaster_hyphenation_working.sqlite`](tests/data/translatemaster_hyphenation_working.sqlite) | `CC0-1.0 OR MIT` |
| the divisions used as training labels | computed by the rule engine in [`src/slabika/`](src/slabika) | `Apache-2.0 OR MIT` |
| the training, split and evaluation pipeline | [`tools/liang_experiment.py`](tools/liang_experiment.py) | `Apache-2.0 OR MIT` |
| the resulting Liang patterns | [`patterns/`](patterns) | `CC0-1.0 OR MIT` |

Nothing else is needed: no private prose corpus, no licensed dictionary, no
pre-divided word list. With `patgen` on `PATH`, two commands rebuild both
published pattern files from the bundled vocabulary, and independent runs of the
same checkout produce byte-identical files.

That closes a loop which is normally open. A published pattern file is usually a
terminal artefact: it can be loaded, but not audited, not corrected in one place
and rebuilt, not re-derived at all. Here every stage is readable and editable —
fix a rule in the engine, add your own words, change the split or the `patgen`
parameters, rerun the generator, and you have your own patterns plus a
machine-readable report of exactly what changed. As far as the author is aware,
this is the first Slovak hyphenation pattern set published together with the
complete input it was derived from.

Reproducibility is not correctness. Everything below distinguishes the two: the
project can prove that the patterns follow from the bundled data and the current
engine, and it deliberately makes no claim that every division in them is
correct under *Pravidlá slovenského pravopisu* (PSP).

## Why the labels are computed, not collected

The Liang/`patgen` algorithm is not the disputed part. Pattern quality is bounded
by the quality and consistency of the labelled words used for training; source
lists with conflicting divisions propagate those inconsistencies into the
patterns. The usual practice is to **assemble** that list from existing sources,
which inherits their inconsistencies without a way to see or fix them.

This project attacks the input instead. The Python engine computes syllables and
typographic break points from an explicit model of vowel and diphthong nuclei,
syllabic `ŕ`, `ĺ`, `r`, `l`, consonant clusters and recognised morpheme seams.
The Liang patterns are then trained on forms labelled by that engine; the labels
are not collected from existing hyphenation sources. This makes them internally
consistent with the engine; it does **not** make them automatically correct under
PSP. Existing text is used only to decide which vocabulary has to be covered;
see [`LICENSING.md`](LICENSING.md) §3.

### The hard part: the perceived stem

Many rules are mechanical once the linguistic analysis is known: vowel nuclei,
syllabic consonants, consonant distribution and typographic edge constraints can
be implemented directly. The difficult cases are the morpheme seams for which a
reader intuitively decides whether part of the word is still perceived as a
stem. The same sequence of letters may be a productive prefix plus a recognised
stem in one word, but part of a lexicalised or borrowed whole in another. A
character-level algorithm cannot reliably recover that distinction from spelling
alone.

This is why the project needs a large and varied vocabulary. It is not a source
of ready-made divisions and not a whole-word exception dictionary; it is the
evidence against which candidate analyses are found, tested across paradigms and
contrasted with near misses. Individual cases require review under PSP, but the
implementation then captures the narrowest supported family rule rather than
memorising the reviewed word. Cases without enough evidence remain explicitly
unresolved. Building and adjudicating this lexical evidence is therefore the
largest part of the work, even though much of the final engine is rule-based.

## How much of the vocabulary has actually been checked

The engine computes a division for all 195,230 forms, but computing is not
checking. Individual review is a separate, much smaller and fully tracked layer,
and the honest summary is that most of the inventory has never been looked at
one word at a time:

| review layer | forms | share of 195,230 |
| --- | ---: | ---: |
| decided by the author in the review console | 10,210 | 5.23% |
| decided in four frozen blind audits | 8,028 | 4.11% |
| either of the above (union, 3,268 in both) | 14,970 | 7.67% |
| adjudicated by two AI models under PSP | 1,239 | 0.63% |
| never individually reviewed | ~180,000 | ~92% |

**The author's own review** is in `tests/data/review_decisions.sqlite` and covers
10,210 forms: 9,519 confirmed the engine, 660 corrected it, 22 were marked
uncertain, 8 invalid and 1 flagged. These are the decisions that drove the
engine's rule work.

**The blind audits** are the four `tests/data/blind_*` sets — 5,000, 2,000,
1,000 and 100 forms, frozen with a manifest hash. Their contract is
*forms-only*: the reviewer receives the bare word with no engine output, no
prior decision and no adjudication, so the answer cannot be anchored on what the
engine already said. These were carried out by isolated LLM reviewers rather
than by the author, which is exactly why they are stored as evidence and never
as authority. Of the 8,100 decisions, 6,601 came back resolved, 1,477 uncertain
and 22 invalid.

**The dual-model adjudication** is in `tests/data/ai_adjudication/` — 17 runs,
1,346 adjudications over 1,239 distinct forms. Every run used the same two
independent models, recorded verbatim in each file as `models.A` and `models.B`:

| slot | model as recorded |
| --- | --- |
| A | `claude-opus-5[high]` |
| B | `gpt-6-astra[sub][high]` |

Each model answers alone, without seeing the other. Where the two answers
differ, each model is shown the other's reasoning and may revise
(*cross-review*); if they still differ, a reconciliation round follows; if they
still differ after that, the case is recorded as an open disagreement rather
than averaged away. Across all runs: 1,079 agreed independently, 145 agreed
after cross-review, 23 after reconciliation, and 99 remained unresolved — 71
distinct forms.

### Where AI review and the author's review still disagree

350 forms carry both an author's decision and a model consensus. On 297 of them
the two agree. **53 still differ**, in 15 word families, and they are listed
here rather than quietly reconciled:

| pattern | forms | example: author | example: models |
| --- | ---: | --- | --- |
| models preferred the engine over the author | 30 | `dô·stoj·nom` | `dôs·toj·nom` |
| author's decision was revised after the run | 13 | `o·po·tre·bu·je` | `opot·re·bu·je` |
| models rejected both answers | 4 | `Jac·kson` | `Jack·son` |
| depends on the pronunciation of a foreign name | 4 | `Arch·ae·a·lus` | `Ar·chae·a·lus` |
| models accepted both as codified variants | 2 | `pá·čid·lom` | `pá·či·dlom` |

The families are `opotrebovať`, `dôstojný`, `najposlednejší`, `neposlať`,
`apartmán`, `Jackson`, `obojpohlavný`, `alžbetínska`, `avantgarda`,
`najúhlavnejší`, `Hippokratov`, `páčidlo`, `Archaealus`, `Glendower` and
`Arbre`/`Lois`. None of these is
resolved by consensus, and none of them may be: a model majority is not a
normative authority. They stay open until a PSP argument settles them, and they
can be regenerated from the tracked data at any time. Every review layer above
is a detector of places that need a PSP decision — nothing more.

## How this differs from the 1992 patterns

In the held-out evaluation further below, Jana Chlebíková's patterns reproduce
the engine's division on 89.63% of whole words, so roughly one word in ten is
divided differently. The differences are not random. The largest group is the
morpheme seam: those patterns carry morphology as a hand-written list of 994
prefixes and stems, so a word outside that list falls through to the
phonotactic rules and the seam disappears. How the 1992 file was built, in its
author's own words, and what that predicts about these differences, is
documented in [`docs/hyph-sk-1992-origin.md`](docs/hyph-sk-1992-origin.md).

| word | 1992 patterns | this engine | what the extra point would allow |
| --- | --- | --- | --- |
| bezodkladne | `be·z·od·kladne` | `bez·od·kladne` | `be-zodkladne`, splitting `bez-` |
| najúspešnejší | `na·jús·peš·nejší` | `naj·ús·peš·nejší` | `na-júspešnejší`, moving `j` out of `naj-` |
| trojuholník | `tro·j·u·hol·ník` | `troj·uhol·ník` | `tro-juholník` |
| nadužívanie | `na·du·ží·va·nie` | `nad·uží·va·nie` | `na-dužívanie` |
| rozorať | `ro·zo·rať` | `roz·orať` | `ro-zorať` |
| abstrakcia | `ab·s·trak·cia` | `ab·strak·cia` | `abs-trakcia` |

The reverse case exists too: points the older patterns do not offer at all,
which costs nothing in correctness but does cost line breaks in a narrow
measure.

| word | 1992 patterns | this engine |
| --- | --- | --- |
| rozum | `rozum` (no break) | `ro·zum` |
| poobede | `po·obede` | `po·o·bede` |
| predĺžiť | `pre·dĺžiť` | `pre·dĺ·žiť` |
| administratíva | `ad·mi·ni·stra·tíva` | `ad·mi·nis·tra·tíva` |

Both columns were produced with the same TeX edge minima of 2/3, so the
comparison is like for like; `tex/hyph-sk.tex` is bundled in this repository, so
any of these can be checked directly. This is not a defect list. Those patterns
were built in 1992 with the resources of 1992, they have served Slovak
typesetting for three decades, and the point of showing the contrast is only
that a rule engine can carry a distinction — *this is a prefix* — that a table
of letter fragments has no way to represent.

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

Typographic division has three output levels, and they are genuinely different
outputs of the same algorithm rather than corrections of one another. For
example, `hyphenate("všeobecne")` returns the preferred `vše·obec·ne`, while
`hyphenate("všeobecne", contextual=True)` also exposes the legal but discouraged
point and returns `vše·o·bec·ne`. The latter does not fix the former: it merely
makes a point available when the preferred points do not fit the measure.
Codified doublets are exposed by `all_points=True`.

## What is in this repository

| path | what it is |
| --- | --- |
| `src/slabika/` | the rule engine and public API — `syllables`, `break_points`, `divisions`, `hyphenate` |
| `src/slabika/review/` | the local review console shipped with the package |
| `tests/data/translatemaster_hyphenation_working.sqlite` | the working word inventory: 195,230 isolated forms with casing and review state |
| `tests/data/blind_*`, `tests/data/ai_adjudication/` | frozen blind-audit samples and advisory AI adjudications used as evidence, not as authority |
| `tests/` | the test suite: engine, boundary classes, review console, generated-pattern invariants, provenance and licensing |
| `tools/liang_experiment.py` | the generator: labels, deterministic split, `patgen` training, evaluation, `report.json` |
| `tools/review/`, `tools/morph/` | audit, impact and morphology-induction utilities used during adjudication |
| `patterns/hyph-sk-slabika.tex` | the published preferred Liang pattern set |
| `patterns/hyph-sk-slabika-permissive.tex` | the published permissive Liang pattern set |
| `tex/hyph-sk.tex` | Jana Chlebíková's 1992 Slovak patterns, bundled under their MIT licence as the comparison baseline |
| `docs/pravidla-delenia-slov.md` | the project's independent Slovak restatement of PSP chapter V |
| `docs/hyph-sk-1992-origin.md` | how Chlebíková's 1992 patterns were built, from her own account, and what it predicts about the differences measured here |
| `LICENSING.md`, `CONTRIBUTING.md`, `REUSE.toml` | per-layer licensing, data provenance and contribution requirements |
| `run_review_local.bat`, `run_review.bat` | Windows launchers for the review console (external reviewer / maintainer) |

No sentences, word order or source-text structure are published: the inventory
holds isolated forms only.

## Reproduce the patterns yourself

Requirements are Python 3.10 or newer and the `patgen` executable from TeX Live
or MiKTeX on `PATH`. To run the full validation suite as well, install the
development tools with `python -m pip install -e ".[dev]"`.

From the repository root, these two commands rebuild all training labels from the
current engine, train both modes, evaluate them on the deterministic held-out set
and replace the two tracked pattern files:

```console
python tools/liang_experiment.py --mode preferred --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

The generator reads `tests/data/translatemaster_hyphenation_working.sqlite`. It
accepts rows whose casing status is `resolved` or `inferred`, casefolds and
deduplicates them, rejects unsupported spellings, and uses the stable salt
`slabika-liang-v1` for the train/test split. The generated `train.dic` contains
the engine-labelled training words. Each output directory also contains
`patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` and the machine-readable
`report.json`. The `--patterns-output` path is the final packaged TeX source.

For this snapshot, the source inventory has 195,767 rows and SHA-256
`d2bcafa945c86cf7eca000bc8ee6a4dc272311977669aa057ffa6182b1d2b821`. After
filtering it supplies 193,119 supported unique words: 154,496 training words and
38,623 held-out words. The resulting preferred and permissive files have SHA-256
`3460bdc9e28bd657cb926d1f1a74d069db09733e6b43cce6e300d882b1208743` and
`61f6346392bde47e8aaf77635c67fbc3e3c76a9c393090927b27f62724e7ab57`,
respectively.

### Verify a rebuild or a contribution

1. Read each `report.json`. Its `corpus` and `split` objects explain exactly how
   many rows were accepted, rejected, deduplicated, trained and held out; `files`
   records the input, training-dictionary and generated-pattern SHA-256 values;
   `evaluation` contains exact-word, precision and recall results plus the first
   30 mismatches.
2. With the unchanged checkout and matching `patgen`, the two generated files
   should have the hashes above and `git diff --exit-code -- patterns/` should
   report no difference. After an intentional engine or vocabulary change, review
   both the pattern diff and the metric changes rather than expecting the old
   hashes.
3. Run the project checks:

```console
python -m pytest
python -m ruff check .
reuse lint
```

The test suite covers the engine, review console, generated-pattern invariants,
provenance and licensing consistency. Ruff checks Python sources and REUSE checks
that every distributed file has the correct licence metadata. These checks and
the held-out score establish reproducibility and fidelity to the current engine;
they do **not** prove that a changed division is correct under PSP. Language
changes still require PSP evidence and the regression review described below.

## Change the input and rebuild

Everything the generator consumes is editable, and the licences impose no
condition on redistributing what you derive.

- **Change a language rule.** Edit the engine, run the test suite, then rerun the
  two generator commands. The labels, both pattern files and the reported metrics
  follow from the change.
- **Add vocabulary.** Insert additional forms into the inventory and rerun. More
  varied evidence is the main lever on quality; new words must be your own
  material or public domain (see below).
- **Change the experiment.** The split salt, the held-out fraction, the `patgen`
  parameters and the output mode are all in `tools/liang_experiment.py`, and each
  run documents itself in `report.json`.
- **Keep the result.** Patterns derived from this data may be published,
  repackaged or shipped commercially under either offered licence, with no
  obligation back to this project.

### Review and submit PSP-grounded corrections

The bundled review console lets a reader inspect the vocabulary without editing
the project's tracked decisions. From a checkout, install and start it with:

```console
python -m pip install -e .
slabika-review
```

It opens a local address in the default browser. The bundled inventory is
read-only; the reviewer's work is stored separately in `review_decisions.sqlite`
in the directory from which the command is run. `--decisions` selects another
decision store and `--db` selects another inventory.

On Windows, the recommended entry point for an independent reviewer is
`run_review_local.bat`. It needs no package installation, checks for Python 3.10
or newer and keeps each user's decisions under `%LOCALAPPDATA%\slabika-review`.
It therefore cannot modify the project's review database. `run_review.bat` is the
maintainer launcher: it deliberately opens the tracked project review data and is
not the right launcher for an external review.

The console keeps two questions separate:

- **typographic division** says where a written word may be broken at the end of
  a line; this is the output used to train the Liang patterns;
- **syllabification** describes the spoken syllables and may legitimately have
  different boundaries.

For a useful correction, search for the word, inspect the current typographic
result, enter the proposed boundaries and save the suggestion. `-` and `·` may be
used as boundary markers; neither may change, remove or add letters. Mark a
proper name, foreign word, abbreviation, invalid form or uncertain case when
applicable instead of forcing an unsupported answer.

The normative authority is chapter V, *Word division*, of PSP. The independent
project restatement in
[`docs/pravidla-delenia-slov.md`](docs/pravidla-delenia-slov.md) is the quickest
reference. The current engine, syllabification, the 1992 TeX patterns, AI review
and previous human decisions are evidence or comparison signals, not authorities.
A submission is strongest when its note gives the exact PSP rule, explains the
morpheme or sound analysis and lists related forms or a contrasting near miss.
Please distinguish a preferred point from an equally codified variant or a legal
but discouraged contextual point.

The **Download corrections** button exports a timestamped `slabika-corrections`
JSON file containing only saved proposals that still differ from the current
engine. It includes the form, engine output and version, proposed output, note
and flags. Send that file unchanged to the project author by email, or attach it
to an issue; supporting PSP evidence can be written in the message. Sending the
JSON does not alter the repository and does not make a proposal canonical
automatically. Every accepted correction is checked against PSP and for
corpus-wide regressions. Because one bad word is usually evidence of a missing
family rule, fixes normally add the narrowest supported rule and tests, not a
whole-word exception.

### Contribute vocabulary

New vocabulary is welcome only when it is the contributor's own material or
public-domain material. Do not submit extracted third-party dictionary, lexical
database or word-list content. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the
licensing and provenance requirements.

## The published Liang pattern files

The project publishes two **work-in-progress** pattern sets learned solely from
the bundled vocabulary. Of its 195,767 inventory rows, 193,119 supported unique
words remain after excluding `needs_review` forms and applying alphabet and
casefold filtering. The deterministic split assigns 154,496 words to training and
keeps 38,623 words unseen for both evaluations:

- [`patterns/hyph-sk-slabika.tex`](patterns/hyph-sk-slabika.tex) is the default
  preferred set (5,231 patterns), trained from `break_points(word)`;
- [`patterns/hyph-sk-slabika-permissive.tex`](patterns/hyph-sk-slabika-permissive.tex)
  is the permissive set for narrow measures (4,835 patterns), trained from
  `break_points(word, all_points=True, contextual=True)`.

Both sets contain no whole-word exceptions. TeX edge minima 2/3 were applied to
both the input and the evaluation.

A standard Liang pattern file exposes one undifferentiated set of points; it
cannot retain the instruction “prefer this point, use that one only in a narrow
measure”. Two separate files therefore carry that distinction. Normal typesetting
should use the preferred set. The permissive set additionally exposes equally
codified variants and legal but discouraged contextual points; the two sets must
not be loaded together.

On 38,623 held-out words, with the same TeX left/right minima of 2/3 applied to
both competitors and to the target, the result was:

| patterns | exact whole words | point precision | point recall |
| --- | ---: | ---: | ---: |
| **slabika preferred (5,231 patterns)** | **98.6770%** (38,112/38,623) | **99.6283%** | **99.5121%** |
| Jana Chlebíková 1992 against the preferred target | 89.6279% | 96.0111% | 95.3423% |
| **slabika permissive (4,835 patterns)** | **98.7728%** (38,149/38,623) | **99.6545%** | **99.5635%** |
| Jana Chlebíková 1992 against the permissive target | 89.1023% | 96.3877% | 94.8691% |

This is a benchmark of **fidelity to the current rule engine**, not an
independent PSP correctness benchmark. Engine points outside the common TeX
minima were excluded from scoring. The files are useful for testing and
downstream experiments, but they are not a final pattern release and are not yet
wired into the Python package.

### Using the patterns elsewhere

The `.tex` suffix describes the source syntax, not the only environment in which
the patterns can be used. The payload is standard Liang pattern data: it can be
loaded by TeX-compatible tooling, repackaged as a Hunspell-style hyphenation
dictionary for applications such as LibreOffice, OpenOffice, Scribus or Pyphen,
or converted to the pattern format of a JavaScript Liang engine such as
Hyphenopoly. Each target still needs its own encoding and minima metadata,
wrapper or compiled format, language registration and testing; merely copying
this repository file into an application or a website does not install it.
Browsers do not expose a web API for loading an arbitrary custom pattern file
into CSS `hyphens: auto`.

The patterns perform one task only: predicting typographic break points in
words. They do not expose the rule engine's linguistic syllables, morpheme
analysis, three output levels, or its distinction between an unsupported spelling
and a supported word with no available break.

## Current status

`slabika` is an **alpha** (`0.1.0`) Python package for Python 3.10 and newer. It
has no runtime dependencies and can be installed from a checkout with
`python -m pip install -e .`.

| component | current state |
| --- | --- |
| rule-based Python engine | **present** — syllabification and typographic division are implemented and tested separately |
| public API | **present** — `syllables`, `break_points`, `divisions` and `hyphenate` |
| output levels in the project's PSP interpretation | **present** — preferred points by default, codified doublets with `all_points=True`, discouraged-but-legal points with `contextual=True` |
| whole-word exception dictionary | **absent by design** — representative known unresolved cases remain failing `xfail` specifications until a rule can account for them |
| complete input and pipeline for the published pattern set | **present** — the bundled SQLite vocabulary and tracked generator reproduce both pattern files without an external corpus |
| source prose corpus | **not published** — no sentences, word order or source-text structure are shipped |
| experimental Liang patterns | **present** — preferred and permissive sets in `patterns/`, explicitly marked work in progress |
| use of Liang patterns by the Python package | **not implemented** — the package runs the rule engine directly |
| independent PSP gold benchmark or certified overall accuracy | **not available yet** |
| final TeX release and integrations for browsers, office suites or typesetters | **not available yet** |

The tracked engine, review-console and provenance tests cover the language rules,
boundary classes, public API, local editor and licensing constraints, and they
run from a clean checkout. Known unresolved language cases stay visible as strict
expected failures instead of being hidden in a word list. The 195,230-form
inventory has also been used for corpus-scale robustness checks, but most of
those forms have not been independently adjudicated. A run without exceptions is
evidence of robustness, not evidence that every division is correct. The project
therefore makes no overall accuracy claim for the rule engine today.

### Known limits of the Python engine

- Spelling alone does not always reveal word identity or pronunciation. Apparent
  prefixes that have lexicalised, borrowed vowel sequences and unadapted foreign
  names still include known unresolved cases.
- There is deliberately no table of whole-word overrides. A missing linguistic
  distinction remains an explicit regression until it can be expressed as a rule
  or as a justified future language-data layer.
- `hyphenate` leaves unsupported spellings untouched, while `syllables` raises
  `ValueError` for alphabetic characters outside the analysable inventory. An
  empty `break_points` result does not distinguish an unsupported spelling from a
  supported word with no legal break.
- The engine's morpheme analysis is rule-based and intentionally incomplete; it
  is not a general Slovak morphological analyser and it does not know the
  language or pronunciation of an arbitrary foreign word.

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
provisions later added in MPL-2.0 — terms that a good deal of existing
typesetting and dictionary code sits under. Offering the code under MIT as well
removes that barrier for downstream projects that are genuinely on that side of
the line: take the patent grant if you want it, take MIT if Apache is the thing
standing in your way.

The same logic runs through the other layers. Data, patterns and documentation
can be taken under `CC0-1.0` with no licence conditions at all — or under MIT,
for compliance tooling that expects a conventional OSI licence. **Every layer of
this project is therefore also offered under MIT**, if that is easier than
explaining CC0 to a review board. MIT itself does not expressly address the EU
`sui generis` database right; the `CC0-1.0` dedication does, and that dedication
applies independently of which alternative a downstream compliance inventory
records. Writing MIT in your inventory does not opt out of it.

See [`LICENSING.md`](LICENSING.md) for the full statement, including data
provenance and how CC0-1.0 disposes of the EU `sui generis` database right.
Per-file licensing follows [REUSE 3.3](https://reuse.software/) and is declared in
`REUSE.toml`. There is deliberately no Apache `NOTICE` file, so no extra notice
text has to travel with your redistribution.

**`CC0-1.0` itself imposes no attribution requirement.** This does not affect any
moral or personality right that cannot be waived under applicable law — for the
documentation, which is authored prose, that reservation is not theoretical.
CC0-1.0 waives what it can waive, to the fullest extent the applicable law
allows, and does not purport to reach further. The code carries no advertising or
acknowledgement requirement either, but redistributing it does mean keeping the
notices required by whichever licence you pick, MIT or Apache-2.0.

## Conformance

Output is intended to conform to the rules of Slovak orthography codified in
*Pravidlá slovenského pravopisu* (JÚĽŠ SAV), chapter **V. Rozdeľovanie slov**.
PSP is used as a statement of what the correct answer is — not as a source of
data. The project's independent Slovak-language restatement is in
[`docs/pravidla-delenia-slov.md`](docs/pravidla-delenia-slov.md); test vocabulary
comes from this project's own word material. This project is not affiliated with,
nor endorsed by, JÚĽŠ SAV.

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
ISBN 80-224-0109-9), chapter 2 *Fonológia*. That book makes the case this project
rests on: that a formal model of a language has to start from its sound system,
and that morphology cannot be done correctly without consulting phonology. The
classification given there — vowel quantity and resonance, hardness, voicing
pairs, place and manner of articulation, syllabic consonants, the rhythmic law —
is what `slabika.phonology` encodes. Páleš in turn credits **J. Dvončová** (1980)
and **J. Horecký** (1977) for the classification itself.

The algorithms above that layer — syllabification, morpheme-seam handling and the
typographic convention — are this project's own work; Páleš's book does not
address hyphenation.

Jana Chlebíková's 1992 Slovak TeX patterns are bundled in `tex/hyph-sk.tex` under
their MIT licence and are used here only as a comparison baseline.

The benchmarking methodology and the case for treating word-list quality as the
real bottleneck follow O. Metelka and P. Sojka, *Hyph-bench: Benchmark Dataset of
Hyphenated Words for Generating Hyphenation Patterns*, RASLAN 2025.
