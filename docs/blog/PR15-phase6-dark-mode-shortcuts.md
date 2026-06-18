# Dark Mode, Keyboard Shortcuts, and the Art of Progressive Enhancement

Phase 6 is a polish sprint. The board works. The drawer works. Drag-and-drop works. What Phase 6 adds is the layer that separates a working tool from a pleasant one: dark mode, keyboard shortcuts, and a richer composer.

None of these features are load-bearing. The app functions without them. But they are the features that determine whether you enjoy using the app every day or merely tolerate it.

---

## What We Built

Three independent features in PR #15, each adding a new dimension of usability:

**1. Composer pickers.** The quick-add composer at the bottom of each day column gained collapsible pickers for priority, category, size, and estimate. Previously the composer could only accept a title. Now it creates fully-specified tasks inline without opening the drawer.

**2. Dark mode.** A toggle button in the topbar switches the board to a dark colour scheme. All Mantine components update via `forceColorScheme`. Custom CSS responds to the `[data-mantine-color-scheme="dark"]` attribute selector.

**3. Keyboard shortcuts.** J/K navigate between cards. E opens the drawer. D marks the selected card done. Implemented as a `clientside_callback` that listens to `keydown` events.

---

## Dark Mode: The Mantine Way

Dash Mantine Components ships a `dmc.MantineProvider` that wraps the entire layout. The `forceColorScheme` prop accepts `"light"` or `"dark"` and drives every Mantine component's colour scheme simultaneously:

```python
dmc.MantineProvider(
    children=[...],
    id="mantine-provider",
    forceColorScheme="light",
)
```

A callback reads `store-theme` and updates `forceColorScheme`:

```python
@app.callback(
    Output("mantine-provider", "forceColorScheme"),
    Input("store-theme", "data"),
)
def update_color_scheme(theme):
    return theme or "light"
```

When `forceColorScheme` changes, Mantine sets a `data-mantine-color-scheme` attribute on the document root. CSS custom properties handle the rest:

```css
:root {
    --bg-primary: #f5f3ee;
    --text-primary: #1a1a2e;
}

[data-mantine-color-scheme="dark"] {
    --bg-primary: #1a1a2e;
    --text-primary: #f5f3ee;
}
```

Every component that uses `var(--bg-primary)` or `var(--text-primary)` flips automatically. The dark palette inverts the light palette — the warm cream becomes the dark ink, and vice versa. This is not accidental: the colour choices in PR #1 were made with this inversion in mind.

The dark mode toggle button's tooltip reads "preserves session only" — the theme is in `store-task` which is memory-only, not persisted to the database. On page reload, the board returns to light mode. This was a deliberate scope decision: persisting user preferences adds a `user_settings` table, a preferences service, and a load-on-startup callback. For a personal tool where dark mode is typically set at the OS level, this complexity is not justified.

---

## Keyboard Shortcuts: Clientside Callbacks

Keyboard shortcuts require listening to `keydown` events. In Dash, there are two ways to do this: a Python callback that polls a `dcc.Interval` (slow, server round-trip per keystroke) or a clientside callback that runs in the browser.

The clientside callback:

```python
app.clientside_callback(
    """
    function(n_intervals) {
        if (window._stride_keys_registered) return window.dash_clientside.no_update;
        document.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            if (e.key === 'j') { /* move selection down */ }
            if (e.key === 'k') { /* move selection up */ }
            if (e.key === 'e') { /* open drawer */ }
            if (e.key === 'd') { /* mark done */ }
        });
        window._stride_keys_registered = true;
        return window.dash_clientside.no_update;
    }
    """,
    Output("dummy-output", "children"),
    Input("tick", "n_intervals"),
)
```

The `window._stride_keys_registered` flag is a guard against re-registering on every tick. Clientside callbacks fire every time their `Input` changes — without the guard, the tick would register a new keydown listener every 60 seconds, and after an hour of use, 60 listeners would be firing per keystroke.

The `e.target.tagName` check prevents shortcuts from firing when the user is typing in an input field. Without this, pressing D to mark a task done while typing in the title field would intercept the character.

The `if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;` pattern is so common in keyboard shortcut implementations that it belongs in the CLAUDE.md under "JS keyboard shortcut guard patterns."

---

## The Composer Pickers

The composer (quick-add form at the bottom of each column) previously only accepted a title. Tasks created via the composer had no priority, no estimate, no category — they were all set to defaults.

Phase 6 adds a disclosure triangle that expands to reveal:
- `dmc.SegmentedControl` for priority (P1/P2/P3/P4)
- `dmc.ChipGroup` for category
- `dmc.SegmentedControl` for size (XS/S/M/L/XL)
- `dmc.NumberInput` for estimate

The composer is now a `dmc.Stack` with the title input always visible and the picker panel hidden by default. A `dmc.ActionIcon` with a chevron toggles visibility via a clientside callback — no server round-trip for a UI toggle.

`store-composer-open` tracks which column's composer is expanded. Only one composer can be open at a time — opening one closes the other.

---

## The Trade-offs, Honestly

Session-only dark mode is the most deliberate limitation. The correct long-term solution is a `user_preferences` table and a load-on-startup callback. The pragmatic short-term solution is the in-memory store. Both are valid for their respective time horizons.

Keyboard shortcuts are not documented anywhere in the UI. They are power-user features discoverable by accident or by reading this article. A help modal listing all shortcuts was considered and deferred — it adds a component, a toggle callback, and CSS for a feature that most users will either know from habit or not use at all.

The composer picker expansion uses a `dcc.Store` for open/closed state, which means the server is involved in a UI-only toggle. The correct implementation is a fully clientside toggle — but Dash's `clientside_callback` model makes it harder to update nested component properties cleanly. This is one of Dash's friction points: purely client-side state management is harder than it should be.

---

## What the AI-Assisted Workflow Actually Looked Like

Dark mode: I specified the CSS custom property approach and the `forceColorScheme` pattern. The AI generated the CSS and the callback. The colour values were mine — the dark palette was designed alongside the light palette in PR #1.

Keyboard shortcuts: I specified the guard pattern (input/textarea check), the key bindings, and the one-time registration requirement. The AI generated the clientside callback. I reviewed the `window.dash_clientside.no_update` return value — a Dash-specific pattern for "I received the trigger but have no output to produce."

Composer pickers: I designed the component hierarchy (always-visible title, disclosure triangle, picker stack). The AI generated the DMC component tree. Testing confirmed the single-open constraint worked correctly.

---

## What This Unlocks

Dark mode makes the board usable in the evenings without eye strain. Keyboard shortcuts make task management faster for users who prefer not to reach for the mouse. The richer composer means tasks can be fully specified at creation time without the second step of opening the drawer to set properties.

Together these features change the daily experience of using Stride from "functional" to "pleasant." That distinction matters more for a tool you use every day than for a tool you use occasionally.

---

## Takeaway for Consultants

Progressive enhancement is the right model for polish features. Dark mode, keyboard shortcuts, and richer forms all add value without changing the core functionality. Build them when the core is stable, not before. A well-polished tool built on a shaky foundation will not hold; a solid foundation with no polish is a tool people tolerate but do not love.

Clientside callbacks are the right tool for browser-only interactions — dark mode colour scheme updates, keyboard event listeners, UI toggle state. Server round-trips for pure client-side interactions add latency and server load for no benefit. Know the boundary.

---

## LinkedIn Summary

Phase 6 of Stride added dark mode (one prop, two CSS variables, no DB persistence needed), keyboard shortcuts (clientside callback with a registration guard to prevent listener accumulation), and a richer quick-add composer. Each was built as a polish layer on a stable foundation. The dark mode CSS custom property pattern — one `[data-mantine-color-scheme="dark"]` selector, twenty variables — drives the entire colour scheme flip from one attribute change.
