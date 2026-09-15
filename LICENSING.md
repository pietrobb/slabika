# Licensing, provenance and acknowledgements

slabika — Slovak syllabification and hyphenation
Copyright 2026 Peter Bezemek <peter.bezemek@gmail.com>
Project home: <https://github.com/pietrobb/slabika>

> This document is **informational**. It explains the licensing of this
> repository and records where its material comes from. It is not itself a
> licence, it adds no conditions to any licence, and nothing in it needs to be
> reproduced when you redistribute this project or anything derived from it.
>
> The binding terms are the licence texts in [`LICENSES/`](LICENSES) and the
> SPDX identifiers declared in [`REUSE.toml`](REUSE.toml) and in the per-file
> headers.

---

## 1. Licensing overview

The repository is deliberately licensed in layers, so that every part can be
reused by the widest possible set of downstream projects — including projects
whose own licence is incompatible with Apache-2.0.

| layer | SPDX expression |
| --- | --- |
| Source code, build configuration and tests | `Apache-2.0 OR MIT` |
| Language data (word lists, inventories) | `CC0-1.0 OR MIT` |
| Generated hyphenation patterns | `CC0-1.0 OR MIT` |
| Documentation and non-build repository metadata | `CC0-1.0 OR MIT` |

A Python distribution built from this repository therefore contains files under
more than one licence, and its `License-Expression` metadata is
`(Apache-2.0 OR MIT) AND (CC0-1.0 OR MIT) AND MIT`. That `AND` is a statement about the
archive, not about any single file: no file is under both a code licence and a
data licence at the same time. Each `OR` inside it is a choice you make.

The bundled DE/FR upstream patterns in `src/slabika/patterns/foreign/` are MIT-only; their original copyright and permission notices are retained verbatim, with per-file SPDX sidecars.
For project-owned files, per-file declarations and `REUSE.toml` determine the layer.
Runtime linguistic inventories, including `src/slabika/data/phonology.json`,
are data under `CC0-1.0 OR MIT`. The local build-time Python grammar modules
are offered under `Apache-2.0 OR MIT` for their implementation,
including embedded paradigm constants. This implementation licence does not
claim exclusive rights in grammatical facts or change the runtime data licence.

One consequence is deliberate: **every layer of this project is offered under
MIT**, so an organisation whose compliance policy rejects `CC0-1.0` outright —
a real policy, not a hypothetical one — does not have to argue about the data
layer. It takes MIT for everything, under a single conventional OSI licence.

The two options are not interchangeable in one respect, and it is the respect
that matters most to European reusers of the data: **`CC0-1.0` expressly
addresses the sui generis database right** (see section 2), and MIT, being a
copyright licence, says nothing about it. The MIT alternative is offered
primarily for compliance systems and policies that expect a conventional OSI
licence identifier in an inventory.

Where the MIT licence text refers to "the Software", it is to be read as
referring to whatever material it is applied to here — including word lists and
documentation. That is a reading of the text, not a condition added to it.

In SPDX syntax, `OR` exposes alternative licensing bases to downstream tooling:
**you choose**, per use, whichever of the listed licences suits you, and you do
not have to comply with both. For `Apache-2.0 OR MIT` that is the whole story.

`CC0-1.0` is different in kind, and the difference is in the reuser's favour. It
is a public-domain dedication rather than an ordinary conditional licence: once
applied, its waiver operates for the benefit of the public generally, and it is
not contingent on any particular user selecting that branch of the expression.
The data in this repository is dedicated under CC0-1.0. An inventory that
records `MIT` against these files is not wrong — MIT is genuinely offered — but
recording it does not undo, or opt out of, what CC0-1.0 has already released.

Rationale:

* **Code is `Apache-2.0 OR MIT`.** Apache-2.0 carries an explicit patent grant
  and is the licence most readily accepted by corporate legal review — but it
  is incompatible with GPL-2.0-only, and MPL-1.1 lacks the Apache-2.0
  compatibility provisions later added in MPL-2.0. Offering MIT as an
  alternative removes that barrier: a project that is genuinely GPL-2.0-only
  can take the library under MIT, a corporate integrator can take it under
  Apache-2.0 for the patent grant. This is the dual-licence convention
  established by the Rust ecosystem.

* **Data and generated patterns are `CC0-1.0 OR MIT`.** Word forms and syllable
  boundaries are facts about Slovak, and CC0 additionally addresses database
  rights (see section 2), which matters in the European Union and is what makes
  the material usable without friction in academic work, e.g. in hyphenation
  benchmark datasets. MIT is offered alongside it for automated compliance
  systems that expect a conventional OSI software licence in their inventory,
  and for organisations whose policy does not admit CC0. The patterns carry the
  same terms as the data they are generated from — a derived artefact should
  never be harder to reuse than its input.

* **Documentation is `CC0-1.0 OR MIT`** for the same reason, and so that the
  `License-Expression` of the distribution stays exact rather than
  approximate: a source distribution ships the documentation too.

There is deliberately **no Apache `NOTICE` file** in this repository. Apache-2.0
§4(d) makes the contents of a `NOTICE` file travel with every downstream
redistribution, and this project has nothing that needs to. Accordingly, no
additional NOTICE attribution text has to accompany a downstream
redistribution; only the obligations of the licence the user selects apply —
including, for code, the notice requirements of MIT or of Apache-2.0 §4. Putting
provenance essays into `NOTICE` would impose permanent attribution baggage on
users for no reason — the opposite of the intent here.

---

## 2. Database rights (EU sui generis)

The language data in this repository — word lists, syllabification inventories,
and any derived corpora — is offered under `CC0-1.0 OR MIT`. To the extent that
any copyright, related right, or sui generis database right subsists in that
material, the rightsholder applies those terms to it.

<!-- REUSE-IgnoreStart -->
**The database right is dealt with by CC0-1.0 itself; this document adds
nothing to it.** CC0-1.0 defines the "Copyright and Related Rights" it waives
so as to expressly include *database rights* — see CC0-1.0 sections 1(v) and
1(vi), and the waiver in section 2. Taking the data under the CC0-1.0 option
therefore already clears, without any further instrument and to the extent the
rights are held by the rightsholder who applied it:
<!-- REUSE-IgnoreEnd -->

* **(a)** any sui generis database right arising under Directive 96/9/EC of the
  European Parliament and of the Council of 11 March 1996 on the legal
  protection of databases, and under any national implementation thereof,
  including Slovak Act No. 185/2015 Coll. (Autorský zákon);
* **(b)** any right in the selection, arrangement, structure or presentation of
  the contents of those datasets;
* **(c)** any right to restrict extraction or re-utilisation of the whole or of
  any part of those datasets.

CC0-1.0 can only dispose of rights the person applying it holds. It does not
clear third-party rights or establish the provenance of an input. The source
history described in section 3 must be checked separately before claiming a
replacement artefact has cleared provenance; a licence label is not that check.

**This section adds no conditions to CC0-1.0 and does not modify it.** It is a
description of what CC0-1.0 does, written out because the database right is the
question EU reusers ask first — not a separate, additional or amended licence.
Where this description and CC0-1.0 could be read differently, CC0-1.0 governs.

`CC0-1.0` expressly addresses the sui generis database right; MIT itself does
not. The CC0 dedication applies to this material independently of the MIT
alternative — it is made to the public at large, not granted to whoever selects
that branch of the expression — so the MIT option, which exists for compliance
policies that do not admit CC0, does not narrow it.

### Attribution

**`CC0-1.0` itself imposes no attribution requirement.** Under that option no
permission, attribution, notification or registration is a condition of
copying, modifying, redistributing or commercially exploiting this material, in
whole or in part, in any medium, for any purpose. CC0-1.0 waives what it can
waive, to the fullest extent permitted by the applicable law, and says so in its
own terms; it does not purport to reach further.

The `MIT` option exists for compliance policies that do not admit CC0, and like
any permissive software licence it carries the usual notice obligation: the
copyright notice and the permission notice have to be retained in copies and in
substantial portions. Neither option carries an advertising or acknowledgement
requirement.

Nothing in this document purports to waive any moral or personality right that
cannot be waived under applicable law — for example the rights of an author
under §18 of Slovak Act No. 185/2015 Coll. Attribution is welcome. It is not
required under CC0-1.0.

---

## 3. Provenance of the language data

Two different things are called "word material" in this project, and they are
deliberately kept apart: what the datasets *are*, and where the *vocabulary*
they cover was drawn from.

**What the word-division datasets are.** They consist of isolated word forms and the
positions of syllable boundaries within them. They are deduplicated and sorted.
They retain no running text, no sentence order, no word order, and no n-gram,
frequency or collocation information, and therefore do not preserve the sequence
or the expressive structure of any source text. The choice, order and
combination of words is where originality can arise; an alphabetised set of
isolated forms carries none of it. The syllable boundaries are not transcribed from any
source — they are computed by this project's own phonological analysis, and the
inflected forms are produced by morphological expansion.

**Where the vocabulary was drawn from.** The question of which words a Slovak
hyphenator has to get right was answered from Slovak prose written or
translated by the copyright holder, and from literary sources in the public
domain. That work was carried out independently: it was not commissioned, not
produced in the course of employment, and is not subject to any publishing
contract, exclusive licence or other agreement that would restrict the use made
of it here. Isolated lexical items are used for coverage checks and, in the
grammar builder released in 0.3.0, as surface-form evidence for morphological induction.

Where that prose is a translation, only isolated Slovak word forms survive
deduplication and sorting. No sentence, sequence, structure or other expressive
element of an underlying work is retained in the dataset.

**German, French and English language profiles.** The JSON files in
`src/slabika/data/` are separate statistical layers. The German and French profiles
were trained from maintainer-approved prose in the local TranslateMaster corpus;
the French sources are *Histoire de ma vie* and *L’Île mystérieuse*. The English
profile was trained from 66 English-language Project Gutenberg transcriptions,
plus the seven Raymond Chandler projects in the maintainer-approved local
TranslateMaster corpus. The Gutenberg selection comprises 46 works by Jack London
and 20 works by 14 other authors whose selected works are in the public domain in
both the United States and the European Union. Editions with an unexpired or
unresolved European contributor term were deliberately excluded, including *The
Kempton-Wace Letters* and two Gordon Grant illustrated editions. The Chandler
source texts are local build inputs and are not distributed by this project. The
build script records every Gutenberg eBook identifier and a hash of every input
text. The distributed profiles contain only aggregate character n-gram log-odds;
they contain no sentences, word order, frequencies or source-word lists. The Slovak
contrast is
this project's independently assembled inventory described above. Hunspell
dictionaries are used only as external evaluation aids and contribute no weights
or lexical entries to the distributed profiles.

`foreign_readings.json` is a separate, independently written description of
spelling-to-syllabic-role facts for a limited set of foreign lexical families.
It contains no copied dictionary entries, foreign hyphenation patterns or Human
review breakpoints. The production engine maps these units to Slovak PSP rules,
including Slovak inflectional junctions. Like the other linguistic data, it is
offered under `CC0-1.0 OR MIT`; this adds no runtime dependency.

The working corpus also contains later additions labelled as PSP/OGS examples,
Wikidata vocabulary, municipality names, generated paradigms and review imports.
The annotation source labels are not a complete acquisition or permissions ledger.
For the original translation vocabulary, the source basis is the maintainer's recorded declarations (2026-08-22, reiterated 2026-09-09), reflected in this document since the initial slabika commit `06b54a2`. These are affirmative provenance declarations, not an independent legal certification. They need not be rediscovered or replaced by a title investigation for each word.

| input class | recorded source/use | remaining distinction |
| --- | --- | --- |
| Original Slovak prose and translations | Maintainer's independently assembled vocabulary; declarations above | Later annotation changes do not identify a new acquisition source |
| Generated numerals and family paradigms | Project-generated forms, identified by `generated_numeral` and named paradigm batches | Generated support is not an independent attestation |
| Wikidata-labelled professions, animals and plants | Operator-supplied lists, corrected and inflected locally on 2026-09-11 | Wikidata structured data is CC0; the label alone does not establish the full supplied-list acquisition chain |
| Municipality names | Operator-supplied `unikatne_posledne_slova_obci.txt`, 2,299 input forms; source SHA-256 `26ca5da401b3913a40875c3000b8aedbe1958d66dd253126cecf9908c7979214`; maintainer confirmed Wikidata as the source on 2026-09-14 | Wikidata structured data is CC0; exact export/query was not supplied, and is not claimed to have been independently verified |
| PSP/OGS example vocabulary | Separately labelled examples used to test implementation of the rules | No permission to redistribute book prose or table presentation is asserted |
| Review-console imports | `test.txt`, `zlozene_slova.txt`, `zakerne_slova.txt`; maintainer confirmed on 2026-09-14 that these word lists were AI-generated and manually checked by him; only their forms enter induction | Generated vocabulary, not independent attestations or normative authority; no external source list is asserted |
| Grammar supplement | Operator-requested AI-authored forms and bound-member declarations in `tests/data/grammar_supplement.json` | Authored assumptions, not Human review or independent corpus witnesses |

These classes feed the released compound inventory when present in `forms.form`; it would be inaccurate to describe that corpus as testing-only. The builder records its exact normalized input hash separately from this source-class account. Annotation counts are not acquisition counts, and source hashes establish identity, not permission. Missing documentation is not a finding of infringement.

**English membership is separate from the profiles.** `src/slabika/data/english_morphology_members.json` contains 55,637 isolated forms exported by `tools/export_english_morphology.py` from successful English rows of the local generated review inventory. Its input is the union of the same 66 Gutenberg works and seven local Chandler projects described above. The recorded `source_forms_sha256` matches that selection. The export contains no IPA, alignment, model weights or Human divisions; successful pronunciation status affects selection only. The maintainer approved Chandler-derived n-grams on 2026-09-12 while acknowledging that Chandler is not yet in the EU public domain. That approval is not itself an acquisition record for the original-language texts or an explicit rights assessment of a distributed word-membership list. On 2026-09-14 the maintainer stated that the Chandler originals had been downloaded but that the source was no longer remembered. Their acquisition source and terms therefore remain unknown; this is not a finding of infringement. On the same date, the maintainer explicitly instructed that the existing Chandler-derived character n-gram profiles and isolated-word inventory be retained for release. Version 0.3.0 retains them unchanged and does not distribute the source books. This records the maintainer's release decision, not a claim that the originals are already public domain or that all acquisition terms have been independently cleared.

The compound inventory is generated from local inflectional grammar and
surface forms in the project's corpus.
Its separate `tests/data/grammar_supplement.json` records operator-requested AI-authored surface forms and explicitly typed bound/indeclinable members; these are lexical assumptions, not human-reviewed or independent attestations. The builder hashes this input, lists added forms, and keeps compound examples separate from induced paradigm evidence.
Word forms and grammatical rules are linguistic facts (Act No. 185/2015 Coll., §5(a)),
but this does not itself clear rights in copied expression or substantial database extraction. The project
licences apply only to rights held by their grantors. Release clearance must cover
the induction inputs and any separately distributed review databases. The 0.3.0 packaging configuration excludes working SQLite databases from the wheel and ships them in the source archive, under `tests/data/` and licensed `CC0-1.0 OR MIT` with the rest of the project's word inventory and review evidence. This is deliberate redistribution, not an oversight: the reproducibility and provenance claims in the README are only checkable by a third party if the inputs and the adjudication trail travel with the pipeline. It is consistent with §3, where the vocabulary is accounted for as the project's own prose and translations, Wikidata-derived municipality names and reviewed AI-generated lists, rather than an extracted third-party lexicon. It does not relieve the need to clear the inputs of generated runtime assets.

---

## 4. Relationship to normative sources

The behaviour of this project is intended to conform to the rules of Slovak
orthography as codified in *Pravidlá slovenského pravopisu* (PSP), published by
the Ľudovít Štúr Institute of Linguistics of the Slovak Academy of Sciences
(Jazykovedný ústav Ľ. Štúra SAV), chapter *V. Rozdeľovanie slov*, and to the
descriptive phonology of Slovak in the standard reference literature.

PSP is used here as a **normative reference** — a statement of what the correct
result is. The working corpus also records a small PSP/OGS vocabulary supplement:

* Rule descriptions in this repository are independent restatements written by
  the authors. They are not translations or transcriptions of PSP text.
* Test vocabulary includes independently assembled material and individually
  consulted examples; the PSP/OGS supplement is labelled in the working corpus.

Conformance to a published standard is not a licence-relevant dependency and
imposes no restriction on users of this project. This project is not affiliated
with, nor endorsed by, JÚĽŠ SAV; conformance is a goal stated here, not a
certification granted by anyone.

---

## 5. Acknowledgements and intellectual provenance

This section is a statement of intellectual debt. It is informational and
creates no licence obligation for users of this project.

The classification of Slovak phonemes recorded in
`src/slabika/data/phonology.json` and used by `slabika.phonology` —
vowel quantity and resonance, diphthongs, syllabic consonants, consonant
hardness, voicing pairs, place and manner of articulation, palatalization, and
the rhythmic law — follows the description given by:

> Emil Páleš, *Sapfo — parafrázovač slovenčiny: počítačový nástroj na
> modelovanie v jazykovede* (1994), chapter 2 (*Fonológia*).
> 1st edition, VEDA, vydavateľstvo Slovenskej akadémie vied
> (publishing house of the Slovak Academy of Sciences), Bratislava.
> ISBN 80-224-0109-9.

In that work the classification is itself attributed to J. Dvončová (1980) and
J. Horecký (1977).

The Slovak names of the phoneme classes carried in the `terminology` block of
that file are the settled terminology of Slovak phonetics, not coinages of any
one author: the same terms are used in the standard descriptive literature, for
example in E. Pauliny, *Slovenská fonológia* (SPN, Bratislava, 1979) and in
Á. Kráľ – J. Sabol, *Fonetika a fonológia* (SPN, Bratislava, 1989).

What is taken from these sources is the descriptive analysis of the Slovak
sound system: which phonemes exist, and how they group by their articulatory
and distributional properties. That is a scientific description of a natural
language rather than creative expression. No text, table layout or wording has
been copied from any of these works; the tables and the code here are
independently written expressions of the same linguistic facts.

The layers built on top of the phoneme inventory — syllabification, the
handling of morpheme seams, the typographic line-break convention, the word
material, and the pattern generation pipeline — are original to this project.
The build-time grammar implements inflectional paradigms and alternation rules; `tools/build_composita_grammar.py` uses them to derive stems from the project's corpus forms. The cited grammatical and phonological descriptions are not hyphenation specifications; PSP governs the division rules.

The local grammar separates its inflectional tables by word class:

| module | role |
| --- | --- |
| `noun_patterns.py` | Noun inflectional paradigms |
| `adjective_patterns.py` | Adjective inflectional paradigms |
| `verb_patterns.py` | Verb inflectional paradigms |

Phonology and alternation rules support paradigm synthesis. Corpus induction requires supporting forms and a synthesis round trip; role-specific inflection licensing determines which generated forms may serve as compound members. Authored supplements are recorded separately from corpus evidence. Build metadata records the exact local source SHA-256 values and normalized input hashes.

The pattern tables cite Páleš (1994), pp. 41–47, for grammatical endings and alternation rules encoded in Python. This is not a grant to reproduce book prose, images or protected presentation, and this provenance account does not certify independent creation of every element of the book's selection/arrangement. The statement about independently expressed **phonology** is not a blanket clearance statement for morphology tables. The generator reads the local implementation and corpus forms. Implementing grammatical facts is distinct from redistributing a third-party lexicon; citation alone is not permission. Build-time modules are included in the source archive, not the wheel.

---

## 6. Third-party components

This project has no third-party code dependencies at runtime.

Optional pattern generation uses `patgen`, distributed with TeX Live and listed
on CTAN as public domain software. It is invoked as an external program: it is
not bundled, linked, or redistributed here, and its licence affects neither
this project nor its output.

---

## 7. Inbound contributions

Contributions are accepted under the same terms as the layer they touch — code
under `Apache-2.0 OR MIT`, data and documentation under `CC0-1.0 OR MIT`. See
[`CONTRIBUTING.md`](CONTRIBUTING.md). This is what keeps the dual licence of
the code intact: a contribution accepted under Apache-2.0 alone would silently
remove the MIT option for everyone downstream.
