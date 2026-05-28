"""Overdue task alerting callbacks.

Keeps store-overdue current and drives the topbar amber pill:
  - Content: "⚠ N overdue"
  - Visibility: shown when count > 0, hidden when all clear
  - Click: jumps store-week-offset to the week containing the oldest
    overdue task so the user lands directly on the problem
"""

from __future__ import annotations

import datetime

from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import get_overdue_summary


def _week_offset_for_day_key(day_key: str) -> int:
    """Return the store-week-offset integer for the week containing day_key."""
    target = datetime.date.fromisoformat(day_key)
    today = datetime.date.today()
    today_monday = today - datetime.timedelta(days=today.weekday())
    target_monday = target - datetime.timedelta(days=target.weekday())
    return round((target_monday - today_monday).days / 7)


def register_callbacks(app):

    # -----------------------------------------------------------------------
    # Refresh the overdue store on every tick and whenever tasks change
    # -----------------------------------------------------------------------
    @app.callback(
        Output("store-overdue", "data"),
        Input("tick", "n_intervals"),
        Input("store-tasks", "data"),   # task mutations (done, move, delete) refresh this
    )
    def refresh_overdue(_tick, _tasks):
        conn = app_db()
        return get_overdue_summary(conn)

    # -----------------------------------------------------------------------
    # Drive the pill: content + show/hide
    # -----------------------------------------------------------------------
    @app.callback(
        Output("btn-overdue-pill", "children"),
        Output("btn-overdue-pill", "style"),
        Input("store-overdue", "data"),
    )
    def update_overdue_pill(overdue):
        count = (overdue or {}).get("count", 0)
        if count == 0:
            return no_update, {"display": "none"}
        label = f"⚠ {count} overdue"
        return label, {"display": "inline-flex"}

    # -----------------------------------------------------------------------
    # Click the pill → jump to the week containing the oldest overdue task
    # -----------------------------------------------------------------------
    @app.callback(
        Output("store-week-offset", "data", allow_duplicate=True),
        Input("btn-overdue-pill", "n_clicks"),
        State("store-overdue", "data"),
        prevent_initial_call=True,
    )
    def jump_to_oldest_overdue(n_clicks, overdue):
        if not n_clicks:
            raise PreventUpdate
        oldest = (overdue or {}).get("oldest_day_key")
        if not oldest:
            raise PreventUpdate
        return _week_offset_for_day_key(oldest)
