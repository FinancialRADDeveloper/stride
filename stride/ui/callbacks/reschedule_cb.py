"""Reschedule picker callbacks — shared by column 'Reschedule all' and per-card move."""

from __future__ import annotations

import datetime

from dash import ALL, Input, Output, State, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import list_tasks, move_task as svc_move
from stride.ui.components.board import _week_days


def _do_move(source: dict, target_day_key: str, week_offset: int) -> list[dict]:
    """Move tasks then return a refreshed task list.

    source = {"mode": "day", "key": "2026-05-16"}  → move all open tasks in that day
    source = {"mode": "task", "task_id": "abc..."}  → move that one task
    """
    conn = app_db()
    if source.get("mode") == "task":
        svc_move(conn, source["task_id"], target_day_key)
    else:
        day_key = source["key"]
        open_tasks = list_tasks(conn, day_keys=[day_key], include_done=False, full=False)
        for task in open_tasks:
            svc_move(conn, task.id, target_day_key)
    days = _week_days(week_offset or 0)
    refreshed = list_tasks(conn, day_keys=[d.isoformat() for d in days], include_done=True, full=True)
    return [t.model_dump() for t in refreshed]


def register_callbacks(app):

    # Open picker from column "Reschedule →" button
    @app.callback(
        Output("store-reschedule-source", "data"),
        Output("reschedule-modal", "opened"),
        Output("reschedule-datepicker", "value"),
        Input({"type": "btn-reschedule-day", "day_key": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def open_picker_day(n_clicks_list):
        if not any(n_clicks_list):
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not triggered:
            raise PreventUpdate
        return {"mode": "day", "key": triggered["day_key"]}, True, None

    # Open picker from per-card "→" button
    @app.callback(
        Output("store-reschedule-source", "data", allow_duplicate=True),
        Output("reschedule-modal", "opened", allow_duplicate=True),
        Output("reschedule-datepicker", "value", allow_duplicate=True),
        Input({"type": "btn-move-task", "task_id": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def open_picker_card(n_clicks_list):
        if not any(n_clicks_list):
            raise PreventUpdate
        triggered = ctx.triggered_id
        if not triggered:
            raise PreventUpdate
        for tc in ctx.triggered:
            if tc["value"] and tc["value"] > 0:
                return {"mode": "task", "task_id": triggered["task_id"]}, True, None
        raise PreventUpdate

    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Output("reschedule-modal", "opened", allow_duplicate=True),
        Output("store-reschedule-source", "data", allow_duplicate=True),
        Input("btn-reschedule-today",        "n_clicks"),
        Input("btn-reschedule-tomorrow",     "n_clicks"),
        Input("btn-reschedule-next-week",    "n_clicks"),
        Input("btn-reschedule-next-weekend", "n_clicks"),
        State("store-reschedule-source", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def reschedule_quick(c_today, c_tmrw, c_nweek, c_nwknd, source, week_offset):
        triggered = ctx.triggered_id
        if not triggered or not source:
            raise PreventUpdate
        today = datetime.date.today()
        if triggered == "btn-reschedule-today":
            target = today
        elif triggered == "btn-reschedule-tomorrow":
            target = today + datetime.timedelta(days=1)
        elif triggered == "btn-reschedule-next-week":
            target = today + datetime.timedelta(days=(7 - today.weekday()))
        elif triggered == "btn-reschedule-next-weekend":
            days_to_sat = (5 - today.weekday()) % 7 or 7
            target = today + datetime.timedelta(days=days_to_sat)
        else:
            raise PreventUpdate
        return _do_move(source, target.isoformat(), week_offset), False, None

    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Output("reschedule-modal", "opened", allow_duplicate=True),
        Output("store-reschedule-source", "data", allow_duplicate=True),
        Input("reschedule-datepicker", "value"),
        State("store-reschedule-source", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def reschedule_from_calendar(date_value, source, week_offset):
        if not date_value or not source:
            raise PreventUpdate
        return _do_move(source, date_value, week_offset), False, None
