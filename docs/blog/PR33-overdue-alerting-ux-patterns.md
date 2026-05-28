# Making Overdue Debt Impossible to Ignore: UX Patterns for Task Boards

There is a failure mode specific to calendar-week task boards: you open the app on a Thursday, see a manageable list of tasks for this week, and feel reasonably in control. What you are not seeing is the three tasks that slid off the left edge of the view window two Fridays ago and have been quietly ageing in the dark ever since.

The board is not lying to you. It is showing you exactly what you asked for — this week. But the design has a blind spot, and the blind spot compounds. Every week you do not notice the overflow, the overdue count grows. By the time you scroll back and find it, you have missed something that mattered.

PR #33 closes that blind spot.

---

## The Problem with Scroll-to-Discover

Stride's board renders a rolling window of days — today and the days immediately around it. Columns for past days with incomplete tasks already carry visual weight via a subtle left-border accent. That is enough signal when the task is one day overdue and still on screen. It is no signal at all when the task is three weeks old and off the left edge of the viewport.

The underlying issue is that overdue debt is ambient. It does not announce itself. A task does not send you a notification because it missed its day; it just sits there, still in state `pending`, day key no longer in the visible window. If the interface does not actively surface it, you will miss it.

The design goal for this feature was simple: make the total overdue count impossible to miss on every visit to the board, regardless of where your current view window is positioned, and make recovery — jumping to the oldest overdue work — a single interaction.

---

## What We Built

Three visual layers, each carrying a distinct message:

A past-day column that contains incomplete tasks gets an amber left-border accent. This was already in place for the current view window. It remains unchanged — the column-level signal is still appropriate when the work is close.

Each such column header now also shows a `⚠ N overdue` badge directly in the header row. The badge answers "how many in this column?" without requiring you to count cards.

The new element is a topbar amber pill — always visible, positioned in the application header — showing the total overdue count across all history, not just the current view. When the count is zero, the pill sets `display: none` and disappears entirely. When there is anything overdue, the pill is there, in amber, with a number. Clicking it jumps the board to the week containing the oldest overdue task.

The interaction model is deliberate: the pill tells you *how many*, the click takes you *where*. No modal. No confirmation dialog. No secondary screen. One piece of ambient information, one action to act on it.

---

## The Architectural Decisions

### A Separate Store for Global State

The most significant decision was introducing a dedicated `store-overdue` rather than deriving the count from the existing `store-tasks`.

`store-tasks` is windowed. It holds the tasks for the currently visible day range — roughly six to seven days. Deriving an overdue count from it would only count overdue tasks that happen to be in the current view, which is exactly the blind spot we are trying to fix.

The overdue store runs a separate query:

```python
def get_overdue_summary(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) AS n, MIN(day_key) AS oldest "
        "FROM tasks WHERE status = 'pending' AND day_key < ?",
        (today_key(),),
    ).fetchone()
    return {"count": row["n"], "oldest_day": row["oldest"]}
```

`COUNT(*)` plus `MIN(day_key)` in a single pass. At SQLite scale on a personal task board, this executes in microseconds. The query is global — it scans all history — but there is no window filter. That is the point.

Separating this concern keeps `store-tasks` doing what it does well (fast, windowed rendering data) and gives the overdue pill its own authoritative data source.

### Dual Trigger

The overdue store refreshes on two signals: the 60-second application tick, and any change to `store-tasks`.

The tick ensures the pill stays accurate over time. The `store-tasks` trigger ensures immediate feedback when you mark a task complete. Without it, you would watch the task card disappear from the board and wait up to sixty seconds to see the pill count drop. That lag is long enough to feel broken.

The pattern is a standard Dash multi-input callback — both signals in the `Input` list, the callback runs on whichever fires first. The implementation is straightforward; the decision to include both triggers is the thing that makes the UX feel responsive.

### Service-First Architecture

The SQL lives in `stride/services/tasks.py`. The callback that populates `store-overdue` imports from the service and does nothing else substantive — it gets a connection, calls the service function, returns the result. This is the same pattern used throughout Stride: business logic in a file with zero Dash imports, testable in isolation, callable from anywhere.

### CSS Variables and the Zero-State

All amber colours in the feature reference a single `--amber` CSS custom property already defined in Stride's theme. The border accent, the badge, the pill — all inherit from the same variable. A theme change propagates automatically.

The zero-state behaviour is worth noting explicitly. The pill element is always in the DOM. When the count is zero, the callback sets `display: none`. When the count is non-zero, it sets `display: inline-flex`. This avoids layout shifts from components appearing and disappearing, while keeping the DOM clean and predictable. There is no conditional rendering, no component mounting and unmounting — the pill is always there, just sometimes invisible.

---

## Commit Discipline

The feature landed in five commits:

```
service: add get_overdue_summary query to tasks service
board: amber column accent and per-column overdue badge
topbar: overdue pill component — amber, zero-state hidden
callbacks: wire store-overdue with tick + store-tasks dual trigger
css: overdue pill and badge styles via --amber variable
```

Service first, because it is the testable core. Board component second, because the column accent and badge are independent of the topbar. Topbar component third. Callbacks fourth, once both component targets existed. CSS last.

Each commit is independently reviewable. A reviewer can evaluate the SQL in the service commit without knowing what the pill looks like. They can evaluate the callback trigger logic without knowing anything about the component structure. This discipline requires resisting the temptation to commit a working blob of code simply because it works — working is not the same as reviewable.

---

## The Principle

The broader lesson here is about what ambient information should cost the user. The overdue count, once it exists, should require zero effort to notice. Not a notification, not a badge you have to navigate to, not a setting you have to enable — a number, always visible, in the place you already look when you open the app.

The one-click recovery mechanic follows from the same principle. If seeing the debt is zero effort, acting on it should be as close to zero effort as possible. The pill gives you the count; the click positions the view. You are now looking at the oldest overdue work and can start clearing it.

The design is not clever. That is the point. Clever interaction design usually means the user has to learn something. This interaction design means they never have to wonder where their stale tasks went.

---

## Takeaway for Consultants

A feature that surfaces ambient system state — debt, failures, drift from intent — is almost always higher leverage than a feature that adds a new workflow. Users can work around missing workflows. They cannot work around information they never see.

If you are building a productivity tool, ask which parts of its state are invisible by default. The answer is usually more than you expect, and the fix is usually simpler than you fear: one query, one badge, one click.
