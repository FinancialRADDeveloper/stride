"""Inline task composer component."""

from __future__ import annotations

from dash import html, dcc
import dash_mantine_components as dmc


_PRIORITY_DATA = [
    {"value": "P1", "label": "P1"},
    {"value": "P2", "label": "P2"},
    {"value": "P3", "label": "P3"},
    {"value": "P4", "label": "P4"},
]

_SIZE_DATA = [
    {"value": "XS", "label": "XS"},
    {"value": "S",  "label": "S"},
    {"value": "M",  "label": "M"},
    {"value": "L",  "label": "L"},
    {"value": "XL", "label": "XL"},
]

_CATEGORY_DATA = [
    {"value": "build",    "label": "Build"},
    {"value": "work",     "label": "Work"},
    {"value": "home",     "label": "Home"},
    {"value": "admin",    "label": "Admin"},
    {"value": "health",   "label": "Health"},
    {"value": "personal", "label": "Personal"},
]


def composer(day_key: str) -> html.Div:
    """Inline composer for adding a task to a specific day.

    Hidden by default; shown when the '+ Add task' button is clicked.
    IDs use pattern-matching so one set of callbacks handles all days.
    """
    return html.Div(
        id={"type": "composer", "day_key": day_key},
        className="composer",
        style={"display": "none"},
        children=[
            dcc.Input(
                id={"type": "input-new-task", "day_key": day_key},
                type="text",
                placeholder="Task title — press Enter or click Add",
                className="composer-input",
                debounce=False,
                value="",
                n_submit=0,
            ),
            html.Div(
                className="composer-pickers",
                style={"display": "none"},
                children=[
                    html.Div(
                        className="composer-picker-group",
                        children=[
                            html.Span("Priority", className="composer-picker-label mono"),
                            dmc.SegmentedControl(
                                id={"type": "composer-priority", "day_key": day_key},
                                data=_PRIORITY_DATA,
                                value="P3",
                                size="xs",
                                color="blue",
                            ),
                        ],
                    ),
                    html.Div(
                        className="composer-picker-group",
                        children=[
                            html.Span("Size", className="composer-picker-label mono"),
                            dmc.SegmentedControl(
                                id={"type": "composer-size", "day_key": day_key},
                                data=_SIZE_DATA,
                                value="M",
                                size="xs",
                            ),
                        ],
                    ),
                    html.Div(
                        className="composer-picker-group",
                        children=[
                            html.Span("Category", className="composer-picker-label mono"),
                            dmc.SegmentedControl(
                                id={"type": "composer-category", "day_key": day_key},
                                data=_CATEGORY_DATA,
                                value="personal",
                                size="xs",
                            ),
                        ],
                    ),
                    html.Div(
                        className="composer-picker-group composer-picker-group--desc",
                        children=[
                            html.Span("Description", className="composer-picker-label mono"),
                            dcc.Textarea(
                                id={"type": "composer-description", "day_key": day_key},
                                className="composer-desc-input",
                                placeholder="Optional notes…",
                                rows=2,
                                value="",
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="composer-actions",
                children=[
                    html.Button(
                        "▾ Details",
                        className="btn-expand-composer",
                        type="button",
                        n_clicks=0,
                    ),
                    html.Button(
                        "Cancel",
                        id={"type": "btn-cancel-add", "day_key": day_key},
                        className="btn-cancel",
                        n_clicks=0,
                    ),
                    html.Button(
                        "Add task",
                        id={"type": "btn-confirm-add", "day_key": day_key},
                        className="btn-confirm",
                        n_clicks=0,
                    ),
                ],
            ),
        ],
    )
