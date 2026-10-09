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

The training labels are computed by the current engine, not collected from existing Slovak hyphenation dictionaries; see [LICENSING.md](LICENSING.md) §3 for the vocabulary provenance. Foreign-word labels can incorporate the DE/FR pattern adapters or optional English G2P. Reproducibility consequently depends on the exact engine, inventory and optional-runtime environment, not just on the `patgen` command. Concretely, the chain is re-runnable from the **published source archive** as well as from a Git checkout at the tagged revision: the sdist carries the corpus, the review evidence, the grammar, the labelling engine and the training pipeline, and the published report records every input hash so a third party can tell whether their inputs match. `patgen` and the optional `slabika-pronunciation` runtime are external toolchain and must be installed separately. The wheel is runtime only and deliberately carries no databases, so a `pip install` user can use and inspect the library but cannot re-derive the patterns; see [Reproduce from the published source archive](#reproduce-from-the-published-source-archive).

Reproducibility is not correctness. Neither internally consistent labels nor agreement with the engine proves correctness under *Pravidlá slovenského pravopisu* (PSP).

### Why a new Slovak pattern set

Jana Chlebíková published Slovak Liang patterns in 1992; they have served Slovak typesetting for decades and remain the bundled baseline in `tex/hyph-sk.tex`. Her method was a careful manual transcription of grammatical rules into Liang notation, not `patgen` training over a published word list. It was an important practical solution, and this project claims no priority for Slovak hyphenation. The primary account and later analysis are summarized in [docs/hyph-sk-1992-origin.md](docs/hyph-sk-1992-origin.md).

The historical file is nevertheless not a sufficient foundation for a system that must be inspectable and improvable. Its complete derivation cannot be rerun; letter fragments retain neither a linguistic explanation nor the morphological analysis behind a boundary; and its treatment of foreign words and exceptions was deliberately limited. This does not make the 1992 work poor. It makes it a valuable baseline whose practical limits can now be measured and repaired.

One measurement shows the size of those limits:

| evidence | current project | Chlebíková 1992 | what it establishes |
| --- | ---: | ---: | --- |
| exact held-out words against the preferred engine target, TeX minima 2/3 | **98.7438%** | **90.4338%** | reproducibility of the engine, not PSP correctness |

A common source of difference is **recognized morphological structure**: a prefix plus base, the members of a compound, or a base plus a derivational or grammatical suffix. A letter-pattern table sees recurring character fragments but does not retain that analysis. The following are 21 verified morphological examples, not cases declared wrong merely because the outputs differ. `·` marks an available line break. The 1992 column applies the TeX left/right minima 2/3; the current-engine column is the literal result of `hyphenate(word)`, whose API does not apply those TeX edge minima.

| kind | word | recognized structure | 1992 patterns | current engine |
| --- | --- | --- | --- | --- |
| prefix and base | `bezodkladne` | `bez- + od- + klad-` | `be·z·od·kladne` | `bez·od·klad·ne` |
| prefix and base | `najúspešnejší` | `naj- + úspeš- + nejš-` | `na·jús·peš·nejší` | `naj·úspeš·nej·ší` |
| prefix and base | `rozkroj` | `roz- + kroj-` | `rozk·roj` | `roz·kroj` |
| nested prefixes | `neočistí` | `ne- + o- + čist-` | `ne·očistí` | `ne·očis·tí` |
| prefix and base | `predúradné` | `pred- + úrad- + n-` | `pre·dú·radné` | `pred·úrad·né` |
| compound | `trojuholník` | `troj- + uhol- + ník` | `tro·j·u·hol·ník` | `troj·uhol·ník` |
| compound | `samoobslužný` | `samo- + ob- + služ- + n-` | `sa·mo·obs·lužný` | `sa·mo·ob·služ·ný` |
| compound | `sebaistý` | `seba- + ist-` | `se·baistý` | `se·ba·is·tý` |
| compound | `pravouhlý` | `pravo- + uhl-` | `pra·vouhlý` | `pra·vo·uh·lý` |
| compound | `novovzbudený` | `novo- + vzbud- + en-` | `no·vovz·bu·dený` | `no·vo·vzbu·de·ný` |
| compound | `mäsožravce` | `mäso- + žrav- + ec` | `mä·sož·ravce` | `mä·so·žrav·ce` |
| compound | `pomstychtivý` | `pomsty- + chtiv-` | `po·mstych·tivý` | `po·msty·chti·vý` |
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

The productive compound layer is built by `python tools/build_composita_grammar.py` from the project's corpus surface forms, local inflectional grammar and an explicitly attributed supplement. The packaged `src/slabika/data/composita.json` contains **11,470 first members** and **20,207 second-member heads**, with role-specific paradigms and input fingerprints. Runtime reads only this versioned JSON; ordinary use requires no corpus database. Rebuilding requires the project corpus and the build-time grammar. Both are tracked in this Git repository and both ship in the published source archive; neither is in the wheel. The statistically induced `morphs.json` is an audit aid and does not determine production boundaries.

The inventory does not mean “break after every known string”. The engine requires both a credible first member and an attested second-member head followed only by an allowed inflectional tail. It does not combine two weak inferences, and guards several collisions with prefixes and endings — among them the verb-forming `-ova-`, which ends in the same `-o-` a linking vowel does, so an inferred first member may not divide `rezervovalo` or `talentovanosť`. This lets it infer unseen `žlto|modrý`, `svetlo|zelený` or `modro|zelenkastý`, while rejecting a false analysis such as `jahodo|vých`.

Ordinary users do **not** regenerate this inventory; they use the packaged JSON. Validation covers **206,205 corpus rows**, with linguistic decisions assessed under PSP. The test suite reports **over 1,570 passing tests with one expected failure**. These checks do not guarantee correct analysis of every word. Data sources and licences are documented in [LICENSING.md](LICENSING.md).

### How the generator obtains roots and stems

Here, a “root” is the technical base of an inflectional paradigm, not necessarily a minimal etymological root. `tools/build_composita_grammar.py` works as follows:

1. Read alphabetic surface forms from `forms.form` in `tests/data/translatemaster_hyphenation_working.sqlite`, lowercase and deduplicate them. **Human decisions and stored divisions are not inputs.** The original vocabulary comes from the author's prose and translations; later additions include Wikidata vocabulary and municipality names, plus AI-generated word lists manually checked by the maintainer. See [LICENSING.md](LICENSING.md) §3 for the provenance limits.
2. Add separately attributed AI-authored forms from `tests/data/grammar_supplement.json`, such as missing inflections of `gram` or `plavebný`, without changing the original database. These are explicit lexical assumptions, not independent evidence that the synthesis algorithm is correct.
3. Try noun, adjective, pronoun and verb paradigms from the project's local inflectional grammar. Remove a candidate ending, synthesize the paradigm and require an exact round trip plus its citation form in the corpus. Automatic acceptance requires **at least three distinct supporting forms other than the lemma** owned by that analysis after competition; syncretic cells do not count repeatedly. Ownership is a heuristic, not semantic disambiguation of homographs.
4. Derive first members with linking `-o-/-e-`, using oblique noun stems where appropriate (`vietor → vetr- → vetro-`). Store **exact licensed second-member forms by grammatical role**, including alternations, participles and separately recorded derivations. Universal inflectional endings are not appended to every stem.
5. Declare bound members (`biblio-`, personal `-graf`, adjectival `-tváry`, toponymic `-plukovo`) and indeclinable first members (`všade-`) separately in the supplement. An authored bound head needs at least one original-corpus compound with a recognized first member and a valid form of the declared paradigm. This verifies occurrence of an **authored rule**, not statistical induction; it does not lower the three-form induction threshold or fabricate independent support cells.

The generator derives stems from corpus forms using inflectional rules whose paradigm tables follow the grammatical description in Páleš (1994), pp. 41–47. Data sources are documented in [LICENSING.md](LICENSING.md). PSP is the authority for word division.

### Candidate generation and verification

Maintainers first save a full-API baseline before changing the engine/inventory. Each output path must be new:

```console
python tools/compare_composita.py --output scratch/baseline.json
python tools/build_composita_grammar.py --output scratch/grammar-audit.json --runtime-output scratch/grammar-runtime.json
python tools/compare_composita.py --inventory scratch/grammar-runtime.json --baseline scratch/baseline.json --output scratch/comparison.json --allow-engine-changes --check
python tools/review_composita_changes.py --report scratch/comparison.json --reviews tests/data/grammar_release_review.json --allowlist scratch/approved.json --audit-output scratch/review-audit.json
python tools/compare_composita.py --inventory scratch/grammar-runtime.json --baseline scratch/baseline.json --output scratch/comparison-checked.json --allow-engine-changes --allowlist scratch/approved.json --check
```

The first comparison intentionally exits unsuccessfully when differences exist, but saves its report. `--allow-engine-changes` permits comparing revisions; it **does not approve differences**. Review materialization accepts only exact transitions matching recorded PSP decisions; unapproved changes and stale approvals fail the final gate. All four `hyphenate`/`break_points` modes and `divisions` are compared, not just preferred division. AI decisions do not overwrite Human review.

The audit retains analyses, support forms and authored declarations; runtime JSON retains the inventory and input metadata. SHA-256 identifies normalized corpus forms, the supplement, grammar modules and builder, not legal permission. The builder refuses to overwrite production and checks for source changes during generation. Promotion requires the full-API quality gate and an explicit maintainer review of documented source declarations and any remaining uncertainty. A custom `--corpus` does not automatically include the standard supplement; pass `--supplement` explicitly.

Build-time grammar, the word inventory and the review databases are absent from the wheel and present in the source archive. Regeneration therefore works from either a Git checkout or `pip download --no-binary :all: slabika`; ordinary library use requires neither.

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

At that junction, groups such as `sch`, `ch`, `ck`, `tz` and `ng` are mapped as sound units. Indivisibility alone does not decide which side of a boundary contains the unit: stem-final German `ng` remains the coda [ŋ] because it cannot open the following Slovak syllable. A Slovak ending alone does not establish a change to separately pronounced `n+g`; the particular artificial derivative below has no independently documented pronunciation.

| input | current `hyphenate()` output |
| --- | --- |
| `Frankensteinovi` | `Fran·ken·stei·no·vi` |
| `Sternwoodovi` | `Stern·woo·do·vi` |
| `Beaurevoiru` | `Beau·re·voi·ru` |
| `Pickelgeringen` | `Pi·ckel·ge·rin·gen` |
| `Schneiderovská` | `Schnei·de·rov·ská` |
| `Arbeitsunfähigkeitsbescheinigung` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gung` |
| `Arbeitsunfähigkeitsbescheinigungovská` | `Ar·beits·un·fä·hig·keits·be·schei·ni·gung·ov·ská` |
| `people` (optional G2P) | `peo·ple` |
| `pepper` (optional G2P) | `pep·per` |
| `penknife` (optional G2P) | `pen·knife` |
| `modestly` (optional G2P) | `mo·dest·ly` |
| `penthouse` (optional G2P) | `pent·house` |

These are regression examples verified on 2026-09-12, not a certified PSP gold set. Language inference, pronunciation and morphology remain fallible.

## Installation and review consoles

The core is an **alpha** (`0.4.0`) for Python 3.10+ with no required third-party runtime packages:

```console
python -m pip install slabika
slabika-review --db /path/to/local/inventory.sqlite
```

For an editable source checkout with the test and licence tools, use `python -m pip install -e ".[dev]"` instead.

German/French pattern resources and explicit foreign readings are bundled. Broader English G2P requires a separately built/installed `slabika-pronunciation==0.1.0`; it is not on PyPI and is deliberately not declared as an installable extra of the core 0.4.0 release. See [pronunciation/README.md](pronunciation/README.md) for native build instructions and limitations. The optional model bundle has separate attribution/provenance concerns and is **not an unrestricted, MIT-only release**.

### Slovak review

From 0.4.0, working inventories and review databases are excluded from the wheel but ship in the source archive, and they remain tracked in the Git repository. A source checkout or an unpacked sdist therefore finds its corpus automatically and needs no extra arguments. `slabika-review --db /path/to/inventory.sqlite` is only needed to open an inventory kept outside the checkout; it opens that file read-only and keeps decisions in `review_decisions.sqlite` in the launch directory, while `--decisions` selects another decision store. The Slovak console computes the current engine's output, including eligible foreign routes.

On Windows, `run_review_local.bat` is for independent reviewers: it requires no package installation and stores decisions under `%LOCALAPPDATA%\slabika-review`. `run_review.bat` is the maintainer launcher and deliberately opens tracked project decisions.

The project decisions are tracked compressed, as `tests/data/review_decisions.sqlite.xz` (13.0 MB instead of 56.4 MB). The console unpacks the working copy `tests/data/review_decisions.sqlite` next to it on demand: when it is missing, or when a newer `.xz` arrived with `git pull` and the copy has no changes of its own. On a clean stop (Ctrl+C) it packs new decisions back into the `.xz`, which is then the file to commit. If both the `.xz` and the unpacked copy changed, it refuses to start rather than overwrite either one. The same steps are available by hand: `python -m slabika.review.packed status|unpack|pack [--force]`. A decision store passed with `--decisions` that has no `.xz` next to it is opened as before.

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

As of **2026-10-09**, the tracked Slovak data has this current state:

| metric | count |
| --- | ---: |
| inventory rows | **206,184** |
| active unique forms shown by the review console after folding case-only aliases | **206,112** |
| stored Human decision rows (raw table) | **27,168** |
| active canonical forms with any Human evidence | **26,837 (13.02%)** |
| typographic divisions reviewed | **26,661 (12.94%)** — 25,002 confirms, 1,659 corrections |
| spoken syllabifications reviewed | **349 (0.17%)** — 266 forms have both outputs reviewed |

The raw decision rows comprise 25,293 latest `confirm`, 1,709 `correct`, 121 `classify`, 36 `uncertain`, 8 `invalid` and 1 `flag` actions. Raw rows include deleted forms and casing aliases, so they are not a coverage numerator; coverage uses the console's current canonical view. Classification and syllabification are tracked separately from typographic division. Review decisions are evidence, not normative authority.

The four frozen blind audits contain 8,100 decisions over 8,028 distinct forms: 6,601 resolved, 1,477 uncertain and 22 invalid. Reviewers received bare forms without engine output or earlier decisions. They were isolated LLM reviewers, not the author.

### Versioned dual-model verdicts

`tests/data/review_decisions.sqlite` (tracked as `review_decisions.sqlite.xz`) files every dual-model run together with the exact inputs that produced it. `ai_rule_sets`, `ai_prompts` and `ai_schemas` keep the full rules text, prompt and response schema under version labels; `ai_models` names the models; `engine_versions` records the package version, Git commit, uncommitted-change flag and content hash of the engine that the run was compared with. `ai_runs` links a run to all of these and keeps its compressed transcript, `ai_verdicts` holds one outcome per form, and `ai_model_answers` keeps every model answer in every round. The tables are append-only: a changed rules text becomes a new version, and older verdicts remain readable together with the rules they were produced under. `tools/review/import_ai_run.py` refuses a run whose per-batch hashes do not match the texts it is filed under.

The first filed run, `blind1000-20260930` (rules r1, prompt v4, schema s1, `claude-opus-5-5[high]` with `gpt-6.1-sol[sub][high]`), covers 1,000 forms sampled uniformly from the inventory: 862 independent agreements, 26 agreements after review, 40 uncertain, 2 unresolved disagreements and 70 invalid responses. Of the 888 agreed forms, 860 match the engine output at run time and 28 differ. Model agreement is advisory evidence, not a PSP verdict, and never overwrites a Human decision.

Eleven runs are filed so far, **33,331 verdicts over 33,323 distinct forms** with 67,934 stored model answers:

| run | rules / prompt / schema | forms | agreed (independent + after review) | uncertain | unresolved | invalid | agreed, differs from engine at run time |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `blind1000-20260930` | r1 / v4 / s1 | 1,000 | 888 (862 + 26) | 40 | 2 | 70 | 28 |
| `blind3331-20261001` | r5 / v8 / s2 | 3,331 | 3,137 (3,083 + 54) | 172 | 2 | 20 | 268 |
| `blind3000-20261002` | r5 / v8 / s2 | 3,000 | 2,849 (2,818 + 31) | 128 | 3 | 20 | 89 |
| `blind2000-20261003` | r6 / v8 / s2 | 2,000 | 1,845 (1,831 + 14) | 92 | 3 | 60 | 44 |
| `blind3000b-20261003` | r6 / v8 / s2 | 3,000 | 2,768 (2,735 + 33) | 130 | 2 | 100 | 63 |
| `blind3000c-20261004` | r7 / v8 / s2 | 3,000 | 2,861 (2,834 + 27) | 136 | 3 | 0 | 61 |
| `blind3000d-20261004` | r7 / v8 / s2 | 3,000 | 2,557 (2,466 + 91) | 424 | 9 | 10 | 447 |
| `blind3000e-20261005` | r7 / v8 / s2 | 3,000 | 2,674 (2,570 + 104) | 311 | 15 | 0 | 268 |
| `blind4000f-20261007` | r7 / v8 / s2 | 4,000 | 3,788 (3,659 + 129) | 197 | 15 | 0 | 206 |
| `blind4000g-20261008` | r7 / v8 / s2 | 4,000 | 3,874 (3,775 + 99) | 109 | 17 | 0 | 72 |
| `blind4000h-20261008` | r7 / v8 / s2 | 4,000 | 3,861 (3,766 + 95) | 127 | 12 | 0 | 58 |

Agreed forms that differed from the engine were judged by the operator. Accepted divisions were applied to the engine for the **whole word family**, not to the single form, and are pinned by regression tests; rejected ones keep the engine division and are pinned as well. After `blind3000b`, 60 of its 63 differences were accepted and propagated to their families (for example `kar·dio·ló·go·via`, `bú·ria·ce` with a spoken diphthong but `špe·ci·a·lis·ta` with a spoken hiatus, `ne·opý·tam`, `úsko·koch`, `úc·ty·hod·ný`, `von·kajš·ko·vo`); the operator kept `prázd·nej·ších`, `sto·trid·sať·šty·ri` and `šty·rid·sia·ti·de·via·ti`. Twelve earlier Human confirmations that contradicted the accepted families were rewritten through the audited decision path, which keeps the previous value in `decision_log.previous_json`.

After `blind3000c`, the operator accepted 57 of its 61 differences: a root-initial vowel or short onset after a prefix or at the word start stays with the root (`ohľa·de`, `ozveš`, `usta·vič·ný`, `po·obe·do·val`, `za·opat·ru·je`, `ideo·ló·gi·ou`), a number of consonant clusters move to the following syllable (`di·va·dla·mi`, `ka·di·dlu`, `ha·cko·va·nia`, `ne·jde·te`, `šnu·ro·va·čky`) or stay with the preceding one (`jem·nos·ti`, `vi·ce·pre·zi·den·tom`, `pries·tran·ný` like `pries·tor`, `zú·čast·ňo·va·li`), and a few foreign words follow their spoken form (`In·di·a·mi`, `koz·mo·nau·ta`, `grape·frui·te`). Nine of the accepted families overturned earlier pinned decisions (`ot·vo·rí`, `po·msta`, `odo·pie·rať`, `záz·rak`, `naš·la`, `očist·ca`, `za·mest·nan·ci`, `tan·co·va·čky`, `upra·to·va·čka`). The operator kept `bejz·ba·lis·ta`, `pa·žra·vo`, `pot·ký·na·jú` and `na·vrst·ve·né`. Twenty-three Human confirmations in the changed families were rewritten through the same audited path. The run was launched with the label r6 although its rules text already carried the `blind3000b` additions to the compound first parts; it is filed as r7, and the importer records such a relabelling only together with a written reason.

`blind3000d` was not a uniform sample: it took the 831 forms where the published Liang patterns and 2,169 forms where the Chlebíková 1992 patterns disagreed with the engine, which explains its much higher share of differences. The operator went through all 447 in groups and accepted 391; three verbs of the `-tknúť` family received the operator's own division (`ne·pot·kla`, `ne·zat·kli`), because every verb ending in `-tknúť` is now divided after the `t`. The remaining 53 keep the engine division (for example `fi·al·kám`, `pot·kli`, `poz·dĺž·nej`, `úcti·vá`, `na·vni·voč`, `ozve·na·mi`). Accepted divisions were again applied to whole families: a prefix stays whole before a root-initial onset or vowel (`ovlá·da`, `usko·čí`, `úska·lie`, `ne·opil`, `zo·vše·obec·ní`, `pra·ide·a·mi`), the forms of `vyjsť`, `nejsť` and `začať` divide after the first consonant of the cluster (`vyj·de`, `nej·de`, `zač·ne`), the stem decides in `úcty·hod·ný`, `ost·na·tý`, `kost·na·tý`, `pre·do·šlé`, `von·kajš·ka`, `vešt·ba` and `-os·ti` words (`jas·nos·ti`), and foreign names follow their pronunciation (`Gei·ge·rov·ho`, `Shake·spea·rov`). Several of these families overturned earlier pinned decisions (`ne·jde·te`, `úc·ty·hod·ný`, `von·kaj·škom`, `pre·doš·lý`, `dis·ku·sia·mi`). Five Human confirmations in the changed families (`ovláda`, `zovšeobecní`, `úctyhodný`, `začne`, `začnú`) were rewritten through the audited path.

`blind3000e` was selected the same way from the forms not yet reviewed. Of its 268 differences the operator accepted 186 and kept the engine division for 68, mostly where an earlier decision already covered the family (`pot·kne`, `zač·ni·te`, `vyj·dú`, `naš·lo`, `úcti·vom`, `vrst·va·mi`, `an·gi·o·lóg`, `upo·doz·rie·vať`); 13 remain open and keep the engine division for now, and `ne·na·vrst·vi·lo` follows the `vrst·va` family. Accepted families: a prefix stays whole before a root-initial vowel or onset (`ne·oso·žia`, `za·ode·nej`, `ovla·že·nie`, `obo·hra·tá`, `ospr·cho·val`, `úspe·chy`, `úspeš·ní`), several stems keep their consonant cluster (`al·geb·ra`, `met·re`, `rif·le`, `ne·dôs·toj·nom`, `zne·uc·ti·lo`, `žried·lo`, `pišt·ci`), compounds keep their parts (`dez·or·ga·ni·zá·cia`, `pro·ti·otáz·ke`, `psy·cho·ana·lý·ze`, `pra·otec`) and foreign names follow their pronunciation (`Shake·spea·ra`, `Frank·fur·tu`). The `-si·a·mi` and `-zi·a·mi` plurals now follow `dis·ku·si·a·mi` (`mi·si·a·mi`, `di·men·zi·a·mi`). Sixty-seven Human confirmations in the changed families (`dôstojný`, `úspech`, `zneuctenie`, `dimenziami`, `arcipraotec` and their forms) were rewritten through the audited path.

`blind4000f` took 12 forms where the published Liang patterns and 3,988 where the Chlebíková 1992 patterns disagreed with the engine, again only from forms not yet reviewed. Of its 206 differences the operator accepted 107 and kept the engine division for 99, mostly where an earlier decision already covered the family (`vyj·de`, `zač·ne`, `pre·do·šlý`, `prázd·ny`, `vrst·va`, `an·ti·kvár`, `teo·ré·ma`, `cent·ná·rov`) and for the tens `šty·rid·sať`, `dvad·sať`, whose `-dsať` is no longer a living word. Accepted families: a root-initial vowel stays with the root after a prefix (`ne·okú·ša`, `ne·úmer·ne`, `pre·exis·ten·cia`, `uklo·nil`, `omlá·te·ný`, `uchva·ti·teľ`, `ušlia·pa·li`), stems and compound parts stay whole (`klád·lo`, `pri·vlast·ňu·je`, `roz·pro·stre·nia`, `naj·ozaj·stnej·ší`, `bo·jaz·li·vý`, `kryš·ta·lo·gra·fia`), and plain engine errors were fixed (`na·pre·du·je`, `le·gen·da`, `high·ball`). The `-čka` nouns after a vowel-final base now prefer the break before `k` (`hrač·ka`, `tan·co·vač·ky`, `za·sa·dač·ke`, `upra·to·vač·ka`) and keep `hra·čka` as a permissible point; this reverses the `blind3000c` pins `tan·co·va·čky` and `upra·to·va·čka`. Twenty Human confirmations in the changed families (`bojazlivý` and `upratovačka` with their forms) were rewritten through the audited path.

`blind4000g` took 7 forms where the published Liang patterns and 2,215 where the Chlebíková 1992 patterns disagreed with the engine, plus 1,778 forms drawn uniformly from those not yet reviewed. Of the 2,215, the models sided with the engine in 2,083; of the uniform 1,778, they agreed with it in 1,712. Of its 72 differences the operator accepted 14 and kept the engine division for 58, all of them families an earlier decision, test or Human confirmation already covered (`pos·la·nie`, `úcty·hod·ný`, `prázd·ny`, `po·msty·chti·vý`, `be·ze·ctný`, `dvad·sať`). Accepted: the engine no longer makes a vowelless syllable in `vy·lha·ný` (or `Lha·sa`), `ne·vyk·la` comes from `vyknúť` like `zvyk·la`, `uzrú` is not divided like `uzrie`, `os·lov·ský` is formed from `Os·lo`, `stereo-` stays whole before `-metria` (`ste·reo·met·ria`), and `In·ter·pret`, `Du·nois`, `fo·to·gra·fi·a·mi` and `spo·lu·vy·sla·nec` follow their related forms. The operator decided three families with a prefix or hiatus the models heard: `zá·snu·by`, `ná·klon·nosť` and `Ni·a·ga·ra`. The pins `ne·vy·kla` and `vy·l·ha·né` of the earlier audit batches were rewritten; no Human confirmation was affected.

`blind4000h` took 3 forms from the console's `?` queue, 1,408 where the Chlebíková 1992 patterns disagreed with the engine and 2,589 drawn uniformly from those not yet reviewed. Of the 1,408, the models sided with the engine in 1,333; of the uniform 2,589, they agreed with it in 2,468. Of its 58 differences the operator accepted 8 and kept the engine division for 50, again families an earlier decision, test or Human confirmation already covered (`úcty·hod·ný`, `prázd·ny`, `pos·la·nie`, `dot·kne`, `bejz·bal`, `vlast·ný`, `dvad·sať`). Accepted, each for the whole family: `zá·ste·na` and `zá·šti·ta` keep the prefix like `zá·snu·by`, `ne·ctia` follows `ne·ctnos·tí`, the one-letter prefix stays with the root in `ušľa·pa·ný` and `úžľa·bi·na`, `ka·ri·e·riz·mus` follows `ka·ri·é·ra`, `Brook·ly·ne` reads `oo` as one vowel, and the operator chose the hiatus of `en·tu·zi·az·mus`. From the queue, the operator confirmed `Mur·ray·ho`, whose `ay` is one vowel. No pin or Human confirmation was affected.

The earlier engine–Chlebíková comparison set and the older dual-model adjudications were removed on 2026-10-01: they could not be tied to a recorded rules text and prompt. They remain available in Git history.

## Reproduce and evaluate Liang patterns

Install development tools with `python -m pip install -e ".[dev]"` and put `patgen` from TeX Live or MiKTeX on `PATH`. From the repository root:

```console
python tools/liang_experiment.py --mode preferred --train-on-all --output-dir scratch/liang-preferred --patterns-output patterns/hyph-sk-slabika.tex
python tools/liang_experiment.py --mode permissive --train-on-all --output-dir scratch/liang-permissive --patterns-output patterns/hyph-sk-slabika-permissive.tex
```

These commands **replace the tracked pattern files**. Omit `--patterns-output` to leave the release artefacts untouched and write everything into the output directory instead. The generator reads the working SQLite inventory, accepts `resolved`/`inferred` casing, casefolds and deduplicates, filters unsupported spellings, and splits with salt `slabika-liang-v1`. With `--train-on-all` the split model is trained only to measure generalization (under `<output-dir>/holdout`); the written file comes from a second run over every word, so the release files contain no deliberately unseen part of the inventory. Outputs include `train.dic`, `patterns.0`, `patterns.raw`, `slovak.tra`, `patgen.log` and `report.json` with corpus counts, input/output hashes, evaluation metrics and sample mismatches.

Both files were **regenerated on 2026-10-09 from the engine that includes the operator-accepted AI review families** (runs up to `blind4000h-20261008`). The inventory contains 206,184 rows, SHA-256 `1b9d02b48234e1bda3183b3b7ad14884af4c4e2c4cc894bb95d459b13d236077`. Of 204,532 eligible source rows, filtering yields 203,879 supported unique words. The generalization model trains on **163,121 words and holds out 40,758**; the published files train on all **203,879**. The generator excludes retired `invalid` forms and includes 1,035 generated numeral forms in training; 186 corpus numerals are deliberately moved out of the test split to prevent overlap. `patgen` runs six levels: the four of the cshyphen profile (Metelka and Sojka, Hyph-bench 2025, Table 4) and two more with patterns of length 2–8 and good/bad/threshold weights 1/2/1. With only the four levels, the last, inhibiting level suppressed about 460 correct points that no later level could restore.

| generalization: split model on held-out words (2026-10-09) | exact whole words | point precision | point recall |
| --- | ---: | ---: | ---: |
| slabika preferred, 5,410 patterns | 98.7438% (40,246/40,758) | 99.5867% | 99.5957% |
| Chlebíková 1992 against preferred target | 90.4338% | 95.8537% | 96.0729% |
| slabika permissive, 5,089 patterns | 98.8150% (40,275/40,758) | 99.6159% | 99.6286% |
| Chlebíková 1992 against permissive target | 89.5775% | 96.2661% | 95.3238% |

| published files: trained on every word, measured on every word | exact whole words, patterns alone | wrong points | missed points | with the `\hyphenation` list |
| --- | ---: | ---: | ---: | ---: |
| `hyph-sk-slabika.tex`, 5,932 patterns | 99.9990% (203,877/203,879) | 2 | 0 | 100% (2 exceptions) |
| `hyph-sk-slabika-permissive.tex`, 5,515 patterns | 99.9971% (203,873/203,879) | 4 | 2 | 100% (6 exceptions) |

The first table estimates behaviour on words outside the inventory; the second only shows how closely the released files reproduce the words they were trained on. Both sides used TeX 2/3 minima. This measures **fidelity to the engine at generation time**, not independent PSP correctness or current adapter accuracy. Published SHA-256 values are:

- `patterns/hyph-sk-slabika.tex`: `9b83776eed9af3549a4e1dea89195feae3481e8024e46bd753dcf5605c556934`;
- `patterns/hyph-sk-slabika-permissive.tex`: `1f558616d0e856374fed6b53758bc8d796024f3b9b628a474860314e578b72f0`.

Generation used Python 3.11.9, MiKTeX-PATGEN 1.0 (MiKTeX 26.5), and installed `slabika-pronunciation==0.1.0` with English (US) MFA G2P v3.0.0 (model archive SHA-256 `9923b38d59a8b3e3e322f225c52523c2a6248e5ffc9fd89be151ade2dc97cb02`). Pattern output explicitly uses LF, matching Git on Windows too. Pin the input revision and runtime/model for hash comparisons; missing G2P can change the labels. The preferred/permissive reports in `patterns/` record the release run's full evaluation. The library uses DE/FR upstream inputs, **not** its own generated Slovak patterns.

A single Liang file cannot encode “prefer this boundary, use another only if necessary”. The preferred and permissive files carry those alternatives separately and should not be loaded together. Their only whole-word exceptions are the `\hyphenation` list at the end of each file: the few inventory words that its patterns alone divide differently from the engine. They do not include the language detector or G2P model. They are versioned release artefacts alongside the Python package, but the library does not load them automatically.

### Reproduce from the published source archive

The source archive is self-contained: it carries the inputs, the evidence, the pipeline and the test suite. No Git checkout and no separate corpus download are needed.

```console
pip download --no-binary :all: --no-deps slabika
tar -xf slabika-0.4.0.tar.gz
cd slabika-0.4.0
python -m pip install -e ".[dev]"
python -m pytest
python tools/liang_experiment.py --mode preferred --train-on-all --output-dir liang-preferred
python tools/liang_experiment.py --mode permissive --train-on-all --output-dir liang-permissive
```

On Windows without an editable install, use `set PYTHONPATH=src&& python -m pytest`; the generator resolves its own paths and needs no `PYTHONPATH`.

The databases the archive ships, all under `tests/data/`:

| file | size | what it is | needed for |
| --- | ---: | --- | --- |
| `translatemaster_hyphenation_working.sqlite` | 13.9 MB | the 206,205-row form inventory, SHA-256 `6625bda4…` | pattern regeneration, full-corpus tests, review console |
| `review_decisions.sqlite.xz` | 13.0 MB (56.4 MB unpacked) | every Human decision and the versioned dual-model runs | auditing the provenance claims, README statistics tests |
| `blind_*/manifest.sqlite`, `blind_*/results.sqlite` | 3.9 MB | the four frozen blind audits with their signed manifests | blind-audit checks, review console |

They compress well; the wheel stays at 3.5 MB and contains no databases at all. `python tools/audit_release_artifacts.py --inventory src/slabika/data/composita.json <archive>` enforces that split: a database anywhere outside `tests/data/` is a defect, and any database in a wheel is a defect.

**What the archive cannot supply.** Two things are external toolchain and are not redistributable here:

- `patgen` — install TeX Live or MiKTeX and put it on `PATH`. Without it the generator stops before pattern synthesis.
- the optional English G2P model — `pip install slabika-pronunciation` (about 40 MB). Without it the foreign-word labels change, so hashes will not match the published run even though the pipeline completes.

With both installed, the run reproduces end to end. Without them it still runs the engine, the corpus filtering and the evaluation, but the resulting hashes are then your own, not the release's. The report records every input hash precisely so this difference is visible rather than silent.

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

The 2026-09-15 release run recorded **1,145 passed, 1 expected failure and no unexpected failures**. Ruff and REUSE 3.3 checks also passed. The same suite was run from an unpacked source archive in a clean virtual environment: **1,138 passed, 7 skipped, 1 expected failure**, the skips being the English G2P tests that need the optional `slabika-pronunciation` runtime. REUSE compliance records the declared licences and notices; it does not resolve the still-uncertain provenance and rights clearance of the optional MFA models' training data.

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
