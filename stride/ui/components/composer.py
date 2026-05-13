"""Inline task composer component."""

from __future__ import annotations

from dash import html, dcc


def composer(day_key: str) -> html.Div:
    """Inline composer for adding a task to a specific day.

    Hidden by default; shown when the '+ Add task' button is clicked.
    IDs use pattern-matching so one set of callbacks handles all days.
    """
    return html.Div(
        id={"type": "composer", "day_key": day_key},
        className="composer",
        style={"display": "none"},  # hidden by default
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
                className="composer-actions",
                children=[
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
