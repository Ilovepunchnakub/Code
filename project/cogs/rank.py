"""Cog สำหรับ /rank ตารางคะแนน"""

from __future__ import annotations

import time
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import UserStore
from views.buttons import RankCategoryView


class RankCog(commands.Cog):
    """คำสั่งดูอันดับผู้เล่น"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.user_store = UserStore(base / "users.json")
        self._cache: dict[str, tuple[float, discord.Embed]] = {}

    def _render_rank(self, category: str) -> discord.Embed:
        now = time.time()
        cached = self._cache.get(category)
        if cached and now - cached[0] <= 45:
            return cached[1]

        rows = [v for k, v in self.user_store.load().items() if k != "schema_version"]

        if category == "python":
            sorted_users = sorted(rows, key=lambda x: x.get("languages_cleared", {}).get("python", 0), reverse=True)
            title = "🏆 TOP PLAYERS - Python"
            line_fn = lambda u: f"Python Clear {u.get('languages_cleared', {}).get('python', 0)}"
        elif category == "c":
            sorted_users = sorted(rows, key=lambda x: x.get("languages_cleared", {}).get("c", 0), reverse=True)
            title = "🏆 TOP PLAYERS - C Language"
            line_fn = lambda u: f"C Clear {u.get('languages_cleared', {}).get('c', 0)}"
        elif category == "streak":
            sorted_users = sorted(rows, key=lambda x: x.get("login", {}).get("consecutive_days", 0), reverse=True)
            title = "🏆 TOP PLAYERS - Streak"
            line_fn = lambda u: f"Streak {u.get('login', {}).get('consecutive_days', 0)} วัน"
        elif category == "coins":
            sorted_users = sorted(rows, key=lambda x: x.get("coins", 0), reverse=True)
            title = "🏆 TOP PLAYERS - Coins"
            line_fn = lambda u: f"Coins {u.get('coins', 0):,}"
        elif category == "accuracy":
            sorted_users = sorted(rows, key=lambda x: ((x.get("correct", 0) / max(1, x.get("attempted", 1))) * 100), reverse=True)
            title = "🏆 TOP PLAYERS - Accuracy"
            line_fn = lambda u: f"Acc {(u.get('correct', 0) / max(1, u.get('attempted', 1)) * 100):.1f}%"
        else:
            sorted_users = sorted(rows, key=lambda x: (x.get("exp", 0), x.get("level", 1)), reverse=True)
            title = "🏆 TOP PLAYERS"
            line_fn = lambda u: f"Lv{u.get('level', 1)} | EXP {u.get('exp', 0)}"

        lines = [f"#{index} {user.get('name', 'Unknown'):<12} {line_fn(user)}" for index, user in enumerate(list(sorted_users)[:10], start=1)]
        embed = discord.Embed(title=title, description="\n".join(lines) or "ยังไม่มีผู้เล่น", color=discord.Color.purple())
        self._cache[category] = (now, embed)
        return embed

    @app_commands.command(name="rank", description="ดูอันดับผู้เล่นสูงสุด")
    async def rank(self, interaction: discord.Interaction) -> None:
        embed = self._render_rank("all")

        async def on_pick(sub_interaction: discord.Interaction, category: str) -> None:
            await sub_interaction.response.edit_message(embed=self._render_rank(category), view=view)

        view = RankCategoryView(on_pick=on_pick)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RankCog(bot))
