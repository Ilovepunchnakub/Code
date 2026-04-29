"""ตัวช่วยสร้าง Embed มาตรฐาน"""

from __future__ import annotations

import discord

from config import BOT_NAME, BOT_VERSION, COLORS


def panel(title: str, description: str, tone: str = "main") -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=COLORS.get(tone, COLORS["main"]))
    embed.set_footer(text=f"{BOT_NAME} • {BOT_VERSION}")
    return embed
