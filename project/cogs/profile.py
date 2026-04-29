"""Cog สำหรับ /profile โปรไฟล์ผู้เล่น"""

from __future__ import annotations

from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from utils.database import UserStore
from utils.leveling import level_progress
from views.buttons import ProfileActionView, ThemeSelectView


class ProfileCog(commands.Cog):
    """แสดงโปรไฟล์เกมของผู้ใช้"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.user_store = UserStore(base / "users.json")

    def _progress_bar(self, current: int, total: int, length: int = 10) -> str:
        filled = int((current / max(1, total)) * length)
        return "[" + ("█" * filled) + ("░" * (length - filled)) + "]"

    @app_commands.command(name="profile", description="ดูโปรไฟล์ผู้เล่น")
    async def profile(self, interaction: discord.Interaction) -> None:
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        level, current_exp, required_exp = level_progress(int(user_data.get("exp", 0)))
        accuracy = (user_data.get("correct", 0) / max(1, user_data.get("attempted", 1))) * 100

        theme = user_data.get("inventory", {}).get("profile_theme", "Blue Neon")
        theme_color = {
            "Blue Neon": discord.Color.dark_blue(),
            "Gold Royal": discord.Color.gold(),
            "Dark Hacker": discord.Color.dark_grey(),
            "Purple Mythic": discord.Color.purple(),
            "Crimson Dragon": discord.Color.red(),
        }.get(theme, discord.Color.dark_blue())

        embed = discord.Embed(
            title="╔══════════════════╗\n⚔️ PLAYER PROFILE\n╚══════════════════╝",
            description=(
                f"👤 Name: {interaction.user.display_name}\n"
                f"🏆 Rank: {user_data.get('rank', 'Bronze')}\n"
                f"✨ Level: {level}\n"
                f"🔥 EXP: {current_exp} / {required_exp}\n"
                f"💰 Coins: {user_data.get('coins', 0):,}\n"
                f"📚 Cleared: {len(user_data.get('completed_tasks', {}))} Tasks\n"
                f"🎯 Accuracy: {accuracy:.1f}%\n"
                f"🔥 Streak: {user_data.get('login', {}).get('consecutive_days', 0)} Days\n"
                f"🏅 Badges: {len(user_data.get('badges', []))}\n"
                f"{self._progress_bar(current_exp, required_exp)} Progress"
            ),
            color=theme_color,
        )
        embed.set_footer(text=f"Theme: {theme}")

        async def on_theme(sub_interaction: discord.Interaction) -> None:
            async def pick_theme(theme_name: str, target_interaction: discord.Interaction) -> None:
                current = self.user_store.ensure_user(target_interaction.user.id, target_interaction.user.display_name)
                current.setdefault("inventory", {})["profile_theme"] = theme_name
                self.user_store.update_user(target_interaction.user.id, current)
                await target_interaction.response.send_message(f"✅ เปลี่ยนธีมเป็น {theme_name} แล้ว", ephemeral=True)

            view = ThemeSelectView(
                owner_id=sub_interaction.user.id,
                on_pick=lambda i, theme_name: pick_theme(theme_name, i),
            )
            await sub_interaction.response.send_message("🎨 เลือกธีมโปรไฟล์", view=view, ephemeral=True)

        async def on_badges(sub_interaction: discord.Interaction) -> None:
            badges = user_data.get("badges", [])
            await sub_interaction.response.send_message(
                embed=discord.Embed(
                    title="🏅 Badges",
                    description="\n".join(f"• {badge}" for badge in badges[:40]) or "ยังไม่มี Badge",
                    color=discord.Color.gold(),
                ),
                ephemeral=True,
            )

        async def on_stats(sub_interaction: discord.Interaction) -> None:
            stats = user_data.get("stats", {})
            stats_embed = discord.Embed(title="📈 สถิติผู้เล่น", color=discord.Color.blurple())
            stats_embed.add_field(name="First Try Clear", value=str(stats.get("first_try_clear", 0)), inline=True)
            stats_embed.add_field(name="No Hint Clear", value=str(stats.get("no_hint_clear", 0)), inline=True)
            stats_embed.add_field(name="Perfect Output", value=str(stats.get("perfect_output", 0)), inline=True)
            stats_embed.add_field(name="Achievements", value=f"{len(user_data.get('achievements', []))}/100", inline=True)
            await sub_interaction.response.send_message(embed=stats_embed, ephemeral=True)

        async def on_rank(sub_interaction: discord.Interaction) -> None:
            await sub_interaction.response.send_message("🏆 ใช้ /rank เพื่อดูอันดับล่าสุด", ephemeral=True)

        view = ProfileActionView(
            owner_id=interaction.user.id,
            on_theme=on_theme,
            on_badges=on_badges,
            on_stats=on_stats,
            on_rank=on_rank,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProfileCog(bot))
