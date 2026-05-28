# From Blank Screen to Working Board: Building the Dash UI Layer

After four PRs establishing the prototype, scaffold, database, and service layer, the board still shows `html.H1("Stride")`. PR #10 changes that. By the end of this PR, there are day columns, task cards, navigation buttons, and a reactive state model that will hold for the rest of the project.

This is where Dash's reactive programming model either clicks or it does not. For me, it clicked here — and the pattern it established shaped every subsequent UI feature.

---

## What We Built

PR #10 contains six new files, each a focused layer:

- `stride/ui/board.py` — the `board()` function takes a flat task list and week offset, groups tasks by `day_key`, and returns the column layout
- `stride/ui/card.py` — the `task_card()` function renders a single task card with title, priority chip, estimate badge, and action buttons
- `stride/ui/topbar.py` — the `topbar()` layout with Prev/Next/Today navigation buttons and week label
- `stride/callbacks/board_cb.py` — the board refresh callback wired to `store-tasks` and `store-week-offset`
- `stride/services/seed.py` — `seed_if_empty()` creates sample tasks on first boot
- Updates to `stride/app.py` — registers all components and callbacks, calls `seed_if_empty()`

The visual result: a horizontal row of six day columns, each with a header showing the day name, date, open task count, and a capacity bar indicating how full the day is relative to an eight-hour estimate. Below each header is a stack of task cards.

---

## The Store-Driven Architecture

The most important decision in this PR is the state model. All application state lives in `dcc.Store` components in the layout:

- `store-tasks` — the flat list of all tasks for the current week, serialised as JSON
- `store-week-offset` — integer, 0 = current week, -1 = previous week, +1 = next week
- `store-selected` — the task ID of the currently selected card (null when none)
- `store-theme` — light/dark mode flag (added later)

The board callback signature captures this model:

```python
@app.callback(
    Output("board-container", "children"),
    Input("store-tasks", "data"),
    Input("store-week-offset", "data"),
)
def refresh_board(tasks_data, week_offset):
    conn = app_db()
    tasks = get_tasks_for_week(conn, week_offset)
    return board(tasks, week_offset)
```

When `store-week-offset` changes — because the user clicked Prev or Next — the board callback fires and re-renders all six columns. When `store-tasks` changes — because a task was created, moved, or completed — the board callback fires again. The board is always a pure function of its store inputs.

This is Dash's reactive model enforced as an architectural constraint. Callbacks do not call each other. They do not share mutable state. They react to store changes, produce UI updates, and exit.

---

## Why Pure Data Transforms in Callbacks

The board callback does exactly one thing: compute the board layout from the current task list and week offset. It does not update the week offset. It does not create tasks. It does not interact with any other store. It is a pure data transform.

This constraint is what makes Dash callbacks testable and predictable. A callback that both reads the week offset and writes to `store-tasks` creates a dependency cycle — Dash will warn about this and the behaviour is undefined. Keeping callbacks as pure transforms avoids the entire class of "callback fires unexpectedly" bugs.

The corollary: callbacks that write to stores should be triggered by UI interactions, not by other callbacks. The Prev button writes to `store-week-offset`. The board callback reads `store-week-offset`. The arrow goes from button click to store write to board refresh — never board refresh to board refresh.

---

## The `board()` Function

`board()` is the most-called function in the UI layer. It takes a flat list of `Task` objects and a week offset, groups tasks by `day_key`, and builds the column structure.

The day key format is `YYYY-MM-DD` — a string that sorts correctly, compares with equality, and can be constructed from any `datetime.date`. The `_day_label()` helper converts a `day_key` string to a human-readable header: "Mon 3 Jun", "Tue 4 Jun", etc. The capacity bar is computed from total `estimate_min` for tasks in that column divided by 480 (8 hours in minutes), capped at 100%.

The column layout is `html.Div` hierarchy — no Mantine yet. Pure HTML with CSS classes. The visual design matches the prototype from PR #1: narrow borders, cream background, task cards stacked vertically with spacing.

---

## Seed Data: Developer Ergonomics as a Feature

`seed_if_empty()` creates eight sample tasks across three days — a mix of priorities, some with estimates, some without — on first boot if the `tasks` table is empty. The check is fast: `SELECT COUNT(*) FROM tasks`.

The reason: a blank board is disorienting when testing. You open the app, see nothing, and immediately wonder whether the board is empty or whether there is a rendering bug. Seed data confirms the board is working. When you delete all the seed tasks, `seed_if_empty()` does not recreate them — the check is `if count == 0`, not a scheduled repopulation.

This is a developer ergonomics decision. The cost is near zero (a few INSERT statements that only run once). The benefit is a usable application from the first `uv run stride`.

---

## The Trade-offs, Honestly

Pure HTML without Mantine means the initial visual design is basic. No Mantine card borders, no Mantine badge styling, no smooth transitions. This was intentional — adding Mantine components before the layout structure is established would mix two concerns. Phase 3 introduces Mantine incrementally for the components that benefit most from it (the detail drawer, the modal, the date picker).

The board callback re-renders all six columns on every task change. If one task's title is updated, the entire board refreshes. For a task count in the dozens, this is imperceptible. At hundreds of tasks, it might produce visible flicker. The fix — partial re-renders using component IDs per column — was not implemented because the current scale does not require it. Premature optimisation avoided.

The `seed_if_empty()` call runs on every app startup. In production with a real database, the `COUNT(*)` query adds one database round-trip to cold start. At SQLite speeds, this is measured in microseconds.

---

## What the AI-Assisted Workflow Actually Looked Like

The six files in this PR were developed in sequence: service first (adding `get_tasks_for_week` to the existing service), then `board.py`, then `card.py`, then `topbar.py`, then callbacks, then integration in `app.py`. Each was a separate commit.

The `board()` function grouping logic — `itertools.groupby` after sorting by `day_key` — was AI-generated from a specification. The CSS class names and hierarchy followed the prototype from PR #1, which I provided as context. The callback wiring — Inputs, Outputs, state management — was specified and AI-generated, then reviewed for the pure-transform constraint.

The capacity bar logic (estimate minutes / 480, capped at 100%) was my calculation, AI-implemented. The colour transitions from green to amber to red were specified as CSS `hsl()` values.

---

## What This Unlocks

A working board with real data is the foundation for every subsequent interaction. PR #11 (the detail drawer) requires clickable cards — those exist now. PR #13 (drag and drop) requires `data-task-id` attributes on cards and `data-drop-day` attributes on columns — both are added here. PR #23 (the reschedule modal) requires the "Reschedule →" button on past columns — the column component is defined here.

More broadly, the store-driven architecture established in this PR is the pattern every callback in the project follows. Every new feature that modifies state writes to a store. Every feature that reads state reads from a store. The board is always a function of its stores.

---

## Takeaway for Consultants

Dash's reactive model is powerful when you commit to it fully. Treat callbacks as pure data transforms: they read from stores, compute outputs, and write to stores. They do not call each other. They do not share mutable state. The moment a callback tries to do two things — read data and update navigation — it becomes harder to reason about and easier to break.

Seed data is not a testing shortcut. It is documentation that the board renders correctly on first boot, accessible to any developer who clones the repository.

---

## LinkedIn Summary

PR #10 turned a blank Dash screen into a working day-lane task board. The architectural commitment: all state in `dcc.Store` stores, all callbacks as pure data transforms, no callback calling another callback. This pattern held for 23 more PRs without modification. The board callback is 12 lines. The service function it calls is 15. The clarity comes from the constraint.
