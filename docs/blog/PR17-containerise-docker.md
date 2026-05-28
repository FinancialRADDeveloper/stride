# Containerising Stride: The Docker Decisions That Made AWS Deployment Clean

A working local application is not a production application. PR #17 is the bridge: a Dockerfile that builds Stride into a reproducible container, a docker-compose for local development, a GitHub Actions CI pipeline for automated builds, and a health check that every deployment layer depends on.

The decisions made here — image layering, the `0.0.0.0` bind address, the WAL/DELETE journal mode discovery — echo through every subsequent infrastructure PR.

---

## What We Built

Four files and a series of fixes:

- `Dockerfile` — multi-stage Python 3.12 slim image using `uv` for dependency installation
- `docker-compose.yml` — local development setup with volume mount for SQLite persistence
- `.github/workflows/ci.yml` — build-on-PR, push-to-ECR-on-merge GitHub Actions workflow
- Health endpoint already in place from PR #3 — used immediately by docker-compose and later by App Runner

---

## The Dockerfile: Layer Caching Strategy

The Dockerfile's most important design decision is the separation between dependency installation and source code copy:

```dockerfile
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy only dependency files first — this layer is cached as long as
# pyproject.toml and uv.lock do not change
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Now copy source — this layer rebuilds on every source change
COPY stride/ ./stride/

CMD ["uv", "run", "stride"]
```

The `--no-install-project` flag in `uv sync` installs all declared dependencies but does not install the project itself (the `stride` package). The project is installed implicitly when `uv run stride` executes — by which point the source code is already in the image.

The consequence of this ordering: the dependency installation layer (which takes the most time) is cached by Docker as long as `pyproject.toml` and `uv.lock` have not changed. A source-only change — editing a callback, fixing a CSS rule, adjusting a service function — skips the dependency layer entirely. Build time goes from 60-90 seconds (full dependency install) to 8-12 seconds (just the source copy).

This is not a Stride-specific optimisation. It is the standard Docker layer caching pattern for any Python application. Document it once in your project template and apply it everywhere.

---

## The `0.0.0.0` Bug

Dash's default bind address is `127.0.0.1` — loopback only. On your laptop, this is correct: `http://localhost:8050` resolves to `127.0.0.1`. Inside a Docker container, `127.0.0.1` is the container's loopback — completely unreachable from the host, regardless of port mapping.

The symptom: `docker-compose up` runs without errors. The health check (`curl http://localhost:8050/health`) times out. Port 8050 is mapped. The app is running. Nothing responds.

The fix:

```python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
```

`0.0.0.0` binds to all interfaces — the loopback and the container's network interface that Docker's port mapping reaches. The health check responds. The compose file works.

This is the most common Docker networking mistake. It appears in almost every Python web application containerised for the first time because the local development bind address is correct for local development and wrong for containers. The fix is two characters. The debugging, if you do not already know what to look for, can take an hour.

The lesson is now in CLAUDE.md: "Dash runs on 0.0.0.0 in containers — 127.0.0.1 is unreachable from the Docker host."

---

## The WAL Journal Mode Discovery

The docker-compose maps `./data:/app/data` — a bind mount from the local `data/` directory into the container. On Linux, this works correctly with both WAL and DELETE journal modes. On Windows, NTFS locking semantics differ.

WAL mode creates `stride.db-wal` and `stride.db-shm` alongside the main database file. On a Windows bind-mount, the file locking required by WAL checkpointing fails silently. The database appears to accept writes, but the WAL file is never checkpointed into the main database file. On container restart, the WAL file is gone. Recent writes are lost.

The fix: `PRAGMA journal_mode=DELETE` enforced on every connection in `app_db()`. DELETE mode writes directly to the main database file. No secondary files, no cross-platform locking issues.

This bug was not discovered until running on Windows Docker Desktop. It did not appear in CI (Linux) or in local development without Docker. The fix was a one-line `PRAGMA` in the connection factory and a comment explaining why. The comment is essential — without it, the next developer to look at the code will see "DELETE mode instead of the higher-performance WAL" and wonder why.

---

## GitHub Actions CI

The CI workflow triggers on pull requests and main branch merges:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t stride:test .
      - name: Health check
        run: |
          docker run -d -p 8050:8050 --name stride-test stride:test
          sleep 5
          curl --fail http://localhost:8050/health
          docker stop stride-test
```

The CI does not need AWS credentials for PR builds — it just builds the image and runs the health check. ECR push is only triggered on main branch merges (where OIDC credentials are available). This keeps the PR feedback loop fast and avoids requiring AWS access for contributor PRs.

The health endpoint from PR #3 is the integration test. If the app boots and responds to `/health`, the container is working. This is not a comprehensive test suite — it is a smoke test that catches the most common failure modes: import errors, missing dependencies, bind address issues.

---

## The Trade-offs, Honestly

`python:3.12-slim` is a reasonable production base image but not the smallest possible. `python:3.12-alpine` would produce a smaller image but Alpine's `musl` libc causes compatibility issues with some Python packages that link to `glibc`. Slim is the pragmatic choice.

The `CMD ["uv", "run", "stride"]` entry point goes through `uv`'s subprocess orchestration. This adds a small startup overhead (uv validates the environment before executing) and means the container has two processes running (uv and the Python app). For a single-user application, this is acceptable. A production-grade setup would use `CMD ["python", "-m", "stride"]` directly, bypassing uv.

Docker-compose does not scale horizontally — it runs a single container. SQLite's single-writer semantics mean horizontal scaling would require a database change anyway, so this limitation is consistent with the architecture.

---

## What the AI-Assisted Workflow Actually Looked Like

The Dockerfile was AI-generated from a specification: "Python 3.12 slim, uv, multi-stage, source copy after dependency install, `CMD uv run stride`." The `--no-install-project` flag was AI-suggested based on the specification. The `0.0.0.0` fix was discovered during testing and AI-confirmed as the correct approach.

The WAL journal mode issue was diagnosed by the symptom (writes not persisting across restarts on Windows). The AI suggested the `PRAGMA journal_mode=DELETE` fix after the root cause was identified.

The CI workflow was AI-generated from a template — "build on PR, push to ECR on main, health check as smoke test." The OIDC configuration came in the next infrastructure PR.

---

## What This Unlocks

A containerised application is a deployable application. From PR #17 forward, every feature PR produces an image that can be deployed to any container runtime. The AWS pipeline (PR #30) builds directly on this foundation — same Dockerfile, same entry point, same health check.

---

## Takeaway for Consultants

Layer caching is the most impactful Docker optimisation available at zero cost. Copy dependency manifests and install dependencies before copying source code. A 60-second build becomes a 10-second build for source-only changes. Do this on every project.

Bind address `0.0.0.0` in containers is not optional. `127.0.0.1` is correct for local development and wrong for every containerised deployment scenario.

---

## LinkedIn Summary

Containerising Stride revealed two bugs: the `127.0.0.1` bind address that makes every Python web app invisible in Docker (fixed with `0.0.0.0`), and WAL journal mode that silently loses writes on Windows bind-mounts (fixed with `PRAGMA journal_mode=DELETE`). The Dockerfile layering strategy cuts build time from 90 seconds to 10 for source-only changes. Both patterns are now permanent fixtures in my project templates.
