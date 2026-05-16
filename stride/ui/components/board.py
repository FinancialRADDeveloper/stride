"""Board and column components."""

from __future__ import annotations

import datetime
from typing import Sequence

from dash import html

from stride.ui.components.card import task_card
from stride.ui.components.composer import composer
from stride.ui.theme import CAPACITY_OK_COLOUR, CAPACITY_WARN_COLOUR, CAPACITY_OVER_COLOUR

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

DAY_CAPACITY_MIN = 480  # 8h soft cap


def _week_days(week_offset: int) -> list[datetime.date]:
    """Return dates for the board window.

    offset=0: Monday of this week through today+5, so at least 5 future
    days are always visible regardless of the current weekday.
    Other offsets: fixed 6-day chunks anchored to Monday.
    """
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    start = monday + datetime.timedelta(days=6 * week_offset)
    if week_offset == 0:
        end = today + datetime.timedelta(days=5)
        n = max(6, (end - monday).days + 1)
    else:
        n = 6
    return [start + datetime.timedelta(days=i) for i in range(n)]


def _fmt_minutes(minutes: int) -> str:
    if minutes == 0:
        return "0m"
    if minutes < 60:
        return f"{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"


def _day_column(
    day: datetime.date,
    tasks: list[dict],
    is_first: bool,
    week_offset: int = 0,
) -> html.Div:
    """Render one day column."""
    today = datetime.date.today()
    is_today = day == today
    is_past = day < today

    day_key = day.isoformat()
    day_name = _DAY_NAMES[day.weekday()]
    date_label = f"{day.day:02d} {_MONTH_SHORT[day.month - 1]}"

    open_tasks = [t for t in tasks if not t.get("done", False)]
    total_min = sum(t.get("estimate_min") or 0 for t in open_tasks)
    cap_pct = min(100, int((total_min / DAY_CAPACITY_MIN) * 100))
    over = total_min > DAY_CAPACITY_MIN

    # Capacity bar colour
    if over:
        bar_colour = CAPACITY_OVER_COLOUR
    elif cap_pct > 75:
        bar_colour = CAPACITY_WARN_COLOUR
    else:
        bar_colour = CAPACITY_OK_COLOUR

    col_classes = "day-column"
    if is_today:
        col_classes += " day-column--today"
    if is_past:
        col_classes += " day-column--past"
    if is_first:
        col_classes += " day-column--first"

    # Day label: "Today", "Tomorrow", or weekday name
    diff = (day - today).days
    if diff == 0:
        day_label = "Today"
    elif diff == 1:
        day_label = "Tomorrow"
    else:
        day_label = day_name

    # Column header
    header = html.Div(
        className="col-header",
        children=[
            html.Div(
                className="col-header-top",
                children=[
                    html.Div(
                        className="col-header-name-row",
                        children=[
                            html.H2(
                                day_label,
                                className="col-day-label" + (" col-day-label--past" if is_past else ""),
                            ),
                            html.Span("NOW", className="col-now-badge mono") if is_today else None,
                        ],
                    ),
                    html.Span(date_label, className="col-date mono"),
                ],
            ),
            html.Div(
                className="col-header-stats",
                children=[
                    html.Span(
                        f"{len(open_tasks)} open · {_fmt_minutes(total_min)}",
                        className="col-stats mono",
                    ),
                    html.Button(
                        "Reschedule →",
                        id={"type": "btn-reschedule-day", "day_key": day_key},
                        className="btn-reschedule",
                        n_clicks=0,
                        title=f"Reschedule open tasks from {day_label}",
                    ) if ((is_past or is_today) and open_tasks) else None,
                    html.Span(
                        f"{cap_pct}%",
                        className="col-cap-pct mono" + (" col-cap-pct--over" if over else ""),
                        title="Soft capacity: 8 hours",
                    ),
                ],
            ),
            # Capacity bar
            html.Div(
                className="col-cap-track",
                children=[
                    html.Div(
                        className="col-cap-bar",
                        style={"width": f"{cap_pct}%", "background": bar_colour},
                    ),
                ],
            ),
        ],
    )

    # Card stack
    card_children = []

    if not tasks:
        card_children.append(
            html.Div(
                f"nothing for {day_label.lower()}",
                className="col-empty serif",
            )
        )
    else:
        for t in tasks:
            card_children.append(task_card(t, week_offset=week_offset))

    # Composer (hidden by default, shown via callback)
    card_children.append(composer(day_key))

    # Add task button
    card_children.append(
        html.Button(
            "+ Add task",
            id={"type": "btn-add", "day_key": day_key},
            className="btn-add-task",
            n_clicks=0,
        )
    )

    card_stack = html.Div(
        card_children,
        className="col-cards",
        id={"type": "col-drop", "day_key": day_key},
    )

    # data-drop-day on the outer column so the entire column (header + cards)
    # is a drop target; dnd.js reads this attribute to know the destination day.
    return html.Div(
        [header, card_stack],
        className=col_classes,
        **{"data-drop-day": day_key},
    )


def board(tasks: list[dict] | None = None, week_offset: int = 0) -> html.Div:
    """Render the horizontally-scrolling board of 6 day columns.

    tasks: flat list of task dicts (all days); will be filtered per column.
    week_offset: drives which 6 days are shown.
    """
    if tasks is None:
        tasks = []

    days = _week_days(week_offset)

    # Group tasks by day_key
    tasks_by_day: dict[str, list[dict]] = {d.isoformat(): [] for d in days}
    for t in tasks:
        dk = t.get("day_key", "")
        if dk in tasks_by_day:
            tasks_by_day[dk].append(t)

    # Sort within each day: open first (by priority then created_at), done last
    _pri_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    for dk, day_tasks in tasks_by_day.items():
        day_tasks.sort(key=lambda t: (
            1 if t.get("done") else 0,
            _pri_order.get(t.get("priority", "P3"), 2),
            t.get("created_at", 0),
        ))

    today = datetime.date.today()
    columns = []
    for day in days:
        day_tasks = tasks_by_day[day.isoformat()]
        if day < today and not day_tasks:
            continue
        columns.append(_day_column(day, day_tasks, len(columns) == 0, week_offset=week_offset))

    return html.Div(
        html.Div(columns, className="board-inner"),
        className="board",
        id="board",
    )
