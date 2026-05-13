"""Composer callbacks: show/hide inline add form, submit new task."""

from __future__ import annotations

from dash import Input, Output, State, ALL, MATCH, callback, no_update, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import create_task


def register_callbacks(app):
    # Show composer when '+ Add task' is clicked
    @app.callback(
        Output({"type": "composer", "day_key": MATCH}, "style"),
        Input({"type": "btn-add", "day_key": MATCH}, "n_clicks"),
        Input({"type": "btn-cancel-add", "day_key": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_composer(add_clicks, cancel_clicks):
        triggered = ctx.triggered_id
        if not triggered:
            raise PreventUpdate
        if triggered.get("type") == "btn-add" and add_clicks:
            return {"display": "block"}
        if triggered.get("type") == "btn-cancel-add":
            return {"display": "none"}
        raise PreventUpdate

    # Reset input when composer is shown
    @app.callback(
        Output({"type": "input-new-task", "day_key": MATCH}, "value"),
        Input({"type": "btn-add", "day_key": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_composer_input(n_clicks):
        if n_clicks:
            return ""
        raise PreventUpdate

    # Submit new task on button click or Enter
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Output({"type": "composer", "day_key": MATCH}, "style", allow_duplicate=True),
        Output({"type": "input-new-task", "day_key": MATCH}, "value", allow_duplicate=True),
        Input({"type": "btn-confirm-add", "day_key": MATCH}, "n_clicks"),
        Input({"type": "input-new-task", "day_key": MATCH}, "n_submit"),
        State({"type": "input-new-task", "day_key": MATCH}, "value"),
        State("store-tasks", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def submit_new_task(confirm_clicks, n_submit, title, current_tasks, week_offset):
        triggered = ctx.triggered_id
        if not triggered:
            raise PreventUpdate

        # Only submit when there's actual input
        if not title or not title.strip():
            raise PreventUpdate

        # Resolve day_key from the triggered component id
        day_key = triggered.get("day_key", "")
        if not day_key:
            raise PreventUpdate

        conn = app_db()
        new_task = create_task(
            conn,
            title=title.strip(),
            day_key=day_key,
        )

        # Add to store
        new_task_dict = new_task.model_dump()
        updated_tasks = list(current_tasks or [])
        updated_tasks.append(new_task_dict)

        return updated_tasks, {"display": "none"}, ""
