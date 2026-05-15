"""Keyboard shortcut callbacks."""

from __future__ import annotations

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate


def register_callbacks(app):
    @app.callback(
        Output("store-selected", "data", allow_duplicate=True),
        Output("store-tasks", "data", allow_duplicate=True),
        Input("store-kb-action", "data"),
        State("store-selected", "data"),
        State("store-tasks", "data"),
        prevent_initial_call=True,
    )
    def handle_kb(kb, selected_id, tasks):
        if not kb:
            raise PreventUpdate
        action = kb.get("action")
        tasks = tasks or []

        if action == "close":
            return None, no_update

        if action == "open-drawer" and selected_id:
            # Drawer already open — no-op; if nothing selected, nothing to open
            return no_update, no_update

        if action == "toggle-done" and selected_id:
            from stride.db import app_db
            from stride.services.tasks import toggle_done, list_tasks
            conn = app_db()
            toggle_done(conn, selected_id)
            day_keys = list({t["day_key"] for t in tasks})
            refreshed = list_tasks(conn, day_keys=day_keys, include_done=True, full=False)
            return no_update, [t.model_dump() for t in refreshed]

        raise PreventUpdate
