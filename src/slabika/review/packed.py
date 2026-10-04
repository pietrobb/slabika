# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Keep a SQLite store tracked as ``<name>.sqlite.xz`` and work on an unpacked copy.

The repository carries only the compressed file. ``ensure_unpacked`` creates or
refreshes the working copy next to it when needed, ``pack`` writes local changes
back. A small ``<name>.sqlite-sync`` file records which compressed file the copy
came from, so a newer repository version is never mixed with unpacked edits.

    python -m slabika.review.packed status|unpack|pack [--force] [path]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import os
import sqlite3
from pathlib import Path

DEFAULT_STORE = Path(__file__).resolve().parents[3] / "tests" / "data" / "review_decisions.sqlite"
PRESET = 9


class PackConflict(RuntimeError):
    pass


def packed_path(db: Path) -> Path:
    return db.with_name(db.name + ".xz")


def _sync_path(db: Path) -> Path:
    return db.with_name(db.name + "-sync")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_sync(db: Path) -> dict:
    try:
        return json.loads(_sync_path(db).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_sync(db: Path) -> None:
    state = {"xz_sha256": _sha256(packed_path(db)), "db_sha256": _sha256(db)}
    _sync_path(db).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def decompress(source: Path, target: Path) -> None:
    temporary = target.with_name(target.name + ".unpacking")
    with lzma.open(source, "rb") as reader, temporary.open("wb") as writer:
        for block in iter(lambda: reader.read(1 << 20), b""):
            writer.write(block)
    os.replace(temporary, target)


def status(db: Path) -> str:
    """One of: plain, missing, current, changed, outdated, conflict."""
    xz = packed_path(db)
    if not xz.exists():
        return "plain"
    if not db.exists():
        return "missing"
    sync = _read_sync(db)
    local_changed = sync.get("db_sha256") != _sha256(db)
    if sync.get("xz_sha256") == _sha256(xz):
        return "changed" if local_changed else "current"
    return "conflict" if local_changed else "outdated"


def ensure_unpacked(db: Path, force: bool = False) -> str:
    """Make ``db`` usable; unpack it from ``db.xz`` when missing or outdated.

    Returns the status before the call. Raises PackConflict when the compressed
    file changed and the working copy also has changes that were never packed.
    """
    state = status(db)
    if state == "conflict" and not force:
        raise PackConflict(
            f"{packed_path(db)} changed since {db} was unpacked, and {db} has unpacked "
            "changes of its own. Keep local changes: python -m slabika.review.packed pack "
            f"--force {db}; take the repository version: python -m slabika.review.packed "
            f"unpack --force {db}"
        )
    if state in ("missing", "outdated") or (state == "conflict" and force):
        decompress(packed_path(db), db)
        _write_sync(db)
    return state


def pack(db: Path, force: bool = False) -> bool:
    """Write ``db`` to ``db.xz``. Returns False when there was nothing to pack."""
    state = status(db)
    if state == "current":
        return False
    if state == "conflict" and not force:
        raise PackConflict(
            f"{packed_path(db)} changed since {db} was unpacked; packing would overwrite "
            "it. Use --force to keep the local copy."
        )
    if state == "missing":
        raise FileNotFoundError(db)
    snapshot = db.with_name(db.name + ".packing")
    snapshot.unlink(missing_ok=True)
    with sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True) as source:
        source.execute("VACUUM INTO ?", (str(snapshot),))
    source.close()
    temporary = packed_path(db).with_name(packed_path(db).name + ".tmp")
    try:
        with snapshot.open("rb") as reader, lzma.open(temporary, "wb", preset=PRESET) as writer:
            for block in iter(lambda: reader.read(1 << 20), b""):
                writer.write(block)
        os.replace(temporary, packed_path(db))
    finally:
        snapshot.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
    _write_sync(db)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("status", "unpack", "pack"))
    parser.add_argument("path", type=Path, nargs="?", default=DEFAULT_STORE)
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.command == "unpack":
            before = ensure_unpacked(arguments.path, arguments.force)
            print(f"{arguments.path}: {before} -> {status(arguments.path)}")
        elif arguments.command == "pack":
            packed = pack(arguments.path, arguments.force)
            print(f"{packed_path(arguments.path)}: {'packed' if packed else 'already current'}")
        else:
            print(f"{arguments.path}: {status(arguments.path)}")
    except PackConflict as error:
        parser.exit(2, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
