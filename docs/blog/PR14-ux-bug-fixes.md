# Three UX Bugs and What They Revealed About Dash's Callback Model

After Phase 3, Stride had a working board, a detail drawer with inline editing, and a move-to flyout. What it also had was three bugs that only became visible after using the app for a few days.

None of the three were architectural failures. They were each a consequence of one design choice in Dash's reactive model meeting one edge case the initial implementation had not anticipated. Fixing them required understanding why they happened, not just patching the symptom.

---

## What We Fixed

Three bugs, three root causes, three fixes:

**Bug 1: Category resets after saving another field.** Edit a task's title in the drawer. The category chip resets to the default value. Edit the description. The category resets again. Every time any other field saves, the category goes back to its default.

**Bug 2: Marking a task complete doesn't open the drawer.** The design intent: clicking the complete button on a card should mark the task done and open the drawer to show a completion state (a congratulatory message and the activity timeline showing "Marked done"). In practice, clicking complete marks the task done but the drawer does not open.

**Bug 3: Move-to flyout only shows future dates.** The flyout from PR #11 shows day buttons for the rest of the current week and the next week. If you need to move a task to yesterday — because you completed it then but forgot to record it — there is no way to do it from the flyout.

---

## Bug 1: Callback Race Conditions

The category chip is a `dmc.ChipGroup`. It renders based on the task data loaded when the drawer opens, stored in a local component `value` prop. When the title field blurs, the title-save callback fires, updates the task in the database, and writes the full task list back to `store-tasks`. The drawer-load callback then fires — because `store-tasks` changed — and repopulates all drawer fields, including the category chip.

But the category chip repopulation is reading from the database's stored value, not from whatever the user has currently selected. If the user has selected a different category but has not saved it yet (they were editing the title first), the repopulation overwrites their unsaved category selection.

The fix was callback ordering and store separation. Category changes now write immediately to `store-tasks` via their own blur-save callback — the same pattern as title and description. When the drawer-load callback fires and repopulates fields, the category is already saved, so the repopulation is reading the correct value.

The root cause: the assumption that "users edit one field at a time before saving." They do not. They open the drawer, change the category (no blur-save fires yet because they have not left the chip), edit the title (blur fires, title saves, drawer repopulates, category resets). The fix is to save every field on change, not just on blur, for fields that do not have natural "intermediate states" (category chips, segmented controls) — as opposed to text inputs where intermediate characters should not trigger saves.

---

## Bug 2: Separate Concerns in One User Action

Marking a task complete is one user action, but it requires two system actions: write `done=True` to the database, and open the drawer for that task. In Dash's callback model, these are two separate outputs — `store-tasks` (updated by `toggle_done`) and `store-selected` (set to the task ID to open the drawer).

The initial `toggle_done` callback wrote to `store-tasks` and returned. It did not write to `store-selected`. The drawer-open logic was entirely separate, triggered only by clicking the card body.

The fix: extend the `toggle_done` callback to also output to `store-selected`:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Output("store-selected", "data", allow_duplicate=True),
    Input({"type": "btn-done", "task_id": ALL}, "n_clicks"),
    State("store-selected", "data"),
    prevent_initial_call=True,
)
def toggle_done(n_clicks, selected_id):
    ctx = dash.callback_context
    if not any(n_clicks):
        raise PreventUpdate
    task_id = ctx.triggered_id["task_id"]
    conn = app_db()
    toggle_done_service(conn, task_id)
    return get_tasks_serialised(conn), task_id
```

The key insight: one user action can have multiple system consequences. Dash's callback model supports multiple `Output` targets in a single callback. This is the correct pattern when a user action should produce atomic changes across multiple stores.

---

## Bug 3: Past Dates Deliberately Excluded, Then Not

The move-to flyout in PR #11 only showed future dates. The reasoning at the time: you move tasks forward, not backward. Why would you move a task to a past date?

A day of using the board produced the answer: backdating. You completed a task yesterday but forgot to mark it done in Stride. You want to move it to yesterday's column and mark it complete there. You can't, because there are no past-date options in the flyout.

The fix was a one-parameter change: the flyout now shows a configurable window of dates in both directions. The default is 14 days backward and 14 days forward from today.

The lesson is worth stating plainly: your first assumption about how users will use a feature is a hypothesis, not a fact. "Users only move tasks forward" was a hypothesis. Using the app for one day falsified it. The fix is a parameter change and a window of dates. The original design was a premature constraint.

---

## The Deeper Pattern: Dash's Sharp Edges

All three bugs share a common thread. They are consequences of Dash's reactive model meeting assumptions that seemed reasonable at design time and proved wrong at use time.

The reactive model: callbacks fire when their `Input` values change. Multiple callbacks can update the same store if they use `allow_duplicate=True`. The order in which multiple triggered callbacks fire is not strictly guaranteed. When a user action triggers one callback (title save) that in turn triggers another (drawer reload), the intermediate state between those two callback executions can produce unexpected results.

Understanding this model is the difference between "Dash is confusing" and "Dash behaves exactly as specified." The spec is clear — callbacks are reactive, not imperative; state is in stores, not in components; a callback cannot call another callback directly. When bugs like these appear, they are almost always a sign that an assumption was made about what state would be present at callback execution time, and that assumption was wrong.

The mitigations:
- Save eagerly (every change, not just blur) for stateless UI controls
- Combine related outputs into a single callback when they represent one atomic user action
- Test every feature by simulating real usage patterns, not just happy paths

---

## What the AI-Assisted Workflow Actually Looked Like

Bug 1 (category reset) was diagnosed by adding `print` statements to the callback chain and observing the firing order. The fix was mine — change from blur-save to change-save for stateless controls. The AI implemented the callback adjustment.

Bug 2 (complete doesn't open drawer) was diagnosed immediately from the callback signature — `toggle_done` had no output to `store-selected`. Adding it was a two-line change. The reasoning ("one user action, two system consequences, one callback with two outputs") was mine.

Bug 3 (no past dates) was user feedback from using the app. The fix was trivial. The lesson — hypotheses about usage patterns need to be tested — was noted in the project reflection.

---

## What This Unlocks

Three bugs fixed, three edge cases documented, three patterns clarified. The CLAUDE.md file grew by three entries after this PR. The board was usable enough for daily use by the end of this PR.

---

## Takeaway for Consultants

Use your own tools. The three bugs in this PR were each discovered by using Stride for real work. Hypotheses about usage patterns — "users only move tasks forward," "users edit one field at a time" — are disproved by actual usage. Build the feature, use it for a day, then fix what breaks.

In Dash specifically: when a user action should produce atomic changes across multiple stores, combine them into one callback with multiple outputs. This is not a workaround; it is the correct pattern.

---

## LinkedIn Summary

PR #14 fixed three UX bugs that only became visible after daily use: category chips resetting on every save, completions not opening the drawer, and the move flyout blocking backdating. Each was a consequence of a reasonable assumption that real usage disproved. The diagnostic process for each took longer than the fix. Use your own tools — the best QA is genuine daily use.
