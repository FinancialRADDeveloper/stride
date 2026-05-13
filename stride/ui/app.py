"""Stride Dash application factory."""

from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import html, dcc

from stride.db import app_db
from stride.services.seed import seed_if_empty
from stride.ui.theme import STRIDE_THEME
from stride.ui.components.topbar import topbar
from stride.ui.components.detail import detail_drawer


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="Stride",
        assets_folder="../assets",
        suppress_callback_exceptions=True,
        external_stylesheets=[],
    )

    # Seed on first boot
    conn = app_db()
    seed_if_empty(conn)

    app.layout = _layout

    # Register all callbacks
    from stride.ui.callbacks import board_cb, card_cb, composer_cb, detail_cb
    board_cb.register_callbacks(app)
    card_cb.register_callbacks(app)
    composer_cb.register_callbacks(app)
    detail_cb.register_callbacks(app)

    return app


def _layout():
    return dmc.MantineProvider(
        theme=STRIDE_THEME,
        children=html.Div(
            id="stride-root",
            children=[
                topbar(),
                html.Div(
                    className="stride-body",
                    children=[
                        # Board: empty shell — callbacks populate it
                        html.Div(
                            html.Div(className="board-inner", id="board-inner"),
                            className="board",
                            id="board",
                        ),
                        detail_drawer(),
                    ],
                ),
                # Stores
                dcc.Store(id="store-tasks", data=[]),
                dcc.Store(id="store-selected", data=None),
                dcc.Store(id="store-week-offset", data=0),
                dcc.Store(id="store-show-done", data=True),
                dcc.Store(id="store-dnd-drop", data=None),
                # Tick: triggers task refresh every 60 seconds
                dcc.Interval(id="tick", interval=60_000, n_intervals=0),
            ],
        ),
    )
