"""Card-level callbacks: click to select, toggle done, add task button, move menu."""

from __future__ import annotations

from dash import Input, Output, State, ALL, MATCH, callback, no_update, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import (
    list_tasks,
    move_task as svc_move,
    toggle_done as svc_toggle_done,
)
from stride.ui.components.board import _week_days


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

    # ------------------------------------------------------------------
    # Move-to menu: btn-move-to fires when a day item is clicked
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input({"type": "btn-move-to", "task_id": ALL, "day_key": ALL}, "n_clicks"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def on_move_to(n_clicks_list, week_offset):
        if not ctx.triggered_id:
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not isinstance(triggered, dict) or triggered.get("type") != "btn-move-to":
            raise PreventUpdate
        # Only fire on a genuine click
        for tc in ctx.triggered:
            if tc["value"] and tc["value"] > 0:
                task_id = triggered["task_id"]
                to_day_key = triggered["day_key"]
                conn = app_db()
                svc_move(conn, task_id, to_day_key)
                # Refresh task list for the visible window
                days = _week_days(week_offset or 0)
                day_keys = [d.isoformat() for d in days]
                tasks = list_tasks(conn, day_keys=day_keys, include_done=True, full=True)
                return [t.model_dump() for t in tasks]
        raise PreventUpdate
