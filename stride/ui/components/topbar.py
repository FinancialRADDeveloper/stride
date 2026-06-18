"""TopBar component — fixed 56px header."""

from __future__ import annotations

from dash import html
import dash_mantine_components as dmc


def topbar() -> html.Div:
    """Return the fixed header bar with logo, date range, and controls."""
    return html.Div(
        id="topbar",
        className="topbar",
        children=[
            # Left: logo + wordmark + view switcher
            html.Div(
                className="topbar-left",
                children=[
                    html.Div(className="topbar-logo", children="S"),
                    html.Div([
                        html.Div("Stride", className="topbar-wordmark"),
                        html.Div("personal · day-board", className="topbar-subtitle mono"),
                    ]),
                    html.Div(className="topbar-divider"),
                    html.Div(
                        className="topbar-week-label",
                        children=[
                            html.H1(
                                "This week",
                                id="topbar-view-heading",
                                className="topbar-heading",
                            ),
                            html.Span(
                                id="topbar-date-range",
                                className="topbar-date-range mono",
                            ),
                        ],
                    ),
                    html.Div(className="topbar-divider"),
                    dmc.SegmentedControl(
                        id="view-mode-control",
                        value="week",
                        data=[
                            {"value": "day",   "label": "Day"},
                            {"value": "week",  "label": "Week"},
                            {"value": "month", "label": "Month"},
                        ],
                        size="xs",
                        styles={"root": {"background": "transparent"}},
                    ),
                ],
            ),
            # Right: controls
            html.Div(
                className="topbar-right",
                children=[
                    # Overdue pill — hidden when no overdue tasks; callback drives content + visibility
                    html.Button(
                        id="btn-overdue-pill",
                        className="topbar-overdue-pill",
                        title="Jump to oldest overdue tasks",
                        n_clicks=0,
                        style={"display": "none"},
                    ),
                    html.Button(
                        "★ Achievements",
                        id="btn-achievements",
                        className="btn-text",
                        title="View completed tasks and streak",
                        n_clicks=0,
                    ),
                    html.Div(className="topbar-spacer"),
                    html.Div(
                        className="topbar-show-done",
                        children=dmc.Switch(
                            id="toggle-show-done",
                            label="Completed",
                            checked=True,
                            size="sm",
                        ),
                    ),
                    html.Div(className="topbar-spacer"),
                    html.Button("‹", id="btn-prev-week", className="btn-icon",
                                title="Previous period", n_clicks=0),
                    html.Button("Today", id="btn-today", className="btn-text",
                                title="Jump to today", n_clicks=0),
                    html.Button("›", id="btn-next-week", className="btn-icon",
                                title="Next period", n_clicks=0),
                    html.Div(className="topbar-spacer"),
                    html.Button("☾", id="btn-dark-mode", className="btn-icon",
                                title="Toggle dark mode  (preserves session only)", n_clicks=0),
                ],
            ),
        ],
    )
