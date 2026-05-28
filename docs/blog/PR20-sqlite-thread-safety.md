# The SQLite Concurrency Bug That Was Always There

It appeared under load testing. A single user clicking rapidly between cards triggered it. Two browser tabs open simultaneously made it consistent. The error:

```
sqlite3.InterfaceError: SQLite objects created in a thread can only be used in that same thread.
```

The bug was not in a recent commit. It was in the connection factory from PR #5 — a module-level `conn` object shared by all requests. It worked during development because single-click testing rarely triggers concurrent request handling. Under any realistic concurrent usage, it was a silent data corruption waiting to happen.

---

## What We Built

One file changed: `stride/db.py`. The `app_db()` function refactored from a module-level shared connection to a `threading.local()` per-thread connection:

```python
# Before (PR #5)
_conn: sqlite3.Connection | None = None

def app_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect("data/stride.db")
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=DELETE")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn
```

```python
# After (PR #20)
_local = threading.local()

def app_db() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect("data/stride.db")
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=DELETE")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn
```

The change is twelve lines. The consequences of not making it are severe.

---

## Why SQLite Connections Are Not Thread-Safe

SQLite connections are not safe to share across threads. This is not a SQLite limitation so much as a fundamental correctness constraint: a connection tracks its own transaction state, cursor state, and error state. Two threads simultaneously using the same connection produce undefined behaviour — they may overwrite each other's cursor positions, interleave transactions, or trigger the `check_same_thread` assertion that produces the `InterfaceError`.

SQLite includes a `check_same_thread` parameter:

```python
conn = sqlite3.connect("stride.db", check_same_thread=False)
```

This flag disables the assertion. It does not fix the underlying problem — it removes the safety check while leaving the unsafety. Disabling `check_same_thread` is sometimes described as the fix for the `InterfaceError`. It is not. It is a way to suppress the error while the underlying concurrency bug continues to corrupt data silently.

The correct solution is one connection per thread.

---

## Dash's Concurrency Model

Dash runs on Flask's development server in single-threaded mode during early development. In production (via `gunicorn` or Dash's own production server), it uses a thread pool. Each incoming request may be handled by a different thread.

For Stride on App Runner, the thread pool is configured implicitly by `uv run stride` — Dash's built-in server with default threading. In development with `debug=True`, Flask uses a single thread, which is why the bug was invisible during initial development. The single thread meant requests were always processed sequentially by the same thread with the same connection.

Adding a second browser tab changed this: the two tabs could send simultaneous requests, and the Flask server's thread pool would handle them on different threads — each reaching for the module-level `_conn` that was created on whichever thread initialised it first.

---

## Why `threading.local()` Instead of a Connection Pool

The alternatives to `threading.local()`:

**A connection pool** (like SQLAlchemy's pool or `queue.Queue` of connections) manages a fixed set of connections and lends them to callers on demand. This is the correct approach for high-concurrency web applications where the thread pool is large or where connection creation is expensive (Postgres: establishing a TCP connection, authenticating, initialising session state — this takes 50-100ms).

For SQLite, connection creation is opening a file — measured in microseconds. Stride's thread pool has at most a handful of concurrent threads. A connection pool would add complexity (checkout/checkin, pool exhaustion handling, connection health checks) for zero measurable benefit.

**A singleton connection with a lock** would work but serialises all database access through one connection, eliminating any concurrency benefit from the thread pool.

`threading.local()` is the simplest correct solution: one connection per thread, created lazily on first access by that thread, reused for all subsequent requests on that thread. Five lines of code, correct, no ongoing maintenance.

---

## The Risk Before the Fix

Before PR #20, the module-level connection was created on the first thread to call `app_db()`. Every subsequent call from any thread returned the same connection object. The consequence depends on the access pattern:

**Sequential requests (single user, no overlap):** Works. The single thread creates the connection and reuses it. No concurrency, no problem.

**Overlapping requests (rapid clicking, multiple tabs):** Fails. Two threads attempt to use the same connection simultaneously. Possible outcomes: `InterfaceError` (the visible symptom), corrupted cursor state (silent, incorrect data returned), corrupted transaction (silent write loss). The `InterfaceError` is actually the best outcome — it surfaces the bug visibly.

**The worst case is no error:** A shared connection that happens to serve concurrent requests without raising `InterfaceError` may still produce silently incorrect results — rows from one request's cursor appearing in another request's result set. This produces mysterious, unreproducible data inconsistencies.

---

## What the AI-Assisted Workflow Actually Looked Like

The bug was diagnosed from the `InterfaceError` traceback. The stack trace pointed to `app_db()` returning a connection and a callback using it on a different thread than where it was created.

The `threading.local()` fix was AI-suggested immediately from the error message. The explanation — "one connection per thread, `threading.local()` is the correct pattern for per-thread singletons in Python" — was already in my knowledge from prior projects. The AI confirmed it was the correct approach for SQLite specifically.

The `check_same_thread=False` alternative was explicitly rejected in the PR description: "This flag disables the check, not the problem. We need per-thread connections, not disabled safety checks."

The fix was written, tested under concurrent access (two rapid clicks in two browser tabs), and committed as a single focused PR.

---

## What This Unlocks

Concurrent safety. Multiple browser tabs, rapid interactions, future production load — all handled correctly. The `threading.local()` pattern also means the connection factory is correct for any deployment model, from single-thread development to multi-worker production.

The pattern is now the foundation for every future database interaction. New service functions written after PR #20 inherit thread safety automatically — they call `app_db()` and get a thread-local connection.

---

## Takeaway for Consultants

Never share a SQLite connection across threads. `check_same_thread=False` suppresses the safety assertion without fixing the underlying problem; disabling it in production is asking for silent data corruption. `threading.local()` is the correct, cheap, zero-overhead solution.

More broadly: concurrency bugs are invisible during single-user, single-tab, non-overlapping request development. Test your application with concurrent access before shipping. Open two browser tabs and click rapidly. The bugs that appear are real production bugs that were always there.

---

## LinkedIn Summary

Stride had a latent SQLite thread-safety bug from day one: a shared module-level connection used by every Dash callback, across every thread in the pool. It was invisible under single-threaded development and catastrophic under any concurrent access. The fix was `threading.local()` — five lines, one connection per thread, created lazily. The `check_same_thread=False` flag that most Stack Overflow answers suggest is not a fix — it removes the safety check while leaving the bug. Know the difference.
