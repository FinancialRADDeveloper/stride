# Project Settings

> Living document — updated as the project evolves.

## Project Identity

| Field | Value |
|-------|-------|
| Project name | _TBD_ |
| One-line description | _TBD_ |
| Target audience | Developers |
| Public repo | _TBD_ |
| Hashnode blog | _TBD_ |
| LinkedIn profile | _TBD_ |

## Goals

1. Build a tool that solves a problem no current market tool solves satisfactorily.
2. Demonstrate AI-enabled development best practices throughout the build.
3. Build in public — blog every meaningful step on Hashnode, share on LinkedIn.
4. Raise profile as a senior AI-enabled developer in the community.

---

## AI Tooling Stack

| Tool | Role | When to use |
|------|------|-------------|
| **Claude Code** (CLI) | Primary agentic assistant — architecture, complex multi-file changes, research | Long-context reasoning, multi-step tasks, research sub-agents |
| **Cursor** | In-editor completions and quick edits | Fast inline changes, autocomplete |
| **GitHub Codex** | _TBD_ | _TBD_ |
| **Junie** (JetBrains) | _TBD_ | _TBD_ |
> See `docs/claude-best-practices.md` for detailed guidance on using Claude effectively.

---

## Repository Structure

```
self-organisation/
├── project-settings.md       # This file
├── CLAUDE.md                 # Claude Code instructions (root)
├── docs/
│   ├── claude-best-practices.md
│   └── architecture.md       # TBD
├── blog/
│   ├── blog-series-plan.md
│   ├── blog-post-01.md
│   └── blog-post-02.md
├── src/                      # Source code (TBD)
├── output/
└── tmp/
```

---

## Development Principles

### AI-First Workflow
- Every significant decision is documented (for blogging and future reference).
- Prompts that produce exceptional results are saved in `docs/prompt-library.md`.
- AI tools are used intentionally — right tool, right task.

### Code Quality
- Best practices from day one: linting, formatting, tests.
- No shortcuts that would embarrass on a public repo.

### Build in Public
- Every meaningful milestone → Hashnode post → LinkedIn share.
- Honest about what works and what doesn't — including AI tool limitations.

---

## Blogging Workflow

1. At the end of each meaningful session, note key decisions and learnings.
2. Sub-agent (Claude) drafts the Hashnode post from session notes.
3. Review, personalise, and publish.
4. Share on LinkedIn using the prepared hook line from the blog plan.

See `blog/blog-series-plan.md` for the full series plan.

---

## Open Questions

- [ ] What is the tool actually called?
- [ ] What specific problem is it solving?
- [ ] What is the primary tech stack (language, framework)?
- [ ] Which other AI tool was mentioned alongside Claude? (Speech-to-text may have garbled the name — confirm: Gemini? Copilot? Other?)
- [ ] Will this be open source?
- [ ] Target launch / MVP date?
