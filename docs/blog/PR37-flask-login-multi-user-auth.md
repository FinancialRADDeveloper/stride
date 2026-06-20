# From One Desk to Three: Adding Authentication to a Single-User Dash App

There is a moment in the life of every research tool when it works well enough that someone else wants to use it.

For a quant researcher at a hedge fund, that moment is both gratifying and uncomfortable. The tool runs on your machine, in your environment, against your data. It was never designed to have multiple users — it was designed to have *you*. Handing it to a portfolio manager or a second researcher means confronting every assumption you made when "production" meant closing your laptop and going home.

Stride hit that moment this week. The app works. A friend asked if his wife and a friend could use it too. That is not a product milestone — it is a structural problem. Until now, the app had no concept of identity. Every visitor saw the same board, the same tasks, the same everything. Adding a second user would not give them their own workspace; it would give them yours.

PR #37 fixes the foundation layer: authentication. Every feature that follows — isolated task boards, per-user settings, the reading list — will build on what lands here.

---

## Why Username/Password, Not OAuth

The first question was what kind of authentication to use. Three obvious candidates:

**Google OAuth** is the easy answer for most web apps. It delegates the hard work — credential storage, session management, 2FA — to a provider that does it well. The catch is that it requires a Google account. John Hawkins is deep in the Apple ecosystem. Requiring Google accounts as a prerequisite for a productivity app that has nothing to do with Google is unnecessary friction for users you know personally.

**Magic links** — send a one-time sign-in link to an email address — have the advantage of requiring no password at all. No stored credentials, no forgotten passwords, no password reset flow to build. The catch is that they require a live transactional email service from day one. Adding a Mailgun dependency just to onboard three users to a prototype felt like the wrong order of operations.

**Username and password** is the well-worn path. Everyone understands it. It has no external dependencies. Werkzeug — already a Flask dependency — ships `generate_password_hash` and `check_password_hash` built on PBKDF2-HMAC-SHA256, so there is no hand-rolled crypto to worry about. The password reset flow needs an email service eventually, but it can stub to a log line while the rest of the system is being built.

The decision was username/password. Not because it is the most sophisticated option, but because it is the most appropriate one for the current stage and the current set of users.

---

## The Architecture: Flask Inside Dash

Dash is a Flask application. This is easy to forget when you are writing callbacks, but it matters enormously when you need to add HTTP-layer behaviour. Flask-Login — the standard Flask session management library — attaches directly to the Flask server that Dash runs on.

The integration has a few non-obvious requirements.

**Template folder.** Dash manages its own Jinja2 environment for its internals, but the login pages need to be served as ordinary Flask-rendered HTML, not as Dash component trees. The solution is to pre-create the Flask server with a `template_folder` argument before handing it to Dash:

```python
server = Flask(__name__, template_folder=_TEMPLATES_DIR)
app = dash.Dash(__name__, server=server, ...)
```

If you let Dash create the server and try to set `template_folder` afterwards, Jinja2's loader is already configured and your templates will not be found.

**The session guard.** Flask-Login's `before_request` hook intercepts every incoming HTTP request before it reaches any route handler or Dash callback. The guard is simple: if the path is not in a whitelist of public routes, and the user is not authenticated, redirect to `/login`.

The whitelist matters. `/login`, `/logout`, `/forgot-password`, `/reset-password`, `/health`, and `/assets/` all need to be reachable without authentication. Get the list wrong and you lock the login page itself behind the login page.

**User identity in callbacks.** This is the subtlest part. `current_user` from Flask-Login is only valid during an HTTP request — during the Flask request context. Dash callbacks run asynchronously, in a thread pool, without a request context. Calling `current_user` inside a callback will either return the wrong user or raise an error.

The pattern that works: capture the user's id at layout-render time, seed it into a `dcc.Store`, and pass it into callbacks as `State`. The layout function is called per HTTP request, so `current_user` is valid there. Once it is in a store, callbacks can read it reliably without touching Flask-Login at all:

```python
def _layout():
    uid = current_user.id if current_user.is_authenticated else ""
    return dmc.MantineProvider(children=[
        ...
        dcc.Store(id="store-user-id", data=uid),
    ])
```

Every subsequent PR that needs to scope data to a user will read from `store-user-id` as `State`. The pattern is set once here and reused everywhere.

---

## The Service Layer

`stride/services/auth.py` contains all user and token operations: `create_user`, `get_user_by_email`, `get_user_by_id`, `verify_password`, `set_password`, `generate_reset_token`, `validate_reset_token`, `consume_reset_token`.

It has zero imports from Dash or Flask. Every function takes a `sqlite3.Connection` as its first argument. This is not accidental — it means the entire auth surface can be tested with a plain Python test runner, no app required. It means the CLI can call it without booting the web server. It means the functions compose with the same patterns used everywhere else in the codebase.

The reset token design is worth noting: tokens are UUIDs, stored in a `login_tokens` table with a 15-minute expiry timestamp and a `used_at` column. `validate_reset_token` checks expiry and that `used_at IS NULL`. `consume_reset_token` sets `used_at` to now. Single-use enforcement is a database query, not application state — which means it survives server restarts and scales across processes.

---

## Security Details That Are Easy to Miss

**User enumeration.** The forgot-password endpoint must return the same response whether or not the email address is registered. If "that email doesn't exist" is a different response from "check your inbox", an attacker can probe for valid accounts by automating requests and reading the response. The implementation generates the token internally if the user exists, but always renders the same message: "If that address is registered, a reset link has been sent." GitHub, Auth0, and every serious auth provider use this pattern.

**Open redirect.** After login, the route reads a `next` query parameter to redirect the user to wherever they were going before the auth guard intercepted them. Without a check, an attacker can craft a link like `/login?next=https://evil.com` and use Stride's login page to redirect to an arbitrary URL after credentials are submitted. The guard is one line:

```python
if not next_url.startswith("/"):
    next_url = "/"
```

Trivial to add, often forgotten.

**Password hashing.** Werkzeug's `generate_password_hash` uses PBKDF2-HMAC-SHA256 with a random salt by default. No configuration required. The output includes the algorithm, iterations, salt, and hash in a single string — future-proof against algorithm upgrades because the stored string is self-describing. `check_password_hash` reads the algorithm from the stored string, so a future migration to Argon2 can be done row by row as users log in without invalidating existing sessions.

---

## Admin-Seeded Accounts

There is no self-registration in v1. The `create-user` CLI command is the registration surface:

```bash
stride create-user --email steph@example.com --name "Steph"
# Prompts for password and confirmation, hidden input
```

For three known users, this is the right model. Self-registration adds complexity — email verification to prevent fake accounts, spam risk, account management UI — that is wasted investment at this scale. When Stride moves toward a hosted product with unknown users, self-registration is a one-PR addition on top of the infrastructure already in place.

---

## Commit Sequence

```
feat: users and login_tokens migration (0003_users.sql)
feat: auth service layer — create_user, verify_password, reset tokens
feat: Flask-Login integration — User model, LoginManager, before_request guard
feat: auth routes blueprint + HTML templates, wire into create_app
feat: Dash layout captures current_user — store-user-id + topbar user chip
feat: create-user CLI command — admin seeds accounts for Steph and John
```

Migration first, because nothing else compiles without the schema. Service layer second — it is the testable core that everything else depends on. Flask-Login wiring third. Routes and templates fourth, once the wiring existed to back them. Layout changes fifth, once the routes were in place to validate against. CLI last, as a consumer of the service layer.

The sequence is not just aesthetic. Each commit is independently deployable. If the template styling turned out to need revision after stakeholder review, the service layer and the session guard would be unaffected. If the CLI needed a different UX, the web auth flow would not change. Separating concerns in commits is how you keep a feature reviewable as it grows.

---

## What This Unlocks

Authentication is infrastructure, not a feature. Nobody signs in to Stride because they enjoy signing in — they sign in because it is the price of having their own workspace.

The board itself does not yet enforce user isolation. All three users, once they have accounts, will see the same tasks. That changes in the next PR, which adds `user_id` to the tasks table and scopes every query accordingly. Auth had to come first, because you cannot scope data to a user identity that does not exist yet.

The pattern here — establish identity before enforcing isolation — is the same pattern you follow in any multi-tenant system. Get the identity layer right, make it testable, make it a stable foundation, then build the data boundaries on top of it.

---

## The Broader Lesson

The quant researcher's journey from "runs on my machine" to "runs for the team" always goes through authentication. It does not matter whether the tool is a risk dashboard, a relative value model, a convertible bond scanner, or a personal task board. The moment a second user needs access, you need identity.

Most researchers delay this as long as possible. The cost of delaying is that you end up retrofitting identity into a system that was never designed for it — and retrofit auth is always messier than designed auth. The data model assumes one user. The queries have no user scoping. The session management is an afterthought. You end up in a multi-week refactor to add something that would have been a clean two-PR addition if you had done it before the first feature.

The lesson is to add the auth skeleton early, even before you need it, even if the first version just has one user. The skeleton here — User model, session guard, service layer, CLI account creation — is forty lines of real code and a migration file. The skeleton is cheap. The retrofit is not.
