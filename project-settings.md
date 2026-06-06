# Project Settings

> Living document — updated as the project evolves.

## Project Identity

| Field | Value |
|-------|-------|
| **Project name** | Stride |
| **One-line description** | A personal rolling day-lane task board with ambient history tracking and Google Calendar sync. |
| **Target audience** | Developers, indie hackers, and power users |
| **Public repo** | [github.com/FinancialRADDeveloper/stride](https://github.com/FinancialRADDeveloper/stride) |
| **Hashnode blog** | Drafts in `blog/` |
| **LinkedIn profile** | [Alan Russell](https://www.linkedin.com/in/financialraddeveloper/) |

## Goals

1. Build a personal organising tool that solves a problem no current market tool solves satisfactorily (rolling daily lanes + ambient task history).
2. Demonstrate AI-assisted development best practices throughout the build, maintaining clean software engineering boundaries.
3. Build in public — blog every meaningful step on Hashnode and share on LinkedIn.
4. Establish credibility as a practitioner in agentic AI-assisted software development.

---

## AI Tooling Stack

| Tool | Role | When to use |
|------|------|-------------|
| **Antigravity** (Google) | Primary agentic assistant — architecture, complex multi-file changes, automated verification | Long-context reasoning, multi-step tasks, test verification, refactoring |
| **Claude Code** (Anthropic) | Secondary agentic assistant | Scaffolding, drafting specifications, and initial feature writes |
| **Cursor** | In-editor completions and quick edits | Fast inline changes, visual diff reviews |

> See `docs/ai-assisted-best-practices.md` for detailed guidance on using these tools effectively.

---

## Repository Structure

```
self-organisation/
├── README.md                 # Project entry point and quick start
├── project-settings.md       # This file (project goals & stack)
├── docs/                     # Development notes & specifications
│   ├── ai-assisted-best-practices.md
│   ├── phase-5-spec.md       # Google Calendar sync specification
│   ├── phase-6-spec.md       # Polish, dark mode, keyboard shortcuts spec
│   └── blog/                 # Technical PR-by-PR engineering logs
├── blog/                     # Draft Hashnode blog posts
├── stride/                   # Source code (Python / Dash app)
│   ├── assets/               # JS drag-drop, CSS styles
│   ├── services/             # Pure Python DB & business logic
│   ├── ui/                   # Dash layout, components, and callbacks
│   └── cli.py                # Command line entrypoint
├── tests/                    # Service layer unit tests (pytest)
├── requirements.txt          # Production dependencies
└── requirements-dev.txt      # Development/testing dependencies
```

---

## Development Principles

### AI-Assisted Workflow
- Every significant decision is documented in pull request logs for blogging and future reference.
- We run with high branch discipline: always checkout a new branch (prefixed with `cleanup/`, `feat/`, or `fix/`) off the latest remote `main` before writing code.
- We verify everything using the automated test suite before opening a Pull Request.

### Code Quality
- Enforce strict separation of concerns: database queries and business logic belong in pure-Python services; the UI layer only renders and communicates via `dcc.Store`.
- No shortcuts: everything is type-hinted, structured, and tested.

### Build in Public
- Every PR has an accompanying blog draft documenting the technical and psychological choices.
- Honest about what works, what doesn't, and what we learned about developer-agent ergonomics.

---

## Blogging Workflow

1. At the end of each PR session, write a brief technical log (`docs/blog/PRXX-name.md`).
2. Draft the Hashnode post from session notes inside `blog/`.
3. Review, personalize, and publish to Hashnode.
4. Share on LinkedIn using prepared hook lines from the blog plan.
