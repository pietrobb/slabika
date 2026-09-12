# SPDX-FileCopyrightText: 2026 slabika contributors
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Migrations for legacy review stores."""

import sqlite3


def allow_classification_action(store: sqlite3.Connection) -> None:
    """Extend the legacy action constraint without changing any decisions."""
    sql = store.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='decisions'"
    ).fetchone()[0]
    if "'classify'" in sql or "action TEXT NOT NULL," in sql:
        return
    old = "'confirm', 'correct', 'flag', 'uncertain', 'invalid'"
    if old not in sql:
        raise ValueError("Unrecognized decisions action constraint")
    objects = store.execute(
        "SELECT sql FROM sqlite_master WHERE tbl_name='decisions' "
        "AND type IN ('index', 'trigger') AND sql IS NOT NULL"
    ).fetchall()
    store.execute("SAVEPOINT classification_schema")
    try:
        store.execute(sql.replace('CREATE TABLE decisions',
                                  'CREATE TABLE decisions_classify_migration', 1)
                      .replace(old, old + ", 'classify'", 1))
        store.execute("INSERT INTO decisions_classify_migration SELECT * FROM decisions")
        store.execute("DROP TABLE decisions")
        store.execute("ALTER TABLE decisions_classify_migration RENAME TO decisions")
        for obj in objects:
            store.execute(obj[0])
        store.execute("RELEASE classification_schema")
    except Exception:
        store.execute("ROLLBACK TO classification_schema")
        store.execute("RELEASE classification_schema")
        raise
