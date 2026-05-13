"""Task CRUD operations with append-only event history.

Every public function:
1. Loads the task (if needed).
2. Validates the change.
3. Writes the updated task row (updated_at = now).
4. Appends matching event row(s).
5. Returns the refreshed Task pydantic model.

All five steps run in one SQLite transaction so the DB is never left in a
partial state.

All timestamps are unix milliseconds: int(time.time() * 1000).
day_key format: 'YYYY-MM-DD'.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
import time
import uuid
from typing import Any

from stride.models import (
    STALE_MOVE_THRESHOLD,
    CalendarLink,
    Task,
    TaskEvent,
)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_EDITABLE_FIELDS = frozenset(
    {"title", "description", "priority", "size", "estimate_min", "time_of_day"}
)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _generate_id() -> str:
    return "c" + uuid.uuid4().hex[:20]


def _today_local() -> datetime.date:
    return datetime.date.today()


def _age_days(created_at_ms: int) -> int:
    created_date = datetime.date.fromtimestamp(created_at_ms / 1000)
    return (_today_local() - created_date).days


def _row_to_task(
    row: sqlite3.Row,
    move_count: int = 0,
    edit_count: int = 0,
    calendar: CalendarLink | None = None,
    history: list[TaskEvent] | None = None,
) -> Task:
    created_at: int = row["created_at"]
    ad = _age_days(created_at)
    done = bool(row["done"])
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        priority=row["priority"],
        size=row["size"],
        estimate_min=row["estimate_min"],
        time_of_day=row["time_of_day"],
        day_key=row["day_key"],
        done=done,
        created_at=created_at,
        updated_at=row["updated_at"],
        move_count=move_count,
        edit_count=edit_count,
        age_days=ad,
        is_stale=(move_count >= STALE_MOVE_THRESHOLD and not done),
        calendar=calendar,
        history=history or [],
    )


def _fetch_counts(conn: sqlite3.Connection, task_id: str) -> tuple[int, int]:
    """Return (move_count, edit_count) for a task."""
    row = conn.execute(
        """
        SELECT
            SUM(kind = 'moved') AS moves,
            SUM(kind = 'edited') AS edits
        FROM task_events
        WHERE task_id = ?
        """,
        (task_id,),
    ).fetchone()
    return (int(row["moves"] or 0), int(row["edits"] or 0))


def _fetch_calendar_link(
    conn: sqlite3.Connection, task_id: str
) -> CalendarLink | None:
    row = conn.execute(
        "SELECT * FROM calendar_links WHERE task_id = ?", (task_id,)
    ).fetchone()
    if row is None:
        return None
    return CalendarLink(
        calendar_id=row["calendar_id"],
        google_event_id=row["google_event_id"],
        etag=row["etag"],
        last_pushed_at=row["last_pushed_at"],
        last_pulled_at=row["last_pulled_at"],
        origin=row["origin"] if row["origin"] in ("stride", "google") else "stride",
    )


def _fetch_history(conn: sqlite3.Connection, task_id: str) -> list[TaskEvent]:
    rows = conn.execute(
        "SELECT * FROM task_events WHERE task_id = ? ORDER BY ts ASC",
        (task_id,),
    ).fetchall()
    events: list[TaskEvent] = []
    for r in rows:
        events.append(
            TaskEvent(
                id=r["id"],
                task_id=r["task_id"],
                ts=r["ts"],
                kind=r["kind"],
                payload=json.loads(r["payload"] or "{}"),
            )
        )
    return events


def _append_event(
    conn: sqlite3.Connection,
    task_id: str,
    kind: str,
    payload: dict[str, Any],
) -> None:
    conn.execute(
        "INSERT INTO task_events (task_id, ts, kind, payload) VALUES (?, ?, ?, ?)",
        (task_id, _now_ms(), kind, json.dumps(payload)),
    )


def _load_task_row(conn: sqlite3.Connection, task_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise ValueError(f"Task not found: {task_id}")
    return row


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def create_task(
    conn: sqlite3.Connection,
    *,
    title: str,
    day_key: str,
    priority: str = "P3",
    size: str = "M",
    description: str = "",
    category_id: str = "personal",
    estimate_min: int | None = None,
    time_of_day: str | None = None,
) -> Task:
    """Insert a new task and append a 'created' event.

    Returns the Task with computed fields.
    """
    task_id = _generate_id()
    now = _now_ms()

    with conn:
        conn.execute(
            """
            INSERT INTO tasks
              (id, title, description, priority, size, category_id,
               estimate_min, time_of_day, day_key, done, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                task_id,
                title,
                description,
                priority,
                size,
                category_id,
                estimate_min,
                time_of_day,
                day_key,
                now,
                now,
            ),
        )

        # Build a snapshot dict for the payload
        snapshot = {
            "id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "size": size,
            "category_id": category_id,
            "estimate_min": estimate_min,
            "time_of_day": time_of_day,
            "day_key": day_key,
            "done": False,
            "created_at": now,
            "updated_at": now,
        }
        _append_event(conn, task_id, "created", {"snapshot": snapshot})

    row = _load_task_row(conn, task_id)
    return _row_to_task(row, move_count=0, edit_count=0)


def delete_task(conn: sqlite3.Connection, task_id: str) -> None:
    """Delete a task and all its events (cascade).

    Copies the latest snapshot into deleted_tasks before deletion so the
    tombstone survives for audit / calendar reconcile.
    """
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return  # already gone

    now = _now_ms()
    with conn:
        # Copy to tombstone table if it exists (migration may not have run yet)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO deleted_tasks
                  (id, title, description, priority, size, category_id,
                   estimate_min, time_of_day, day_key, done,
                   created_at, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["title"],
                    row["description"],
                    row["priority"],
                    row["size"],
                    row["category_id"],
                    row["estimate_min"],
                    row["time_of_day"],
                    row["day_key"],
                    row["done"],
                    row["created_at"],
                    row["updated_at"],
                    now,
                ),
            )
        except Exception:
            pass  # deleted_tasks table may not exist in older schemas

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def list_tasks(
    conn: sqlite3.Connection,
    *,
    day_keys: list[str] | None = None,
    include_done: bool = True,
    full: bool = False,
) -> list[Task]:
    """Return tasks, optionally filtered by day_keys.

    If full=True, also loads history for each task.
    Computes move_count, edit_count, age_days, is_stale per task.
    """
    query = "SELECT * FROM tasks"
    conditions: list[str] = []
    params: list[Any] = []

    if day_keys is not None:
        placeholders = ", ".join("?" for _ in day_keys)
        conditions.append(f"day_key IN ({placeholders})")
        params.extend(day_keys)

    if not include_done:
        conditions.append("done = 0")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    rows = conn.execute(query, params).fetchall()
    tasks: list[Task] = []
    for row in rows:
        move_count, edit_count = _fetch_counts(conn, row["id"])
        calendar = _fetch_calendar_link(conn, row["id"])
        history = _fetch_history(conn, row["id"]) if full else []
        tasks.append(
            _row_to_task(
                row,
                move_count=move_count,
                edit_count=edit_count,
                calendar=calendar,
                history=history,
            )
        )
    return tasks


def get_task(
    conn: sqlite3.Connection,
    task_id: str,
    *,
    full: bool = True,
) -> Task | None:
    """Return a single Task by id, or None if not found."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    move_count, edit_count = _fetch_counts(conn, task_id)
    calendar = _fetch_calendar_link(conn, task_id)
    history = _fetch_history(conn, task_id) if full else []
    return _row_to_task(
        row,
        move_count=move_count,
        edit_count=edit_count,
        calendar=calendar,
        history=history,
    )


def move_task(
    conn: sqlite3.Connection,
    task_id: str,
    to_day_key: str,
) -> Task:
    """Move a task to a different day.

    No-op (no event written) if the task is already on that day.
    Returns the task (unchanged or updated).
    """
    row = _load_task_row(conn, task_id)
    from_day_key: str = row["day_key"]

    if from_day_key == to_day_key:
        # No-op: return task as-is (no event written)
        move_count, edit_count = _fetch_counts(conn, task_id)
        calendar = _fetch_calendar_link(conn, task_id)
        return _row_to_task(row, move_count=move_count, edit_count=edit_count, calendar=calendar)

    now = _now_ms()
    with conn:
        conn.execute(
            "UPDATE tasks SET day_key = ?, updated_at = ? WHERE id = ?",
            (to_day_key, now, task_id),
        )
        _append_event(
            conn,
            task_id,
            "moved",
            {"from": from_day_key, "to": to_day_key},
        )

    return get_task(conn, task_id, full=False)  # type: ignore[return-value]


def toggle_done(conn: sqlite3.Connection, task_id: str) -> Task:
    """Flip the done flag; append 'done' or 'reopened' event accordingly."""
    row = _load_task_row(conn, task_id)
    current_done = bool(row["done"])
    new_done = not current_done
    kind = "done" if new_done else "reopened"
    now = _now_ms()

    with conn:
        conn.execute(
            "UPDATE tasks SET done = ?, updated_at = ? WHERE id = ?",
            (int(new_done), now, task_id),
        )
        _append_event(conn, task_id, kind, {})

    return get_task(conn, task_id, full=False)  # type: ignore[return-value]


def update_task(
    conn: sqlite3.Connection,
    task_id: str,
    **fields: Any,
) -> Task:
    """Update one or more editable fields on a task.

    Accepted fields: title, description, priority, size, estimate_min, time_of_day.
    Does NOT accept day_key (use move_task) or done (use toggle_done).
    Writes one 'edited' event per changed field.
    """
    invalid = set(fields) - _EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Cannot update field(s) via update_task: {invalid}")

    row = _load_task_row(conn, task_id)

    changed: list[tuple[str, Any, Any]] = []
    for field, new_value in fields.items():
        old_value = row[field]
        if old_value != new_value:
            changed.append((field, old_value, new_value))

    if not changed:
        # No actual changes — return current task unchanged
        move_count, edit_count = _fetch_counts(conn, task_id)
        calendar = _fetch_calendar_link(conn, task_id)
        return _row_to_task(row, move_count=move_count, edit_count=edit_count, calendar=calendar)

    now = _now_ms()
    set_clauses = ", ".join(f"{f} = ?" for f, _, _ in changed)
    set_values = [nv for _, _, nv in changed]
    set_values.append(now)
    set_values.append(task_id)

    with conn:
        conn.execute(
            f"UPDATE tasks SET {set_clauses}, updated_at = ? WHERE id = ?",
            set_values,
        )
        for field, old_value, new_value in changed:
            _append_event(
                conn,
                task_id,
                "edited",
                {"field": field, "from": old_value, "to": new_value},
            )

    return get_task(conn, task_id, full=False)  # type: ignore[return-value]
