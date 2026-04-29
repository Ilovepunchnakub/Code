"""ระบบ EXP จากการแชท"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import discord
from discord.ext import commands

from utils.database import UserStore


class ChatExpCog(commands.Cog):
    CHAT_EXP_CONFIG = {"min_length": 6, "cooldown_seconds": 30, "exp_per_message": (3, 8)}

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.user_store = UserStore(base / "users.json")
        self.cooldowns: dict[int, datetime] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        content = (message.content or "").strip()
        if content.startswith("/") or content.startswith("!") or len(content) < self.CHAT_EXP_CONFIG["min_length"]:
            return

        now = datetime.utcnow()
        last = self.cooldowns.get(message.author.id)
        if last and (now - last) < timedelta(seconds=self.CHAT_EXP_CONFIG["cooldown_seconds"]):
            return

        self.cooldowns[message.author.id] = now
        user = self.user_store.ensure_user(message.author.id, message.author.display_name)
        gain = random.randint(*self.CHAT_EXP_CONFIG["exp_per_message"])
        user["chat_exp"] = int(user.get("chat_exp", 0)) + gain
        user["exp"] = int(user.get("exp", 0)) + gain
        self.user_store.update_user(message.author.id, user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ChatExpCog(bot))
