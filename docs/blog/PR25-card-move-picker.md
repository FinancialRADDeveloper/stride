# Replacing a Bespoke Flyout With a Shared Modal: The Composition Win

The move-to flyout from PR #11 was a purpose-built UI component — a row of day-target buttons that appeared below each task card when the `→` button was clicked. It worked. It was limited: no calendar, no quick picks, no connection to the reschedule infrastructure built in PR #23.

PR #25 replaced the flyout with the shared reschedule modal. The same `dmc.Modal` that handles column bulk-reschedules now also handles single-task moves. The change demonstrates one of the most satisfying patterns in component-based UI development: you build something for one use case, discover a second use case that fits the same component with a minor extension, and the duplication you avoided pays dividends.

---

## What We Built

The per-card `→` move button previously opened a `html.Div` flyout rendered inline with the card. PR #25 replaces this with a call to the shared reschedule modal:

1. The `→` button callback now sets `store-reschedule-source` to a task-specific value instead of a day_key string
2. The reschedule modal callback reads the source and discriminates: if the source is a day_key string, bulk-move; if it is a task ID dictionary, single-move

The source discriminator format:
- **Column reschedule:** `store-reschedule-source = "2026-05-28"` (an ISO date string)
- **Card move:** `store-reschedule-source = {"task_id": 42}` (a dict with task_id)

The callback reads the source type:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Output("store-reschedule-source", "data", allow_duplicate=True),
    Input("btn-today", "n_clicks"),
    Input("btn-tomorrow", "n_clicks"),
    Input("btn-next-week", "n_clicks"),
    State("store-reschedule-source", "data"),
    prevent_initial_call=True,
)
def reschedule_quick(today_clicks, tomorrow_clicks, next_week_clicks, source):
    if not source:
        raise PreventUpdate
    target = _compute_target(dash.callback_context.triggered_id)
    conn = app_db()
    if isinstance(source, str):
        # Column bulk-reschedule
        bulk_reschedule(conn, from_day_key=source, to_day_key=target)
    elif isinstance(source, dict) and "task_id" in source:
        # Single task move
        move_task(conn, source["task_id"], target)
    return get_tasks_serialised(conn), None
```

The discriminator is a Python `isinstance` check. The source value carries enough information to determine the action — no separate mode store is required.

---

## Why This Is Better Than the Original Flyout

The original flyout had three limitations:

**Limited date options.** The flyout showed six buttons for the six visible column dates. If you wanted to move a task to a date outside the current view, you had to navigate the board and then find the task again. The modal's calendar picker handles arbitrary dates.

**Bespoke code.** The flyout was implemented entirely within the card component and its callbacks — distinct from the reschedule infrastructure in PR #23. Two codepaths for the same conceptual action (move a task to a different date).

**No quick picks.** Today, Tomorrow, and Next week were not available in the flyout — only the literal visible dates.

Replacing the flyout with the shared modal eliminates all three limitations at once. The card move button now has the same capabilities as the column reschedule button.

---

## The Source Discriminator Pattern

The `store-reschedule-source` discriminator is worth describing in detail because it is a pattern that appears whenever a shared component needs to behave differently based on what triggered it.

Two design options:

**Option A: Separate stores.** `store-column-reschedule-source` for columns, `store-card-move-source` for cards, `store-modal-open` for open/close state. Three stores, each with a clear single purpose. The modal watches all three and acts accordingly.

**Option B: Discriminator store.** One `store-reschedule-source` that carries different value types for different use cases. Null = closed. String = column reschedule. Dict = card move. One store, three states, clean.

Option A is more explicit but adds synchronisation complexity — all three stores need to be kept consistent when the modal closes. Option B is more compact but requires the callback to inspect the value type to determine the action.

I chose Option B because the discrimination logic is simple (isinstance check) and the alternative introduces three stores where one suffices. If the discrimination became more complex — three different use cases with overlapping value formats — Option A would be the right refactor. For two use cases with non-overlapping formats, Option B is cleaner.

---

## Removing the Flyout

The flyout code in `card.py` and its associated CSS was deleted. Deletion is important — it is easy to leave old code in place "in case we need it," which leaves technical debt and dead code that confuses future readers.

The old flyout callback (`show_move_flyout` in `board_cb.py`) was also removed. Its responsibility moved to the card move button opening the reschedule modal. The flyout's day-button callbacks (`move_to_day` pattern) were replaced by the reschedule modal's existing quick-pick and calendar callbacks.

Net lines changed: negative. The PR removed more code than it added. This is a win — fewer lines, more capability.

---

## The Trade-offs, Honestly

The isinstance discriminator is weakly typed. If a bug in a future PR sets `store-reschedule-source` to an unexpected value type, the callback falls through both branches and does nothing — no error, no feedback. This is acceptable because the discriminator values are set by two specific callbacks (`btn-reschedule` column button and `btn-move` card button) that have clearly defined output formats. The risk of unexpected value types is low.

The card's move button is now visually identical to the column's reschedule button. Users who learned "the `→` button opens a flyout" need to relearn "the `→` button opens the modal." This is acceptable for a personal tool where I am the only user. For a team tool, a migration period or in-app tooltip would smooth the transition.

---

## What the AI-Assisted Workflow Actually Looked Like

The discriminator pattern was my design — the insight that `store-reschedule-source` could carry different value types for different use cases, and that a Python isinstance check was the cleanest discriminator. The AI implemented the callback modification.

The flyout deletion was straightforward — removing a component from `card.py`, its CSS, and its callback. The AI was used to verify that no other parts of the codebase referenced the deleted component IDs.

The isinstance-based dispatch in the reschedule callback was AI-generated from a specification: "if source is a string, bulk_reschedule; if source is a dict with task_id, move_task."

---

## What This Unlocks

A single, powerful rescheduling interface for both column-level and card-level operations. The codebase has fewer components, fewer callbacks, and less CSS. Future rescheduling features — "move all tasks tagged with a category," "reschedule to a specific time block" — can be added by extending the source discriminator without adding new modal components.

---

## Takeaway for Consultants

When you build a component for one use case, ask yourself before shipping: what other use cases could this serve? If the answer is "another use case with a minor parametric change," build the extension immediately and remove the bespoke code it replaces. Composition beats duplication even when the duplication is small.

The discriminator pattern — one store, multiple value types, isinstance-based dispatch — is a clean alternative to multiple purpose-specific stores when the use cases are few and the value types are non-overlapping.

---

## LinkedIn Summary

PR #25 replaced Stride's bespoke card move flyout with the shared reschedule modal built in PR #23. The discriminator: `store-reschedule-source` carries a date string for column reschedules or `{task_id: N}` for single-task moves. One modal, two use cases, less code. Net lines changed: negative. Building the shared modal generically in PR #23 made this reuse cost thirty minutes of work rather than a new component from scratch.
