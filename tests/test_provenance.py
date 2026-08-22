# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""
Consistency checks for the attribution and licensing surfaces.

Attribution and licensing are stated in several places at once, because they
have different audiences: LICENSING.md is the full statement for licence
review, the READMEs are for humans, REUSE.toml and the SPDX headers are for
compliance tooling.

Duplication is intentional, but it means an edit in one place can silently
contradict another. These tests fail when that happens.
"""

import ast
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

LICENSING = (ROOT / "LICENSING.md").read_text(encoding="utf-8")
CONTRIBUTING = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
README_EN = (ROOT / "README.md").read_text(encoding="utf-8")
README_SK = (ROOT / "README.sk.md").read_text(encoding="utf-8")
PHONOLOGY = (ROOT / "src" / "slabika" / "phonology.py").read_text(encoding="utf-8")
INVENTORY_PATH = ROOT / "src" / "slabika" / "data" / "phonology.json"
INVENTORY = INVENTORY_PATH.read_text(encoding="utf-8")
REUSE = (ROOT / "REUSE.toml").read_text(encoding="utf-8")
PYPROJECT = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

ATTRIBUTION_SURFACES = {
    "LICENSING.md": LICENSING,
    "README.md": README_EN,
    "README.sk.md": README_SK,
    "phonology.py": PHONOLOGY,
    "data/phonology.json": INVENTORY,
}

def flat(text):
    """Markdown is hard-wrapped; a phrase test must not depend on where."""
    return re.sub(r"\s+", " ", text)


HOLDER = "Peter Bezemek"
EMAIL = "peter.bezemek@gmail.com"

# REUSE-IgnoreStart
#: The tag itself, kept in one place because the tests below assert on its shape
#: rather than on any particular name. A bare `Copyright` opening a heading is
#: what reuse once read as an attribution here, so a year is required after it —
#: and after `©` and `(c)` for the same reason: `(c) any right to restrict
#: extraction` is a line of §2. The year binds to all three bare forms, not only
#: to the last of them; `\b` may not follow `©` or `)`, which are not word
#: characters, or the symbol branches would match nothing at all. The explicit
#: SPDX tag needs no year, only a holder, and is the way to write a notice that
#: genuinely has none.
COPYRIGHT_TAG = "SPDX-FileCopyrightText"
NOTICE = re.compile(
    rf"^(?:{COPYRIGHT_TAG}:\s*\S"
    rf"|(?:©|\(c\)|Copyright\b)[^\n]*?\b\d{{4}}\b)",
    re.IGNORECASE,
)
# REUSE-IgnoreEnd
ISBN = "80-224-0109-9"

DECLARED_LICENCES = {"Apache-2.0", "CC0-1.0", "MIT"}
CODE_LICENCE = "Apache-2.0 OR MIT"
DATA_LICENCE = "CC0-1.0 OR MIT"
DISTRIBUTION_LICENCE = "(Apache-2.0 OR MIT) AND (CC0-1.0 OR MIT)"


# --------------------------------------------------------------------------
# The Páleš citation must be identical wherever it appears
# --------------------------------------------------------------------------


@pytest.mark.parametrize("surface", sorted(ATTRIBUTION_SURFACES))
def test_pales_is_credited_in_every_attribution_surface(surface):
    text = ATTRIBUTION_SURFACES[surface]
    assert "Páleš" in text, f"{surface} does not credit Emil Páleš"  # stem: Páleša, Pálešovi
    assert "1994" in text, f"{surface} omits the year of the cited work"
    assert ISBN in text, f"{surface} omits or contradicts the ISBN {ISBN}"


@pytest.mark.parametrize("surface", sorted(ATTRIBUTION_SURFACES))
def test_chain_of_attribution_is_complete(surface):
    """Páleš attributes the classification onwards; so must we."""
    text = ATTRIBUTION_SURFACES[surface]
    # Stem match: Slovak declines the names (Dvončová → Dvončovej, Horecký → Horeckého).
    assert "Dvončov" in text, f"{surface} omits J. Dvončová, Páleš's own source"
    assert "Horeck" in text, f"{surface} omits J. Horecký, Páleš's own source"


def test_the_slovak_class_names_are_not_traced_to_a_single_book():
    """
    The inventory is a classification, and a classification is not expression —
    except that the `terminology` block is the one place where actual Slovak
    wording sits next to a cited work. The terms are standard (Pauliny,
    Kráľ–Sabol use the same ones), so naming a second, independent source ends
    the 'transcribed from one book' reading at the only point it could start.
    """
    for surface in ("LICENSING.md", "data/phonology.json"):
        text = ATTRIBUTION_SURFACES[surface]
        assert "Pauliny" in text and "Sabol" in text, (
            f"{surface} traces the Slovak class names to Páleš alone; they are the "
            f"settled terminology of the field and appear in independent sources."
        )


def test_only_one_isbn_is_ever_mentioned():
    """A second ISBN anywhere means a citation was edited in one place only."""
    for surface, text in ATTRIBUTION_SURFACES.items():
        found = set(re.findall(r"\b\d{2}-\d{3}-\d{4}-\d\b", text))
        assert found <= {ISBN}, f"{surface} mentions unexpected ISBN(s): {found - {ISBN}}"


def test_readme_does_not_claim_the_phonology_as_original_work():
    """
    The README once said the phonological inventory was the author's own work,
    which contradicted LICENSING.md §5 after Páleš was credited. Guard against a
    regression: any sentence claiming original work must not cover phonology.
    """
    for surface in ("README.md", "README.sk.md"):
        text = ATTRIBUTION_SURFACES[surface]
        for match in re.finditer(r"[^.]*\bhis (own|original) work\b[^.]*", text):
            sentence = match.group(0)
            assert not re.search(
                r"phonolog|phoneme|fonológi|foném",
                sentence,
                re.IGNORECASE,
            ), f"{surface} claims the phoneme inventory as the author's own work: {sentence!r}"


# --------------------------------------------------------------------------
# Holder and contact
#
# The heading deliberately avoids the word that opens a copyright notice: reuse
# scans headings too, and this file would then be attributed to whatever text
# followed it. The test below enforces that for the whole repository.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, text",
    [
        ("LICENSING.md", LICENSING),
        ("README.md", README_EN),
        ("README.sk.md", README_SK),
        ("REUSE.toml", REUSE),
        ("pyproject.toml", PYPROJECT),
        ("LICENSE", (ROOT / "LICENSE").read_text(encoding="utf-8")),
    ],
)
def test_copyright_holder_is_named_consistently(name, text):
    assert HOLDER in text, f"{name} does not name the copyright holder"


@pytest.mark.parametrize(
    "name, text",
    [
        ("LICENSING.md", LICENSING),
        ("README.md", README_EN),
        ("README.sk.md", README_SK),
        ("REUSE.toml", REUSE),
        ("pyproject.toml", PYPROJECT),
    ],
)
def test_contact_address_is_consistent(name, text):
    found = set(re.findall(r"[\w.+-]+@[\w.-]+\.\w+", text))
    assert EMAIL in found, f"{name} does not give the maintainer's address"
    assert found == {EMAIL}, f"{name} gives conflicting addresses: {found - {EMAIL}}"


# --------------------------------------------------------------------------
# Licence layers
# --------------------------------------------------------------------------


def test_every_declared_licence_has_its_full_text():
    """REUSE requires the text of every SPDX identifier actually used."""
    for licence in DECLARED_LICENCES:
        path = ROOT / "LICENSES" / f"{licence}.txt"
        assert path.is_file(), f"REUSE.toml declares {licence} but LICENSES/{licence}.txt is missing"
        assert path.read_text(encoding="utf-8").strip(), f"LICENSES/{licence}.txt is empty"


def test_reuse_annotations_yield_to_per_file_headers():
    """
    'aggregate' would add the maintainer's copyright to every future
    contributor's file on top of their own header. 'closest' makes REUSE.toml a
    fallback for files without a header, which is what CONTRIBUTING promises
    when it says contributors keep their copyright.
    """
    assert 'precedence = "aggregate"' not in REUSE, (
        "REUSE.toml uses precedence 'aggregate': it would attach "
        f"'{HOLDER}' to files written by someone else."
    )
    assert 'precedence = "closest"' in REUSE


def test_licence_texts_are_verbatim_and_carry_no_holder_name():
    """
    REUSE requires the texts in LICENSES/ to be the unmodified originals. Baking
    a name into LICENSES/MIT.txt makes the central text wrong the moment someone
    else contributes; the holder belongs in SPDX-FileCopyrightText, per file.
    """
    for licence in DECLARED_LICENCES:
        text = (ROOT / "LICENSES" / f"{licence}.txt").read_text(encoding="utf-8")
        assert HOLDER not in text, (
            f"LICENSES/{licence}.txt names '{HOLDER}'. Restore the verbatim text "
            f"(`reuse download {licence}`) and leave copyright to the SPDX headers."
        )


def test_root_licence_pointer_exists_and_only_points():
    """
    Without a root LICENSE, GitHub and most scanners report 'no license' — the
    single biggest practical brake on adoption. It must stay a pointer, though:
    a second copy of a licence text is a second thing to keep in sync.
    """
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "LICENSES/" in text, "the root LICENSE does not point at LICENSES/"
    for licence in DECLARED_LICENCES:
        assert licence in text, f"the root LICENSE does not mention the {licence} layer"
    assert "Permission is hereby granted" not in text, "the root LICENSE duplicates the MIT text"
    assert "Apache License" not in text, "the root LICENSE duplicates the Apache text"


def test_distribution_metadata_covers_every_licence_in_the_archive():
    """
    PEP 639 reads `license` as the licensing of the whole distribution archive.
    Declaring only the code licence understates a wheel that also ships CC0
    data, and an SBOM scanner comparing declaration to content flags it.
    """
    assert f'license = "{DISTRIBUTION_LICENCE}"' in PYPROJECT, (
        f"pyproject.toml must declare '{DISTRIBUTION_LICENCE}': the archive mixes "
        f"'{CODE_LICENCE}' code with '{DATA_LICENCE}' data and documentation."
    )
    assert "hatchling>=1.27" in PYPROJECT, (
        "PEP 639 `license`/`license-files` needs hatchling>=1.27; an older backend "
        "silently produces wrong metadata."
    )


def test_every_layer_is_reachable_under_one_common_licence():
    """
    Corporate policy engines block the CC0-1.0 token outright, and Fedora will
    not take CC0 for code. If any layer were CC0-only, such a user would have to
    fork the project instead of consuming it. MIT must therefore be one of the
    options in every expression the project declares — that is what makes the
    whole archive satisfiable under a single conventional OSI licence.
    """
    for expression in set(re.findall(r'SPDX-License-Identifier = "([^"]+)"', REUSE)):
        assert "MIT" in expression.split(" OR "), (
            f"REUSE.toml declares '{expression}', which cannot be satisfied under MIT. "
            f"Every layer must stay reachable without accepting CC0-1.0."
        )


def test_non_code_layers_are_licensed_identically():
    """
    Data, patterns and documentation are one licensing story, not three. Letting
    them drift apart is what forced the unreadable
    '(Apache-2.0 OR MIT) AND CC0-1.0 AND (MIT OR CC0-1.0)' shape on the
    distribution metadata.
    """
    blocks = REUSE.split("[[annotations]]")[1:]
    non_code = [b for b in blocks if f'"{CODE_LICENCE}"' not in b]
    assert len(non_code) == 3, "expected data, patterns and documentation blocks"
    for block in non_code:
        assert f'SPDX-License-Identifier = "{DATA_LICENCE}"' in block, (
            f"a non-code layer departs from '{DATA_LICENCE}':\n{block.strip()}"
        )


def test_no_annotation_block_discards_a_contributors_copyright():
    """
    'override' ignores *all* closer licensing information, copyright included —
    so a contributor's own SPDX-FileCopyrightText inside a data file would be
    reported as the maintainer's. CONTRIBUTING promises the opposite ('You keep
    your copyright'), and REUSE applies precedence to copyright and to licence
    separately, so 'closest' keeps their line while the licence still falls back
    to REUSE.toml. A stray *licence* header is caught by the test below instead.
    """
    assert 'precedence = "override"' not in REUSE, (
        "an annotation block uses 'override', which drops per-file copyright lines"
    )


# REUSE-IgnoreStart
def test_no_file_under_a_data_path_declares_its_own_licence():
    """
    The guard 'override' used to provide, without its cost: a data file must not
    relicense the layer from inside itself. Enforced here, where the failure
    names the file instead of silently resolving to something else.
    """
    tag = "SPDX-License-Identifier:"
    for parent in (ROOT / "data", ROOT / "src" / "slabika" / "data",
                   ROOT / "patterns", ROOT / "src" / "slabika" / "patterns"):
        if not parent.is_dir():
            continue
        for path in parent.rglob("*"):
            if not path.is_file():
                continue
            head = path.read_bytes()[:4096].decode("utf-8", "replace")
            if tag not in head:
                continue
            declared = head.split(tag, 1)[1].splitlines()[0].strip().rstrip("*/-# ")
            assert declared == DATA_LICENCE, (
                f"{path.relative_to(ROOT)} declares '{declared}'. Files under a data or "
                f"pattern path take '{DATA_LICENCE}' from REUSE.toml; a header here "
                f"relicenses the layer from inside it."
            )
# REUSE-IgnoreEnd


def test_informational_documents_are_not_shipped_as_licence_terms():
    """
    Anything in license-files lands in .dist-info/licenses/ and is read as terms.
    LICENSING.md says of itself that nothing in it needs to be reproduced — so
    shipping it there would recreate the NOTICE baggage it exists to avoid.
    """
    declared = re.search(r"license-files = \[([^\]]*)\]", PYPROJECT).group(1)
    assert "LICENSING.md" not in declared, "LICENSING.md is informational, not licence terms"
    assert "LICENSES/*" in declared
    assert '"LICENSE"' in declared, (
        "the root LICENSE belongs in license-files: it is the map of which layer is "
        "under which licence, and .dist-info/licenses/ is where a scanner looks for it."
    )


def test_data_and_pattern_layers_are_annotated_where_they_actually_live():
    """
    The packaged tree is src/slabika/**. A glob that only covers a top-level
    data/ leaves the shipped data matched by the src/** block instead — silently
    relicensing CC0 data as code.
    """
    packaged = re.search(r'packages = \["([^"]+)"\]', PYPROJECT).group(1).replace("\\", "/")
    for layer in ("data", "patterns"):
        assert f'"{packaged}/{layer}/**"' in REUSE, (
            f"REUSE.toml does not annotate {packaged}/{layer}/**, so anything shipped "
            f"there falls through to the {CODE_LICENCE} source-code block."
        )


def test_no_code_lives_under_a_cc0_data_directory():
    """
    Fedora reclassified CC0-1.0 as content-only, not acceptable for code. One
    .py file under a CC0 path turns the data layer into a packaging problem.
    """
    for parent in (ROOT / "data", ROOT / "src" / "slabika" / "data"):
        if parent.is_dir():
            offenders = [p.name for p in parent.rglob("*.py")]
            assert not offenders, f"executable code under a CC0-1.0 path: {offenders}"


def test_the_phoneme_inventory_is_data_and_not_literals_in_the_code():
    """
    phonology.py used to carry the inventory as literals and, to stay honest
    about that, an SPDX header of its own: 'Apache-2.0 OR MIT OR CC0-1.0'. It
    was the only file in the archive with a third option, nothing documented it,
    and it put CC0 on code — the combination Fedora refuses and the one that
    makes the Apache patent grant beside the point. The layer boundary belongs
    between files, so the facts live in the data layer and the module reads them.
    """
    assert INVENTORY_PATH.is_file(), "the phoneme inventory is not in the data layer"
    inventory = json.loads(INVENTORY)

    phonemes = set()
    def collect(node):
        if isinstance(node, list):
            phonemes.update(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key == "terminology":
                    continue
                if isinstance(value, str) and len(value) <= 2:
                    phonemes.update((key, value))
                else:
                    collect(value)
    collect(inventory)

    quoted = {node.value for node in ast.walk(ast.parse(PHONOLOGY))
              if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    leaked = sorted(quoted & phonemes)
    assert not leaked, (
        f"phonology.py spells out the phonemes {leaked}. A fact written into the code is a "
        f"fact under the code licence; read it from data/phonology.json instead."
    )


# REUSE-IgnoreStart
def test_no_document_quotes_an_spdx_tag_outside_an_ignore_block():
    """
    The cheap half of the SBOM test above, so a checkout without `reuse` still
    catches it. An SPDX tag shown as an example is a real declaration to any
    scanner unless it sits between the ignore markers.
    """
    tag = "SPDX-License-Identifier:"
    for path in sorted(ROOT.rglob("*.md")):
        # rglob, not glob: the documents are in the root today, but a docs/
        # directory would reopen the hole silently. Skip what is not ours.
        if any(part.startswith(".") or part in ("scratch", "build", "dist")
               for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8")
        outside = re.sub(r"REUSE-IgnoreStart.*?REUSE-IgnoreEnd", "", text, flags=re.S)
        assert tag not in outside, (
            f"{path.name} shows an SPDX tag outside REUSE-IgnoreStart/End; the SBOM will "
            f"report the document itself under that licence."
        )
# REUSE-IgnoreEnd


def test_no_unexpected_licence_is_introduced():
    """A new SPDX identifier in REUSE.toml must be a conscious decision."""
    used = set(re.findall(r'SPDX-License-Identifier = "([^"]+)"', REUSE))
    ids = {token for entry in used for token in entry.replace(" OR ", " ").split()}
    assert ids == DECLARED_LICENCES, f"unexpected licence(s) in REUSE.toml: {ids ^ DECLARED_LICENCES}"


def test_three_layer_split_is_stated_in_both_readmes():
    for surface in ("README.md", "README.sk.md"):
        text = ATTRIBUTION_SURFACES[surface]
        for licence in DECLARED_LICENCES:
            assert licence in text, f"{surface} does not state the {licence} layer"


def test_attribution_is_never_presented_as_a_condition_of_use():
    """The central promise of the data licensing. Every surface carries it."""
    assert "imposes no attribution requirement" in flat(LICENSING)
    assert "Attribution is welcome. It is not required under CC0-1.0." in flat(LICENSING)
    assert "imposes no attribution requirement" in flat(README_EN)
    assert "neukladajú povinnosť uvádzať autora" in flat(README_SK)


def test_the_attribution_statement_is_about_the_licence_not_about_the_world():
    """
    'No attribution requirement of any kind' and 'úplne bez uvedenia autora' are
    claims about the legal position; CC0-1.0 waives only to the fullest extent
    the applicable law allows, and §18 of Act 185/2015 makes moral rights
    non-waivable. Every surface already said so a paragraph later, which made
    the opening sentence the broader of the two. The statement that survives
    both is the one about the instrument: CC0-1.0 imposes no such requirement.
    """
    overreaching = {
        "LICENSING.md": ("no attribution requirement of any kind",),
        "README.md": (
            "no attribution at all",
            "no attribution whatsoever",
            # A statement about what a redistributor may do, not about what the
            # instrument requires — and the documentation is authored prose, so
            # §18 bites exactly where this sentence promised it would not.
            "without naming anyone",
        ),
        "README.sk.md": ("úplne bez uvedenia autora", "aby ste niekoho menovali"),
    }
    for surface, phrases in overreaching.items():
        text = flat(ATTRIBUTION_SURFACES[surface])
        for phrase in phrases:
            assert phrase not in text, (
                f"{surface} states the absence of attribution as an absolute fact "
                f"('{phrase}'). Say what CC0-1.0 imposes; it waives only to the "
                f"extent the applicable law permits."
            )


def test_attribution_promise_does_not_overreach_into_non_waivable_rights():
    """
    An absolute 'no attribution ever' claim is wrong under Slovak law: §18 of
    Act 185/2015 makes moral rights non-waivable. Both the English and the
    Slovak statement must acknowledge that, or the promise is legally sloppy.
    """
    assert "cannot be waived under applicable law" in flat(LICENSING), (
        "LICENSING.md does not reserve rights that cannot be waived"
    )
    assert "185/2015" in LICENSING
    assert "vzdať nemožno" in README_SK, "the Slovak README overstates the attribution waiver"


def test_the_reservation_sits_in_the_same_paragraph_as_the_claim():
    """
    Both README statements were once true only when read to the end: the opening
    sentence said attribution is never needed, and the reservation followed two
    lines later. A reader who quotes the bold sentence quotes the overreach. The
    reservation has to be in the paragraph a quoter would take.
    """
    for surface, claim, reservation in (
        ("README.md", "imposes no attribution requirement", "cannot be waived under applicable law"),
        ("README.sk.md", "neukladajú povinnosť uvádzať autora", "vzdať nemožno"),
    ):
        paragraphs = [flat(p) for p in ATTRIBUTION_SURFACES[surface].split("\n\n")]
        holding = [p for p in paragraphs if claim in p]
        assert holding, f"{surface} no longer states the attribution claim"
        for paragraph in holding:
            assert reservation in paragraph, (
                f"{surface} states '{claim}' in a paragraph that does not reserve the "
                f"rights it cannot waive. Quoted alone, that paragraph overreaches."
            )


def test_slovak_copyright_act_is_cited_by_the_right_section():
    """
    The exclusion of ideas, methods, principles and information from copyright
    is §5(a) of Act 185/2015, not §3(6). A wrong pin-cite is the first thing a
    reviewer checks and the cheapest thing to get wrong.
    """
    assert "185/2015 Coll., §5(a)" in flat(LICENSING)
    assert "§3(6)" not in LICENSING


def test_no_attribution_claim_does_not_swallow_redistribution_notices():
    """
    MIT and Apache-2.0 both require notices to be preserved on redistribution.
    'No attribution required' is true of *use* and of the CC0 layers; stated
    without that boundary it reads as a promise the licences do not make.
    """
    assert "MIT or Apache-2.0" in flat(README_EN), (
        "README.md states no attribution without bounding it to the licence's own notices"
    )
    assert "MIT alebo Apache-2.0" in flat(README_SK), (
        "README.sk.md states no attribution without bounding it to the licence's own notices"
    )
    assert "only the obligations of the licence the user selects apply" in flat(LICENSING)


def test_the_no_attribution_promise_names_the_option_it_belongs_to():
    """
    'The licensing terms impose no attribution requirement' was true while the
    data was CC0-only. Adding the MIT option made it false for half of them —
    MIT requires the notices to be retained. The promise must name CC0.
    """
    section = flat(LICENSING.split("### Attribution")[1].split("---")[0])
    head = section[: section.index("no attribution requirement")]
    assert "CC0-1.0" in head, (
        "the attribution promise is stated unconditionally; under the MIT option "
        "the notices still have to be retained"
    )
    assert "retained in copies" in section, "the MIT notice obligation is not stated"


def test_the_readme_headline_promises_a_possibility_not_a_property():
    """
    'The data and the patterns require no attribution at all' is what gets
    scanned and quoted; the qualifier after the dash is not. Stated as a
    property of the material it is false for the MIT option, which does require
    the notices. Stated as something the reuser can do — 'can be used with no
    attribution at all', by taking CC0 — it is true of both options at once.
    """
    for name, text, claim in (("README.md", README_EN, "require no attribution"),
                              ("README.sk.md", README_SK, "nevyžadujú uvedenie autora")):
        assert claim not in flat(text), (
            f"{name} states the absence of attribution as a property of the licensing. "
            f"Under the MIT option the notices are still required; phrase it as what "
            f"the CC0-1.0 option lets the reuser do."
        )


def test_cc0_is_described_as_a_dedication_not_as_a_licence_to_be_picked():
    """
    CC0-1.0 is a public-domain dedication: once applied it operates for the
    public generally, and its waiver of database rights is not contingent on a
    given user selecting the CC0 branch of 'CC0-1.0 OR MIT'. Documents that say
    'choose CC0-1.0 if your question is the database right' imply the opposite —
    that an inventory recording MIT forfeits the waiver. It does not.
    """
    text = flat(LICENSING)
    assert "public-domain dedication rather than an ordinary conditional licence" in text
    assert "not contingent on any particular user selecting" in text
    assert "applies to this material independently of the MIT" in text, (
        "§2 does not say the CC0 dedication stands independently of the MIT option"
    )
    for implication in ("choose CC0-1.0 if", "should take the CC0-1.0 option"):
        assert implication not in text, (
            f"LICENSING.md reads the CC0 dedication as an offer that takes effect on "
            f"selection ('{implication}')"
        )
    assert "vzdanie sa práv voči verejnosti" in flat(README_SK), (
        "the Slovak README presents CC0 as an ordinary licence the user picks"
    )


def test_the_mit_fallback_is_not_claimed_to_cover_database_rights():
    """
    'Every layer is under MIT, so the whole project can be taken under MIT
    alone' overreaches: MIT is a copyright licence and is silent on the sui
    generis database right, which is exactly what §2 offers CC0-1.0 for. Every
    surface that makes the MIT-for-everything point must carry the boundary.
    """
    for name, text in (("LICENSE", (ROOT / "LICENSE").read_text(encoding="utf-8")),
                       ("LICENSING.md", LICENSING),
                       ("README.md", README_EN)):
        assert "under MIT alone" not in flat(text), f"{name} claims MIT alone covers everything"
        assert "database right" in flat(text), (
            f"{name} offers MIT for every layer without saying what MIT does not reach"
        )
    assert "právo k databáze, ktoré MIT nerieši" in flat(README_SK), (
        "README.sk.md presents the MIT fallback without the database-right boundary"
    )


def test_the_extra_database_waiver_is_not_a_modified_licence():
    """The §2 waiver must read as a restatement of CC0, never as new terms."""
    assert "adds no conditions to CC0-1.0 and does not modify it" in LICENSING


def test_the_database_waiver_claims_only_rights_the_applier_holds():
    """
    CC0 disposes of the applier's own rights; Creative Commons says to apply it
    only to those, or where one has authority to act for their owner. Listing
    'any right in the selection, arrangement ...' without that bound reads as if
    the dedication cleared a third party's database right too. Nothing here is
    taken from a third-party database, so the bound costs nothing and the
    unbounded sentence would be the only overreach left in §2.
    """
    section = flat(LICENSING.split("## 2.")[1].split("## 3.")[0])
    lead = section[: section.index("* **(a)**")]
    assert "to the extent the rights are held by the rightsholder" in lead, (
        "§2 presents the CC0 dedication as clearing database rights outright; "
        "it can only clear the rights of whoever applied it."
    )
    assert "no dataset in this repository is taken over from a third-party database" in section


def test_the_root_licence_map_does_not_imply_mit_forfeits_the_waiver():
    """
    The root LICENSE is the short version, and the only one a reader may see on
    its own. Saying MIT 'does not' address database rights and stopping there
    invites the reading that selecting MIT gives the CC0 waiver up. LICENSING.md
    and both READMEs already carry the correction; this file is where its
    absence would do the damage.
    """
    text = flat((ROOT / "LICENSE").read_text(encoding="utf-8"))
    assert "Selecting MIT does not forfeit that" in text
    assert "operates for the public generally" in text


def test_an_informational_document_does_not_purport_to_grant_or_waive():
    """
    LICENSING.md opens by saying it is not a licence. A sentence of the form
    'the rightsholder expressly and irrevocably waives ...' contradicts that in
    the same document: either it operates, or the opening is wrong. CC0-1.0
    already covers database rights by its own terms, so the description is
    enough and the custom instrument is not needed.
    """
    assert "It is not itself a" in flat(LICENSING)
    for verb in ("hereby waives", "expressly and irrevocably waives", "hereby grants"):
        assert verb not in flat(LICENSING), (
            f"LICENSING.md performs a licensing act ('{verb}') while declaring itself "
            f"informational. State what CC0-1.0 does instead of re-doing it."
        )


def test_licence_rationale_makes_no_falsifiable_claim_about_a_named_project():
    """
    The README used to argue from `libhyphen` being 'tri-licensed
    MPL-1.1 / GPL-2.0 / LGPL-2.1'. Both GPL and LGPL there are 'or later', so a
    GPL-3.0 build can take Apache-2.0 after all — and hyphenation patterns are
    read as data anyway, never linked. One falsifiable sentence discredits the
    document around it; the general incompatibility claim needs no example.
    """
    for surface in ("README.md", "README.sk.md", "LICENSING.md"):
        text = ATTRIBUTION_SURFACES[surface]
        assert "libhyphen" not in text.lower(), (
            f"{surface} argues from a named downstream project's licence. "
            f"Version-pinned claims about third-party licensing rot silently."
        )
        assert "GPL-2.0 build" not in text


def test_both_readmes_tell_the_same_compatibility_story():
    """
    The Slovak README once carried a vague claim ('a large part of the
    ecosystem is GPL-2.0-only') *and* a contradicting concrete paragraph after
    it. Whatever incompatibility is named must be named in both.
    """
    for surface in ("README.md", "README.sk.md"):
        text = ATTRIBUTION_SURFACES[surface]
        assert "GPL-2.0-only" in text and "MPL-1.1" in text, (
            f"{surface} states a different set of incompatibilities than its counterpart"
        )


def test_contributing_points_at_one_data_directory():
    """
    'Generators belong in tools/, their output in data/' contradicted every
    other path in the same file. The packaged tree is the only correct answer.
    """
    packaged = re.search(r'packages = \["([^"]+)"\]', PYPROJECT).group(1).replace("\\", "/")
    assert f"{packaged}/data/" in CONTRIBUTING
    assert "output in `data/`" not in CONTRIBUTING, (
        f"CONTRIBUTING.md sends generator output to a top-level data/, "
        f"but the annotated and packaged path is {packaged}/data/"
    )


def test_fedora_claim_stays_within_what_can_be_checked():
    """
    'Fedora and other distributions no longer accept CC0' is broader than the
    evidence: the checkable fact is Fedora's own allowed-content classification.
    """
    assert "Fedora and other" not in CONTRIBUTING, (
        "CONTRIBUTING.md generalises a Fedora-specific policy to unnamed distributions"
    )
    assert "allowed for content but not generally for code" in flat(CONTRIBUTING)


def test_readme_sends_the_provenance_question_to_the_document_that_answers_it():
    """
    The README says the word list is generated rather than collected. That is
    the claim a licence reviewer will want substantiated, so it must not stand
    alone — §3 is where the substantiation lives.
    """
    assert "not collected from existing" in flat(README_EN)
    assert "LICENSING.md) §3" in flat(README_EN), "README.md states the claim without the cross-reference"


def test_the_provenance_argument_claims_nothing_about_who_owns_lexis():
    """
    §3 used to argue that the choice of Slovak lexis in a translation is the
    translator's contribution rather than the original author's. That allocates
    authorship between two people — a legal theory the project would then have
    to defend, and does not need: what carries the section is that only isolated
    word forms survive deduplication and sorting. State the operation performed,
    not a conclusion about who owns what.
    """
    section = flat(LICENSING.split("## 3.")[1].split("## 4.")[0])
    assert "not the original author's" not in section, (
        "§3 allocates the lexis of a translation between translator and original "
        "author. Describe what deduplication and sorting leave behind instead."
    )
    assert "only isolated Slovak word forms survive" in section
    assert "No sentence, sequence, structure or other expressive element" in section


def test_the_datasets_are_described_by_what_they_drop_not_by_impossibility():
    """
    '§3 no source text can be reconstructed from them, in whole or in part' is an
    impossibility claim, and the paragraph disclaims it two sentences later by
    admitting that isolated lexical items do survive. What the section can carry
    is the operation performed: sequence and structure are gone. Infopaq (C-5/08)
    puts originality in the choice, order and combination of words — describing
    the loss of order is the argument, and it does not have to be proved absolute.
    """
    section = flat(LICENSING.split("## 3.")[1].split("## 4.")[0])
    assert "reconstructed" not in section, (
        "§3 claims a source text cannot be reconstructed. State what the datasets "
        "no longer retain; do not undertake to prove an impossibility."
    )
    assert "do not preserve the sequence or the expressive structure" in section
    assert "choice, order and combination of words" in section


def test_no_absolute_claim_about_copyright_in_facts():
    """
    'Facts are not subject to copyright in any jurisdiction' is a legal theory
    the project would have to defend. CC0 exists so it does not have to.
    """
    assert "in any jurisdiction" not in LICENSING
    assert "To the extent that any copyright" in flat(LICENSING)


def test_no_apache_notice_file_exists():
    """
    Apache-2.0 §4(d) makes NOTICE contents travel with every redistribution.
    Nothing in this project needs to, so the file must not come back.
    """
    for name in ("NOTICE", "NOTICE.txt", "NOTICE.md", "NOTICE.TXT"):
        assert not (ROOT / name).exists(), (
            f"{name} reintroduces perpetual downstream attribution obligations"
        )


# --------------------------------------------------------------------------
# Per-file SPDX headers
# --------------------------------------------------------------------------


def _python_sources():
    return sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "tests").rglob("*.py"))


# REUSE-IgnoreStart
# The SPDX tags below are the strings being asserted on, not declarations about
# this file. Without these markers `reuse lint` parses them as real headers.
@pytest.mark.parametrize("path", _python_sources(), ids=lambda p: p.name)
def test_python_files_carry_matching_spdx_headers(path):
    head = path.read_text(encoding="utf-8")[:400]
    # A holder, not this holder. CONTRIBUTING promises contributors keep their
    # copyright, and pinning the maintainer's name here would fail the first
    # file an outside contributor writes — the thing 'closest' precedence and
    # the SBOM test are there to protect.
    assert re.search(rf"{COPYRIGHT_TAG}:\s*\S", head), (
        f"{path.name} lacks a copyright header"
    )
    declared = re.search(r"SPDX-License-Identifier:\s*(.+)", head)
    assert declared, f"{path.name} lacks an SPDX licence header"
    # Equality, not containment: 'Apache-2.0 OR MIT OR CC0-1.0' contains the code
    # licence as a substring and would have passed while adding a third option.
    assert declared.group(1).strip() == CODE_LICENCE, (
        f"{path.name} declares '{declared.group(1).strip()}', not '{CODE_LICENCE}'. Dropping "
        f"either half breaks a downstream group: Apache-2.0 alone locks out GPL-2.0-only "
        f"projects, MIT alone drops the patent grant. Adding a third option is worse — CC0 on "
        f"code is what Fedora refuses, and it makes the Apache patent grant beside the point."
    )


def test_code_dual_licence_is_stated_everywhere_it_is_promised():
    """The Apache-2.0 OR MIT choice must be visible to tooling and to humans."""
    assert f'SPDX-License-Identifier = "{CODE_LICENCE}"' in REUSE
    assert CODE_LICENCE in PYPROJECT
    assert CODE_LICENCE in LICENSING
    assert CODE_LICENCE in README_EN
    assert CODE_LICENCE in README_SK


    for name in ("LICENSE-APACHE", "LICENSE-MIT"):
        assert not (ROOT / name).exists(), (
            f"{name} is back in the repository root. REUSE 3.3 expects licence texts only "
            f"under LICENSES/<SPDX-id>.txt; a second copy is a place for the two to drift apart."
        )


# REUSE-IgnoreEnd


def test_inbound_contributions_carry_the_same_dual_licence():
    """
    A contribution accepted under Apache-2.0 alone would silently remove the
    MIT option for everyone downstream. CONTRIBUTING.md must say so.
    """
    assert CODE_LICENCE in CONTRIBUTING, "CONTRIBUTING.md does not state inbound code licensing"
    assert "CC0-1.0" in CONTRIBUTING, "CONTRIBUTING.md does not state inbound data licensing"


# --------------------------------------------------------------------------
# Cross-links between the two READMEs
# --------------------------------------------------------------------------


def _in_git_worktree():
    """
    reuse excludes build and cache artefacts by consulting .gitignore, which it
    can only do inside a checkout. Unpacked from an sdist or a zip, it scans
    .pytest_cache/ — created by the very run invoking it — and reports files
    without licensing information. Without git on PATH it cannot consult
    .gitignore either, even inside a checkout.
    """
    try:
        probe = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                               cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return False
    return probe.returncode == 0


def _reuse_or_skip():
    reuse = shutil.which("reuse")
    if reuse is None:
        pytest.skip("reuse is not installed (pip install -e .[dev])")
    if not _in_git_worktree():
        pytest.skip("outside a git worktree reuse cannot honour .gitignore")
    return reuse


def test_repository_passes_reuse_lint():
    """
    Everything else here checks what the documents say. This checks that the
    machine-readable side actually holds: every file covered, every declared
    licence present, every SPDX expression parseable.
    """
    result = subprocess.run([_reuse_or_skip(), "lint"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


# REUSE-IgnoreStart
def test_reuse_resolves_every_file_to_the_licence_of_its_layer():
    """
    `reuse lint` only asks whether every file has *some* licensing information.
    It passes just as happily when the information is wrong — an SPDX tag quoted
    inside a documentation example is syntactically a declaration, so
    CONTRIBUTING.md was reported as Apache-2.0 code belonging to '<your name>'.
    The same hazard turns any heading beginning with the word that opens a
    copyright notice into an attribution. Only the resolved SBOM shows it, so
    that is what this test reads.
    """
    result = subprocess.run([_reuse_or_skip(), "spdx"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    # The rule, not a table of extensions: a file is code if it is source or
    # build configuration *and* does not live in a data or pattern directory.
    # Classifying by suffix alone made src/slabika/data/foo.toml code, and made
    # a pattern file in a format not yet listed fail as unclassifiable. A browser
    # interface is source too, so its markup and scripts count as code.
    def expected_licences(name):
        under_data = any(part in ("data", "patterns") for part in Path(name).parts[:-1])
        is_code = Path(name).suffix in (".py", ".toml", ".html", ".css", ".js") and not under_data
        return frozenset((CODE_LICENCE if is_code else DATA_LICENCE).split(" OR "))

    for block in result.stdout.split("FileName: ")[1:]:
        lines = block.splitlines()
        name = lines[0].strip().replace("\\", "/").lstrip("./")
        resolved = frozenset(re.findall(r"LicenseInfoInFile: (.+)", block))
        holders = re.search(r"FileCopyrightText: <text>(.*?)</text>", block, re.S)

        expected = expected_licences(name)
        assert resolved == expected, (
            f"{name} resolves to {sorted(resolved)}, not {sorted(expected)}. If the "
            f"file quotes an SPDX tag as an example, wrap it in REUSE-IgnoreStart/End."
        )
        # Shape, not count. A second holder is a contributor, which CONTRIBUTING
        # explicitly allows and 'closest' precedence exists to preserve; what
        # must not appear is prose — a heading opening with the word that opens
        # a notice was reported here as the holder once.
        attributed = holders.group(1).strip().splitlines() if holders else []
        assert attributed, f"{name} resolves to no copyright holder at all"
        strays = [line for line in attributed if not NOTICE.match(line.strip())]
        assert not strays, (
            f"{name} attributes {strays} — that is prose read as a copyright notice. "
            f"Wrap it in REUSE-IgnoreStart/End or reword it."
        )
# REUSE-IgnoreEnd


# REUSE-IgnoreStart
@pytest.mark.parametrize(
    "line, is_notice",
    [
        # An explicit tag is a declaration; a holder is enough, no year needed.
        ("SPDX-FileCopyrightText: 2026 Jana Novakova", True),
        ("SPDX-FileCopyrightText: Jana Novakova", True),
        # Bare forms are ambiguous with prose, so they must carry a year.
        ("© 2026 Peter Bezemek", True),
        ("(c) 2026 Peter Bezemek", True),
        ("Copyright 2026 Peter Bezemek", True),
        # Prose. The first two are lines of LICENSING.md; the third is the
        # heading reuse once reported as this project's copyright holder.
        ("(c) any right to restrict extraction or re-utilisation", False),
        ("Copyright and Related Rights", False),
        ("Copyright holder and contact", False),
        ("© Some Prose Here", False),
    ],
)
def test_notice_shape_separates_a_copyright_line_from_prose(line, is_notice):
    """
    The guard the SBOM test leans on, tested directly rather than through reuse.
    Both halves matter: prose that opens with a notice word must not pass, and a
    real notice must not be rejected — a year requirement written as
    `(?:©|\\(c\\)|Copyright)\\b` silently does the latter, because `\\b` after a
    non-word character never matches a following space.
    """
    assert bool(NOTICE.match(line)) is is_notice
# REUSE-IgnoreEnd


def test_readmes_link_to_each_other():
    assert "README.sk.md" in README_EN, "the English README does not link to the Slovak one"
    assert "README.md" in README_SK, "the Slovak README does not link to the English one"
