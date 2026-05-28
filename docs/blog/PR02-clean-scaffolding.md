# The PR That Was Just Housekeeping — and Why That PR Matters

Not every pull request introduces a feature. Some PRs are about making space for the features that follow. PR #2 is one of those. It relocated the HTML prototype, cleared the `stride/` directory, and established the directory layout that every subsequent commit would build on.

It is a short article. But the lesson inside it is not trivial.

---

## What We Built

Two changes, no new functionality:

1. The prototype was relocated from its original position into `prototype/stride/` — a clean separation from the Python application source code.
2. The `stride/` directory was cleared to make room for the real Python app.

That is it. No new files with logic. No new dependencies. A commit that moves things and deletes things.

---

## Why Clean Scaffolding Matters

There is a version of this project where the prototype files sit adjacent to the Python source. The directory tree would be confusing from day one: some HTML files that are design references, some Python files that are the actual application, nothing clearly labelling which is which. New contributors (or future me, six months later) would have to reconstruct the distinction from context clues.

The prototype is not the app. It should not look like the app from the directory structure. Putting it in `prototype/stride/` makes the distinction explicit and permanent. A `README.md` in that directory confirms the purpose: this is a design reference, not runnable software.

Clearing `stride/` for the Python application sounds obvious, but the discipline is real. The temptation when working on a new project is to accumulate artefacts in one place — "I'll sort out the directory structure later." Later never comes, or it comes when the project is large enough that moving things breaks imports and confuses `git log`. Moving things in PR #2 means every subsequent PR builds on a clean structure.

---

## The Key Decision: Keep the Prototype in the Repository

The alternative was to delete the prototype entirely once the HTML mockup served its purpose. The argument for deletion: it is dead code, it adds noise, it is one more thing to explain.

I kept it for three reasons.

First, it is a historical artefact. Looking at the prototype alongside the running application shows you how faithfully the design was realised and where it diverged. That story is worth preserving.

Second, it is a portfolio asset. For a consulting project, showing a client the design prototype alongside the production code demonstrates a deliberate, professional development process. "We started here, we built toward this" is a stronger narrative than "here is the finished thing."

Third, it takes up negligible space. HTML and CSS files are kilobytes. There is no performance or size argument for deleting them.

---

## The Trade-offs, Honestly

Two directories that look similar but are fundamentally different things is a potential source of confusion. The mitigation is documentation — the `prototype/stride/README.md` exists specifically to answer the question "what is this?" before it becomes a support burden.

There is also a maintenance question: does the prototype get updated when the design evolves? The answer is no. The prototype is a snapshot of the original design intent. When the application diverges — adding dark mode, changing the card layout for Phase 3 — the prototype stays as it was. It is not a living spec; it is a starting point.

---

## What the AI-Assisted Workflow Actually Looked Like

This PR was not AI-assisted in any meaningful sense. It was a `git mv` and a `git rm`. The decision about where things should live was made while writing the architecture spec in PR #1. PR #2 executed that decision.

This is worth noting because not every commit in an AI-assisted project uses AI. Some commits are just engineering hygiene. The AI is a tool that speeds up implementation; it does not replace the developer's judgment about project structure.

---

## What This Unlocks

A clean `stride/` directory. Every subsequent PR can assume that `stride/` is the Python application and nothing else. The prototype is findable without cluttering the source tree. The directory structure answers "what is this project?" from the first `ls`.

For a project that will eventually be open-sourced or handed to another developer, directory clarity is not cosmetic. It is documentation.

---

## Takeaway for Consultants

Housekeeping PRs are not a sign of disorganisation. They are a sign of deliberate project management. The cost of a messy directory structure compounds with every commit. Paying the cleanup cost early, when there are two files to move instead of two hundred, is the right trade-off.

A clean scaffold is not the same as a correct architecture — but it is a prerequisite for one. You cannot reason clearly about a codebase you cannot navigate.

---

## LinkedIn Summary

PR #2 was one `git mv` and one `git rm`. It relocated the design prototype and cleared the directory for the real Python app. The lesson: housekeeping PRs are not waste — they are the price of a codebase that stays navigable as it grows. Paying that cost at two files instead of two hundred is always the right trade.
