"""Detail drawer callbacks: populate drawer content and handle mutations."""

from __future__ import annotations

import datetime

from dash import Input, Output, State, callback, no_update, ctx
from dash.exceptions import PreventUpdate

from stride.db import app_db
from stride.services.tasks import (
    delete_task as svc_delete,
    get_task,
    list_tasks,
    move_task as svc_move,
    update_task,
)
from stride.ui.components.board import _week_days
from stride.ui.components.detail import build_detail_content


def _refresh_tasks(week_offset: int) -> list[dict]:
    """Fetch the current window's tasks as plain dicts (full=True for history)."""
    days = _week_days(week_offset or 0)
    day_keys = [d.isoformat() for d in days]
    conn = app_db()
    tasks = list_tasks(conn, day_keys=day_keys, include_done=True, full=True)
    return [t.model_dump() for t in tasks]


def _refresh_selected(task_id: str) -> dict | None:
    """Re-fetch a single task with full history as a dict."""
    if not task_id:
        return None
    conn = app_db()
    task = get_task(conn, task_id, full=True)
    if task is None:
        return None
    return task.model_dump()


def register_callbacks(app):
    # ------------------------------------------------------------------
    # Populate drawer when a card is selected or store-tasks updates
    # ------------------------------------------------------------------
    @app.callback(
        Output("detail-header-meta", "children"),
        Output("detail-title", "value"),
        Output("detail-description", "value"),
        Output("detail-priority", "value"),
        Output("detail-size", "value"),
        Output("detail-category", "value"),
        Output("detail-estimate", "value"),
        Output("detail-time", "value"),
        Output("detail-assignee", "value"),
        Output("detail-counters", "children"),
        Output("detail-history", "children"),
        Output("detail-drawer", "opened", allow_duplicate=True),
        Input("store-selected", "data"),
        Input("btn-close-drawer", "n_clicks"),
        Input("btn-save-drawer", "n_clicks"),
        Input("store-tasks", "data"),
        prevent_initial_call=True,
    )
    def populate_detail(selected_id, close_clicks, save_clicks, tasks):
        triggered = ctx.triggered_id

        if triggered in ("btn-close-drawer", "btn-save-drawer"):
            return (
                no_update, no_update, no_update, no_update, no_update,
                no_update, no_update, no_update, no_update, no_update, no_update, False
            )

        if not selected_id or not tasks:
            raise PreventUpdate

        # Find the task in the store
        task = next((t for t in tasks if t.get("id") == selected_id), None)
        if task is None:
            raise PreventUpdate

        (
            header_meta,
            title_val,
            desc_val,
            priority_val,
            size_val,
            category_val,
            estimate_val,
            time_val,
            assignee_val,
            counters_el,
            history_el,
        ) = build_detail_content(task)

        opened = no_update
        if triggered == "store-selected":
            opened = True

        return (
            header_meta,
            title_val,
            desc_val,
            priority_val,
            size_val,
            category_val,
            estimate_val if estimate_val is not None else None,
            time_val,
            assignee_val,
            counters_el,
            history_el,
            opened,
        )

    # ------------------------------------------------------------------
    # Save title on blur
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-title", "n_blur"),
        State("detail-title", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_title(n_blur, value, task_id, week_offset):
        if not task_id or value is None:
            raise PreventUpdate
        conn = app_db()
        update_task(conn, task_id, title=value.strip() if value.strip() else value)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save description on blur
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-description", "n_blur"),
        State("detail-description", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_description(n_blur, value, task_id, week_offset):
        if not task_id:
            raise PreventUpdate
        conn = app_db()
        update_task(conn, task_id, description=value or "")
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save priority immediately on change
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-priority", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_priority(value, task_id, week_offset):
        if not task_id or not value:
            raise PreventUpdate
        conn = app_db()
        update_task(conn, task_id, priority=value)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save size immediately on change
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-size", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_size(value, task_id, week_offset):
        if not task_id or not value:
            raise PreventUpdate
        conn = app_db()
        update_task(conn, task_id, size=value)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save category immediately on change
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-category", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_category(value, task_id, week_offset):
        if not task_id or not value:
            raise PreventUpdate
        # category_id is not an editable field via update_task — update directly
        conn = app_db()
        # Guard: only write if the value actually changed
        current = conn.execute(
            "SELECT category_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if current is None or current["category_id"] == value:
            raise PreventUpdate
        import time as _time
        with conn:
            conn.execute(
                "UPDATE tasks SET category_id = ?, updated_at = ? WHERE id = ?",
                (value, int(_time.time() * 1000), task_id),
            )
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save estimate on blur
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-estimate", "n_blur"),
        State("detail-estimate", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_estimate(n_blur, value, task_id, week_offset):
        if not task_id:
            raise PreventUpdate
        conn = app_db()
        estimate = int(value) if value is not None else None
        update_task(conn, task_id, estimate_min=estimate)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save time of day immediately on change
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-time", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_time(value, task_id, week_offset):
        if not task_id:
            raise PreventUpdate
        conn = app_db()
        # value is "HH:MM:SS" from dmc.TimeInput; store as "HH:MM"
        time_val = None
        if value:
            # strip seconds if present
            parts = value.split(":")
            time_val = ":".join(parts[:2]) if len(parts) >= 2 else value
        update_task(conn, task_id, time_of_day=time_val)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Save assignee on blur
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("detail-assignee", "n_blur"),
        State("detail-assignee", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_assignee(n_blur, value, task_id, week_offset):
        if not task_id:
            raise PreventUpdate
        conn = app_db()
        update_task(conn, task_id, assignee=value.strip() if value and value.strip() else None)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Delete task
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Output("store-selected", "data", allow_duplicate=True),
        Output("detail-drawer", "opened", allow_duplicate=True),
        Input("detail-delete", "n_clicks"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def on_delete(n_clicks, task_id, week_offset):
        if not n_clicks or not task_id:
            raise PreventUpdate
        conn = app_db()
        svc_delete(conn, task_id)
        return _refresh_tasks(week_offset), None, False

    # ------------------------------------------------------------------
    # Save & close — flush all text fields then dismiss the drawer
    # Priority / size / category / time already auto-save on change.
    # This covers title, description, estimate, and assignee (blur-based).
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Input("btn-save-drawer", "n_clicks"),
        State("detail-title", "value"),
        State("detail-description", "value"),
        State("detail-estimate", "value"),
        State("detail-assignee", "value"),
        State("store-selected", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def save_and_close(n_clicks, title, description, estimate, assignee, task_id, week_offset):
        if not n_clicks or not task_id:
            raise PreventUpdate
        conn = app_db()
        updates: dict = {}
        if title is not None:
            updates["title"] = title.strip() or title
        if description is not None:
            updates["description"] = description
        if estimate is not None:
            updates["estimate_min"] = int(estimate)
        if assignee is not None:
            updates["assignee"] = assignee.strip() or None
        if updates:
            update_task(conn, task_id, **updates)
        return _refresh_tasks(week_offset)

    # ------------------------------------------------------------------
    # Context-menu delete — triggered by right-click "Delete task"
    # Uses store-ctx-delete written by context_menu.js via set_props.
    # ------------------------------------------------------------------
    @app.callback(
        Output("store-tasks", "data", allow_duplicate=True),
        Output("store-selected", "data", allow_duplicate=True),
        Output("detail-drawer", "opened", allow_duplicate=True),
        Input("store-ctx-delete", "data"),
        State("store-week-offset", "data"),
        prevent_initial_call=True,
    )
    def on_ctx_delete(task_id, week_offset):
        if not task_id:
            raise PreventUpdate
        conn = app_db()
        svc_delete(conn, task_id)
        return _refresh_tasks(week_offset), None, False
