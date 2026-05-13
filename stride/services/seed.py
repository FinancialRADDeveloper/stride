"""Seed realistic tasks on first boot if the DB is empty."""

from __future__ import annotations

import datetime
import sqlite3

from stride.services.tasks import create_task, list_tasks


def _today() -> str:
    return datetime.date.today().isoformat()


def _offset(days: int) -> str:
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


def seed_if_empty(conn: sqlite3.Connection) -> int:
    """Insert seed tasks if there are currently 0 tasks. Returns count inserted."""
    existing = list_tasks(conn, include_done=True)
    if existing:
        return 0

    seeds = [
        # Today
        dict(
            title="Draft blog post outline — Phase 2 UI",
            day_key=_today(),
            priority="P1",
            size="L",
            description="Capture the Dash board layout decisions, component conventions, and what it took to get cards rendering.",
            category_id="build",
            estimate_min=120,
        ),
        dict(
            title="Reply to inbox — flag anything urgent",
            day_key=_today(),
            priority="P3",
            size="XS",
            category_id="admin",
            estimate_min=15,
        ),
        dict(
            title="30-minute walk",
            day_key=_today(),
            priority="P4",
            size="S",
            category_id="health",
            estimate_min=30,
        ),
        # Tomorrow
        dict(
            title="Review pull request and merge",
            day_key=_offset(1),
            priority="P2",
            size="M",
            category_id="work",
            estimate_min=60,
        ),
        dict(
            title="Plan weekend — add tasks for Saturday",
            day_key=_offset(1),
            priority="P4",
            size="XS",
            category_id="personal",
            estimate_min=10,
        ),
    ]

    for s in seeds:
        create_task(conn, **s)

    return len(seeds)
