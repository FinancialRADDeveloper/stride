# Adding a Save Button to a Blur-Save UI: Belt-and-Suspenders UX

Blur-save was the original design for the detail drawer. Edit a field. Click away. It saves. No button required.

After a week of using Stride daily, the uncertainty became obvious: "Did that save? Did I click away far enough? Is the title I typed now in the database or did the focus not move?"

PR #22 added an explicit Save button to the drawer header. Not instead of blur-save — alongside it. Both mechanisms now work. This is the "belt-and-suspenders" pattern, and it is the right answer when user confidence in data persistence is a usability requirement.

---

## What We Built

A single `dmc.Button("Save", id="btn-save-task")` in the drawer header, positioned to the right of the close button. One new callback that fires on button click, reads all current field values from the drawer as `State` inputs, and calls `update_task` once with all field values:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Output("store-save-indicator", "data"),
    Input("btn-save-task", "n_clicks"),
    State("drawer-title", "value"),
    State("drawer-description", "value"),
    State("drawer-priority", "value"),
    State("drawer-category", "value"),
    State("drawer-size", "value"),
    State("drawer-estimate", "value"),
    State("store-selected", "data"),
    prevent_initial_call=True,
)
def save_task(n_clicks, title, description, priority, category, size, estimate, task_id):
    if not n_clicks or not task_id:
        raise PreventUpdate
    conn = app_db()
    update_task(conn, task_id, TaskUpdate(
        title=title,
        description=description,
        priority=priority,
        category=category,
        size=size,
        estimate_min=estimate,
    ))
    return get_tasks_serialised(conn), True
```

The `store-save-indicator` is a transient store that triggers a brief visual confirmation — the Save button changes to "Saved ✓" for two seconds, then resets. The reset is a clientside callback on the indicator store.

---

## Why Keep Blur-Save

Blur-save provides data persistence guarantees that an explicit Save button does not. If a user edits the title, then immediately closes the drawer (without clicking Save), blur-save ensures the title is in the database. An explicit-only save model would silently discard the change.

The combination:
- **Blur-save:** every field saves when focus leaves it — data is never lost by navigation
- **Save button:** explicit confirmation that all current field values are persisted — provides user confidence

Removing blur-save to add the Save button would have been wrong. The Save button alone requires the user to remember to click it before closing the drawer. Forget once, lose data. Blur-save is the safety net that makes the explicit Save button optional rather than required.

The `prevent_initial_call=True` on blur-save callbacks and `allow_duplicate=True` on the shared `store-tasks` output are unchanged from PR #11. The Save button callback uses the same flags. Multiple callbacks writing to `store-tasks` is the expected and correct state — Dash handles this cleanly with `allow_duplicate=True`.

---

## The State Pattern

The Save button callback reads field values as `State`, not `Input`. This distinction matters:

- `Input`: the callback fires when this value changes
- `State`: the callback reads this value but does not fire when it changes

The Save button callback fires on `Input("btn-save-task", "n_clicks")` — a click on the button. It reads all field values as `State` — they do not trigger the callback, they provide context to it when the trigger fires.

This is the standard Dash pattern for form submission: one trigger (the button click), multiple data readers (the field states). If field values were declared as `Input`, the callback would fire on every keystroke in every field — defeating the purpose of a Save button.

---

## The Visual Confirmation

The "Saved ✓" visual feedback addresses the second half of the uncertainty: "Did I click the button? Did it register?" A button that visually confirms its action closes the feedback loop.

The implementation uses `store-save-indicator` as a transient signal:

```python
# Python: sets store-save-indicator to True on save
# Clientside JS: watches store-save-indicator, updates button label, resets after 2 seconds
app.clientside_callback(
    """
    function(indicator) {
        if (!indicator) return window.dash_clientside.no_update;
        document.getElementById('btn-save-task').innerText = 'Saved ✓';
        setTimeout(function() {
            document.getElementById('btn-save-task').innerText = 'Save';
        }, 2000);
        return false;  // reset the indicator
    }
    """,
    Output("store-save-indicator", "data"),
    Input("store-save-indicator", "data"),
)
```

The clientside callback avoids a server round-trip for a purely visual state change. The 2-second timeout is a client-side `setTimeout` — again, no server involvement. The button label resets automatically.

The `return false` resets the indicator store to `False`. This is important: if the indicator stayed `True`, clicking Save a second time would not trigger the callback (the value would not change from `True` to `True`). Resetting to `False` after display means the next save click transitions from `False` to `True` and fires correctly.

---

## The Trade-offs, Honestly

A Save button alongside blur-save creates two ways to do the same thing. Some UX designers argue this is confusing — users do not know which mechanism to rely on. The counter-argument: belt-and-suspenders UX for data persistence is always better than either mechanism alone. Users who know about blur-save can ignore the Save button. Users who do not can click it. No data is lost either way.

The visual confirmation adds the clientside callback, a store, and a setTimeout. This is more complexity than the button alone. The alternative — a static button with no confirmation — leaves the user with the same uncertainty the button was meant to resolve.

The drawer now has two paths to persistence. The blur-save callbacks and the Save button callback both call `update_task`. Both write to `store-tasks`. If both fire in quick succession (user edits title, immediately clicks Save before the blur fires), they produce two `update_task` calls with the same data. The second call is a no-op. This is acceptable.

---

## What the AI-Assisted Workflow Actually Looked Like

The user feedback driving this PR was from genuine daily use — the uncertainty about whether blur-save had fired was real and recurring. The requirement was clear: add an explicit Save button that reads all current field values and saves them atomically.

The `State` vs `Input` pattern was specified: "button click is the Input, all field values are State." The AI generated the callback signature. The clientside confirmation was specified: "show 'Saved ✓' for 2 seconds, then reset." The AI generated the clientside callback.

The transient store pattern for the confirmation — write `True` on save, clientside resets it to `False` — was a collaborative design. The AI suggested the pattern; I verified it handles the "save twice" edge case correctly.

---

## What This Unlocks

User confidence in data persistence. The uncertainty that made PR #11's blur-save feel unreliable is resolved by explicit confirmation. Both mechanisms working in parallel means no data is lost and users always know their changes are saved.

---

## Takeaway for Consultants

Explicit Save buttons and auto-save are not mutually exclusive. The combination — auto-save on blur for data safety, explicit Save for user confidence — is the right model for any editing interface where data loss would be frustrating. Use `State` inputs for form field values in Save button callbacks. Visual confirmation (even a brief "Saved ✓") closes the user's mental feedback loop and eliminates the "did that work?" uncertainty.

---

## LinkedIn Summary

Blur-save in Stride's detail drawer was technically correct but psychologically unsatisfying — "Did that save?" was a recurring uncertainty. Adding an explicit Save button alongside (not instead of) blur-save resolved it. The pattern: belt-and-suspenders for data persistence. Blur-save prevents data loss; the explicit button provides confirmation. The `State` pattern in Dash — button click is the Input, field values are State — is the standard form submission model. A brief "Saved ✓" confirmation closes the feedback loop.
