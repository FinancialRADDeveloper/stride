"""Achievements panel callbacks — open/close and content refresh."""

from __future__ import annotations

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.achievements import get_achievements
from stride.ui.components.achievements import render_achievements


def register_callbacks(app):

    # -----------------------------------------------------------------------
    # Open the panel when the topbar button is clicked
    # -----------------------------------------------------------------------
    @app.callback(
        Output("store-achievements-open", "data"),
        Input("btn-achievements", "n_clicks"),
        Input("btn-achievements-close", "n_clicks"),
        State("store-achievements-open", "data"),
        prevent_initial_call=True,
    )
    def toggle_achievements(open_clicks, close_clicks, is_open):
        from dash import ctx
        if ctx.triggered_id == "btn-achievements-close":
            return False
        # Toggle on each topbar click so clicking again closes it
        return not bool(is_open)

    # -----------------------------------------------------------------------
    # Sync drawer open state from the store
    # -----------------------------------------------------------------------
    @app.callback(
        Output("achievements-drawer", "opened"),
        Input("store-achievements-open", "data"),
    )
    def sync_drawer_open(is_open):
        return bool(is_open)

    # -----------------------------------------------------------------------
    # Populate content whenever the panel opens or the tick fires while open
    # -----------------------------------------------------------------------
    @app.callback(
        Output("ach-stats",   "children"),
        Output("ach-content", "children"),
        Input("store-achievements-open", "data"),
        Input("tick", "n_intervals"),
        State("store-achievements-open", "data"),
        prevent_initial_call=True,
    )
    def refresh_achievements(opened_data, _tick, is_open):
        # Only query when the panel is visible
        if not is_open:
            raise PreventUpdate
        conn = app_db()
        data = get_achievements(conn)
        stats_el, content_el = render_achievements(data)
        return stats_el, content_el
