"""ตัวช่วยอ่านเขียน JSON แบบ async thread-safe"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
USERS_PATH = BASE_DIR / "users.json"
ASSIGNMENTS_PATH = BASE_DIR / "assignments.json"
_lock = asyncio.Lock()


def _default_user(user_id: str, name: str) -> dict[str, Any]:
    return {
        "name": name,
        "coding_exp": 0,
        "coding_level": 1,
        "chat_exp": 0,
        "chat_level": 1,
        "coins": 0,
        "rank": "Bronze",
        "tasks_cleared": 0,
        "tasks_attempted": 0,
        "streak": 0,
        "last_daily": None,
        "last_chat_exp": None,
        "achievements": [],
        "cleared_tasks": [],
        "history": [],
        "hard_cleared": 0,
        "clean_pass": 0,
        "best_streak": 0,
        "fav_lang": None,
        "c_cleared": 0,
        "python_cleared": 0,
        "join_date": None,
        "last_seen": None,
        "user_id": user_id,
    }


async def load_users() -> dict[str, Any]:
    async with _lock:
        if not USERS_PATH.exists():
            USERS_PATH.write_text("{}", encoding="utf-8")
        return json.loads(USERS_PATH.read_text(encoding="utf-8") or "{}")


async def save_users(data: dict[str, Any]) -> None:
    async with _lock:
        USERS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def load_assignments() -> dict[str, Any]:
    if not ASSIGNMENTS_PATH.exists():
        ASSIGNMENTS_PATH.write_text("{}", encoding="utf-8")
    return json.loads(ASSIGNMENTS_PATH.read_text(encoding="utf-8") or "{}")


async def save_assignments(data: dict[str, Any]) -> None:
    async with _lock:
        ASSIGNMENTS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def get_user(user_id: str, name: str = "Unknown") -> dict[str, Any]:
    users = await load_users()
    if user_id not in users:
        users[user_id] = _default_user(user_id, name)
    else:
        default = _default_user(user_id, users[user_id].get("name", name))
        for key, value in default.items():
            users[user_id].setdefault(key, value)
    if not users[user_id].get("join_date"):
        users[user_id]["join_date"] = __import__("datetime").datetime.utcnow().isoformat()
    await save_users(users)
    return users[user_id]


async def update_user(user_id: str, updates: dict[str, Any]) -> None:
    users = await load_users()
    current = users.get(user_id, _default_user(user_id, updates.get("name", "Unknown")))
    current.update(updates)
    users[user_id] = current
    await save_users(users)
