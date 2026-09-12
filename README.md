# slabika

Slovak syllabification and typographic word division — two distinct results built on a shared phonological and morphological analysis.

```python
>>> import slabika
>>> slabika.syllables("najneuveriteľnejšími")
['naj', 'ne', 'u', 've', 'ri', 'teľ', 'nej', 'ší', 'mi']
>>> slabika.hyphenate("Prekladateľský", separator="-")
'Pre-kla-da-teľ-ský'
>>> slabika.break_points("Prekladateľský")
[3, 6, 8, 11]
>>> slabika.hyphenate("Schneiderovská")
'Schnei·de·rov·ská'
>>> slabika.hyphenate("théâtre")
'thé·âtre'
```

The package also handles supported foreign words **inside Slovak text**. The target is Slovak PSP division, not native English, German or French typography. All three foreign routes are connected to `hyphenate`, `break_points`, `divisions` and the Slovak review console. Broader English support requires the optional pronunciation package; German and French pattern adaptation does not.

Po slovensky: [README.sk.md](README.sk.md).

## Why this exists

This did not start as a linguistics project. It started as a typesetting problem: the author needed to set Slovak text automatically — to a measure, justified, with correct hyphenation — without a person walking through the output line by line. A justified line is either broken in a legal place or it is wrong, and the reader sees it immediately.

What existed was a set of TeX patterns from 1992, but not the complete word list and reproducible pipeline that produced it. There was no way to fix one wrong word by changing an inspectable rule and rebuilding everything downstream. A pattern file that cannot be re-derived can only be replaced, never repaired.

The missing piece was not another pattern-matching algorithm but the input: vocabulary, explicit linguistic rules, and traceable adjudication. That is what this repository builds. Fix a rule, add vocabulary, rerun the generator, and obtain new patterns plus a machine-readable report of what changed. Jana Chlebíková published Slovak TeX patterns in 1992; this project claims no priority for Slovak hyphenation itself. Its contribution is an inspectable input-to-pattern chain.

The author's translations exposed another requirement: foreign names with Slovak endings need **Slovak division informed by foreign pronunciation**. Neither treating every letter as Slovak nor blindly applying the foreign language's native hyphenation rules is enough. The two adapter strategies below address this, with explicit limits rather than a claim of universal coverage.

## What a Liang pattern is

Frank Liang's 1983 algorithm, used by TeX and many typesetting systems, matches short letter fragments carrying digits between letters. In `1ná2`, an odd digit permits a break and an even digit forbids one. Overlaid matches take the highest digit at each position. The algorithm does not know grammar.

The companion program `patgen` learns patterns from words with marked divisions. **Pattern quality is bounded by the quality of that training list.** Inconsistent labels are silently generalized; a pattern records no linguistic reason for its output. This project therefore treats the vocabulary and its division rules as the main work, and the learned patterns as a downstream artefact.

| stage | location | licence |
| --- | --- | --- |
| project word inventory and review evidence | `tests/data/` | `CC0-1.0 OR MIT` |
| project engine and training pipeline | `src/slabika/`, `tools/liang_experiment.py` | `Apache-2.0 OR MIT` |
| generated Slovak Liang patterns | `patterns/` | `CC0-1.0 OR MIT` |
| upstream DE/FR pattern inputs | `src/slabika/patterns/foreign/` | MIT, original notices retained |

The training labels are computed by the current engine, not collected from existing Slovak hyphenation dictionaries; see [LICENSING.md](LICENSING.md) §3 for the vocabulary provenance. Foreign-word labels can incorporate the DE/FR pattern adapters or optional English G2P. Reproducibility consequently depends on the exact engine, inventory and optional-runtime environment, not just on the `patgen` command.

Reproducibility is not correctness. Neither internally consistent labels nor agreement with the engine proves correctness under *Pravidlá slovenského pravopisu* (PSP).

### The hard part: the perceived stem

Vowel nuclei, consonant distribution and edge constraints are often mechanical once the linguistic analysis is known. Morpheme seams are harder: the same spelling can be a productive prefix plus a recognizable stem, or part of a lexicalized whole. Spelling alone cannot reliably recover that distinction.

A broad vocabulary provides evidence for testing family rules and contrasting near misses. The preferred remedy is the narrowest supported generalization, not a new override for every word. The code nevertheless contains a small explicit reviewed-foreign breakpoint table alongside lexical reading data; it would be inaccurate to describe the current engine as entirely exception-free. Unresolved cases remain visible in tests and review records.

## Architecture

| module | responsibility |
| --- | --- |
| `slabika.phonology` | shared phoneme inventory: quantity, voicing, place, manner, palatalization |
| `slabika.syllabify` | phonotactic division into spoken syllables |
| `slabika.typo` | written-word break points, route precedence and typographic constraints |
| `slabika.phonotactics` | well-formedness, rhythmic law, preposition vocalization |
| `slabika.language` | shared EN/DE/FR/SK ranking and separate conservative language evidence |
| `slabika.foreign` | explicit foreign reading families and Slovak inflectional junctions |
| `slabika.english`, `slabika.english_projection` | optional English G2P, spelling alignment and limited morphology |
| `slabika.foreign_patterns` | DE/FR native-pattern proposals adapted toward PSP |
| `slabika.review.server`, `slabika.review.foreign` | Slovak live-engine review and separate stored foreign-proposal review |

`syllabify` and `typo` are not a pipeline in which one merely filters the other. They make separate decisions over shared analysis. Spoken `ma·slo` and typographic `mas|lo` can legitimately differ. Foreign typographic support does **not** imply a general EN/DE/FR implementation of `syllables()`.

Typographic results distinguish preferred, equally codified variant and contextual points. For example, `hyphenate("všeobecne")` returns `vše·obec·ne`; `contextual=True` adds a legal but discouraged point, producing `vše·o·bec·ne`. `all_points=True` exposes codified variants. The broad EN and DE/FR adapters currently return preferred points only; they do not independently classify every foreign boundary into all three levels.

## Foreign words in Slovak text

### 1. Language evidence, not a language oracle

`language_scores(word)` ranks English, German, French and Slovak using a shared model of **character 3-, 4- and 5-grams**, including word-edge markers. These are letter fragments inside isolated words, not sequences of words in a sentence. `detect_language(word)` selects the highest-scoring language; the scores are not calibrated probabilities. It can return `None` for unsuitable input or no matches.

Separately, `is_english`, `is_german`, `is_french` and their `*_evidence` functions use language-specific profiles with score, minimum-support and coverage gates. They need not agree with one another or with the shared ranking. Recognized bases and Slovak endings can expose stronger evidence than the whole inflected form. Manual review flags do not override production routing.

The bundled shared profile records a held-out macro accuracy of **91.50%**: EN 88.28%, DE 96.39%, FR 85.67%, SK 95.65%. These are historical measurements against **source-corpus proxy labels**, not independently adjudicated language labels and certainly not division accuracy. Shared spellings were excluded and related spelling families grouped when splitting training, calibration and test data.

### 2. Route precedence

The actual order in `typo._collect_points` matters:

1. Reject non-alphabetic input for automatic whole-word routing; honor the small reviewed-foreign breakpoint table.
2. Try the explicit reading inventory in `foreign_readings.json`. An unambiguous language-specific profile and matching described reading are required. This established route can also handle declared Slovak endings and takes precedence over the newer models.
3. Otherwise try the optional English route. It requires the shared English winner plus English profile evidence **or** membership in the bundled English corpus inventory. Existing local lexical readings are protected.
4. Otherwise try DE/FR pattern adaptation with agreement between the shared ranking and the relevant language-specific evidence, while protecting local lexical readings. For a recognized German base with a Slovak ending, the base's shared ranking can override the whole-word winner.
5. If a route is unavailable or ineligible, retain the existing Slovak/lexical path; unsupported spellings may remain unchanged. Falling back is not proof of a correct foreign division.

Thus the implementation is more than “detect language, then always use its adapter”. For example, the whole-word rank for `Schneiderovská` is Slovak, but the recognized German base permits German–Slovak composition. The established reading of `Sternwoodovi` can likewise be used without requiring the shared whole-word English winner.

### 3. Pronunciation-first: English and explicitly described families

For declared EN/DE/FR families, `foreign.py` maps spelling units to a simplified sound-role representation, applies Slovak PSP rules and maps the resulting offsets back to the original spelling. Multi-letter sound units are preserved; declared morpheme seams and Slovak endings remain part of the analysis.

For broader English coverage, the separately installed `slabika-pronunciation` package predicts **phones plus spelling-to-phone spans**. `english_projection.py` repairs narrowly recognized alignment errors, identifies nuclei and consonant groups, projects PSP-style boundaries back onto written letters, and handles written doubled consonants. This is our division/projection layer over an external trained pronunciation model — not a pronunciation model trained entirely by this project.

Conservative morphology additionally recognizes supported `-knife/-knives`, `-house/-houses` compounds and some `-ly` formations. It checks corpus constituents and compatible pronunciations; arbitrary concatenations are not treated as compounds. The bundled `english_morphology_members.json` contains **55,637 forms**, not IPA, saved division points or human decisions.

The broad route currently accepts ASCII alphabetic spellings. It does not provide general English-base-plus-Slovak-suffix analysis; that support remains limited to the explicit reading families. If the runtime is absent, fails, returns inconsistent spans or cannot completely project a boundary, the route abstains. Runtime presence can change results: `people` is `peo·ple` with the optional route, but the fallback gives `pe·op·le`.

### 4. Pattern-first: German and French

This second strategy uses **TeX patterns**, not running prose or a G2P transcript at division time. `hyph-de-1996.tex` and `hyph-fr.tex` propose native boundaries; local spelling/sound rules adapt them toward PSP. Most native points remain unchanged, so this is a heuristic adapter, not a full phonological or morphological proof for each word.

Examples of explicit adaptations are German `Kat·ze → Ka·tze` (protecting `tz`) and `Fens·ter → Fen·ster`, French `pa·trie → pat·rie`, and selected written hiatus boundaries. `adapt_foreign_word` returns `native_points`, final `points` and named `changes`. Its optional `morpheme_points` accepts independently established seams that take priority over local moves; automatic routing does not discover all such seams.

The explicit API bypasses language detection and supports only DE/FR:

```python
>>> slabika.foreign_hyphenate("patrie", "fr")
'pat·rie'
>>> result = slabika.adapt_foreign_word("Katze", "de")
>>> result.native_points, result.points
((3,), (2,))
>>> result.render("-")
'Ka-tze'
```

Explicit adaptation uses 2/2 letter margins and can normalize decomposed Unicode and handle apostrophes. Automatic whole-word routing is stricter and alphabetic. Neither should be mistaken for native-language hyphenation certification.

### 5. German base with a Slovak ending

A recognized Slovak ending no longer rejects the whole word merely because it contains `á` or another non-German letter. The engine adapts the **German base**, retains its internal boundaries, and uses Slovak rules for the ending and its junction. A consonant-initial suffix preserves the seam; a vowel-initial ending can redistribute the base's final consonants.

At that junction, groups such as `sch`, `ch`, `ck`, `tz` and `ng` are mapped as sound units. German `ng` is kept together on the assumption that its [ŋ] pronunciation survives. A Slovak ending alone does not establish a change to separately pronounced `n+g`; the particular artificial derivative below has no independently documented pronunciation.

| input | current `hyphenate()` output |
| --- | --- |
| `Frankensteinovi` | `Fran·ken·stei·no·vi` |
| `Sternwoodovi` | `Stern·woo·do·vi` |
| `Beaurevoiru` | `Beau·re·voi·ru` |
| `Pickelgeringen` | `Pi·ckel·ge·rin·gen` |
| `Schneiderovská` | `Schnei·de·rov·ská` |
| `Arbeitsunfähigkeitsbescheinigung` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gung` |
| `Arbeitsunfähigkeitsbescheinigungovská` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gu·ngov·ská` |
| `people` (optional G2P) | `peo·ple` |
| `pepper` (optional G2P) | `pep·per` |
| `penknife` (optional G2P) | `pen·knife` |
| `modestly` (optional G2P) | `mo·dest·ly` |
| `penthouse` (optional G2P) | `pent·house` |

These are regression examples verified on 2026-09-12, not a certified PSP gold set. Language inference, pronunciation and morphology remain fallible.

## Installation and review consoles

The core is an **alpha** (`0.1.0`) for Python 3.10+ with no required third-party runtime packages:

```console
python -m pip install -e .
slabika-review
```

German/French pattern resources and explicit foreign readings are bundled. Broader English G2P requires a separately built/installed `slabika-pronunciation==0.1.0` (the `pronunciation` extra declares that dependency; this is not a claim that a public wheel is available). See [pronunciation/README.md](pronunciation/README.md) for native build instructions and limitations. The optional model bundle has separate attribution/provenance concerns and is **not an unrestricted, MIT-only release**.

### Slovak review

`slabika-review` opens the bundled inventory read-only and keeps decisions separately in `review_decisions.sqlite` in the launch directory. `--db` and `--decisions` choose different files. The Slovak console computes the current engine's output, including eligible foreign routes.

On Windows, `run_review_local.bat` is for independent reviewers: it requires no package installation and stores decisions under `%LOCALAPPDATA%\slabika-review`. `run_review.bat` is the maintainer launcher and deliberately opens tracked project decisions.

The language/classification column separates automatic profile flags, human labels and inherited import/AI flags. An undetected language is not assumed to be Slovak. Text uploads can build a worklist; **Random 200** selects an alphabetical block of unreviewed forms. Typographic division and spoken syllabification are reviewed separately.

### Independent DE/FR/EN review

`run_review_de.bat`, `run_review_fr.bat` and `run_review_en.bat` open separate inventories and human decision stores. Default requested ports are SK 8765, DE 8766, FR 8767, EN 8768; the server can select another free port. Equivalent commands, **after generating the foreign inventories**, are:

```console
slabika-review --language de
slabika-review --language fr
slabika-review --language en
```

`--foreign-dir` defaults to `tests/data/foreign_review` in a source checkout. Each language uses `<language>.sqlite` plus `<language>_decisions.sqlite`. Those large local databases are not bundled in the ordinary checkout or wheel; the launchers do not download or generate them automatically.

Unlike Slovak review, foreign review displays **stored proposals and generated IPA**, with status, raw phones, alignment and model provenance. The corpus supplies its language, so this view bypasses automatic language detection. DE/FR division proposals are independent of the displayed G2P estimate. IPA is a broad automatic transcription, not a verified pronunciation; stress is not inferred. Local inventories on 2026-09-12 contain DE **131,150**, FR **35,552** and EN **55,638** forms. German IPA and proposals are complete; French has 6 IPA errors but all division proposals; English has 1 pronunciation/proposal error and 2,306 incomplete projections alongside 53,331 complete experimental proposals. There is no foreign spoken-syllable editor or Chlebíková comparison.

The same word can have independent decisions in all three corpora. Guards reject a wrong-language or Slovak decision database. Confirmations, corrections, undo and JSON export retain separate human ownership. Engine or generated-proposal updates do not rewrite human decisions. Restarting the Slovak server loads changed engine code; restarting a foreign console alone does **not** regenerate stored proposals.

## Foreign-data tools

These maintainer tools run from a checkout. Profile/corpus builders use local source inputs (including TranslateMaster and the English source cache), not material silently downloaded by the library. Inspect each script's arguments/defaults before rebuilding; the router builder uses its imported default paths. The current foreign builder uses Python 3.11's `hashlib.file_digest`, although the core supports 3.10.

| tool | purpose and write behavior |
| --- | --- |
| `tools/build_german_profile.py` | fit DE-vs-SK n-gram evidence and emit profile/audit metadata |
| `tools/build_french_profile.py` | fit FR-vs-SK evidence |
| `tools/build_english_profile.py` | fit EN-vs-SK evidence; optional `--download` for the declared Gutenberg source selection |
| `tools/build_language_router_profile.py` | fit comparable four-language ranking, family-grouped splits and proxy-label metrics |
| `tools/audit_foreign_routing.py` | record corpus-wide routing outputs and compare with an optional baseline |
| `tools/evaluate_foreign_corpora.py` | held-out corpus experiment for language routing and optional pronunciation projection |
| `tools/evaluate_foreign_adapter.py` | export full DE/FR native-vs-adapted TSV and change/coverage statistics; not an accuracy benchmark |
| `tools/build_foreign_review.py` | create/resume separate DE/FR/EN evidence inventories, IPA, proposals, statuses and model hashes; leaves human decisions alone |
| `tools/refresh_english_review.py` | reproject stored EN alignments with shared projection/morphology; dry-run by default, `--apply` backs up and updates generated proposals only |
| `tools/export_english_morphology.py` | export generated EN form membership to the runtime JSON; no IPA or human breakpoints |
| `pronunciation/` | separate native pronunciation package, model manifest, notices and tests |

Typical maintainer sequence, with required local corpora and pronunciation runtime already available:

```console
python tools/build_foreign_review.py --language all
python tools/refresh_english_review.py
python tools/refresh_english_review.py --apply
python tools/export_english_morphology.py
```

The first command seeds all forms and processes pending/error rows in resumable transactions. `--limit` limits evidence generation, not the seeded vocabulary. Successful old evidence is preserved; it is not a blanket refresh. Run the English dry-run and inspect its report before `--apply`; that second stage adds the shared morphology refinement to builder projections. Export membership when its source inventory changes. Runtime and review share projection code, but explicit-corpus review and automatic routing need not return identical results for every form.

## Data and review statistics

As of 2026-09-12, the Slovak inventory contains **206,272 isolated forms** and the decision store has **17,944 records**: 16,742 `confirm`, 1,149 `correct`, 25 `uncertain`, 19 `classify`, 8 `invalid` and 1 `flag`. These are stored row actions, not necessarily completed reviews of typographic division; syllabification and classification are tracked separately. Review decisions are evidence, not normative authority.

The earlier 195,230-form review snapshot recorded 10,210 author decisions (9,519 confirmations, 660 corrections, 22 uncertain, 8 invalid, 1 flagged) and 8,028 distinct forms across four blind audits. Their union was 14,970 forms, with 3,268 in both. These historical figures are not current coverage percentages.

The four frozen blind audits contain 8,100 decisions over 8,028 distinct forms: 6,601 resolved, 1,477 uncertain and 22 invalid. Reviewers received bare forms without engine output or earlier decisions. They were isolated LLM reviewers, not the author.

The tracked dual-model evidence contains 17 runs and 1,346 adjudications over 1,239 distinct forms. Recorded model slots are `claude-opus-5[high]` and `gpt-6-astra[sub][high]`. There were 1,079 independent agreements, 145 agreements after cross-review, 23 after reconciliation and 99 unresolved decisions over 71 distinct forms. These layers overlap and must not simply be added to estimate checked vocabulary.

An earlier author/AI comparison found 49 discrepancies among 350 shared forms, in 14 families, including `dôstojný`, `opotrebovať`, `páčidlo` and foreign names. That is a historical comparison, not a fresh count of currently open disputes. Neither human opinion nor model consensus settles a case without an independent PSP argument.

## How this differs from the 1992 patterns

The current evaluation below finds about one whole-word disagreement in ten between Chlebíková's patterns and the integrated engine. A common source is morphology: a rule engine can retain a recognized prefix seam that a letter-pattern table fails to represent. The author's account of how the 1992 patterns were built is discussed in [docs/hyph-sk-1992-origin.md](docs/hyph-sk-1992-origin.md).

| word | 1992 patterns, 2/3 margins | engine, 2/3 margins |
| --- | --- | --- |
| `bezodkladne` | `be·z·od·kladne` | `bez·od·kladne` |
| `najúspešnejší` | `na·jús·peš·nejší` | `naj·ús·peš·nejší` |
| `trojuholník` | `tro·j·u·hol·ník` | `troj·uhol·ník` |
| `rozorať` | `ro·zo·rať` | `roz·orať` |
| `rozum` | `rozum` | `ro·zum` |
| `administratíva` | `ad·mi·ni·stra·tíva` | `ad·mi·nis·tra·tíva` |

These comparisons are evidence, not a blanket defect list. The 1992 patterns have served Slovak typesetting for decades and remain the bundled baseline in `tex/hyph-sk.tex`.

## Reproduce and evaluate Liang patterns

Install development tools with `python -m pip install -e ".[dev]"` and put `patgen` from TeX Live or MiKTeX on `PATH`. From the repository root:

```console
python tools/liang_experiment.py --mode preferred --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

These commands **replace the tracked pattern files**. The generator reads the working SQLite inventory, accepts `resolved`/`inferred` casing, casefolds and deduplicates, filters unsupported spellings, and splits with salt `slabika-liang-v1`. Outputs include `train.dic`, `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` and `report.json` with corpus counts, input/output hashes, evaluation metrics and sample mismatches.

Both files were **regenerated on 2026-09-12 with the integrated EN/DE/FR routes**. The inventory contains 206,272 rows, SHA-256 `480904efc4f84652bd3d0103f965eaac6b877241c662fcab1525d0a500fd41be`. Of 204,572 eligible source rows, filtering yields 203,919 supported unique words: **163,156 training and 40,763 held out**. The generator excludes retired `invalid` forms and includes 1,035 generated numeral forms in training; 186 corpus numerals are deliberately moved out of the test split to prevent overlap.

| current pattern evaluation (2026-09-12) | exact whole words | point precision | point recall |
| --- | ---: | ---: | ---: |
| slabika preferred, 5,577 patterns | 98.4643% (40,137/40,763) | 99.5399% | 99.4341% |
| Chlebíková 1992 against preferred target | 89.5886% | 96.0266% | 95.3947% |
| slabika permissive, 5,259 patterns | 98.6115% (40,197/40,763) | 99.5682% | 99.5101% |
| Chlebíková 1992 against permissive target | 89.0489% | 96.3900% | 94.9244% |

Both sides used TeX 2/3 minima. This measures **fidelity to the engine at generation time**, not independent PSP correctness or current adapter accuracy. Published SHA-256 values are:

- `patterns/hyph-sk-slabika.tex`: `7f7867d214f3e8afcc3596a19b0bee61b1db3e5c2a7ded509f0e5f74c55f218c`;
- `patterns/hyph-sk-slabika-permissive.tex`: `0a4bfb363880d6cf7eaac5375c6c44369435a6295483f1e3867c36e9ced52368`.

Generation used Python 3.11.9, MiKTeX-PATGEN 1.0 (MiKTeX 26.5), and installed `slabika-pronunciation==0.1.0` with English (US) MFA G2P v3.0.0 (model archive SHA-256 `9923b38d59a8b3e3e322f225c52523c2a6248e5ffc9fd89be151ade2dc97cb02`). Pattern output now explicitly uses LF, matching Git on Windows too. Pin the input revision and runtime/model for hash comparisons; missing G2P can change the labels. The preferred/permissive reports in `patterns/` record this run's full evaluation. Earlier exact-word rates were 98.6866%/98.8240% on a different engine and 40,733-word test; the slight decline is not a controlled ablation or a PSP accuracy measurement. The library uses DE/FR upstream inputs, **not** its own generated Slovak patterns.

A single Liang file cannot encode “prefer this boundary, use another only if necessary”. The preferred and permissive files carry those alternatives separately and should not be loaded together. They contain no whole-word exceptions, do not include the language detector or G2P model, and are not a final release.

### Using patterns elsewhere

Standard Liang data can be used by TeX-compatible tools or converted for Hunspell-style hyphenation consumers such as LibreOffice, OpenOffice, Scribus and Pyphen, or JavaScript engines such as Hyphenopoly. Each target needs format/encoding/minima metadata, registration and testing. Copying a `.tex` file does not install it. Browsers provide no web API for loading an arbitrary custom pattern file into CSS `hyphens: auto`.

These pattern files predict written break points only, not spoken syllables, morphological explanations or three ranked output levels.

## Validation and known limits

```console
python -m pytest
python -m ruff check .
reuse lint
```

For a source-only Windows run, use `set PYTHONPATH=src&& python -m pytest`. Fresh Python processes avoid stale cached model/engine results after code changes.

The 2026-09-12 full run recorded **931 passed, 1 expected failure and 3 provenance/REUSE failures**. Language and review regressions passed; the repository is not yet fully REUSE-clean. The remaining failures concern optional pronunciation licence declarations, the missing root CC-BY-4.0 licence text, and layer classification for the separate pronunciation subtree. Passing linguistic tests does not clear redistribution provenance.

Known limits include uncertain language identity, incomplete morphology, ambiguous spelling-to-sound alignment and heuristic DE/FR adaptation. Unsupported spelling can remain unchanged in `hyphenate`; `syllables` can raise `ValueError` for unsupported alphabetic characters. An empty breakpoint list does not distinguish unsupported input from a valid word with no allowed break. There is no independently adjudicated overall PSP accuracy claim.

## Review and contribute

PSP chapter V is the authority. The independent project restatement is [docs/pravidla-delenia-slov.md](docs/pravidla-delenia-slov.md). The engine, TeX, AI and human review are comparison signals, not authorities. This project is not affiliated with or endorsed by JÚĽŠ SAV.

In review, enter boundaries with `-` or `·` without changing letters; use flags for proper names, foreign words, abbreviations, uncertainty and invalid forms. Explain the relevant PSP rule, pronunciation or morpheme analysis and related/contrasting forms. The **Download corrections** action exports a timestamped `slabika-corrections` JSON of proposals still differing from the engine, with notes and provenance. Send it to the maintainer or attach it to an issue; exporting does not make a proposal canonical.

Vocabulary contributions must be the contributor's own material or public-domain material, not extracts from third-party lexical databases or dictionaries. No source prose, word order or sentence structure is published in the word inventory. See [CONTRIBUTING.md](CONTRIBUTING.md) and [LICENSING.md](LICENSING.md).

## Licensing

| layer | licence |
| --- | --- |
| project source code | `Apache-2.0 OR MIT` |
| project language data | `CC0-1.0 OR MIT` |
| generated Slovak hyphenation patterns | `CC0-1.0 OR MIT` |
| project documentation | `CC0-1.0 OR MIT` |
| bundled upstream DE/FR patterns and Chlebíková baseline | MIT, original notices retained |
| optional pronunciation models | upstream CC-BY-4.0 declarations; separate attribution and provenance review |

Project-owned layers offer MIT as an alternative for consumers unable to use Apache-2.0 or CC0. This does **not** relicense third-party pronunciation models. The optional native runtime and model package has its own notices; operational use is not proof of redistribution clearance. See [pronunciation/MODEL_ATTRIBUTION.md](pronunciation/MODEL_ATTRIBUTION.md) and [pronunciation/THIRD_PARTY_NOTICES.md](pronunciation/THIRD_PARTY_NOTICES.md).

CC0-1.0 expressly addresses the EU `sui generis` database right; MIT itself does not. Recording MIT in a compliance inventory does not undo the independently applied CC0 dedication. Apache-2.0 offers a patent grant; the MIT alternative avoids incompatibilities with GPL-2.0-only and Apache's incompatibility with MPL-1.1.

**CC0-1.0 itself imposes no attribution requirement.** This does not affect moral or personality rights that cannot be waived under applicable law. Redistribution of code still requires the notices imposed by the chosen MIT or Apache-2.0 licence. There is no project Apache `NOTICE` file adding further attribution text. Binding terms live in `LICENSES/` and per-file declarations; [LICENSING.md](LICENSING.md) explains the architecture.

## Author and acknowledgements

Created and maintained by **Peter Bezemek** — <peter.bezemek@gmail.com>, [@pietrobb](https://github.com/pietrobb).

The phoneme classification follows **Emil Páleš**, *Sapfo — parafrázovač slovenčiny: počítačový nástroj na modelovanie v jazykovede* (VEDA, Bratislava, 1994, ISBN 80-224-0109-9), chapter 2 *Fonológia*. Páleš in turn credits **J. Dvončová** (1980) and **J. Horecký** (1977). The classification provides the phonological foundation; the project's syllabification, morphology and division algorithms above it are separate work. Páleš's book does not address hyphenation.

Jana Chlebíková's 1992 Slovak patterns remain the MIT-licensed comparison baseline. The benchmark methodology and focus on training-list quality also draw on O. Metelka and P. Sojka, *Hyph-bench: Benchmark Dataset of Hyphenated Words for Generating Hyphenation Patterns*, RASLAN 2025.
