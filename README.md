# slabika

Slovak syllabification and hyphenation — derived from a full phonological
inventory, not from a pattern table someone once guessed at.

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

Slovak has never had a hyphenation implementation worth the name. What ships in
word processors, browsers and typesetting systems today is either derived from
Czech patterns or generated from small, inconsistent word lists — and it shows
in every narrow column of Slovak text ever set.

The problem is not the Liang/`patgen` algorithm, which is excellent. The problem
is the input: pattern quality is bounded by the quality and the consistency of
the hyphenated word list it is trained on. Word lists scraped from open
dictionaries carry the inconsistencies of their sources into the patterns.

This project attacks the input instead. Syllable boundaries are computed from
the phonology of the language — vowel and diphthong nuclei, syllabic `ŕ`, `ĺ`,
`r`, `l`, consonant clusters, morpheme seams — and the word list is generated
by morphological expansion, not collected from existing hyphenated sources. A
generated list can be arbitrarily large and has, by construction, zero internal
inconsistency. Existing text is used only to decide which vocabulary has to be
covered; see [`LICENSING.md`](LICENSING.md) §3.

## Layers

The package is layered, and the order is deliberate:

| module | what it is |
| --- | --- |
| `slabika.phonology` | phoneme inventory: quantity, voicing, place, manner, palatalization |
| `slabika.syllabify` | phonotactic division into syllables — **the primary result** |
| `slabika.typo` | typographic line-break convention — *derived* from syllables |
| `slabika.phonotactics` | well-formedness, rhythmic law, preposition vocalization |

Syllabification is the product. Hyphenation is one consumer of it; text-to-speech,
prosody, verse metrics and morphology are others.

## Status

Early, and released as such on purpose. The library works, carries 167 tests,
and has been run over the whole vocabulary it is meant to serve: 197 749
distinct word forms drawn from the copyright holder's own Slovak translations
(59 works, 6.4 million tokens — the corpus itself is not shipped here). It
raised no exception on any of them, at roughly 30 µs per form, and it
reproduced every one of the 486 divisions that have been adjudicated by hand or
confirmed on review — 486 of 486.

That is the whole of the evidence. The other forms have not been checked one by
one, and two defects are known and not fixed in this release:

- the compositional first part `geo` is kept whole by design (`geo·ló·gia`) and
  fires on foreign proper names that merely begin with those letters
  (`George` → `Geo·r·ge`); that path is also the only one that does not
  lower-case its output;
- 666 forms, mostly French and English names, receive no break point although a
  legal one exists. Declining to divide foreign phonotactics is defensible, but
  the caller cannot presently tell that refusal apart from "this word has no
  legal break point at all".

The pattern-generation layer and the released word list are not in this
repository yet.

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
data. Rule descriptions here are independent restatements, and test vocabulary
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
