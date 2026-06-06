# Stride

> A personal day-lane task board — built in public with AI.

Stride is a tool built because nothing on the market quite fit. It's a day-based kanban board with first-class history tracking (how many times has this card been moved? how old is it?), Google Calendar two-way sync, and a clean, honest UI that makes stale tasks uncomfortable rather than invisible.

This repo documents the entire build — design, architecture, code, and the AI-assisted workflow behind all of it.

---

## Status

| Phase | Status |
|---|---|
| Design prototype (HTML + React) | ✅ Done |
| Python spec | ✅ Done |
| Phase 1 — Skeleton (Dash + SQLite) | ✅ Done |
| Phase 2 — Board UI | ✅ Done |
| Phase 3 — Mutations & history | ✅ Done |
| Phase 4 — Drag and drop | ✅ Done |
| Phase 5 — Google Calendar sync | 🚧 In Progress (`feat/phase-5-gcal`) |
| Phase 6 — Polish | 🚧 In Progress (`feat/phase-6-composer-polish`) |

---

## What's in this repo

```
Stride.html              # Interactive HTML/JS design prototype
prototype/               # React/JSX source files for the original prototype
stride/                  # Stride Python/Dash application source code
├── assets/              # Static assets (CSS, JS drag-drop, client-side listeners)
├── services/            # Pure Python business/DB logic (tasks, achievements, etc.)
├── ui/                  # Dash application layout, components, and callbacks
└── cli.py               # Typer CLI entrypoint
docs/                    # Development documentation, design specs, and PR logs (docs/blog/)
blog/                    # Draft Hashnode blog posts
tests/                   # Pytest test suite for service layer functions
project-settings.md      # Project goals and AI tooling stack
Stride - Python Spec.md  # Full build spec for the Python/Dash app
```

---

## Running the Application

Stride runs locally as a containerised app or a standard Python application.

### Running with Docker (Recommended)
You can run Stride inside a Docker container without needing any host Python setup:
```bash
docker compose up --build
```
Then open `http://localhost:8050` in your web browser.

### Running Locally with Python
To run the server locally, install the dependencies from `requirements.txt` into your virtual environment:
```bash
pip install -r requirements.txt
python -m stride run --port 8050
```
Then open `http://127.0.0.1:8050` in your web browser.

### Running Tests
Execute the local test suite using:
```bash
pip install -r requirements-dev.txt
pytest
```

### (Optional) Running the Legacy Design Prototype
To view the original interactive React prototype in the browser:
```bash
python -m http.server 8080
```
Then open `http://localhost:8080/Stride.html`.

---

## Tech Stack

| Layer | Choice |
|---|---|
| **UI Framework** | [Plotly Dash](https://dash.plotly.com/) (Python) |
| **UI Components** | [dash-mantine-components](https://www.dash-mantine-components.com/) |
| **Database** | SQLite (single file, deleted journal mode for thread safety) |
| **Calendar Sync** | Google Calendar API & Cryptography (Fernet token encryption) |
| **Job Scheduler** | APScheduler (for periodic pull syncs) |
| **Validation** | Pydantic (v2) |

---

## Blog Series & Engineering Logs

*From Prompt to Product: Building My Own AI-Powered Tool* — documenting every architectural decision, UX pattern, and lessons learned.

- **Draft Blog Series:** Drafted articles for Hashnode are in [blog/](file:///c:/Code/stride/blog).
- **PR Technical Logs:** Detailed write-ups for all 35 Pull Requests are located in [docs/blog/](file:///c:/Code/stride/docs/blog), detailing:
  - Architecture decisions (such as the append-only event ledger and thread-safe SQLite connection).
  - UX challenges (such as React 18 event capture phase for DnD and withOverlay-free drawers).
  - Motivation mechanics (such as the Achievements Panel and Streak Tracking).
  - Dependency hygiene (transitioning away from `uv` to `pip` in PR #35).

---

## AI Tooling

Stride is built using an **AI-assisted, agent-directed workflow**. We utilize:
- **Google's Antigravity Agent:** For large-scale refactorings, verification loops, and codebase tidiness.
- **Claude Code:** For initial scaffolding and feature implementation.
- **Cursor:** For fast inline edits and autocomplete.

All tooling decisions and prompt patterns are documented in `project-settings.md` and `docs/ai-assisted-best-practices.md`.
