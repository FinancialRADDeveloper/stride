# Right-Click Context Menu: Event Delegation, Vanilla JS, and the Z-Index Wars

Task cards in Stride have action buttons: complete, move, delegated toggle. These are visible, accessible, always-on controls. But there is a class of less-frequent actions — delete, a future "duplicate," "copy link" — that are better surfaced as secondary actions behind a right-click, not cluttering the card with additional buttons.

PR #28 added a right-click context menu on task cards. It is pure vanilla JavaScript — no DMC, no Dash component, no Python for the menu itself. The menu appears, the user clicks an item, a store is written, Python handles the consequence.

---

## What We Built

- A CSS-positioned `<div class="ctx-menu">` injected into the document body by JavaScript on right-click
- Menu items: Edit (opens drawer), Move (opens date picker modal), Delete (writes to `store-ctx-delete`)
- Dismiss on outside click or Escape key
- `store-ctx-delete` store: a `dcc.Store` that Python watches — when a task ID appears in it, `delete_task` is called and the board refreshes
- Z-index layering so the menu appears above all other UI elements

---

## Why Vanilla JS Instead of `dmc.Menu`

Dash Mantine Components includes a `dmc.Menu` component with full keyboard navigation, accessibility attributes, and sub-menu support. It is the "right" way to add a menu in a Mantine-driven Dash application.

The problem: `dmc.Menu` requires wiring a separate `dmc.MenuTarget` and `dmc.MenuDropdown` into each task card in the Dash layout. With a dynamic card count — the board can have anywhere from zero to fifty cards visible — each card needs its own menu component registered in the layout, with its own callback wiring.

Dynamic component counts in Dash are handled with pattern-matching callbacks (`ALL`, `MATCH`, `ALLSMALLER`). This is functional but adds complexity: each card's menu target needs a pattern-matched ID, the dropdown items need pattern-matched IDs, and the callback needs to extract the task ID from the triggered component's ID dictionary.

This is the correct approach for a well-maintained Dash component library. It is overkill for a context menu that needs to:
1. Appear at the cursor position on right-click
2. Offer three options
3. Write a store value on selection
4. Dismiss on outside click or Escape

Vanilla JavaScript handles all of this with less complexity than the DMC pattern-matching approach, without adding any Dash component registration overhead.

---

## The Event Delegation Pattern

The right-click listener is registered at `document` level, not on individual cards:

```js
document.addEventListener('contextmenu', function (e) {
    var card = e.target.closest('.task-card');
    if (!card) return;
    e.preventDefault();
    var taskId = card.getAttribute('data-task-id');
    showContextMenu(e.clientX, e.clientY, taskId);
}, true);  // capture phase, for React 18 compatibility
```

`e.target.closest('.task-card')` walks up the DOM tree from the click target to find the nearest `.task-card` ancestor. If the user right-clicks on the priority badge inside a card, `closest('.task-card')` still finds the card. If they right-click on empty board space, `closest('.task-card')` returns null and the handler exits without showing the menu.

This is the same event delegation pattern as the DnD implementation. One listener at document level, capturing events from any number of cards. Adding or removing cards does not require re-registering listeners.

The `true` (capture phase) argument is, again, the React 18 requirement from PR #29's lesson.

---

## The Menu Implementation

```js
function showContextMenu(x, y, taskId) {
    dismissContextMenu();  // remove any existing menu
    
    var menu = document.createElement('div');
    menu.className = 'ctx-menu';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.setAttribute('data-task-id', taskId);
    
    menu.innerHTML = [
        '<div class="ctx-item" data-action="edit">Edit</div>',
        '<div class="ctx-item" data-action="move">Move...</div>',
        '<div class="ctx-item ctx-item--danger" data-action="delete">Delete</div>',
    ].join('');
    
    document.body.appendChild(menu);
}
```

The menu is a raw `div` appended directly to `document.body`. Positioning at `(x, y)` from `e.clientX, e.clientY` places it at the cursor position. The `position: fixed` CSS ensures it stays in place if the board scrolls.

Item clicks are delegated from the menu element:

```js
document.addEventListener('click', function (e) {
    var item = e.target.closest('.ctx-item');
    if (!item) {
        dismissContextMenu();
        return;
    }
    var menu = item.closest('.ctx-menu');
    var taskId = menu.getAttribute('data-task-id');
    var action = item.getAttribute('data-action');
    
    if (action === 'edit') {
        window.dash_clientside.set_props('store-selected', { data: parseInt(taskId) });
    } else if (action === 'move') {
        window.dash_clientside.set_props('store-reschedule-source', { data: { task_id: parseInt(taskId) } });
    } else if (action === 'delete') {
        window.dash_clientside.set_props('store-ctx-delete', { data: { task_id: parseInt(taskId), ts: Date.now() } });
    }
    
    dismissContextMenu();
}, false);
```

Each action writes to a store via `window.dash_clientside.set_props`. Edit writes to `store-selected` (opens the drawer). Move writes to `store-reschedule-source` (opens the reschedule modal, using the same discriminator pattern from PR #25). Delete writes to `store-ctx-delete`.

The `ts: Date.now()` on the delete payload is, again, the deduplication guard from PR #13.

---

## The Delete Flow

Delete is the most consequential action — it is irreversible (no undo in the current implementation). The flow:

1. User clicks Delete in the context menu
2. JS writes `{task_id, ts}` to `store-ctx-delete`
3. Python callback fires:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Input("store-ctx-delete", "data"),
    prevent_initial_call=True,
)
def handle_delete(delete_data):
    if not delete_data:
        raise PreventUpdate
    conn = app_db()
    delete_task(conn, delete_data["task_id"])
    return get_tasks_serialised(conn)
```

No confirmation dialog. Delete fires immediately. This is a deliberate choice for a personal tool where misclicks are rare and undo is planned for a future PR. For a team tool, a confirmation dialog would be required.

---

## The Z-Index Wars

The context menu appeared behind the detail drawer overlay when the drawer was open. The drawer's overlay was `z-index: 300`. The context menu was `z-index: 100`. A simple fix: set the context menu to `z-index: 1000`.

But `z-index: 1000` is the first step in a war. Modal dialogs are `z-index: 200`. Tooltips are `z-index: 400`. The `dmc.MantineProvider` manages z-index internally for its components. Custom absolute-positioned elements set their own z-index without coordination.

The correct fix is to audit the z-index layers and establish a named system:

```css
:root {
    --z-board: 1;
    --z-card: 10;
    --z-drawer: 300;
    --z-modal: 400;
    --z-ctx-menu: 500;
    --z-tooltip: 600;
}
```

This PR added the named CSS custom properties and updated every positioned element to use them. The context menu is `var(--z-ctx-menu)` — guaranteed to be above the drawer but below tooltips.

---

## The Trade-offs, Honestly

No confirmation on delete is aggressive. A "deleted" state with a brief undo window (like Gmail's "Undo send") would be the correct UX. The task_events log makes undo technically feasible — the `delete` event records the task ID, and restoring a deleted task would be a service function. This is on the roadmap.

The context menu is not keyboard-accessible. Right-click is not a keyboard gesture on most systems. The existing card action buttons provide keyboard-accessible alternatives for all three menu actions (the move button, the complete button, the Edit keyboard shortcut from PR #15). The context menu is an ergonomic enhancement, not the only path to any action.

The menu is injected directly into `document.body`. This means it sits outside Dash's React tree and is not managed by Dash's rendering lifecycle. This is intentional — it avoids the complexity of pattern-matching callbacks for dynamic card counts — but it means the menu cannot use Mantine's theme tokens or animation system.

---

## What the AI-Assisted Workflow Actually Looked Like

The event delegation pattern and `set_props` bridge were established from PR #13. The AI applied the same patterns to the context menu use case.

The z-index system was AI-suggested after the overlay conflict was reported. The CSS custom property approach — named layers in `:root` — was my specification; the AI identified all the existing z-index values that needed updating.

The `ts: Date.now()` pattern in the delete payload was applied automatically — it is now a CLAUDE.md convention for all store payloads written from JS.

---

## What This Unlocks

A secondary action surface for task cards that does not clutter the primary card UI. Delete is now accessible without opening the drawer. Move is a right-click away. The context menu is extensible — future items (Duplicate, Add to today, Copy link) can be added by adding items to the menu HTML and a case to the click handler.

---

## Takeaway for Consultants

Event delegation at document level is the correct pattern for JavaScript menus on dynamic content. One listener handles every card without re-registration on Dash re-renders. The `data-attribute` + `closest()` pattern cleanly identifies which card was right-clicked without relying on component IDs.

Establish z-index layers early — named CSS custom properties in `:root`. The alternative is discovering z-index conflicts in production and fixing them one at a time, which requires auditing every positioned element in the codebase.

---

## LinkedIn Summary

PR #28 added a vanilla JS right-click context menu to Stride's task cards. One document-level contextmenu listener handles all cards via event delegation — no re-registration on Dash re-renders. Edit/Move/Delete each bridge to Python via `window.dash_clientside.set_props` writing to a store. The z-index discovery: three components fighting for screen real estate, resolved with a named CSS custom property layer system (`--z-ctx-menu: 500`). Sometimes the right tool is 60 lines of vanilla JS, not a framework component.
