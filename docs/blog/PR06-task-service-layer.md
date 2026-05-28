# The Architecture Decision That Made Everything Else Easy

There is one decision in Stride's codebase that I would replicate on every project and recommend to every developer building a Python web application: the service layer with zero framework imports.

It sounds simple. `stride/services/tasks.py` imports `sqlite3`, `datetime`, `pydantic`, and nothing from `dash`. Every function takes a `sqlite3.Connection` as its first argument and returns a Python object. None of the service functions know that a web framework exists.

This decision, made in PR #6 before the first Dash callback was written, is the reason every subsequent PR was faster to build, easier to debug, and simpler to reason about.

---

## What We Built

PR #6 adds `stride/services/tasks.py` — the complete task service layer:

**Pydantic models:**
- `Task` — the full task model, serialised from database rows
- `TaskCreate` — validated input for creating a new task
- `TaskUpdate` — validated input for patching task fields

**CRUD functions:**
- `create_task(conn, data: TaskCreate) -> Task`
- `get_task(conn, task_id: int) -> Task | None`
- `get_tasks_for_day(conn, day_key: str) -> list[Task]`
- `update_task(conn, task_id: int, data: TaskUpdate) -> Task`
- `move_task(conn, task_id: int, to_day_key: str) -> Task`
- `toggle_done(conn, task_id: int) -> Task`
- `delete_task(conn, task_id: int) -> None`

**Append-only event logging:**

Every mutation function writes to `task_events` after the primary operation. `create_task` logs a `created` event. `update_task` logs an `edit` event with the changed fields in a JSON payload. `move_task` logs a `move` event with `from_day_key` and `to_day_key`. `toggle_done` logs `done` or `undone` depending on the new state. This is not optional or configurable — it is built into every mutation by design.

---

## Why Zero Dash Imports

Dash is a web framework. Its imports pull in React rendering infrastructure, callback context, component registries, and a Flask server. None of this should be necessary to run a function that inserts a row into a SQLite database.

When service functions import Dash:

1. **They cannot be tested without booting Dash.** A test for `create_task` should be three lines: open an in-memory SQLite connection, call the function, assert the returned task. If the function imports anything from Dash, the test runner has to initialise a Dash application, which requires a browser-compatible environment and is slow.

2. **They are not reusable outside the Dash context.** A CLI utility, a migration script, a Jupyter notebook — any of these might legitimately want to call `get_tasks_for_day`. If the function imports Dash, running it outside a Dash server raises import errors or requires Dash to be initialised.

3. **They obscure what the function depends on.** A function that takes `conn: sqlite3.Connection` and a data model has declared its complete dependency surface. A function that also imports `dash` has an implicit dependency on the entire Dash runtime state.

The service layer in Stride has zero Dash imports because those three consequences are expensive and avoidable.

---

## The Append-Only Event Log

The `task_events` table was designed in PR #5. PR #6 is where the events are written and the design is validated in practice.

Every mutation function follows a two-step pattern:

```python
def move_task(conn: sqlite3.Connection, task_id: int, to_day_key: str) -> Task:
    # Step 1: perform the mutation
    task = get_task(conn, task_id)
    conn.execute(
        "UPDATE tasks SET day_key = ? WHERE id = ?",
        (to_day_key, task_id)
    )
    # Step 2: log the event
    conn.execute(
        "INSERT INTO task_events (task_id, kind, payload) VALUES (?, ?, ?)",
        (task_id, "move", json.dumps({"from": task.day_key, "to": to_day_key}))
    )
    conn.commit()
    return get_task(conn, task_id)
```

The event is written in the same transaction as the mutation. Either both succeed or neither does. An event without a corresponding mutation — or a mutation without a corresponding event — is impossible.

The payoff comes in PR #11 (the activity timeline), PR #31 (achievements), and any future "undo" feature. The `task_events` table is not being written for the current feature; it is being written for the features that do not exist yet. This is cheap to do at mutation time and expensive to retrofit later, because retrofit requires crawling existing database rows and reconstructing history from state snapshots.

---

## Pydantic Models as the Contract

`TaskCreate` and `TaskUpdate` are Pydantic models. They serve two purposes.

First, validation. If a callback passes `estimate_min = "twenty"` instead of an integer, Pydantic raises a `ValidationError` before the function reaches the database. The validation error is specific — "estimate_min: value is not a valid integer" — rather than a SQLite type error or a silent truncation.

Second, documentation. The function signature `create_task(conn, data: TaskCreate)` tells you exactly what fields are required and what their types are. You do not need to read the SQL statement or the database schema to know what input `create_task` expects.

`TaskUpdate` uses Pydantic's `Optional` fields with `None` defaults. Only the fields explicitly provided in an update call are applied. This means a callback that only wants to update the title does not need to provide the estimate, the category, the priority, or any other field — the service function applies only what is given.

---

## The Trade-offs, Honestly

Two SQL statements per mutation (the operation plus the event) adds a small overhead. At task scale — tens or hundreds of tasks, not millions — this is completely invisible. The event log also grows unboundedly with use: every toggle_done/undone cycle adds two rows. For a personal task board used daily, this adds perhaps 30-50 rows per day. After a year: around 15,000 rows. SQLite handles this with ease.

Pydantic adds a dependency and a validation layer that slows object creation slightly. For a web application where the bottleneck is network latency, not object construction, this trade-off is irrelevant.

The `Optional` field pattern in `TaskUpdate` means a database update with no fields set is valid and does nothing. The service should arguably raise an error in this case — but the callbacks that call `update_task` always supply at least one field, so the defensive case has never fired.

---

## What the AI-Assisted Workflow Actually Looked Like

The Pydantic models and CRUD function signatures were specified in the PR description, then AI-generated. The specification said "service layer, zero Dash imports, Pydantic models for Task/TaskCreate/TaskUpdate, append-only events on every mutation." The implementation followed the spec.

The event payload design — what to store in the JSON payload for each event kind — was mine. I specified "move event stores from_day_key and to_day_key," "edit event stores changed field names and old/new values," and so on. The AI implemented the serialisation. The schema decisions about what to preserve came from experience with audit trails in production systems.

The four service files (tasks, seed, db, migrations) were each a separate commit. Service, then seed data, then connect to the app entry point. Each was reviewable independently.

---

## What This Unlocks

With the service layer in place, the UI layer becomes thin wiring. Every callback becomes: read from stores, call a service function, write to stores. No business logic lives in callbacks. The callbacks cannot have bugs in their business logic because they do not have business logic.

This is the point at which the architecture pays off. PR #10 (the board UI), PR #11 (the drawer and mutations), PR #13 (drag and drop) — all of them call service functions directly. The callbacks are short enough to read and understand in sixty seconds.

---

## Takeaway for Consultants

If you build Python web applications, the most valuable architectural constraint you can enforce is service layer independence: no framework imports, pure Python, independently testable. The cost is one extra parameter (`conn`) on every function. The payoff is a business logic layer that runs, tests, and debugs independently of whether a browser is connected.

Append-only event logs are underutilised. Writing events at mutation time is cheap. Reconstructing history from state later is expensive and lossy. If your application will ever need audit trails, undo, or activity timelines, write events from the first mutation.

---

## LinkedIn Summary

The single architectural decision that made every Stride PR faster: `stride/services/tasks.py` has zero Dash imports. Every function takes a `sqlite3.Connection` and returns a Python object. The callbacks are thin wiring — they call service functions, nothing else. The payoff: every service function tests in three lines, runs in a notebook, and debugs without a browser. Enforce service layer independence from PR #1 and you will never regret it.
