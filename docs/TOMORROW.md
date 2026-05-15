# Tomorrow's Session Briefing

**Project:** Stride — personal day-lane task board  
**Repo:** `C:\Code\stride` | GitHub: `FinancialRADDeveloper/stride`  
**Stack:** Python 3.11 · Plotly Dash 2.17 · dash-mantine-components · SQLite · uv · Pydantic v2  
**Run:** `uv run stride --port 8050` (or preview_start "stride" via launch.json)

---

## Current Git State

- **main** is the source of truth — always branch from here
- **PR #14** (`fix/ux-polish`) is open and ready to merge — do this FIRST
  - Fixes: category chip resetting, complete-task opens drawer, move flyout shows past dates
- **Rule:** NEVER push to main directly. Always branch → commit → PR → merge.
- **PR format:** Business summary first, Technical Detail second. No "Generated with Claude Code" footers.

---

## What's Already Built

| Phase | PR | What it does |
|-------|----|--------------|
| 1 | #3 | Python scaffold — uv + Dash boots |
| 2 | #10 | Board UI — 6 day columns, capacity bars, cards, topbar |
| 3 | #11 | Editable drawer, move flyout, counters, event timeline |
| 4 | #13 | HTML5 drag-and-drop across day columns |
| UX fix | #14 (open) | Category chip, complete-task drawer, past move dates |

### Key Architecture Points

- **Layout is a callable** (`app.layout = _layout`), not a static variable. Essential for multi-user.
- **store-tasks** is the single source of truth. Board re-renders from it; drawer reads from it.
- **Append-only event history** in `task_events` table. Every mutation writes an event row.
- **check_same_thread=False** on SQLite connection (Dash callbacks run in worker threads).
- **dcc.Store** pattern: JS writes via `window.dash_clientside.set_props`, server reads in callbacks.
- **Checkbox as sibling** of card div (not child) to prevent click bubbling — see card.py.
- **category_id** is in the Task Pydantic model and populated from DB row — don't omit it.

### File Map

```
stride/
  assets/
    stride.css          ← all styles
    dnd.js              ← HTML5 drag-drop event delegation
  migrations/
    0001_init.sql       ← 8-table schema (categories, tasks, task_events, etc.)
  services/
    tasks.py            ← create_task, list_tasks, get_task, move_task, toggle_done, update_task, delete_task
    seed.py             ← seed 5 tasks on first boot
  ui/
    app.py              ← create_app() factory, layout callable, callback registration
    theme.py            ← colour tokens, STRIDE_THEME dict
    components/
      topbar.py         ← week nav, Completed toggle
      board.py          ← 6 day columns, capacity bars
      card.py           ← task card with draggable, move flyout, checkbox as sibling
      detail.py         ← dmc.Drawer with all editable fields, counters, timeline
      composer.py       ← inline "Add task" form (hidden by default, fully wired)
    callbacks/
      board_cb.py       ← week nav, tick refresh, DnD drop, board re-render
      card_cb.py        ← card click → drawer, toggle done, move-to flyout
      detail_cb.py      ← populate drawer, blur-save title/desc, immediate-save chips
      composer_cb.py    ← show/hide composer, create_task on submit
  config.py             ← paths, OAUTH_REDIRECT_URI, FERNET_KEY_PATH
  db.py                 ← get_connection(), run_migrations(), app_db() singleton
  models.py             ← Task, TaskEvent, CalendarLink Pydantic models
  cli.py                ← Typer app, `uv run stride` entry point
docs/
  dash-guide.md         ← Dash learning guide (updated with Phase 3 & 4 by Haiku agent)
  phase-5-spec.md       ← Google Calendar sync spec
  phase-6-spec.md       ← Polish phase spec
tests/
  conftest.py           ← db fixture (in-memory SQLite)
  test_db.py            ← migrations + seed categories
  test_tasks.py         ← create, update, move, toggle, counters (6 tests, all pass)
```

---

## Long-term Vision (don't lose sight of this)

1. **Today:** Task board as the centre pane of a wide-screen dashboard
2. **Near-term panes:** Left = AI assistant, Right = aggregated email + diary
3. **Target user:** Professional developers on 27"+ widescreens — NOT mobile/tablet
4. **SaaS path:** Inexpensive hosting (Railway/Fly.io), multi-user auth, REST API layer
5. **Portfolio role:** Alan's consulting shop window AND a chargeable product

---

## Priority Order for Tomorrow

### 1. Merge PR #14 (5 min)
Go to GitHub, merge `fix/ux-polish` → main.

### 2. Phase 6 — Add Task Polish (branch: `feat/phase-6-composer-polish`)
The "+ Add task" button and composer are ALREADY wired (see `composer.py` + `composer_cb.py`).
What's needed is CSS polish + priority/category picker in the composer form.
See `docs/phase-6-spec.md` for full spec.

### 3. Phase 5 — Google Calendar Sync (branch: `feat/phase-5-gcal`)
Most complex phase. DB schema already has the tables. OAuth redirect URI already in config.py.
See `docs/phase-5-spec.md` for full spec.

### 4. Keyboard Shortcuts
JS listener in a new `keyboard.js` asset. Updates `store-kb-action` store. Server callback responds.
See Phase 6 spec.

### 5. Dash Guide
The Haiku agent is (or has) updated `docs/dash-guide.md` with Phase 3 & 4 patterns.
Commit that update at the start of the session.

---

## Tests to Write

Currently tests cover Phase 1 service layer only. No UI tests. Before Phase 5, add:
- `tests/test_composer.py` — create_task via service layer with category_id
- `tests/test_move.py` — move past/future filtering logic
- `tests/test_category.py` — category_id round-trips through model_dump()

---

## Known Gotchas

| Gotcha | How to handle |
|--------|---------------|
| `uv.lock` must be committed | Always `git add uv.lock` after dependency changes |
| PyCharm holds `stride.exe` | `Stop-Process -Name "stride" -Force` before uv commands |
| dmc.Drawer needs `keepMounted=True` | Otherwise callbacks can't find IDs before first open |
| category_id must be in Task model | `_row_to_task` must pass `category_id=row["category_id"]` |
| Drag events need delegation | Attach to document, not individual cards — Dash re-renders destroy listeners |
| `allow_duplicate=True` needed | Any Output written by multiple callbacks needs this |
| ChipGroup fires on populate | Read-before-write guard in save callbacks |
| PRs must target `main` | Use `gh pr create --base main` every time |
