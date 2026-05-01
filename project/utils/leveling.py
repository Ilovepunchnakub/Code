"""โมดูลคำนวณเลเวล แรงค์ คอมโบ และรางวัล"""

from __future__ import annotations

import math
from typing import Any


RANK_TABLE = [
    ("Bronze", 0),
    ("Silver", 200),
    ("Gold", 500),
    ("Platinum", 900),
    ("Diamond", 1400),
    ("Master", 2200),
    ("Grandmaster", 3200),
    ("Legend", 4500),
]

DIFFICULTY_EXP = {"easy": 20, "medium": 50, "hard": 120}


def exp_to_level(exp: int) -> int:
    """สูตรเลเวลตามสเปค: level = sqrt(exp/100) แต่เริ่มขั้นต่ำที่ 1"""

    return max(1, int(math.sqrt(max(exp, 0) / 100)) + 1)


def level_progress(exp: int) -> tuple[int, int, int]:
    """คืนค่า (level, current_exp_in_level, required_exp_in_level)"""

    level = exp_to_level(exp)
    prev_total = int(((level - 1) ** 2) * 100)
    next_total = int((level**2) * 100)
    return level, exp - prev_total, next_total - prev_total


def calculate_rank(user_data: dict[str, Any]) -> str:
    """คำนวณแรงค์จาก exp + accuracy แบบง่ายและโปร่งใส"""

    accuracy = 0.0
    if user_data.get("attempted", 0) > 0:
        accuracy = (user_data.get("correct", 0) / user_data.get("attempted", 1)) * 100

    score = user_data.get("exp", 0) + int(accuracy * 3)
    current = "Bronze"
    for rank_name, threshold in RANK_TABLE:
        if score >= threshold:
            current = rank_name
    return current


def combo_multiplier(combo_count: int) -> float:
    """คืน multiplier คอมโบตามเงื่อนไข"""

    if combo_count >= 10:
        return 1.25
    if combo_count >= 5:
        return 1.25
    if combo_count >= 2:
        return 1.10
    return 1.0


def apply_rewards(user_data: dict[str, Any], task: dict[str, Any], first_clear: bool) -> dict[str, Any]:
    """อัปเดตรางวัล exp/coins/combo/badge แล้วคืนข้อมูลผู้ใช้ใหม่"""

    difficulty = str(task.get("difficulty", "easy")).lower()
    base_exp = int(task.get("exp", DIFFICULTY_EXP.get(difficulty, 20)))
    base_coins = int(task.get("coins", 5))

    if first_clear:
        base_exp = int(base_exp * 1.5)

    user_data["combo_count"] = int(user_data.get("combo_count", 0)) + 1
    multiplier = combo_multiplier(user_data["combo_count"])

    gained_exp = int(base_exp * multiplier)
    gained_coins = int(base_coins * multiplier)

    user_data["exp"] = int(user_data.get("exp", 0)) + gained_exp
    user_data["coins"] = int(user_data.get("coins", 0)) + gained_coins
    user_data["level"] = exp_to_level(user_data["exp"])
    user_data["rank"] = calculate_rank(user_data)

    badges = user_data.setdefault("badges", [])
    if user_data["combo_count"] >= 10 and "Rare Chest Hunter" not in badges:
        badges.append("Rare Chest Hunter")

    return {
        "exp": gained_exp,
        "coins": gained_coins,
        "combo": user_data["combo_count"],
        "multiplier": multiplier,
    }
