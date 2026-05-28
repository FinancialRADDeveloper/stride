"""Achievements service — completed task history, stats, and streak.

Returns a structured dict consumed by the achievements panel component.
Pure Python, no Dash imports — testable in isolation.
"""

from __future__ import annotations

import datetime
import sqlite3
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_minutes(minutes: int | None) -> str:
    if not minutes:
        return ""
    if minutes < 60:
        return f"{minutes}m"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m}m" if m else f"{h}h"


def _day_label(date: datetime.date, today: datetime.date) -> str:
    diff = (today - date).days
    if diff == 0:
        return "Today"
    if diff == 1:
        return "Yesterday"
    return date.strftime("%-d %b")   # e.g. "23 May"  (Linux/Mac; falls back below)


def _safe_day_label(date: datetime.date, today: datetime.date) -> str:
    """strftime %-d is Linux-only; handle Windows gracefully."""
    try:
        return _day_label(date, today)
    except ValueError:
        diff = (today - date).days
        if diff == 0:
            return "Today"
        if diff == 1:
            return "Yesterday"
        return date.strftime("%d %b").lstrip("0")   # "05 May" → "5 May"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_achievements(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return completed task history grouped by calendar day, with stats.

    Structure:
        {
            "stats": {"week_count": int, "week_min": int, "streak": int},
            "days": [
                {
                    "label": str,       # "Today", "Yesterday", "23 May" …
                    "date": str,        # "YYYY-MM-DD"
                    "count": int,
                    "tasks": [
                        {
                            "id": str,
                            "title": str,
                            "category_id": str,
                            "priority": str,        # "P1"…"P4"
                            "estimate_min": int|None,
                            "completed_at_ms": int,
                            "time_str": str,        # "14:32"
                        }
                    ]
                },
                …
            ]
        }
    """
    today = datetime.date.today()
    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    week_ago_ms = now_ms - 7 * 24 * 60 * 60 * 1000

    # All 'done' events joined to their task.
    rows = conn.execute(
        """
        SELECT
            t.id,
            t.title,
            t.category_id,
            t.priority,
            t.estimate_min,
            e.ts   AS completed_at_ms
        FROM task_events e
        JOIN tasks t ON t.id = e.task_id
        WHERE e.kind = 'done'
        ORDER BY e.ts DESC
        """,
    ).fetchall()

    # Deduplicate: a task that was done → reopened → done again keeps only
    # the most-recent 'done' timestamp (we see it once in the history).
    seen: dict[str, dict[str, Any]] = {}
    for r in rows:
        task_id: str = r["id"]
        if task_id not in seen or r["completed_at_ms"] > seen[task_id]["completed_at_ms"]:
            seen[task_id] = dict(r)

    completions = sorted(seen.values(), key=lambda x: x["completed_at_ms"], reverse=True)

    # --- Stats ---------------------------------------------------------------
    week_tasks = [c for c in completions if c["completed_at_ms"] >= week_ago_ms]
    week_count = len(week_tasks)
    week_min   = sum(c["estimate_min"] or 0 for c in week_tasks)

    # Streak: consecutive calendar days ending today (or yesterday) with ≥1 completion
    completion_dates: set[datetime.date] = set()
    for c in completions:
        d = datetime.date.fromtimestamp(c["completed_at_ms"] / 1000)
        completion_dates.add(d)

    streak = 0
    check = today if today in completion_dates else today - datetime.timedelta(days=1)
    while check in completion_dates:
        streak += 1
        check -= datetime.timedelta(days=1)

    # --- Group by day --------------------------------------------------------
    days_map: dict[str, dict[str, Any]] = {}
    for c in completions:
        d = datetime.date.fromtimestamp(c["completed_at_ms"] / 1000)
        dk = d.isoformat()
        if dk not in days_map:
            days_map[dk] = {
                "label": _safe_day_label(d, today),
                "date":  dk,
                "count": 0,
                "tasks": [],
            }
        ts = datetime.datetime.fromtimestamp(c["completed_at_ms"] / 1000)
        days_map[dk]["tasks"].append(
            {
                "id":              c["id"],
                "title":           c["title"],
                "category_id":     c["category_id"] or "personal",
                "priority":        c["priority"],
                "estimate_min":    c["estimate_min"],
                "completed_at_ms": c["completed_at_ms"],
                "time_str":        ts.strftime("%H:%M"),
            }
        )
        days_map[dk]["count"] += 1

    # Sort days newest-first
    days = sorted(days_map.values(), key=lambda x: x["date"], reverse=True)

    return {
        "stats": {
            "week_count": week_count,
            "week_min":   week_min,
            "streak":     streak,
        },
        "days": days,
    }
