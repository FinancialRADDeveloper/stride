# Phase 6 — Add Task Polish, Keyboard Shortcuts, Dark Mode

**Branch:** `feat/phase-6-composer-polish`  
**PR target:** `main`  
**Dependencies:** All already in `pyproject.toml`

---

## What This Phase Delivers

- **Composer polish** — priority, category and size pickers inline in the "+ Add task" form
- **Keyboard shortcuts** — J/K navigate cards, E opens drawer, D marks done, N opens composer
- **Dark mode toggle** — topbar button swaps Mantine `colorScheme`; preference persisted in `dcc.Store`
- **Empty-state message** — friendly prompt when a day column has no tasks

The composer submit logic and show/hide callbacks are **already wired** in `composer_cb.py`. This phase layers richer inputs on top.

---

## Part 1 — Composer Polish

### What the form needs to gain

| Field | Current | After |
|-------|---------|-------|
| Title | `dcc.Input` ✓ | unchanged |
| Priority | missing | `dmc.SegmentedControl` (P1/P2/P3/P4) |
| Category | missing | `dmc.SegmentedControl` (6 options) |
| Size | missing | `dmc.SegmentedControl` (XS/S/M/L/XL) |

### Updated composer component (stride/ui/components/composer.py)

```python
import dash_mantine_components as dmc
from dash import html, dcc

PRIORITY_DATA = [
    {"value": "P1", "label": "P1"},
    {"value": "P2", "label": "P2"},
    {"value": "P3", "label": "P3"},
    {"value": "P4", "label": "P4"},
]

CATEGORY_DATA = [
    {"value": "build",    "label": "Build"},
    {"value": "work",     "label": "Work"},
    {"value": "home",     "label": "Home"},
    {"value": "admin",    "label": "Admin"},
    {"value": "health",   "label": "Health"},
    {"value": "personal", "label": "Personal"},
]

SIZE_DATA = [
    {"value": "XS", "label": "XS"},
    {"value": "S",  "label": "S"},
    {"value": "M",  "label": "M"},
    {"value": "L",  "label": "L"},
    {"value": "XL", "label": "XL"},
]

def composer(day_key: str) -> html.Div:
    return html.Div(
        id={"type": "composer", "day_key": day_key},
        className="composer",
        style={"display": "none"},
        children=[
            dcc.Input(
                id={"type": "input-new-task", "day_key": day_key},
                type="text",
                placeholder="Task title — press Enter or click Add",
                className="composer-input",
                debounce=False,
                value="",
                n_submit=0,
            ),
            html.Div(
                className="composer-pickers",
                children=[
                    dmc.SegmentedControl(
                        id={"type": "composer-priority", "day_key": day_key},
                        data=PRIORITY_DATA,
                        value="P3",
                        size="xs",
                        className="composer-segmented",
                    ),
                    dmc.SegmentedControl(
                        id={"type": "composer-size", "day_key": day_key},
                        data=SIZE_DATA,
                        value="M",
                        size="xs",
                        className="composer-segmented",
                    ),
                    dmc.SegmentedControl(
                        id={"type": "composer-category", "day_key": day_key},
                        data=CATEGORY_DATA,
                        value="personal",
                        size="xs",
                        className="composer-segmented",
                    ),
                ],
            ),
            html.Div(
                className="composer-actions",
                children=[
                    html.Button(
                        "Cancel",
                        id={"type": "btn-cancel-add", "day_key": day_key},
                        className="btn-cancel",
                        n_clicks=0,
                    ),
                    html.Button(
                        "Add task",
                        id={"type": "btn-confirm-add", "day_key": day_key},
                        className="btn-confirm",
                        n_clicks=0,
                    ),
                ],
            ),
        ],
    )
```

### Updated submit callback (stride/ui/callbacks/composer_cb.py)

Add the three new `State` inputs and pass them to `create_task`:

```python
@app.callback(
    Output("store-tasks", "data", allow_duplicate=True),
    Output({"type": "composer", "day_key": MATCH}, "style", allow_duplicate=True),
    Output({"type": "input-new-task", "day_key": MATCH}, "value", allow_duplicate=True),
    Input({"type": "btn-confirm-add", "day_key": MATCH}, "n_clicks"),
    Input({"type": "input-new-task", "day_key": MATCH}, "n_submit"),
    State({"type": "input-new-task", "day_key": MATCH}, "value"),
    State({"type": "composer-priority", "day_key": MATCH}, "value"),
    State({"type": "composer-size", "day_key": MATCH}, "value"),
    State({"type": "composer-category", "day_key": MATCH}, "value"),
    State("store-tasks", "data"),
    State("store-week-offset", "data"),
    prevent_initial_call=True,
)
def submit_new_task(confirm_clicks, n_submit, title, priority, size, category_id,
                    current_tasks, week_offset):
    ...
    new_task = create_task(
        conn,
        title=title.strip(),
        day_key=day_key,
        priority=priority or "P3",
        size=size or "M",
        category_id=category_id or "personal",
    )
    ...
```

### CSS additions (stride/assets/stride.css)

```css
/* Composer picker row */
.composer-pickers {
    display: flex;
    gap: 6px;
    margin: 6px 0;
    flex-wrap: wrap;
}

.composer-segmented {
    flex-shrink: 0;
}

/* Composer overall */
.composer {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px 8px;
    margin: 6px 0 4px;
}

.composer-input {
    width: 100%;
    border: none;
    background: transparent;
    font-size: 13px;
    outline: none;
    padding: 4px 0;
    color: var(--text-primary);
}

.composer-input:focus {
    border-bottom: 1px solid var(--accent);
}

.composer-actions {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
    margin-top: 8px;
}
```

---

## Part 2 — Keyboard Shortcuts

### Architecture

A new JS asset (`stride/assets/keyboard.js`) attaches a `keydown` listener to `document`. It writes a `{action, ts}` object to the `store-kb-action` dcc.Store via `window.dash_clientside.set_props`. A server callback reads that store and dispatches to the appropriate service call.

### stride/assets/keyboard.js

```javascript
(function() {
  var IGNORE_TAGS = ['INPUT', 'TEXTAREA', 'SELECT'];

  document.addEventListener('keydown', function(e) {
    if (IGNORE_TAGS.includes(e.target.tagName)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    var action = null;
    switch (e.key) {
      case 'j': action = 'next-card';     break;
      case 'k': action = 'prev-card';     break;
      case 'e': action = 'open-drawer';   break;
      case 'd': action = 'toggle-done';   break;
      case 'n': action = 'new-task';      break;
      case 'Escape': action = 'close';    break;
    }
    if (!action) return;
    e.preventDefault();

    window.dash_clientside.set_props('store-kb-action', {
      data: { action: action, ts: Date.now() }
    });
  });
})();
```

### store-kb-action (stride/ui/app.py)

Add to the layout's `dcc.Store` list:

```python
dcc.Store(id="store-kb-action", data=None),
dcc.Store(id="store-focused-task", data=None),  # id of currently focused card
```

### Keyboard callback (stride/ui/callbacks/kb_cb.py)

```python
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

def register_callbacks(app):
    @app.callback(
        Output("store-selected", "data", allow_duplicate=True),
        Output("store-tasks", "data", allow_duplicate=True),
        Output("store-focused-task", "data"),
        Input("store-kb-action", "data"),
        State("store-tasks", "data"),
        State("store-selected", "data"),
        State("store-focused-task", "data"),
        prevent_initial_call=True,
    )
    def handle_kb(kb, tasks, selected_id, focused_id):
        if not kb:
            raise PreventUpdate
        action = kb.get("action")
        tasks = tasks or []

        if action in ("next-card", "prev-card"):
            ids = [t["id"] for t in tasks if not t.get("done")]
            if not ids:
                raise PreventUpdate
            if focused_id not in ids:
                new_focused = ids[0]
            else:
                idx = ids.index(focused_id)
                delta = 1 if action == "next-card" else -1
                new_focused = ids[(idx + delta) % len(ids)]
            return no_update, no_update, new_focused

        if action == "open-drawer" and focused_id:
            return focused_id, no_update, no_update

        if action == "toggle-done" and focused_id:
            from stride.db import app_db
            from stride.services.tasks import toggle_done
            conn = app_db()
            toggle_done(conn, focused_id)
            # refresh store
            from stride.services.tasks import list_tasks
            import datetime
            # use existing tasks list to infer day_keys in view
            day_keys = list({t["day_key"] for t in tasks})
            refreshed = list_tasks(conn, day_keys=day_keys, include_done=True)
            return no_update, [t.model_dump() for t in refreshed], no_update

        if action == "close":
            return None, no_update, no_update

        raise PreventUpdate
```

Register `kb_cb` in `stride/ui/app.py` alongside the other callbacks.

---

## Part 3 — Dark Mode Toggle

### Architecture

Dash's `dcc.Store(id="store-theme")` holds `"light"` or `"dark"`. A button in the topbar triggers a callback that flips the value. A second callback passes it to `dmc.MantineProvider`'s `forceColorScheme` prop (DMC 2.x).

### Topbar addition (stride/ui/components/topbar.py)

```python
html.Button(
    "☾",
    id="btn-dark-mode",
    className="btn-icon",
    title="Toggle dark mode",
    n_clicks=0,
),
```

Add to layout (stride/ui/app.py):

```python
dcc.Store(id="store-theme", data="light"),
```

Wrap the entire layout in `dmc.MantineProvider`:

```python
dmc.MantineProvider(
    id="mantine-provider",
    forceColorScheme="light",
    children=[...existing layout...],
)
```

### Theme callback (stride/ui/callbacks/theme_cb.py)

```python
from dash import Input, Output, State, callback, no_update

def register_callbacks(app):
    @app.callback(
        Output("store-theme", "data"),
        Output("mantine-provider", "forceColorScheme"),
        Input("btn-dark-mode", "n_clicks"),
        State("store-theme", "data"),
        prevent_initial_call=True,
    )
    def toggle_theme(n, current):
        new = "dark" if current == "light" else "light"
        return new, new
```

### CSS variables for dark mode

Add to `stride.css`:

```css
[data-mantine-color-scheme="dark"] {
    --surface-0: #0f1117;
    --surface-1: #1a1d27;
    --surface-2: #22263a;
    --border:    #2e3249;
    --text-primary: #e2e8f0;
    --text-muted:   #8892a4;
    --accent:    #6c7ae0;
}
```

---

## Part 4 — Empty State

### Board column empty state (stride/ui/components/board.py)

When `card_stack` has no children, replace it with a styled placeholder:

```python
if not card_children:
    card_stack_children = [
        html.Div(
            [
                html.Div("Nothing yet", className="empty-state-title"),
                html.Div(
                    "Click '+ Add task' to plan your day",
                    className="empty-state-hint mono",
                ),
            ],
            className="empty-state",
        )
    ]
else:
    card_stack_children = card_children
```

```css
.empty-state {
    padding: 32px 12px;
    text-align: center;
    opacity: 0.45;
}

.empty-state-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 4px;
}

.empty-state-hint {
    font-size: 11px;
    color: var(--text-muted);
}
```

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `stride/ui/components/composer.py` | **Modify** — add three `dmc.SegmentedControl` pickers |
| `stride/ui/callbacks/composer_cb.py` | **Modify** — read priority/size/category State, pass to create_task |
| `stride/ui/components/topbar.py` | **Modify** — add dark mode button |
| `stride/ui/components/board.py` | **Modify** — empty-state placeholder when column is empty |
| `stride/ui/app.py` | **Modify** — add `store-kb-action`, `store-focused-task`, `store-theme`; wrap in `MantineProvider`; register `kb_cb`, `theme_cb` |
| `stride/ui/callbacks/kb_cb.py` | **Create** — keyboard shortcut dispatcher |
| `stride/ui/callbacks/theme_cb.py` | **Create** — dark/light mode toggle |
| `stride/assets/keyboard.js` | **Create** — document-level keydown listener |
| `stride/assets/stride.css` | **Modify** — composer polish, dark mode vars, empty state |

---

## Edge Cases to Handle

- `keyboard.js` must guard against `INPUT`/`TEXTAREA` focus — never intercept typing
- `n` shortcut (new task) needs to know which day column is "active" — default to today's date if unclear
- Dark mode: some hardcoded `style={"color": ...}` on cards use hex values; CSS vars won't override inline styles — audit and move to classes
- `dmc.SegmentedControl` in composer resets to default when composer is re-shown — the reset callback must also reset the pickers to defaults (P3, M, personal)
- `forceColorScheme` requires DMC 2.x — check `dmc.__version__` in a debug print if it doesn't work; fallback is `colorScheme` prop

---

## Testing Strategy

```
tests/test_composer.py
```

1. `submit_new_task` with priority=P1, size=L, category_id="build" — verify task persisted with those values
2. `submit_new_task` with empty title — verify no task created (service layer guard)
3. Keyboard shortcut: mock `store-kb-action` data `{action: "toggle-done"}` with focused task — verify done flag flips

No UI tests for dark mode (CSS-only). Manual verification sufficient.
