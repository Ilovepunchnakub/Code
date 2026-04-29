"""Cog หลักของระบบเรียน/ส่งงาน/เดลี่/ร้านค้า"""

from __future__ import annotations

import random
from datetime import date
from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from utils.achievements import evaluate_achievements
from utils.checker import JudgeQueueWorker, precheck_keywords
from utils.database import AssignmentStore, UserStore
from utils.leveling import apply_rewards, level_progress
from views.buttons import ChapterView, LanguageView, QuestCardView, ShopView, TaskView
from views.modals import SubmitCodeModal


class LearnCog(commands.Cog):
    """รวมคำสั่งเรียนแบบเกม RPG"""

    DAILY_TABLE = {
        1: {"coins": 20, "exp": 10, "text": "Day 1: +20 Coins +10 EXP"},
        2: {"coins": 30, "exp": 0, "text": "Day 2: +30 Coins"},
        3: {"coins": 50, "exp": 20, "text": "Day 3: +50 Coins +20 EXP"},
        4: {"coins": 0, "exp": 0, "text": "Day 4: EXP Boost x2 1 ชม.", "boost": "x2_1h"},
        5: {"coins": 100, "exp": 0, "text": "Day 5: +100 Coins"},
        6: {"coins": 0, "exp": 0, "text": "Day 6: Random Chest", "chest": True},
        7: {"coins": 0, "exp": 0, "text": "Day 7: 🔥 Weekly Jackpot", "jackpot": True},
    }

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.assignment_store = AssignmentStore(base / "assignments.json")
        self.user_store = UserStore(base / "users.json")
        self.judge_queue = JudgeQueueWorker(worker_count=2)

    def _main_embed(self, title: str, description: str) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=discord.Color.dark_blue())

    def _register_login(self, user_data: dict[str, Any]) -> None:
        """อัปเดต login streak เมื่อ user เรียกใช้งานคำสั่งหลัก"""

        today = date.today().isoformat()
        login = user_data.setdefault("login", {"last_date": "", "consecutive_days": 0, "total_days": 0})
        if login.get("last_date") == today:
            return

        save_streak = int(user_data.get("inventory", {}).get("save_streak", 0))
        if login.get("last_date"):
            prev = date.fromisoformat(login["last_date"])
            gap = (date.fromisoformat(today) - prev).days
            if gap == 1:
                login["consecutive_days"] = int(login.get("consecutive_days", 0)) + 1
            elif gap > 1:
                if save_streak > 0:
                    user_data["inventory"]["save_streak"] = save_streak - 1
                else:
                    login["consecutive_days"] = 1
        else:
            login["consecutive_days"] = 1

        login["total_days"] = int(login.get("total_days", 0)) + 1
        login["last_date"] = today


    def build_learn_start_embed(self) -> discord.Embed:
        return self._main_embed("⚔️ Coding Arena", "📘 **เลือกภาษา**\n> เลือกภาษาเพื่อเริ่มเส้นทางนักพัฒนา")

    def build_daily_reward_embed(self, reward_text: str, jackpot_text: str, streak: int) -> discord.Embed:
        return discord.Embed(
            title="🎁 Daily Reward",
            description=f"{reward_text}{jackpot_text}\n🔥 Streak: {streak} วัน",
            color=discord.Color.green(),
        )

    def _announce_new_achievements(self, unlocked: list[str]) -> discord.Embed | None:
        if not unlocked:
            return None
        return discord.Embed(
            title="🏅 ปลดล็อก Achievement ใหม่!",
            description="\n".join(f"• {name}" for name in unlocked[:8]),
            color=discord.Color.purple(),
        )

    @app_commands.command(name="learn", description="เริ่มเรียนเขียนโปรแกรมแบบ Interactive")
    async def learn(self, interaction: discord.Interaction) -> None:
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        self._register_login(user_data)
        self.user_store.update_user(interaction.user.id, user_data)

        embed = self._main_embed("⚔️ Coding Arena", "📘 **เลือกภาษา**\n> เลือกภาษาเพื่อเริ่มเส้นทางนักพัฒนา")

        async def on_pick_language(sub_interaction: discord.Interaction, language: str) -> None:
            await self._show_chapters(sub_interaction, language)

        view = LanguageView(owner_id=interaction.user.id, on_pick=on_pick_language)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _show_chapters(self, interaction: discord.Interaction, language: str) -> None:
        assignments = self.assignment_store.load()
        chapters = assignments.get(language, {})
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        user_level = int(user_data.get("level", 1))

        unlocked = {k: v for k, v in chapters.items() if int(v.get("locked_level", 1)) <= user_level}
        if not unlocked:
            await interaction.response.send_message("⚠️ ยังไม่มีบทเรียนที่ปลดล็อกในตอนนี้", ephemeral=True)
            return

        viewed = set(user_data.get("viewed_chapters", []))
        viewed.update(f"{language}:{chapter_key}" for chapter_key in unlocked.keys())
        user_data["viewed_chapters"] = list(viewed)
        newly = evaluate_achievements(user_data, {"event": "view_chapter"})
        self.user_store.update_user(interaction.user.id, user_data)

        embed = self._main_embed("📘 เลือกบทเรียน", "> กรุณาเลือกบทที่ต้องการเรียน")
        bonus = self._announce_new_achievements(newly)
        if bonus:
            embed.add_field(name="✨ Achievement", value="ปลดล็อกใหม่! ดูแจ้งเตือนหลังเลือกบท", inline=False)

        async def on_pick_chapter(sub_interaction: discord.Interaction, chapter_key: str) -> None:
            chapter = unlocked[chapter_key]
            tasks = chapter.get("tasks", [])
            await self._show_tasks(sub_interaction, language, chapter_key, chapter, tasks)

        view = ChapterView(owner_id=interaction.user.id, chapters=unlocked, on_pick=on_pick_chapter)
        await interaction.response.edit_message(embed=embed, view=view)
        if bonus:
            await interaction.followup.send(embed=bonus, ephemeral=True)

    async def _show_tasks(
        self,
        interaction: discord.Interaction,
        language: str,
        chapter_key: str,
        chapter: dict[str, Any],
        tasks: list[dict[str, Any]],
    ) -> None:
        embed = self._main_embed(f"🧠 {chapter.get('title', 'บทเรียน')}", "เลือกโจทย์ที่ต้องการทำจากเมนูด้านล่าง")

        async def on_pick_task(sub_interaction: discord.Interaction, task: dict[str, Any]) -> None:
            await self._show_task_card(sub_interaction, language, chapter_key, chapter, task, tasks)

        view = TaskView(owner_id=interaction.user.id, tasks=tasks, on_pick=on_pick_task)
        await interaction.response.edit_message(embed=embed, view=view)

    async def _show_task_card(
        self,
        interaction: discord.Interaction,
        language: str,
        chapter_key: str,
        chapter: dict[str, Any],
        task: dict[str, Any],
        tasks: list[dict[str, Any]],
    ) -> None:
        embed = self._main_embed(f"📜 {task.get('title')}", task.get("description", "ไม่มีคำอธิบาย"))
        embed.add_field(name="🎯 เป้าหมาย", value="ให้ผ่านทุก testcase", inline=False)
        embed.add_field(name="⭐ EXP Reward", value=str(task.get("exp", 20)), inline=True)
        embed.add_field(name="💰 Coins Reward", value=str(task.get("coins", 5)), inline=True)
        embed.add_field(name="📈 Difficulty", value=str(task.get("difficulty", "easy")).upper(), inline=True)
        embed.add_field(name="📚 Hint", value=task.get("hint", "-"), inline=False)

        async def on_submit(sub_interaction: discord.Interaction) -> None:
            await sub_interaction.response.send_modal(
                SubmitCodeModal(
                    on_submit_handler=lambda modal_interaction, code: self._on_submit_code(
                        modal_interaction, language, chapter_key, task, code
                    )
                )
            )

        async def on_hint(sub_interaction: discord.Interaction) -> None:
            user_data = self.user_store.ensure_user(sub_interaction.user.id, sub_interaction.user.display_name)
            user_data["used_hint_count"] = int(user_data.get("used_hint_count", 0)) + 1
            unlocked = evaluate_achievements(user_data, {"event": "hint"})
            self.user_store.update_user(sub_interaction.user.id, user_data)
            await sub_interaction.response.send_message(
                embed=discord.Embed(title="💡 Hint", description=task.get("hint", "ยังไม่มี Hint"), color=discord.Color.gold()),
                ephemeral=True,
            )
            badge = self._announce_new_achievements(unlocked)
            if badge:
                await sub_interaction.followup.send(embed=badge, ephemeral=True)

        async def on_example(sub_interaction: discord.Interaction) -> None:
            await sub_interaction.response.send_message(
                embed=discord.Embed(
                    title="📖 ตัวอย่างโค้ด",
                    description=f"```\n{task.get('example_code', '// ยังไม่มีตัวอย่าง')}\n```",
                    color=discord.Color.blurple(),
                ),
                ephemeral=True,
            )

        async def on_back(sub_interaction: discord.Interaction) -> None:
            await self._show_tasks(sub_interaction, language, chapter_key, chapter, tasks)

        view = QuestCardView(owner_id=interaction.user.id, on_submit=on_submit, on_hint=on_hint, on_example=on_example, on_back=on_back)
        await interaction.response.edit_message(embed=embed, view=view)

    async def _on_submit_code(
        self,
        interaction: discord.Interaction,
        language: str,
        chapter_key: str,
        task: dict[str, Any],
        code: str,
    ) -> None:
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)

        if not user_data.get("stats", {}).get("first_submission_done"):
            user_data.setdefault("stats", {})["first_submission_done"] = True

        ok, warning = precheck_keywords(code, task)
        if not ok:
            await interaction.response.send_message(
                embed=discord.Embed(title="⚠️ ตรวจพบข้อควรแก้ไข", description=warning, color=discord.Color.gold()),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.followup.send(
            embed=discord.Embed(title="⏳ กำลังตรวจคำตอบ", description="ระบบกำลังรันโค้ดผ่าน Judge...", color=discord.Color.gold()),
            ephemeral=True,
        )

        result = await self.judge_queue.submit(language=language, code=code, task=task)

        user_data["attempted"] = int(user_data.get("attempted", 0)) + 1
        task_key = f"{language}:{chapter_key}:{task.get('id')}"
        first_clear = task_key not in user_data.get("completed_tasks", {})

        if result.passed:
            user_data["correct"] = int(user_data.get("correct", 0)) + 1
            user_data.setdefault("completed_tasks", {})[task_key] = {
                "title": task.get("title"),
                "difficulty": task.get("difficulty", "easy"),
            }
            lang_stat = user_data.setdefault("languages_cleared", {"python": 0, "c": 0})
            lang_stat[language] = int(lang_stat.get(language, 0)) + 1
            diff = str(task.get("difficulty", "easy")).lower()
            diff_stat = user_data.setdefault("difficulty_clears", {"easy": 0, "medium": 0, "hard": 0})
            diff_stat[diff] = int(diff_stat.get(diff, 0)) + 1

            if first_clear:
                user_data.setdefault("stats", {})["first_try_clear"] = int(user_data.get("stats", {}).get("first_try_clear", 0)) + 1

            if int(user_data.get("used_hint_count", 0)) == 0:
                user_data.setdefault("stats", {})["no_hint_clear"] = int(user_data.get("stats", {}).get("no_hint_clear", 0)) + 1

            if result.verdict == "Accepted":
                user_data.setdefault("stats", {})["perfect_output"] = int(user_data.get("stats", {}).get("perfect_output", 0)) + 1

            reward = apply_rewards(user_data, task, first_clear=first_clear)
            reward_note = (
                f"\n\n🎁 ได้รับ EXP +{reward['exp']} | Coins +{reward['coins']}"
                f"\n🔥 Combo: {reward['combo']} | Multiplier x{reward['multiplier']:.2f}"
            )
        else:
            user_data["combo_count"] = 0
            user_data["wrong_submissions"] = int(user_data.get("wrong_submissions", 0)) + 1
            if not user_data.get("stats", {}).get("first_fail_done"):
                user_data.setdefault("stats", {})["first_fail_done"] = True
            reward_note = ""
            if task_key in user_data.get("completed_tasks", {}):
                user_data.setdefault("stats", {})["retry_after_fail"] = int(user_data.get("stats", {}).get("retry_after_fail", 0)) + 1

        level, current_exp, required_exp = level_progress(int(user_data.get("exp", 0)))
        user_data["level"] = level

        newly_unlocked = evaluate_achievements(user_data, {"event": "submit"})
        self.user_store.update_user(interaction.user.id, user_data)

        color = discord.Color.green() if result.passed else discord.Color.red()
        status = "✅ ผ่าน" if result.passed else f"❌ {result.verdict}"
        embed = discord.Embed(title=status, color=color)
        testcase_lines = [
            f"Testcase #{case.index} {'✅' if case.passed else '❌'} | Expected: `{case.expected}` | Got: `{case.got or '-'}`"
            for case in result.testcase_results
        ]
        embed.add_field(name="ผลการทดสอบ", value="\n".join(testcase_lines) or "-", inline=False)
        embed.add_field(name="Expected Output", value=f"```\n{result.expected_output}\n```", inline=False)
        embed.add_field(name="Your Output", value=f"```\n{result.your_output}\n```", inline=False)
        embed.add_field(name="Error Message", value=f"```\n{result.error_message}\n```", inline=False)
        if result.passed:
            embed.add_field(name="⚔️ Progress", value=f"Level {level} | EXP {current_exp}/{required_exp}{reward_note}", inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)
        achievement_embed = self._announce_new_achievements(newly_unlocked)
        if achievement_embed:
            await interaction.followup.send(embed=achievement_embed, ephemeral=True)

    @app_commands.command(name="progress", description="ดูความคืบหน้าและค่าเกมทั้งหมด")
    async def progress(self, interaction: discord.Interaction) -> None:
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        completed = user_data.get("completed_tasks", {})
        completed_text = "\n".join(f"• {k} - {v.get('title', '-') }" for k, v in list(completed.items())[:12])
        if not completed_text:
            completed_text = "ยังไม่มีงานที่ผ่าน เริ่มได้ด้วย /learn ✨"

        level, current_exp, required_exp = level_progress(int(user_data.get("exp", 0)))
        embed = self._main_embed("📊 ความคืบหน้า", completed_text)
        embed.add_field(name="✨ Level", value=str(level), inline=True)
        embed.add_field(name="🔥 EXP", value=f"{current_exp}/{required_exp}", inline=True)
        embed.add_field(name="💰 Coins", value=str(user_data.get("coins", 0)), inline=True)
        embed.add_field(name="🏆 Rank", value=str(user_data.get("rank", "Bronze")), inline=True)
        embed.add_field(name="⚡ Combo", value=str(user_data.get("combo_count", 0)), inline=True)
        embed.add_field(name="🏅 Achievements", value=f"{len(user_data.get('achievements', []))}/100", inline=True)
        accuracy = (user_data.get("correct", 0) / max(1, user_data.get("attempted", 1))) * 100
        embed.add_field(name="🎯 Accuracy", value=f"{accuracy:.1f}%", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="daily", description="รับ Daily Reward รายวันแบบเกม")
    async def daily(self, interaction: discord.Interaction) -> None:
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)
        self._register_login(user_data)
        daily = user_data.setdefault("daily", {"date": "", "claimed": False, "week_day": 0})

        today = date.today().isoformat()
        if daily.get("date") == today and daily.get("claimed", False):
            await interaction.response.send_message("✅ วันนี้คุณรับ Daily Reward แล้ว", ephemeral=True)
            return

        week_day = int(daily.get("week_day", 0)) + 1
        if week_day > 7:
            week_day = 1
        daily["week_day"] = week_day
        daily["date"] = today
        daily["claimed"] = True

        reward = self.DAILY_TABLE[week_day]
        user_data["coins"] = int(user_data.get("coins", 0)) + int(reward.get("coins", 0))
        user_data["exp"] = int(user_data.get("exp", 0)) + int(reward.get("exp", 0))

        jackpot_text = ""
        event = "daily"
        if reward.get("boost"):
            user_data.setdefault("inventory", {})["boost_until"] = reward["boost"]
        if reward.get("chest"):
            chest_bonus = random.choice([20, 40, 80])
            user_data["coins"] += chest_bonus
            jackpot_text = f"\n🎁 Random Chest: +{chest_bonus} Coins"
        if reward.get("jackpot"):
            jackpot = random.choice(["500_coins", "rare_badge", "exp_x3", "special_title", "golden_frame"])
            if jackpot == "500_coins":
                user_data["coins"] += 500
                jackpot_text = "\n🔥 Weekly Jackpot: +500 Coins"
            elif jackpot == "rare_badge":
                user_data.setdefault("badges", []).append("Weekly Jackpot Badge")
                jackpot_text = "\n🔥 Weekly Jackpot: Rare Badge"
            elif jackpot == "exp_x3":
                user_data.setdefault("inventory", {})["boost_until"] = "x3_1h"
                jackpot_text = "\n🔥 Weekly Jackpot: EXP x3"
            elif jackpot == "special_title":
                user_data.setdefault("inventory", {}).setdefault("titles", []).append("Jackpot Hero")
                jackpot_text = "\n🔥 Weekly Jackpot: Title พิเศษ"
            else:
                user_data.setdefault("inventory", {}).setdefault("titles", []).append("Golden Frame Profile")
                jackpot_text = "\n🔥 Weekly Jackpot: Golden Frame Profile"
            event = "weekly_jackpot"

        unlocked = evaluate_achievements(user_data, {"event": event})
        self.user_store.update_user(interaction.user.id, user_data)

        embed = self.build_daily_reward_embed(reward["text"], jackpot_text, user_data.get("login", {}).get("consecutive_days", 1))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        extra = self._announce_new_achievements(unlocked)
        if extra:
            await interaction.followup.send(embed=extra, ephemeral=True)

    @app_commands.command(name="shop", description="เปิดร้านค้าไอเท็ม")
    async def shop(self, interaction: discord.Interaction) -> None:
        user_data = self.user_store.ensure_user(interaction.user.id, interaction.user.display_name)

        embed = discord.Embed(
            title="🛒 RPG Shop",
            description="ซื้อไอเท็มได้ด้วย Coins\n- 🏅 Gold Title: 100\n- 🔥 EXP Boost 1 วัน: 150\n- 💜 Rare Badge: 220\n- 🛡️ Save Streak: 250",
            color=discord.Color.dark_blue(),
        )
        embed.add_field(name="💰 Coins ของคุณ", value=str(user_data.get("coins", 0)), inline=False)

        async def on_buy(sub_interaction: discord.Interaction, item_key: str) -> None:
            item = ShopView.ITEMS[item_key]
            latest = self.user_store.ensure_user(sub_interaction.user.id, sub_interaction.user.display_name)
            if int(latest.get("coins", 0)) < int(item["cost"]):
                await sub_interaction.response.send_message("❌ Coins ไม่พอ", ephemeral=True)
                return

            latest["coins"] = int(latest.get("coins", 0)) - int(item["cost"])
            badges = latest.setdefault("badges", [])
            inventory = latest.setdefault("inventory", {"titles": [], "boost_until": "", "save_streak": 0})

            if item_key == "title_gold" and "Gold Challenger" not in inventory.setdefault("titles", []):
                inventory["titles"].append("Gold Challenger")
            elif item_key == "purple_badge" and "Rare Collector" not in badges:
                badges.append("Rare Collector")
            elif item_key == "exp_boost":
                inventory["boost_until"] = "x2_1d"
            elif item_key == "save_streak":
                inventory["save_streak"] = int(inventory.get("save_streak", 0)) + 1

            unlocked = evaluate_achievements(latest, {"event": "shop"})
            self.user_store.update_user(sub_interaction.user.id, latest)
            await sub_interaction.response.send_message(
                embed=discord.Embed(title="✅ ซื้อสำเร็จ", description=f"ซื้อ {item['name']} เรียบร้อย", color=discord.Color.green()),
                ephemeral=True,
            )
            extra = self._announce_new_achievements(unlocked)
            if extra:
                await sub_interaction.followup.send(embed=extra, ephemeral=True)

        view = ShopView(owner_id=interaction.user.id, on_buy=on_buy)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LearnCog(bot))
