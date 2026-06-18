"""Stride Dash application factory."""

from __future__ import annotations

import os

import dash
import dash_mantine_components as dmc
from dash import html, dcc
from flask import Flask, jsonify

from stride.auth import init_login
from stride.db import app_db
from stride.routes.auth_bp import login_bp
from stride.services.seed import seed_if_empty
from stride.ui.theme import STRIDE_THEME
from stride.ui.components.topbar import topbar
from stride.ui.components.detail import detail_drawer
from stride.ui.components.reschedule_picker import reschedule_picker
from stride.ui.components.achievements import achievements_panel

_TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
_SECRET_KEY = os.environ.get("STRIDE_SECRET_KEY", "dev-secret-change-me-in-production")


def create_app() -> dash.Dash:
    # Pre-create Flask server so we can set template_folder before Dash sees it
    server = Flask(__name__, template_folder=_TEMPLATES_DIR)

    app = dash.Dash(
        __name__,
        server=server,
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

    # Auth: Flask-Login + session secret
    init_login(server, _SECRET_KEY)
    server.register_blueprint(login_bp)

    # Seed on first boot
    conn = app_db()
    seed_if_empty(conn)

    # Health-check endpoint — used by App Runner and docker-compose healthchecks
    @server.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    app.layout = _layout

    # Register all callbacks
    from stride.ui.callbacks import board_cb, card_cb, composer_cb, detail_cb, kb_cb, theme_cb, reschedule_cb, overdue_cb, achievements_cb
    board_cb.register_callbacks(app)
    card_cb.register_callbacks(app)
    composer_cb.register_callbacks(app)
    detail_cb.register_callbacks(app)
    kb_cb.register_callbacks(app)
    theme_cb.register_callbacks(app)
    reschedule_cb.register_callbacks(app)
    overdue_cb.register_callbacks(app)
    achievements_cb.register_callbacks(app)

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
                        achievements_panel(),
                    ],
                ),
                # Stores
                dcc.Store(id="store-tasks", data=[]),
                dcc.Store(id="store-reschedule-source", data=None),
                dcc.Store(id="store-selected", data=None),
                dcc.Store(id="store-week-offset", data=0),
                dcc.Store(id="store-view-mode", data="week"),
                dcc.Store(id="store-show-done", data=True),
                dcc.Store(id="store-dnd-drop", data=None),
                dcc.Store(id="store-ctx-delete", data=None),
                dcc.Store(id="store-kb-action", data=None),
                dcc.Store(id="store-theme", data="light"),
                # Overdue summary: {count, oldest_day_key} — refreshed on tick
                dcc.Store(id="store-overdue", data={"count": 0, "oldest_day_key": None}),
                dcc.Store(id="store-achievements-open", data=False),
                # Tick: triggers task refresh every 60 seconds
                dcc.Interval(id="tick", interval=60_000, n_intervals=0),
            ],
        ),
    )
