# Dependency Hygiene: Removing Tooling Overhead and Pivoting to Antigravity

In the world of modern Python development, there is a constant temptation to adopt the latest, shiniest tooling under the banner of speed and modern standards. I fell into this pattern early in Stride's development by introducing `uv`—a blazing fast Rust-based package resolver—to manage the application's environment and virtual environments.

But as the project progressed toward containerisation and a Docker-first local setup, a subtle friction emerged: if the application primarily runs inside a container, why are we adding the complexity of a secondary, non-standard tool like `uv` on the host and inside the Docker layers? 

PR #35 is a clean-up commit that strips out `uv` in favour of standard Python packaging (`pip` + `requirements.txt`), simplifies the Docker runtime, and marks a tooling pivot as we switch from Claude Code to Antigravity for our developer partner.

---

## Vibe Coding vs. Deliberate Tooling

I have nothing against `uv` itself—it is an impressive piece of engineering. However, my personal and professional experience has been anchored in standard `pip` and `poetry`. 

Allowing a tool like `uv` to creep into the codebase without a dedicated learning session or structured comparison felt like a symptom of **vibe coding**—where tools and dependencies are accepted simply because they were recommended in the moment or seemed convenient, rather than being chosen through a deliberate engineering process.

If we are going to adopt a new tool like `uv`, it should be a point of discussion in its own right. In the future, I plan to write an article or raise a PR specifically analyzing the trade-offs of `pip`, `poetry`, and `uv` in both local environments and Docker containers. But until we have that structured evaluation, it is better to stick to the standard, highly understood baseline of `pip` and `requirements.txt`.

By stripping `uv` out, we aligned local dev and containerization:
1. We created clean, explicit [requirements.txt](file:///c:/Code/stride/requirements.txt) and [requirements-dev.txt](file:///c:/Code/stride/requirements-dev.txt) files.
2. We deleted `uv.lock`.
3. We updated the [Dockerfile](file:///c:/Code/stride/Dockerfile) to use standard, cached `pip install` commands.
4. We replaced the command in [.claude/launch.json](file:///c:/Code/stride/.claude/launch.json) to boot the Dash app directly using `python -m stride run`.

---

## Toward Dev Containers: Local to AWS Parity

The long-term vision for Stride’s developer experience is to transition toward a **Dev Container** model. 

In a typical python project, developers spend too much time configuring their local machines—managing python versions, virtual environments, path variables, and IDE quirks, particularly when developing across disparate systems like PyCharm on Windows or integrating with agentic workflows like Antigravity. 

Our goal is to reduce local configuration to almost zero:
* **Production Mirror:** Whatever container image we run in AWS is the exact same environment we should run locally.
* **Environment Isolation:** Local development should happen entirely inside a container environment. 
* **Reduced Friction:** A developer should be able to clone the repository and run `docker compose up` without worrying about their host machine's Python version or venv setup.

Removing host-level dependency managers like `uv` is a step toward this parity. It forces us to ensure the Docker container is the self-contained, authoritative source of truth for the application runtime.

---

## What We Learned

### 1. Caching Dependencies Without UV
One of the main reasons for using `uv` inside Docker was build-time caching. However, you can achieve the same caching behaviour with standard `pip` by copying only `requirements.txt` before copying the application source code:

```dockerfile
# Install dependencies first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and pyproject.toml to install stride package
COPY stride/ stride/
COPY pyproject.toml ./

# Install stride package itself without reinstalling dependencies
RUN pip install --no-cache-dir --no-deps .
```

Docker caches the `pip install` layer. As long as `requirements.txt` doesn't change, rebuilding the image after a source code change takes seconds.

### 2. Keep Local Main Equal to Remote Main
When doing small, iterative development cycles, never assume your local `main` matches the remote. Always run `git fetch` and align your local branches with `origin/main` before branching. Diverging from the remote leads to merge conflicts, lost history, and stale assumptions.

---

## Next Steps

With the database, UI, drag-and-drop, achievements panel, and overdue alerting successfully running on a clean, `uv`-free standard Python foundation, we are ready to move forward. The next step is the implementation of **Phase 5 (Google Calendar Sync)**, which will be developed on a dedicated feature branch.
