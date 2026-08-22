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
`(Apache-2.0 OR MIT) AND (CC0-1.0 OR MIT)`. That `AND` is a statement about the
archive, not about any single file: no file is under both a code licence and a
data licence at the same time. Each `OR` inside it is a choice you make.

Which layer a file belongs to is decided by where it lives, and there are no
per-file exceptions to that. Tables of linguistic facts are therefore kept in
the data layer even when they are consumed only by the code: the phoneme
inventory is `src/slabika/data/phonology.json`, read at import by
`slabika.phonology`, rather than a set of literals inside that module. A file
that mixed the two would have to carry a licence that is neither, which is
exactly the kind of exception a compliance scanner has to escalate to a human.

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

CC0-1.0 can only dispose of rights the person applying it holds, and it is
applied here only to material in which the rightsholder holds them: no dataset
in this repository is taken over from a third-party database (see section 3).
The limitation is therefore formal rather than practical.

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

**What the datasets are.** They consist of isolated word forms and the
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
of it here. It is used as a check on coverage, not as data, and nothing beyond
isolated lexical items is carried over from it.

Where that prose is a translation, only isolated Slovak word forms survive
deduplication and sorting. No sentence, sequence, structure or other expressive
element of an underlying work is retained in the dataset.

No dataset in this repository is a copy, extract or re-arrangement of a
third-party lexical database, dictionary, or word list.

Individual word forms and their syllable boundaries are facts about the Slovak
language rather than creative expression; Slovak law expressly excludes ideas,
methods, principles and information from the subject matter of copyright
(Act No. 185/2015 Coll., §5(a)). Rather than rely on that analysis, the
datasets are released under the terms in section 2 above — including the
CC0-1.0 option, which also disposes of the database right — so that the
question does not have to be answered by anyone downstream.

---

## 4. Relationship to normative sources

The behaviour of this project is intended to conform to the rules of Slovak
orthography as codified in *Pravidlá slovenského pravopisu* (PSP), published by
the Ľudovít Štúr Institute of Linguistics of the Slovak Academy of Sciences
(Jazykovedný ústav Ľ. Štúra SAV), chapter *V. Rozdeľovanie slov*, and to the
descriptive phonology of Slovak in the standard reference literature.

PSP is used here as a **normative reference** — a statement of what the correct
result is. It is not used as a source of data:

* Rule descriptions in this repository are independent restatements written by
  the authors. They are not translations or transcriptions of PSP text.
* Test vocabulary exercising each rule is drawn from this project's own word
  material, not from the illustrative examples printed in PSP.

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
> modelovanie v jazykovede*, 1st edition, VEDA, vydavateľstvo Slovenskej
> akadémie vied (publishing house of the Slovak Academy of Sciences),
> Bratislava, 1994, ISBN 80-224-0109-9, chapter 2 (*Fonológia*).

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
None of the works cited above deals with hyphenation.

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
