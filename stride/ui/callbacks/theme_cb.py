"""Dark / light mode toggle callback."""

from __future__ import annotations

from dash import Input, Output, State
from dash.exceptions import PreventUpdate


def register_callbacks(app):
    @app.callback(
        Output("store-theme", "data"),
        Output("mantine-provider", "forceColorScheme"),
        Input("btn-dark-mode", "n_clicks"),
        State("store-theme", "data"),
        prevent_initial_call=True,
    )
    def toggle_theme(n, current):
        if not n:
            raise PreventUpdate
        new = "dark" if current == "light" else "light"
        return new, new
