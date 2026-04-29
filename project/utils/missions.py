"""ระบบภารกิจรายวัน/รายสัปดาห์"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

TZ_BKK = timezone(timedelta(hours=7))


def _today_bkk() -> str:
    return datetime.now(TZ_BKK).date().isoformat()


def _week_bkk() -> str:
    now = datetime.now(TZ_BKK).isocalendar()
    return f"{now.year}-W{now.week}"


def reset_daily_missions(user_data: dict[str, Any]) -> None:
    daily = user_data.setdefault("daily_missions", {"date": None, "tasks_done": 0, "chat_done": 0, "daily_claimed": False})
    if daily.get("date") != _today_bkk():
        daily.update({"date": _today_bkk(), "tasks_done": 0, "chat_done": 0, "daily_claimed": False})


def reset_weekly_missions(user_data: dict[str, Any]) -> None:
    weekly = user_data.setdefault("weekly_missions", {"week": None, "tasks_done": 0})
    if weekly.get("week") != _week_bkk():
        weekly.update({"week": _week_bkk(), "tasks_done": 0})


def update_mission_progress(user_data: dict[str, Any], action: str) -> None:
    reset_daily_missions(user_data)
    reset_weekly_missions(user_data)
    if action == "task_pass":
        user_data["daily_missions"]["tasks_done"] = int(user_data["daily_missions"].get("tasks_done", 0)) + 1
        user_data["weekly_missions"]["tasks_done"] = int(user_data["weekly_missions"].get("tasks_done", 0)) + 1
    elif action == "chat":
        user_data["daily_missions"]["chat_done"] = int(user_data["daily_missions"].get("chat_done", 0)) + 1
    elif action == "daily_claim":
        user_data["daily_missions"]["daily_claimed"] = True
