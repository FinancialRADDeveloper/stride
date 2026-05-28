# Choosing SQLite for a Production App — and Why That's the Right Call More Often Than You Think

Every new project faces the database question. For Stride, the choice was SQLite. Not as a temporary measure, not as a prototype shortcut, but as a deliberate production decision — the same database that powers the running application on AWS App Runner today.

The choice is still sometimes treated as surprising. "SQLite is for mobile apps and local tooling, not production." This belief is outdated. Stripe, Shopify, and GitHub all use SQLite in various production contexts. The question is not whether SQLite is a legitimate production database — it is — but whether it fits the specific constraints of your application.

---

## What We Built

PR #5 adds three things:

1. **A migration runner** (`stride/migrations/`) — numbered SQL files (`001_create_tasks.sql`, `002_add_task_events.sql`, etc.) applied in order by `run_migrations(conn)`, tracked via a `schema_version` table
2. **A connection factory** (`app_db()`) — returns a configured `sqlite3.Connection` with `row_factory = sqlite3.Row`, WAL journal mode, and foreign key enforcement
3. **The initial schema** — two tables: `tasks` and `task_events`

The `tasks` table captures the full task model: `id`, `title`, `description`, `priority`, `estimate_min`, `day_key`, `done`, `created_at`, `category`, `size`. The `task_events` table is append-only: `id`, `task_id`, `kind` (edit/move/done/undone/delete), `payload` (JSON), `created_at`. Events are never modified after insert.

---

## Why SQLite

The decision criteria for Stride's database:

**Single user, single writer.** A personal task board has one authenticated user — me. Concurrent writes from multiple users or processes are not a concern. SQLite's single-writer model is not a limitation; it is a match.

**Zero infrastructure.** SQLite is a file. There is no database server to start, stop, monitor, or upgrade. In production (App Runner), the database file lives in the container's data directory and is replicated to S3 by Litestream (see PR #30). In development, `uv run stride` creates the file on first boot. No connection strings, no environment variables for database credentials, no VPC routing.

**Portability.** The production database can be downloaded to a laptop as a single file and opened with `sqlite3 stride.db` for debugging. Postgres offers `pg_dump`, which is excellent — but it requires a server, authentication, and format knowledge. SQLite inspection requires a filename.

**Performance at scale.** A personal task board will never exceed tens of thousands of tasks. SQLite reads and writes at this scale are sub-millisecond. The performance envelope that would require Postgres is multiple orders of magnitude beyond any realistic usage pattern for Stride.

---

## The Migration Pattern

The migration runner is worth describing in detail because it is a pattern that appears in almost every project and is frequently overcomplicated.

```
stride/migrations/
    001_create_tasks.sql
    002_create_task_events.sql
    003_add_category_column.sql
    004_add_delegated_flag.sql
    005_add_reschedule_columns.sql
```

`run_migrations(conn)` does the following:
1. Creates the `schema_version` table if it does not exist
2. Reads the current version from `schema_version` (defaults to 0 if the table is empty)
3. Lists all `.sql` files in the migrations directory, sorts them by filename
4. Applies each migration whose number is greater than the current version
5. Updates `schema_version` after each successful migration

Each migration file is a plain SQL file containing the DDL for one change. The files are idempotent: adding a column uses `ADD COLUMN IF NOT EXISTS`, creating a table uses `CREATE TABLE IF NOT EXISTS`. A migration that has already been applied can be re-run without errors. This matters for development environments where you might run migrations multiple times.

The `schema_version` table is the simplest possible migration tracking: one row, one integer. No migration timestamps, no checksums, no lock tables. For a single-user application with a controlled deployment process, this is correct.

---

## The WAL/DELETE Journal Mode Decision

The initial implementation used WAL (Write-Ahead Logging) journal mode — `PRAGMA journal_mode=WAL` on every connection. WAL mode offers better read/write concurrency and lower contention under multiple readers. For a Dash application with a thread pool, this seemed like the right choice.

Then we containerised on Windows.

WAL mode creates two additional files alongside the database: `stride.db-wal` and `stride.db-shm`. On Linux, these files behave correctly with Docker bind-mounts. On Windows, NTFS locking semantics differ from POSIX. When the container writes to the WAL file via a Windows bind-mount (the `./data:/app/data` Docker volume), the file locking fails silently — the database appears to write correctly but the WAL file is never checkpointed into the main database file. On container restart, the WAL file is gone and recent writes are lost.

The fix was to revert to DELETE journal mode — `PRAGMA journal_mode=DELETE` on every connection, enforced in the `app_db()` factory. DELETE mode writes directly to the main database file. No secondary files, no locking dependencies, no Windows bind-mount issues. The performance impact is negligible at Stride's write volume.

This is a case where the "better" technical choice (WAL) broke a real deployment constraint (Windows Docker development). Knowing this, the correct default is DELETE mode with a comment explaining why, not WAL mode with a mystery failure on Windows.

---

## The Key Decision: `row_factory = sqlite3.Row`

SQLite's default `fetchone()` and `fetchall()` return tuples. Accessing columns by index (`row[0]`, `row[1]`) is error-prone and opaque. `sqlite3.Row` makes columns accessible by name (`row["title"]`, `row["day_key"]`).

This is a small thing that has a large effect on code readability. With `row_factory = sqlite3.Row`, service functions that return task data read like Python dictionaries. Without it, every function that accesses task data has to maintain positional awareness of the column order.

It also makes refactoring safe. If you add a column between `title` and `description` in the schema, every piece of code accessing `row[1]` for description breaks silently. Code accessing `row["description"]` does not.

---

## What the AI-Assisted Workflow Actually Looked Like

The migration pattern — numbered SQL files, `schema_version` table, sorted application — was AI-generated from a specification. The specification said "idempotent SQL files, integer version tracking, applied in order." The implementation was standard and correct on the first pass.

The WAL vs DELETE decision was mine. The AI suggested WAL as the higher-performance option. The Windows bind-mount issue was discovered later, during the containerisation sprint, and the revert to DELETE was a fix commit. The lesson was recorded in CLAUDE.md: "SQLite uses DELETE journal mode. WAL creates extra files that fail on Windows bind-mounts."

The schema design — particularly the `task_events` append-only log — was specified in the architecture document from PR #1. The AI implemented the DDL.

---

## What This Unlocks

A working database layer means the service layer (PR #6) can be built and tested immediately. The migration runner means every environment — development, CI, production — starts with the correct schema automatically, with no manual `CREATE TABLE` steps. The append-only event log means every subsequent feature that needs history (the activity timeline in PR #11, the achievement counts in PR #31) gets it for free.

---

## Takeaway for Consultants

SQLite is not a toy database. For single-user applications, local tools, and applications where portable, zero-infrastructure data storage is a feature rather than a limitation, SQLite is the correct choice. Choose the database that matches your actual constraints — not the one that would be correct for a much larger, more complex version of your application.

The migration pattern described here scales from two tables to two hundred. Numbered SQL files, integer version tracking, idempotent DDL — these three properties are all you need. Do not reach for Alembic or Flyway until the complexity demands it.

---

## LinkedIn Summary

Stride uses SQLite in production. Not as a prototype shortcut — as a deliberate choice. Single user, zero infrastructure, portable file, sub-millisecond reads. The migration runner is 40 lines of Python that scales from 2 tables to 200. The WAL/DELETE lesson: the "better" journal mode broke on Windows Docker bind-mounts, so the correct default is DELETE with a comment explaining why. Fit the database to the constraints, not the constraints to a prestigious database.
