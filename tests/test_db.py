"""Tests for stride.db — migration runner and seed data."""


def test_migrations_apply(db):
    """All 8 tables defined in 0001_init.sql must exist after migrations."""
    expected_tables = {
        "categories",
        "tasks",
        "task_events",
        "calendar_accounts",
        "calendars",
        "calendar_links",
        "oauth_tokens",
        "settings",
    }

    rows = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    actual_tables = {row["name"] for row in rows}

    assert expected_tables <= actual_tables, (
        f"Missing tables: {expected_tables - actual_tables}"
    )


def test_seed_categories(db):
    """Exactly 6 default categories must be seeded with the correct ids."""
    expected_ids = {"build", "work", "home", "admin", "health", "personal"}

    rows = db.execute("SELECT id FROM categories").fetchall()
    actual_ids = {row["id"] for row in rows}

    assert len(rows) == 6, f"Expected 6 categories, got {len(rows)}"
    assert actual_ids == expected_ids, (
        f"Category id mismatch. Missing: {expected_ids - actual_ids}, "
        f"Extra: {actual_ids - expected_ids}"
    )
