"""Detail drawer component — editable in Phase 3."""

from __future__ import annotations

import datetime

from dash import html, dcc
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

_CATEGORIES = list(CATEGORY_COLOURS.keys())


def _fmt_minutes(minutes: int | None) -> str:
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"


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
        old_val = payload.get("from", "")
        new_val = payload.get("to", "")
        old_str = f"'{old_val}'" if isinstance(old_val, str) and len(str(old_val)) < 30 else str(old_val)
        new_str = f"'{new_val}'" if isinstance(new_val, str) and len(str(new_val)) < 30 else str(new_val)
        detail_text = f"{field}: {old_str} → {new_str}"
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
    """Return the right-side detail drawer with editable fields.

    Populated and made interactive by detail_cb callbacks.
    """
    # Priority segmented control options
    priority_data = [
        {"value": "P1", "label": "P1 Critical"},
        {"value": "P2", "label": "P2 High"},
        {"value": "P3", "label": "P3 Normal"},
        {"value": "P4", "label": "P4 Low"},
    ]

    # Size segmented control options
    size_data = [
        {"value": "XS", "label": "XS"},
        {"value": "S", "label": "S"},
        {"value": "M", "label": "M"},
        {"value": "L", "label": "L"},
        {"value": "XL", "label": "XL"},
    ]

    # Category chips
    category_chips = []
    for cat in _CATEGORIES:
        colour = CATEGORY_COLOURS.get(cat, "#9ca3af")
        category_chips.append(
            dmc.Chip(
                cat.capitalize(),
                value=cat,
                styles={
                    "label": {
                        "textTransform": "capitalize",
                        "fontSize": "12px",
                    }
                },
            )
        )

    return dmc.Drawer(
        id="detail-drawer",
        position="right",
        size=440,
        withCloseButton=False,
        keepMounted=True,
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
                    # Title — editable Textarea
                    html.Div(
                        className="detail-section",
                        children=[
                            dmc.Textarea(
                                id="detail-title",
                                placeholder="Task title…",
                                autosize=True,
                                minRows=1,
                                maxRows=3,
                                styles={
                                    "input": {
                                        "fontSize": "20px",
                                        "fontWeight": "600",
                                        "border": "none",
                                        "borderBottom": "1px solid #e5e7eb",
                                        "borderRadius": "0",
                                        "padding": "4px 0 8px",
                                        "background": "transparent",
                                        "resize": "none",
                                    },
                                    "root": {"marginBottom": "12px"},
                                },
                            ),
                        ],
                    ),
                    # Description — editable Textarea
                    html.Div(
                        className="detail-section",
                        children=[
                            dmc.Textarea(
                                id="detail-description",
                                placeholder="Add a description…",
                                autosize=True,
                                minRows=2,
                                styles={
                                    "input": {
                                        "fontSize": "13px",
                                        "border": "1px solid #e5e7eb",
                                        "borderRadius": "6px",
                                        "background": "#fafaf8",
                                        "resize": "none",
                                    },
                                    "root": {"marginBottom": "16px"},
                                },
                            ),
                        ],
                    ),
                    # Fields grid — editable
                    html.Div(
                        id="detail-fields",
                        className="detail-fields-editable",
                        children=[
                            # Priority
                            html.Div(
                                className="detail-field-row",
                                children=[
                                    html.Div("Priority", className="detail-field-label mono"),
                                    dmc.SegmentedControl(
                                        id="detail-priority",
                                        data=priority_data,
                                        value="P3",
                                        size="xs",
                                        styles={
                                            "root": {"width": "100%"},
                                        },
                                    ),
                                ],
                            ),
                            # Size
                            html.Div(
                                className="detail-field-row",
                                children=[
                                    html.Div("Size", className="detail-field-label mono"),
                                    dmc.SegmentedControl(
                                        id="detail-size",
                                        data=size_data,
                                        value="M",
                                        size="xs",
                                        styles={
                                            "root": {"width": "100%"},
                                        },
                                    ),
                                ],
                            ),
                            # Category
                            html.Div(
                                className="detail-field-row",
                                children=[
                                    html.Div("Category", className="detail-field-label mono"),
                                    dmc.ChipGroup(
                                        id="detail-category",
                                        multiple=False,
                                        children=category_chips,
                                    ),
                                ],
                            ),
                            # Estimate
                            html.Div(
                                className="detail-field-row",
                                children=[
                                    html.Div("Estimate", className="detail-field-label mono"),
                                    dmc.NumberInput(
                                        id="detail-estimate",
                                        placeholder="minutes",
                                        suffix=" min",
                                        min=0,
                                        step=5,
                                        styles={
                                            "input": {"fontSize": "13px"},
                                            "root": {"width": "160px"},
                                        },
                                    ),
                                ],
                            ),
                            # Time of day
                            html.Div(
                                className="detail-field-row",
                                children=[
                                    html.Div("Time of day", className="detail-field-label mono"),
                                    dmc.TimeInput(
                                        id="detail-time",
                                        styles={
                                            "input": {"fontSize": "13px"},
                                            "root": {"width": "160px"},
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Counters block
                    html.Div(id="detail-counters", className="detail-counters"),
                    # History
                    html.Div(id="detail-history", className="detail-history"),
                    # Delete button
                    html.Div(
                        className="detail-delete-row",
                        children=[
                            dmc.Button(
                                "Delete task",
                                id="detail-delete",
                                color="red",
                                variant="subtle",
                                size="xs",
                                styles={"root": {"marginTop": "8px"}},
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def build_detail_content(task: dict) -> tuple:
    """Build the dynamic content elements from a task dict.

    Returns (header_meta, title_value, description_value, priority_value,
             size_value, category_value, estimate_value, time_value,
             counters_el, history_el).
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
    is_stale = task.get("is_stale", False)
    history = task.get("history", [])

    # Header meta
    age_label = "today" if age_days == 0 else f"{age_days}d ago"
    header_meta = html.Span(
        [
            html.Span(task_id[:12].upper(), className="mono detail-id"),
            html.Span(f" · created {age_label}", className="mono detail-created"),
        ]
    )

    # Counters block with stale warning
    counter_children = [
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
    ]

    counters_el = html.Div(
        className="detail-counters-block",
        children=[
            html.Div(
                className="detail-counters-grid",
                children=counter_children,
            ),
            # Stale warning chip
            html.Div(
                "Stale — moved 3+ times",
                className="detail-stale-warning mono",
            ) if is_stale else None,
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

    return (
        header_meta,
        title,
        description,
        priority,
        size,
        category_id,
        estimate_min,
        time_of_day or "",
        counters_el,
        history_el,
    )
