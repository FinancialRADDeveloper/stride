"""Board-level callbacks: week navigation, task refresh, show-done toggle."""

from __future__ import annotations

import datetime

from dash import Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import list_tasks, move_task as svc_move
from stride.ui.components.board import _week_days, board as render_board


def _tasks_for_window(week_offset: int, include_done: bool = True) -> list[dict]:
    """Fetch tasks for the 6 visible days as plain dicts."""
    days = _week_days(week_offset)
    day_keys = [d.isoformat() for d in days]
    conn = app_db()
    tasks = list_tasks(conn, day_keys=day_keys, include_done=include_done, full=True)
    result = []
    for t in tasks:
        d = t.model_dump()
        # Resolve category_id from the DB — it's stored on the task
        result.append(d)
    return result


def _date_range_label(week_offset: int) -> str:
    days = _week_days(week_offset)
    start = days[0]
    end = days[-1]
    month_short = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if start.month == end.month:
        return f"{start.day} – {end.day} {month_short[end.month - 1]} {end.year}"
    return (
        f"{start.day} {month_short[start.month - 1]} – "
        f"{end.day} {month_short[end.month - 1]} {end.year}"
    )


def register_callbacks(app):
    @app.callback(
        Output("store-week-offset", "data"),
        Input("btn-prev-week", "n_clicks"),
        Input("btn-next-week", "n_clicks"),
        Input("btn-today", "n_clicks"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def update_week_offset(prev_clicks, next_clicks, today_clicks, current_offset):
        from dash import ctx
        if ctx.triggered_id == "btn-prev-week":
            return (current_offset or 0) - 1
        if ctx.triggered_id == "btn-next-week":
            return (current_offset or 0) + 1
        if ctx.triggered_id == "btn-today":
            return 0
        return no_update

    @app.callback(
        Output("store-show-done", "data"),
        Input("toggle-show-done", "checked"),
        prevent_initial_call=True,
    )
    def update_show_done(checked):
        return bool(checked)

    @app.callback(
        Output("store-tasks", "data"),
        Input("tick", "n_intervals"),
        Input("store-week-offset", "data"),
        State("store-show-done", "data"),
    )
    def refresh_tasks(n_intervals, week_offset, show_done):
        include_done = bool(show_done) if show_done is not None else True
        return _tasks_for_window(week_offset or 0, include_done=True)

    @app.callback(
        Output("topbar-date-range", "children"),
        Input("store-week-offset", "data"),
    )
    def update_date_range(week_offset):
        return _date_range_label(week_offset or 0)

    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("store-dnd-drop", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def on_dnd_drop(drop_data, week_offset):
        if not drop_data:
            raise PreventUpdate
        task_id = drop_data.get("task_id")
        to_day_key = drop_data.get("to_day_key")
        if not task_id or not to_day_key:
            raise PreventUpdate
        conn = app_db()
        svc_move(conn, task_id, to_day_key)
        days = _week_days(week_offset or 0)
        day_keys = [d.isoformat() for d in days]
        tasks = list_tasks(conn, day_keys=day_keys, include_done=True, full=True)
        return [t.model_dump() for t in tasks]

    @app.callback(
        Output("board-inner", "children"),
        Input("store-tasks", "data"),
        Input("store-show-done", "data"),
        Input("store-week-offset", "data"),
    )
    def render_board_from_store(tasks, show_done, week_offset):
        tasks = tasks or []
        include_done = bool(show_done) if show_done is not None else True
        filtered = tasks if include_done else [t for t in tasks if not t.get("done")]
        rendered = render_board(tasks=filtered, week_offset=week_offset or 0)
        # rendered.children is the board-inner div; return its children (the columns)
        return rendered.children.children
