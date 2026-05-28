# Drag-and-Drop in Dash: Bridging Vanilla JS Into a React-Managed Page

The board could display tasks and the drawer could edit them, but tasks still had to be moved by clicking the `→` flyout button. Drag-and-drop was the next feature — and building it required bridging two different event systems.

PR #13 implemented the first working DnD. It worked for most of the project's development. Then PR #29 fixed the edge case that React 18 introduced. Together they tell the full story. This article covers the first implementation; the React 18 fix is covered separately.

---

## What We Built

A vanilla JavaScript drag-and-drop system that communicates with Python via a Dash store bridge:

- `stride/assets/dnd.js` — registers drag event listeners at `document` level
- `store-dnd-drop` — a `dcc.Store` that receives drop events from JS
- A Python callback in `board_cb.py` that reads `store-dnd-drop` and calls `move_task`

The UX: pick up a card, see a drag ghost, drag across day columns (each highlights on hover), release over a target column, watch the card appear in the new column.

---

## Why Vanilla JS Instead of a DnD Library

Dash is built on React. There are excellent React DnD libraries — `react-dnd`, `@dnd-kit/core`, `dnd-kit` — that provide rich drag-and-drop with accessibility support, keyboard navigation, and smooth animations.

The problem: these are React libraries. To use them in Dash, you would need to write a Dash custom component — a React component registered with Dash's component system, compiled via `npm`, published as a Python package. This is possible and some Dash extension authors have done it. It is also a significant investment: setting up a Node.js build environment, writing JSX, managing React version compatibility, maintaining a separate package.

Stride's DnD requirements are modest: pick up a card, drop it on a column. No sorting within a column, no multi-card selection, no animated reordering. For these requirements, HTML5 Drag and Drop API is sufficient and vanilla JS is the right tool.

---

## The Event Bridge

Dash 2.9 introduced `window.dash_clientside.set_props` — a JavaScript API that writes directly to a component's properties without a round-trip to the server. This is the mechanism that makes the vanilla JS DnD bridge work.

```js
document.addEventListener('drop', function (e) {
    e.preventDefault();
    var toDay = e.currentTarget.getAttribute('data-drop-day');
    if (!toDay || !dragging) return;
    window.dash_clientside.set_props('store-dnd-drop', {
        data: { task_id: dragging, to_day_key: toDay, ts: Date.now() }
    });
    dragging = null;
}, false);
```

`set_props` writes `{ task_id, to_day_key, ts }` into the `store-dnd-drop` store. The Python callback watching that store fires:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Input("store-dnd-drop", "data"),
    prevent_initial_call=True,
)
def handle_dnd_drop(drop_data):
    if not drop_data:
        raise PreventUpdate
    conn = app_db()
    move_task(conn, drop_data["task_id"], drop_data["to_day_key"])
    return get_tasks_serialised(conn)
```

The `ts` field in the drop data is a `Date.now()` timestamp. Its purpose is deduplication: Dash only fires a callback when a store's value changes. If you drop a card back onto the same column it was already in, the `{ task_id, to_day_key }` payload is identical to the last drop and the callback does not fire. The `ts` field guarantees a different value on each drop.

---

## The Data Attributes

Cards carry `data-task-id` attributes:

```python
html.Div(
    ...,
    **{"data-task-id": str(task.id)},
    draggable="true",
    className="task-card",
)
```

Columns carry `data-drop-day` attributes:

```python
html.Div(
    ...,
    **{"data-drop-day": day_key},
    className="day-column",
)
```

The JS event handlers read these attributes to determine what is being dragged and where it is being dropped. The `dragging` variable in module scope is set to the `data-task-id` on `dragstart` and cleared on `dragend` and `drop`.

Data attributes on generated Dash components is the standard pattern for bridging Python-generated layouts to JavaScript. The alternative — maintaining a JS-side map of component IDs — is fragile because Dash generates component IDs dynamically and can reuse them after re-renders.

---

## Event Delegation

All five event listeners are registered at `document` level, not on individual elements:

```js
document.addEventListener('dragstart', handler, false);
document.addEventListener('dragover', handler, false);
document.addEventListener('drop', handler, false);
document.addEventListener('dragend', handler, false);
document.addEventListener('dragleave', handler, false);
```

Event delegation means one set of listeners handles all cards and all columns, regardless of how many there are or how many times Dash re-renders the board. If Dash re-renders the board (because a task was added), the card elements are replaced with new DOM nodes — but the document-level listeners continue to work because they catch events from any element via bubbling.

The alternative — adding individual `addEventListener` calls to each card and column element — would break on every board re-render, because the old elements (with their listeners) would be discarded and the new elements would have no listeners.

---

## The `dragover` Prevention Pattern

A critical detail in HTML5 DnD: the browser only fires `drop` on an element if `dragover` has called `e.preventDefault()` on that element for every drag frame. Without this, the browser treats the element as non-droppable and the ghost snaps back on release.

The `dragover` handler:

```js
document.addEventListener('dragover', function (e) {
    if (!dragging) return;
    if (!e.target.closest('[data-drop-day]')) return;
    e.preventDefault();
    // highlight the column
    e.target.closest('[data-drop-day]').classList.add('drag-over');
}, false);
```

The double guard — check `dragging` is set, check the hover target has `data-drop-day` — means `preventDefault()` is only called over valid drop targets. Hovering over the topbar or empty areas of the page does not trigger `preventDefault`, so those areas correctly reject drops.

---

## What Broke (and the React 18 Sequel)

The initial implementation used `false` (bubble phase) for all listeners. This worked correctly during initial development. After other PRs were merged and the React version Dash shipped moved to React 18, the drag ghost appeared on pickup but drops did nothing. The `dragging` variable was never being set, because the `dragstart` listener was never firing.

The root cause — React 18's event delegation change from `document` to the React root element — and the fix (switching all listeners to capture phase, `true` as the third argument) are the subject of the existing blog post #01. This article covers the original implementation; the fix is documented there.

---

## The Trade-offs, Honestly

HTML5 DnD has known accessibility gaps. There is no keyboard navigation for dragging — users relying on keyboard input cannot move cards via DnD. The move-to flyout (and later the reschedule modal) provide keyboard-accessible alternatives, which means DnD is an ergonomic enhancement rather than the only mechanism.

The `dragging` module-scope variable creates a potential issue if two drags happen simultaneously — but browsers do not allow two simultaneous drag gestures, so this is not a real problem.

The `ts` field deduplication guard is a workaround for Dash's change-detection semantics. It is the correct solution given those semantics, but it is worth knowing that dropping a card onto its current column still sends a `move_task` call to the server (because the `ts` changed), which does a no-op database update. Not a problem in practice.

---

## What the AI-Assisted Workflow Actually Looked Like

The DnD architecture — document-level listeners, `set_props` bridge, `store-dnd-drop` consumer — was my design. The AI implemented the JavaScript event handlers and the Python callback from a specification. The `ts` deduplication issue was discovered during testing and the fix (`Date.now()` in the payload) was AI-suggested once the problem was described.

The CLAUDE.md note after this PR: "DnD bridge: `store-dnd-drop` receives `{task_id, to_day_key, ts}`. JS uses `window.dash_clientside.set_props`. Always include `ts: Date.now()` to avoid deduplication killing drops to the same column."

---

## What This Unlocks

Drag-and-drop makes the board feel fluid. Combined with the move-to flyout (for precise date selection) and later the reschedule modal, tasks can be repositioned quickly from any interface. The board moves from "a display you can edit" to "a surface you can manipulate."

---

## Takeaway for Consultants

When bridging vanilla JS into a React-managed page, event delegation at `document` level is the correct approach — it survives re-renders that replace individual DOM nodes. The `data-attribute` pattern for connecting JS to Python-generated layouts is reliable and simple. And always include a deduplication guard in your store payloads: `Date.now()` costs nothing and prevents the "why didn't that fire?" debugging session.

---

## LinkedIn Summary

Drag-and-drop in Stride uses vanilla HTML5 DnD + a `dcc.Store` bridge — no React DnD library, no custom Dash component. One `set_props` call from JS writes to a store; Python handles the database update. Event delegation at document level means the listeners survive board re-renders. The `ts: Date.now()` deduplication guard prevents Dash from swallowing drops onto the same column. The full React 18 sequel is in a companion post.
