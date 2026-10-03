# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Read-only experiment: name priors versus sentence-initial capitalization.

This does not change runtime routing. Unlabelled corpus forms are exposure
proxies, not language truth; review labels are not independent test labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from slabika import hyphenate, language_scores  # noqa: E402
from slabika.language import normalize_language, reviewed_language  # noqa: E402

# Native-word controls, also tested with sentence-initial capitalization.
SLOVAK_CONTROLS = """
aby ahoj ak ale ani áno až bez bol bola bolo boli bude budú by bývať
celý cesta človek čo deň dnes dobrý dom doma druhý dvere hovorí hlavný
hneď chcem ich ide iba ja je jeho jej jeden ešte keď kde kto kniha
ktorý lebo len ľudia mal malé mama má medzi miesto môj môže musí my
na nad náš nebol nech nie nič nový o od okno ona oni on opäť ostatné
otec päť po pod povedal práca pre pred preto pri prvý potom rok ruka
sa som srdce stále sú svet svoj tak tam teraz tiež to tu tvoj už v
voda veľký veľmi večer všetko vy z za zajtra zem zo život žena
""".split()
SLOVAK_NAME_CONTROLS = """
Štefan Štefana Štefanovi Jozef Jozefa Jozefovi Ľudovít Ľudovíta
Ľudovítovi Ján Jána Jánovi Juraj Juraja Jurajovi Michal Michala
Michalovi Bratislava Bratislavy Bratislave Košice Košíc Košiciach
""".split()


def candidate_language(ranking, foreign_bonus: float, minimum_margin: float) -> str | None:
    if not ranking:
        return None
    adjusted = sorted(
        ((item.score + (foreign_bonus if item.language != "slovak" else 0), item.language)
         for item in ranking),
        reverse=True,
    )
    if len(adjusted) < 2 or adjusted[0][0] - adjusted[1][0] < minimum_margin:
        return None
    # A tie is not evidence of a language identity.
    if adjusted[0][0] == adjusted[1][0]:
        return None
    return adjusted[0][1]


def family_key(form: str) -> str:
    # Keep explicit base-prefix relatives together in diagnostics, never treat
    # this approximate grouping as a morphological or language judgement.
    return form.lower()[:4]


def experiment(inventory: Path, decisions: Path) -> dict:
    with closing(sqlite3.connect(inventory.resolve().as_uri() + "?mode=ro", uri=True)) as con:
        forms = [row[0] for row in con.execute("SELECT form FROM forms ORDER BY form")]
    with closing(sqlite3.connect(decisions.resolve().as_uri() + "?mode=ro", uri=True)) as con:
        rows = con.execute(
            "SELECT form, is_proper_name, language FROM decisions "
            "WHERE COALESCE(is_deleted, 0) = 0 ORDER BY form"
        ).fetchall()
    proper = {form for form, flag, _ in rows if flag == 1}
    labelled = {form: normalize_language(label) for form, flag, label in rows
                if flag == 1 and label is not None}
    capitals = {form for form in forms if len(form) >= 3 and form[0].isupper()
                and (form.isalpha() or all(part.isalpha() for part in form.split("-")))}
    lowercase = {form for form in forms if len(form) >= 3 and form.isalpha() and form.islower()}
    title_controls = {form[0].upper() + form[1:] for form in SLOVAK_CONTROLS if len(form) >= 3}
    groups = {
        "confirmed_names": proper,
        "all_capitalized_inventory": capitals,
        "lowercase_inventory_titlecased_proxy": {form[0].upper() + form[1:] for form in lowercase},
        "native_sentence_initial_controls": title_controls,
        "slovak_name_controls": set(SLOVAK_NAME_CONTROLS),
    }
    all_forms = set().union(*groups.values())
    rankings = {form: language_scores(form) for form in sorted(all_forms)}
    results = []
    # Explore both a foreign-name prior and a reject/abstain margin. Parameters
    # are a sweep, not an independently validated calibrated profile.
    for bonus in (0, 2, 5, 10):
        for margin in (0, 5, 10, 20):
            by_group = {}
            for name, words in groups.items():
                predictions = {form: candidate_language(rankings[form], bonus, margin)
                               for form in sorted(words)}
                counts = Counter(predictions.values())
                detail = {"size": len(words),
                          "predictions": {language or "abstain": count
                                          for language, count in counts.items()}}
                if name in ("native_sentence_initial_controls", "slovak_name_controls"):
                    detail["false_foreign"] = [form for form, language in predictions.items()
                                               if language not in (None, "slovak")]
                if name in ("confirmed_names", "all_capitalized_inventory"):
                    # Exposure relative to the unchanged generic score; not
                    # an error rate because these forms have no gold language.
                    switched = [form for form, language in predictions.items()
                                if language is not None and rankings[form]
                                and language != rankings[form][0].language]
                    detail["identity_switches"] = len(switched)
                    detail["switch_examples"] = switched[:30]
                by_group[name] = detail
            evaluation = Counter()
            for form, expected in labelled.items():
                predicted = candidate_language(rankings[form], bonus, margin)
                evaluation["abstain" if predicted is None else
                           "correct" if predicted == expected else "wrong"] += 1
            results.append({"foreign_bonus": bonus, "minimum_margin": margin,
                            "groups": by_group, "review_label_diagnostic": dict(evaluation)})
    changed = []
    explicit_forms = {form.lower() for form, _, label in rows if label is not None}
    for form in sorted(capitals):
        ranking = rankings[form]
        if not ranking or form.lower() in explicit_forms or reviewed_language(form) is not None:
            continue
        before = hyphenate(form)
        after = hyphenate(form, language=ranking[0].language)
        if before != after:
            changed.append({"form": form, "top_score_language": ranking[0].language,
                            "current": before, "ungated_guess": after})
    return {
        "method": "Existing multiclass scores; 16 name-prior/margin candidates, no runtime changes",
        "limitations": [
            "Inventory casing has no sentence position; titlecased lower-case forms are exposure proxies.",
            "Lowercase inventory includes foreign words; proxy counts are not false-positive rates.",
            "Review labels are diagnostic only, not an independent gold set.",
            "Four-character grouping is approximate; actual lexicon calibration needs base identity.",
            "Correct language does not prove correct pronunciation or typographic division.",
        ],
        "sources": {"inventory": str(inventory), "decisions": str(decisions),
                    "router_sha256": hashlib.sha256(
                        (ROOT / "src/slabika/data/language_router_profile.json").read_bytes()
                    ).hexdigest()},
        "confirmed_labelled_names": labelled,
        "labelled_family_groups": len({family_key(form) for form in labelled}),
        "independent_calibration_available": False,
        "candidates": results,
        "forced_top_language_division_changes": changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path,
                        default=ROOT / "tests/data/translatemaster_hyphenation_working.sqlite")
    parser.add_argument("--decisions", type=Path,
                        default=ROOT / "tests/data/review_decisions.sqlite")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = experiment(args.inventory, args.decisions)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved read-only experiment to {args.output}")
    print("Independent calibration unavailable; no profile was activated.")
    print(f"Forced top-language guesses change {len(result['forced_top_language_division_changes'])} divisions.")
    for candidate in result["candidates"]:
        groups = candidate["groups"]
        print(candidate["foreign_bonus"], candidate["minimum_margin"],
              "native false foreign", len(groups["native_sentence_initial_controls"]["false_foreign"]),
              "SK name false foreign", len(groups["slovak_name_controls"]["false_foreign"]),
              "review labels", candidate["review_label_diagnostic"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
