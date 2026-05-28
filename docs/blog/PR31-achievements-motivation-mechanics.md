# Building Motivation Mechanics into a Productivity Tool — the Psychology Behind the Achievements Panel

Most task management tools are anxiety machines. The board shows you what is left. The overdue items turn red. The backlog grows. You close the app feeling worse than when you opened it.

I noticed this pattern in my own use of Stride. I was finishing tasks, but the board never felt lighter because new ones arrived at roughly the same rate. The sense of forward motion was missing. Not because I was not making progress — but because the tool had no vocabulary for progress. It only spoke in terms of what remained.

The Achievements panel is the answer to that. A left-side drawer showing every task you have completed, grouped by day, with a rolling weekly count, an estimate of time invested, and a consecutive-day streak. It is a small feature — five commits, maybe two hundred lines of Python — but the design decisions behind it are worth explaining because they reflect a set of choices about architecture and psychology that I think apply broadly.

---

## What We Built

The Achievements panel opens from a topbar button. It slides in from the left side of the board without covering it — you can see your completed history on the left while the open tasks remain visible on the right. A stats bar at the top shows your week-to-date count, estimated hours invested, and your current streak. Below it, tasks are grouped by day from newest to oldest, each row showing the category colour, task title, priority, and completion time.

The panel refreshes when it opens and when the 60-second application tick fires while it is open. When it is closed, it does nothing — no database queries, no computation, no network traffic.

---

## The Key Architectural Decisions

### Service-First Design

The core logic lives in `stride/services/achievements.py`. This file has zero Dash imports. It takes a `sqlite3.Connection` and returns a structured Python dictionary. That is its entire API.

```python
def get_achievements(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return completed task history grouped by calendar day, with stats."""
```

This is the same pattern used throughout Stride for every service: pure Python, no framework coupling, testable without starting the application. You can call `get_achievements` from a CLI, a REST endpoint, or a test suite. You can mock it in a callback test. You can benchmark it independently.

The component file (`stride/ui/components/achievements.py`) is equally clean: pure builder functions that take a dictionary and return Dash component trees. No callbacks, no database calls, no business logic. The callbacks (`stride/ui/callbacks/achievements_cb.py`) are the thin layer that connects the service to the component — they get a database connection, call the service, pass the result to the renderer, and return the output to Dash.

This separation is not just good software engineering. It is what makes it possible to work on the service logic, the component layout, and the callback wiring as genuinely independent commits.

### Python Deduplication Rather Than SQL

A task in Stride can be completed, reopened, and completed again. The `task_events` table records every state change: a row with `kind = 'done'` for each completion event. A naive SQL query — `SELECT DISTINCT task_id` or `GROUP BY task_id` — would either count a task twice or lose the correct completion timestamp.

The service fetches all `'done'` events ordered by timestamp descending, then deduplicates in Python:

```python
seen: dict[str, dict[str, Any]] = {}
for r in rows:
    task_id: str = r["id"]
    if task_id not in seen or r["completed_at_ms"] > seen[task_id]["completed_at_ms"]:
        seen[task_id] = dict(r)
```

The first time we see a task ID, we keep it. If we see it again with a later timestamp, we update it. By the time the loop ends, `seen` contains exactly one entry per task — the most recent completion. The tasks appear once in the history, at the time they were last finished.

This could be done in SQL with a self-join or a window function. I chose Python because the logic is explicit, easy to read, and easy to test with a fixture. The data volume for a personal task board is never large enough for a SQL optimisation to matter.

### `withOverlay=False`

The drawer is implemented using `dmc.Drawer` from Dash Mantine Components. By default, a drawer renders a semi-transparent overlay behind it that blocks interaction with the underlying page. I disabled this:

```python
dmc.Drawer(
    id="achievements-drawer",
    withOverlay=False,
    withCloseButton=False,
    styles={"inner": {"top": "56px"}},  # sit below the topbar
    ...
)
```

The consequence is that the board remains fully interactive when the achievements panel is open. You can review what you completed while looking at what is still open. You can click a task on the board to edit it, drag cards between columns, or add a new task — all without closing the panel first.

This was a conscious decision about the user experience. Context switching between "what have I done" and "what is left to do" should feel fluid, not like entering and exiting a modal state. The drawer slides in alongside the board, not over it.

### Lazy Refresh

The `tick` store fires every 60 seconds to keep the board data current. The achievements callback listens to `tick`, but does nothing when the panel is closed:

```python
def refresh_achievements(opened_data, _tick, is_open):
    if not is_open:
        raise PreventUpdate
    conn = app_db()
    data = get_achievements(conn)
    ...
```

`PreventUpdate` is Dash's way of saying "I received the trigger but I have decided not to update anything." The database query never runs unless someone is actively looking at the panel. The 60-second tick is a no-op for this callback most of the time.

For a personal tool running on modest infrastructure, this matters less for performance than for correctness. You do not want background queries running against SQLite during a rapid sequence of task updates — the database is single-writer and you do not want to introduce contention.

---

## The Psychology

The design is consciously borrowed from habit-tracking applications. Duolingo's streak mechanic is the most visible version of this pattern: miss a day and you lose your streak, which creates an asymmetric loss aversion that motivates daily engagement. Whether that is the right psychology for a task board is debatable — I chose the strict version where a missed day resets the streak to zero, which some users find punishing.

The week count and time estimate serve a different purpose. They are accountability numbers. At the end of a Wednesday with 11 tasks done and 4.5 hours of estimated work, those numbers make the day feel productive in a way that an empty inbox does not. They are especially useful during periods where the backlog is growing faster than you can clear it — the board looks worse but the panel shows you are still moving.

The completion time on each row (`14:32`, `09:17`) was an addition I initially thought was noise. It turned out to be surprisingly useful. Seeing that you completed three tasks between 09:00 and 09:30 on a Tuesday tells you something about when you are most productive that no aggregate statistic captures.

---

## The Trade-offs, Honestly

The streak resets on a missed day. I considered a "longest recent streak" model — tracking streaks as intervals rather than a running counter from today — but decided against it. The strict model creates more motivation on days when you are tempted not to open the app. The softer model would feel more forgiving but would lose the urgency that makes streaks useful.

The time estimate relies on the `estimate_min` field that users set when creating tasks. If a task has no estimate, it contributes zero to the weekly total. Users who do not set estimates get an accurate task count but an underestimated time figure. This is documented nowhere in the UI because the correct response is to set estimates, not to special-case missing ones.

The drawer sits below the topbar (`top: 56px` in the drawer styles) because the topbar contains navigation controls you should always be able to reach. This is a CSS value that would need updating if the topbar height ever changed. It is a coupling that is invisible until it breaks.

---

## What the AI-Assisted Workflow Actually Looked Like

Five commits: service → component → callbacks → CSS → integration into `app.py`. Each is independently reviewable and was written in that order. The service was written first because it is the testable core. The component was written second to establish the HTML structure without worrying about data flow. The callbacks connected the two once both existed. CSS polished the visual output. The final integration commit added the topbar button and registered the callbacks in the app factory.

I wrote the streak logic myself — the algorithm for walking backward from today through the completion dates set — because it required reasoning about the edge case where today has no completions but yesterday does (a streak that started before today should still be counted). The AI implemented the grouping and sorting once the algorithm was established.

The `withOverlay=False` decision was mine. The AI's first implementation used the default overlay behaviour and I changed it after testing, because the overlay made the panel feel like an interruption rather than a companion.

---

## What This Unlocks

The achievements panel is infrastructure for a future gamification layer. The streak count is already there. The week count is already there. Future additions — milestones, badges, best-week comparisons — can be added to the service and rendered in the same panel without changing the callback or component architecture.

More importantly, it changes the emotional texture of using Stride. The board is no longer only a list of things that need doing. It is also a record of things that got done. That is not a trivial change for a personal productivity tool.

---

## Takeaway for Consultants

When you build a tool for yourself or your team, motivation mechanics are not features — they are load-bearing. A board that only shows what is left to do will be abandoned when the backlog grows. A board that also shows what got done will be used on the days when progress feels invisible.

The architecture lesson is simpler: keep your service layer pure. `achievements.py` has no Dash imports. It runs in a test, in a notebook, from a CLI. Every hour you spend enforcing that boundary pays dividends when you want to test, migrate, or extend the logic without touching the UI.
