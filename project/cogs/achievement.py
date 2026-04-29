"""คำสั่ง /achievement"""

from __future__ import annotations

from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import UserStore


class AchievementCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.user_store = UserStore(base / "users.json")

    @app_commands.command(name="achievement", description="ดูรายการ achievement")
    async def achievement(self, interaction: discord.Interaction) -> None:
        user = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        ach = user.get("achievements", [])
        embed = discord.Embed(
            title="🏅 Achievement ของคุณ",
            description="\n".join(f"• {a}" for a in ach[:60]) or "ยังไม่มี achievement",
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"ปลดล็อกแล้ว {len(ach)} รายการ")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AchievementCog(bot))
