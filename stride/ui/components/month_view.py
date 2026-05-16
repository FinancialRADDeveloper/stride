"""Month calendar grid view."""

from __future__ import annotations

import datetime

from dash import html

from stride.ui.theme import PRIORITY_COLOURS, CATEGORY_COLOURS

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_DAY_HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def _anchor_month(week_offset: int) -> tuple[int, int]:
    """Return (year, month) for the given week offset."""
    today = datetime.date.today()
    anchor = today + datetime.timedelta(weeks=week_offset)
    return anchor.year, anchor.month


def month_view(tasks: list[dict], week_offset: int) -> html.Div:
    """Render a full-month calendar grid."""
    today = datetime.date.today()
    year, month = _anchor_month(week_offset)

    first_of_month = datetime.date(year, month, 1)
    if month == 12:
        first_of_next = datetime.date(year + 1, 1, 1)
    else:
        first_of_next = datetime.date(year, month + 1, 1)
    last_of_month = first_of_next - datetime.timedelta(days=1)

    # Index tasks by day_key
    tasks_by_day: dict[str, list[dict]] = {}
    for t in tasks:
        dk = t.get("day_key", "")
        if dk:
            tasks_by_day.setdefault(dk, []).append(t)

    # Grid starts on Monday of the week containing the 1st of the month
    grid_start = first_of_month - datetime.timedelta(days=first_of_month.weekday())
    # Grid ends on Sunday of the week containing the last day
    grid_end = last_of_month + datetime.timedelta(days=6 - last_of_month.weekday())

    # Build header row
    header_row = html.Div(
        [html.Div(h, className="month-header-cell mono") for h in _DAY_HEADERS],
        className="month-row month-header-row",
    )

    # Build week rows
    rows = [header_row]
    current = grid_start
    while current <= grid_end:
        cells = []
        for _ in range(7):
            day_tasks = tasks_by_day.get(current.isoformat(), [])
            open_tasks = [t for t in day_tasks if not t.get("done", False)]
            done_tasks = [t for t in day_tasks if t.get("done", False)]

            in_month = current.month == month
            is_today = current == today
            is_past = current < today

            cell_cls = "month-cell"
            if not in_month:
                cell_cls += " month-cell--outside"
            if is_today:
                cell_cls += " month-cell--today"
            elif is_past:
                cell_cls += " month-cell--past"

            day_num_cls = "month-day-num mono"
            if is_today:
                day_num_cls += " month-day-num--today"

            # Task pills — up to 3 open, then "+N more"
            pills = []
            for t in open_tasks[:3]:
                priority = t.get("priority", "P3")
                colour = PRIORITY_COLOURS.get(priority, "#9ca3af")
                pills.append(
                    html.Div(
                        t.get("title", "")[:24],
                        className="month-task-pill mono",
                        style={"borderLeft": f"2px solid {colour}"},
                        title=t.get("title", ""),
                    )
                )
            overflow = len(open_tasks) - 3
            if overflow > 0:
                pills.append(
                    html.Div(f"+{overflow} more", className="month-task-more mono")
                )

            # Done count indicator
            done_indicator = (
                html.Div(f"✓ {len(done_tasks)}", className="month-done-count mono")
                if done_tasks and in_month else None
            )

            cells.append(
                html.Div(
                    className=cell_cls,
                    children=[
                        html.Div(str(current.day), className=day_num_cls),
                        html.Div(pills, className="month-task-list"),
                        done_indicator,
                    ],
                )
            )
            current += datetime.timedelta(days=1)

        rows.append(html.Div(cells, className="month-row"))

    return html.Div(rows, className="month-grid")
