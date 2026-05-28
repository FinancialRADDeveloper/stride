# Why I Spent a Day on HTML Mockups Before Writing a Line of Python

The first commit to Stride is not a Python file. It is an HTML prototype.

That is not an accident or a detour. It is a decision that shaped every architecture choice that came after it. Before I touched Dash or SQLite or `uv`, I needed to know what I was building toward — not in words, but visually, in a browser, where I could resize it and scroll it and click around enough to understand whether the concept was real.

This is the story of PR #1, the design prototype. It is the shortest PR in the series in terms of functional lines, and probably the most important one.

---

## What We Built

PR #1 contains two things. First, a static HTML/CSS prototype in `prototype/stride/` — a complete visual mockup of the day-lane task board, built entirely in plain HTML and CSS with no Python or JavaScript logic. Second, a Python build specification: a Markdown document laying out the architecture of the real app before a single component was written.

The prototype shows the intended layout: a horizontal row of day columns (Monday through Sunday), each containing task cards in a scrollable stack. The colour palette is warm cream (`#f5f3ee`) for backgrounds and dark ink (`#1a1a2e`) for text — a combination that is easy on the eyes during long working sessions and holds up well in direct sunlight on a laptop screen. Headers use a serif face; task times and identifiers use monospace. The card design shows title, priority indicator, estimate badge, and a category chip.

The build spec commits to the key architectural constraints:

- Service layer first — all business logic in `stride/services/`, zero Dash imports, independently testable
- SQLite for persistence — single file, no server, no connection string management
- `uv` as package manager — fastest resolver available, deterministic lockfile
- Dash + Dash Mantine Components for the UI layer — React under the hood without writing React

Neither the prototype nor the spec is the application. They are the target.

---

## The Key Decision: Design-First Before Framework

The strongest objection to a design-first approach is "you are wasting time on HTML that will be thrown away." I want to address this directly, because the objection contains a wrong assumption.

Dash components are opinionated. `dmc.Card`, `dmc.Badge`, `dmc.Drawer`, `dmc.SegmentedControl` — each of these has a visual grammar and a set of constraints. If you start by learning the components and then try to fit them to a design, you are building something the framework suggests rather than something you actually want. Constraints emerge from the component library rather than from your problem.

If instead you start with a browser mockup — something visual and tangible that you have tested by looking at it — you arrive at the framework knowing exactly what you need to produce. You can then evaluate each component on the question "does this give me what I already know I want?" rather than "what does this make possible?"

For a task board specifically, the spatial metaphor is non-negotiable. The columns must feel like columns. The cards must feel like cards you can pick up. The day header must show just enough at a glance — open count, total estimate, date. Getting these proportions right in HTML took two hours. Getting them right in Dash would have taken two hours of `print(layout)` debugging, and the result would have been more hesitant.

The trade-off is real: the prototype is not the app. Every margin, every colour, every font choice has to be recreated in Dash's component model. That recreation effort is not zero — but it is bounded, because the target is known.

---

## The Architecture Spec: Committing to Constraints Early

The build spec is worth discussing separately because it made decisions that were never revisited:

**Service layer with zero Dash imports.** This is the constraint that shapes everything. If a service function imports `dash` for any reason — to access a store, to use a callback context, anything — it can no longer be tested without booting Dash. I enforced this as a hard rule from day one. It meant that by the time the board was running in a browser, every service function had been exercised in plain Python. The UI layer is genuinely thin.

**Append-only event log.** The spec anticipated a `task_events` table before the schema existed. Append-only means you never overwrite history — every edit, move, completion is a new row. This gives you a timeline for free, enables undo, and makes debugging production issues much simpler. You can always reconstruct state from events.

**Migrations from day one.** The spec mandated a `schema_version` table and numbered SQL migration files. At the time there was only one table. By phase 4 there were eight columns added across five migration files, and none of the production deployments required any manual database intervention.

The value of a build spec is not that you follow it perfectly — you do not. It is that when you deviate from it, you have to make an active decision. "We said service layer only, but this callback needs to call the DB directly — is that right?" Usually the answer is to refactor. Occasionally it is acceptable to deviate. Either way, the spec makes the deviation visible.

---

## The Trade-offs, Honestly

Time spent on the prototype is time not spent building. For a two-week sprint with a clear feature list, front-loading design is harder to justify. For a project that could grow over months and whose visual character matters for consulting portfolio purposes, it is the right investment.

The prototype also locked in certain design decisions that were hard to change later. The warm cream background was chosen because it photographs well and looks distinctive in screenshots. When I considered adding a dark mode, I had to ensure the dark palette felt equally intentional — which it does, because the light palette was deliberate rather than a default.

The biggest practical cost: maintaining two directories. `prototype/stride/` is a completely separate artefact from `stride/`. It does not run in Docker. It does not have dependencies. It is just HTML. If a developer unfamiliar with the project clones the repo and runs the prototype, they see something that looks like the app but does not work. A README in the prototype directory clarifies this, but it is still a potential point of confusion.

---

## What the AI-Assisted Workflow Actually Looked Like

The prototype was generated from a structured brief: layout goals, colour values, font choices, card contents, interaction patterns (hover, selected state, drag placeholder). The AI produced the HTML and CSS. I reviewed it in a browser, adjusted proportions and spacing to match my mental model, and iterated until it felt right. Three rounds of iteration, roughly ninety minutes total.

The build spec was different. I drafted the architectural constraints myself — service layer separation, append-only events, migration runner — and used the AI to structure them into a readable document and check for internal consistency. The constraints came from experience with projects where these things were not enforced from the start.

This pattern — human decision, AI implementation — is the standard workflow throughout the project. The AI is fastest when the decision is already made. The prototype and spec gave it a complete brief before the first `uv init`.

---

## What This Unlocks

A design prototype is proof of concept as a visual artefact. The architecture spec is proof of concept as a technical document. Together they establish that the project is buildable and that you know what you are building. Every subsequent PR has a clear target to hit and a constraint system to work within.

For a consulting portfolio project, this also matters for communication. When a client asks "what did you build?", you can show them the prototype alongside the working application and explain the gap between them — which is the whole story of the engineering.

---

## Takeaway for Consultants

Before writing a line of framework code, know what you are targeting. A two-hour HTML prototype is not wasted time — it is the cheapest way to validate your visual concept and establish a target for every component decision that follows. Combined with an architecture spec that commits to key constraints upfront, it gives you a project that grows coherently rather than accreting features without direction.

The `prototype/` directory in a codebase is not dead code. It is the original vision, preserved alongside its realisation.

---

## LinkedIn Summary

I started building Stride — a Python/Dash task board — with a static HTML prototype and an architecture spec before touching any Python. Design-first means every Dash component decision has a target to hit, not a blank slate to fill. The spec committed to service-layer separation and append-only events before a schema existed. Those constraints held for 33 PRs. The prototype took two hours. The discipline it enforced saved many more.
