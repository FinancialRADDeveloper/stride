# Stride

> A personal day-lane task board — built in public with AI.

Stride is a tool I built because nothing on the market quite fit. It's a day-based kanban board with first-class history tracking (how many times has this card been moved? how old is it?), Google Calendar two-way sync, and a clean, honest UI that makes stale tasks uncomfortable rather than invisible.

This repo documents the entire build — design, architecture, code, and the AI-assisted workflow behind all of it.

---

## Status

| Phase | Status |
|---|---|
| Design prototype (Claude Design) | ✅ Done |
| Python spec | ✅ Done |
| Phase 1 — Skeleton (Dash + SQLite) | 🔜 Next |
| Phase 2 — Board UI | ⬜ Planned |
| Phase 3 — Mutations & history | ⬜ Planned |
| Phase 4 — Drag and drop | ⬜ Planned |
| Phase 5 — Google Calendar sync | ⬜ Planned |
| Phase 6 — Polish | ⬜ Planned |

---

## What's in this repo

```
Stride.html              # Interactive design prototype (Claude Design)
stride/                  # React/JSX source for the prototype
Stride - Python Spec.md  # Full build spec for the Python/Dash app
blog/                    # Hashnode post drafts
docs/                    # Development notes
tools/                   # Utility scripts
project-settings.md      # Project goals and AI tooling stack
```

---

## Running the design prototype

The prototype is a self-contained React app that runs in the browser. Because it loads local JSX files, you need a tiny local server — not a full install, just Python:

```bash
cd /path/to/self-organisation
python -m http.server 8080
```

Then open `http://localhost:8080/Stride.html`.

**What it shows:** the full board UI with realistic seed data — day columns, category filtering, card detail panel, calendar chooser, and a tweaks panel. Nothing persists; it's a design tool, not the real app.

---

## Tech stack (real app — coming in Phase 1)

| Layer | Choice |
|---|---|
| UI framework | [Dash](https://dash.plotly.com/) (Python) |
| Database | SQLite (single file, local) |
| Calendar sync | Google Calendar API (OAuth 2.0) |
| Env / runner | [uv](https://github.com/astral-sh/uv) |

---

## Blog series

*From Prompt to Product: Building My Own AI-Powered Tool* — building and documenting every step on Hashnode.

Posts published so far: [coming soon]

---

## AI tooling

Built using **Claude Code** as the primary coding assistant, with the full workflow documented in `project-settings.md` and `docs/claude-best-practices.md`.
