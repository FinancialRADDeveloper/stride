"""Task card component."""

from __future__ import annotations

import datetime

from dash import html

from stride.ui.theme import PRIORITY_COLOURS, CATEGORY_COLOURS

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
_MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _week_days_for_card(week_offset: int = 0) -> list[datetime.date]:
    """Return the 6 visible day dates for the given week offset."""
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    start = monday + datetime.timedelta(days=6 * week_offset)
    return [start + datetime.timedelta(days=i) for i in range(6)]


def _day_label(day: datetime.date) -> str:
    today = datetime.date.today()
    diff = (day - today).days
    if diff == 0:
        return "Today"
    if diff == 1:
        return "Tomorrow"
    if diff == -1:
        return "Yesterday"
    day_name = _DAY_NAMES[day.weekday()]
    date_str = f"{day.day} {_MONTH_SHORT[day.month - 1]}"
    return f"{day_name} {date_str}"


# Background tints for priority badges
_PRIORITY_BG = {
    "P1": "#fef2f2",
    "P2": "#fffbeb",
    "P3": "#eef2ff",
    "P4": "#f9fafb",
}

_PRIORITY_LABEL = {
    "P1": "Critical",
    "P2": "High",
    "P3": "Normal",
    "P4": "Low",
}

_SIZE_HINT = {
    "XS": "<15m",
    "S": "~25m",
    "M": "~1h",
    "L": "~2h",
    "XL": "half day",
}


def _fmt_minutes(minutes: int | None) -> str:
    if minutes is None:
        return ""
    if minutes < 60:
        return f"{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"


def task_card(task: dict, week_offset: int = 0) -> html.Div:
    """Render a single task card.

    ID is pattern-matched: {'type': 'card', 'task_id': task['id']}
    week_offset is used to generate move-to menu items for other days.
    """
    task_id = task["id"]
    priority = task.get("priority", "P3")
    size = task.get("size", "M")
    done = task.get("done", False)
    is_stale = task.get("is_stale", False)
    move_count = task.get("move_count", 0)
    edit_count = task.get("edit_count", 0)
    age_days = task.get("age_days", 0)
    estimate_min = task.get("estimate_min")
    title = task.get("title", "")
    description = task.get("description", "")
    category_id = task.get("category_id", "personal")
    current_day_key = task.get("day_key", "")

    pri_colour = PRIORITY_COLOURS.get(priority, "#9ca3af")
    pri_bg = _PRIORITY_BG.get(priority, "#f9fafb")
    cat_colour = CATEGORY_COLOURS.get(category_id, "#9ca3af")

    card_classes = "task-card"
    if done:
        card_classes += " task-card--done"
    if is_stale:
        card_classes += " task-card--stale"

    children = []

    # Category colour strip on left edge
    children.append(
        html.Div(
            className="card-category-strip",
            style={"background": cat_colour},
            title=category_id,
        )
    )

    # Stale badge
    if is_stale:
        children.append(
            html.Div(
                "STALE",
                className="card-stale-badge mono",
                title=f"Moved {move_count} times — consider breaking it down or dropping it",
            )
        )

    # Checkbox + title row
    checkbox_classes = "card-checkbox"
    if done:
        checkbox_classes += " card-checkbox--done"

    title_classes = "card-title"
    if done:
        title_classes += " card-title--done"

    children.append(
        html.Div(
            className="card-top-row",
            children=[
                html.Button(
                    "✓" if done else "",
                    id={"type": "btn-toggle-done", "task_id": task_id},
                    className=checkbox_classes,
                    n_clicks=0,
                    title="Reopen task" if done else "Complete task",
                    style={"borderColor": pri_colour, "background": pri_colour if done else "transparent"},
                ),
                html.Div(
                    className="card-title-block",
                    children=[
                        html.Div(title, className=title_classes),
                        html.Div(
                            description,
                            className="card-description",
                        ) if description else None,
                    ],
                ),
            ],
        )
    )

    # Bottom metadata row
    meta_chips = []

    # Priority chip
    meta_chips.append(
        html.Span(
            [
                html.Span(className="chip-dot", style={"background": pri_colour}),
                html.Span(_PRIORITY_LABEL.get(priority, priority), className="mono"),
            ],
            className="chip chip--priority mono",
            style={"color": pri_colour, "background": pri_bg},
            title=f"{_PRIORITY_LABEL.get(priority, priority)} priority",
        )
    )

    # Size chip
    meta_chips.append(
        html.Span(
            size,
            className="chip chip--size mono",
            title=f"Size: {size} ({_SIZE_HINT.get(size, '')})",
        )
    )

    # Estimate chip
    if estimate_min is not None:
        meta_chips.append(
            html.Span(
                _fmt_minutes(estimate_min),
                className="chip chip--estimate mono",
                title="Estimated time",
            )
        )

    # Spacer
    meta_chips.append(html.Div(className="chip-spacer"))

    # Edit/move/age glyphs on the right
    glyph_parts = []
    if edit_count > 0:
        glyph_parts.append(
            html.Span(
                f"✎ {edit_count}" if edit_count > 1 else "✎",
                className="glyph mono",
                title=f"{edit_count} edit{'s' if edit_count > 1 else ''}",
            )
        )
    if move_count > 0:
        glyph_parts.append(
            html.Span(
                f"⟳ {move_count}",
                className="glyph mono",
                title=f"Moved {move_count} time{'s' if move_count > 1 else ''}",
            )
        )
    if age_days > 0:
        age_class = "glyph mono glyph--old" if age_days >= 7 else "glyph mono"
        glyph_parts.append(
            html.Span(
                f"{age_days}d",
                className=age_class,
                title=f"Created {age_days} day{'s' if age_days > 1 else ''} ago",
            )
        )

    if glyph_parts:
        meta_chips.append(
            html.Div(glyph_parts, className="card-glyphs")
        )

    children.append(
        html.Div(meta_chips, className="card-meta")
    )

    card_div = html.Div(
        children=children,
        id={"type": "card", "task_id": task_id},
        className=card_classes,
        n_clicks=0,
    )

    # Move-to flyout — plain HTML buttons in a CSS hover-shown dropdown.
    # Keeps Dash pattern-matched IDs on each day button without Mantine context issues.
    visible_days = _week_days_for_card(week_offset)
    day_buttons = []
    for day in visible_days:
        day_key = day.isoformat()
        if day_key == current_day_key:
            continue  # skip current day
        label = _day_label(day)
        day_buttons.append(
            html.Button(
                label,
                id={"type": "btn-move-to", "task_id": task_id, "day_key": day_key},
                className="move-day-btn",
                n_clicks=0,
            )
        )

    move_flyout = html.Div(
        [
            html.Button("→", className="card-move-btn", title="Move to…"),
            html.Div(
                [html.Div("Move to", className="move-menu-label mono")] + day_buttons,
                className="move-menu-dropdown",
            ),
        ],
        className="card-move-wrapper",
    )

    # Wrapper positions the move flyout as an absolute overlay on the card
    return html.Div(
        [card_div, move_flyout],
        className="card-wrapper",
        style={"position": "relative"},
    )
