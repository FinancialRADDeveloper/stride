# Mobile-First Isn't About Shrinking Your Desktop Layout

The board worked on desktop. On a phone, it was a disaster — columns too wide to see fully, scrolling erratic, tap targets too small, no concept of "this column is the current one." The mobile sprint fixed all of this, and the primary tool was CSS scroll snap — a browser feature so well-suited to the problem that the alternative (a JavaScript carousel library) was never seriously considered.

PR #19 (the second attempt — more on that) produced the mobile layout that shipped. The first attempt, PR #18, was closed without merging because the snap logic was wrong.

---

## What We Built

No new Python. No new callbacks. No new services. PR #19 is entirely CSS, HTML attributes, and meta tags:

- **Viewport meta tag** — `width=device-width, initial-scale=1.0` for correct mobile rendering
- **CSS scroll snap** — `scroll-snap-type: x mandatory` on the board, `scroll-snap-align: start` on each column
- **Touch targets** — minimum 44px tap areas on all interactive elements (iOS HIG standard)
- **Responsive layout** — `@media (max-width: 768px)` overrides for full-width columns, compressed card padding, hidden desktop controls
- **PWA meta tags** — `apple-mobile-web-app-capable`, `theme-color` for home screen installation

---

## CSS Scroll Snap: The Right Tool

A horizontal carousel showing one column at a time is a common mobile UI pattern. The typical implementation involves:

1. A JavaScript library (`Swiper.js`, `Embla`, `Glide`) with scroll position tracking, touch gesture detection, animation easing, and snap-to-column logic, or
2. CSS scroll snap — a browser feature that does all of this natively

CSS scroll snap requires three declarations:

```css
.board {
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
}

.day-column {
    flex: 0 0 100vw;
    scroll-snap-align: start;
}
```

`scroll-snap-type: x mandatory` on the container tells the browser: after any scroll gesture ends, snap to the nearest snap point. `scroll-snap-align: start` on each column tells the browser: the left edge of each column is a snap point.

The result: native momentum scrolling between columns, smooth deceleration to the snap point, hardware-accelerated animation, and no JavaScript. It works in every modern mobile browser. The "mandatory" mode means the board always rests on a column boundary — never between two columns.

The alternative (a JS carousel library) would add:
- A Node.js dependency
- JavaScript bundle weight
- A JS execution overhead on every gesture
- Compatibility maintenance as library versions update
- The risk that the library's internal state diverges from Dash's component state

CSS scroll snap adds none of these. It is the correct tool.

---

## The Viewport Meta Tag: Non-Negotiable

Without `<meta name="viewport" content="width=device-width, initial-scale=1.0">`, mobile browsers render the page as if it were a desktop viewport (typically 980px wide) and scale it down to fit the phone screen. Every element appears tiny. Text requires pinch-to-zoom to read.

The viewport meta tag tells the browser: render at the actual device width, do not scale. This is the single most important change for any web application going mobile. Everything else is refinement.

Stride uses Dash, which generates its `index.html` programmatically. Adding the viewport meta tag requires extending the index template:

```python
app = Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "apple-mobile-web-app-capable", "content": "yes"},
        {"name": "theme-color", "content": "#f5f3ee"},
    ]
)
```

Dash's `meta_tags` parameter inserts `<meta>` tags into the generated `<head>`. This is the supported mechanism — not editing a template file.

---

## Touch Targets and the iOS HIG

Apple's Human Interface Guidelines specify 44×44 points as the minimum tap target size. Below this, taps become unreliable — the user's finger obscures the target and touch registration misses.

The card action buttons (complete, move, delegated toggle) were originally 24px — fine for desktop mouse clicks, too small for mobile fingers. Phase 6 updated them to 44px minimum hit areas using padding and `min-width`/`min-height` overrides.

The category chips and priority buttons in the composer were similarly expanded. The drawer close button, the complete button on the card, and the navigation arrows were all checked against the 44px standard.

This is tedious work — reviewing every interactive element for touch target size — but it is the difference between a mobile layout that technically works and one that users can actually use without frustration.

---

## Why PR #18 Was Closed

PR #18 was the first attempt at mobile CSS. The snap logic was implemented with `scroll-snap-align: center` on each column and `flex: 0 0 90vw` (90% of viewport width). The intent was to show a peek of the adjacent column, indicating there is more to scroll.

The result: the snap points were misaligned. On a 390px-wide iPhone, 90vw columns are 351px. Snap points are at 0, 351, 702, 1053... The board container has no padding, so the left edge of column 2 is 351px from the left. After snapping to column 2, the left edge is exactly at the viewport left — the peek of column 1 has disappeared because column 2 is now fully left-aligned. The "peek" intent was never achieved.

The correct implementation for peek is complex: the container needs padding and the columns need a width that accounts for that padding. For `padding: 16px` on each side and `calc(100vw - 32px)` column width, the math works. But the simpler implementation — `100vw` columns with no peek — is cleaner and more predictable. PR #19 chose simplicity over the peek effect.

The lesson: close PRs that have wrong mental models. PR #18 was not a bad attempt at the right design — it was based on a misunderstanding of how snap points and column widths interact. Iterating on it would have produced more complicated wrong code. A fresh start with the correct mental model produces clean code.

---

## The Trade-offs, Honestly

Full-width columns (`100vw`) give no visual indication that other columns exist. There is no peek, no partial-column hint. Users must discover scrolling through exploration. A visual indicator (a horizontal dot-navigation like a carousel) would address this — it is on the backlog.

`-webkit-overflow-scrolling: touch` adds momentum scrolling on iOS but is a non-standard property deprecated in some Safari versions. It still works and produces a noticeably better scroll feel on older iOS devices. The deprecation risk is low for a personal tool.

The responsive breakpoint (`768px`) is a single threshold. On tablets in landscape mode (1024px wide), the desktop layout applies but may feel cramped. This is acceptable for Stride's user base.

---

## What the AI-Assisted Workflow Actually Looked Like

The viewport meta tag and CSS scroll snap properties were AI-generated from a specification: "mobile-first, one column per viewport width, CSS snap, no JS library." The `meta_tags` Dash parameter syntax was looked up and AI-confirmed.

The touch target audit was manual — I reviewed every interactive element in the mobile layout on an iPhone and flagged the ones below 44px. The CSS fixes were AI-generated.

PR #18 was written and then closed after testing revealed the snap misalignment. PR #19 was a fresh start with the corrected mental model. The AI helped with both — the implementation of #18 and the diagnosis of why it was wrong.

---

## What This Unlocks

A board you can use on your phone. The mobile layout is a first-class experience — not a scaled-down desktop, not a "mobile-optimised" view with reduced features. Every feature available on desktop is available on mobile. Drag-and-drop does not work with touch events (HTML5 DnD uses mouse events on desktop) — but the move-to flyout and reschedule modal are fully touch-accessible.

---

## Takeaway for Consultants

CSS scroll snap is the correct tool for native-feeling horizontal carousels in mobile web applications. Three declarations, zero JavaScript, full browser support, no library maintenance burden. Use it before reaching for a JavaScript carousel library.

Close PRs with wrong mental models. The code from PR #18 was not reusable — the snap misalignment was a fundamental conceptual error, not an off-by-one fix. Starting clean in PR #19 produced better code in less time than debugging a wrong approach.

---

## LinkedIn Summary

The Stride mobile layout uses CSS scroll snap — three CSS declarations, zero JavaScript, native browser momentum scrolling. The first attempt (PR #18) had the snap math wrong; rather than debug a misaligned mental model, I closed it and started fresh. PR #19 is cleaner and took less time. The lesson: close PRs with wrong foundations before they become legacy code you have to maintain.
