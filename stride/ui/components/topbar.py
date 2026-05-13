"""TopBar component — fixed 56px header."""

from __future__ import annotations

import datetime

from dash import html
import dash_mantine_components as dmc


def topbar() -> html.Div:
    """Return the fixed header bar with logo, date range, and controls."""
    return html.Div(
        id="topbar",
        className="topbar",
        children=[
            # Left: logo + wordmark
            html.Div(
                className="topbar-left",
                children=[
                    html.Div(
                        className="topbar-logo",
                        children="S",
                    ),
                    html.Div([
                        html.Div("Stride", className="topbar-wordmark"),
                        html.Div("personal · day-board", className="topbar-subtitle mono"),
                    ]),
                    html.Div(className="topbar-divider"),
                    html.Div(
                        className="topbar-week-label",
                        children=[
                            html.H1("This week", className="topbar-heading"),
                            html.Span(
                                id="topbar-date-range",
                                className="topbar-date-range mono",
                            ),
                        ],
                    ),
                ],
            ),
            # Right: controls
            html.Div(
                className="topbar-right",
                children=[
                    # "Completed" toggle
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
                    # Prev week
                    html.Button(
                        "‹",
                        id="btn-prev-week",
                        className="btn-icon",
                        title="Previous period",
                        n_clicks=0,
                    ),
                    # Today
                    html.Button(
                        "Today",
                        id="btn-today",
                        className="btn-text",
                        title="Jump to today",
                        n_clicks=0,
                    ),
                    # Next week
                    html.Button(
                        "›",
                        id="btn-next-week",
                        className="btn-icon",
                        title="Next period",
                        n_clicks=0,
                    ),
                ],
            ),
        ],
    )
