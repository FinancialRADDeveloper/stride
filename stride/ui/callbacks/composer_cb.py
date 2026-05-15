"""Composer callbacks: show/hide inline add form, submit new task."""

from __future__ import annotations

from dash import Input, Output, State, MATCH, no_update, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import create_task


def register_callbacks(app):
    # Show / hide composer. Clear the title input on open.
    # Picker values (priority/size/category) are NOT reset here —
    # keeping them as State-only avoids Dash pruning the SegmentedControls
    # from the dynamically-rendered board on first render.
    @app.callback(
        Output({"type": "composer",       "day_key": MATCH}, "style"),
        Output({"type": "input-new-task", "day_key": MATCH}, "value"),
        Input({"type": "btn-add",        "day_key": MATCH}, "n_clicks"),
        Input({"type": "btn-cancel-add", "day_key": MATCH}, "n_clicks"),
        prevent_initial_call=True,
    )
    def toggle_composer(add_clicks, cancel_clicks):
        triggered = ctx.triggered_id
        if not triggered:
            raise PreventUpdate
        if triggered.get("type") == "btn-add" and add_clicks:
            return {"display": "block"}, ""
        if triggered.get("type") == "btn-cancel-add":
            return {"display": "none"}, no_update
        raise PreventUpdate

    # Submit new task on button click or Enter
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Output({"type": "composer",       "day_key": MATCH}, "style", allow_duplicate=True),
        Output({"type": "input-new-task", "day_key": MATCH}, "value", allow_duplicate=True),
        Input({"type": "btn-confirm-add", "day_key": MATCH}, "n_clicks"),
        Input({"type": "input-new-task",  "day_key": MATCH}, "n_submit"),
        State({"type": "input-new-task",    "day_key": MATCH}, "value"),
        State({"type": "composer-priority", "day_key": MATCH}, "value"),
        State({"type": "composer-size",     "day_key": MATCH}, "value"),
        State({"type": "composer-category", "day_key": MATCH}, "value"),
        State("store-tasks", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def submit_new_task(confirm_clicks, n_submit, title, priority, size, category_id,
                        current_tasks, week_offset):
        triggered = ctx.triggered_id
        if not triggered:
            raise PreventUpdate

        if not title or not title.strip():
            raise PreventUpdate

        day_key = triggered.get("day_key", "")
        if not day_key:
            raise PreventUpdate

        conn = app_db()
        new_task = create_task(
            conn,
            title=title.strip(),
            day_key=day_key,
            priority=priority or "P3",
            size=size or "M",
            category_id=category_id or "personal",
        )

        new_task_dict = new_task.model_dump()
        updated_tasks = list(current_tasks or [])
        updated_tasks.append(new_task_dict)

        return updated_tasks, {"display": "none"}, ""
