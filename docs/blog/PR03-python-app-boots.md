# The Blank Screen That Matters More Than Any Feature

The first thing I want from a new project is a blank screen that starts.

Not a feature. Not a database. Not a login page. A blank screen that starts — where running `uv run stride` in a terminal produces a browser tab with something on it, no errors, no dependency conflicts, no "works on my machine" caveats. Every feature built after that point has the same starting guarantee: it boots.

PR #3 is that blank screen. Here is why it deserves its own article.

---

## What We Built

Three things in this PR, and they are carefully ordered:

1. A `pyproject.toml` with `uv` as the package manager, defining `stride` as the project name and entry point
2. A minimal Dash application (`stride/app.py`) that renders a single heading and serves on port 8050
3. A `/health` endpoint returning `{"status": "ok"}` at `GET /health`

That is the entire feature set. The app shows `html.H1("Stride")` in a browser. The health endpoint returns a JSON blob. Nothing else.

---

## Why uv

The Python packaging ecosystem has evolved substantially. For this project, the choices were `pip`, `pip-tools`, `poetry`, `conda`, and `uv`. Here is why `uv` won.

**Speed.** `uv` resolves and installs dependencies faster than any other tool in the Python ecosystem by a significant margin. On a clean environment, `uv sync` runs in seconds. `pip install -r requirements.txt` on the same dependency list takes several times longer. For a project where I would be frequently rebuilding Docker images and creating new environments, this matters.

**Lockfile semantics.** `uv.lock` is a complete, reproducible snapshot of every transitive dependency at exact versions. `pip freeze > requirements.txt` captures installed versions but not the dependency graph. `uv.lock` captures both, which means `uv sync` from a lockfile produces bit-identical environments on any machine.

**Single command for development.** `uv run stride` discovers the entry point from `pyproject.toml`, activates the virtual environment, and runs the application. No manual `source venv/bin/activate`, no `python -m stride`. One command, always works.

**Modern `pyproject.toml` standard.** `uv` uses the PEP 517/518 standard `pyproject.toml` format. There is no `setup.py`, no `setup.cfg`, no separate `requirements.txt` for development vs production dependencies. One file describes the project completely.

The trade-off: `uv` is newer and less universally known than `pip`. If a contributor is unfamiliar with it, the `README.md` install instructions are two lines (`curl -LsSf https://astral.sh/uv/install.sh | sh` then `uv sync`). This has never been a problem in practice.

---

## The Health Endpoint Is Not Optional

A `/health` endpoint returning `{"status": "ok"}` sounds like infrastructure boilerplate. It is, and that is exactly the point.

Dash runs on top of Flask. Flask allows adding arbitrary routes alongside the Dash application using `server.add_url_rule(...)`, where `server` is the underlying Flask application instance. The health endpoint is registered at startup:

```python
server = app.server

@server.route("/health")
def health():
    return {"status": "ok"}
```

Docker's `HEALTHCHECK` instruction calls this endpoint. AWS App Runner calls this endpoint. The compose file calls this endpoint. Every deployment and container orchestration mechanism that Stride will ever run in expects a health endpoint. Adding it in PR #3 — before any of those mechanisms exist — means it will never be forgotten.

The alternative is to add it "when we containerise," which is PR #17. By then, the health check is a one-line afterthought you have to remember to add. Having it from day one means it is part of the application's contract, not an infrastructure afterthought.

---

## The Key Decision: Port 8050, Not Customisable Yet

Dash's default port is 8050. PR #3 hard-codes it. This is acceptable for the first working version and was replaced with environment variable configuration before the containerisation PR. But making the app boot quickly matters more than making it configurable before there is any configuration context.

The principle: make it work, then make it correct, then make it configurable. Never add configuration for things that only have one value yet.

---

## The Trade-offs, Honestly

A blank screen that boots is not a deliverable. If you showed this to a client or a stakeholder, they would not be impressed. Its value is entirely internal — it establishes a baseline that every subsequent commit has to maintain. If PR #4 introduces a Python syntax error that prevents the app from starting, that is immediately visible because there was a working baseline to break.

This is the argument for walking skeleton development: build the thinnest possible slice through every architectural layer early, then fill it in. Stride's walking skeleton is `uv run stride` → Flask dev server → Dash app → browser. From PR #3 forward, every PR that breaks this chain is caught before merge.

The health endpoint adds a tiny amount of complexity — one function, one route registration. The benefit is a consistent deployment contract. The cost approaches zero.

---

## What the AI-Assisted Workflow Actually Looked Like

`pyproject.toml` and `uv` setup: AI-generated from the brief "Dash application, Python 3.12, uv package manager, entry point is `uv run stride`." The generated file was correct on the first pass.

The Dash application boilerplate: one page, one heading, Flask server extraction. Standard pattern, AI-generated, reviewed for the health endpoint pattern.

The health endpoint: I specified "add a `/health` endpoint returning JSON `{"status": "ok"}`." This is a solved problem; the implementation is unambiguous.

The valuable decision-making in this PR was about `uv` over alternatives and about including the health endpoint from day one. Those decisions were made before any code was generated.

---

## What This Unlocks

Every PR from here builds on a working foundation. The CI pipeline (added in PR #17) runs `docker build` + container health check — it passes from day one because the health endpoint already exists. The deploy scripts expect a `/health` response — they work because the endpoint was defined in the application contract, not bolted on later.

More practically: `uv run stride` works from any clean checkout. New contributors (or future me on a new machine) can run the application in under a minute without reading a setup guide. That ergonomic baseline is worth protecting.

---

## Takeaway for Consultants

The first thing a project needs is not a feature — it is a working skeleton that boots. A blank screen that starts successfully is the foundation that makes every subsequent commit testable. Add your health endpoint before you need it. Choose your package manager deliberately and document the reasoning. These decisions are permanent; changing them later is expensive and disruptive.

A project that does not boot is not a project. A project that boots with one heading is a project you can build on.

---

## LinkedIn Summary

PR #3 for Stride is a Dash app that shows a single heading. That is it. But it boots, it has a health endpoint, and it uses `uv` for sub-second dependency resolution. The principle: get the skeleton working before building anything else. Every feature after this had a working baseline to break — and that makes every regression visible immediately. Walking skeleton development is the cheapest form of integration testing.
