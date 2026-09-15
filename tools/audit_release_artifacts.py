# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Check actual core archives for unapproved databases and the exact candidate JSON.

Wheels must stay runtime-only: any database is a defect. Source archives ship the
inputs the published patterns are derived from, so databases are allowed there --
but only under tests/data/, never inside the importable package.

This is a distribution-content check, not input-rights clearance or PSP approval.
Run after the separate full-API comparison gate. No archive is extracted or edited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


DATABASE_HOME = ("tests", "data")


def inspect_archive(path: Path, inventory: bytes) -> dict:
    issues, seen, compounds = [], set(), []
    expected = hashlib.sha256(inventory).hexdigest()
    is_wheel = path.suffix == ".whl"

    def inspect(name: str, content: bytes):
        if name in seen:
            issues.append(f"duplicate archive member: {name}")
        seen.add(name)
        parts = PurePosixPath(name).parts
        basename = parts[-1].lower() if parts else ""
        if ".." in parts or name.startswith("/") or "\\" in name:
            issues.append(f"unsafe archive path: {name}")
        if any(
            basename.endswith(ext) or ext + "-" in basename
            for ext in (".sqlite", ".sqlite3", ".db")
        ) or content.startswith(b"SQLite format 3\x00"):
            if is_wheel or parts[1:3] != DATABASE_HOME:
                issues.append(f"working database in distribution: {name}")
        if "pronunciation" in parts or "slabika_pronunciation" in parts:
            issues.append(f"optional pronunciation payload in core: {name}")
        if parts[-3:] == ("slabika", "data", "composita.json"):
            compounds.append(name)
            if hashlib.sha256(content).hexdigest() != expected:
                issues.append(f"compound inventory differs from reviewed candidate: {name}")

    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                if not entry.is_dir():
                    inspect(entry.filename, archive.read(entry))
    else:
        with tarfile.open(path, "r:*") as archive:
            for entry in archive:
                if entry.isfile():
                    with archive.extractfile(entry) as stream:
                        inspect(entry.name, stream.read())
                elif not entry.isdir():
                    issues.append(f"non-regular archive member: {entry.name}")
    if len(compounds) != 1:
        issues.append(f"expected one compound inventory, found {len(compounds)}")
    return {
        "archive": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "files": len(seen),
        "inventory_sha256": expected,
        "issues": issues,
        "passed": not issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path, nargs="+")
    parser.add_argument("--inventory", type=Path, required=True)
    args = parser.parse_args()
    inventory = args.inventory.read_bytes()
    data = json.loads(inventory)
    if data.get("schema_version") != 3 or not data.get("input", {}).get("surface_forms_sha256"):
        parser.error("expected a fingerprinted grammar-derived candidate, not a legacy inventory")
    results = [inspect_archive(path, inventory) for path in args.archives]
    print(
        json.dumps(
            {
                "scope": "archive contents only; not legal or linguistic clearance",
                "archives": results,
                "passed": all(r["passed"] for r in results),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
