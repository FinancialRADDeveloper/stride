# Building the Detail Drawer: Inline Editing, Move Flyout, and Activity Timeline

The board from PR #10 shows tasks. PR #11 makes them editable. Clicking a card opens a right-side drawer where you can edit every field, see the task's history, and move it to another day. This is the feature that makes Stride feel like a real tool rather than a read-only display.

It is also the PR where Dash Mantine Components entered the project, where the `task_events` log paid its first dividend, and where I discovered the most common pitfall in Dash callback design.

---

## What We Built

Three features in this PR, each dependent on the previous:

**1. The detail drawer.** Clicking a task card sets `store-selected` to the task ID. A `dmc.Drawer` component watches `store-selected` and slides in from the right, loaded with the full task data: title (text input), description (textarea), priority (segmented control), category (chip group), size (segmented control), estimate (number input).

**2. Blur-save.** Every field in the drawer saves on blur — when you click away from the input or tab to the next field, the value writes to the database via `update_task`. No Save button in this PR (added in PR #22 after user feedback).

**3. The activity timeline.** Below the edit fields, a chronological list of `task_events` entries: "Created", "Moved from Mon 2 Jun to Tue 3 Jun", "Marked done", "Edited: title". Timestamps shown in `HH:MM` format. This uses the append-only event log built into the service layer from PR #6 — zero additional work to display it.

**4. Move-to flyout.** Each task card has a `→` button. Clicking it reveals a row of day-target buttons. Clicking a day target calls `move_task` via a callback and closes the flyout.

---

## Introducing Dash Mantine Components

The drawer is the first component in Stride that uses DMC. The choice to introduce Mantine here rather than earlier was intentional. DMC brings:

- A complete visual component library (buttons, inputs, badges, modals, drawers, date pickers) that is consistent with Mantine's design system
- Dark mode support via `dmc.MantineProvider`'s `forceColorScheme` prop
- Animation and transition support (the drawer slides in with a smooth animation)

But DMC also adds complexity: the `dmc.MantineProvider` must wrap the entire layout, every component import must be explicit, and some DMC components have slightly different prop names than their plain HTML counterparts.

The incremental adoption strategy — DMC for the drawer first, then for other components as they are added — meant the board layout was not disrupted. Cards stayed as `html.Div` elements until their styling needed upgrading. The drawer got DMC styling from the start because its visual character (the slide-in animation, the header with close button) is exactly what DMC provides and hard to replicate with plain HTML.

---

## Blur-Save: The UX Decision That Generated Feedback

Blur-save means the input saves when it loses focus. You type a new title, tab away, and the title is saved. There is no Save button. The pattern is familiar from Google Docs and Notion.

The implementation uses Dash's `Input(..., "value")` with `allow_duplicate=True` on the task store output. Each field has its own callback:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Input("drawer-title", "value"),
    State("store-selected", "data"),
    prevent_initial_call=True,
)
def save_title(title, selected_id):
    if not selected_id or title is None:
        raise PreventUpdate
    conn = app_db()
    update_task(conn, selected_id, TaskUpdate(title=title))
    return get_tasks_serialised(conn)
```

`prevent_initial_call=True` prevents the callback from firing when the drawer first opens and populates the field. `allow_duplicate=True` allows multiple callbacks to write to `store-tasks` — without it, Dash raises an error because two callbacks compete on the same output.

The feedback after using this for a week: blur-save is not obviously "saved." Users (me, in this context) sometimes closed the drawer and were not sure whether the last field had saved. This drove PR #22 — adding an explicit Save button — while keeping blur-save as a backup to prevent data loss on navigation.

---

## The `allow_duplicate=True` Discovery

Dash's callback model has a rule: each `Output` can only be written by one `Input` trigger per callback. If you have five blur-save callbacks, each writing to `store-tasks`, Dash raises a `DuplicateCallback` error — five callbacks competing on the same output.

The fix is `allow_duplicate=True` on every `Output("store-tasks", "data")` except the first registration. This tells Dash "I know multiple callbacks write this store; that is intentional."

The accompanying rule: every callback that writes to a shared store must use `prevent_initial_call=True`. Without it, all five callbacks fire on app startup to "initialise" the store — which is unnecessary and causes a cascade of database reads.

These two flags together — `allow_duplicate=True` and `prevent_initial_call=True` — are the standard pattern for every mutation callback in Stride.

---

## The Activity Timeline: Free Dividends

The timeline in the drawer bottom is generated from `task_events`. The query is a simple `ORDER BY created_at ASC` on rows for the current task ID. The result is rendered as a list of `html.Li` elements with formatted timestamps.

What makes this notable is what it cost: nothing. The events were written by the service layer in PR #6 as a design decision, before any UI for them existed. By the time the drawer was built, three weeks of task events were already in the database.

This is the compound interest of append-only logging. You write events at mutation time because it is cheap. You display them in the drawer because the data is already there. Every subsequent feature that needs history — the achievements panel in PR #31 — also gets it for free.

---

## Move-to Flyout

The `→` button on each card opens a row of day-target buttons positioned below the card. Clicking a day target calls `move_task` via a Python callback, updates the board, and closes the flyout.

The flyout is rendered in the card component as a hidden `html.Div` with `style={"display": "none"}`. A clientside callback toggles visibility on button click. This avoids a server round-trip just to show the flyout — the state toggle is local to the browser.

One notable bug: when the flyout showed future dates only, backdate moves were impossible. Fixed in PR #14 to include dates in a two-week window in both directions. The "past dates" restriction made sense as a first implementation assumption and was wrong immediately.

---

## The Trade-offs, Honestly

Blur-save creates a UX ambiguity — is this saved? — that a Save button resolves. The choice to start with blur-save was the right call: it is faster to use and keeps the drawer clean. The save button addition (PR #22) proved that the right answer was both, not one or the other.

The move-to flyout was replaced in PR #25 with the reschedule modal — a more powerful, reusable component. The flyout worked, but it was bespoke code for a single interaction that the modal generalised. Incremental replacement is the right strategy: build the simple version first, replace it when you build something better.

---

## What the AI-Assisted Workflow Actually Looked Like

This PR's five commits are: DMC drawer component, title/description blur-save callbacks, priority/category/size callbacks, activity timeline, and move-to flyout. Each was developed and committed in sequence.

The `allow_duplicate=True` issue was discovered during development — the first attempt to register five blur-save callbacks produced a Dash `DuplicateCallback` error. The fix was AI-suggested once the error message was provided. The explanation — "Dash only allows one callback per output, use `allow_duplicate=True` for intentional multi-writer stores" — was then committed to CLAUDE.md for future reference.

---

## What This Unlocks

A working drawer means every task in the board is editable in-place. The `task_events` timeline is live. The move-to flyout lets you reschedule from the card. This is the feature set that makes daily use of Stride possible — not just a board to look at, but a tool to interact with.

---

## Takeaway for Consultants

Dash's `allow_duplicate=True` + `prevent_initial_call=True` is the pattern for any application where multiple user interactions update the same piece of state. Learn it once, apply it everywhere. The error message when you get it wrong is clear; the fix is two flags.

The deeper lesson: write your audit trail at mutation time. The activity timeline cost zero additional implementation effort because the events were already in the database from week one. Retrofit is possible but always lossy — you cannot reconstruct history from state snapshots that were never recorded.

---

## LinkedIn Summary

PR #11 introduced the detail drawer — inline editing with blur-save, an activity timeline built from the append-only event log, and a move-to flyout. The implementation unlocked Dash's `allow_duplicate=True` pattern for multi-writer stores. The timeline was free: three weeks of events were already in the database before any UI existed. That is the compound interest of designing for audit at mutation time.
