"""
stride.db — SQLite connection factory and migration runner.

Only three public symbols are needed by the rest of the app:
  get_connection(db_path) -> sqlite3.Connection
  run_migrations(conn)
  app_db() -> sqlite3.Connection   # module-level singleton
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from stride.config import DB_PATH, MIGRATIONS_DIR

# ---------------------------------------------------------------------------
# Connection factory
# ---------------------------------------------------------------------------


def get_connection(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults.

    - row_factory = sqlite3.Row so columns are accessible by name
    - WAL journal mode for concurrent reader/writer
    - Foreign key enforcement ON
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # WAL mode lets the background sync loop write while Dash reads
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ---------------------------------------------------------------------------
# Migration runner
# ---------------------------------------------------------------------------


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply all *.sql migration files from MIGRATIONS_DIR in sorted order.

    Each file is executed as a single script via executescript(), which
    commits any open transaction before running and commits again at the
    end. Migration files are designed to be idempotent (CREATE IF NOT
    EXISTS, INSERT OR IGNORE) so re-running is safe.
    """
    migration_files = sorted(Path(MIGRATIONS_DIR).glob("*.sql"))
    for path in migration_files:
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
    conn.commit()


# ---------------------------------------------------------------------------
# Application singleton
# ---------------------------------------------------------------------------

_connection: Optional[sqlite3.Connection] = None


def app_db() -> sqlite3.Connection:
    """Return the application-level SQLite connection.

    Opens the connection and applies migrations on the first call;
    returns the cached connection on every subsequent call.

    Not thread-safe across processes — that's fine for a single-user
    local app. The background scheduler accesses via the same singleton
    (WAL mode handles the concurrent writes).
    """
    global _connection
    if _connection is None:
        # Ensure the data directory exists so sqlite3.connect() can create the file
        db_path = Path(DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        _connection = get_connection(db_path)
        run_migrations(_connection)
    return _connection
