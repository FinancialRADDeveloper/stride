"""
stride.db — SQLite connection factory and migration runner.

Only three public symbols are needed by the rest of the app:
  get_connection(db_path) -> sqlite3.Connection
  run_migrations(conn)
  app_db() -> sqlite3.Connection   # module-level singleton
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Optional

from stride.config import DB_PATH, MIGRATIONS_DIR

# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults.

    - row_factory = sqlite3.Row so columns are accessible by name
    - Foreign key enforcement ON

    WAL mode is intentionally omitted: it requires Unix file-locking
    primitives that fail on Windows bind-mounts inside Docker. DELETE
    mode (SQLite default) works on all host filesystems. This is a
    temporary concern — once we migrate to Postgres, this module
    disappears entirely.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ---------------------------------------------------------------------------
# Migration runner
# ---------------------------------------------------------------------------


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply all *.sql migration files from MIGRATIONS_DIR in sorted order.

    Tracks applied migrations in _applied_migrations so each file runs
    exactly once, even across restarts. Files must be named so that sorting
    them produces the correct application order (e.g. 0001_..., 0002_...).
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS _applied_migrations (
            name       TEXT PRIMARY KEY,
            applied_at INTEGER NOT NULL
        );
        """
    )
    import time as _time

    migration_files = sorted(Path(MIGRATIONS_DIR).glob("*.sql"))
    for path in migration_files:
        name = path.name
        already = conn.execute(
            "SELECT 1 FROM _applied_migrations WHERE name = ?", (name,)
        ).fetchone()
        if already:
            continue
        sql = path.read_text(encoding="utf-8")
        try:
            conn.executescript(sql)
        except sqlite3.OperationalError as exc:
            # "duplicate column name" means a prior run applied this migration
            # before the tracking table existed — treat it as already applied.
            if "duplicate column name" not in str(exc):
                raise
        conn.execute(
            "INSERT INTO _applied_migrations (name, applied_at) VALUES (?, ?)",
            (name, int(_time.time() * 1000)),
        )
        conn.commit()
    conn.commit()


# ---------------------------------------------------------------------------
# Application singleton — one connection per thread
# ---------------------------------------------------------------------------

_local = threading.local()


def app_db() -> sqlite3.Connection:
    """Return a per-thread SQLite connection.

    Flask runs callbacks on a thread pool; sharing one connection across
    threads causes sqlite3.InterfaceError when cursors interleave.
    threading.local() gives each thread its own connection. Migrations are
    idempotent so running them per-thread is safe.
    """
    if getattr(_local, "connection", None) is None:
        db_path = Path(DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _local.connection = get_connection(db_path)
        run_migrations(_local.connection)
    return _local.connection
