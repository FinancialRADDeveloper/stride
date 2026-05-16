# Stride Aggregator Dashboard — Planning Document

**Date:** 2026-05-16  
**Branch target:** `design/stride-prototype` → new feature branches per phase  
**Status:** Planning only — no code written

---

## Executive Summary

Stride is evolving from a single-purpose weekly task board into a single-destination productivity hub: one browser window that replaces your email client, calendar app, news reader, and portfolio tracker. The design is inspired by Windows FancyZones — a fixed three-pane tiled layout (email left, tasks centre, calendar right) with secondary screens (news, investments) accessible without a browser tab change. The centre pane remains the current Dash board, unchanged in function; the surrounding panes are built as independent scroll zones using CSS flexbox with `overflow-y: auto` per pane. OAuth tokens for Google and Microsoft are encrypted with Fernet and stored in the existing `oauth_tokens` SQLite table; background polling via APScheduler prevents API calls from blocking Dash callbacks. The SQLite → PostgreSQL migration must precede the multi-user SaaS launch, but all single-user work can be developed and shipped against SQLite.

---

## 1. Layout Architecture in Dash

### Recommended approach: CSS flexbox, not DMC Grid

`dmc.Grid` and `dmc.SimpleGrid` are designed for content grids, not application chrome. They re-flow columns at breakpoints and do not give independent scroll areas without extra overrides. The correct approach is plain CSS flexbox on a wrapper `html.Div`, with three child divs that each carry `overflow-y: auto; height: 100%`. This is well-trodden territory — it is exactly how VS Code, Notion, and Linear render their multi-pane shells.

**Layout skeleton in `stride/ui/app.py`:**

```python
html.Div(
    id="stride-body",
    className="stride-body",          # existing class, needs expansion
    children=[
        html.Div(id="pane-email",    className="pane pane--left"),
        html.Div(id="pane-centre",   className="pane pane--centre",
                 children=[board_area()]),
        html.Div(id="pane-calendar", className="pane pane--right"),
    ],
)
```

**CSS:**

```css
.stride-body {
    display: flex;
    flex-direction: row;
    flex: 1;
    min-height: 0;          /* critical: lets children scroll inside a flex parent */
    overflow: hidden;
}

.pane {
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    overflow-x: hidden;
    min-width: 0;
}

.pane--left    { flex: 0 0 25%; border-right: 1px solid var(--line); }
.pane--centre  { flex: 1 1 50%; }
.pane--right   { flex: 0 0 25%; border-left:  1px solid var(--line); }
```

The current `body { overflow: hidden }` and `#stride-root { height: 100vh; display: flex; flex-direction: column }` already provide the outer shell. The board's horizontal scroll (`overflow-x: auto` on `.board`) continues to work because it is scoped inside `.pane--centre`, which clips vertically but does not clip horizontally at the board level.

**Existing board CSS interaction:**  
The current `.board` uses `overflow: hidden` at the outer wrapper with `overflow-x: auto` on `.board-inner`. Once `.pane--centre` becomes the scroll host for the column cards, the board's own `overflow` settings can be simplified. The `height: 100%` on `.board` needs to be changed to `flex: 1` so it grows to fill the centre pane rather than relying on an explicit height.

**Resizable pane widths:**  
There is no Dash/DMC component for drag-to-resize split panes. The two realistic options are:

1. **`dash-resizable-panels`** — a thin Python wrapper around the `react-resizable-panels` library. It is not in the current `pyproject.toml` but installs cleanly alongside DMC. This is the recommended path: it requires adding one dependency and wrapping the three panes in a `ResizablePanelGroup`.

2. **Custom JS bridge** — a `mousedown`/`mousemove` listener in a `.js` asset file that reads the drag delta and updates CSS custom properties. This adds ~60 lines of vanilla JS and zero new Python dependencies, but it bypasses Dash's component system and is harder to maintain.

Recommendation: use `dash-resizable-panels` for Phase A; defer until Phase B or C if it adds complexity to the initial layout shell.

**Secondary screens (News, Investments):**  
The cleanest approach that fits "no browser tab change" is a narrow icon sidebar on the far left (inside `pane--left` as a fixed strip, or as a sibling div before `pane--left`). Clicking an icon writes a value to a `dcc.Store(id="store-active-screen")`. A callback then toggles `style={"display": "none"}` on `pane-email` and `pane-calendar` and replaces `pane-centre` content with the chosen secondary screen. An alternative is a `dmc.Tabs` row directly below the topbar — simpler to implement, but it adds a persistent UI element even on the default view and risks looking cluttered. The icon sidebar approach matches the "don't break flow" philosophy better: the default three-pane view has no visible tab bar, and switching to a secondary screen is a deliberate mode change.

---

## 2. Email Aggregation Pane

### What it displays (v1 scope)

- Unread count badge at top of pane
- Scrollable list of inbox threads: sender avatar/initials, sender name, subject, snippet, relative time ("2h ago")
- Unread threads visually distinct (bolder weight, accent left-border)
- Click a thread row → inline expansion showing the latest message body (HTML stripped to plain text for v1)
- "Convert to task" button on each thread — opens the composer pre-filled with the email subject as the task title and a link to the thread in the description

### Sources

| Provider | API | Auth |
|---|---|---|
| Gmail | Google Gmail API v1 | OAuth 2.0, scope `gmail.readonly` |
| Outlook / Office 365 | Microsoft Graph API v1.0 | OAuth 2.0, scope `Mail.Read` |
| Generic IMAP | `imaplib` stdlib | username/password or App Password |

For v1, implement Gmail and Outlook only. IMAP is a long-tail fallback.

### OAuth approach

**Gmail** uses Google's OAuth 2.0 server (`accounts.google.com`). The existing `google_auth_oauthlib` package (already in `pyproject.toml` from Phase 5) handles the flow. The scope needs extending: Phase 5 requested `calendar` only; this phase adds `gmail.readonly`. Because scopes are incremental, users who completed Phase 5 OAuth will need to re-authorise with the combined scope. This is unavoidable with Google's consent model.

**Microsoft Graph** uses Microsoft's OAuth 2.0 server (`login.microsoftonline.com`). The `requests-oauthlib` package (already installed transitively) can drive the PKCE flow. The app registration is done once in Azure Portal → App registrations; the client ID and secret are stored in environment variables (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`), never in the database.

**Token storage:** Reuse the existing `oauth_tokens` table and Fernet encryption pattern from Phase 5 (`stride/services/gcal.py`). Extend the `calendar_accounts.provider` check constraint to `('google', 'outlook', 'imap')`. One row per connected account; the access token and refresh token are stored as encrypted blobs.

**Multi-account:** The `calendar_accounts` table already supports multiple rows per provider (unique index is on `(provider, email)`, not on `provider` alone). The email pane UI should render a source selector (small pills at the top of the pane: "Gmail — alan@...", "Outlook — alan@work.com") with an "all" default that merges threads sorted by date.

### Polling strategy

Email must not block Dash callbacks. The architecture:

1. An APScheduler `IntervalTrigger` job runs every 60 seconds per connected account.
2. The job calls the Gmail/Graph API, fetches the latest 50 threads, upserts into a new `email_threads` SQLite table.
3. A Dash `dcc.Interval(id="tick-email", interval=60_000)` triggers a callback that reads `email_threads` from SQLite and refreshes the pane — no API call in the callback.

This is identical to the existing GCal sync pattern. The `tick` interval already in `app.py` (60s) can be reused; a dedicated `tick-email` gives independent control.

**Rate limits:**
- Gmail API: 250 quota units/user/second; fetching 50 thread summaries costs ~100 units. Polling at 60s is trivially within limit.
- Graph API: 10,000 calls/10 minutes per app. 1 call/60s per user = 1 call/minute. No concern until thousands of concurrent users.

**Push vs polling for v1:** Gmail supports push via Google Pub/Sub (Cloud subscription required). Graph supports webhooks (HTTPS endpoint required, subscription expires every 3 days and must be renewed). Both require additional cloud infrastructure. For v1 on a single-user local install or App Runner deployment, 60-second polling is acceptable. The user is notified of new email within 60 seconds, which is better than most email clients' push latency on mobile. Defer push to a post-v1 iteration.

### v1 scope boundary

- Read-only: no send, no reply, no archive from within Stride
- "Convert to task" is the one write action — it writes to the Stride DB, not back to the email provider
- No search in v1 — just the most recent 50 threads per account

---

## 3. Diary / Calendar Aggregation Pane

### What it displays (v1 scope)

- "What's next" hero: the next upcoming event today, with countdown ("in 47 minutes"), event title, and calendar colour dot
- Today's agenda: time-ordered list of all events for today, each showing start time, title, calendar colour, and duration
- Tomorrow preview: compact 3–5 event list below a divider
- "Add to task list" button on each event (mirrors email's "convert to task")
- Colour coding uses the calendar's colour from the `calendars` table (already stored from Phase 5)

### Sources

| Provider | API | Notes |
|---|---|---|
| Google Calendar | Google Calendar API v3 | Reuses Phase 5 OAuth token and `gcal.py` service |
| Outlook Calendar | Microsoft Graph API v1.0 `/me/calendarView` | Same OAuth token as Outlook email |

The existing `calendars` and `calendar_links` tables already accommodate both providers. The `calendar_accounts.provider` field distinguishes them.

### Relationship to Phase 5 GCal sync

Phase 5 planned two-way sync: Stride tasks push to GCal, GCal events pull into Stride. This calendar pane is a display-layer addition on top of that sync. The pane does not replace Phase 5 — it extends it:

- Phase 5's APScheduler job already fetches GCal events into the Stride DB.
- The calendar pane reads from the same `calendar_links` / events cache that Phase 5 populates.
- The "Add to task list" action in the calendar pane is the reverse of Phase 5's "push task to calendar" — it creates a Stride task from a calendar event and optionally links them via `calendar_links`.

If Phase 5 was not implemented before this phase: the calendar pane needs its own read-only event cache table (`calendar_events`: `id, account_id, calendar_id, title, start_at, end_at, location, description, colour`). The APScheduler poller fetches events for today + tomorrow and upserts into this table.

### Polling

Same pattern as email: APScheduler job every 5 minutes (calendar events are less time-sensitive than email), `dcc.Interval(id="tick-calendar", interval=300_000)` in the Dash layout, callback reads from SQLite.

---

## 4. News Aggregator Screen

### What it is

A secondary screen that replaces the centre pane (or all three panes) when the user clicks the "News" icon in the activity sidebar. It is not always visible — the default view is email + tasks + calendar.

### Feed sources

| Source | Type | Auth | Free tier |
|---|---|---|---|
| User-configured RSS/Atom URLs | RSS/Atom | None | Unlimited |
| Hacker News | JSON API (news.ycombinator.com/hn.algolia.com) | None | Unlimited |
| The Guardian | REST API | API key (free) | 5,000 req/day |
| NewsAPI.org | REST API | API key (free) | 100 req/day (dev tier) |
| Reddit (read-only) | REST API | OAuth app (free) | 60 req/min |

For v1: RSS/Atom + HackerNews. NewsAPI and Reddit add OAuth complexity and low free-tier limits. The Guardian is a good first premium add-on.

### Database schema additions

```sql
CREATE TABLE news_feeds (
    id          TEXT PRIMARY KEY,        -- 'feed_' + ulid()
    user_id     TEXT,                    -- NULL for single-user; user FK for multi-user
    name        TEXT NOT NULL,
    url         TEXT NOT NULL,           -- RSS/Atom URL or 'hackernews:top'
    enabled     INTEGER NOT NULL DEFAULT 1,
    last_fetched_at INTEGER,             -- unix ms
    fetch_error TEXT                     -- last error message, NULL = ok
);

CREATE TABLE news_items (
    id            TEXT PRIMARY KEY,      -- 'ni_' + ulid() or provider ID
    feed_id       TEXT NOT NULL REFERENCES news_feeds(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    url           TEXT NOT NULL,
    published_at  INTEGER,              -- unix ms
    snippet       TEXT,
    read          INTEGER NOT NULL DEFAULT 0,
    saved         INTEGER NOT NULL DEFAULT 0,   -- bookmarked
    fetched_at    INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_news_feed_pub ON news_items(feed_id, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_unread   ON news_items(read, published_at DESC);
```

### Architecture

APScheduler job: every 15–30 minutes per feed (configurable), fetches RSS via `feedparser` (add to `pyproject.toml`; it is pure Python, no native deps). Upserts into `news_items`. Old items (> 7 days, read) are pruned.

Dash pane reads from SQLite on a `dcc.Interval(id="tick-news", interval=900_000)` (15 min).

### UI

- Source pills at top (filter by feed)
- Card list: headline, source name, age, 1–2 sentence snippet
- Click article title → opens in a **new browser tab** (this is the one acceptable tab open; external content should not be embedded in Stride)
- Bookmark icon → sets `saved=1`; saved items appear in a "Read later" section
- "Convert to task" from a saved item — creates a task with the article title and URL in the description

---

## 5. Investments Aggregator Screen

### What it is

A secondary screen showing a portfolio watchlist and market overview. Display only — no trading, no brokerage API.

### Data sources

| Provider | Free tier | Auth | Latency |
|---|---|---|---|
| Alpha Vantage | 25 calls/day, 500/month | API key | 15–20 min delay (free) |
| Twelve Data | 800 credits/day | API key | Real-time on free tier |
| Polygon.io | Previous close only | API key | End of day |
| Open Exchange Rates | 1,000 req/month | API key | Real-time |
| Yahoo Finance (unofficial) | Unlimited | None | ~15 min delay |

**Yahoo Finance TOS warning:** The unofficial `yfinance` Python library scrapes Yahoo Finance's undocumented JSON endpoints. Yahoo's Terms of Service prohibit automated data extraction for commercial purposes. Using `yfinance` in a hosted SaaS product (takeitinyourstride.com) exposes the product to a cease-and-desist. For a personal local install it is a common practice, but it must not be the default in the hosted product. Recommended approach: use Twelve Data or Alpha Vantage for the hosted product; document Yahoo Finance as an optional local-only provider with an explicit opt-in warning in the UI.

### Database schema additions

```sql
CREATE TABLE watchlist (
    id          TEXT PRIMARY KEY,        -- 'wl_' + ulid()
    user_id     TEXT,
    ticker      TEXT NOT NULL,           -- 'AAPL', 'VUSA.L', 'BTC-USD'
    name        TEXT,                    -- optional display name
    sort_order  INTEGER NOT NULL DEFAULT 0,
    enabled     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE price_cache (
    ticker      TEXT PRIMARY KEY,
    price       REAL,
    currency    TEXT,
    day_change  REAL,                    -- absolute
    day_pct     REAL,                    -- percentage
    week_52_hi  REAL,
    week_52_lo  REAL,
    sparkline   TEXT,                    -- JSON array of closing prices, last 30 days
    fetched_at  INTEGER NOT NULL,
    source      TEXT NOT NULL            -- 'twelve_data', 'alpha_vantage', 'yfinance'
);

CREATE TABLE portfolio_positions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT,
    ticker      TEXT NOT NULL,
    shares      REAL NOT NULL,
    avg_cost    REAL NOT NULL,           -- cost basis per share in base currency
    currency    TEXT NOT NULL DEFAULT 'GBP'
);
```

### Architecture

APScheduler job: every 5 minutes during market hours (09:00–17:30 Mon–Fri in the relevant market timezone), every 60 minutes outside hours. The job fetches prices for all enabled watchlist tickers and upserts into `price_cache`.

Dash pane reads from `price_cache` on a `dcc.Interval(id="tick-investments", interval=300_000)`.

### UI

- Watchlist table: ticker, name, current price, day change (£ and %), 52-week range bar
- Sparkline chart: `plotly.graph_objects.Scatter` with `mode='lines'`, minimal axes — Plotly is already a dependency, so this is zero extra cost
- Portfolio section (optional, user enters positions): total value, total P&L, per-position breakdown
- FX rates widget (optional): GBP/USD, GBP/EUR — powered by Open Exchange Rates free tier

---

## 6. Navigation Between Screens

### Recommended: icon activity bar

A narrow (~48px wide) vertical strip on the far-left edge of `stride-body`, before `pane--left`. It contains icon buttons for each mode:

```
[ M ]   ← Stride logo / home (default view)
[ @ ]   ← Email (default: left pane is email)
[ □ ]   ← Tasks (always visible as centre pane)
[ ◻ ]   ← Calendar (default: right pane is calendar)
─────
[ ≡ ]   ← News aggregator
[ ∿ ]   ← Investments aggregator
[ ⚙ ]   ← Settings (future)
```

Clicking an icon writes to `dcc.Store(id="store-active-screen", data="default" | "news" | "investments")`. A single callback on that store toggles visibility of the three panes and swaps the centre content.

**Why not `dmc.Tabs`:**
- Tabs add a persistent horizontal element below the topbar that is visible even on the default view.
- Tabs communicate "you are in one of N equal modes", which is wrong — the default three-pane view is the primary state; news and investments are peripherals.
- The activity bar idiom (VS Code, Slack, Linear) communicates "change the left panel context" without disturbing the primary workspace. It is more learnable for a power-user tool.

**Keyboard navigation:** The existing keyboard shortcut system (`keyboard.js`, `store-kb-action`) can be extended:
- `1` → default view, `2` → news, `3` → investments
- These do not conflict with the existing J/K/E/D/N/Escape bindings.

**Restoring default view:** The Stride logo icon at the top of the activity bar always returns to the default three-pane layout. This gives a single, obvious "home" target.

---

## 7. Multi-User Considerations

### SQLite concurrency risk

SQLite in WAL mode handles one writer and multiple concurrent readers safely. For a single-user local install, this is fine. For a hosted multi-user SaaS, the risk is:

- Multiple concurrent users writing to the same SQLite file from separate App Runner processes
- App Runner scales horizontally — each container has its own local filesystem; SQLite cannot be shared across containers without a shared volume (EFS on AWS), which has high latency

**Decision point:** SQLite + EFS is technically feasible but fragile and slow. PostgreSQL is the correct answer. The PostgreSQL migration must be complete before multi-user launch.

### Migration path: SQLite → PostgreSQL

All migrations are pure SQL (`stride/migrations/`). The migration runner in `stride/db.py` (`run_migrations`) applies files in sorted order. A clean PostgreSQL migration strategy:

1. Write a `0003_postgres_compat.sql` that removes SQLite-specific pragmas and any `AUTOINCREMENT` keywords (PostgreSQL uses `SERIAL` or `GENERATED ALWAYS AS IDENTITY`).
2. Replace `stride/db.py`'s `sqlite3.connect` with `psycopg2.connect` (or `asyncpg` if moving to async) — gated behind `DATABASE_URL` env var. If `DATABASE_URL` is set, use PostgreSQL; otherwise fall back to SQLite for local dev.
3. All application queries already use parameterised SQL with named columns (`sqlite3.Row` → `psycopg2.extras.RealDictCursor`), so query code does not change.
4. The APScheduler singleton and `app_db()` singleton pattern both need to become per-user connection pool instances under PostgreSQL.

### Per-user data isolation

All new tables (`email_threads`, `calendar_events`, `news_feeds`, `news_items`, `watchlist`, `portfolio_positions`) need a `user_id TEXT` column. For single-user SQLite, `user_id` is always `NULL` or a hardcoded sentinel. For multi-user PostgreSQL, `user_id` references a `users` table (to be designed as part of the auth system — not in scope for any phase defined here).

The existing tables (`tasks`, `calendar_accounts`, `oauth_tokens`) do not currently have a `user_id` column. Adding it is a non-breaking migration (nullable column, existing rows get `NULL`).

---

## 8. Implementation Phases

### Phased roadmap table

| Phase | Name | Deliverable | Effort | Key Dependencies | Biggest Risk |
|---|---|---|---|---|---|
| A | Three-pane shell | Left/centre/right divs, icon activity bar, `store-active-screen`, secondary screen toggle (empty placeholders) | S | None beyond current stack | Board layout regression — existing `overflow` CSS must be audited before touching `stride-body` |
| B | Calendar pane | Google Calendar OAuth token reuse, today's agenda display, tomorrow preview, "what's next" hero, `tick-calendar` polling | M | Phase 5 GCal OAuth (or re-implement read-only subset); `calendar_events` table | Outlook Calendar OAuth is a second OAuth provider — scope to Google only for v1 of this phase |
| C | Email pane — Gmail | Gmail OAuth (`gmail.readonly` scope added to existing Google token), `email_threads` table, inbox list, thread expand, "convert to task" | L | Phase B (shared Google OAuth infrastructure) | Gmail OAuth scope change forces existing users to re-consent; token migration needed |
| D | Email pane — Outlook | Microsoft Graph OAuth (`Mail.Read`), same pane UI as Gmail, multi-account merge | M | Phase C (pane UI already built) | Azure app registration is manual; Microsoft's consent screen UX is more complex than Google's |
| E | News aggregator | `feedparser` RSS polling, `news_feeds` + `news_items` tables, news screen UI, "save to read later", "convert to task" | M | Phase A (activity bar navigation) | `feedparser` occasionally chokes on malformed RSS; needs error handling and per-feed retry backoff |
| F | Investments aggregator | Twelve Data API key setup, `watchlist` + `price_cache` tables, sparkline charts, portfolio P&L | L | Phase A (activity bar navigation) | Free tier API limits; Yahoo Finance TOS risk if used in production |
| G | Resizable panes | `dash-resizable-panels` integration, persist pane widths in `settings` table | S | Phase A | New Dash component may conflict with DMC; test in isolation first |
| H | Multi-user + PostgreSQL | `user_id` column migration, `DATABASE_URL` env var switch, connection pooling, user auth (separate design) | XL | All prior phases | This is a platform rewrite, not a feature — deserves its own planning document |

### Phase-by-phase detail

**Phase A — Three-pane shell (effort: S)**

Files to change:
- `stride/ui/app.py` — add `store-active-screen`, restructure `stride-body` into three panes + activity bar
- `stride/assets/stride.css` — `.pane`, `.pane--left`, `.pane--centre`, `.pane--right`, `.activity-bar` classes
- `stride/ui/components/topbar.py` — remove week nav from topbar if it moves to centre pane header
- New: `stride/ui/callbacks/nav_cb.py` — `store-active-screen` → pane visibility toggle

Risk: The board's current CSS assumes it occupies the full body width. The `flex: 1 1 50%` on `.pane--centre` must be validated against the board's horizontal scroll behaviour.

**Phase B — Calendar pane (effort: M)**

Files to create/change:
- `stride/migrations/0003_calendar_events.sql` — `calendar_events` table (if Phase 5 did not create it)
- `stride/services/calendar_pane.py` — `fetch_today_events(account_id)` using existing `gcal.py` token infrastructure
- `stride/services/scheduler.py` — APScheduler setup (may already exist from Phase 5); add `calendar_poll` job
- `stride/ui/components/pane_calendar.py` — agenda list, countdown widget
- `stride/ui/callbacks/calendar_pane_cb.py` — `tick-calendar` → read DB → render pane

**Phase C — Email pane Gmail (effort: L)**

Files to create/change:
- `stride/migrations/0004_email_threads.sql` — `email_threads` table
- `stride/services/gmail.py` — Gmail API client, fetch threads, upsert to DB
- `stride/services/scheduler.py` — add `gmail_poll` job
- `stride/ui/components/pane_email.py` — thread list, expand, convert-to-task
- `stride/ui/callbacks/email_pane_cb.py` — `tick-email` → read DB → render pane
- `stride/ui/app.py` — add `tick-email` Interval

The "convert to task" action reuses the existing `create_task` service function from `stride/services/tasks.py`.

---

## 9. Technical Risks and Open Questions

### Risk register

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Three-pane CSS breaks existing board scroll | High | Medium | Build Phase A on a separate branch; add a visual regression screenshot test before merging |
| OAuth token expiry in background poller | High | High | Google access tokens expire after 1 hour. The poller must call `credentials.refresh(Request())` before each API call. `google-auth` handles this automatically if the `Credentials` object has a refresh token. For Microsoft, use `msal` (add to `pyproject.toml`) which handles token refresh transparently. **This is the single most important implementation detail to get right.** |
| GDPR / data privacy — email content in SQLite | High | High for SaaS | Storing email content (even as a plain-text snippet) on the server means Stride processes personal data on behalf of the user. For the single-user case (user runs their own instance), no problem. For hosted SaaS (takeitinyourstride.com), Stride becomes a data processor under UK GDPR. Required: privacy policy, data processing agreement, right to erasure implementation (a "disconnect and delete all email data" button), and clear disclosure that email is stored server-side. Do not launch the email pane on the hosted product without legal review. |
| CSP headers with multiple OAuth providers | Medium | High | The Dash Flask server does not set CSP headers by default. When adding OAuth redirects, the redirect URIs for Google (`accounts.google.com`) and Microsoft (`login.microsoftonline.com`) must be allowed in `Content-Security-Policy: form-action`. Add CSP headers in a Flask `after_request` hook. The main Dash content (Plotly, DMC) is all same-origin, so `script-src 'self'` is safe. |
| Yahoo Finance TOS on hosted product | High | Medium if used | Do not include `yfinance` as a default data source for the hosted product. Gate it behind an opt-in setting with a visible disclaimer. Use Twelve Data or Alpha Vantage by default. |
| Dash `suppress_callback_exceptions=True` with new dynamic IDs | Low | Low | Already enabled in `app.py`. New pane components can use pattern-matching callbacks without issue. |
| APScheduler thread safety with SQLite WAL | Low | Low | Already addressed — `check_same_thread=False` and WAL mode are set in `db.py`. The scheduler uses the same `app_db()` singleton. |
| `dash-resizable-panels` DMC compatibility | Medium | Unknown | Untested pairing. Phase G should be developed in a scratch branch and tested against DMC 0.14 before committing. If incompatible, fall back to the vanilla JS approach. |

---

## Open Decisions (requires user input)

1. **Phase 5 status:** Was the Google Calendar OAuth (Phase 5) actually implemented and merged? The plan above assumes Phase B can reuse `gcal.py` and the existing `oauth_tokens` infrastructure. If Phase 5 is unimplemented, Phase B must build the OAuth token store from scratch — add ~1 week of effort.

2. **Outlook email vs Gmail email priority:** Should Phase C be Outlook-first (the user's work email) or Gmail-first? The plan above does Gmail first because the Google OAuth library is already in `pyproject.toml`. If the user's primary inbox is Outlook, swap the order.

3. **Reply from Stride:** Should the email pane support sending replies in a later phase? The answer affects schema design now — specifically whether `email_threads` needs to store the full message headers needed to construct a `Reply-To` chain.

4. **News screen layout:** Should news replace the entire three-pane area (full-width feed), or replace only the centre pane while email and calendar remain visible? The full-width option gives more vertical space for reading; the centre-only option maintains context (you can still see what's in your calendar while reading news).

5. **Investment currency:** Should the investments pane default to GBP (given the user's likely UK base) or be currency-agnostic per ticker? The `portfolio_positions` table above has a `currency` column, but the FX conversion logic (e.g., converting USD-priced stocks to GBP portfolio value) needs a decision on whether to build it in Phase F or defer.

6. **SQLite vs PostgreSQL timeline:** At what user count does the hosted product need PostgreSQL? SQLite + EFS on App Runner can serve ~50 concurrent single-user sessions without serious contention (WAL mode serialises writes but not reads). Phase H (PostgreSQL migration) should be triggered before the public beta, not after.

7. **Mobile responsiveness:** The three-pane layout is explicitly designed for wide desktop screens. On a phone, two of the three panes are hidden. Is there a mobile-specific layout planned, or does the mobile app plan (documented in `docs/mobile-responsiveness-plan.md`) supersede this design for small screens?

---

## Appendix: New Python Dependencies Required

| Package | Phase | Purpose |
|---|---|---|
| `feedparser` | E | RSS/Atom parsing |
| `msal` | D | Microsoft Graph OAuth token management |
| `twelve-data` or `alpha_vantage` | F | Market data |
| `dash-resizable-panels` | G | Drag-to-resize panes |

All other integrations (Google OAuth, APScheduler, Fernet encryption, Plotly) are already in `pyproject.toml`.
