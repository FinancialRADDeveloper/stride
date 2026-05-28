# What Git History Is Actually For

PR #4 is a merge commit. The prototype relocation from PR #2 and the Python scaffold from PR #3 land on `main`. No new functionality. No new code worth describing.

And yet the decision to do it this way — feature branch per PR, merge to main, clean history — is worth one article, because it shapes how the rest of the project reads.

---

## What We Built

Nothing new. PR #4 brought two earlier branches onto `main`:

- The `prototype/stride/` relocation (PR #2)
- The working Python skeleton (PR #3)

After this merge, `main` has a running Python application and a clean directory structure. All development from this point forward branches from `main`, adds one logical unit of work, and merges back.

---

## Why Git Hygiene Matters at Phase 1

Most projects accumulate git debt the way they accumulate technical debt: gradually, then suddenly. The first five commits are clean and deliberate. Then there is a "quick fix" directly on main. Then a "WIP" commit that never gets cleaned up. By the time the project is six months old, `git log` is archaeology.

Stride enforces a pattern from PR #1: every change is a branch, every branch is a PR, every PR is merged with a descriptive commit message. This is not bureaucracy for a solo project — it is a record of decisions.

The git log is documentation. `git log --oneline` on Stride reads like a product roadmap:

```
feat: Phase 6 — composer pickers, dark mode, keyboard shortcuts
feat: Phase 3 — editable drawer, move-to flyout, counters & timeline
feat: Phase 2 board UI — day-lane task board
feat: Add SQLite database layer and migration runner
Get the Python app booting end-to-end
```

Each line is a chapter. Each chapter is a reviewable unit. A developer joining the project six months later can read this log and understand the sequence of decisions without reading any code.

---

## The Key Decision: One Logical Unit Per PR

The constraint that makes git history readable is "one logical unit per PR." This is harder than it sounds because features naturally bleed into each other. The database layer wants to be a service too. The service wants to have UI. The UI wants to have CSS.

The discipline is to slice the work across layers, not across features. PR #5 (the database layer) contains only database concerns — schema, migrations, connection factory. The service layer is a separate PR. The UI is a separate PR. Each PR is independently reviewable and independently revertable.

For a consulting portfolio, this matters beyond aesthetics. A reviewer looking at a PR that contains only the database layer can evaluate the schema design, the migration approach, and the connection model in isolation. A reviewer looking at a 600-line PR that adds the database, the service, the UI, and the CSS at once is seeing a result, not a process. The process is what demonstrates engineering judgment.

---

## The Trade-offs, Honestly

Branch-per-PR has overhead. For a solo developer, creating branches, opening PRs, and merging them takes minutes that direct-to-main commits would not. The overhead is real and the benefit is entirely in the record — no one is code-reviewing these PRs except future me.

I kept the discipline anyway. The reason is that this project is explicitly a portfolio piece, and the portfolio includes the git history. Every consulting engagement I use this project to illustrate will involve someone reading the commit log. That audience deserves a readable log.

There is also a practical benefit for solo development: the PR description forces a moment of reflection. "What is this PR for? What did I decide? What broke?" Writing that down once, at the time of the work, is infinitely easier than reconstructing it from memory six months later.

---

## What the AI-Assisted Workflow Actually Looked Like

PR #4 was a standard `git merge`. The AI's contribution was a reminder (encoded in CLAUDE.md as a constraint) to always pull main and branch from it before starting new work. This prevents the "I've been developing on a stale base" problem that creates unnecessary merge conflicts.

The CLAUDE.md constraint: "Always branch from refreshed main. `git pull main` before every new branch. No exceptions."

---

## What This Unlocks

A clean `main` branch with a working application as the baseline. Every subsequent branch has a known-good starting point. The `git log` is readable from day one.

For the AWS pipeline (PR #17) and GitHub Actions CI, a clean main branch is essential — the CI trigger is a push to main, and every commit on main should represent a releasable state. Starting this discipline in PR #4 means it was never retrofitted.

---

## Takeaway for Consultants

Git history is read more than it is written. The five minutes spent writing a clear commit message and PR description are paid back every time someone — including you — reads the log six months later. For a consulting portfolio, readable git history is as important as readable code. It shows process, not just output.

One logical unit per PR is the constraint that keeps history readable. It requires discipline to enforce from the first commit. It is much harder to enforce from commit 50.

---

## LinkedIn Summary

PR #4 is a merge commit — no new code. The article it represents is about why git hygiene matters at phase 1 of a solo project. Clean branch-per-PR discipline from day one means the git log reads like a product roadmap rather than archaeology. For a consulting portfolio, the history is part of the portfolio. The five minutes per PR spent on clean commits pay back continuously.
