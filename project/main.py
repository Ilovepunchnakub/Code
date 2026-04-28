"""Entry point สำหรับ Discord Bot ระบบ Interactive Courseware + RPG"""

from __future__ import annotations

import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv


class CodingArenaBot(commands.Bot):
    """บอทหลักที่โหลด cog ทั้งหมดและ sync slash command"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        """โหลด extension และซิงก์คำสั่งตอนเริ่มระบบ"""

        for extension in ["cogs.learn", "cogs.profile", "cogs.rank", "cogs.admin"]:
            await self.load_extension(extension)
        await self.tree.sync()

    async def on_ready(self) -> None:
        """แจ้งสถานะเมื่อออนไลน์"""

        print(f"✅ Bot online as {self.user} (ID: {self.user.id})")


async def main() -> None:
    """โหลด token จาก ENV และสตาร์ทบอท"""

    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("กรุณาตั้งค่า DISCORD_TOKEN ก่อนรัน")

    bot = CodingArenaBot()
    await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
