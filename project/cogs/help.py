"""คำสั่ง /ช่วยเหลือ"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ช่วยเหลือ", description="ดูรายการคำสั่งทั้งหมด")
    async def help_th(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="🆘 ช่วยเหลือ", color=discord.Color.blue())
        embed.description = (
            "📚 /เรียน\n👤 /โปรไฟล์\n🏆 /อันดับ\n🎁 /รายวัน\n🏅 /ภารกิจ\n👑 /แอดมิน\n🆘 /ช่วยเหลือ"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
