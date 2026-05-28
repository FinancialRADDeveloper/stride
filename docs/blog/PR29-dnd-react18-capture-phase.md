# The Bug That Revealed a React 18 Architectural Change Most Developers Don't Know About

I shipped drag-and-drop between day columns. It worked. I merged other PRs. Then I came back to test it again and the drag ghost appeared — the translucent floating card you get when you pick something up — but when I released the mouse, nothing happened. The card snapped back. No drop. No move.

This is the kind of bug that makes you question whether you changed something, or whether the world changed around you. The answer, it turned out, was the latter.

---

## What We Built and Why

Stride is a day-lane task board built in Python using Dash. Dash compiles Python component trees to React and serves them from a Python backend. It is an excellent choice for a productivity dashboard — but it has no first-class drag-and-drop. That meant writing a small vanilla JavaScript bridge: `stride/assets/dnd.js`.

The approach is simple. Cards carry a `data-task-id` attribute. Day columns carry a `data-drop-day` attribute. The JS file listens for native HTML5 drag events at `document` level using event delegation — one set of listeners handles every card and every column regardless of how many times Dash re-renders the board. On drop, it calls `window.dash_clientside.set_props` to write `{ task_id, to_day_key }` into a `dcc.Store`, and a Python callback handles the actual database update.

This works cleanly in isolation. The problem was what happened when Dash's React version entered the picture.

---

## The Key Technical Decision

React 18 moved event delegation. In React 17 and earlier, React attached its synthetic event system at `document`. In React 18, it attaches at the React root element — the `<div id="react-entry-point">` or equivalent. This was a deliberate architectural change made to improve compatibility with micro-frontends and server components.

The consequence for our code: bubble-phase listeners registered at `document` now fire *after* React has already processed the event at the root. For most events, this is irrelevant. For HTML5 drag events, it is fatal.

Here is what was breaking. The `dnd.js` IIFE (immediately-invoked function expression) holds a closure variable called `dragging`, initialised to `null`. On `dragstart`, it is set to the task ID. On `dragover`, the first thing the handler does is check `if (!dragging) return;`. If `dragging` is null, the handler exits before calling `e.preventDefault()`. The browser only fires `drop` if `dragover` has called `preventDefault()` on every frame the drag passes over a target. If it does not, the browser treats the target as non-droppable and the release does nothing.

Because our `dragstart` listener was in bubble phase at `document`, it never fired at all — React processed the event at the root and it never propagated far enough. `dragging` stayed `null`. Every `dragover` returned immediately. Drop never fired. The ghost appeared because that is native browser behaviour that does not depend on our listeners. The release did nothing because we never told the browser the target was droppable.

The fix is a single argument. Every `addEventListener` call in `dnd.js` takes `true` as its third parameter:

```js
document.addEventListener('dragstart', function (e) { ... }, true);
document.addEventListener('dragend',   function (e) { ... }, true);
document.addEventListener('dragover',  function (e) { ... }, true);
document.addEventListener('dragleave', function (e) { ... }, true);
document.addEventListener('drop',      function (e) { ... }, true);
```

The third argument `true` puts the listener in *capture phase*. Capture fires top-down from `window` to the target, before bubble phase fires bottom-up from the target to `document`. Capture-phase listeners at `document` fire before React's delegation system even sees the event.

One commit. Five lines changed. A morning of debugging.

---

## The Second Bug: Dash Store Deduplication

While I was in there, I found a second failure mode. Dash is built on a reactive store model: when a `dcc.Store` value changes, dependent callbacks fire. "Changes" means the new value is not deeply equal to the old one. If you drop a card onto the same column it is already in — or if Dash happens to compare two identical drop payloads — the store does not update, so the callback does not fire, and the move does not happen.

The fix is a `ts` field:

```js
window.dash_clientside.set_props('store-dnd-drop', {
    data: { task_id: dragging, to_day_key: toDay, ts: Date.now() }
});
```

`Date.now()` returns the current Unix timestamp in milliseconds. It is almost certainly different on each drop, which means the store value is almost certainly different, which means the callback fires. The `ts` field is ignored server-side — it is purely a deduplication guard.

---

## The Trade-offs, Honestly

Capture-phase listeners fire before React can process events. For drag-and-drop, this is exactly what you want — you are bridging a vanilla JS DnD system into a React-managed page, and you need to see the event first. If you later add more complex event handling that interacts with React's synthetic event system in the same gesture, you will need to think carefully about the ordering. There is no free lunch.

Also worth acknowledging: this bug was invisible during local development in the early commits because the listener registration happened before any re-renders that might reveal the ordering issue. It only surfaced after other PRs landed and the board went through more render cycles. Silent regressions like this are the hardest to debug because you cannot easily bisect them — the fix was introduced days before the symptom appeared.

---

## What the AI-Assisted Workflow Actually Looked Like

This was not one of the sessions where AI generated the solution in thirty seconds. The investigation was iterative: reading the Dash docs on `set_props`, checking whether the JS was even loading (it was), adding `console.log` calls to verify which listeners were firing (none of them), and then searching for React 18 drag event changes.

Once we understood the root cause, the fix was trivial and the explanation precise enough to write directly into the commit message. The three commits in the fix branch are: add the `ts` field to the drop payload, guard `e.dataTransfer` for null (a separate crash on fast drag interactions), and switch to capture phase. Each is a standalone, reviewable unit with a clear rationale.

The CLAUDE.md file now records this as a named gotcha: "DnD listeners use capture phase — `dnd.js` adds all `addEventListener` calls with `true` (capture phase). React 18 delegates events to the root element; bubble-phase listeners at `document` never fire." Future sessions start with that knowledge. The bug is not rediscoverable.

---

## What This Unlocks

With reliable DnD, the board behaves like a real task management tool rather than a prototype. Cards can be moved between days in a single gesture. The drop target highlights on hover. The move persists to SQLite immediately. It is the kind of interaction that the rest of the tool depends on feeling right.

---

## Takeaway for Consultants

If you are building anything in a Python framework that wraps React — Dash, Streamlit with custom components, Panel — and you are bridging vanilla JavaScript event handlers, you are working in two event systems simultaneously. React 18 changed where it attaches its delegation layer, and that change is not prominently documented. Check which version of React your framework is shipping, and test capture-phase registration if your custom JS listeners stop firing after a framework update. The third argument to `addEventListener` is easy to overlook and genuinely consequential.
