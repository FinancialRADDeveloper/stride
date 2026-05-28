# Stride — Claude context

Personal day-lane task board. Dash (Python) frontend + SQLite backend, containerised for AWS App Runner.

## Commands

```bash
# Local dev (no Docker)
uv run stride                        # start on http://localhost:8050
uv run stride --debug                # hot-reload + Dash DevTools

# Tests
uv run pytest                        # all tests
uv run pytest tests/test_tasks.py    # single file
uv run ruff check stride/            # lint
uv run ruff format stride/           # format

# Docker
docker compose up -d                 # start (uses cached image)
docker compose build --no-cache stride && docker compose up -d  # rebuild + start
docker logs stride-stride-1 --follow # tail logs
docker logs stride-stride-1 --since 1m  # last-minute only (use to confirm requests hit Docker, not preview)

# Database (dev)
sqlite3 data/stride.db               # open REPL against local DB
```

## Architecture

```
stride/
  config.py          # env vars: DATA_DIR, STRIDE_SECRET, STRIDE_DEBUG
  db.py              # get_connection(), run_migrations(), app_db() singleton
  models.py          # Pydantic models: Task, Category, TaskEvent
  services/
    tasks.py         # pure service layer — no Dash imports; testable in isolation
    seed.py          # inserts sample data on first boot
  migrations/
    0001_init.sql    # schema: tasks, categories, task_events, calendar_accounts
    0002_assignee.sql
  ui/
    app.py           # create_app() — Dash app factory, layout, /health endpoint
    theme.py         # STRIDE_THEME dict for dmc.MantineProvider
    components/      # pure builders — return html.* / dmc.* trees, NO callbacks
      board.py       # week/day columns + card stacks
      card.py        # individual task card (draggable)
      topbar.py      # nav bar, view switcher, show-done toggle
      detail.py      # right-side edit drawer
      month_view.py  # month calendar grid
      composer.py    # "Add task" input
      reschedule_picker.py
    callbacks/       # all @app.callback definitions
      board_cb.py    # week navigation, task refresh, DnD drop, view modes
      card_cb.py     # card clicks, move-to, done toggle
      detail_cb.py   # drawer open/close, field saves, delete
      composer_cb.py # new task creation
      reschedule_cb.py
      kb_cb.py       # keyboard shortcut handling
      theme_cb.py    # dark/light toggle
  assets/            # Dash auto-loads *.js and *.css from here
    dnd.js           # HTML5 drag-and-drop → dcc.Store bridge
    keyboard.js      # global keyboard shortcuts (J/K/E/D)
    context_menu.js  # right-click context menu
    composer.js      # composer focus helpers
    autoreload.js    # polls /health, hard-refreshes on deploy
    stride.css       # all CSS (CSS variables for dark mode)
tests/
  conftest.py        # db fixture: in-memory SQLite with migrations applied
  test_tasks.py      # service-layer tests (no UI)
infra/
  bootstrap.cfn.yaml # one-shot CloudFormation: ECR, S3, OIDC, IAM roles
  bootstrap.sh       # run once to provision AWS infrastructure
  apprunner-deploy.sh # create-or-deploy an App Runner service
  wait-for-service.sh # poll App Runner until RUNNING
```

## Key patterns & gotchas

**Service layer is pure Python** — `stride/services/tasks.py` has zero Dash imports. Keep it that way. It must be callable from tests, CLI, and a future REST API without starting the Dash app.

**`app_db()` is per-thread** — uses `threading.local()`. Dash runs callbacks on a thread pool; never share a single connection across threads. Each callback that needs DB gets `conn = app_db()`.

**Adding a DB column** — always write a new `0003_*.sql` migration file. Never `ALTER TABLE` inline. The migration runner in `db.py` applies files in sorted order, exactly once.

**WAL mode is disabled** — `PRAGMA journal_mode = DELETE`. WAL requires Unix file-locking primitives that break on Windows Docker bind-mounts. Don't re-enable it without testing on the Docker volume path.

**DnD listeners use capture phase** — `dnd.js` adds all `addEventListener` calls with `true` (capture phase). React 18 delegates events to the root element; bubble-phase listeners at `document` never fire. This is the fix for "drag ghost appears but drop doesn't register".

**`dcc.Store` deduplication** — Dash skips callbacks when the new store value equals the old one. Any store write that might repeat identical data needs a `ts: Date.now()` field to force a change (see `store-dnd-drop`).

**`window.dash_clientside.set_props`** — the correct Dash 2.9+ API for writing to a component prop from vanilla JS without a Python round-trip. Used in `dnd.js` to trigger the drop callback.

**CSS variables for theming** — dark mode is handled by `[data-mantine-color-scheme="dark"]` selectors in `stride.css`. Use `var(--surface)`, `var(--text)`, `var(--border)` etc — do not hardcode hex colours in component Python.

**`data-task-id` / `data-drop-day`** — DnD anchors. Cards carry `data-task-id`; day columns carry `data-drop-day`. The JS reads these; changing their names breaks DnD silently.

**Board refresh pattern** — callbacks write task data into `store-tasks`. The render callback reads from the store and rebuilds the DOM. Never trigger a render callback directly from a mutation; mutate → refresh store → store triggers render.

**`include_done=True` always** — `list_tasks()` is always called with `include_done=True`. Filtering happens in the render callback based on `store-show-done`, not in SQL. Keeps store data consistent.

**Month view offset** — `_anchor_month(week_offset)` in `board_cb.py` derives `(year, month)` from a week offset relative to today. Don't compute month dates independently.

## State stores (dcc.Store ids)

| Store | Contents |
|-------|----------|
| `store-tasks` | `list[dict]` — current visible tasks |
| `store-week-offset` | `int` — weeks from today (0 = this week) |
| `store-view-mode` | `"week"` \| `"day"` \| `"month"` |
| `store-selected` | `task_id` of open detail drawer (or `None`) |
| `store-show-done` | `bool` |
| `store-dnd-drop` | `{task_id, to_day_key, ts}` — written by dnd.js |
| `store-reschedule-source` | `task_id` that opened the reschedule picker |
| `store-ctx-delete` | `task_id` to delete (written by context_menu.js) |
| `store-kb-action` | keyboard action string (written by keyboard.js) |
| `store-theme` | `"light"` \| `"dark"` |

## Environment variables

| Var | Default | Notes |
|-----|---------|-------|
| `DATA_DIR` | `./data` | SQLite lives at `$DATA_DIR/stride.db` |
| `STRIDE_SECRET` | required | Flask secret key |
| `STRIDE_DEBUG` | `false` | Set `true` for Dash hot-reload |
| `STRIDE_PORT` | `8050` | Override listen port |
| `LITESTREAM_REPLICA_URL` | unset | If set, Litestream replicates SQLite to S3 (production only) |

## Development workflow

**Branch → iterative commits → PR. Never commit a feature as one blob.**

Each branch is one feature. Within the branch, commit each logical increment separately so the history reads like a story:

```
feat: add achievements service (SQL query + stats logic)
feat: add achievements panel component shell + day-group layout
feat: wire achievements open/close callbacks
feat: add achievements CSS + dark mode support
feat: add Achievements button to topbar + register callbacks in app.py
```

This produces a PR whose commits a reviewer (or LinkedIn audience) can step through one at a time and follow the reasoning. It is not about commit volume — it is about logical boundaries.

**Never push directly to main.** Always branch → PR.  
**Always pull main before branching:** `git checkout main && git pull origin main && git checkout -b feat/...`

## AWS / deployment

See `infra/bootstrap.sh` for one-shot AWS setup.  
After bootstrap: set GitHub secrets `AWS_ACCOUNT_ID`, `STRIDE_SECRET_UAT`, `STRIDE_SECRET_PROD`.  
Create GitHub environment `production` with yourself as required reviewer.  
Push to main → CI builds + pushes to ECR → deploy.yml deploys UAT → you approve → Prod.

Domain: `takeitinyourstride.com` (Namecheap) — CNAME to App Runner Prod URL after first deploy.
