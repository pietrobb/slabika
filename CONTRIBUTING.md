# Contributing

Bug reports are welcome, and a badly hyphenated word is a useful bug report.
Please include the word, what the library returns, and what it should return.

One thing worth knowing before you propose a fix: **a single wrongly hyphenated
word is usually the symptom of a missing rule, not an exception.** Patches that
add a word to a lookup table will generally be turned down in favour of finding
the rule the word is telling us about. The engine carries no word list at all —
the one it used to have was measured against the adjudicated decisions and
found to contradict them — so a word that no rule reaches stays wrong until the
rule exists, and the failing expectation is recorded as an `xfail` in the tests.

## Licensing of contributions

The code in this project is dual-licensed `Apache-2.0 OR MIT` so that it can be
used both by corporate integrators who want the Apache patent grant and by
GPL-2.0-only projects, which cannot take Apache-2.0. That choice only survives
if every contribution carries it too.

By submitting a contribution for inclusion in this project, you agree to license
it under the terms applicable to the layer it modifies:

* **source code** — `Apache-2.0 OR MIT`, matching the rest of the code;
* **language data** (word lists, syllabification material,
  `src/slabika/data/**`) — `CC0-1.0 OR MIT`;
* **documentation** — `CC0-1.0 OR MIT`;

and you confirm that the material is yours to submit under those terms —
including any patent rights you would be granting under Apache-2.0 §3.
Contributions offered under different terms cannot be accepted unless agreed
explicitly before inclusion.

Please keep executable code out of the data directories. Fedora treats
`CC0-1.0` as allowed for content but not generally for code, so a single `.py`
file under `src/slabika/data/` would turn the whole data layer into a packaging
problem. Generators belong in `tools/`, their output in `src/slabika/data/`.

As a matter of provenance policy, this project does not incorporate word
material extracted from third-party dictionaries, lexical databases or word
lists, even where the licence of such a source might technically permit it.
Word material must be either your own or from a source in the public domain.

No CLA, no copyright assignment. You keep your copyright.

## Practical notes

New Python files need the SPDX header:

<!-- REUSE-IgnoreStart -->
```python
# SPDX-FileCopyrightText: 2026 <your name>
# SPDX-License-Identifier: Apache-2.0 OR MIT
```
<!-- REUSE-IgnoreEnd -->

(The markers around that block tell `reuse` the tags are an example, not this
file's own licensing. Without them the SBOM reports CONTRIBUTING.md as
Apache-2.0 code owned by `<your name>`.)

Run the tests before opening a pull request:

```
python -m pytest tests/
```

`tests/test_provenance.py` checks that the licensing and attribution statements
across the repository do not contradict each other. If it fails, an edit landed
in one file and not in its counterparts.
