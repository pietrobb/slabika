# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Inspect built payloads, not just a packaging declaration."""

import io
import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_release_artifacts import inspect_archive  # noqa: E402

CANDIDATE = json.dumps({"schema_version": 3, "input": {"surface_forms_sha256": "a" * 64}}).encode()


def wheel(tmp_path, extra=None, inventory=CANDIDATE):
    path = tmp_path / "test.whl"
    with zipfile.ZipFile(path, "w") as out:
        out.writestr("slabika/data/composita.json", inventory)
        for name, data in (extra or {}).items():
            out.writestr(name, data)
    return path


def test_clean_wheel_matches_the_exact_candidate(tmp_path):
    report = inspect_archive(wheel(tmp_path), CANDIDATE)
    assert report["passed"] and report["files"] == 1


@pytest.mark.parametrize(
    "name,data",
    [
        ("slabika/review/data/inventory.sqlite", b"not even a valid db"),
        ("slabika/review/data/inventory.sqlite-wal", b"wal"),
        ("slabika/data/renamed.json", b"SQLite format 3\x00payload"),
        ("slabika_pronunciation/model.bin", b"model"),
        ("../escape.txt", b"bad path"),
    ],
)
def test_unapproved_payload_is_rejected(tmp_path, name, data):
    assert not inspect_archive(wheel(tmp_path, {name: data}), CANDIDATE)["passed"]


def test_legacy_or_stale_inventory_is_rejected(tmp_path):
    assert not inspect_archive(wheel(tmp_path, inventory=b"{}"), CANDIDATE)["passed"]


def test_missing_inventory_is_rejected(tmp_path):
    path = tmp_path / "empty.whl"
    with zipfile.ZipFile(path, "w"):
        pass
    assert not inspect_archive(path, CANDIDATE)["passed"]


def test_source_archive_uses_the_same_payload_checks(tmp_path):
    path = tmp_path / "test.tar.gz"
    with tarfile.open(path, "w:gz") as out:
        info = tarfile.TarInfo("slabika-test/src/slabika/data/composita.json")
        info.size = len(CANDIDATE)
        out.addfile(info, io.BytesIO(CANDIDATE))
    assert inspect_archive(path, CANDIDATE)["passed"]
    with tarfile.open(path, "w:gz") as out:
        info = tarfile.TarInfo("slabika-test/linked.sqlite")
        info.type = tarfile.SYMTYPE
        info.linkname = "/private/database.sqlite"
        out.addfile(info)
    assert not inspect_archive(path, CANDIDATE)["passed"]


def test_cli_does_not_accept_unfingerprinted_legacy_inventory(tmp_path):
    inventory = tmp_path / "legacy.json"
    inventory.write_text("{}", encoding="utf8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/audit_release_artifacts.py"),
            "--inventory",
            str(inventory),
            str(wheel(tmp_path)),
        ],
        capture_output=True,
    )
    assert result.returncode == 2


def test_database_paths_cannot_be_force_included():
    tomllib = pytest.importorskip("tomllib")
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf8"))
    targets = config["tool"]["hatch"]["build"]["targets"]
    for target in ("wheel", "sdist"):
        assert "**/*.sqlite" in targets[target]["exclude"]
        assert "**/*.db" in targets[target]["exclude"]
        assert not any(
            ".sqlite" in name or ".db" in name for name in targets[target].get("force-include", {})
        )
