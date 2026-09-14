# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""A review of one seam must never silently approve another changed API mode."""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from compare_composita import MODES
from review_composita_changes import render, reviewed_changes


def output(form, points):
    return {
        **{mode: {"break_points": points, "hyphenate": render(form, points)} for mode in MODES},
        "divisions": [form[:p] + "-" + form[p:] for p in points],
    }


def decision():
    return {
        "schema_version": 1,
        "reviewer": "AI test",
        "authority": "PSP V",
        "groups": [{"forms": ["etnograf"], "remove": [5], "add": [4], "reason": "etno|graf"}],
    }


def test_exact_reviewed_transition_materializes():
    change = {
        "form": "etnograf",
        "before": output("etnograf", [2, 5]),
        "after": output("etnograf", [2, 4]),
    }
    approved, pending = reviewed_changes([change], decision())
    assert approved == [change] and not pending


@pytest.mark.parametrize("field", [*MODES, "divisions"])
def test_other_output_change_is_not_approved(field):
    change = {
        "form": "etnograf",
        "before": output("etnograf", [2, 5]),
        "after": output("etnograf", [2, 4]),
    }
    change["after"] = copy.deepcopy(change["after"])
    change["after"][field] = (
        [] if field == "divisions" else {"break_points": [4], "hyphenate": "etno·graf"}
    )
    approved, pending = reviewed_changes([change], decision())
    assert not approved and len(pending) == 1


def test_unreviewed_form_remains_pending():
    change = {"form": "neznáme", "before": output("neznáme", [2]), "after": output("neznáme", [3])}
    assert reviewed_changes([change], decision())[1] == [
        {"form": "neznáme", "reason": "not reviewed"}
    ]


def test_contextual_modes_must_remain_exactly_unchanged_when_declared():
    review = decision()
    review["groups"] = [
        {
            "forms": ["Indoázii"],
            "remove": [5],
            "add": [],
            "preserve_contextual": True,
            "reason": "Indo|ázii",
        }
    ]
    before = output("Indoázii", [2, 4, 5])
    after = output("Indoázii", [2, 4])
    for mode in ("contextual", "all_contextual"):
        after[mode] = before[mode]
    change = {"form": "Indoázii", "before": before, "after": after}
    assert reviewed_changes([change], review)[0] == [change]
    after["contextual"] = {"break_points": [2, 4], "hyphenate": "In·do·ázii"}
    assert not reviewed_changes([change], review)[0]


@pytest.mark.parametrize("form", ["oslovinu", "oslovinou"])
def test_nominal_reading_removes_only_the_spurious_contextual_prefix(form):
    review = decision()
    review["groups"] = [
        {
            "forms": [form],
            "remove": [],
            "add": [2],
            "contextual_remove": [1],
            "reason": "osol, not o- plus verb",
        }
    ]
    before = output(form, [4, 6])
    after = output(form, [2, 4, 6])
    for mode in ("contextual", "all_contextual"):
        before[mode] = output(form, [1, 4, 6])[mode]
    change = {"form": form, "before": before, "after": after}
    assert reviewed_changes([change], review)[0] == [change]
    after["contextual"] = output(form, [1, 2, 4, 6])["contextual"]
    assert not reviewed_changes([change], review)[0]


@pytest.mark.parametrize("points", [[0], [True], [99], [1, 1], [2]])
def test_invalid_contextual_removal_rejected(points):
    review = decision()
    review["groups"][0].update({"contextual_remove": points, "add": [2]})
    with pytest.raises(ValueError):
        reviewed_changes([], review)


def test_duplicate_decisions_are_rejected():
    review = decision()
    review["groups"] *= 2
    with pytest.raises(ValueError, match="duplicate"):
        reviewed_changes([], review)
