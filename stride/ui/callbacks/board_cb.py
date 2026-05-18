"""Board-level callbacks: week navigation, task refresh, show-done toggle, view modes."""

from __future__ import annotations

import datetime

from dash import Input, Output, State, no_update, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import list_tasks, move_task as svc_move
from stride.ui.components.board import _week_days, board as render_board
from stride.ui.components.month_view import month_view as render_month, _anchor_month

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _tasks_for_window(week_offset: int) -> list[dict]:
    days = _week_days(week_offset)
    day_keys = [d.isoformat() for d in days]
    conn = app_db()
    tasks = list_tasks(conn, day_keys=day_keys, include_done=True, full=True)
    return [t.model_dump() for t in tasks]


def _tasks_for_month(week_offset: int) -> list[dict]:
    today = datetime.date.today()
    year, month = _anchor_month(week_offset)
    first = datetime.date(year, month, 1)
    if month == 12:
        last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    day_keys = [
        (first + datetime.timedelta(days=i)).isoformat()
        for i in range((last - first).days + 1)
    ]
    conn = app_db()
    tasks = list_tasks(conn, day_keys=day_keys, include_done=True, full=True)
    return [t.model_dump() for t in tasks]


def _tasks_for_day(week_offset: int) -> list[dict]:
    today = datetime.date.today()
    # Day view uses week_offset to pick the anchor week; show only today
    day_key = today.isoformat()
    conn = app_db()
    tasks = list_tasks(conn, day_keys=[day_key], include_done=True, full=True)
    return [t.model_dump() for t in tasks]


def _week_date_range_label(week_offset: int) -> str:
    days = _week_days(week_offset)
    start, end = days[0], days[-1]
    if start.month == end.month:
        return f"{start.day} – {end.day} {_MONTH_SHORT[end.month - 1]} {end.year}"
    return (
        f"{start.day} {_MONTH_SHORT[start.month - 1]} – "
        f"{end.day} {_MONTH_SHORT[end.month - 1]} {end.year}"
    )


def _month_offset_jump(week_offset: int, direction: int) -> int:
    """Return new week_offset to land in the previous/next month."""
    today = datetime.date.today()
    today_monday = today - datetime.timedelta(days=today.weekday())
    year, month = _anchor_month(week_offset)

    if direction > 0:
        # Next month
        if month == 12:
            target_first = datetime.date(year + 1, 1, 1)
        else:
            target_first = datetime.date(year, month + 1, 1)
    else:
        # Previous month
        if month == 1:
            target_first = datetime.date(year - 1, 12, 1)
        else:
            target_first = datetime.date(year, month - 1, 1)

    # Week offset for the Monday on or before target_first
    target_monday = target_first - datetime.timedelta(days=target_first.weekday())
    return round((target_monday - today_monday).days / 7)


def register_callbacks(app):

    # Sync view-mode store from the segmented control
    @app.callback(
        Output("store-view-mode", "data"),
        Output("store-week-offset", "data", allow_duplicate=True),
        Input("view-mode-control", "value"),
        prevent_initial_call=True,
    )
    def update_view_mode(value):
        # Reset offset to 0 (today) when switching views so we never land on a blank past period
        return value or "week", 0

    # Week/day/month offset navigation
    @app.callback(
        Output("store-week-offset", "data"),
        Input("btn-prev-week", "n_clicks"),
        Input("btn-next-week", "n_clicks"),
        Input("btn-today", "n_clicks"),
        State("store-week-offset", "data"),
        State("store-view-mode", "data"),
        prevent_initial_call=True,
    )
    def update_week_offset(prev_clicks, next_clicks, today_clicks, current_offset, view_mode):
        offset = current_offset or 0
        view = view_mode or "week"

        if ctx.triggered_id == "btn-today":
            return 0
        if ctx.triggered_id == "btn-prev-week":
            if view == "month":
                return _month_offset_jump(offset, -1)
            return offset - 1
        if ctx.triggered_id == "btn-next-week":
            if view == "month":
                return _month_offset_jump(offset, +1)
            return offset + 1
        return no_update

    @app.callback(
        Output("store-show-done", "data"),
        Input("toggle-show-done", "checked"),
        prevent_initial_call=True,
    )
    def update_show_done(checked):
        return bool(checked)

    # Fetch tasks appropriate for the current view
    @app.callback(
        Output("store-tasks", "data"),
        Input("tick", "n_intervals"),
        Input("store-week-offset", "data"),
        Input("store-view-mode", "data"),
        State("store-show-done", "data"),
    )
    def refresh_tasks(n_intervals, week_offset, view_mode, show_done):
        offset = week_offset or 0
        view = view_mode or "week"
        if view == "month":
            return _tasks_for_month(offset)
        if view == "day":
            return _tasks_for_day(offset)
        return _tasks_for_window(offset)

    # Update topbar heading + date range label
    @app.callback(
        Output("topbar-view-heading", "children"),
        Output("topbar-date-range", "children"),
        Input("store-week-offset", "data"),
        Input("store-view-mode", "data"),
    )
    def update_labels(week_offset, view_mode):
        offset = week_offset or 0
        view = view_mode or "week"
        today = datetime.date.today()

        if view == "month":
            year, month = _anchor_month(offset)
            return _MONTH_NAMES[month - 1] + f" {year}", ""
        if view == "day":
            return "Today", f"{today.day} {_MONTH_SHORT[today.month - 1]} {today.year}"
        # week
        return "This week", _week_date_range_label(offset)

    # Render board or month grid into board-inner
    @app.callback(
        Output("board-inner", "children"),
        Output("board", "className"),
        Input("store-tasks", "data"),
        Input("store-show-done", "data"),
        Input("store-week-offset", "data"),
        Input("store-view-mode", "data"),
    )
    def render_board_from_store(tasks, show_done, week_offset, view_mode):
        tasks = tasks or []
        offset = week_offset or 0
        view = view_mode or "week"
        include_done = bool(show_done) if show_done is not None else True

        if view == "month":
            content = render_month(tasks, offset)
            return content, "board board--month"

        # Week or day
        filtered = tasks if include_done else [t for t in tasks if not t.get("done")]
        if view == "day":
            rendered = render_board(tasks=filtered, week_offset=0, view_mode="day")
        else:
            rendered = render_board(tasks=filtered, week_offset=offset)
        return rendered.children.children, "board"

    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("store-dnd-drop", "data"),
        State("store-week-offset", "data"),
        State("store-view-mode", "data"),
        prevent_initial_call=True,
    )
    def on_dnd_drop(drop_data, week_offset, view_mode):
        if not drop_data:
            raise PreventUpdate
        task_id = drop_data.get("task_id")
        to_day_key = drop_data.get("to_day_key")
        if not task_id or not to_day_key:
            raise PreventUpdate
        conn = app_db()
        svc_move(conn, task_id, to_day_key)
        offset = week_offset or 0
        view = view_mode or "week"
        if view == "month":
            return _tasks_for_month(offset)
        if view == "day":
            return _tasks_for_day(offset)
        return _tasks_for_window(offset)
