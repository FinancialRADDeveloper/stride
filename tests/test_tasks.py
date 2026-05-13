"""Tests for stride.services.tasks — per spec §9."""

from __future__ import annotations

import pytest

from stride.services.tasks import (
    create_task,
    get_task,
    list_tasks,
    move_task,
    toggle_done,
    update_task,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event_kinds(conn, task_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT kind FROM task_events WHERE task_id = ? ORDER BY ts, id",
        (task_id,),
    ).fetchall()
    return [r["kind"] for r in rows]


def _event_count(conn, task_id: str, kind: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM task_events WHERE task_id = ? AND kind = ?",
        (task_id, kind),
    ).fetchone()
    return row["n"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_create_writes_one_event(db):
    """create_task writes exactly one 'created' event."""
    task = create_task(
        db,
        title="Write spec",
        day_key="2026-05-13",
    )
    kinds = _event_kinds(db, task.id)
    assert kinds == ["created"], f"Expected ['created'], got {kinds}"


def test_update_writes_per_field_events(db):
    """update_task with 3 changed fields writes 3 'edited' events with correct from/to."""
    task = create_task(
        db,
        title="Original title",
        day_key="2026-05-13",
        priority="P3",
        size="M",
        description="Original description",
    )

    updated = update_task(
        db,
        task.id,
        title="New title",
        priority="P1",
        description="New description",
    )

    edited_rows = db.execute(
        "SELECT payload FROM task_events WHERE task_id = ? AND kind = 'edited' ORDER BY ts, id",
        (task.id,),
    ).fetchall()

    import json

    payloads = [json.loads(r["payload"]) for r in edited_rows]
    assert len(payloads) == 3, f"Expected 3 edited events, got {len(payloads)}"

    # Build a map of field -> {from, to}
    by_field = {p["field"]: p for p in payloads}

    assert "title" in by_field
    assert by_field["title"]["from"] == "Original title"
    assert by_field["title"]["to"] == "New title"

    assert "priority" in by_field
    assert by_field["priority"]["from"] == "P3"
    assert by_field["priority"]["to"] == "P1"

    assert "description" in by_field
    assert by_field["description"]["from"] == "Original description"
    assert by_field["description"]["to"] == "New description"


def test_move_same_day_is_noop(db):
    """move_task to the same day_key writes no 'moved' event."""
    task = create_task(db, title="Same day", day_key="2026-05-13")
    move_task(db, task.id, "2026-05-13")

    moved_count = _event_count(db, task.id, "moved")
    assert moved_count == 0, f"Expected 0 moved events, got {moved_count}"

    # Task day_key is unchanged
    t = get_task(db, task.id, full=False)
    assert t is not None
    assert t.day_key == "2026-05-13"


def test_move_cross_day_writes_event(db):
    """move_task to a different day writes a 'moved' event with both day keys."""
    task = create_task(db, title="Cross-day move", day_key="2026-05-13")
    moved = move_task(db, task.id, "2026-05-14")

    assert moved.day_key == "2026-05-14"

    moved_rows = db.execute(
        "SELECT payload FROM task_events WHERE task_id = ? AND kind = 'moved'",
        (task.id,),
    ).fetchall()
    assert len(moved_rows) == 1

    import json

    payload = json.loads(moved_rows[0]["payload"])
    assert payload["from"] == "2026-05-13"
    assert payload["to"] == "2026-05-14"


def test_derived_counts(db):
    """move_count and edit_count are computed correctly after a mixed sequence."""
    task = create_task(db, title="Count test", day_key="2026-05-12")

    # 2 moves
    move_task(db, task.id, "2026-05-13")
    move_task(db, task.id, "2026-05-14")

    # 1 edit (2 fields changed = 2 edit events)
    update_task(db, task.id, title="Updated title", description="Updated desc")

    t = get_task(db, task.id, full=False)
    assert t is not None
    assert t.move_count == 2, f"Expected move_count=2, got {t.move_count}"
    assert t.edit_count == 2, f"Expected edit_count=2, got {t.edit_count}"

    # Also verify via list_tasks
    tasks = list_tasks(db, day_keys=["2026-05-14"])
    assert len(tasks) == 1
    assert tasks[0].move_count == 2
    assert tasks[0].edit_count == 2


def test_toggle_done_sequence(db):
    """toggle_done three times → 'done', 'reopened', 'done'; final done=True."""
    task = create_task(db, title="Toggle test", day_key="2026-05-13")

    t1 = toggle_done(db, task.id)
    assert t1.done is True

    t2 = toggle_done(db, task.id)
    assert t2.done is False

    t3 = toggle_done(db, task.id)
    assert t3.done is True

    # Check the sequence of events (excluding the initial 'created')
    kinds = _event_kinds(db, task.id)
    toggle_kinds = [k for k in kinds if k in ("done", "reopened")]
    assert toggle_kinds == ["done", "reopened", "done"], (
        f"Expected ['done', 'reopened', 'done'], got {toggle_kinds}"
    )

    # Final state
    final = get_task(db, task.id, full=True)
    assert final is not None
    assert final.done is True
