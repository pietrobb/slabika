# SPDX-FileCopyrightText: 2026 Peter Bezemek
# SPDX-License-Identifier: Apache-2.0 OR MIT
import sqlite3
from contextlib import closing

import pytest

from slabika.review import packed


def _write(db, value):
    with closing(sqlite3.connect(db)) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS t(v TEXT)")
        connection.execute("DELETE FROM t")
        connection.execute("INSERT INTO t VALUES (?)", (value,))


def _read(db):
    with closing(sqlite3.connect(db)) as connection:
        return connection.execute("SELECT v FROM t").fetchone()[0]


def test_plain_store_without_archive_is_left_alone(tmp_path):
    db = tmp_path / "d.sqlite"
    assert packed.ensure_unpacked(db) == "plain"
    assert not db.exists()


def test_pack_then_unpack_round_trip(tmp_path):
    db = tmp_path / "d.sqlite"
    _write(db, "a")
    assert packed.pack(db)
    assert packed.status(db) == "current"
    assert not packed.pack(db)
    db.unlink()
    assert packed.ensure_unpacked(db) == "missing"
    assert _read(db) == "a"
    assert packed.status(db) == "current"


def test_local_changes_are_kept_and_packed(tmp_path):
    db = tmp_path / "d.sqlite"
    _write(db, "a")
    packed.pack(db)
    _write(db, "b")
    assert packed.ensure_unpacked(db) == "changed"
    assert _read(db) == "b"
    assert packed.pack(db)
    db.unlink()
    packed.ensure_unpacked(db)
    assert _read(db) == "b"


def test_newer_archive_replaces_an_untouched_copy(tmp_path):
    db, other = tmp_path / "d.sqlite", tmp_path / "other" / "d.sqlite"
    other.parent.mkdir()
    _write(db, "a")
    packed.pack(db)
    _write(other, "new")
    packed.pack(other)
    packed.packed_path(db).write_bytes(packed.packed_path(other).read_bytes())
    assert packed.ensure_unpacked(db) == "outdated"
    assert _read(db) == "new"


def test_newer_archive_never_overwrites_unpacked_edits(tmp_path):
    db, other = tmp_path / "d.sqlite", tmp_path / "other" / "d.sqlite"
    other.parent.mkdir()
    _write(db, "a")
    packed.pack(db)
    _write(other, "new")
    packed.pack(other)
    packed.packed_path(db).write_bytes(packed.packed_path(other).read_bytes())
    _write(db, "local")
    with pytest.raises(packed.PackConflict):
        packed.ensure_unpacked(db)
    with pytest.raises(packed.PackConflict):
        packed.pack(db)
    assert _read(db) == "local"
    packed.ensure_unpacked(db, force=True)
    assert _read(db) == "new"
