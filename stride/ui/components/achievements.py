"""Achievements panel component — left-side drawer showing completed task history.

Pure builder functions — no callbacks here. Returns html.* / dmc.* trees.
The panel is populated by achievements_cb.py via a dcc.Store.
"""

from __future__ import annotations

from dash import html
import dash_mantine_components as dmc

from stride.ui.theme import CATEGORY_COLOURS, PRIORITY_COLOURS


# ---------------------------------------------------------------------------
# Sub-components
# ---------------------------------------------------------------------------

def _priority_dot(priority: str) -> html.Span:
    colour = PRIORITY_COLOURS.get(priority, "#9ca3af")
    return html.Span(
        style={
            "display": "inline-block",
            "width": "7px",
            "height": "7px",
            "borderRadius": "50%",
            "background": colour,
            "flexShrink": "0",
            "marginTop": "5px",
        }
    )


def _category_dot(category_id: str) -> html.Span:
    colour = CATEGORY_COLOURS.get(category_id, "#9ca3af")
    return html.Span(
        className="ach-cat-dot",
        style={"background": colour},
    )


def _task_row(task: dict) -> html.Div:
    """One completed task row: category dot · title · priority · time."""
    return html.Div(
        className="ach-task-row",
        children=[
            _category_dot(task["category_id"]),
            html.Span(task["title"], className="ach-task-title"),
            html.Span(task["priority"], className=f"ach-priority ach-priority--{task['priority'].lower()}"),
            html.Span(task["time_str"], className="ach-task-time mono"),
        ],
    )


def _day_group(day: dict) -> html.Div:
    """One day block: heading + list of completed task rows."""
    label = f"{day['label']} — {day['count']} done"
    return html.Div(
        className="ach-day-group",
        children=[
            html.Div(label, className="ach-day-label"),
            html.Div(
                className="ach-task-list",
                children=[_task_row(t) for t in day["tasks"]],
            ),
        ],
    )


def _stats_bar(stats: dict) -> html.Div:
    """Summary line: X done this week · Xh Xm · X-day streak."""
    week_count = stats.get("week_count", 0)
    week_min   = stats.get("week_min", 0)
    streak     = stats.get("streak", 0)

    # Format time
    if week_min >= 60:
        h = week_min // 60
        m = week_min % 60
        time_str = f"{h}h {m}m" if m else f"{h}h"
    elif week_min > 0:
        time_str = f"{week_min}m"
    else:
        time_str = "0m"

    streak_label = f"{streak}-day streak 🔥" if streak >= 2 else (
        "1-day streak" if streak == 1 else "no streak yet"
    )

    parts = [
        html.Span(f"{week_count} done this week", className="ach-stat-item"),
        html.Span("·", className="ach-stat-sep"),
        html.Span(time_str, className="ach-stat-item"),
        html.Span("·", className="ach-stat-sep"),
        html.Span(streak_label, className="ach-stat-item"),
    ]

    return html.Div(parts, className="ach-stats-bar")


def _empty_state() -> html.Div:
    return html.Div(
        "Nothing completed yet — go tick something off! ✓",
        className="ach-empty",
    )


# ---------------------------------------------------------------------------
# Panel shell (mounted once in app.py; populated by callbacks)
# ---------------------------------------------------------------------------

def achievements_panel() -> dmc.Drawer:
    """Return the achievements drawer shell.

    Content is rendered into #ach-content by the achievements callback.
    The drawer opens/closes via store-achievements-open.
    """
    return dmc.Drawer(
        id="achievements-drawer",
        opened=False,
        position="left",
        size="480px",
        withOverlay=False,          # board stays interactive behind the panel
        withCloseButton=False,      # we provide our own header close button
        styles={
            "body":   {"padding": "0", "background": "var(--surface)", "height": "100%"},
            "header": {"display": "none"},
            "inner":  {"top": "56px"},   # sit below the topbar
        },
        children=html.Div(
            className="ach-panel",
            children=[
                # Header row
                html.Div(
                    className="ach-header",
                    children=[
                        html.Span("Achievements", className="ach-title"),
                        html.Button(
                            "✕",
                            id="btn-achievements-close",
                            className="btn-icon",
                            n_clicks=0,
                        ),
                    ],
                ),
                # Stats bar (populated by callback)
                html.Div(id="ach-stats"),
                # Scrollable day groups (populated by callback)
                html.Div(id="ach-content", className="ach-scroll"),
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Public render helper called from the callback
# ---------------------------------------------------------------------------

def render_achievements(data: dict) -> tuple[html.Div, html.Div]:
    """Return (stats_bar_children, content_children) from get_achievements() output.

    Called by the achievements callback to populate #ach-stats and #ach-content.
    """
    stats = data.get("stats", {})
    days  = data.get("days", [])

    stats_el   = _stats_bar(stats)
    content_el = html.Div(
        [_day_group(d) for d in days] if days else [_empty_state()]
    )
    return stats_el, content_el
