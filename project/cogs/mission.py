"""คำสั่ง /ภารกิจ"""

from __future__ import annotations

from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import UserStore
from utils.missions import reset_daily_missions, reset_weekly_missions


class MissionCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.user_store = UserStore(base / "users.json")

    @app_commands.command(name="ภารกิจ", description="ดูภารกิจรายวันและรายสัปดาห์")
    async def mission(self, interaction: discord.Interaction) -> None:
        user = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        reset_daily_missions(user)
        reset_weekly_missions(user)
        self.user_store.update_user(interaction.user.id, user)
        d = user.get("daily_missions", {})
        w = user.get("weekly_missions", {})
        embed = discord.Embed(title="🏅 ภารกิจ", color=discord.Color.gold())
        embed.add_field(name="รายวัน", value=f"📝 ผ่านโจทย์ {d.get('tasks_done',0)}/3\n💬 แชท {d.get('chat_done',0)}/10\n📅 รับรายวัน {'✅' if d.get('daily_claimed') else '❌'}", inline=False)
        embed.add_field(name="รายสัปดาห์", value=f"📚 ผ่านโจทย์ {w.get('tasks_done',0)}/20", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MissionCog(bot))
