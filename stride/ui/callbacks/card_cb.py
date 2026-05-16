"""Card-level callbacks: click to select, toggle done, add task button, move menu."""

from __future__ import annotations

from dash import Input, Output, State, ALL, no_update, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import toggle_done as svc_toggle_done


def register_callbacks(app):
    @app.callback(
        Output("store-selected", "data"),
        Output("detail-drawer", "opened"),
        Input({"type": "card", "task_id": ALL}, "n_clicks"),
        State("store-tasks", "data"),
        prevent_initial_call=True,
    )
    def on_card_click(n_clicks_list, tasks):
        if not ctx.triggered_id:
            raise PreventUpdate
        # ctx.triggered_id is {'type': 'card', 'task_id': ...}
        triggered = ctx.triggered_id
        if not isinstance(triggered, dict) or triggered.get("type") != "card":
            raise PreventUpdate
        # Only act on a genuine click (not the initial 0)
        task_id = triggered["task_id"]
        # Find the matching n_clicks value
        for tc in ctx.triggered:
            if tc["value"] and tc["value"] > 0:
                return task_id, True
        raise PreventUpdate

    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input({"type": "btn-toggle-done", "task_id": ALL}, "n_clicks"),
        State("store-tasks", "data"),
        prevent_initial_call=True,
    )
    def on_toggle_done(n_clicks_list, tasks):
        if not ctx.triggered_id:
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not isinstance(triggered, dict) or triggered.get("type") != "btn-toggle-done":
            raise PreventUpdate
        # Only act when n_clicks > 0
        for tc in ctx.triggered:
            if tc["value"] and tc["value"] > 0:
                task_id = triggered["task_id"]
                conn = app_db()
                svc_toggle_done(conn, task_id)
                # Return updated task list
                if tasks is None:
                    return no_update
                updated = []
                for t in tasks:
                    if t["id"] == task_id:
                        t = dict(t)
                        t["done"] = not t.get("done", False)
                    updated.append(t)
                return updated
        raise PreventUpdate

