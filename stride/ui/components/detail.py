"""Detail drawer component — read-only in Phase 2."""

from __future__ import annotations

import datetime

from dash import html
import dash_mantine_components as dmc

from stride.ui.theme import PRIORITY_COLOURS, CATEGORY_COLOURS

_PRIORITY_LABEL = {
    "P1": "Critical",
    "P2": "High",
    "P3": "Normal",
    "P4": "Low",
}

_SIZE_HINT = {
    "XS": "<15m",
    "S": "~25m",
    "M": "~1h",
    "L": "~2h",
    "XL": "half day",
}

_EVENT_KIND_LABEL = {
    "created": "Created",
    "moved": "Moved",
    "edited": "Edited",
    "done": "Completed",
    "reopened": "Reopened",
    "scheduled": "Linked to calendar",
    "unscheduled": "Unlinked from calendar",
    "deleted": "Deleted",
}


def _fmt_minutes(minutes: int | None) -> str:
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"


def _field_row(label: str, value: str) -> html.Div:
    return html.Div(
        className="detail-field",
        children=[
            html.Div(label, className="detail-field-label mono"),
            html.Div(str(value), className="detail-field-value"),
        ],
    )


def _event_row(event: dict) -> html.Div:
    ts_ms = event.get("ts", 0)
    ts = datetime.datetime.fromtimestamp(ts_ms / 1000)
    time_str = ts.strftime("%H:%M")
    today = datetime.date.today()
    event_date = ts.date()
    diff = (today - event_date).days
    if diff == 0:
        rel = "today"
    elif diff == 1:
        rel = "yesterday"
    else:
        rel = f"{diff}d ago"

    kind = event.get("kind", "")
    payload = event.get("payload", {})
    label = _EVENT_KIND_LABEL.get(kind, kind)

    # Build a descriptive text based on kind
    if kind == "moved":
        from_day = payload.get("from", "?")
        to_day = payload.get("to", "?")
        detail_text = f"{from_day} → {to_day}"
    elif kind == "edited":
        field = payload.get("field", "?")
        detail_text = f"field: {field}"
    else:
        detail_text = ""

    return html.Div(
        className="event-row",
        children=[
            html.Div(
                className="event-dot",
                style={
                    "background": {
                        "created": "#6366f1",
                        "moved": "#0ea5e9",
                        "edited": "#f59e0b",
                        "done": "#22c55e",
                        "reopened": "#9ca3af",
                    }.get(kind, "#9ca3af")
                },
            ),
            html.Div(
                className="event-body",
                children=[
                    html.Div(
                        [
                            html.Span(label, className="event-kind"),
                            html.Span(f" {detail_text}", className="event-detail") if detail_text else None,
                        ],
                        className="event-description",
                    ),
                    html.Div(f"{rel} · {time_str}", className="event-time mono"),
                ],
            ),
        ],
    )


def detail_drawer() -> dmc.Drawer:
    """Return the right-side detail drawer.

    Populated by the detail_cb callbacks when store-selected changes.
    Read-only in Phase 2 — Phase 3 makes it editable.
    """
    return dmc.Drawer(
        id="detail-drawer",
        position="right",
        size=440,
        withCloseButton=False,
        overlayProps={"opacity": 0, "blur": 0},
        styles={
            "body": {"padding": 0, "overflowY": "auto"},
            "content": {
                "background": "#ffffff",
                "borderLeft": "1px solid #e5e7eb",
                "boxShadow": "-4px 0 24px rgba(0,0,0,0.08)",
            },
        },
        children=[
            # Header
            html.Div(
                id="detail-header",
                className="detail-header",
                children=[
                    html.Div(id="detail-header-meta", className="detail-header-meta"),
                    html.Button(
                        "✕",
                        id="btn-close-drawer",
                        className="btn-icon",
                        n_clicks=0,
                        title="Close (Esc)",
                    ),
                ],
            ),
            # Scrollable body
            html.Div(
                id="detail-body",
                className="detail-body",
                children=[
                    html.Div(id="detail-title", className="detail-title"),
                    html.Div(id="detail-description", className="detail-description"),
                    html.Div(id="detail-fields", className="detail-fields"),
                    html.Div(id="detail-history", className="detail-history"),
                    html.Div(id="detail-counters", className="detail-counters"),
                ],
            ),
        ],
    )


def build_detail_content(task: dict) -> tuple:
    """Build the content elements from a task dict.

    Returns (header_meta, title, description, fields, history, counters).
    """
    task_id = task.get("id", "")
    title = task.get("title", "")
    description = task.get("description", "")
    priority = task.get("priority", "P3")
    size = task.get("size", "M")
    estimate_min = task.get("estimate_min")
    time_of_day = task.get("time_of_day")
    category_id = task.get("category_id", "personal")
    done = task.get("done", False)
    age_days = task.get("age_days", 0)
    move_count = task.get("move_count", 0)
    edit_count = task.get("edit_count", 0)
    history = task.get("history", [])

    pri_colour = PRIORITY_COLOURS.get(priority, "#9ca3af")
    cat_colour = CATEGORY_COLOURS.get(category_id, "#9ca3af")

    # Header meta
    age_label = "today" if age_days == 0 else f"{age_days}d ago"
    header_meta = html.Span(
        [
            html.Span(task_id[:12].upper(), className="mono detail-id"),
            html.Span(f" · created {age_label}", className="mono detail-created"),
        ]
    )

    # Title
    title_el = html.Div(
        title,
        className="detail-title-text" + (" detail-title-text--done" if done else ""),
    )

    # Description
    desc_el = html.P(description, className="detail-desc-text") if description else html.P(
        "No description.", className="detail-desc-empty"
    )

    # Fields
    fields_el = html.Div(
        className="detail-fields-grid",
        children=[
            _field_row("Priority", f"{priority} · {_PRIORITY_LABEL.get(priority, priority)}"),
            _field_row("Size", f"{size} · {_SIZE_HINT.get(size, '')}"),
            _field_row("Estimate", _fmt_minutes(estimate_min)),
            _field_row("Time of day", time_of_day or "—"),
            _field_row("Category", category_id),
            _field_row("Status", "Done" if done else "Open"),
        ],
    )

    # History (newest first)
    sorted_history = sorted(history, key=lambda e: e.get("ts", 0), reverse=True)
    history_el = html.Div(
        className="detail-history-list",
        children=[
            html.Div(
                f"Activity · {len(history)} event{'s' if len(history) != 1 else ''}",
                className="detail-section-heading mono",
            ),
            html.Div(
                [_event_row(ev) for ev in sorted_history] if sorted_history else
                [html.Div("No history.", className="detail-empty")],
                className="detail-history-scroll",
            ),
        ],
    )

    # Counters
    counters_el = html.Div(
        className="detail-counters-grid",
        children=[
            html.Div([
                html.Div("Age", className="counter-label mono"),
                html.Div("<1d" if age_days == 0 else f"{age_days}d", className="counter-value mono"),
            ]),
            html.Div([
                html.Div("Moves", className="counter-label mono"),
                html.Div(str(move_count), className="counter-value mono"),
            ]),
            html.Div([
                html.Div("Edits", className="counter-label mono"),
                html.Div(str(edit_count), className="counter-value mono"),
            ]),
            html.Div([
                html.Div("Status", className="counter-label mono"),
                html.Div("Done" if done else "Open", className="counter-value mono"),
            ]),
        ],
    )

    return header_meta, title_el, desc_el, fields_el, history_el, counters_el
