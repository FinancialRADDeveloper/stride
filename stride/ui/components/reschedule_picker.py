"""Reschedule date-picker modal."""

from __future__ import annotations

import datetime

from dash import html
import dash_mantine_components as dmc

_DAY_SHORT  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _date_label(d: datetime.date) -> str:
    return f"{_DAY_SHORT[d.weekday()]} {d.day} {_MONTH_SHORT[d.month - 1]}"


def _option_row(label: str, day: datetime.date, btn_id: str) -> html.Button:
    return html.Button(
        children=[
            html.Span(label, className="reschedule-option-label"),
            html.Span(_date_label(day), className="reschedule-option-date mono"),
        ],
        id=btn_id,
        className="reschedule-option",
        n_clicks=0,
    )


def reschedule_picker() -> dmc.Modal:
    """Single modal instance shared by all columns. Content computed fresh each layout call."""
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()))
    days_to_sat = (5 - today.weekday()) % 7 or 7
    next_saturday = today + datetime.timedelta(days=days_to_sat)

    return dmc.Modal(
        id="reschedule-modal",
        opened=False,
        withCloseButton=False,
        padding=0,
        size=300,
        styles={
            "content": {
                "borderRadius": "12px",
                "overflow": "hidden",
                "boxShadow": "0 8px 32px rgba(0,0,0,0.18)",
            },
            "body": {"padding": 0},
        },
        children=[
            html.Div(
                className="reschedule-options",
                children=[
                    _option_row("Today",        today,         "btn-reschedule-today"),
                    _option_row("Tomorrow",     tomorrow,      "btn-reschedule-tomorrow"),
                    _option_row("Next week",    next_monday,   "btn-reschedule-next-week"),
                    _option_row("Next weekend", next_saturday, "btn-reschedule-next-weekend"),
                ],
            ),
            html.Div(className="reschedule-divider"),
            html.Div(
                className="reschedule-calendar-wrap",
                children=[
                    dmc.DatePicker(
                        id="reschedule-datepicker",
                        value=None,
                    ),
                ],
            ),
        ],
    )
