"""ระบบ Achievement 100 แบบ พร้อมตัวตรวจปลดล็อก"""

from __future__ import annotations

from typing import Any

ACHIEVEMENT_NAMES = [
    "First Step", "Hello World", "New Challenger", "Rookie Coder", "Learning Begins", "Explorer", "Curious Mind", "Try Again", "Never Quit", "Warm Up",
    "3 Day Streak", "7 Day Streak", "14 Day Streak", "30 Day Streak", "Iron Will", "Daily Grinder", "Unstoppable", "Routine Master", "Habit Builder", "Coding Everyday",
    "Sunrise Coder", "Midnight Coder", "Weekend Warrior", "Monthly Hero", "Legendary Routine",
    "printf Novice", "scanf User", "Loop Master", "Pointer Hunter", "Array Rookie", "String Tamer", "Struct Knight", "Function Crafter", "Recursion Entry", "Memory Guard",
    "Bug Slayer C", "Fast Compiler", "C Adept", "C Master", "C Legend",
    "Snake Born", "Print Wizard", "Variable Master", "If Else Lord", "Loop Walker", "List Keeper", "Dict Sage", "Function Ninja", "Class Builder", "Python Adept",
    "Python Master", "Python Legend", "Clean Syntax", "Zen Coder", "Import King",
    "Easy Hunter", "10 Easy Clears", "Medium Slayer", "Hard Survivor", "Hard Winner", "Nightmare Clear", "Elite Problem Solver", "No Fear", "Genius Path", "Impossible?",
    "Final Boss", "Mind Breaker", "Brainstormer", "One Shot Clear", "God Tier",
    "No Hint Clear", "Speed Runner", "First Try Clear", "Perfect Output", "Zero Error", "Combo x5", "Combo x10", "Accuracy 90%", "Accuracy 100%", "Smart Fixer",
    "Comeback King", "Retry Legend", "Fast Learner", "Problem Crusher", "Meta Brain",
    "Rich Player", "Millionaire", "Ranked Bronze", "Ranked Silver", "Ranked Gold", "Ranked Platinum", "Ranked Diamond", "Ranked Master", "Ranked Legend", "Top 10 Server",
    "Rank #1", "Hidden One", "Easter Egg Hunter", "Developer Favorite", "The Chosen Coder",
]

ACHIEVEMENTS = [{"id": idx + 1, "name": name} for idx, name in enumerate(ACHIEVEMENT_NAMES)]


def _has(owned: list[str], name: str) -> bool:
    return name in owned


def _try_unlock(owned: list[str], name: str, unlocked: list[str], badges: list[str]) -> None:
    if not _has(owned, name):
        owned.append(name)
        unlocked.append(name)
        badges.append(name)


def evaluate_achievements(user_data: dict[str, Any], context: dict[str, Any]) -> list[str]:
    """ประเมิน achievement จาก state ผู้ใช้และ context ของเหตุการณ์ล่าสุด"""

    unlocked: list[str] = []
    owned = user_data.setdefault("achievements", [])
    badges = user_data.setdefault("badges", [])

    completed_count = len(user_data.get("completed_tasks", {}))
    attempted = int(user_data.get("attempted", 0))
    correct = int(user_data.get("correct", 0))
    coins = int(user_data.get("coins", 0))
    streak = int(user_data.get("login", {}).get("consecutive_days", 0))
    combo = int(user_data.get("combo_count", 0))
    rank = str(user_data.get("rank", "Bronze"))
    accuracy = (correct / max(1, attempted)) * 100

    if user_data.get("stats", {}).get("first_submission_done"):
        _try_unlock(owned, "First Step", unlocked, badges)
        _try_unlock(owned, "New Challenger", unlocked, badges)
    if completed_count >= 1:
        _try_unlock(owned, "Hello World", unlocked, badges)
        _try_unlock(owned, "Learning Begins", unlocked, badges)
    if completed_count >= 3:
        _try_unlock(owned, "Rookie Coder", unlocked, badges)
    if len(user_data.get("viewed_chapters", [])) >= 5:
        _try_unlock(owned, "Explorer", unlocked, badges)
    if int(user_data.get("used_hint_count", 0)) >= 1:
        _try_unlock(owned, "Curious Mind", unlocked, badges)
    if user_data.get("stats", {}).get("first_fail_done"):
        _try_unlock(owned, "Try Again", unlocked, badges)
    if int(user_data.get("stats", {}).get("retry_after_fail", 0)) >= 1:
        _try_unlock(owned, "Never Quit", unlocked, badges)

    if streak >= 3:
        _try_unlock(owned, "3 Day Streak", unlocked, badges)
    if streak >= 7:
        _try_unlock(owned, "7 Day Streak", unlocked, badges)
    if streak >= 14:
        _try_unlock(owned, "14 Day Streak", unlocked, badges)
    if streak >= 30:
        _try_unlock(owned, "30 Day Streak", unlocked, badges)

    c_clear = int(user_data.get("languages_cleared", {}).get("c", 0))
    py_clear = int(user_data.get("languages_cleared", {}).get("python", 0))
    if c_clear >= 1:
        _try_unlock(owned, "printf Novice", unlocked, badges)
    if c_clear >= 5:
        _try_unlock(owned, "C Adept", unlocked, badges)
    if c_clear >= 10:
        _try_unlock(owned, "C Master", unlocked, badges)
    if c_clear >= 20:
        _try_unlock(owned, "C Legend", unlocked, badges)
    if py_clear >= 1:
        _try_unlock(owned, "Snake Born", unlocked, badges)
    if py_clear >= 5:
        _try_unlock(owned, "Python Adept", unlocked, badges)
    if py_clear >= 10:
        _try_unlock(owned, "Python Master", unlocked, badges)
    if py_clear >= 20:
        _try_unlock(owned, "Python Legend", unlocked, badges)

    easy_clear = int(user_data.get("difficulty_clears", {}).get("easy", 0))
    medium_clear = int(user_data.get("difficulty_clears", {}).get("medium", 0))
    hard_clear = int(user_data.get("difficulty_clears", {}).get("hard", 0))
    if easy_clear >= 1:
        _try_unlock(owned, "Easy Hunter", unlocked, badges)
    if easy_clear >= 10:
        _try_unlock(owned, "10 Easy Clears", unlocked, badges)
    if medium_clear >= 1:
        _try_unlock(owned, "Medium Slayer", unlocked, badges)
    if hard_clear >= 1:
        _try_unlock(owned, "Hard Survivor", unlocked, badges)
    if hard_clear >= 3:
        _try_unlock(owned, "Hard Winner", unlocked, badges)

    if int(user_data.get("stats", {}).get("no_hint_clear", 0)) >= 1:
        _try_unlock(owned, "No Hint Clear", unlocked, badges)
    if int(user_data.get("stats", {}).get("first_try_clear", 0)) >= 1:
        _try_unlock(owned, "First Try Clear", unlocked, badges)
    if int(user_data.get("stats", {}).get("perfect_output", 0)) >= 1:
        _try_unlock(owned, "Perfect Output", unlocked, badges)
    if combo >= 5:
        _try_unlock(owned, "Combo x5", unlocked, badges)
    if combo >= 10:
        _try_unlock(owned, "Combo x10", unlocked, badges)
    if accuracy >= 90:
        _try_unlock(owned, "Accuracy 90%", unlocked, badges)
    if accuracy >= 100 and attempted >= 3:
        _try_unlock(owned, "Accuracy 100%", unlocked, badges)

    if coins >= 1000:
        _try_unlock(owned, "Rich Player", unlocked, badges)
    if coins >= 10000:
        _try_unlock(owned, "Millionaire", unlocked, badges)

    rank_map = {
        "Bronze": "Ranked Bronze",
        "Silver": "Ranked Silver",
        "Gold": "Ranked Gold",
        "Platinum": "Ranked Platinum",
        "Diamond": "Ranked Diamond",
        "Master": "Ranked Master",
        "Legend": "Ranked Legend",
        "Grandmaster": "Ranked Master",
    }
    if rank in rank_map:
        _try_unlock(owned, rank_map[rank], unlocked, badges)

    if context.get("event") == "weekly_jackpot":
        _try_unlock(owned, "The Chosen Coder", unlocked, badges)
    if context.get("event") == "easter_egg":
        _try_unlock(owned, "Easter Egg Hunter", unlocked, badges)

    return unlocked
