# Stride — Python Build Spec

> Personal day-lane task board. Single user, one machine, lives in a Python venv.
> Companion to the HTML prototype in this project (`Stride.html`) — that's the
> visual + interaction source of truth; this doc translates it into a buildable
> Python application.

**Stack:** Dash · SQLite · Google Calendar (two-way OAuth) · `uv` for env mgmt
**Target runtime:** localhost only, run via `uv run stride` from `self-organisation/`
**Deliverable in this spec:** enough detail that an AI coding assistant (Claude Code) can scaffold and build the first running version without further design clarification.

---

## 1. Philosophy & non-goals

Stride is a **personal organising tool**, not a team product. That shapes everything:

- **Single user, single device.** No auth on the app itself. Filesystem permissions are the security boundary. OAuth is only for Google's API.
- **Local-first.** SQLite file in the repo. No network needed except for the calendar sync loop.
- **History is first-class.** Every meaningful change writes an event row. Nothing about a card is reconstructable from a snapshot alone.
- **Friction matters more than features.** If a feature can't be hit in two clicks or one keyboard shortcut, it shouldn't ship in v0.1.
- **Honest stale-ness.** Cards that get pushed forward repeatedly should look more uncomfortable, not less. The UI surfaces age + move count deliberately.

**Explicit non-goals for v0.1:** projects/labels, search, recurring tasks (other than manual duplication), subtasks, mobile UI, multi-user, attachments, notifications. All are reasonable v0.2+ candidates but are out of scope here.

---

## 2. Tech stack — what each piece is for

| Piece | Library | Why |
|---|---|---|
| Web framework | `dash >= 2.17` | Python-native UI, callback model is a good fit for a dashboard-style app, no separate JS build step |
| UI primitives | `dash-mantine-components >= 0.14` | Polished components (Modal, Drawer, Menu, ColorPicker, TimeInput) that match the Stride aesthetic better than vanilla Dash |
| Pattern callbacks | `dash` builtin | Per-card and per-column callbacks via `MATCH` / `ALL` selectors |
| Drag & drop | Clientside callback + HTML5 DnD | Dash has no first-class DnD. We add a tiny `assets/dnd.js` that handles native HTML5 drag events and writes to a `dcc.Store`, then a server callback persists. Details in §6. |
| Database | `sqlite3` (stdlib) | One file, zero setup, perfect for personal scale. Migrations via plain SQL files in `migrations/`. |
| Schema/types | `pydantic >= 2.0` | Validate inputs and shape outbound JSON for `dcc.Store` |
| Date/time | `pendulum` | Saner timezone handling than `datetime`. All timestamps stored UTC ms; rendered in local TZ. |
| Background work | `apscheduler` (BackgroundScheduler) | One thread, runs calendar sync every N minutes |
| Google API | `google-api-python-client`, `google-auth-oauthlib` | Standard library for GCal access |
| Token storage | SQLite + `cryptography.fernet` | Encrypt refresh tokens with a key derived from a passphrase or `STRIDE_SECRET` env var |
| Tests | `pytest`, `pytest-asyncio` | The non-UI parts (services, sync) must be tested. UI is exercised manually. |
| Lint/format | `ruff` | Single tool, fast |
| Env / runner | `uv` | Matches the AI-first workflow in `project-settings.md` |

> **Note on drag-and-drop:** the simplest viable choice. If `dash-mantine-components` adds a stable `Sortable` we can swap to it. Avoid bringing in React directly — that defeats the purpose of choosing Dash.

---

## 3. Repository layout

Sits inside `self-organisation/`:

```
self-organisation/
├── stride/                       # python package
│   ├── __init__.py
│   ├── __main__.py               # `python -m stride` entry
│   ├── cli.py                    # typer/argparse CLI: run, sync, db
│   ├── config.py                 # paths, env, settings dataclass
│   ├── db.py                     # connection, migrations, low-level helpers
│   ├── models.py                 # pydantic models: Task, TaskEvent, CalendarLink
│   ├── services/
│   │   ├── __init__.py
│   │   ├── tasks.py              # CRUD + history recording (the heart)
│   │   ├── calendar.py           # GCal OAuth + push/pull + reconcile
│   │   └── scheduler.py          # apscheduler bootstrapping
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py                # Dash app construction + register callbacks
│   │   ├── theme.py              # color tokens + CSS variables
│   │   ├── layout.py             # top-level layout(): TopBar + Board + Drawer
│   │   ├── components/
│   │   │   ├── topbar.py
│   │   │   ├── board.py
│   │   │   ├── column.py
│   │   │   ├── card.py
│   │   │   ├── composer.py
│   │   │   └── detail.py
│   │   └── callbacks/
│   │       ├── board_cb.py       # day navigation, show-done toggle
│   │       ├── card_cb.py        # select, toggle done, drag-drop
│   │       ├── composer_cb.py    # add task
│   │       └── detail_cb.py      # edit fields, link calendar, delete
│   ├── assets/                   # served at /assets/*; CSS, fonts, JS
│   │   ├── stride.css
│   │   ├── geist.woff2 (+others)
│   │   └── dnd.js                # clientside DnD glue
│   └── migrations/
│       ├── 0001_init.sql
│       └── 0002_add_calendar_links.sql
├── data/
│   ├── stride.db                 # gitignored
│   └── client_secret.json        # GCal OAuth creds — gitignored
├── tests/
│   ├── test_tasks.py
│   ├── test_history.py
│   └── test_calendar_sync.py
├── pyproject.toml
├── uv.lock
└── README.md
```

Notes:
- `assets/` is Dash's magic folder — anything in it is auto-served at `/assets/`.
- `data/` is git-ignored. The DB file ships empty; first run creates it via migrations.
- `client_secret.json` is the OAuth client credentials, downloaded by the user from Google Cloud Console.

---

## 4. Data model

### Source of truth

`data/stride.db` — a single SQLite file. WAL mode on for concurrent reader (the UI) and writer (sync loop).

### Tables

```sql
-- categories: user-defined buckets (Build, Home, Work, …)
CREATE TABLE categories (
  id           TEXT PRIMARY KEY,                 -- 'build', 'home', etc — stable
  name         TEXT NOT NULL,                    -- editable
  color        TEXT NOT NULL,                    -- hex
  sort_order   INTEGER NOT NULL DEFAULT 0,
  created_at   INTEGER NOT NULL
);
-- Seeded on first run with: build, work, home, admin, health, personal.

-- tasks: one row per card
CREATE TABLE tasks (
  id              TEXT PRIMARY KEY,             -- 'c' + ulid()
  title           TEXT NOT NULL,
  description     TEXT NOT NULL DEFAULT '',
  priority        TEXT NOT NULL CHECK (priority IN ('P1','P2','P3','P4')),
  size            TEXT NOT NULL CHECK (size IN ('XS','S','M','L','XL')),
  category_id     TEXT NOT NULL REFERENCES categories(id),
  estimate_min    INTEGER,                      -- nullable; defaults from size on create
  time_of_day     TEXT,                         -- 'HH:MM' or NULL
  day_key         TEXT NOT NULL,                -- 'YYYY-MM-DD'
  done            INTEGER NOT NULL DEFAULT 0,
  created_at      INTEGER NOT NULL,             -- unix ms
  updated_at      INTEGER NOT NULL              -- unix ms
);
CREATE INDEX idx_tasks_day_key ON tasks(day_key);
CREATE INDEX idx_tasks_category ON tasks(category_id);
CREATE INDEX idx_tasks_done ON tasks(done);

-- task_events: append-only history
CREATE TABLE task_events (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  ts         INTEGER NOT NULL,                  -- unix ms
  kind       TEXT NOT NULL,                     -- see §5
  payload    TEXT NOT NULL DEFAULT '{}'         -- JSON blob
);
CREATE INDEX idx_events_task ON task_events(task_id, ts);

-- calendar_accounts: connected providers
CREATE TABLE calendar_accounts (
  id           TEXT PRIMARY KEY,                 -- 'acc_' + ulid()
  provider     TEXT NOT NULL CHECK (provider IN ('google','outlook')),
  email        TEXT NOT NULL,
  label        TEXT NOT NULL,                    -- user-renamable, eg 'Personal Google'
  connected_at INTEGER NOT NULL,
  disabled_at  INTEGER
);
CREATE UNIQUE INDEX idx_accounts_email ON calendar_accounts(provider, email);

-- calendars: sub-calendars under each account (mirrors GCal sidebar)
CREATE TABLE calendars (
  id           TEXT PRIMARY KEY,                 -- provider's id (eg gcal calendarId)
  account_id   TEXT NOT NULL REFERENCES calendar_accounts(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  color        TEXT NOT NULL,                    -- hex
  role         TEXT NOT NULL CHECK (role IN ('owner','writer','reader')),
  visible      INTEGER NOT NULL DEFAULT 1,       -- whether to show on board background
  sort_order   INTEGER NOT NULL DEFAULT 0,
  last_synced_at INTEGER
);
CREATE INDEX idx_calendars_account ON calendars(account_id);

-- calendar_links: 1:1 with tasks that are pushed to a specific calendar
CREATE TABLE calendar_links (
  task_id          TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
  calendar_id      TEXT NOT NULL REFERENCES calendars(id),
  google_event_id  TEXT NOT NULL,                -- works for outlook too; semantic id
  etag             TEXT,
  last_pushed_at   INTEGER,
  last_pulled_at   INTEGER,
  origin           TEXT NOT NULL CHECK (origin IN ('stride','imported'))
);
CREATE UNIQUE INDEX idx_links_event ON calendar_links(calendar_id, google_event_id);

-- oauth_tokens: encrypted, one row per (provider, account)
CREATE TABLE oauth_tokens (
  account_id        TEXT PRIMARY KEY REFERENCES calendar_accounts(id) ON DELETE CASCADE,
  access_token_enc  BLOB NOT NULL,
  refresh_token_enc BLOB NOT NULL,
  expires_at        INTEGER NOT NULL,
  scope             TEXT NOT NULL,
  updated_at        INTEGER NOT NULL
);

-- settings: free-form key/value. Known keys:
--   task_target_personal_calendar_id  TEXT  — which calendar receives "Personal" pushes
--   task_target_shared_calendar_id    TEXT  — which calendar receives "Shared" pushes
--   home_timezone                     TEXT  — eg 'Europe/London'
--   stale_move_threshold              INTEGER (default 3)
--   day_capacity_minutes              INTEGER (default 480)
CREATE TABLE settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL                            -- JSON
);
```

### Derived fields (computed, not stored)

These are computed in the service layer per task; **do not denormalize**.

| Field | Definition |
|---|---|
| `move_count` | `COUNT(*) FROM task_events WHERE kind='moved' AND task_id=?` |
| `edit_count` | `COUNT(*) FROM task_events WHERE kind='edited' AND task_id=?` |
| `age_days` | `(today_local - date(created_at_local))` in days |
| `is_stale` | `move_count >= 3 AND done = 0` |
| `calendar_linked` | `EXISTS row in calendar_links` |

Cache these on the `Task` pydantic model when reading; the UI never queries directly.

### Pydantic shapes

```python
class TaskEvent(BaseModel):
    id: int
    task_id: str
    ts: int                          # unix ms
    kind: Literal['created','moved','edited','done','reopened','scheduled','unscheduled','deleted']
    payload: dict[str, Any] = {}

class CalendarLink(BaseModel):
    calendar_id: str
    google_event_id: str
    etag: str | None
    last_pushed_at: int | None
    last_pulled_at: int | None
    origin: Literal['stride','google']

class Task(BaseModel):
    id: str
    title: str
    description: str = ''
    priority: Literal['P1','P2','P3','P4'] = 'P3'
    size: Literal['XS','S','M','L','XL'] = 'M'
    estimate_min: int | None = None
    time_of_day: str | None = None       # 'HH:MM'
    day_key: str                          # 'YYYY-MM-DD'
    done: bool = False
    created_at: int
    updated_at: int
    # computed
    move_count: int = 0
    edit_count: int = 0
    age_days: int = 0
    is_stale: bool = False
    calendar: CalendarLink | None = None
    history: list[TaskEvent] = []         # only loaded when full=True
```

### Constants (mirror the prototype)

```python
SIZE_MINUTES = {'XS': 10, 'S': 25, 'M': 60, 'L': 120, 'XL': 240}
SIZE_HINT    = {'XS': '<15m', 'S': '~25m', 'M': '~1h', 'L': '~2h', 'XL': 'half day'}
PRIORITY_LABEL = {'P1': 'Critical', 'P2': 'High', 'P3': 'Normal', 'P4': 'Low'}
DAY_CAPACITY_MIN = 480   # soft 8h
STALE_MOVE_THRESHOLD = 3
```

---

## 5. The history protocol — what writes an event, and what it contains

Every mutation goes through `services/tasks.py`. **Mutations never touch the DB directly from callbacks.** Every public service function:

1. Loads the task,
2. Validates the change,
3. Writes the new task row (`updated_at = now`),
4. Appends the matching event(s),
5. Returns the refreshed `Task` pydantic model.

All five steps run in one SQLite transaction.

### Event kinds and their payloads

| `kind` | When | `payload` shape |
|---|---|---|
| `created` | New task inserted | `{ "snapshot": <task as dict at creation> }` |
| `moved` | `day_key` changes | `{ "from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "from_label": "Mon May 11", "to_label": "Today" }` |
| `edited` | Any of: title, description, priority, size, estimate_min, time_of_day | `{ "field": "title", "from": "...", "to": "..." }` — one event per field changed in a save |
| `done` | `done` flips false → true | `{}` |
| `reopened` | `done` flips true → false | `{}` |
| `scheduled` | calendar_links row created | `{ "calendar_id": "primary", "google_event_id": "...", "origin": "stride" }` |
| `unscheduled` | calendar_links row deleted | `{ "google_event_id": "..." }` |
| `deleted` | Task row deleted | `{}` (cascade will remove other events; this one is kept for audit via a separate `deleted_tasks` table — see below) |

> **Tombstones.** When a task is deleted, copy the latest snapshot into a `deleted_tasks` table before cascading. Lets us undo and lets calendar reconcile know "the user really did delete this".

### Service function signatures

```python
# tasks.py — these are the only entry points UI may call

def create_task(*, title, day_key, priority='P3', size='M',
                description='', estimate_min=None, time_of_day=None) -> Task: ...

def update_task(task_id: str, **fields) -> Task:
    """
    Accepts any subset of: title, description, priority, size, estimate_min,
    time_of_day. Writes one 'edited' event per changed field.
    Does NOT accept day_key (use move_task) or done (use toggle_done).
    """

def move_task(task_id: str, to_day_key: str) -> Task:
    """Updates day_key, increments implicit move_count via event."""

def toggle_done(task_id: str) -> Task: ...

def delete_task(task_id: str) -> None: ...

def list_tasks(*, day_keys: list[str] | None = None,
               include_done: bool = True,
               full: bool = False) -> list[Task]:
    """If full, also loads history."""

def get_task(task_id: str, *, full: bool = True) -> Task | None: ...
```

```python
# calendar.py
def link_task_to_calendar(task_id: str) -> CalendarLink: ...
def unlink_task_from_calendar(task_id: str) -> None: ...
def sync_once() -> SyncReport: ...   # called by scheduler or on demand
def begin_oauth_flow() -> str: ...    # returns auth URL
def complete_oauth_flow(code: str) -> None: ...
```

---

## 6. UI — translating the prototype to Dash

The `Stride.html` prototype is the visual spec. Match it tightly. Notes on the translation:

### 6.1 Layout

```
app.layout = dmc.MantineProvider(
  theme=stride_theme,
  children=html.Div(id='stride-root', children=[
    TopBar(),                # fixed 56px
    html.Div([
      Board(initial_days=days_window()),     # horizontally-scrolling columns
      Drawer(id='detail-drawer', position='right', size=440),  # houses Detail
    ], className='stride-body'),
    dcc.Store(id='store-cards', data=[]),    # full card list, refreshed on mutation
    dcc.Store(id='store-selected', data=None),
    dcc.Store(id='store-week-offset', data=0),
    dcc.Store(id='store-show-done', data=True),
    dcc.Store(id='store-drag', data={}),     # clientside writes here
    dcc.Interval(id='tick', interval=60_000),# refresh "age" every minute
  ])
)
```

### 6.2 Component conventions

- **Pattern-matching IDs.** Each card has `id={'type': 'card', 'task_id': '<id>'}`. Same for column drop zones (`{'type': 'col-drop', 'day_key': '<k>'}`). Lets a single callback handle all clicks.
- **No inline styles in callbacks.** Components import from `theme.py` (CSS variables). Everything visual lives in `assets/stride.css`.
- **Server-side rendering of the card list.** Cards are not React components — they're Dash `html.Div`s. Re-render the affected column(s) on every mutation. Re-rendering all six is cheap for personal scale.

### 6.3 Drag and drop

`assets/dnd.js` listens for native HTML5 drag events on `[data-card-id]` elements (Dash renders them with that attribute), and on `[data-drop-day]` containers:

```js
// pseudo
document.addEventListener('dragstart', (e) => {
  const card = e.target.closest('[data-card-id]');
  if (!card) return;
  e.dataTransfer.setData('text/plain', card.dataset.cardId);
  e.dataTransfer.effectAllowed = 'move';
});
document.addEventListener('drop', (e) => {
  const col = e.target.closest('[data-drop-day]');
  if (!col) return;
  e.preventDefault();
  const taskId = e.dataTransfer.getData('text/plain');
  const dayKey = col.dataset.dropDay;
  // Write to dcc.Store via clientside callback bridge
  window.dash_clientside.callback_context.triggered_id;
  window.stride_setDrop({task_id: taskId, day_key: dayKey, ts: Date.now()});
});
```

A clientside callback then mirrors `window.stride_setDrop` calls into `store-drag`, which a server callback consumes and calls `tasks.move_task(...)`.

> If this proves fiddly, fall back to a "Move to…" menu on each card. Acceptable for v0.1 — the value of the app is history tracking, not the gesture.

### 6.4 The detail drawer

Uses `dmc.Drawer` with `position='right'` and `size=440`. Same fields as the prototype:
- Title (autosize TextInput)
- Description (Textarea, monospace optional)
- Priority (SegmentedControl, 4 options, colored)
- Size (SegmentedControl, 5 options)
- **Category** (chip group — one chip per category, current one filled with that category's color)
- Estimate (NumberInput, suffix "min")
- Target time (TimeInput)
- **Calendar destination** (three buttons: "Don't schedule" / "Personal" / "Shared" — the latter two resolve to the calendar ids in `settings`; underneath, a "Pick a specific calendar" dropdown grouped by account that lets the user override)
- Activity timeline (rendered from `task.history`, newest first)
- Counters block: Age / Moves / Edits / Status

Field updates debounce 400ms on Title and Description; commit immediately on the picker fields.

### 6.5 Category legend + filter

A horizontal strip directly under the TopBar. Each category renders as a pill with: color swatch · name · live count of open in-window tasks. Clicking a pill filters the board to that category and dims the others; clicking again clears. The strip can be hidden via a setting.

### 6.6 Calendars panel (mirrors the Google Calendar sidebar)

A collapsible panel — same place Google puts its left sidebar — listing connected accounts, each with their sub-calendars. Per calendar row: a colored checkbox (visibility), the name, the role badge (read-only badge for `reader`), and for `owner`/`writer` calendars a small **P** / **S** button to mark that calendar as the Personal / Shared task target. State persists via `calendars.visible` and the two `settings` keys.

---

## 7. Google Calendar integration

### 7.1 OAuth flow

First run, on app start:
1. If no row in `oauth_tokens` → render a "Connect Google Calendar" screen with a single button.
2. Button hits `/oauth/start` → app generates URL via `google_auth_oauthlib.flow.Flow` (scope `https://www.googleapis.com/auth/calendar.events`).
3. User authorises in Google. Redirect URI is `http://localhost:8050/oauth/callback`.
4. Callback handler exchanges code for tokens, encrypts both with Fernet (key from `STRIDE_SECRET` env var or generated and stored at `data/.fernet.key`), saves to `oauth_tokens`.
5. App reloads, scheduler starts.

The OAuth routes are registered on the underlying Flask server: `app.server.add_url_rule(...)`.

### 7.2 Push (Stride → Google / Outlook)

Triggered immediately when a task's calendar link is set/changed, and on any subsequent edit of a linked task's title/description/time/estimate. The destination calendar is whichever `calendar_id` the task is linked to — either set explicitly via the per-card chooser, or implied by the "Personal" / "Shared" target buttons (which resolve to the calendar id stored in `settings.task_target_personal_calendar_id` / `..._shared_calendar_id`).

Both Google and Outlook are abstracted behind a `CalendarBackend` interface; the rest of the code does `backend.upsert_event(account, calendar, event_payload)`.

Event mapping:

| Stride field | GCal field |
|---|---|
| `title` | `summary` |
| `description` | `description` (append a `Stride: <task_id>` footer for reverse lookup) |
| `day_key` + `time_of_day` + `estimate_min` | `start.dateTime`, `end.dateTime`. If `time_of_day` is null → all-day event using `start.date`/`end.date`. |
| `priority` | as a colored event color (P1→11, P2→6, P3→9, P4→8) |
| (none) | `extendedProperties.private.stride_task_id = <id>` for reliable correlation |

On success: store/refresh `etag` and `last_pushed_at`.

### 7.3 Pull (Google → Stride)

Runs every 5 minutes via apscheduler:

1. Fetch events updated since `MAX(last_pulled_at)` using `events.list(updatedMin=...)`.
2. For each event, check `extendedProperties.private.stride_task_id`:
   - **Match → linked task exists:** reconcile (see §7.4).
   - **No match, but event has `Stride:` footer in description:** legacy — adopt the link.
   - **No match, no footer:** import as a new task on the event's date with `origin='google'`. Priority defaults to P3, size to M.
3. For each Stride task with a `calendar_link` whose `google_event_id` no longer exists in GCal: unlink and append `unscheduled` event (don't delete the task).

### 7.4 Reconciliation rules

When both sides changed since last sync:

- If `task.updated_at > calendar_link.last_pushed_at` AND event was modified on Google's side: **Stride wins** for `title`, `description`. **Google wins** for `start`/`end` (the user moved the meeting in calendar — respect it; pull the new date/time back into Stride and record a `moved` event with payload `{ "source": "google_calendar" }`).
- If only one side changed: that side wins, push/pull the other.

> First version can ship "Stride wins for content, Google wins for time" without the more nuanced rule. Document the chosen behavior in the README; surprises here are the #1 cause of two-way-sync user pain.

### 7.5 Failure modes to handle

- Refresh token revoked → app shows banner "Reconnect Google Calendar", disables push, leaves pull at zero.
- Rate limit (429) → exponential backoff, max 1 retry per minute, surfaced as a small dot on the TopBar.
- Network down → sync silently skipped, retried next tick.

---

## 8. CLI

Just enough to operate the thing from a shell:

```
stride run                  # start the Dash app (default :8050)
stride sync                 # one-shot calendar sync, exits
stride db migrate           # apply pending migrations
stride db dump TASK_ID      # print task + history as JSON
stride export DAY_KEY       # JSON dump of a day's tasks (for blog screenshots)
```

Use `typer` — composes with `uv run stride ...` cleanly.

---

## 9. Testing

The UI is exercised manually; tests cover the services.

Must-have test cases:
- `create_task` writes exactly one `created` event.
- `update_task` with 3 field changes writes 3 `edited` events with correct `from`/`to`.
- `move_task(today)` is a no-op (no `moved` event written) when already on today.
- `move_task` cross-day writes a `moved` event with both human labels.
- `move_count` and `edit_count` derived correctly after a mixed sequence.
- `toggle_done` writes `done`, then `reopened`, then `done` again — and `done` is the final state.
- Calendar push builds an all-day event when `time_of_day` is null.
- Calendar pull adopts a new event with the `stride_task_id` extended property.
- Reconcile: Stride title change + Google time change → both survive.

Fixture: an in-memory SQLite DB seeded via `migrations/0001_init.sql`.

---

## 10. Build phases

Suggested order for Claude Code sessions:

**Phase 1 — Skeleton (one session)**
- Repo scaffolding, `pyproject.toml`, `uv` setup
- `db.py` + migrations, basic `tasks.create_task` + `list_tasks`
- Dash app boots, shows hardcoded "Hello Stride"

**Phase 2 — Board UI, no DnD (one session)**
- TopBar, Board, Column, Card components
- `dcc.Store` wiring
- Add-task composer
- Click to open detail drawer with read-only fields

**Phase 3 — Mutations & history (one session)**
- Detail drawer becomes editable
- All `services/tasks.py` functions complete with history
- Move via a "Move to…" menu (not DnD yet)
- Counters and chips render from derived fields

**Phase 4 — Drag and drop (half session)**
- `assets/dnd.js` + clientside callback bridge
- Stale ribbon, capacity bar, off-window count

**Phase 5 — Google Calendar (one session)**
- OAuth flow + token storage
- Push on link / edit
- Pull loop via apscheduler
- Reconcile rule (simple v1: content-from-Stride, time-from-Google)

**Phase 6 — Polish (one session)**
- Keyboard shortcuts (esc to close drawer, n to add to Today, j/k to navigate)
- Empty states, error banners, OAuth-revoked banner
- Light/dark token swap (the HTML prototype is light only; dark is a nice-to-have)

---

## 11. Open questions to resolve as you build

- **Recurring tasks.** Out of scope for v0.1, but the data model should let v0.2 add a `recurrence_rule` column without a major rewrite. Leave a TODO comment.
- **Timezone.** Single user, but: what happens when you travel? Suggest storing `created_at` as UTC ms, `day_key` as local-date in the *home* timezone (stored in settings), and rendering everything in current-device local. Document the choice.
- **Multiple calendars.** v0.1 uses `primary`. v0.2: a "push tasks to calendar X" setting. Schema already allows it via `calendar_id` column.
- **Undo.** A `deleted_tasks` tombstone table is in §5 but no UI for it yet. Phase 6 candidate.
- **Backups.** SQLite is one file. `cron` it nightly to `data/backups/`. Mention in README.

---

## 12. The blog hooks

Per your `blog-series-plan.md`, build phases map to posts:

| Phase | Post |
|---|---|
| 1 → 2 | Post 4: *My First Real Feature — Designed and Built with AI* — the board UI |
| 3 | Post 6: *Architecture Decisions* — the history protocol, why append-only |
| 5 | Post 5: *When AI Gets It Wrong — Debugging With an AI Co-Pilot* — sync conflicts are bug magnets |
| 6 | Post 7 or 8 — depending on what trips you up |

The HTML prototype itself is worth a paragraph in Post 4: "I started by mocking the entire UX as a static React prototype before writing a line of Python, so when I sat down with Claude Code I was implementing a known shape, not exploring one." That's the kind of working detail readers reward.

---

## 13. First prompt for Claude Code

When you start Phase 1, paste this:

> Read `Stride — Python Spec.md` end-to-end. We're starting Phase 1 only.
> Scaffold the repo as described in §3, set up `pyproject.toml` for `uv`, create
> the SQLite schema from §4 in `migrations/0001_init.sql`, implement `db.py`
> (connection + migration runner) and the minimal `tasks.create_task` and
> `tasks.list_tasks` functions in `services/tasks.py` per §5. Boot a Dash app
> in `ui/app.py` that renders a placeholder "Stride" page and lists the count
> of tasks from the DB. Add `pytest` and one test that creates a task and
> reads it back. Stop there — do not start Phase 2.

---

*This spec is paired with `Stride.html` in this project. When the visual or interaction is unclear from the text, the prototype is the tiebreaker.*
