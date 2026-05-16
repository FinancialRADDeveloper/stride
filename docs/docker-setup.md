# Stride — Docker Setup Guide

This guide covers everything needed to build and run Stride inside Docker,
both for day-to-day local development and as a reference for anyone extending
the containerisation.

---

## Prerequisites

1. **Docker Desktop** (Mac or Windows) — [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
   - Must be running before any `docker` or `docker compose` command works
   - Verify it is running:
     ```
     docker version
     ```
     You should see both `Client` and `Server` sections. If you only see `Client`
     or get a connection error, Docker Desktop is not running — start it from
     your Applications folder / Start menu and wait for the whale icon to settle.

2. **No other process on port 8050**
   - If you run Stride locally with `uv run stride`, stop it first.
   - Check: 
     - `netstat -ano | findstr :8050` (Windows)
     - `lsof -i :8050` (Mac)

---

## One-time setup — create a `.env` file

The compose file reads secrets from a `.env` file at the repo root.
Create it once (it is git-ignored so it will never be committed):

```
# .env  — repo root
STRIDE_SECRET=any-long-random-string-you-choose
```

`STRIDE_SECRET` is the Flask session signing key. For local dev any value works;
it just needs to be set so the container does not use the placeholder default.

Generate a good one if you want:
```
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Quick start

```
docker compose up --build
```

- `--build` forces a fresh image build. Omit it on subsequent starts if you
  have not changed `Dockerfile`, `pyproject.toml`, or `uv.lock`.
- Open [http://localhost:8050](http://localhost:8050) in your browser.
- The app is ready when you see the Stride board load, or when the health
  check passes (see Logs section below).

To run in the background:
```
docker compose up --build -d
```

To stop:
```
docker compose down
```

---

## Verifying the container is healthy

### Health endpoint
```
curl http://localhost:8050/health
```
Expected response:
```json
{"status": "ok"}
```

### Docker compose status
```
docker compose ps
```
The `STATUS` column should show `healthy` (not `starting` or `unhealthy`).
It takes up to 15 seconds after the container starts for the first health check
to pass.

### Logs
```
docker compose logs -f stride
```
You should see Dash's startup output ending with something like:
```
Dash is running on http://0.0.0.0:8050/
```

---

## How data persists

Stride's SQLite database lives inside a **Docker named volume** called
`stride-data`, mounted at `/data` inside the container.

```
docker volume ls           # lists all volumes, including stride-data
docker volume inspect stride-data   # shows where Docker stores the files
```

The volume survives `docker compose down` and `docker compose up` — your tasks
are not lost between restarts. To wipe the database and start fresh:

```
docker compose down -v     # -v removes volumes too
```

---

## Rebuilding after code changes

### Changed Python source only (no new dependencies)
```
docker compose up --build
```
The dependency layer is cached — only the `COPY stride/` layer reruns.
Rebuild takes about 5–10 seconds.

### Changed `pyproject.toml` or `uv.lock` (added/removed a package)
```
docker compose build --no-cache
docker compose up
```
This re-runs `uv sync` from scratch. Takes 1–2 minutes depending on connection
speed (downloads packages fresh).

### Changed `Dockerfile` itself
Same as above — `--no-cache` to be safe.

---

## Environment variables reference

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `/data` (container) / `REPO_ROOT/data` (local) | Directory for SQLite file and Fernet key |
| `STRIDE_SECRET` | *(must be set)* | Flask session signing key |
| `STRIDE_PORT` | `8050` | Port the app listens on |
| `STRIDE_DEBUG` | `false` | Enable Dash hot-reload (dev only — never in prod) |

In `docker-compose.yml` these are set directly. For local non-Docker dev they
fall back to sensible defaults in `stride/config.py`.

---

## Useful Docker commands

```bash
# Enter a running container (useful for debugging)
docker compose exec stride bash

# Run a one-off command inside the container
docker compose exec stride python -c "from stride.db import app_db; print('DB ok')"

# Check the SQLite file exists inside the volume
docker compose exec stride ls -lh /data/

# Tail logs with timestamps
docker compose logs -f --timestamps stride

# See how big the image is
docker images stride

# Remove stopped containers and dangling images (housekeeping)
docker system prune
```

---

## Building the image manually (without compose)

```bash
# Build
docker build -t stride:local .

# Run (replace the secret value)
docker run \
  -p 8050:8050 \
  -v stride-data:/data \
  -e DATA_DIR=/data \
  -e STRIDE_SECRET=my-secret \
  stride:local
```

---

## How the Dockerfile works

```
FROM python:3.12-slim
```
Minimal Debian-based Python image. No dev tools, no pip bloat.

```
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```
Copies the `uv` binary from Astral's official image. No install step needed.

```
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
```
Installs production dependencies **before** copying source code. This is the
key layer-caching trick: if you only change Python files (not dependencies),
Docker reuses this layer and the rebuild takes seconds instead of minutes.

```
COPY stride/ stride/
```
Copies application source. Changing any `.py` or `.css` file only rebuilds
from this point onward.

```
ENV DATA_DIR=/data
RUN mkdir -p /data
```
Sets the data directory so `stride/config.py` reads it at startup.

```
HEALTHCHECK ...
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/health')"
```
Uses Python's stdlib `urllib` — no `curl` needed in the slim image. Docker
(and App Runner) poll this every 30 seconds; the container is marked `unhealthy`
after 3 failures.

---

## For contributors: adding new Python dependencies

1. Add the package to `pyproject.toml`
2. Run `uv add <package>` locally — this updates `uv.lock`
3. Commit **both** `pyproject.toml` and `uv.lock`
4. The next Docker build will pick up the new dependency automatically

Never manually edit `uv.lock`. Never run `pip install` inside a container —
it will not persist and breaks the reproducible build.

---

## For contributors: adding a new database migration

1. Create `stride/migrations/NNNN_description.sql` (increment the number)
2. Write idempotent SQL where possible (`CREATE TABLE IF NOT EXISTS`, etc.)
3. For `ALTER TABLE` statements use plain SQL — the migration runner in
   `stride/db.py` tracks which files have been applied and skips them on
   subsequent starts, so `ALTER TABLE` only runs once
4. Test locally: `docker compose down -v && docker compose up --build`
   (the `-v` wipes the volume so migrations run from scratch)

---

## Troubleshooting

### `Cannot connect to the Docker daemon`
Docker Desktop is not running. Start it and wait for the whale icon.

### Port 8050 already in use
Something else is on that port. Either stop it, or change the host port in
`docker-compose.yml` (`"8051:8050"` maps container 8050 to your host's 8051).

### Container starts then immediately exits
Run `docker compose logs stride` to see the error. Common causes:
- Missing or malformed `STRIDE_SECRET`
- A Python import error (syntax mistake in new code)

### Health check stays `starting` forever
The app is taking longer than 15 seconds to boot. Check logs. If it is a
first-run seed/migration taking time, increase `start_period` in
`docker-compose.yml`.

### `uv.lock` out of sync
```
uv lock   # regenerates the lock file
docker compose build --no-cache
```

### I want to inspect the SQLite database
```
docker compose exec stride python -c "
import sqlite3, stride.config as c
conn = sqlite3.connect(c.DB_PATH)
print([r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])
"
```
