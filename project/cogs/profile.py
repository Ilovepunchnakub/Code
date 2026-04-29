"""Cog สำหรับ /profile แบบการ์ดภาพ + embed"""

from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from utils.card_generator import RANK_THEMES, generate_profile_card
from utils.storage import get_user


class ProfileCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="profile", description="ดูโปรไฟล์ของคุณ")
    @app_commands.describe(member="ดูโปรไฟล์ของผู้อื่น (ไม่ระบุ = ของตัวเอง)")
    async def profile(self, interaction: discord.Interaction, member: discord.Member | None = None) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        target = member or interaction.user
        user_data = await get_user(str(target.id), target.display_name)
        card_bytes = await generate_profile_card(target, user_data)
        file = discord.File(card_bytes, filename="profile_card.png")
        embed = self.build_profile_embed(target, user_data)
        embed.set_image(url="attachment://profile_card.png")
        await interaction.followup.send(file=file, embed=embed, ephemeral=True)

    def build_profile_embed(self, user: discord.User, data: dict) -> discord.Embed:
        cleared = int(data.get("tasks_cleared", 0))
        attempted = int(data.get("tasks_attempted", 0))
        accuracy = (cleared / max(1, attempted)) * 100
        c_clear = int(data.get("c_cleared", 0))
        py_clear = int(data.get("python_cleared", 0))
        fav_lang = data.get("fav_lang") or ("C" if c_clear >= py_clear else "Python")
        rank = str(data.get("rank", "Bronze"))

        accent = RANK_THEMES.get(rank, RANK_THEMES["Bronze"])["accent"]
        color = discord.Color.from_rgb(accent[0], accent[1], accent[2])

        embed = discord.Embed(title=f"🧑 {user.display_name}", color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="💻 Coding", value=f"Lv.{data.get('coding_level', 1)} · {int(data.get('coding_exp', 0)):,} EXP\n🏆 {rank}", inline=True)
        embed.add_field(name="💬 Chat", value=f"Lv.{data.get('chat_level', 1)} · {int(data.get('chat_exp', 0)):,} EXP", inline=True)
        embed.add_field(name="💰 Economy", value=f"🪙 {int(data.get('coins', 0)):,} Coins\n🔥 {int(data.get('streak', 0))} วัน", inline=True)
        embed.add_field(name="📊 Statistics", value=f"✅ {cleared} Tasks\n🎯 Accuracy {accuracy:.1f}%\n❤️ Fav {fav_lang}", inline=True)

        ach = data.get("achievements", [])
        ach_text = " ".join(f"`{item}`" for item in ach[:8]) or "ยังไม่มี Achievement ลองทำโจทย์ดูนะ!"
        embed.add_field(name=f"🏅 Achievements ({len(ach)}/100)", value=ach_text, inline=False)
        embed.add_field(name="📅 ประวัติล่าสุด", value=self.format_history_field(data.get("history", [])), inline=False)

        join_date = data.get("join_date") or "-"
        embed.set_footer(text=f"🤖 CodingBot | สมัครเมื่อ {join_date}")
        return embed

    def format_history_field(self, history: list[dict]) -> str:
        if not history:
            return "ยังไม่มีประวัติการส่งงาน"
        lines: list[str] = []
        now = datetime.now(timezone.utc)
        for item in list(history)[-3:][::-1]:
            ts = item.get("timestamp")
            rel = "เมื่อกี้"
            try:
                dt = datetime.fromisoformat(str(ts)).replace(tzinfo=timezone.utc)
                diff = now - dt
                if diff.days >= 1:
                    rel = "เมื่อวาน" if diff.days == 1 else f"{diff.days} วันที่แล้ว"
                else:
                    hours = int(diff.total_seconds() // 3600)
                    rel = "เมื่อกี้" if hours <= 0 else f"{hours} ชม.ที่แล้ว"
            except Exception:
                rel = "เมื่อกี้"
            mark = "✅" if item.get("passed", False) else "❌"
            exp = int(item.get("exp_gained", 0))
            lines.append(f"{mark} {item.get('task_title','-')} ({str(item.get('lang','-')).upper()}) · +{exp} EXP · {rel}")
        return "\n".join(lines)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
