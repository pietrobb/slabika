# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Slovak declension grammar vendored from the sibling Sapfo project.

Build-time only: the compound inventory builders decide whether a candidate
string can be a noun lemma or an adjective root, by generating the paradigm the
pattern prescribes and asking this project's own corpus which cells it attests.
No lexicon row is read here; input lineage and rights still require separate verification.

The pattern tables themselves are cited to Emil Páleš, Sapfo (1994), pp. 41-47;
they are the inflectional paradigms of Slovak, printed in every grammar of the
language. See LICENSING.md.
"""
