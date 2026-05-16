"""Stride Dash application factory."""

from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import html, dcc
from flask import jsonify

from stride.db import app_db
from stride.services.seed import seed_if_empty
from stride.ui.theme import STRIDE_THEME
from stride.ui.components.topbar import topbar
from stride.ui.components.detail import detail_drawer
from stride.ui.components.reschedule_picker import reschedule_picker


def create_app() -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="Stride",
        assets_folder="../assets",
        suppress_callback_exceptions=True,
        external_stylesheets=[],
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
            {"name": "theme-color", "content": "#f5f3ee"},
            {"name": "mobile-web-app-capable", "content": "yes"},
            {"name": "apple-mobile-web-app-capable", "content": "yes"},
            {"name": "apple-mobile-web-app-status-bar-style", "content": "default"},
        ],
    )

    # Seed on first boot
    conn = app_db()
    seed_if_empty(conn)

    # Health-check endpoint — used by App Runner and docker-compose healthchecks
    @app.server.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    app.layout = _layout

    # Register all callbacks
    from stride.ui.callbacks import board_cb, card_cb, composer_cb, detail_cb, kb_cb, theme_cb, reschedule_cb
    board_cb.register_callbacks(app)
    card_cb.register_callbacks(app)
    composer_cb.register_callbacks(app)
    detail_cb.register_callbacks(app)
    kb_cb.register_callbacks(app)
    theme_cb.register_callbacks(app)
    reschedule_cb.register_callbacks(app)

    return app


def _layout():
    return dmc.MantineProvider(
        id="mantine-provider",
        theme=STRIDE_THEME,
        forceColorScheme="light",
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
                        reschedule_picker(),
                    ],
                ),
                # Stores
                dcc.Store(id="store-tasks", data=[]),
                dcc.Store(id="store-reschedule-source", data=None),
                dcc.Store(id="store-selected", data=None),
                dcc.Store(id="store-week-offset", data=0),
                dcc.Store(id="store-show-done", data=True),
                dcc.Store(id="store-dnd-drop", data=None),
                dcc.Store(id="store-kb-action", data=None),
                dcc.Store(id="store-theme", data="light"),
                # Tick: triggers task refresh every 60 seconds
                dcc.Interval(id="tick", interval=60_000, n_intervals=0),
            ],
        ),
    )
