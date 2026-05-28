# Building the Reschedule Modal: Quick Picks, Calendar Escape Hatch, and One Source of Truth

The move-to flyout from PR #11 worked. It was also limited: fixed future dates, no calendar, no bulk-column rescheduling. By the time PR #23 was written, Stride needed a more capable rescheduling mechanism — one that could handle both single-task moves and bulk column reschedules, with quick picks for common cases and a full calendar for edge cases.

The reschedule modal is the result. It is the cleanest Dash component in the project: a `dmc.Modal` with four quick-pick buttons and a date picker, driven by a single discriminator store. The same component handles two completely different use cases from the same UI surface.

---

## What We Built

**The "Reschedule all" button** — added to past-date column headers. If a column has past-date open tasks, a "Reschedule →" button appears. Clicking it opens the reschedule modal.

**The modal** — a `dmc.Modal` containing:
- "Today" button
- "Tomorrow" button
- "Next week" button (Monday of next week)
- A `dmc.DatePicker` for arbitrary date selection

**`store-reschedule-source`** — a `dcc.Store` that tracks what triggered the modal. Its value is either a `day_key` string (for column bulk-reschedule) or `null` (modal closed). The callback reads this to determine whether to move all tasks in a column or proceed with the selected date.

---

## The Modal Open/Close Pattern

Dash Mantine's `dmc.Modal` is controlled by its `opened` prop. True = visible, False = hidden. The standard Dash pattern for modal state:

```python
@app.callback(
    Output("reschedule-modal", "opened"),
    Input("store-reschedule-source", "data"),
)
def toggle_modal(source):
    return source is not None
```

The modal is open whenever `store-reschedule-source` is not null. Setting the store to null (when a button is clicked or the user clicks away) closes the modal. This is cleaner than a separate `store-modal-open` boolean — the source store serves double duty as open/close state and context.

The "Reschedule →" column button sets the store:

```python
@app.callback(
    Output("store-reschedule-source", "data"),
    Input({"type": "btn-reschedule", "day_key": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def open_reschedule_modal(n_clicks):
    ctx = dash.callback_context
    if not any(n_clicks):
        raise PreventUpdate
    day_key = ctx.triggered_id["day_key"]
    return day_key
```

The modal close button sets the store back to null:

```python
@app.callback(
    Output("store-reschedule-source", "data", allow_duplicate=True),
    Input("btn-modal-close", "n_clicks"),
    prevent_initial_call=True,
)
def close_modal(_):
    return None
```

---

## Quick Picks: The 90% Use Case First

The design premise: 90% of reschedule actions are "push to today or tomorrow." When a column of past tasks needs rescheduling, the most common action is "move everything to today" or "move everything to tomorrow."

The quick-pick buttons handle these cases in one click:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Output("store-reschedule-source", "data", allow_duplicate=True),
    Input("btn-today", "n_clicks"),
    State("store-reschedule-source", "data"),
    prevent_initial_call=True,
)
def reschedule_today(_, source):
    if not source:
        raise PreventUpdate
    conn = app_db()
    target = date.today().isoformat()
    bulk_reschedule(conn, from_day_key=source, to_day_key=target)
    return get_tasks_serialised(conn), None  # None closes the modal
```

One click on "Today" — all past tasks in the source column move to today, modal closes, board refreshes. Zero additional interaction required.

"Next week" calculates the coming Monday:

```python
def next_monday() -> date:
    today = date.today()
    days_ahead = 7 - today.weekday()  # weekday() 0=Monday, so 7-0=7 (next Monday)
    if today.weekday() == 0:
        days_ahead = 7  # if today is Monday, next Monday is 7 days away
    return today + timedelta(days=days_ahead)
```

---

## The Calendar: Escape Hatch for Edge Cases

The `dmc.DatePicker` component provides a full calendar for cases where today, tomorrow, and next Monday are all wrong — backdate to last week, reschedule to a specific upcoming date, etc.

The date picker fires a callback on value change:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Output("store-reschedule-source", "data", allow_duplicate=True),
    Input("date-picker", "value"),
    State("store-reschedule-source", "data"),
    prevent_initial_call=True,
)
def reschedule_calendar(date_value, source):
    if not date_value or not source:
        raise PreventUpdate
    conn = app_db()
    bulk_reschedule(conn, from_day_key=source, to_day_key=date_value)
    return get_tasks_serialised(conn), None
```

Selecting a date from the calendar is a single interaction — no "Apply" button required. The calendar selection is the confirmation. The modal closes automatically when the store is set to null.

---

## `bulk_reschedule` in the Service Layer

The service function moves all open (non-done, non-delegated) tasks from one day to another:

```python
def bulk_reschedule(conn: sqlite3.Connection, from_day_key: str, to_day_key: str) -> int:
    """Move all open tasks from from_day_key to to_day_key. Returns count moved."""
    tasks = [t for t in get_tasks_for_day(conn, from_day_key) if not t.done and not t.delegated]
    for task in tasks:
        move_task(conn, task.id, to_day_key)
    return len(tasks)
```

`move_task` writes a `task_events` row for each moved task. After a bulk reschedule, the activity timeline for each task shows the move event. The audit trail is complete.

The function returns the count of moved tasks. The modal could display "Moved 4 tasks to today" — a feature deferred because the simple success feedback (board refreshes, tasks appear in new column) is sufficient.

---

## The Trade-offs, Honestly

The date picker fires on every calendar navigation click, not just on final selection. If you use the calendar's month navigation arrows to browse before selecting a date, each arrow click fires `Input("date-picker", "value")` with the currently displayed month — which may not be the intended selection. The callback guard `if not date_value or not source: raise PreventUpdate` handles the case where `date_value` is null, but a month-navigation click may produce a non-null date value that the user did not intend to select.

`dmc.DatePicker` has a `type` prop that can be set to `"default"` (single date selection) to prevent this, but the "fire on navigation" behaviour is a known quirk of DMC date pickers that requires either careful prop configuration or a separate Apply button. The current implementation accepts the quirk because calendar navigation is an explicit user gesture unlikely to select a date unintentionally.

Quick picks are opinionated. "Next week" always means "next Monday." If today is Thursday, a user might expect "next week" to mean "next Thursday" — same day of the week, next week. The Monday interpretation is the standard calendar convention for "next week" in planning contexts. A tooltip on the button could clarify this; it was not added.

---

## What the AI-Assisted Workflow Actually Looked Like

The modal structure — quick picks + calendar, source store discriminator — was my design. The AI generated the Dash callback signatures and the `dmc.Modal` component tree from a specification.

The `next_monday()` function edge case (if today is Monday, next Monday is 7 days away, not 0) was caught during testing. The initial implementation returned `today` when called on Monday. The fix is one conditional.

The bulk reschedule service function was specified ("move all open, non-delegated tasks from one day to another, writing task_events for each") and AI-generated.

---

## What This Unlocks

A Monday morning ritual: open Stride, see the past-week columns with accumulated tasks, click "Reschedule →" on each past column, hit "Today" or "Tomorrow." All tasks are current in seconds. Without the bulk reschedule modal, this required opening each task individually and using the move flyout.

The modal is also the shared component that PR #25 reuses for single-task moves. Building it generically in PR #23 — with a source discriminator that can carry either a day_key or a task_id — made the PR #25 reuse straightforward.

---

## Takeaway for Consultants

Quick picks for common cases, calendar for edge cases. Design the 90% interaction first: what does the user need in one click? Then add the escape hatch for the 10% that needs more control. A modal with three buttons and a calendar is more powerful and less overwhelming than a full calendar presented immediately.

The source-store discriminator pattern — one store that carries both "is open?" state and "what is the context?" — is efficient and clean. A separate boolean `store-modal-open` adds a second store to synchronise. The discriminator serves both roles: not-null = open, value = context.

---

## LinkedIn Summary

The Stride reschedule modal shows three quick-pick buttons (Today, Tomorrow, Next week) for the 90% case and a full calendar escape hatch for the rest. The `store-reschedule-source` store serves double duty: null = modal closed, day_key string = modal open with context. One click to move an entire column of past tasks to today. Built generically enough that PR #25 reused the same component for single-task moves without modification.
