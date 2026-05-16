# Building Stride: A Developer's Build Log

Stride is a personal task board built around a simple insight: tasks belong to days, not lists. Not a Kanban board with stateless swim lanes — a time-anchored day-lane board where every card sits on a specific date, carries an estimate, ages visibly, and raises a flag when you've moved it three times without doing it. It's the tool I wanted when I was context-switching between consulting engagements and losing track of what mattered each day.

The stack is Python, Dash (Plotly's Flask-based UI framework), SQLite, Pydantic, and eventually Docker targeting AWS App Runner. I chose these deliberately: they let me move fast as a solo developer, keep hosting costs low enough for a personal tool that might become a product, and avoid the React complexity that kills side projects before they ship. This document traces every pull request from the first HTML prototype to a containerised, cloud-ready app — not as a victory lap, but as an honest record of the decisions, the dead ends, and what I'd do differently.

---

## Phase 0 — Design Before Code: The Prototype That Proved the Concept

Before writing a line of Python, I built a fully interactive prototype in plain HTML, React 18, and Babel Standalone — no build step, served with `python -m http.server`. The goal was to validate the UX concept before committing to an implementation stack.

The prototype (`Stride.html` and five JSX files) shipped as PR #1, and it did more than validate the concept — it defined the data model, the visual language, and the feature set that every subsequent PR had to match. Fifteen realistic seed cards with genuine history. A six-column day-lane board with capacity bars. Priority chips, size chips, category colour strips, stale ribbons after three moves. A detail panel with a full activity timeline.

The spec document that shipped alongside it — `Stride - Python Spec.md` — was the architectural blueprint: an eight-table SQLite schema, an append-only event log, Pydantic shapes for every entity, and a six-phase build plan with Claude Code session prompts.

One decision in that spec turned out to be load-bearing: **every mutation writes an event**. Not as a logging afterthought, but as the primary mechanism for derived data. Move count, edit count, stale detection, the activity timeline — all of them fall out of querying `task_events` rather than storing denormalised columns. At personal scale (hundreds of tasks, thousands of events) the aggregation cost is imperceptible. If it ever matters, a materialised view can be added without changing a single service function.

**What this unlocked:** a shared vocabulary between the prototype and the implementation. When I later needed to decide where a field lived, whether something needed a callback or could be clientside, or what the "correct" behaviour was — I could look at the prototype and the spec rather than guess.

> **LinkedIn version:** I built a fully interactive browser prototype before writing a single line of Python. It sounds like a detour, but defining the data model and UX in a zero-dependencies prototype saved me from the most expensive mistake in side projects: building the wrong thing fast. What's your preferred way to validate a concept before committing to a stack?

---

## Phase 1a — Moving Files and Getting the Scaffold Right

PR #2 and PR #3 solved a problem that sounds embarrassing in hindsight: the prototype's JSX files were living in `stride/`, which was the intended Python package root. The two folders were about to conflict.

The fix was mechanical — move `*.jsx` to `prototype/stride/`, update five `<script src>` paths in `Stride.html` — but the lesson was architectural: **clear the ground before you pour the foundation**. A thirty-minute housekeeping PR saved a week of confusing import errors later.

PR #3 delivered the Python walking skeleton: `pyproject.toml`, the `uv` lockfile, a Typer CLI entry point, and a Dash app that served a placeholder page. Nothing more.

```python
# stride/cli.py
@app.command()
def run(port: int = 8050, debug: bool = False):
    """Start the Stride web app."""
    from stride.ui.app import create_app
    dash_app = create_app()
    dash_app.run(port=port, debug=debug)
```

The dependency choices here are worth explaining. `uv` instead of pip or Poetry because it's fast and its `[dependency-groups]` format separates dev deps cleanly. Typer for the CLI because it generates `--help` text for free. Dash over FastAPI + React because I was the only developer — React's component ecosystem is powerful, but it's also a full-time job to maintain. Dash lets me write Python all the way down while still getting a reactive, server-rendered UI.

One thing that bit me: `uv.lock` was initially gitignored, which meant installs weren't reproducible. Fixed in this PR. Reproducibility is non-negotiable before you write any business logic — it's the difference between "works on my machine" and "works on any machine."

**What this unlocked:** a known-good baseline for every subsequent feature branch. Every PR after this one started with `uv sync && uv run stride` as the first verification step.

> **LinkedIn version:** The most important commit in any side project is the walking skeleton — the moment you can `git clone; run one command; see something in your browser`. I spent half a day just on this, and it paid dividends every single day after. What's the first command you run when starting a new project?

---

## Phase 1b — The Database That Would Never Need a Schema Migration (Until It Did)

PR #5 delivered the full SQLite schema and migration runner. Eight tables: `categories`, `tasks`, `task_events`, `calendar_accounts`, `calendars`, `calendar_links`, `oauth_tokens`, `settings`. Written once as `0001_init.sql` with `IF NOT EXISTS` guards throughout so it was idempotent.

The migration runner itself was a deliberate non-framework choice:

```python
def run_migrations(conn: sqlite3.Connection) -> None:
    migration_files = sorted(Path(MIGRATIONS_DIR).glob("*.sql"))
    for path in migration_files:
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
```

No Alembic, no Flyway — just glob `*.sql` in sorted order and run each via `executescript`. Diff-friendly, readable without tooling, easy to explain to anyone who opens the repo. The `0001_`, `0002_` naming convention gives you ordering for free.

Two decisions in the schema that I'd make again: WAL journal mode (`PRAGMA journal_mode = WAL`) lets the UI read while a background scheduler writes. Foreign keys enforced (`PRAGMA foreign_keys = ON`) with `ON DELETE CASCADE` on `task_events` so deleting a task cleans up its history automatically.

The test fixture was an in-memory SQLite connection with migrations applied — every subsequent test in the suite inherits this pattern. Two tests: `test_migrations_apply` (all eight tables exist) and `test_seed_categories` (six category rows, correct slugs). Small, fast, and they caught a real breakage three PRs later.

What I didn't anticipate: the migration runner would need to track which files had already run. That came back to bite me in PR #16.

**What this unlocked:** a transaction-safe connection singleton that any callback in the Dash app could call with `app_db()`. No ORMs, no magic — just `conn.execute()` inside `with conn:` blocks.

> **LinkedIn version:** I chose stdlib `sqlite3` with plain `.sql` files over an ORM, and I'd make the same choice again. For a personal tool, an ORM adds complexity without adding safety — SQLite with WAL mode, foreign keys, and a ten-line migration runner is 80% of what you actually need. What's the simplest database setup you've shipped to production?

---

## Phase 1c — The Service Layer: Where Business Logic Lives

PR #6 was the one that made the architecture real. Six service functions, Pydantic v2 models, and six tests that spec out the exact behaviour of the event log.

The key design: **no callback ever touches the database directly**. Every mutation goes through a service function that validates inputs, writes the task row, appends event rows, and returns a hydrated `Task` Pydantic model — all in one SQLite transaction.

```python
def update_task(conn, task_id, **fields) -> Task:
    invalid = set(fields) - _EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Cannot update field(s) via update_task: {invalid}")
    # ...
    for field, old_value, new_value in changed:
        _append_event(conn, task_id, "edited",
                      {"field": field, "from": old_value, "to": new_value})
```

One `edited` event per changed field. That means if you update title, priority, and size in one save, you get three events with precise field-level diffs — not a single "updated" blob. The activity timeline in the drawer surfaces these as human-readable entries: `priority: 'P2' → 'P3'`.

The `move_task` no-op guard was also important: if a task is already on the target day, return it unchanged and write zero events. Without this, drag-and-drop misdrops would silently inflate the move counter and trigger stale detection.

The six tests match the spec exactly:
- `test_create_writes_one_event` — a created task has exactly one event
- `test_update_writes_per_field_events` — three-field update produces three edited events
- `test_move_same_day_is_noop` — no event written for a same-day move
- `test_move_cross_day_writes_event` — cross-day move writes one moved event with from/to
- `test_derived_counts` — move_count and edit_count are correct after a mixed sequence
- `test_toggle_done_sequence` — three toggles produce done → reopened → done

These tests became the safety net for every refactor in later PRs.

**What this unlocked:** the Phase 2 board UI could be built against a clean, tested service API without worrying about database correctness. The UI team (which was also me, one session later) trusted the service layer completely.

> **LinkedIn version:** The best architectural decision I made was: no UI code touches the database. Every mutation goes through a service function that validates, writes, appends events, and returns a typed model — all in one transaction. It sounds obvious, but most side projects skip this and pay for it in untraceable bugs. Where do you draw the line between UI and data layer?

---

## Phase 2 — The Board That Didn't Have Duplicate ID Errors

PR #10 was the biggest single PR in the project. Ten new files, the full Phase 2 board UI. Five day columns, capacity bars, task cards with category strips and priority chips, an inline composer, a read-only detail drawer, week navigation, and a seed that populated five realistic tasks on first boot.

The first problem I hit was Dash's duplicate-ID error. When you put pattern-matched component IDs in both the initial layout and a callback output, Dash complains that it can't reconcile them. The fix: ship the board as an empty `board-inner` shell in the layout, and let a callback populate it:

```python
# app.py — the initial layout has NO board content
html.Div(
    html.Div(className="board-inner", id="board-inner"),
    className="board",
    id="board",
)

# board_cb.py — the callback renders the full board
@app.callback(Output("board-inner", "children"), Input("store-tasks", "data"), ...)
def render_board_from_store(tasks, show_done, week_offset):
    filtered = tasks if include_done else [t for t in tasks if not t.get("done")]
    rendered = render_board(tasks=filtered, week_offset=week_offset or 0)
    return rendered.children.children  # the column list
```

This pattern — empty shell in layout, callback-rendered content — became the standard for anything with pattern-matched IDs. Violate it and you get cryptic Dash errors that take an afternoon to trace.

The second decision was `check_same_thread=False` on the SQLite connection. Dash runs callbacks in worker threads; without this flag, SQLite raises an error because the connection was created on the main thread. It's a one-liner, but it's the kind of thing that breaks silently in the wrong context.

The third decision: all state lives in `dcc.Store` components, not in module-level variables. This matters for multi-user deployments — Dash's default server doesn't guarantee that the same process handles the same user's requests. Stores are per-session; module variables are per-process. Getting this wrong means users see each other's state.

The capacity bar was a UX decision I'm happy with. Each day column shows a soft 8-hour (480-minute) limit. Bars are green below 75%, amber to 100%, red when over. It makes overcommitment visible without being prescriptive.

**What this unlocked:** a working board that could be demoed. Everything before this was infrastructure; this was the first thing you could actually use.

> **LinkedIn version:** The most counterintuitive thing about building a Dash UI is that the initial layout and the callback-rendered layout can't share component IDs — which means you have to ship an empty shell and let callbacks fill it. Once you understand this rule, the whole framework clicks. What's the mental model shift that made your primary framework finally make sense?

---

## Phase 3 — Making Every Card Actually Do Something

Phase 2 cards were read-only. You could look at them, navigate the week, add new tasks. But editing required opening a drawer that couldn't save. PR #11 changed that.

The editable drawer (Phase 3) involved eight callbacks: populate the drawer when a card is clicked, save on blur for text fields, save immediately on change for pickers (priority, size, category), with one guard I'm particularly glad I added:

```python
def save_category(new_val, task_id):
    # Suppress spurious fires when populate_detail sets the ChipGroup value
    current = conn.execute("SELECT category_id FROM tasks WHERE id=?", (task_id,)).fetchone()
    if current and current["category_id"] == new_val:
        return no_update
    update_task(conn, task_id, category_id=new_val)
```

Without this guard, every time the drawer opened and populated the category chip, it would fire the save callback and write an "edited" event for a field that hadn't changed. The activity timeline would fill with phantom edits.

The move-to flyout was a CSS-only hover reveal rather than a Mantine `dmc.Menu` component. This was a deliberate choice: Mantine's compound components (Menu, Popover, etc.) use React Context to pass state between parent and child. When Dash wraps those children in its own component tree — which it does for pattern-matched IDs — the Context chain breaks and the children don't render. A CSS `:hover` approach sidesteps the problem entirely and is simpler to maintain.

The `keepMounted=True` prop on `dmc.Drawer` deserves a mention. Without it, Dash can't wire callback IDs to drawer children before the drawer is first opened. The first open works; subsequent ones error. Setting `keepMounted` means the drawer's DOM exists from page load, invisible, so Dash can register all its callback outputs before any user interaction.

The delete function wrote to a `deleted_tasks` tombstone table before cascading. The `try/except` around the tombstone write was pragmatic: older schemas might not have the table yet, and a delete should never fail because of an audit concern.

**What this unlocked:** a board where you could actually work. The Phase 2 board was a demo; Phase 3 was usable.

> **LinkedIn version:** The hardest bugs to track down in a reactive UI framework are the ones caused by "spurious fires" — callbacks that trigger on initialisation rather than user action. The fix is almost always a guard that compares the incoming value to the current state before writing. How do you handle the initialisation vs. interaction problem in your reactive UI work?

---

## Phase 4 — Drag and Drop Without a Drag-and-Drop Library

PR #13 added drag-and-drop using HTML5 native events and zero additional dependencies. No `react-beautiful-dnd`, no `@dnd-kit`, nothing. The full implementation is 67 lines of vanilla JavaScript.

The core bridge between JavaScript and Dash:

```javascript
document.addEventListener('drop', function (e) {
  var col = e.target.closest('[data-drop-day]');
  if (!col || !dragging) return;
  e.preventDefault();
  col.classList.remove('day-column--drop-active');
  var toDay = col.dataset.dropDay;
  // Write into the Dash store without a server round-trip
  window.dash_clientside.set_props('store-dnd-drop', {
    data: { task_id: dragging, to_day_key: toDay }
  });
  dragging = null;
});
```

`window.dash_clientside.set_props` is a Dash 2.9+ API that lets JavaScript write directly into a `dcc.Store` from the browser. A Python callback listens to that store and calls `move_task`. One JavaScript event → one server round-trip → board refreshed. Clean.

The deferred `.dragging` class is a subtlety worth noting. If you add the class immediately on `dragstart`, the drag ghost — the semi-transparent copy Dash shows while you're dragging — captures the dimmed version. Wrapping the class assignment in `setTimeout(fn, 0)` defers it until after the ghost is captured, so the ghost shows the undimmed card.

Event delegation (attaching listeners to `document` rather than individual cards) was essential because the board re-renders on every store update. If you attach listeners to individual elements, they disappear when the element is replaced by a re-render. Document-level listeners survive re-renders by design.

The `data-drop-day` attribute goes on the outer column div (the full column including header), not just the card stack. This means you can drop onto the column header and empty areas — a much more forgiving drop target that matches how users actually behave.

**What this unlocked:** the board felt like a tool rather than a form. Being able to grab a card and throw it to tomorrow is the interaction that makes the day-lane model click in practice.

> **LinkedIn version:** I added drag-and-drop to a Dash app without using a drag-and-drop library — just 67 lines of vanilla JavaScript using HTML5 native events and the `dash_clientside.set_props` API. Sometimes the "obvious" dependency isn't the simplest solution. When did avoiding a library pay off for you?

---

## Phase 5 — Three UX Bugs That Were Actually Architecture Bugs

PR #14 fixed three bugs that looked like UI issues but were each rooted in an architectural oversight.

**Bug 1: Category chip resetting on every save.** Every time a task was saved, the category chip snapped back to "Personal". The cause: `category_id` was missing from the `Task` Pydantic model entirely. It was in the database, it was in the seed, but `_row_to_task` never populated it. When `store-tasks` refreshed from the DB, every task's category came back as the default. Fix: add `category_id: str = "personal"` to the model and populate it from the row. One line in the model, one line in the service. The missing field had propagated silently through four phases of development.

**Bug 2: Completing a task opened the detail drawer.** Click the checkbox — drawer opens. This happened because the checkbox was a child of the card div that tracked `n_clicks` for the drawer-open callback. Click on the child, event bubbles up through the parent, parent's `n_clicks` increments, drawer opens. Fix: move the checkbox to be a sibling of the card div inside the wrapper, and use CSS absolute positioning to keep it visually in the same place. The DOM structure and the visual structure diverged intentionally.

**Bug 3: Move-to flyout showing past dates.** The flyout listed all six visible week days, including Tuesday when it was Thursday. Filtering to `day >= today` in the card component was a one-line fix, but the bug revealed a general principle: never show the user an action that can't produce a meaningful result.

All three bugs were caught by using the app, not by writing tests. This is the honest reality of UI development: automated tests catch logic errors in service functions; actual usage catches the interaction design mistakes that tests can't model.

**What this unlocked:** a board that didn't subtly mislead users. Each of these bugs was small, but each one eroded trust in the tool. Fixing all three in one pass was worth the focused effort.

> **LinkedIn version:** The three bugs I fixed last week all had the same root cause: a mismatch between what the data model claimed and what the UI expected. Pydantic models are great for catching type errors; they don't catch missing fields. Where does your type system fall short?

---

## Phase 6 — Polish, Dark Mode, and the Zombie That Ate My Afternoon

PR #15 was supposed to be a quick polish pass: add priority/size/category pickers to the task composer, add a dark mode toggle, add keyboard shortcuts. It turned into a multi-session debugging exercise because of a Dash behaviour I hadn't encountered before.

The pickers in the composer (`dmc.SegmentedControl` for Priority, Size, Category) were initially listed as `Output` in a `reset_composer` callback that cleared them after a task was submitted. Listing them as Outputs caused Dash to strip those components from the board's dynamic render response — a "component pruning" behaviour where outputs in one callback can't also be dynamic children of another. The fix was to change the pickers from `Output` to `State`: read their values at submit time rather than writing to them on reset.

The real debugging pain came from a zombie process. `preview_start` (the Claude Code browser preview tool) silently reconnects to an existing process on port 8050 rather than starting a new one. I'd been iterating on the Phase 6 code for an hour before realising the browser was still talking to the Phase 5 process from a previous session. Every change I made appeared to have no effect. The fix: kill the old PID explicitly before trusting the browser.

The keyboard shortcuts used the same `set_props` pattern as drag-and-drop:

```javascript
// keyboard.js
switch (e.key) {
  case 'Escape': action = 'close';       break;
  case 'd':      action = 'toggle-done'; break;
  case 'e':      action = 'open-drawer'; break;
}
window.dash_clientside.set_props('store-kb-action', {
  data: { action: action, ts: Date.now() }
});
```

The `ts: Date.now()` is necessary: if the user presses `d` twice in quick succession, the action value doesn't change, so Dash's store update doesn't fire. Including a timestamp ensures the store value always changes, which always triggers the callback.

Dark mode was three lines: add `forceColorScheme` to `MantineProvider`, give it a stable `id`, toggle it from a callback. Mantine's CSS variables propagate the theme automatically; custom rules live under `[data-mantine-color-scheme="dark"]`.

**What this unlocked:** a board that felt complete as a daily-use tool. The keyboard shortcuts in particular — Escape to close the drawer, `d` to complete a task — are the difference between a tool you use and a tool you demo.

> **LinkedIn version:** I lost two hours to a zombie server process — a stale background process that silently intercepted browser requests while I was convinced my code changes weren't working. The lesson: always verify your server process is the one you think it is before debugging the code. What's the most embarrassing debugging story you're willing to share?

---

## Phase 7 — The Rolling Window That Changed How the Board Feels

PR #16 addressed a UX problem I'd been tolerating for weeks: on Friday afternoon, the "this week" view showed Monday through Saturday, with today in column five and only one future day visible. On Saturday, it was worse: today was the last column, no future visible at all.

The fix was in `_week_days()`:

```python
def _week_days(week_offset: int) -> list[datetime.date]:
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    start = monday + datetime.timedelta(days=6 * week_offset)
    if week_offset == 0:
        end = today + datetime.timedelta(days=5)
        n = max(6, (end - monday).days + 1)
    else:
        n = 6
    return [start + datetime.timedelta(days=i) for i in range(n)]
```

For offset 0 (this week), the window now always extends to today + 5, regardless of the current weekday. On a Saturday, you see today through the following Thursday. On a Monday, you see Monday through Saturday — the same as before. The minimum column count is six; on late-week days it grows dynamically. Past days with no tasks are hidden entirely, so the board always opens on something actionable.

This PR also addressed the migration tracking gap from Phase 1b. The `_applied_migrations` table now records each SQL file after it runs:

```python
already = conn.execute(
    "SELECT 1 FROM _applied_migrations WHERE name = ?", (name,)
).fetchone()
if already:
    continue
```

The `ALTER TABLE tasks ADD COLUMN assignee TEXT` migration in `0002_assignee.sql` would crash on restart because `executescript` tried to add a column that already existed. With migration tracking, each file runs exactly once. The `duplicate column name` catch handles the one-time bootstrap: existing installations that ran `0002` before the tracking table existed need a graceful fallback.

The `assignee` field itself — the "Delegated to" field in the drawer, the `→ FirstName` chip on cards — was a clean vertical slice: SQL migration, model field, service layer, UI field, callback, card chip. Seven touch points for one feature, which is why the service/model boundary matters: each layer has exactly one job.

**What this unlocked:** a board that feels correct regardless of which day you open it. Small UX details like this are the difference between a tool that delights and a tool that's merely functional.

> **LinkedIn version:** The most important UX feature I shipped this month was not a feature — it was fixing the day-window algorithm so the board always shows at least five future days. Users don't complain about missing future days; they just feel vaguely anxious without knowing why. Good tools remove that anxiety without announcing themselves. What's the smallest change that most improved a product you've worked on?

---

## The Container: From `localhost` to Cloud-Ready

With the board stable and usable, the natural next step was containerisation — both for reproducibility and for the path to a hosted product.

The Dockerfile is 22 lines:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY stride/ stride/

ENV DATA_DIR=/data
RUN mkdir -p /data

EXPOSE 8050
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health')" || exit 1

CMD ["uv", "run", "stride"]
```

Three deliberate choices. First, `uv sync --frozen --no-dev` at the `pyproject.toml` layer — so the dependency installation layer is cached unless dependencies change, not unless source code changes. Source changes don't invalidate the cache. Second, `ENV DATA_DIR=/data` with a separate volume mount point — the SQLite file lives outside the image layer so it survives container restarts and image updates. Third, the `/health` endpoint added to the Flask app so App Runner and docker-compose healthchecks have a meaningful signal.

The health endpoint is four lines in `app.py`:

```python
@app.server.route("/health")
def health():
    return jsonify({"status": "ok"}), 200
```

Dash exposes the underlying Flask app via `app.server`, so adding Flask routes alongside Dash callbacks is seamless. This is one of the underappreciated advantages of Dash over a pure React frontend: the Python backend is just Flask, and you can do anything Flask can do.

**What this unlocked:** a `docker compose up` workflow for local development and a clear path to AWS App Runner for hosting. The same image that runs locally runs in production.

> **LinkedIn version:** The Dockerfile for a Python app with uv is 22 lines. The key insight: copy pyproject.toml and uv.lock first, run `uv sync --frozen`, then copy the source. Source changes don't bust the dependency cache. It sounds obvious but most Python Dockerfiles get this wrong. What's your favourite Docker optimisation?

---

## What's Next

The board works. The container runs. The path to AWS App Runner is clear: push the image, configure the SQLite volume (EFS for persistence), set `STRIDE_SECRET` and `DATA_DIR` environment variables, and the `/health` endpoint handles the readiness probe.

Three things are next on the roadmap, in order of impact:

**Google Calendar sync** is already scaffolded in the schema — `calendar_accounts`, `calendars`, `calendar_links`, `oauth_tokens` are all there. The OAuth flow and sync loop are the missing pieces. The design: tasks can be linked to Google Calendar events. Moving a task changes its calendar date. Changes in Google Calendar pull back into Stride. The `origin` field on `calendar_links` tracks which system owns the event.

**Multi-user and auth** are the transition from personal tool to hosted product. The current singleton `app_db()` is appropriate for single-user; multi-user needs per-session database isolation or a proper user table with row-level filtering. The Dash layout function is already `lambda`-based (multi-user safe for store state); the database layer is the gap.

**Recurring tasks** — there's a comment in `0001_init.sql`: `-- TODO (v0.2): add recurrence_rule TEXT to support recurring tasks without schema rewrite`. The event log makes recurrence tractable: generate future instances lazily from the recurrence rule when building the board window, rather than materialising them in the database.

The architecture held up. Pydantic caught type errors. The event log kept history honest. SQLite survived everything I threw at it. Dash's callback model was occasionally maddening but ultimately the right call for a solo Python developer building a UI-heavy tool.

The code is public at [github.com/FinancialRADDeveloper/stride](https://github.com/FinancialRADDeveloper/stride).
