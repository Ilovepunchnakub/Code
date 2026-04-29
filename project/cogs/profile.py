"""คำสั่ง /profile แบบการ์ดภาพ + embed"""

from __future__ import annotations

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from utils.card_generator import generate_profile_card
from utils.rewards import get_level, get_rank
from utils.storage import get_user


class ProfileCog(commands.Cog):
    """แสดงโปรไฟล์เกมของผู้ใช้"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="profile", description="ดูโปรไฟล์ของคุณ")
    @app_commands.describe(member="ดูโปรไฟล์ของผู้อื่น")
    async def profile(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        await interaction.response.defer(ephemeral=True)
        target = member or interaction.user
        user_data = await get_user(str(target.id), target.display_name)

        coding_exp = int(user_data.get("coding_exp", user_data.get("exp", 0)))
        user_data["coding_level"] = get_level(coding_exp)
        user_data["rank"] = get_rank(coding_exp)

        card_bytes = await generate_profile_card(target, user_data)
        file = discord.File(card_bytes, filename="profile_card.png")

        embed = self.build_profile_embed(target, user_data)
        embed.set_image(url="attachment://profile_card.png")
        await interaction.followup.send(file=file, embed=embed, ephemeral=True)

    def build_profile_embed(self, user: discord.User, data: dict) -> discord.Embed:
        rank = str(data.get("rank", "Bronze"))
        coding_exp = int(data.get("coding_exp", data.get("exp", 0)))
        coding_level = int(data.get("coding_level", get_level(coding_exp)))
        chat_exp = int(data.get("chat_exp", 0))
        chat_level = int(data.get("chat_level", max(1, chat_exp // 100 + 1)))
        attempted = int(data.get("tasks_attempted", data.get("attempted", 0)))
        cleared = int(data.get("tasks_cleared", len(data.get("completed_tasks", {}))))
        accuracy = (cleared / max(1, attempted)) * 100
        fav_lang = data.get("fav_lang") or ("C" if int(data.get("c_cleared", 0)) >= int(data.get("python_cleared", 0)) else "Python")

        embed = discord.Embed(title=f"🧑 {user.display_name}", color=self.get_rank_color(rank), timestamp=datetime.utcnow())
        embed.add_field(name="💻 Coding", value=f"Lv.{coding_level} · {coding_exp:,} EXP\n🏆 {rank}", inline=True)
        embed.add_field(name="💬 Chat", value=f"Lv.{chat_level} · {chat_exp:,} EXP", inline=True)
        embed.add_field(name="💰 Economy", value=f"🪙 {int(data.get('coins', 0)):,}\n🔥 {int(data.get('streak', 0))} วัน", inline=True)
        embed.add_field(name="📊 Statistics", value=f"✅ {cleared}\n🎯 {accuracy:.1f}%\n❤️ {fav_lang}", inline=True)

        ach = data.get("achievements", [])
        embed.add_field(name=f"🏅 Achievements ({len(ach)}/100)", value="  ".join(ach[:8]) or "ยังไม่มี Achievement ลองทำโจทย์ดูนะ!", inline=False)
        embed.add_field(name="📅 ประวัติล่าสุด", value=self.format_history_field(data.get("history", [])), inline=False)
        join_date = data.get("join_date") or "-"
        embed.set_footer(text=f"🤖 CodingBot | สมัครเมื่อ {join_date}")
        return embed

    def format_history_field(self, history: list) -> str:
        if not history:
            return "ยังไม่มีประวัติการทำโจทย์"
        lines = []
        for item in list(reversed(history[-3:])):
            passed = "✅" if item.get("passed") else "❌"
            title = item.get("task_title", "Unknown")
            lang = str(item.get("lang", "-")).upper()
            exp = int(item.get("exp_gained", 0))
            lines.append(f"{passed} {title} ({lang}) · +{exp} EXP")
        return "\n".join(lines)

    def get_rank_color(self, rank: str) -> int:
        rank_colors = {
            "Bronze": 0xCD7F32,
            "Silver": 0xC0C0C0,
            "Gold": 0xFFD700,
            "Platinum": 0x00CED1,
            "Diamond": 0x00BFFF,
            "Master": 0x9400D3,
            "Legend": 0xFF4500,
        }
        return rank_colors.get(rank, 0x1A237E)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
