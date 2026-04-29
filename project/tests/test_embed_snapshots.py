from __future__ import annotations

from cogs.admin import AdminCog
from cogs.learn import LearnCog


def test_adminpanel_embed_snapshot() -> None:
    embed = AdminCog(bot=object()).build_admin_panel_embed().to_dict()
    assert embed["title"] == "👑 Admin Panel"
    assert "เกม AAA" in embed["description"]


def test_learn_embed_snapshot() -> None:
    embed = LearnCog(bot=object()).build_learn_start_embed().to_dict()
    assert embed["title"] == "⚔️ Coding Arena"
    assert "เลือกภาษา" in embed["description"]


def test_daily_embed_snapshot() -> None:
    embed = LearnCog(bot=object()).build_daily_reward_embed("Day 1", "", 3).to_dict()
    assert embed["title"] == "🎁 Daily Reward"
    assert "Streak: 3" in embed["description"]
