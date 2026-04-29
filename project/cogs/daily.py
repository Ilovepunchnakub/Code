"""คำสั่ง /daily"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import UserStore

DAILY_REWARDS = {
    1: {"coins": 20, "exp": 0, "special": None},
    2: {"coins": 30, "exp": 0, "special": None},
    3: {"coins": 50, "exp": 0, "special": None},
    4: {"coins": 0, "exp": 0, "special": "x2_exp_1hour"},
    5: {"coins": 100, "exp": 0, "special": None},
    6: {"coins": 0, "exp": 0, "special": "mystery_chest"},
    7: {"coins": 300, "exp": 100, "special": "jackpot"},
}


class DailyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.user_store = UserStore(base / "users.json")

    @app_commands.command(name="daily", description="รับรางวัลรายวัน")
    async def daily(self, interaction: discord.Interaction) -> None:
        user = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        today = datetime.utcnow().date().isoformat()
        daily = user.setdefault("daily", {"date": "", "week_day": 0})
        if daily.get("date") == today:
            await interaction.response.send_message("✅ วันนี้รับรางวัลแล้ว", ephemeral=True)
            return
        week_day = (int(daily.get("week_day", 0)) % 7) + 1
        reward = DAILY_REWARDS[week_day]
        user["coins"] = int(user.get("coins", 0)) + int(reward["coins"])
        user["exp"] = int(user.get("exp", 0)) + int(reward["exp"])
        daily["date"] = today
        daily["week_day"] = week_day
        self.user_store.update_user(interaction.user.id, user)
        await interaction.response.send_message(
            f"🎁 รับรางวัล Day {week_day} สำเร็จ: +{reward['coins']} Coins, +{reward['exp']} EXP", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DailyCog(bot))
