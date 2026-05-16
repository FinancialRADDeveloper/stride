# Stride — Mobile Web Responsiveness Plan

## Executive Summary

Stride is desktop-first with `overflow: hidden` on the body and `min-width: max-content` on the board — zero usable mobile layout by default. Making it genuinely mobile-friendly is a **medium (M) T-shirt size** (~20 hours): targeted CSS-first approach, a small number of Python layout changes, and a thin JS touch layer. 70% of the improvement comes from CSS-only changes and a single `meta_tags` line in `app.py`.

---

## Quick Wins (highest ROI, least effort)

1. **Viewport meta tag** — one line in `app.py`. Without this, nothing else matters.
2. **`height: 100dvh`** — two CSS lines. Fixes iOS Safari address-bar gap cutting off the board bottom.
3. **Board snap carousel** — six CSS lines in a `@media (max-width: 767px)` block. Swipeable day columns, no Python changes.
4. **`@media (hover: none) { .card-move-btn { opacity: 1; } }`** — one CSS line. Move button always visible on touch.
5. **Topbar collapse** — five CSS lines. Hide secondary elements, keep ‹ Today › arrows.
6. **Drawer `width: 100%` override** — one CSS rule. Prevents 440px drawer overflowing a 390px phone.
7. **Touch target padding on checkbox** — three CSS lines. Prevents misfire frustration.

---

## Board Layout on Mobile

**Recommendation: CSS snap carousel (Option A)**

The board already renders all day columns. Adding `scroll-snap-type` turns it into a swipeable carousel with no Python changes:

```css
@media (max-width: 767px) {
  body { height: 100dvh; overflow: hidden; }
  .board { overflow-x: auto; scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch; }
  .board-inner { min-width: unset; height: 100%; }
  .day-column { flex: 0 0 calc(100vw - 48px); width: calc(100vw - 48px); scroll-snap-align: start; }
}
```

Columns shrink to `calc(100vw - 48px)` with a peek of the next column as a swipe affordance.

---

## Navigation

**Compact topbar + visible ‹ Today › arrows.** Hide: subtitle, divider, week label, Completed toggle, dark mode (via CSS). Keep: logo, wordmark, ‹ Today › buttons.

Add a small `#mobile-footer` fixed-position bar to `app.py` layout — hidden on desktop, shown on mobile — with the Completed toggle and dark mode button.

---

## Touch Interactions

**Move button:** On mobile, add a "Move to" day-chips section at the bottom of the detail drawer (`detail.py`). User taps card → drawer opens → taps destination day. No gesture recognition, no JS touch events.

**Drag-and-drop:** Accept that DnD is desktop-only for now. `dnd.js` uses HTML5 drag events which don't fire on iOS Safari / Android without a polyfill. The drawer move mechanism is the primary move path on mobile.

**Touch targets:** Pad checkbox hit area with CSS `padding: 14px; margin: -14px` — no visual change, correct touch size.

---

## DMC Responsive Capabilities

DMC 0.14 wraps Mantine 7. Available tools:
- `visibleFrom` / `hiddenFrom` props on most layout components
- Responsive style props: `p={"base": 8, "sm": 16}`
- Drawer `size` override via CSS on `.mantine-Drawer-content`

Default breakpoints: `xs`=576px, `sm`=768px, `md`=992px, `lg`=1200px

---

## PWA Baseline

Required for app store path (feeds into Capacitor/TWA):

**1. Viewport meta tag** (in `app.py`):
```python
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
)
```

**2. `stride/assets/manifest.json`:**
```json
{
  "name": "Stride",
  "short_name": "Stride",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f5f3ee",
  "theme_color": "#1a1a1a",
  "icons": [
    { "src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**3. `stride/assets/sw.js`** (minimal service worker — cache assets only, never `/_dash-*` routes):
```javascript
self.addEventListener('install', e => e.waitUntil(
  caches.open('stride-v1').then(cache => cache.addAll(['/', '/assets/stride.css']))
));
self.addEventListener('fetch', e => {
  if (e.request.url.includes('/_dash-')) return; // never cache Dash callbacks
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
```

Register via `app.index_string`.

---

## Implementation Sequence

| Sprint | Work | Effort |
|---|---|---|
| Sprint 1 | Viewport meta tag, 100dvh, board snap carousel, topbar collapse, drawer full-screen | 1–2 days |
| Sprint 2 | Touch targets, move-in-drawer UI, composer keyboard behaviour | 1–2 days |
| Sprint 3 | manifest.json, service worker, install flow testing | 0.5–1 day |
| Sprint 4 | Mobile footer bar, cross-device testing, iOS Safari polish | 1 day |

**Total: ~20 hours**

---

## Files to Touch

| File | Change |
|---|---|
| `stride/ui/app.py` | Add `meta_tags` viewport; add `app.index_string` for manifest + SW registration |
| `stride/assets/stride.css` | Add mobile media queries |
| `stride/assets/manifest.json` | Create new |
| `stride/assets/sw.js` | Create new |
| `stride/assets/icon-192.png` / `icon-512.png` | Create icon assets |
| `stride/ui/components/detail.py` | Add "Move to" chips section |
| `stride/ui/callbacks/detail_cb.py` | Add move-from-drawer callback |

No changes to `board.py`, `card.py`, `topbar.py`, `dnd.js`, or any model/service layer.

---

## Biggest Risks

| Risk | Mitigation |
|---|---|
| iOS Safari `100vh` / virtual keyboard obscuring inputs | Use `100dvh`; ensure composer inputs are inside `overflow-y: auto` container |
| Callback latency on low-end devices | Keep mobile surface minimal; fewer interactive elements visible at once |
| Drawer size overflow (440px > 390px screen) | CSS override `.mantine-Drawer-content { width: 100% !important; }` inside media query |
| Service worker caching `/_dash-*` routes | Explicitly exclude these in the SW fetch handler |
| DnD not working on touch | Accept desktop-only for now; drawer move is the mobile path |
