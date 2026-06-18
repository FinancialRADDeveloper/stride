# What AI-Assisted Software Development Actually Looks Like in Practice — Not Vibe Coding, but a New Kind of Pair Programming

There is a narrative circulating in certain corners of the internet that AI-assisted development means you describe what you want, press enter, and accept whatever comes out. I understand why it sounds appealing. I also understand why it produces software that nobody trusts.

This is not what I did building Stride, and it is not what I would recommend to any consultant who wants to use AI pairing as a professional skill rather than a party trick. What follows is an honest account of how it actually worked across several months of building a real product — a personal task board in Python/Dash with a full AWS deployment pipeline, drag-and-drop, a context menu, view modes, and an achievements panel.

---

## What AI-Assisted Development Is Not

It is not describing a feature in one message and accepting the first response without review. Code produced this way tends to be syntactically correct, architecturally naive, and full of decisions the AI made because you did not make them first. The AI will happily create a global variable where a service function belongs, mix business logic into a callback that should be a component, and produce CSS that works in the exact environment it tested against and nowhere else.

It is not a way to avoid understanding what you are building. If you cannot explain the Dash callback model, you cannot review whether the generated callback is correct. If you do not understand how React 18 changed event delegation, you cannot investigate why the drag-and-drop stopped working after a PR merge. If you do not know what WAL mode does to SQLite on a Windows Docker bind-mount, you will not notice when the AI generates a `PRAGMA journal_mode = WAL` that will silently corrupt your database on restart.

---

## What It Is

AI-assisted development is pair programming with a partner who has excellent recall, tireless availability, and no product judgment whatsoever. That last part is not an insult — it is a description of a specialisation. Product judgment — deciding what to build, what to defer, what trade-off to make — must come from the human. Implementation speed, API recall, boilerplate generation, and consistent style across a large codebase: that is where the AI earns its seat.

In practice this means every session starts with a decision I have already made: what is being built, why, and what the architectural constraints are. The AI operates within those constraints. When it proposes something outside them, I push back. When it produces something I cannot explain, I ask it to explain — and if the explanation is not convincing, I do not accept it.

---

## The Commit Discipline

The git history of Stride reads like a design walkthrough because it was written as one. Every feature lands in multiple focused commits, each a logical slice:

- Service: pure Python business logic, no Dash imports, testable in isolation
- Component: pure builder functions that return component trees, no callbacks
- Callbacks: the reactive layer that connects inputs to outputs
- CSS: visual polish
- Integration: wiring the new feature into the app factory

The achievements panel is a clear example. Five commits spanning `8e640fd` through `06b0104`:

```
8e640fd feat: achievements service — query completed tasks, deduplicate, compute stats
10c227a feat: achievements panel component — drawer shell, day groups, task rows
e9c9abe feat: wire achievements callbacks — open/close toggle and lazy content refresh
30d2756 feat: achievements panel CSS — layout, day groups, task rows, dark mode
06b0104 feat: integrate achievements into app — topbar button, drawer, store
```

Each commit is independently reviewable. A peer reviewer can read `8e640fd` and evaluate whether the deduplication logic is correct without knowing anything about the Dash component structure. They can read `e9c9abe` and evaluate whether the `PreventUpdate` guard is correct without knowing what the panel looks like.

This discipline does not come naturally when working with AI assistance, because the AI is happy to generate everything in one pass. Imposing the structure is a human decision, and it requires resisting the temptation to commit large blobs of working code just because they work. Working is not the same as reviewable.

---

## The PR Discipline

Every pull request in Stride follows the same format: a business summary first, a technical detail section second. Two audiences, two sections.

The business summary answers the questions a product manager, investor, or future-self skimming the history would ask: what does this change, why does it matter, what is the user experience? It uses plain English and no code.

The technical detail section answers the questions a peer reviewer would ask: what changed, why those specific choices, what are the edge cases? It references file paths, function names, and architectural patterns.

This format came from a deliberate choice early in the project. I wanted the PR history to be a document I could share with a non-technical stakeholder or use as the basis for a blog post, not just a diff that required archaeological investigation to understand. The AI drafts PR descriptions well once you give it the template — the structure is consistent across thirty-plus pull requests.

---

## The CLAUDE.md

Dash session context is a real cost. Every AI coding session starts cold — the model does not remember the previous session, does not know your architectural decisions, and does not know your conventions. Rebuilding that context from scratch every time is wasteful and produces inconsistent results.

The CLAUDE.md file is the solution. It is a single file in the repository root that gives the AI everything it needs to be useful from the first message of a new session:

- The full directory map with one-line purpose per file
- Every `dcc.Store` ID and what it holds
- The commands to run, test, lint, and build the application
- The named gotchas: DnD capture phase, WAL mode disabled, per-thread `app_db()`, store dedup `ts` field, CSS variable theming
- The deployment steps for the AWS pipeline

This file was created in commit `bf350db` after the infrastructure sprint — late enough to have something worth documenting, early enough to be useful for the remaining sessions. Its commit message is instructive: "Captures the codebase knowledge Claude needs at session start so context is never rebuilt from scratch."

Without this file, each session requires five to ten minutes of re-establishing context. With it, the AI hits the ground running. The difference is measurable: sessions with a good CLAUDE.md produce the first useful output in under a minute; sessions without it spend the first quarter-hour on archaeology.

---

## The Branch Discipline

One feature. One branch. From a freshly pulled main.

This sounds obvious. It is harder to maintain than it sounds. During the development of Stride, two PRs merged in the wrong order and silently overwrote each other's changes — a view-mode feature and a mobile CSS sprint that both touched the same board component. Neither broke on merge; the conflict was at the logic level, not the syntax level. The later merge won, and some of the earlier work was lost until identified during testing.

The fix is simple: always pull main before branching, never branch from another feature branch, never have two feature branches touching the same file open simultaneously. This is basic version control hygiene, but it is hygiene that AI-assisted development puts pressure on because the AI can generate so much code so quickly that you are tempted to keep layering features without completing the branch-PR-merge cycle. Resist that temptation.

---

## Where the AI Saved Hours

Boilerplate. The CloudFormation template for the AWS bootstrap stack is 230 lines of YAML defining six resources with their IAM trust policies, lifecycle rules, and dependencies. I described the architecture — ECR, S3, OIDC provider, three roles — and the AI generated the template. I reviewed it, corrected the OIDC thumbprint handling, and adjusted the lifecycle policy retention periods. The generation took minutes. The review took minutes. Writing it from scratch would have taken an hour with the AWS documentation open.

API recall. The `window.dash_clientside.set_props` function is the correct Dash 2.9+ API for writing to a component from vanilla JavaScript without a Python round-trip. It is not prominently documented. The AI knew it. The Litestream command-line flags — `-if-replica-exists`, the `replicate -exec` invocation pattern — are correct on the first pass because the AI has seen the Litestream documentation in its training data.

Consistency. CSS variable naming, callback function naming conventions, the service layer pattern, the component builder pattern — these are consistent across every feature because the AI applies the established patterns when asked to. A human developer working alone over several months would naturally drift. The AI does not drift if the conventions are in its context.

---

## Where the Human Had to Intervene

Architectural decisions. The choice between Litestream and EFS, between App Runner and Fargate, between `withOverlay=False` and the default drawer behaviour — these required product judgment and a clear mental model of the trade-offs. The AI can list the trade-offs when asked, but it cannot decide which ones matter given your specific constraints and timeline.

Debugging subtle failures. The React 18 capture-phase bug took a session of investigation. The AI knew about React 18's event delegation change once I described the symptom precisely enough, but the investigation — forming and testing hypotheses, reading what the browser was actually reporting — was iterative and required me to be at the keyboard, not just reading AI output.

Deciding what not to build. Stride has a clear list of deferred features in its spec: projects, labels, recurring tasks, multi-user. Every time a session produced something that crept toward those features, I pulled it back. The AI does not know what you decided not to build. That boundary lives in your head.

---

## The LinkedIn Angle

I am publishing this series because I want to demonstrate something specific to the senior consultants, engineering leads, and product managers I work with: that AI-assisted development, done with professional rigour, produces software that you would be proud to show a client.

The code is reviewed. The commits are logical. The PRs are documented. The architecture is explained in a CLAUDE.md that another engineer could pick up tomorrow. The deployment pipeline has no long-lived credentials, no manual steps, and a clear UAT-to-production promotion flow.

This is not a side project held together with string. It is a product I intend to host publicly, and the engineering discipline reflects that intention.

The consultants who will succeed with AI pairing are not the ones who accept the first output — they are the ones who treat the AI as a highly capable junior engineer who needs clear direction, consistent architecture, and a human with judgment holding the steering wheel. The speed gain is real. The quality control requirement is unchanged.

---

## Takeaway for Consultants

If you are considering adopting AI-paired development in your practice, start with the things that compound: the commit discipline, the PR format, the CLAUDE.md. These are cheap to establish and expensive to retrofit. A codebase built with these habits from the start reads like it was built by a senior team. A codebase built without them reads like it was assembled in a hurry, because it was.

The AI is a tool for acceleration, not a replacement for judgment. Every significant decision in Stride — the architecture, the trade-offs, the product boundaries — was mine. The AI made me faster at implementing those decisions. That is the correct division of labour, and it is one that any experienced consultant should find natural.

The skills that make you a good consultant — clear thinking about trade-offs, the ability to explain a decision to multiple audiences, knowing when something is good enough and when it needs more — are exactly the skills that make AI pairing work well. You are not being replaced. You are getting a very fast typist who never sleeps and knows every API.
