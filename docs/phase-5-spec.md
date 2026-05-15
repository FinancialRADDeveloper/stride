# Phase 5 — Google Calendar Sync

**Branch:** `feat/phase-5-gcal`  
**PR target:** `main`  
**Dependencies:** Already in `pyproject.toml` — `google-api-python-client`, `google-auth-oauthlib`, `cryptography`

---

## What This Phase Delivers

- OAuth 2 flow: user connects their Google account from within the app
- **Push:** new/edited Stride tasks → Google Calendar events
- **Pull:** Google Calendar events → Stride tasks (one-way import)
- **Reconcile:** APScheduler job runs every 5 minutes to keep both sides in sync
- Encrypted token storage (Fernet) — no plaintext credentials on disk

---

## DB Tables Already Exist (from 0001_init.sql)

```sql
calendar_accounts  -- one row per connected Google account
calendars          -- list of user's Google calendars (fetched after OAuth)
calendar_links     -- maps task_id → google_event_id (many-to-many capable)
oauth_tokens       -- encrypted access + refresh token blobs
```

Do NOT create new migration files unless schema changes are needed.

---

## Config Already in Place (stride/config.py)

```python
OAUTH_REDIRECT_URI = "http://localhost:8050/oauth/callback"
FERNET_KEY_PATH = DATA_DIR / ".fernet.key"
STRIDE_SECRET = os.environ.get("STRIDE_SECRET")
```

`client_secret.json` is gitignored at `data/client_secret.json`.

---

## Implementation Plan

### Step 1 — Fernet key bootstrap (stride/services/gcal.py)

```python
from cryptography.fernet import Fernet
from stride.config import FERNET_KEY_PATH, DATA_DIR

def _get_or_create_fernet() -> Fernet:
    if FERNET_KEY_PATH.exists():
        return Fernet(FERNET_KEY_PATH.read_bytes())
    DATA_DIR.mkdir(exist_ok=True)
    key = Fernet.generate_key()
    FERNET_KEY_PATH.write_bytes(key)
    return Fernet(key)

def encrypt_token(data: str) -> bytes:
    return _get_or_create_fernet().encrypt(data.encode())

def decrypt_token(data: bytes) -> str:
    return _get_or_create_fernet().decrypt(data).decode()
```

### Step 2 — OAuth flow (stride/services/gcal.py)

```python
from google_auth_oauthlib.flow import Flow
from stride.config import OAUTH_REDIRECT_URI

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CLIENT_SECRETS_FILE = DATA_DIR / "client_secret.json"

def build_oauth_flow() -> Flow:
    return Flow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES,
        redirect_uri=OAUTH_REDIRECT_URI,
    )

def get_auth_url() -> str:
    flow = build_oauth_flow()
    url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return url

def exchange_code(code: str, conn) -> None:
    """Exchange auth code for tokens; encrypt and store."""
    flow = build_oauth_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    token_blob = json.dumps({
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    })
    encrypted = encrypt_token(token_blob)
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO oauth_tokens (service, token_blob) VALUES (?, ?)",
            ("google", encrypted),
        )
```

### Step 3 — Flask OAuth callback route (stride/ui/app.py)

Dash exposes the raw Flask app via `app.server`. Register the OAuth callback route there:

```python
@app.server.route("/oauth/callback")
def oauth_callback():
    from flask import request, redirect
    code = request.args.get("code")
    if code:
        conn = app_db()
        exchange_code(code, conn)
    return redirect("/")
```

Add this inside `create_app()` after the Dash app is built.

### Step 4 — Push: task → Google event (stride/services/gcal.py)

```python
import googleapiclient.discovery
import google.oauth2.credentials

def _build_service(conn):
    row = conn.execute("SELECT token_blob FROM oauth_tokens WHERE service='google'").fetchone()
    if row is None:
        raise RuntimeError("Google not connected")
    token_data = json.loads(decrypt_token(row["token_blob"]))
    creds = google.oauth2.credentials.Credentials(**token_data)
    return googleapiclient.discovery.build("calendar", "v3", credentials=creds)

def push_task(conn, task_id: str, calendar_id: str = "primary") -> str:
    """Create or update a Google Calendar event for a task. Returns event_id."""
    from stride.services.tasks import get_task
    task = get_task(conn, task_id, full=False)
    service = _build_service(conn)

    event_body = {
        "summary": task.title,
        "description": task.description,
        "start": {"date": task.day_key},
        "end": {"date": task.day_key},
    }
    if task.estimate_min:
        # Convert estimate to a timed event if time_of_day is set
        if task.time_of_day:
            start_dt = f"{task.day_key}T{task.time_of_day}:00"
            from datetime import datetime, timedelta
            end_dt = (datetime.fromisoformat(start_dt) + timedelta(minutes=task.estimate_min)).isoformat()
            event_body["start"] = {"dateTime": start_dt, "timeZone": "Europe/London"}
            event_body["end"] = {"dateTime": end_dt, "timeZone": "Europe/London"}

    # Check if already linked
    row = conn.execute(
        "SELECT google_event_id FROM calendar_links WHERE task_id=?", (task_id,)
    ).fetchone()

    now_ms = int(time.time() * 1000)
    if row:
        event = service.events().update(
            calendarId=calendar_id, eventId=row["google_event_id"], body=event_body
        ).execute()
    else:
        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        with conn:
            conn.execute(
                """INSERT INTO calendar_links
                   (task_id, calendar_id, google_event_id, last_pushed_at, origin)
                   VALUES (?, ?, ?, ?, 'stride')""",
                (task_id, calendar_id, event["id"], now_ms),
            )

    with conn:
        conn.execute(
            "UPDATE calendar_links SET last_pushed_at=?, etag=? WHERE task_id=?",
            (now_ms, event.get("etag"), task_id),
        )
    return event["id"]
```

### Step 5 — Pull: Google events → tasks (stride/services/gcal.py)

```python
def pull_events(conn, calendar_id: str = "primary", days_ahead: int = 14) -> int:
    """Import upcoming Google Calendar events as Stride tasks. Returns count created."""
    import datetime
    service = _build_service(conn)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    end = (datetime.datetime.utcnow() + datetime.timedelta(days=days_ahead)).isoformat() + "Z"

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    created = 0
    for event in result.get("items", []):
        event_id = event["id"]
        # Skip if already linked
        exists = conn.execute(
            "SELECT 1 FROM calendar_links WHERE google_event_id=?", (event_id,)
        ).fetchone()
        if exists:
            continue

        day_key = (event.get("start", {}).get("date")
                   or event["start"]["dateTime"][:10])
        title = event.get("summary", "(no title)")
        description = event.get("description", "")

        from stride.services.tasks import create_task
        task = create_task(conn, title=title, day_key=day_key,
                          description=description, category_id="personal")

        now_ms = int(time.time() * 1000)
        with conn:
            conn.execute(
                """INSERT INTO calendar_links
                   (task_id, calendar_id, google_event_id, last_pulled_at, origin)
                   VALUES (?, ?, ?, ?, 'google')""",
                (task.id, calendar_id, event_id, now_ms),
            )
        created += 1
    return created
```

### Step 6 — APScheduler job (stride/cli.py)

```python
from apscheduler.schedulers.background import BackgroundScheduler

def _start_sync_scheduler(app_db_fn):
    scheduler = BackgroundScheduler()
    def sync_job():
        conn = app_db_fn()
        try:
            from stride.services.gcal import pull_events, push_task
            pull_events(conn)
            # Push any tasks linked to google but not yet pushed today
            rows = conn.execute(
                "SELECT task_id FROM calendar_links WHERE last_pushed_at IS NULL"
            ).fetchall()
            for row in rows:
                try:
                    push_task(conn, row["task_id"])
                except Exception:
                    pass
        except Exception:
            pass  # Never crash the scheduler
    scheduler.add_job(sync_job, "interval", minutes=5)
    scheduler.start()
    return scheduler
```

Call `_start_sync_scheduler(app_db)` inside `create_app()` after the layout is set.

### Step 7 — UI: Connect Google button (stride/ui/components/topbar.py)

Add a small "Connect Calendar" button to the topbar. On click, a callback reads the OAuth URL and uses a `dcc.Location` component to redirect.

```python
# In topbar layout:
html.Button("⟳ Calendar", id="btn-connect-gcal", className="btn-gcal"),
dcc.Location(id="gcal-redirect", refresh=True),
```

```python
# In a new gcal_cb.py:
@app.callback(
    Output("gcal-redirect", "href"),
    Input("btn-connect-gcal", "n_clicks"),
    prevent_initial_call=True,
)
def start_oauth(n_clicks):
    from stride.services.gcal import get_auth_url
    return get_auth_url()
```

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `stride/services/gcal.py` | **Create** — all OAuth + push/pull/reconcile logic |
| `stride/ui/app.py` | **Modify** — add Flask `/oauth/callback` route, start scheduler |
| `stride/ui/components/topbar.py` | **Modify** — add "Connect Calendar" button + `dcc.Location` |
| `stride/ui/callbacks/gcal_cb.py` | **Create** — OAuth redirect callback |
| `stride/cli.py` | **Modify** — start scheduler in the run command |
| `tests/test_gcal.py` | **Create** — mock googleapiclient, test encrypt/decrypt round-trip |

---

## Edge Cases to Handle

- `client_secret.json` missing → show friendly error, not a 500
- Token expired → `google.auth.exceptions.RefreshError` → re-prompt OAuth
- Event with no `date` (all-day) vs `dateTime` — handle both in pull
- Duplicate event import on repeated pull runs — handled by checking `calendar_links`
- Scheduler running in debug/reload mode — only start ONE scheduler instance

---

## Testing Strategy

Use `unittest.mock.patch` to mock `googleapiclient.discovery.build`. Don't make real API calls in tests. Test:
1. `encrypt_token` / `decrypt_token` round-trip
2. `push_task` — verify event body construction without calling Google
3. `pull_events` — mock event list response, verify tasks created
4. Duplicate guard — pull same event twice, verify only one task created
