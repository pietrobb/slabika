# slabika

Slovak syllabification and typographic word division — two distinct results built on a shared phonological and morphological analysis.

```python
>>> import slabika
>>> slabika.syllables("spravodlivosť")
['spra', 'vod', 'li', 'vosť']
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

### Why a new Slovak pattern set

Jana Chlebíková published Slovak Liang patterns in 1992; they have served Slovak typesetting for decades and remain the bundled baseline in `tex/hyph-sk.tex`. Her method was a careful manual transcription of grammatical rules into Liang notation, not `patgen` training over a published word list. It was an important practical solution, and this project claims no priority for Slovak hyphenation. The primary account and later analysis are summarized in [docs/hyph-sk-1992-origin.md](docs/hyph-sk-1992-origin.md).

The historical file is nevertheless not a sufficient foundation for a system that must be inspectable and improvable. Its complete derivation cannot be rerun; letter fragments retain neither a linguistic explanation nor the morphological analysis behind a boundary; and its treatment of foreign words and exceptions was deliberately limited. This does not make the 1992 work poor. It makes it a valuable baseline whose practical limits can now be measured and repaired.

Two different measurements show the size of those limits:

| evidence | current project | Chlebíková 1992 | what it establishes |
| --- | ---: | ---: | --- |
| exact held-out words against the preferred engine target, TeX minima 2/3 | **98.4913%** | **89.5641%** | reproducibility of the engine, not PSP correctness |
| accepted under PSP among 21,514 resolved historical disagreements | **21,508** | **6,196** | adjudication of the disagreement set, not random overall accuracy |

The second row comprises 15,313 cases where only the frozen engine was accepted, 6,195 where both outputs were accepted, 1 where only Chlebíková was accepted and 5 where neither was accepted. Another 1,659 cases remain unresolved. The audit was AI-assisted and deliberately contains only disagreements, so it is strong diagnostic evidence rather than an independent accuracy percentage; its full methodology appears under [PSP-adjudicated comparison set](#psp-adjudicated-comparison-set).

A common source of difference is **recognized morphological structure**: a prefix plus base, the members of a compound, or a base plus a derivational or grammatical suffix. A letter-pattern table sees recurring character fragments but does not retain that analysis. The following are 21 verified morphological examples, not cases declared wrong merely because the outputs differ. `·` marks an available line break. The 1992 column applies the TeX left/right minima 2/3; the current-engine column is the literal result of `hyphenate(word)`, whose API does not apply those TeX edge minima.

| kind | word | recognized structure | 1992 patterns | current engine |
| --- | --- | --- | --- | --- |
| prefix and base | `bezodkladne` | `bez- + od- + klad-` | `be·z·od·kladne` | `bez·od·klad·ne` |
| prefix and base | `najúspešnejší` | `naj- + úspeš- + nejš-` | `na·jús·peš·nejší` | `naj·ús·peš·nej·ší` |
| prefix and base | `rozkroj` | `roz- + kroj-` | `rozk·roj` | `roz·kroj` |
| nested prefixes | `neočistí` | `ne- + o- + čist-` | `ne·očistí` | `ne·o·čis·tí` |
| prefix and base | `predúradné` | `pred- + úrad- + n-` | `pre·dú·radné` | `pred·úrad·né` |
| compound | `trojuholník` | `troj- + uhol- + ník` | `tro·j·u·hol·ník` | `troj·uhol·ník` |
| compound | `samoobslužný` | `samo- + ob- + služ- + n-` | `sa·mo·obs·lužný` | `sa·mo·ob·služ·ný` |
| compound | `sebaistý` | `seba- + ist-` | `se·baistý` | `se·ba·is·tý` |
| compound | `pravouhlý` | `pravo- + uhl-` | `pra·vouhlý` | `pra·vo·uh·lý` |
| compound | `novovzbudený` | `novo- + vzbud- + en-` | `no·vovz·bu·dený` | `no·vo·vzbu·de·ný` |
| compound | `mäsožravce` | `mäso- + žrav- + ec` | `mä·sož·ravce` | `mä·so·žrav·ce` |
| compound | `pomstychtivý` | `pomsty- + chtiv-` | `po·mstych·tivý` | `pom·sty·chti·vý` |
| derivation | `kováčsky` | `kováč- + sk-` | `ko·váčsky` | `ko·váč·sky` |
| derivation | `dedičstiev` | `dedič- + stv-` | `de·dičs·tiev` | `de·dič·stiev` |
| derivation | `hráčske` | `hráč- + sk-` | `hráčske` | `hráč·ske` |
| derivation | `šéfstvom` | `šéf- + stv-` | `šéfs·tvom` | `šéf·stvom` |
| derivation | `víťazstvo` | `víťaz- + stv-` | `ví·ťazs·tvo` | `ví·ťaz·stvo` |
| numeral derivative | `Dvanástka` | `dvanásť- + k-` | `Dva·nás·tka` | `Dva·nást·ka` |
| compound numeral | `dvadsaťdva` | `dvadsať- + dva` | `dvad·saťdva` | `dvad·sať·dva` |
| compound numeral | `dvestotri` | `dve- + sto- + tri` | `dve·stotri` | `dve·sto·tri` |
| compound numeral | `stodvadsaťdva` | `sto- + dvadsať- + dva` | `stod·vad·saťdva` | `sto·dvad·sať·dva` |

The different edge policies explain why the literal engine result `Dva·nást·ka` contains a final point absent from the 2/3 TeX-pattern result. Pattern evaluation filters engine targets to the same TeX minima; this table deliberately shows the public API unchanged. These examples do not turn every other disagreement into a defect: each case must still be decided under PSP.

### The hard part: the perceived stem

Vowel nuclei, consonant distribution and edge constraints are often mechanical once the linguistic analysis is known. Morpheme seams are harder: the same spelling can be a productive prefix plus a recognizable stem, or part of a lexicalized whole. Spelling alone cannot reliably recover that distinction.

A broad vocabulary provides evidence for testing family rules and contrasting near misses. The preferred remedy is the narrowest supported generalization, not a new override for every word. The code nevertheless contains a small explicit reviewed-foreign breakpoint table alongside lexical reading data; it would be inaccurate to describe the current engine as entirely exception-free. Unresolved cases remain visible in tests and review records.

### Where morphological boundaries come from

There is no single database of finished boundaries. `get_morpheme_parts()` combines three layers: manually maintained and regression-tested rules for prefixes, suffixes and ambiguous families; guarded rules for numerals, prefixoids and particular compounds; and a generated inventory for productive compounds. `syllabify` and `typo` share that analysis but apply their own spoken-syllable and written-division rules inside each recognized part. A morpheme seam takes precedence over mechanical consonant redistribution in the preferred typographic result.

The productive compound layer is built by `python tools/build_composita.py` from the local Sapfo lexicon at `../Sapfo/sapfo/data/sapfo_lexicon.db`. That source database is not part of this repository: a clean checkout uses the finished JSON but cannot rebuild it without the local sibling Sapfo project. The generator derives first members from adverb and adjective stems and from noun stems with linking `-o-/-e-`; it separately records possible second-member heads from adjective, adverb, noun and verb entries. The current `src/slabika/data/composita.json` contains **59,506 first members** and **69,718 second-member heads**. This JSON is versioned, packaged and is all the runtime reads: users need neither Sapfo nor the source database. The statistically induced `morphs.json` is used by an audit tool, not for automatic production decisions about Slovak boundaries.

The inventory does not mean “break after every known string”. The engine requires both a credible first member and an attested second-member head followed only by an allowed inflectional tail. It does not combine two weak inferences, and guards several collisions with prefixes and endings. This lets it infer unseen `žlto|modrý`, `svetlo|zelený` or `modro|zelenkastý`, while rejecting a false analysis such as `jahodo|vých`.

Ordinary users do **not** regenerate this inventory. A maintainer rebuilds it only after changing the source lexicon or `tools/build_composita.py`; adding words to the review corpus alone does not change it. Do not edit the generated JSON directly. Add an ordinary productive native member to the source lexicon or `CURATED_NATIVE`, then rebuild. A risky short prefixoid or numeral belongs in `CURATED_NUMERALS` for artefact provenance and also in the guarded runtime layer `_SK_COMPOSITA`/`_licenses_compositum`. Prefixes, suffixes and exceptional families are maintained directly in `syllabify.py` and need no JSON rebuild. Every change needs positive and contrastive regression tests, followed by corpus-wide impact and existing-decision checks.

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

The core is an **alpha** (`0.2.0`) for Python 3.10+ with no required third-party runtime packages:

```console
python -m pip install slabika
slabika-review
```

For an editable source checkout with the test and licence tools, use `python -m pip install -e ".[dev]"` instead.

German/French pattern resources and explicit foreign readings are bundled. Broader English G2P requires a separately built/installed `slabika-pronunciation==0.1.0`; it is not on PyPI and is deliberately not declared as an installable extra of the core 0.2.0 release. See [pronunciation/README.md](pronunciation/README.md) for native build instructions and limitations. The optional model bundle has separate attribution/provenance concerns and is **not an unrestricted, MIT-only release**.

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

As of **2026-09-14**, the tracked Slovak data has this current state:

| metric | count |
| --- | ---: |
| inventory rows | **206,272** |
| active unique forms shown by the review console after folding case-only aliases | **206,200** |
| stored Human decision rows (raw table) | **19,737** |
| active canonical forms with any Human evidence | **19,572 (9.49%)** |
| typographic divisions reviewed | **19,406 (9.41%)** — 18,236 confirms, 1,170 corrections |
| spoken syllabifications reviewed | **346 (0.17%)** — 264 forms have both outputs reviewed |

The raw decision rows comprise 18,448 latest `confirm`, 1,218 `correct`, 37 `classify`, 25 `uncertain`, 8 `invalid` and 1 `flag` actions. Raw rows include deleted forms and casing aliases, so they are not a coverage numerator; coverage uses the console's current canonical view. Classification and syllabification are tracked separately from typographic division. Review decisions are evidence, not normative authority.

The four frozen blind audits contain 8,100 decisions over 8,028 distinct forms: 6,601 resolved, 1,477 uncertain and 22 invalid. Reviewers received bare forms without engine output or earlier decisions. They were isolated LLM reviewers, not the author.

The tracked dual-model evidence contains 17 runs and 1,346 adjudications over 1,239 distinct forms. Recorded model slots are `claude-opus-5[high]` and `gpt-6-astra[sub][high]`. There were 1,079 independent agreements, 145 agreements after cross-review, 23 after reconciliation and 99 unresolved decisions over 71 distinct forms. These layers overlap and must not simply be added to estimate checked vocabulary.

### PSP-adjudicated comparison set

The tracked `tests/data/review_decisions.sqlite` contains the immutable audit queue `engine-chlebikova-exhaustive-2026-08-25-v1`: all **23,173 unique forms** on which the frozen engine and the bundled 1992 patterns disagreed with the same 2/3 margins. The forms were sorted deterministically and assessed in 232 batches of at most 100. Each comparison records the original outputs, proposed PSP division and variants, separate verdicts for the engine and Chlebíková, a PSP citation, rationale and unresolved classification. Human decisions, blind reviews and dual-model adjudications remain separate evidence rather than votes that overwrite one another.

The recorded outcomes are **15,313 engine only**, **6,195 both correct**, **1 Chlebíková only**, **5 neither correct** and **1,659 unresolved**: 21,514 resolved comparisons, not 23,173 certified answers. The counts can be reproduced from `psp_comparisons` by filtering on that audit ID and grouping by `comparison_outcome`; every frozen item has a matching comparison row. This is a **PSP-adjudicated comparison set**, not an independent random gold benchmark: the exhaustive PSP interpretation was AI-assisted, its selection is concentrated entirely on historical disagreements, and unresolved foreign pronunciation was preserved rather than guessed.

At the 2026-09-14 snapshot, active non-deleted Human rows overlap the PSP queue on **2,236 forms**; 2,224 have a comparable Human division. PSP resolved 1,981 of those comparable cases: Human matches at least one admissible PSP variant in **1,858** and differs in **123**, a **93.79%** agreement rate. The remaining 243 comparable cases are unresolved in the PSP layer. This overlap does not make the two evidence layers identical or independent gold benchmarks, and neither human opinion nor model consensus settles a case without a PSP argument.

## Reproduce and evaluate Liang patterns

Install development tools with `python -m pip install -e ".[dev]"` and put `patgen` from TeX Live or MiKTeX on `PATH`. From the repository root:

```console
python tools/liang_experiment.py --mode preferred --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

These commands **replace the tracked pattern files**. The generator reads the working SQLite inventory, accepts `resolved`/`inferred` casing, casefolds and deduplicates, filters unsupported spellings, and splits with salt `slabika-liang-v1`. Outputs include `train.dic`, `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` and `report.json` with corpus counts, input/output hashes, evaluation metrics and sample mismatches.

Both files were **regenerated on 2026-09-13 with the integrated EN/DE/FR routes**. The inventory contains 206,272 rows, SHA-256 `480904efc4f84652bd3d0103f965eaac6b877241c662fcab1525d0a500fd41be`. Of 204,572 eligible source rows, filtering yields 203,919 supported unique words: **163,156 training and 40,763 held out**. The generator excludes retired `invalid` forms and includes 1,035 generated numeral forms in training; 186 corpus numerals are deliberately moved out of the test split to prevent overlap.

| current pattern evaluation (2026-09-13) | exact whole words | point precision | point recall |
| --- | ---: | ---: | ---: |
| slabika preferred, 5,581 patterns | 98.4913% (40,148/40,763) | 99.5588% | 99.4415% |
| Chlebíková 1992 against preferred target | 89.5641% | 95.9699% | 95.3872% |
| slabika permissive, 5,244 patterns | 98.6311% (40,205/40,763) | 99.5833% | 99.5176% |
| Chlebíková 1992 against permissive target | 88.9655% | 96.3333% | 94.8878% |

Both sides used TeX 2/3 minima. This measures **fidelity to the engine at generation time**, not independent PSP correctness or current adapter accuracy. Published SHA-256 values are:

- `patterns/hyph-sk-slabika.tex`: `e56e2e9c72df9463ed9def08fd87d5c0345e5dc40ce0aeaa2046679628942b6b`;
- `patterns/hyph-sk-slabika-permissive.tex`: `564f45a25cdfa5f6589d86c061d83b2e0da8be2f9a710c98c51756556d00e4d1`.

Generation used Python 3.11.9, MiKTeX-PATGEN 1.0 (MiKTeX 26.5), and installed `slabika-pronunciation==0.1.0` with English (US) MFA G2P v3.0.0 (model archive SHA-256 `9923b38d59a8b3e3e322f225c52523c2a6248e5ffc9fd89be151ade2dc97cb02`). Pattern output explicitly uses LF, matching Git on Windows too. Pin the input revision and runtime/model for hash comparisons; missing G2P can change the labels. The preferred/permissive reports in `patterns/` record the release run's full evaluation. The library uses DE/FR upstream inputs, **not** its own generated Slovak patterns.

A single Liang file cannot encode “prefer this boundary, use another only if necessary”. The preferred and permissive files carry those alternatives separately and should not be loaded together. They contain no whole-word exceptions and do not include the language detector or G2P model. They are versioned release artefacts alongside the Python package, but the library does not load them automatically.

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

The 2026-09-13 release run recorded **938 passed, 1 expected failure and no unexpected failures**. Ruff and REUSE 3.3 checks also passed. REUSE compliance records the declared licences and notices; it does not resolve the still-uncertain provenance and rights clearance of the optional MFA models' training data.

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
