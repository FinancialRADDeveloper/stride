-- Enable WAL mode for concurrent reader (UI) and writer (sync loop)
PRAGMA journal_mode = WAL;

-- Enforce referential integrity
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- categories: user-defined buckets (Build, Home, Work, …)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
  id           TEXT PRIMARY KEY,             -- 'build', 'home', etc — stable slug
  name         TEXT NOT NULL,               -- editable display name
  color        TEXT NOT NULL,               -- hex colour
  sort_order   INTEGER NOT NULL DEFAULT 0,
  created_at   INTEGER NOT NULL             -- unix ms
);

-- ---------------------------------------------------------------------------
-- tasks: one row per card
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
  id              TEXT PRIMARY KEY,                        -- 'c' + ulid()
  title           TEXT NOT NULL,
  description     TEXT NOT NULL DEFAULT '',
  priority        TEXT NOT NULL CHECK (priority IN ('P1','P2','P3','P4')),
  size            TEXT NOT NULL CHECK (size IN ('XS','S','M','L','XL')),
  category_id     TEXT NOT NULL REFERENCES categories(id),
  estimate_min    INTEGER,                                 -- nullable; defaults from size on create
  time_of_day     TEXT,                                    -- 'HH:MM' or NULL
  day_key         TEXT NOT NULL,                           -- 'YYYY-MM-DD'
  done            INTEGER NOT NULL DEFAULT 0,
  created_at      INTEGER NOT NULL,                        -- unix ms
  updated_at      INTEGER NOT NULL                         -- unix ms
  -- TODO (v0.2): add recurrence_rule TEXT to support recurring tasks without schema rewrite
);

CREATE INDEX IF NOT EXISTS idx_tasks_day_key  ON tasks(day_key);
CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category_id);
CREATE INDEX IF NOT EXISTS idx_tasks_done     ON tasks(done);

-- ---------------------------------------------------------------------------
-- task_events: append-only history — every meaningful mutation writes a row
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_events (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id    TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  ts         INTEGER NOT NULL,              -- unix ms
  kind       TEXT NOT NULL,                -- created|moved|edited|done|reopened|scheduled|unscheduled|deleted
  payload    TEXT NOT NULL DEFAULT '{}'    -- JSON blob
);

CREATE INDEX IF NOT EXISTS idx_events_task ON task_events(task_id, ts);

-- ---------------------------------------------------------------------------
-- calendar_accounts: connected providers (Google, Outlook)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calendar_accounts (
  id           TEXT PRIMARY KEY,            -- 'acc_' + ulid()
  provider     TEXT NOT NULL CHECK (provider IN ('google','outlook')),
  email        TEXT NOT NULL,
  label        TEXT NOT NULL,              -- user-renamable, eg 'Personal Google'
  connected_at INTEGER NOT NULL,
  disabled_at  INTEGER                     -- NULL = active
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_email ON calendar_accounts(provider, email);

-- ---------------------------------------------------------------------------
-- calendars: sub-calendars under each account (mirrors GCal sidebar)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calendars (
  id             TEXT PRIMARY KEY,          -- provider's id (eg gcal calendarId)
  account_id     TEXT NOT NULL REFERENCES calendar_accounts(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  color          TEXT NOT NULL,            -- hex
  role           TEXT NOT NULL CHECK (role IN ('owner','writer','reader')),
  visible        INTEGER NOT NULL DEFAULT 1,   -- whether to show on board background
  sort_order     INTEGER NOT NULL DEFAULT 0,
  last_synced_at INTEGER                   -- unix ms, NULL = never synced
);

CREATE INDEX IF NOT EXISTS idx_calendars_account ON calendars(account_id);

-- ---------------------------------------------------------------------------
-- calendar_links: 1:1 with tasks that are pushed to a specific calendar
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS calendar_links (
  task_id          TEXT PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
  calendar_id      TEXT NOT NULL REFERENCES calendars(id),
  google_event_id  TEXT NOT NULL,          -- works for Outlook too; semantic event id
  etag             TEXT,
  last_pushed_at   INTEGER,               -- unix ms
  last_pulled_at   INTEGER,               -- unix ms
  origin           TEXT NOT NULL CHECK (origin IN ('stride','imported'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_links_event ON calendar_links(calendar_id, google_event_id);

-- ---------------------------------------------------------------------------
-- oauth_tokens: encrypted, one row per connected account
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS oauth_tokens (
  account_id        TEXT PRIMARY KEY REFERENCES calendar_accounts(id) ON DELETE CASCADE,
  access_token_enc  BLOB NOT NULL,
  refresh_token_enc BLOB NOT NULL,
  expires_at        INTEGER NOT NULL,
  scope             TEXT NOT NULL,
  updated_at        INTEGER NOT NULL
);

-- ---------------------------------------------------------------------------
-- settings: free-form key/value store
-- Known keys:
--   task_target_personal_calendar_id  TEXT    which calendar receives "Personal" pushes
--   task_target_shared_calendar_id    TEXT    which calendar receives "Shared" pushes
--   home_timezone                     TEXT    eg 'Europe/London'
--   stale_move_threshold              INTEGER (default 3)
--   day_capacity_minutes              INTEGER (default 480)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL   -- JSON
);

-- ---------------------------------------------------------------------------
-- Seed default categories (idempotent)
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO categories (id, name, color, sort_order, created_at) VALUES
  ('build',    'Build',    '#6366f1', 0, 0),
  ('work',     'Work',     '#0ea5e9', 1, 0),
  ('home',     'Home',     '#22c55e', 2, 0),
  ('admin',    'Admin',    '#f59e0b', 3, 0),
  ('health',   'Health',   '#ef4444', 4, 0),
  ('personal', 'Personal', '#a855f7', 5, 0);
