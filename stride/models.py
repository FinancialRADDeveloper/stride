"""Pydantic v2 models and constants for Stride task board."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Constants (mirror the HTML prototype)
# ---------------------------------------------------------------------------

SIZE_MINUTES: dict[str, int] = {
    "XS": 10,
    "S": 25,
    "M": 60,
    "L": 120,
    "XL": 240,
}

SIZE_HINT: dict[str, str] = {
    "XS": "<15m",
    "S": "~25m",
    "M": "~1h",
    "L": "~2h",
    "XL": "half day",
}

PRIORITY_LABEL: dict[str, str] = {
    "P1": "Critical",
    "P2": "High",
    "P3": "Normal",
    "P4": "Low",
}

DAY_CAPACITY_MIN: int = 480  # soft 8-hour day

STALE_MOVE_THRESHOLD: int = 3


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TaskEvent(BaseModel):
    id: int
    task_id: str
    ts: int  # unix ms
    kind: Literal[
        "created",
        "moved",
        "edited",
        "done",
        "reopened",
        "scheduled",
        "unscheduled",
        "deleted",
    ]
    payload: dict[str, Any] = {}


class CalendarLink(BaseModel):
    calendar_id: str
    google_event_id: str
    etag: str | None = None
    last_pushed_at: int | None = None
    last_pulled_at: int | None = None
    origin: Literal["stride", "google"] = "stride"


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    priority: Literal["P1", "P2", "P3", "P4"] = "P3"
    size: Literal["XS", "S", "M", "L", "XL"] = "M"
    estimate_min: int | None = None
    time_of_day: str | None = None  # 'HH:MM'
    day_key: str  # 'YYYY-MM-DD'
    done: bool = False
    created_at: int
    updated_at: int
    # computed — populated by the service layer, never stored
    move_count: int = 0
    edit_count: int = 0
    age_days: int = 0
    is_stale: bool = False
    calendar: CalendarLink | None = None
    history: list[TaskEvent] = []  # only loaded when full=True
