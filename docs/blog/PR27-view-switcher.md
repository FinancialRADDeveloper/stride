# Day, Week, Month: Building a View Switcher Without Complicating the State Model

The rolling week view works well for daily planning. But there are moments where you want less context — just today, nothing else — and moments where you want more context — the whole month at a glance to see how load is distributed. PR #27 adds Day and Month views alongside the existing Week view.

The challenge with a view switcher is state management: week offset, current date, current view mode — these are three orthogonal dimensions of navigation state, and adding a third dimension without tangling the first two requires deliberate design.

---

## What We Built

**`dmc.SegmentedControl`** in the topbar with three options: Day, Week, Month. The selection writes to `store-view-mode`.

**Day view** — renders only today's column. No prev/next navigation. No week offset. Just today.

**Week view** — the existing rolling window (unchanged). Prev/Next navigation via `store-week-offset`.

**Month view** — a calendar grid showing all days in the current calendar month. Each cell shows the day number and a task count badge. Read-only — no drag-and-drop, no inline editing from month cells.

**Navigation resets** — switching to Day view resets `store-week-offset` to 0 (today). This prevents the confusing experience of switching to Day view while on an offset week and seeing a day from three weeks ago.

---

## The State Architecture

Before PR #27, navigation state was one store: `store-week-offset` (integer, 0 = current week).

After PR #27, navigation state is two stores:
- `store-view-mode` — string: `"day"`, `"week"`, or `"month"`
- `store-week-offset` — integer, unchanged in meaning

These two stores are independent. View mode is orthogonal to week offset: you can be in Week view at offset +2 (two weeks forward) and switch to Month view to see the current month without disturbing the week offset.

The board rendering callback reads both stores:

```python
@app.callback(
    Output("board-container", "children"),
    Input("store-tasks", "data"),
    Input("store-week-offset", "data"),
    Input("store-view-mode", "data"),
)
def refresh_board(tasks_data, week_offset, view_mode):
    conn = app_db()
    if view_mode == "day":
        return day_board(conn)
    elif view_mode == "month":
        return month_board(conn, week_offset)
    else:  # "week" is the default
        tasks = get_tasks_for_week(conn, week_offset)
        return board(tasks, week_offset)
```

The board callback is the single place where view mode and week offset combine. The stores themselves are independent.

---

## Why Two Stores Instead of One

An alternative design would encode both view mode and week offset in a single store:

```python
store-nav = {"mode": "week", "offset": 0}
```

This looks simpler — one store, two fields. The problems:

1. **Callbacks that only care about week offset have to destructure the combined store.** A callback that navigates prev/next in week view reads `store-nav["offset"]` and writes `{...store-nav, "offset": store-nav["offset"] + 1}`. This is more complex than reading and writing `store-week-offset` directly.

2. **The combined store creates spurious re-renders.** If week offset changes while in Month view, every callback watching `store-nav` fires — including callbacks that only care about view mode. With separate stores, `store-week-offset` changes do not trigger `store-view-mode` watchers.

3. **Future store consumers have mixed dependencies.** The auto-reload callback watches `store-view-mode` to determine whether to show the reload indicator prominently. With a combined store, it receives updates from week offset changes it does not need.

Separate stores for orthogonal concerns is the standard Dash architecture. The rule: if two pieces of state change independently and have independent consumers, they belong in separate stores.

---

## The Month View: Read-Only by Design

Month view renders a calendar grid. The decision to make it read-only was deliberate:

Month view is for planning and review, not task management. The use case: "I want to see how my workload is distributed across the month." This is a read operation — you see counts, you identify imbalances, you switch to Week or Day view to make changes.

Making month view interactive would require:
- Drag-and-drop between calendar cells (complex — month grid cells are not day columns)
- Task detail drawers accessible from calendar cells
- Composer integration on each cell
- Navigation to the week containing a clicked day

This is a significant implementation effort for features that the week and day views already provide. Month view as a read-only overview is 20% of the implementation effort and 80% of the use case value.

The decision is noted in the component's docstring: "Month view is intentionally read-only. For task operations, switch to Week or Day view."

---

## The Month Board Implementation

`_month_board()` generates a calendar grid for the current calendar month:

```python
def _month_board(conn: sqlite3.Connection, week_offset: int) -> html.Div:
    today = date.today()
    # Use week_offset to shift the month being viewed
    target_month = today + relativedelta(months=week_offset // 4)
    
    first_day = target_month.replace(day=1)
    last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
    
    days_in_month = [first_day + timedelta(days=i) for i in range(last_day.day)]
    
    # Get task counts per day
    day_counts = {}
    for day in days_in_month:
        tasks = get_tasks_for_day(conn, day.isoformat())
        day_counts[day] = len([t for t in tasks if not t.done])
    
    # Build calendar grid
    cells = []
    for day in days_in_month:
        count = day_counts.get(day, 0)
        is_today = day == today
        cells.append(html.Div(
            [html.Span(str(day.day)), html.Span(str(count) if count else "", className="count-badge")],
            className=f"month-cell {'today' if is_today else ''} {'has-tasks' if count else ''}"
        ))
    
    return html.Div(cells, className="month-grid")
```

The month grid uses CSS Grid with seven columns (Mon-Sun). `grid-column-start` offsets the first cell to start on the correct weekday. The grid is responsive — it wraps cleanly on mobile.

---

## Navigation in Month View

In Week view, Prev/Next navigates by week offset (one week backward/forward). In Month view, the same Prev/Next buttons navigate by month. The navigation callback reads `store-view-mode` to determine step size:

```python
@app.callback(
    Output("store-week-offset", "data"),
    Input("btn-prev", "n_clicks"),
    Input("btn-next", "n_clicks"),
    Input("btn-today", "n_clicks"),
    State("store-week-offset", "data"),
    State("store-view-mode", "data"),
    prevent_initial_call=True,
)
def navigate(prev, next_, today, offset, view_mode):
    ctx = dash.callback_context
    triggered = ctx.triggered_id
    step = 4 if view_mode == "month" else 1  # 4 weeks ≈ 1 month
    if triggered == "btn-prev":
        return offset - step
    elif triggered == "btn-next":
        return offset + step
    elif triggered == "btn-today":
        return 0
```

This is slightly inelegant — `4 weeks ≈ 1 month` is an approximation. February at offset +4 from a January Monday might show March. A proper calendar implementation would use `relativedelta(months=1)` from `dateutil`. The approximation is acceptable for the current use case and noted in a code comment.

---

## The Trade-offs, Honestly

The `4 weeks ≈ 1 month` approximation in month navigation is a known imprecision. Correct implementation requires converting the week offset to an absolute date, applying `relativedelta(months=±1)`, and converting back to a week offset. The added complexity was not justified for the initial implementation.

Day view has no navigation. There is only ever one "today." This makes the Prev/Next buttons non-functional in Day view — they are visually present but produce no visible change (they navigate the week offset, but day view ignores it). A visual disable on the buttons in Day view would be cleaner; it was not implemented.

Month view queries `get_tasks_for_day` for every day in the month — potentially 31 queries. For a personal tool with a fast SQLite database, this is imperceptible. For a large task database, a single `SELECT * WHERE day_key BETWEEN ? AND ?` query would be more efficient.

---

## What the AI-Assisted Workflow Actually Looked Like

The two-store architecture (separate stores for view mode and week offset) was mine — the reasoning about orthogonal concerns and independent consumers. The AI implemented the `_month_board()` function and the navigation step-size logic.

The month grid CSS (seven-column grid, weekday offset for first cell) was AI-generated from a specification. The visual design — today highlighted, task counts as badges, muted colours for days with no tasks — was specified and AI-implemented.

---

## What This Unlocks

Three planning perspectives: Day for focus, Week for execution, Month for review. Each view mode is appropriate for a different planning horizon. The transition between views is seamless — state is preserved, the board updates immediately, and switching back to Week view shows the same week as before.

---

## Takeaway for Consultants

Orthogonal concerns belong in separate stores. View mode and navigation offset are independent — they change independently and have independent consumers. A combined store would work but would introduce spurious re-renders and complex state management. The Dash architecture principle: one store per independent piece of state.

Read-only views are a valid design pattern. Not every component needs to support every interaction. Month view's read-only constraint makes it simpler to implement and clearly communicates its purpose — overview and review, not manipulation.

---

## LinkedIn Summary

Stride's view switcher adds Day and Month views without tangling the state model. Key design decision: two separate stores for view mode and week offset — orthogonal concerns, independent consumers, no spurious re-renders. Month view is deliberately read-only — it exists for load review and planning, not task operations. The navigation step-size logic adapts to view mode: 1 week in Week view, 4 weeks in Month view. Three views, one board component, zero duplicated state.
