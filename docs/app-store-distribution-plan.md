# Stride — App Store Distribution Plan

## Product Vision

The mobile app is **not** a cut-down version of the desktop board. It is a full-featured **ambient productivity companion** for a different context of use:

- **Quick capture** — a thought hits you while you're out ("need to replace the router, just broke"). Add it before it evaporates. Minimum taps.
- **Today glance** — you're between meetings. What's actually on for today?
- **Proactive alerts** — the app surfaces things rather than waiting for you to check:
  - *"You have 7 things to do today, 3 are overdue"* (daily briefing)
  - *"This task has been sitting since Monday"* (nudge)
  - *"You need to leave now — your meeting's in 20 minutes and you're 15 away"* (location-aware)
  - *"You seem to be near the office — 4 tasks flagged for today"* (geofencing context)

Desktop = plan and review. Mobile = capture anywhere + ambient awareness. Same data, different mode of engagement.

---

## Executive Summary

Stride's fastest path to both app stores: (1) convert to a PWA today, (2) wrap as a TWA for Google Play within a week, (3) wrap with Capacitor.js for iOS App Store within a month. A React Native/Flutter rewrite is unnecessary. The single biggest risk is Apple rejecting a thin web wrapper — Capacitor mitigates this by enabling genuine native features (push notifications, location services, haptics) that satisfy their "minimum native value" bar and deliver the proactive alert vision above.

---

## Recommended Sequence

```
Week 1–2:  PWA (manifest + service worker + Lighthouse audit)
Week 2–3:  Google Play via Bubblewrap TWA
Week 4–6:  Apple Developer enrollment + Capacitor + push notifications + App Store submission
```

**Minimum viable "feels like an app" milestone:** Complete the PWA in week 1. Users on Android can install from Chrome immediately — no app store needed. This alone is 80% of the user experience win.

---

## Phase 1 — PWA Foundation (prerequisite for everything)

See `docs/mobile-responsiveness-plan.md` for implementation details. Required for both store tracks:

- `manifest.json` in `stride/assets/` (Dash auto-serves everything in `assets/`)
- `sw.js` service worker registered via `app.index_string`
- Viewport meta tag
- HTTPS (already provided by App Runner)

**Milestone:** Stride installs from Chrome on Android like an app.

---

## Phase 2 — Google Play via TWA

### What is a TWA?

A Trusted Web Activity is an Android shell that renders a full-screen Chrome Custom Tab pointing at your HTTPS URL. Google officially endorses this as a first-class submission path.

### Requirements

- Valid PWA (manifest + service worker + HTTPS)
- `assetlinks.json` at `https://takeitinyourstride.com/.well-known/assetlinks.json` linking your Android signing key to your domain
- Icons at 192×192 and 512×512 PNG (maskable recommended)

### Tooling

**Bubblewrap CLI** (recommended for signing control):
```
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://takeitinyourstride.com/manifest.json
bubblewrap build
```
Output: signed `.aab` ready for Play Store upload.

**PWA Builder** (pwabuilder.com): Web GUI — useful for auditing the PWA first, then use Bubblewrap for the final build.

### Submission

1. Create Google Play Developer account ($25 one-time)
2. Play Console → Create app → Upload `.aab`
3. Store listing: description, screenshots (browser screenshots are fine), privacy policy URL (required)
4. Internal testing track → promote to production
5. Review time: 1–3 days

### Rejection risk: LOW

TWA is Google-endorsed. Ensure `assetlinks.json` is correct and the offline fallback works. Test with Google's [Digital Asset Links verification tool](https://developers.google.com/digital-asset-links/tools/generator).

**Critical:** Back up the Bubblewrap keystore file immediately after generating it. Losing it means you cannot push updates to the app.

---

## Phase 3 — iOS App Store via Capacitor.js

### Why Capacitor, not WKWebView

Apple's Guideline 4.2 ("Minimum Functionality") rejects apps whose sole function is to display a website accessible in Safari. A plain WKWebView shell has an estimated 30–50% rejection rate (2024–2025 community data).

**Capacitor.js** produces a real Xcode project and exposes a plugin API for native iOS capabilities. Adding push notifications alone substantially reduces rejection risk and adds genuine user value.

### Integration with a server-rendered Dash app

Capacitor supports "server mode" — point it at your live URL instead of a local bundle:

```json
// capacitor.config.json
{
  "appId": "com.vinalytics.stride",
  "appName": "Stride",
  "server": {
    "url": "https://takeitinyourstride.com",
    "cleartext": false
  }
}
```

Dash callbacks (which POST to the server) pass through transparently. Session cookies work normally since the app talks to a real HTTPS origin.

### Setup steps

```
npm init
npm install @capacitor/core @capacitor/cli @capacitor/ios \
  @capacitor/push-notifications \
  @capacitor/geolocation \
  @capacitor-community/background-geolocation
npx cap add ios
npx cap open ios   # opens Xcode
```

Then configure signing, add plugins, wire up Flask backend to FCM/APNs.

### Native plugins for the ambient companion vision

| Plugin | Purpose |
|---|---|
| `@capacitor/push-notifications` | Daily briefing, overdue nudges, manual reminders |
| `@capacitor/geolocation` | One-shot location check when app is open |
| `@capacitor-community/background-geolocation` | Geofence triggers while app is backgrounded ("you're near the office") |
| `@capacitor/haptics` | Tactile feedback on quick-add confirmation |
| `@capacitor/local-notifications` | Scheduled alerts ("leave now" countdown) without server round-trip |

The geofencing plugin is the feature that makes this genuinely different from a bookmarked website. It requires the "Always On" location permission on iOS — Apple scrutinises this, so the App Review notes must clearly explain the user benefit.

### Backend additions for proactive alerts

The Flask backend needs two new responsibilities:

1. **Daily briefing job** — runs at (configurable) 8am, queries tasks due today + overdue, pushes via FCM to user's device token
2. **Task deadline engine** — when a task is due within N hours and not done, push a nudge

Both are Flask endpoints triggered by a lightweight scheduler (APScheduler, already easy to add to the Flask app) or AWS EventBridge scheduled rule calling an App Runner endpoint.

### Push notifications backend

Use Firebase Cloud Messaging (FCM) — it abstracts both APNs (iOS) and FCM (Android) in one API. The Python backend uses the Firebase Admin SDK:

```python
pip install firebase-admin
```

FCM handles APNs certificate management. This is significantly simpler than direct APNs integration.

### Submission

1. Enroll in Apple Developer Program ($99/year — business enrollment via Vinalytics takes 1–3 weeks if DUNS number needed; personal enrollment is faster)
2. Configure provisioning profiles in Xcode (use automatic signing initially)
3. TestFlight internal testing → App Store Connect submission
4. Review time: up to 7 days. Budget 1–2 resubmission cycles.

### What Capacitor Python/Dash developers can do unassisted

- Capacitor setup and `capacitor.config.json` — JSON config + npm commands
- Firebase/FCM backend — Python Flask + Firebase Admin SDK (well-documented)
- App Store Connect metadata and screenshots — tedious but no skill gap

### What requires learning

- Xcode provisioning profiles and signing — steep first-time setup but well-documented. Budget 1–2 days.
- APNs certificate management — use FCM to avoid this entirely.

---

## Developer Account Costs

| Account | Cost | Notes |
|---|---|---|
| Google Play Developer | $25 one-time | No annual renewal |
| Apple Developer Program | $99/year | Required for App Store + TestFlight. App removed if lapsed. |
| Bubblewrap / Capacitor CLI | Free | Open source |
| Mac hardware | $0 if you have one | Xcode requires macOS. MacStadium ~$50/mo if not. |
| Firebase FCM | Free tier | Sufficient for small scale |
| App icons | $0 DIY in Figma | 1024×1024 master → export variants |

**First-year total (both stores, assuming you have a Mac):** ~$125 USD.

---

## The Dash Constraint

### Offline support

Dash is server-rendered — every callback is a network round-trip. Meaningful offline support is not feasible without significant architecture changes. **Do not cache `/_dash-*` routes in the service worker** — these are live endpoints and cached responses will cause silent breakage.

Practical approach: cache only static assets (`/assets/*`). Provide a graceful offline fallback page (static HTML: "You're offline — Stride requires a connection").

### Native feel

Mitigations within Dash:
- Disable `update_title` to prevent browser title flash on navigation
- Use `dcc.Location` for SPA-style URL state
- Use `clientside_callback` for any interaction that must feel instant (gestures, animations)
- Set App Runner minimum instance count to 1 (eliminates cold-start latency)

---

## Risk Register

### Google Play

| Risk | Likelihood | Mitigation |
|---|---|---|
| Rejected for thin wrapper | Low | TWA is Google-endorsed; `assetlinks.json` + coherent app identity is sufficient |
| `assetlinks.json` misconfiguration | Medium | Test with Digital Asset Links verification tool before submitting |
| App crashes offline | Medium | Add service worker offline fallback |
| Signing key loss | High impact | Back up keystore immediately — loss = cannot update app |

### iOS

| Risk | Likelihood | Mitigation |
|---|---|---|
| Rejected for Guideline 4.2 (minimum functionality) | Medium | Add push notifications before first submission |
| Xcode provisioning issues | Medium | Follow Apple's "Distribute an app" guide exactly |
| Apple Developer enrollment delay | Low | Personal enrollment fast; Vinalytics business may need DUNS (1–3 weeks) |
| App pulled for inactivity | Low | Not a concern early; Apple removes apps with no updates in 2+ years |
| APNs cert expiry | Medium | Use FCM as abstraction layer — it manages APNs certs |

### Dash-specific

| Risk | Likelihood | Mitigation |
|---|---|---|
| Service worker caches `/_dash-*` | High if naive | Explicitly exclude in SW fetch handler |
| Slow callbacks on mobile | Medium | Debouncing, loading spinners, minimal mobile surface |
| App Runner cold start on first load | Medium | Set minimum instance count to 1 |

---

## Effort Summary

| Track | Effort | Time |
|---|---|---|
| PWA (manifest + SW) | S | 3–5 days |
| Google Play TWA | S | 2–3 days (after PWA) |
| iOS Capacitor + 1 plugin | M | 2–4 weeks |
| iOS React Native rewrite | XL | 3–6 months (do not do this) |
