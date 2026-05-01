"""Entry point สำหรับ Discord Bot ระบบ Interactive Courseware + RPG"""

from __future__ import annotations

import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import BOT_NAME, BOT_VERSION, load_settings
from utils.startup import ensure_runtime_ready


class CodingArenaBot(commands.Bot):
    """บอทหลักที่โหลด cog ทั้งหมดและ sync slash command"""

    def __init__(self, auto_sync_commands: bool = True) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.auto_sync_commands = auto_sync_commands

    async def setup_hook(self) -> None:
        """โหลด extension และซิงก์คำสั่งตอนเริ่มระบบ"""
        extensions = [
            "cogs.learn",
            "cogs.profile",
            "cogs.rank",
            "cogs.daily",
            "cogs.mission",
            "cogs.admin",
            "cogs.help",
            "cogs.chat_exp",
            "cogs.achievement",
        ]
        for extension in extensions:
            await self.load_extension(extension)

        if self.auto_sync_commands:
            await self.tree.sync()

    async def on_ready(self) -> None:
        """แจ้งสถานะเมื่อออนไลน์"""
        print(f"✅ {BOT_NAME} {BOT_VERSION} online as {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="📚 /เรียน | Coding Sudy"))


async def main() -> None:
    """โหลดคอนฟิกจาก ENV และสตาร์ทบอท"""
    load_dotenv()
    settings = load_settings()
    ensure_runtime_ready(settings.data_dir)

    print(f"🚀 เริ่มระบบในโหมด: {settings.app_env}")
    print(f"📁 data_dir: {settings.data_dir}")
    bot = CodingArenaBot(auto_sync_commands=settings.auto_sync_commands)
    await bot.start(settings.token)


if __name__ == "__main__":
    asyncio.run(main())
