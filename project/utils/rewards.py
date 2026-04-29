"""ระบบคำนวณ EXP/Coins/Rank"""

from __future__ import annotations

from typing import Any

EXP_MULTIPLIER = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
COINS_MULTIPLIER = {"easy": 1.0, "medium": 1.5, "hard": 2.0}

RANK_TABLE = {
    "Bronze": (0, 499),
    "Silver": (500, 1499),
    "Gold": (1500, 2999),
    "Platinum": (3000, 4999),
    "Diamond": (5000, 7999),
    "Master": (8000, 11999),
    "Legend": (12000, 10**9),
}


def get_level(exp: int) -> int:
    return max(1, exp // 100 + 1)


def get_rank(exp: int) -> str:
    for rank, (lo, hi) in RANK_TABLE.items():
        if lo <= exp <= hi:
            return rank
    return "Bronze"


def apply_task_rewards(user_data: dict[str, Any], task: dict[str, Any], first_clear: bool) -> dict[str, int]:
    difficulty = str(task.get("difficulty", "easy")).lower()
    base_exp = int(task.get("exp", 20) * EXP_MULTIPLIER.get(difficulty, 1.0))
    base_coins = int(task.get("coins", 5) * COINS_MULTIPLIER.get(difficulty, 1.0))
    if first_clear:
        base_exp = int(base_exp * 1.5)
        base_coins = int(base_coins * 1.5)
    else:
        base_exp = int(base_exp * 0.5)
        base_coins = int(base_coins * 0.5)

    user_data["coding_exp"] = int(user_data.get("coding_exp", 0)) + base_exp
    user_data["coins"] = int(user_data.get("coins", 0)) + base_coins
    user_data["coding_level"] = get_level(int(user_data.get("coding_exp", 0)))
    user_data["rank"] = get_rank(int(user_data.get("coding_exp", 0)))
    return {"exp": base_exp, "coins": base_coins}
