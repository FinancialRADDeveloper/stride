# Why a Monday-to-Sunday Week Is Wrong for a Task Board

The initial board implementation showed a fixed Mon-Sun week. Week offset 0 was this Monday to this Sunday. Offset -1 was last Monday to last Sunday. Clean, symmetrical, obvious.

Wrong.

If today is Friday, a Mon-Sun week shows you four days of history and one day of future. If today is Monday, it shows you six days of future. The amount of planning horizon visible in the board changes by 83% depending on which day of the week you open it.

PR #16 replaced the fixed week with a rolling day window: the board always shows at least today and five future days, regardless of day of the week. It also added delegated task tracking, fixed a weekend crash, and extended the migration system to handle production upgrades automatically.

---

## What We Built

Four changes in PR #16:

1. **Rolling window algorithm** — the day range calculation was refactored to always show today + at least 5 forward days, with the start of the range adjusted by week offset for navigation
2. **Weekend IndexError fix** — `_day_label()` was crashing on Saturday and Sunday with an `IndexError` on the weekday name lookup
3. **Delegated tasks** — new `delegated` boolean column on `tasks`; tasks with `delegated=True` display a "Waiting" badge but remain on the board
4. **Migration system extension** — added migration file `004_add_delegated_flag.sql` and confirmed the upgrade path works on the production database

---

## The Rolling Window Algorithm

The original algorithm was:

```python
week_start = today - timedelta(days=today.weekday())  # Monday
days = [week_start + timedelta(days=i) for i in range(7)]
```

This gives Mon-Sun. Simple. Wrong for the reasons above.

The rolling window algorithm:

```python
def get_day_range(week_offset: int) -> list[date]:
    today = date.today()
    if week_offset == 0:
        # Always show today + 5 future days minimum
        start = today
        days = [start + timedelta(days=i) for i in range(6)]
    else:
        # For non-zero offsets, show a fixed 6-day block relative to today
        start = today + timedelta(weeks=week_offset)
        days = [start + timedelta(days=i) for i in range(6)]
    return days
```

At `week_offset=0`, today is always day 0. On Monday you see Mon-Sat. On Friday you see Fri-Wed (wrapping into next week). The planning horizon is always at least five days.

For non-zero offsets — when the user navigates backward or forward — the window shifts by whole weeks from today, showing a 6-day block. This means the Prev/Next buttons have consistent stride (one week) while the present view always centres on the current moment.

The trade-off: the board start date is no longer predictable from the calendar week. On Monday, it starts Monday. On Thursday, it starts Thursday. Users accustomed to a fixed Mon-Sun week need to adjust their mental model. This is the right trade-off for a daily-use planning tool: the current day should always be prominent, not potentially buried four days into the view.

---

## The Weekend IndexError

The `_day_label()` function originally did this:

```python
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri"]

def _day_label(day_key: str) -> str:
    d = date.fromisoformat(day_key)
    return f"{DAY_NAMES[d.weekday()]} {d.day} {d.strftime('%b')}"
```

`d.weekday()` returns 0 (Monday) through 6 (Sunday). `DAY_NAMES` had five entries. Accessing `DAY_NAMES[5]` (Saturday) raised `IndexError`.

The fix:

```python
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
```

This is the kind of bug that is invisible during weekday development and emerges on the first weekend use. The rolling window algorithm exacerbated it by potentially showing weekend dates that the fixed Mon-Fri algorithm would have excluded. The bug was dormant until the feature that revealed it was built.

---

## Delegated Tasks

A delegated task is one you have assigned to someone else and are waiting on. You cannot complete it yourself — it is blocked on someone else's action — but you do not want to lose visibility of it.

The `delegated` boolean on `tasks` defaults to `False`. When `True`, the task card displays a "Waiting on" badge in amber and the card body is rendered with reduced opacity to visually distinguish it from actionable tasks. The open count in the column header does not include delegated tasks — they are tracked separately.

The service layer change: `toggle_delegated(conn, task_id)` mirrors `toggle_done` — flips the boolean, writes a `task_events` entry (`kind="delegated"` or `kind="undelegated"`).

The database change: migration `004_add_delegated_flag.sql` adds `delegated INTEGER NOT NULL DEFAULT 0` to the `tasks` table.

---

## The Migration System Paying Off

PR #5 built the migration system. PR #16 used it for the first time on a production database.

The production App Runner instance was running with a database that had no `delegated` column. Deploying PR #16 meant the new code would try to insert and select a column that did not exist. The migration runner handles this:

On startup, `run_migrations(conn)` checks the schema version, finds version 3, and applies `004_add_delegated_flag.sql`. The column is added. The code runs against the updated schema.

Zero manual intervention. Zero downtime (SQLite DDL is fast). Zero data loss. The investment in the migration system in PR #5 — a 40-line runner and a naming convention — paid for itself immediately.

This is the value of migration infrastructure: not the first migration, which you could apply manually with minimal pain, but the tenth migration, which runs automatically against a production database you cannot easily access directly.

---

## The Trade-offs, Honestly

The rolling window is harder to reason about than a fixed week. "What day does the board start on?" is now "today, unless you have navigated away." For a personal tool where you are the only user, this is acceptable — you quickly build the intuition. For a team tool, you would need a clearer visual indicator of the current date range.

Delegated tasks on the board is a deliberate design choice over a separate "waiting" list. Keeping them visible on the day they were delegated (and aging visually if not resolved) creates a natural follow-up mechanism. The alternative — a separate section or filter — is cleaner but requires the user to actively check another view.

---

## What the AI-Assisted Workflow Actually Looked Like

The rolling window algorithm was my design — the specification said "always show today + at least 5 future days at week_offset=0." The AI implemented the date arithmetic. I tested it on every day of the week (Monday through Sunday) to verify the edge cases.

The IndexError was found during testing and fixed immediately. The AI diagnosed the issue from the traceback. The fix was a seven-character addition to the array literal.

The delegated feature was specified from user requirements ("I need to track work I'm waiting on without it disappearing from the board"). The migration, service function, card rendering, and header counter adjustment were AI-generated from that specification.

---

## What This Unlocks

A rolling window means the board is useful every day of the week, not just Monday through Wednesday. Delegated task tracking makes Stride a tool for tracking work in progress, not just personal tasks. The migration system is now proven in production.

---

## Takeaway for Consultants

Fixed Monday-to-Sunday week views are wrong for daily planning. The board should centre on today and show forward planning horizon, not a calendar week that may be mostly historical by Friday. Question calendar assumptions in any planning tool — "this week" often means "most useful planning range."

---

## LinkedIn Summary

The fixed Mon-Sun week view was hiding 4 days of history on Fridays and showing 6 days of future on Mondays. The rolling window fix: always show today + 5 forward days. The seemingly minor algorithm change dramatically improved the board's utility on every day of the week. It also exposed a weekend IndexError that had been dormant — the rolling window was the first code path to generate Saturday/Sunday labels.
