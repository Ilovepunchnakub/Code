"""Cog สำหรับ Admin Panel จัดการโจทย์ผ่าน Discord"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from utils.ai_generator import generate_task
from utils.database import AssignmentStore, UserStore
from views.buttons import AdminPanelView, AdminSelectView, ConfirmDeleteView
from views.modals import AddTaskModal, EditTaskModal


class AdminCog(commands.Cog):
    """คำสั่ง /adminpanel สำหรับผู้ดูแลเซิร์ฟเวอร์"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.assignment_store = AssignmentStore(base / "assignments.json")
        self.user_store = UserStore(base / "users.json")

    def _is_admin(self, interaction: discord.Interaction) -> bool:
        """ตรวจสิทธิ์ admin จาก permission ของผู้ใช้"""

        if interaction.user.guild_permissions.administrator:
            return True
        return False

    @app_commands.command(name="adminpanel", description="เปิดแผงควบคุมแอดมินสำหรับจัดการโจทย์")
    async def adminpanel(self, interaction: discord.Interaction) -> None:
        if not self._is_admin(interaction):
            await interaction.response.send_message("❌ คำสั่งนี้สำหรับแอดมินเท่านั้น", ephemeral=True)
            return

        embed = discord.Embed(
            title="👑 Admin Panel",
            description="จัดการโจทย์และคอร์สได้จากปุ่มด้านล่าง",
            color=discord.Color.dark_blue(),
        )
        view = AdminPanelView(
            on_add=self._open_add_modal,
            on_edit=self._open_edit_picker,
            on_delete=self._open_delete_picker,
            on_manage_chapter=self._manage_chapter,
            on_set_score=self._set_score_hint,
            on_view_all=self._view_all_tasks,
            on_generate_ai=self._generate_ai_task,
            on_analytics=self._show_analytics,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _open_add_modal(self, interaction: discord.Interaction) -> None:
        """เปิดฟอร์มเพิ่มโจทย์"""

        async def on_submit(modal_interaction: discord.Interaction, payload: dict[str, str]) -> None:
            data = self.assignment_store.load()
            language = payload["language"]
            chapter_key = payload["chapter"]

            if language not in data:
                data[language] = {}
            if chapter_key not in data[language]:
                data[language][chapter_key] = {"title": chapter_key, "locked_level": 1, "tasks": []}

            tasks = data[language][chapter_key].setdefault("tasks", [])
            next_id = max([int(task.get("id", 0)) for task in tasks], default=0) + 1
            difficulty = payload["difficulty"] if payload["difficulty"] in {"easy", "medium", "hard"} else "easy"

            new_task = {
                "id": next_id,
                "title": payload["title"],
                "difficulty": difficulty,
                "exp": {"easy": 20, "medium": 50, "hard": 120}[difficulty],
                "coins": {"easy": 5, "medium": 10, "hard": 20}[difficulty],
                "description": payload["description"],
                "accepted_outputs": ["TODO"],
                "required_keywords_any": ["print"] if language == "python" else ["printf", "puts"],
                "forbidden_keywords": ["goto"] if language == "c" else [],
                "hint": "เพิ่ม hint ภายหลังได้",
                "example_code": "# ใส่โค้ดตัวอย่าง",
                "testcases": [{"input": "", "accepted_outputs": ["TODO"]}],
                "time_limit_sec": 2,
                "memory_limit_mb": 128,
                "regex_compare": False,
                "ignore_case": True,
                "ignore_space": True,
            }
            tasks.append(new_task)
            self.assignment_store.save(data)
            await modal_interaction.response.send_message(
                f"✅ เพิ่มโจทย์ `{new_task['title']}` สำเร็จ (ID: {next_id})", ephemeral=True
            )

        await interaction.response.send_modal(AddTaskModal(on_submit_handler=on_submit))

    def _build_task_index(self) -> tuple[list[dict[str, str]], dict[str, tuple[str, str, int]]]:
        """สร้างรายการโจทย์สำหรับ dropdown + map สำหรับอ้างอิงกลับ"""

        data = self.assignment_store.load()
        options: list[dict[str, str]] = []
        key_map: dict[str, tuple[str, str, int]] = {}

        for language, chapters in data.items():
            for chapter_key, chapter in chapters.items():
                for task in chapter.get("tasks", []):
                    key = f"{language}|{chapter_key}|{task.get('id')}"
                    options.append(
                        {
                            "label": f"[{language}] {chapter_key} - {task.get('title')}",
                            "value": key,
                            "description": f"ID {task.get('id')}",
                        }
                    )
                    key_map[key] = (language, chapter_key, int(task.get("id", 0)))
        return options, key_map

    async def _open_edit_picker(self, interaction: discord.Interaction) -> None:
        """ให้แอดมินเลือกโจทย์เพื่อแก้ไข"""

        options, key_map = self._build_task_index()
        if not options:
            await interaction.response.send_message("⚠️ ยังไม่มีโจทย์", ephemeral=True)
            return

        async def on_pick(sub_interaction: discord.Interaction, key: str) -> None:
            language, chapter_key, task_id = key_map[key]

            async def on_submit(modal_interaction: discord.Interaction, payload: dict[str, str]) -> None:
                data = self.assignment_store.load()
                tasks = data[language][chapter_key]["tasks"]
                task = next(item for item in tasks if int(item.get("id", 0)) == task_id)
                if payload.get("title"):
                    task["title"] = payload["title"]
                if payload.get("description"):
                    task["description"] = payload["description"]
                if payload.get("difficulty") in {"easy", "medium", "hard"}:
                    task["difficulty"] = payload["difficulty"]
                if payload.get("accepted_output"):
                    task["accepted_outputs"] = [payload["accepted_output"]]
                self.assignment_store.save(data)
                await modal_interaction.response.send_message("✅ แก้ไขโจทย์สำเร็จ", ephemeral=True)

            await sub_interaction.response.send_modal(EditTaskModal(on_submit_handler=on_submit))

        view = AdminSelectView(options_payload=options, on_pick=on_pick)
        await interaction.response.send_message("✏️ เลือกโจทย์ที่ต้องการแก้ไข", view=view, ephemeral=True)

    async def _open_delete_picker(self, interaction: discord.Interaction) -> None:
        """ให้แอดมินเลือกโจทย์เพื่อลบ"""

        options, key_map = self._build_task_index()
        if not options:
            await interaction.response.send_message("⚠️ ยังไม่มีโจทย์", ephemeral=True)
            return

        async def on_pick(sub_interaction: discord.Interaction, key: str) -> None:
            language, chapter_key, task_id = key_map[key]

            async def on_confirm(confirm_interaction: discord.Interaction) -> None:
                data = self.assignment_store.load()
                tasks = data[language][chapter_key]["tasks"]
                data[language][chapter_key]["tasks"] = [item for item in tasks if int(item.get("id", 0)) != task_id]
                self.assignment_store.save(data)
                await confirm_interaction.response.edit_message(content="✅ ลบโจทย์สำเร็จ", embed=None, view=None)

            async def on_cancel(cancel_interaction: discord.Interaction) -> None:
                await cancel_interaction.response.edit_message(content="ยกเลิกลบโจทย์แล้ว", embed=None, view=None)

            view = ConfirmDeleteView(on_confirm=on_confirm, on_cancel=on_cancel)
            await sub_interaction.response.send_message("🗑️ ยืนยันการลบโจทย์นี้หรือไม่?", view=view, ephemeral=True)

        view = AdminSelectView(options_payload=options, on_pick=on_pick)
        await interaction.response.send_message("🗑️ เลือกโจทย์ที่ต้องการลบ", view=view, ephemeral=True)

    async def _manage_chapter(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "📂 โหมดจัดการบทเรียน: ตอนนี้รองรับเพิ่มบทผ่าน /adminpanel > เพิ่มโจทย์ (ระบบจะสร้าง chapter อัตโนมัติ)",
            ephemeral=True,
        )

    async def _set_score_hint(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "📊 ตั้งค่า EXP/Coins ได้จากการแก้ไขโจทย์ในไฟล์ assignments หรือขยาย modal เพิ่มฟิลด์ได้ทันที",
            ephemeral=True,
        )

    async def _view_all_tasks(self, interaction: discord.Interaction) -> None:
        data = self.assignment_store.load()
        lines = []
        for language, chapters in data.items():
            for chapter_key, chapter in chapters.items():
                for task in chapter.get("tasks", []):
                    lines.append(
                        f"[{language}] {chapter_key} | ID {task.get('id')} | {task.get('title')} | {task.get('difficulty')}"
                    )
        embed = discord.Embed(
            title="👁️ รายการโจทย์ทั้งหมด",
            description="\n".join(lines[:40]) or "ยังไม่มีโจทย์",
            color=discord.Color.dark_blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _generate_ai_task(self, interaction: discord.Interaction) -> None:
        data = self.assignment_store.load()
        generated = generate_task(language="python", difficulty="medium")
        chapter = data.setdefault("python", {}).setdefault("chapter1", {"title": "พื้นฐาน Python", "locked_level": 1, "tasks": []})
        chapter.setdefault("tasks", []).append(generated)
        self.assignment_store.save(data)

        embed = discord.Embed(
            title="🤖 AI สร้างโจทย์สำเร็จ",
            description=f"เพิ่มโจทย์ `{generated['title']}` (ID: {generated['id']})",
            color=discord.Color.purple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _show_analytics(self, interaction: discord.Interaction) -> None:
        users = self.user_store.load().values()
        total_pass = sum(user.get("correct", 0) for user in users)
        total_fail = sum(max(0, user.get("attempted", 0) - user.get("correct", 0)) for user in users)
        avg_attempt = 0.0
        users_list = list(self.user_store.load().values())
        if users_list:
            avg_attempt = sum(user.get("attempted", 0) for user in users_list) / len(users_list)

        embed = discord.Embed(title="📈 Analytics", color=discord.Color.dark_blue())
        embed.add_field(name="คนผ่านรวม", value=str(total_pass), inline=True)
        embed.add_field(name="คนตกรวม", value=str(total_fail), inline=True)
        embed.add_field(name="ค่าเฉลี่ยการส่ง", value=f"{avg_attempt:.2f}", inline=True)
        embed.add_field(name="หมายเหตุ", value="ขยายเป็นรายโจทย์ได้ในอนาคต", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
