# The Stale Client Problem: Auto-Reloading After Server Redeploys

Every deployment of Stride to App Runner produces a new container with a new set of Dash callback fingerprints. The old browser tab, still open, has the fingerprints from the previous deployment. When it tries to execute a callback — moving a task, opening the drawer, navigating weeks — the server rejects it:

```
Callback fingerprint mismatch. Expected <new_hash>. Got <old_hash>.
```

The page is broken until the user does a hard refresh. For a tool you leave open all day, this means discovering the app is broken mid-task, figuring out why, and manually reloading. It is the kind of friction that accumulates into "I stopped using this."

PR #26 eliminated it.

---

## What We Built

A clientside callback that polls the server's callback fingerprint every 60 seconds and triggers an automatic page reload if the client's fingerprint does not match the server's:

```python
app.clientside_callback(
    """
    function(n_intervals) {
        fetch('/_dash-layout')
            .then(r => r.json())
            .then(layout => {
                var serverFingerprint = layout.props && layout.props.children
                    ? layout._dash_layout_fingerprint
                    : null;
                if (!serverFingerprint) return;
                if (!window._strideFingerprint) {
                    window._strideFingerprint = serverFingerprint;
                    return;
                }
                if (window._strideFingerprint !== serverFingerprint) {
                    window.location.reload();
                }
            });
        return window.dash_clientside.no_update;
    }
    """,
    Output("dummy-reload-output", "children"),
    Input("tick", "n_intervals"),
)
```

The callback fires on the 60-second `tick` interval. It fetches Dash's internal `/_dash-layout` endpoint and reads the layout fingerprint. On first load, it stores the fingerprint in `window._strideFingerprint`. On subsequent ticks, it compares the current server fingerprint to the stored one. A mismatch triggers `window.location.reload()`.

---

## Why This Problem Exists

Dash generates callback fingerprints from the callback graph — every registered callback's input/output specification is hashed to produce a unique identifier. This fingerprint is embedded in the page when it loads and sent with every callback request. The server validates that the client's fingerprint matches the current callback graph before executing any callback.

This is a security and consistency mechanism: it prevents stale clients from executing callbacks against a newer server that may have changed the callback signature. If the client sends a callback request with arguments from the old signature and the server has a new signature, the execution would be undefined.

After a deployment, the server's callback graph has changed (even if only slightly — a new callback was added, a parameter was renamed). The browser's cached fingerprint is stale. Every callback fires the fingerprint mismatch error.

---

## Client-Side Check vs Server-Side Push

Two approaches to detecting server redeployment from the browser:

**Server-side push (WebSockets):** The server sends a "you are stale, reload" message when a new deployment starts. This requires a WebSocket connection, a deployment hook that triggers the push, and handling for the case where the WebSocket connection itself is stale. For a containerised application where the old container is simply replaced by a new one, the WebSocket connection drops at deployment — which could itself be a reload signal, but handling WebSocket disconnects in Dash requires more infrastructure.

**Client-side polling:** The browser periodically asks the server "what fingerprint are you running?" If the answer differs from what it loaded with, it reloads. This is simpler, does not require server-side infrastructure changes, and tolerates the brief window between old container shutdown and new container startup (during which polls fail and are silently ignored).

Client-side polling is the right choice here. The 60-second interval means worst-case staleness is 60 seconds — the user may execute one stale callback request per deployment cycle. This is acceptable for a personal tool. The reload is silent when the user is idle (the tab is not interacted with during the 60-second tick window); if the user is actively interacting, the reload happens on the next tick.

---

## The `/_dash-layout` Endpoint

Dash exposes several internal endpoints. `/_dash-layout` returns a JSON representation of the application layout, including a fingerprint field that changes when the callback graph changes.

Using this endpoint is slightly fragile — it is an internal Dash API that could change between Dash versions. A more robust approach would be a dedicated `/version` endpoint that the server explicitly manages and the client polls. This approach was deferred because the Dash version is pinned and the internal API is stable within that version.

The alternative endpoint approach:

```python
@server.route("/version")
def version():
    import os
    return {"version": os.environ.get("DEPLOY_SHA", "dev")}
```

The CI pipeline sets `DEPLOY_SHA` to the git commit SHA on every build. The client polls `/version` and compares the SHA to the one it loaded with. This is more robust and explicit — but requires the CI pipeline to set the environment variable. It is the right architecture for a team product. For a personal tool, polling `/_dash-layout` is acceptable.

---

## User Experience Considerations

When does the reload fire?

**User is idle:** The tab is open but not being interacted with. The 60-second tick fires, the fingerprint mismatch is detected, `window.location.reload()` fires. The page reloads silently — the user may not even notice if they are not looking at the tab.

**User is actively interacting:** The user is mid-task. The tick fires at a slightly inconvenient moment. The page reloads, clearing any unsaved state in the composer or the drawer. This is unfortunate but brief — blur-save in the drawer means the most recent edits are already in the database.

**Deployment happens mid-task:** The user submits a callback. The server rejects it with a fingerprint mismatch. The callback fails with an error. The user sees broken UI. The fix: the next tick fires (within 60 seconds) and reloads the page.

The sweet spot for the tick interval is between "annoying if you are interacting" (too short) and "too long to be useful" (too long). 60 seconds was chosen as a reasonable compromise. Most deployments happen during low-use periods (overnight, during breaks). The 60-second window means the reload is unlikely to interrupt active use.

---

## The Trade-offs, Honestly

A page reload clears in-progress work. If the user is composing a new task in the composer when the reload fires, the partially-typed title is lost. Blur-save protects drawer edits but not composer input. The mitigation — saving composer state to a store that persists across reloads — would add complexity. Deferred.

The `/_dash-layout` polling adds one HTTP request per 60 seconds. For a personal tool, this is negligible. For a high-traffic shared deployment, polling from every client would add meaningful load. The `/version` endpoint approach (a lightweight static response) is better for shared deployments.

---

## What the AI-Assisted Workflow Actually Looked Like

The problem was observed directly: deploying a new image broke the open browser tab. The fingerprint mismatch error was clear from the browser console. The solution — poll for fingerprint changes, reload on mismatch — was specified. The AI generated the clientside callback and the fetch pattern.

The `window._strideFingerprint` initialisation guard (store on first load, compare on subsequent loads) was specified to prevent the first poll from always triggering a reload (comparing undefined to the current fingerprint would always be a mismatch).

---

## What This Unlocks

A deployment experience where browser tabs silently update when the server is redeployed. The development cycle becomes: push a fix, watch the GitHub Actions CI pass, know that open browser tabs will update within a minute without any user action.

---

## Takeaway for Consultants

Stale clients after server redeployments are a source of silent breakage in any Dash application. The fingerprint mismatch error is clear but opaque to users who do not have the developer console open. Polling for fingerprint changes and auto-reloading is a simple, effective fix that eliminates the "why is this broken?" support request.

For team applications, a dedicated `/version` endpoint with the deployment SHA is more robust than relying on Dash's internal `/_dash-layout`. For personal tools, the internal endpoint is acceptable with a pinned Dash version.

---

## LinkedIn Summary

Every Stride deployment created a stale-client problem: open browser tabs had old callback fingerprints that the new server rejected. PR #26 fixed it with a 60-second clientside poll that auto-reloads when the server fingerprint changes. Client-side polling over server-side WebSocket push: simpler, no infrastructure changes, tolerates the deployment window. The reload is silent when you're idle and brief when you're not. Silent fixes for background infrastructure friction are the best kind.
