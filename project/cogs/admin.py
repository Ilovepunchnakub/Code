"""Cog สำหรับ Admin Panel จัดการโจทย์แบบมืออาชีพ"""

from __future__ import annotations

import io
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from utils.ai_generator import generate_task
from utils.database import AssignmentStore
from views.admin_views import AdminPanelView, BulkActionView, ConfirmSaveView, EditFieldView, SelectView
from views.modals import (
    AddTaskPageOneModal,
    AddTaskPageThreeModal,
    AddTaskPageTwoModal,
    BulkImportModal,
    EditJudgeModal,
    EditRewardModal,
    EditSimpleModal,
    เพิ่มโจทย์หน้า1โมดัล,
    เพิ่มโจทย์หน้า2โมดัล,
    เพิ่มโจทย์หน้า3โมดัล,
)


class AdminCog(commands.Cog):
    """คำสั่ง /adminpanel สำหรับผู้ดูแลเซิร์ฟเวอร์"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        base = Path(__file__).resolve().parents[1]
        self.assignment_store = AssignmentStore(base / "assignments.json")
        self.audit_path = base / "admin_audit.log"
        self.add_task_sessions: dict[int, dict[str, Any]] = {}
        self.undo_stack: dict[int, dict[str, Any]] = {}

    def build_admin_panel_embed(self) -> discord.Embed:
        return discord.Embed(
            title="👑 Admin Panel",
            description="โหมดจัดการคอร์สระดับเกม AAA\n> เลือกเมนูจากปุ่มด้านล่าง",
            color=discord.Color.dark_blue(),
        )

    def _is_admin(self, interaction: discord.Interaction) -> bool:
        return bool(interaction.user.guild_permissions.administrator)

    def _log_action(self, actor_id: int, action: str, detail: dict[str, Any]) -> None:
        payload = {
            "at": datetime.utcnow().isoformat() + "Z",
            "actor_id": actor_id,
            "action": action,
            "detail": detail,
        }
        with self.audit_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _set_undo(self, actor_id: int, before_data: dict[str, Any], reason: str) -> None:
        self.undo_stack[actor_id] = {"before": deepcopy(before_data), "reason": reason}

    def _all_task_options(self) -> list[discord.SelectOption]:
        data = self.assignment_store.load()
        options: list[discord.SelectOption] = []
        for language, chapters in data.items():
            if language == "schema_version":
                continue
            for chapter_key, chapter_data in chapters.items():
                for task in chapter_data.get("tasks", []):
                    value = f"{language}|{chapter_key}|{task.get('id')}"
                    label = f"[{language}] {chapter_key} - {task.get('title')}"
                    options.append(discord.SelectOption(label=label[:100], value=value, description=f"ID {task.get('id')}"))
        return options

    def _resolve_task(self, key: str) -> tuple[dict[str, Any], str, str, dict[str, Any]]:
        language, chapter_key, task_id_str = key.split("|")
        task_id = int(task_id_str)
        data = self.assignment_store.load()
        tasks = data[language][chapter_key].get("tasks", [])
        task = next(item for item in tasks if int(item.get("id", 0)) == task_id)
        return data, language, chapter_key, task

    def _apply_task_edit(self, task: dict[str, Any], field: str, value: Any) -> None:
        if field == "title":
            task["title"] = str(value)
        elif field == "description":
            task["description"] = str(value)
        elif field == "reward":
            task["exp"] = int(value["exp"])
            task["xp"] = int(value["exp"])
            task["coins"] = int(value["coins"])
        elif field == "hint":
            task["hint"] = str(value)
        elif field == "main_answer":
            task["main_answer"] = str(value)
            alt_answers = [str(v) for v in task.get("alt_answers", []) if str(v).strip()]
            task["accepted_outputs"] = [task["main_answer"], *alt_answers]
        elif field == "alt_answers":
            alt_answers = [line.strip() for line in str(value).splitlines() if line.strip()]
            task["alt_answers"] = alt_answers
            task["accepted_outputs"] = [str(task.get("main_answer", "")).strip(), *alt_answers]
            task["accepted_outputs"] = [v for v in task["accepted_outputs"] if v]
        elif field == "judge":
            task["accepted_outputs"] = value["accepted_outputs"]
            if task["accepted_outputs"]:
                task["main_answer"] = str(task["accepted_outputs"][0])
                task["alt_answers"] = [str(v) for v in task["accepted_outputs"][1:5]]
            task["required_keywords"] = value["required_keywords"]
            task["forbidden_keywords"] = value["forbidden_keywords"]
            task["time_limit"] = int(value["time_limit"])
            task["memory_limit"] = int(value["memory_limit"])
        task["testcases"] = [{"input": "", "accepted_outputs": task.get("accepted_outputs", [])}]

    def _build_diff_text(self, before: dict[str, Any], after: dict[str, Any]) -> str:
        lines = []
        for key in sorted(set(before) | set(after)):
            if before.get(key) != after.get(key):
                lines.append(f"- {key}: `{before.get(key)}` → `{after.get(key)}`")
        return "\n".join(lines) or "ไม่มีการเปลี่ยนแปลง"

    @app_commands.command(name="adminpanel", description="เปิดแผงควบคุมแอดมินสำหรับจัดการโจทย์")
    async def adminpanel(self, interaction: discord.Interaction) -> None:
        if not self._is_admin(interaction):
            await interaction.response.send_message("❌ คำสั่งนี้สำหรับแอดมินเท่านั้น", ephemeral=True)
            return

        view = AdminPanelView(
            on_add=self._start_add_task_flow,
            on_edit=self._start_edit_flow,
            on_delete=self._start_delete_flow,
            on_change_chapter=self._change_chapter_info,
            on_reward=self._reward_info,
            on_judge=self._judge_info,
            on_view_all=self._view_all_tasks,
            on_ai=self._generate_ai_task,
            on_duplicate=self._start_duplicate_flow,
            on_bulk=self._bulk_action_menu,
            on_rollback=self._rollback_last,
        )
        await interaction.response.send_message(embed=self.build_admin_panel_embed(), view=view, ephemeral=True)

    async def _start_add_task_flow(self, interaction: discord.Interaction) -> None:
        async def page_one_handler(modal_interaction: discord.Interaction, page1: dict[str, Any]) -> None:
            self.add_task_sessions[modal_interaction.user.id] = page1
            await modal_interaction.response.send_modal(AddTaskPageTwoModal(on_submit_handler=page_two_handler))

        async def page_two_handler(modal_interaction: discord.Interaction, page2: dict[str, Any]) -> None:
            self.add_task_sessions.setdefault(modal_interaction.user.id, {}).update(page2)
            await modal_interaction.response.send_modal(AddTaskPageThreeModal(on_submit_handler=page_three_handler))

        async def page_three_handler(modal_interaction: discord.Interaction, page3: dict[str, Any]) -> None:
            payload = self.add_task_sessions.get(modal_interaction.user.id, {})
            payload.update(page3)
            data = self.assignment_store.load()
            before = deepcopy(data)

            language = payload["language"]
            chapter_key = payload["chapter"]
            if language not in data:
                data[language] = {}
            if chapter_key not in data[language]:
                data[language][chapter_key] = {"title": chapter_key, "locked_level": 1, "tasks": []}

            tasks = data[language][chapter_key].setdefault("tasks", [])
            new_id = max([int(task.get("id", 0)) for task in tasks], default=0) + 1

            new_task = {
                "id": new_id,
                "title": payload["title"],
                "description": payload["description"],
                "difficulty": payload["difficulty"],
                "exp": int(payload["exp"]),
                "coins": int(payload["coins"]),
                "accepted_outputs": payload["accepted_outputs"],
                "required_keywords": payload.get("required_keywords", []),
                "forbidden_keywords": payload.get("forbidden_keywords", []),
                "hint": payload.get("hint", ""),
                "example_code": payload.get("example_code", ""),
                "time_limit": int(payload.get("time_limit", 2)),
                "memory_limit": int(payload.get("memory_limit", 128)),
                "testcases": [{"input": "", "accepted_outputs": payload["accepted_outputs"]}],
            }

            tasks.append(new_task)
            self.assignment_store.save(data)
            self._set_undo(modal_interaction.user.id, before, "add_task")
            self._log_action(modal_interaction.user.id, "add_task", {"language": language, "chapter": chapter_key, "task_id": new_id})
            self.add_task_sessions.pop(modal_interaction.user.id, None)

            await modal_interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ เพิ่มโจทย์สำเร็จ",
                    description=f"เพิ่ม `{new_task['title']}` ใน `{language}/{chapter_key}` (ID: {new_id})",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )

        await interaction.response.send_modal(AddTaskPageOneModal(on_submit_handler=page_one_handler))

    async def _start_edit_flow(self, interaction: discord.Interaction) -> None:
        data = self.assignment_store.load()
        language_options = [discord.SelectOption(label=lang.upper(), value=lang) for lang in data.keys() if lang != "schema_version"]

        async def on_pick_language(i1: discord.Interaction, lang: str) -> None:
            chapter_options = [discord.SelectOption(label=f"{key} - {value.get('title', '')}"[:100], value=key) for key, value in data.get(lang, {}).items()]

            async def on_pick_chapter(i2: discord.Interaction, chapter_key: str) -> None:
                task_options = [
                    discord.SelectOption(label=f"ID {task.get('id')} - {task.get('title')}", value=str(task.get("id")))
                    for task in data.get(lang, {}).get(chapter_key, {}).get("tasks", [])
                ]

                async def on_pick_task(i3: discord.Interaction, task_id_str: str) -> None:
                    key = f"{lang}|{chapter_key}|{task_id_str}"
                    await self._open_edit_field_menu(i3, key)

                await i2.response.edit_message(content="3) เลือกโจทย์ที่ต้องการแก้", view=SelectView("เลือกโจทย์", task_options, on_pick_task), embed=None)

            await i1.response.edit_message(content="2) เลือก Chapter", view=SelectView("เลือก Chapter", chapter_options, on_pick_chapter), embed=None)

        await interaction.response.send_message("1) เลือกภาษา", view=SelectView("เลือกภาษา", language_options, on_pick_language), ephemeral=True)

    async def _open_edit_field_menu(self, interaction: discord.Interaction, task_key: str) -> None:
        async def on_field_select(i: discord.Interaction, field: str) -> None:
            if field == "delete":
                await self._delete_task_by_key(i, task_key)
                return

            data, language, chapter_key, task = self._resolve_task(task_key)
            before_all = deepcopy(data)
            before_task = deepcopy(task)

            async def preview_and_confirm(after_value: Any) -> None:
                preview_task = deepcopy(before_task)
                self._apply_task_edit(preview_task, field, after_value)
                diff_text = self._build_diff_text(before_task, preview_task)

                async def do_save(confirm_interaction: discord.Interaction) -> None:
                    latest_data, _, _, latest_task = self._resolve_task(task_key)
                    self._apply_task_edit(latest_task, field, after_value)
                    self.assignment_store.save(latest_data)
                    self._set_undo(confirm_interaction.user.id, before_all, f"edit_{field}")
                    self._log_action(confirm_interaction.user.id, "edit_task", {"task_key": task_key, "field": field, "after": after_value})
                    await confirm_interaction.response.edit_message(content=f"✅ บันทึก `{latest_task.get('title')}` สำเร็จ", embed=None, view=None)

                embed = discord.Embed(title="🔍 Preview ก่อนบันทึก", description=diff_text[:3900], color=discord.Color.gold())
                await i.response.send_message(embed=embed, view=ConfirmSaveView(do_save), ephemeral=True)

            if field in {"title", "description", "hint", "main_answer", "alt_answers"}:
                label_map = {
                    "title": "ชื่อโจทย์ใหม่",
                    "description": "คำอธิบายใหม่",
                    "hint": "Hint ใหม่",
                    "main_answer": "คำตอบหลักใหม่",
                    "alt_answers": "คำตอบเสริม (1 บรรทัด ต่อ 1 คำตอบ)",
                }
                default_map = {
                    "title": str(task.get("title", "")),
                    "description": str(task.get("description", "")),
                    "hint": str(task.get("hint", "")),
                    "main_answer": str(task.get("main_answer", task.get("example_code", ""))),
                    "alt_answers": "\n".join(task.get("alt_answers", [])),
                }
                modal = EditSimpleModal(
                    title="✏️ แก้ไขข้อมูลโจทย์",
                    label=label_map[field],
                    value=default_map[field],
                    on_submit_handler=lambda modal_i, value: preview_and_confirm(value),
                )
                await i.response.send_modal(modal)
            elif field == "reward":
                await i.response.send_modal(
                    EditRewardModal(
                        on_submit_handler=lambda modal_i, value: preview_and_confirm(value),
                        exp_default=int(task.get("exp", 20)),
                        coins_default=int(task.get("coins", 5)),
                    )
                )
            elif field == "judge":
                await i.response.send_modal(
                    EditJudgeModal(on_submit_handler=lambda modal_i, value: preview_and_confirm(value), task=task)
                )

        await interaction.response.send_message("4) เลือกสิ่งที่จะแก้", view=EditFieldView(on_select=on_field_select), ephemeral=True)

    async def _delete_task_by_key(self, interaction: discord.Interaction, task_key: str) -> None:
        data, language, chapter_key, task = self._resolve_task(task_key)
        before = deepcopy(data)
        tasks = data[language][chapter_key].get("tasks", [])
        data[language][chapter_key]["tasks"] = [item for item in tasks if int(item.get("id", 0)) != int(task.get("id", 0))]
        self.assignment_store.save(data)
        self._set_undo(interaction.user.id, before, "delete_task")
        self._log_action(interaction.user.id, "delete_task", {"task_key": task_key})
        await interaction.response.send_message(f"🗑️ ลบโจทย์ `{task.get('title')}` เรียบร้อย", ephemeral=True)

    async def _start_delete_flow(self, interaction: discord.Interaction) -> None:
        options = self._all_task_options()

        async def on_pick(i: discord.Interaction, value: str) -> None:
            await self._delete_task_by_key(i, value)

        await interaction.response.send_message("เลือกโจทย์ที่ต้องการลบ", view=SelectView("เลือกโจทย์", options, on_pick), ephemeral=True)

    async def _start_duplicate_flow(self, interaction: discord.Interaction) -> None:
        options = self._all_task_options()

        async def on_pick(i: discord.Interaction, value: str) -> None:
            data, language, chapter_key, task = self._resolve_task(value)
            before = deepcopy(data)
            tasks = data[language][chapter_key].setdefault("tasks", [])
            new_task = deepcopy(task)
            new_task["id"] = max(int(t.get("id", 0)) for t in tasks) + 1
            new_task["title"] = f"{task.get('title')} (Copy)"
            tasks.append(new_task)
            self.assignment_store.save(data)
            self._set_undo(i.user.id, before, "duplicate_task")
            self._log_action(i.user.id, "duplicate_task", {"from": value, "new_id": new_task["id"]})
            await i.response.send_message(f"📄 Duplicate สำเร็จ: `{new_task['title']}` (ID {new_task['id']})", ephemeral=True)

        await interaction.response.send_message("เลือกโจทย์ที่ต้องการ Duplicate", view=SelectView("เลือกโจทย์", options, on_pick), ephemeral=True)

    async def _bulk_action_menu(self, interaction: discord.Interaction) -> None:
        async def on_export(i: discord.Interaction) -> None:
            data = self.assignment_store.load()
            language_options = [
                discord.SelectOption(label=f"{lang}", value=lang, description=f"จำนวน chapter: {len(chapters)}")
                for lang, chapters in data.items()
                if lang != "schema_version"
            ]
            if not language_options:
                await i.response.send_message("ไม่มีข้อมูล chapter", ephemeral=True)
                return

            async def on_language_pick(lang_i: discord.Interaction, language: str) -> None:
                chapters = data.get(language, {})
                chapter_options = [
                    discord.SelectOption(label=chapter_key, value=chapter_key, description=str(chapter_data.get("title", ""))[:95])
                    for chapter_key, chapter_data in chapters.items()
                ]
                if not chapter_options:
                    await lang_i.response.send_message(f"ไม่พบ chapter ในภาษา `{language}`", ephemeral=True)
                    return

                async def on_chapter_pick(chapter_i: discord.Interaction, chapter_key: str) -> None:
                    chapter_data = data[language][chapter_key]
                    content = json.dumps(chapter_data, ensure_ascii=False, indent=2)
                    file = discord.File(io.BytesIO(content.encode("utf-8")), filename=f"{language}_{chapter_key}.json")
                    await chapter_i.response.send_message("📤 Export สำเร็จ", ephemeral=True, file=file)

                await lang_i.response.send_message(
                    "เลือก chapter ที่ต้องการ export",
                    ephemeral=True,
                    view=SelectView("เลือก chapter", chapter_options, on_chapter_pick),
                )

            await i.response.send_message("เลือกภาษา", ephemeral=True, view=SelectView("เลือกภาษา", language_options, on_language_pick))

        async def on_import(i: discord.Interaction) -> None:
            async def submit_handler(modal_i: discord.Interaction, payload: dict[str, Any]) -> None:
                data = self.assignment_store.load()
                before = deepcopy(data)
                tasks = json.loads(payload["tasks_json"])
                language = payload["language"]
                chapter = payload["chapter"]
                if language not in data:
                    data[language] = {}
                data[language][chapter] = {"title": payload["title"], "locked_level": 1, "tasks": tasks}
                self.assignment_store.save(data)
                self._set_undo(modal_i.user.id, before, "bulk_import")
                self._log_action(modal_i.user.id, "bulk_import", {"language": language, "chapter": chapter})
                await modal_i.response.send_message("📥 Import Chapter สำเร็จ", ephemeral=True)

            await i.response.send_modal(BulkImportModal(on_submit_handler=submit_handler))

        await interaction.response.send_message("📦 เลือกการทำงาน Bulk", view=BulkActionView(on_export=on_export, on_import=on_import), ephemeral=True)

    async def _rollback_last(self, interaction: discord.Interaction) -> None:
        payload = self.undo_stack.get(interaction.user.id)
        if not payload:
            await interaction.response.send_message("ยังไม่มีรายการให้ Undo", ephemeral=True)
            return
        self.assignment_store.save(payload["before"])
        self._log_action(interaction.user.id, "rollback", {"reason": payload["reason"]})
        self.undo_stack.pop(interaction.user.id, None)
        await interaction.response.send_message("↩️ Rollback ล่าสุดเรียบร้อย", ephemeral=True)

    async def _change_chapter_info(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("📂 ใช้เมนู Bulk Import/Export เพื่อย้ายและจัดการ chapter ได้ง่ายขึ้น", ephemeral=True)

    async def _reward_info(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("⭐ ใช้เมนูแก้ไขโจทย์ > ⭐ คะแนน (modal แยกเฉพาะ)", ephemeral=True)

    async def _judge_info(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("⚙️ ใช้เมนูแก้ไขโจทย์ > ⚙️ Judge (modal แยกเฉพาะ)", ephemeral=True)

    async def _view_all_tasks(self, interaction: discord.Interaction) -> None:
        data = self.assignment_store.load()
        lines = []
        for language, chapters in data.items():
            if language == "schema_version":
                continue
            for chapter_key, chapter_data in chapters.items():
                for task in chapter_data.get("tasks", []):
                    lines.append(f"[{language}] {chapter_key} | ID {task.get('id')} | {task.get('title')} | EXP {task.get('exp',0)} | Coins {task.get('coins',0)}")
        embed = discord.Embed(title="👁️ รายการโจทย์ทั้งหมด", description="\n".join(lines[:35]) if lines else "ยังไม่มีโจทย์", color=discord.Color.dark_blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _generate_ai_task(self, interaction: discord.Interaction) -> None:
        data = self.assignment_store.load()
        before = deepcopy(data)
        new_task = generate_task("python", "medium")
        chapter = data.setdefault("python", {}).setdefault("chapter1", {"title": "พื้นฐาน Python", "locked_level": 1, "tasks": []})
        chapter.setdefault("tasks", []).append(new_task)
        self.assignment_store.save(data)
        self._set_undo(interaction.user.id, before, "ai_generate")
        self._log_action(interaction.user.id, "ai_generate", {"task_id": new_task["id"]})
        await interaction.response.send_message(embed=discord.Embed(title="🤖 AI สร้างโจทย์สำเร็จ", description=f"เพิ่มโจทย์ `{new_task['title']}` (ID: {new_task['id']}) แล้ว", color=discord.Color.green()), ephemeral=True)

    @app_commands.command(name="เพิ่มโจทย์", description="เพิ่มโจทย์ใหม่แบบหลายหน้า ภาษาไทย")
    async def add_task_th(self, interaction: discord.Interaction) -> None:
        if not self._is_admin(interaction):
            await interaction.response.send_message("❌ คำสั่งนี้สำหรับแอดมินเท่านั้น", ephemeral=True)
            return

        async def page1(modal_i: discord.Interaction, payload1: dict[str, Any]) -> None:
            self.add_task_sessions[modal_i.user.id] = payload1
            await modal_i.response.send_modal(เพิ่มโจทย์หน้า2โมดัล(page2))

        async def page2(modal_i: discord.Interaction, payload2: dict[str, Any]) -> None:
            self.add_task_sessions.setdefault(modal_i.user.id, {}).update(payload2)
            await modal_i.response.send_modal(เพิ่มโจทย์หน้า3โมดัล(page3))

        async def page3(modal_i: discord.Interaction, payload3: dict[str, Any]) -> None:
            data = self.assignment_store.load()
            before = deepcopy(data)
            payload = self.add_task_sessions.get(modal_i.user.id, {})
            payload.update(payload3)
            language = payload["language"]
            chapter_number = int(payload["chapter_number"])
            chapter_key = f"chapter{chapter_number}"
            chapter = data.setdefault(language, {}).setdefault(
                chapter_key, {"title": payload["chapter_title"], "number": chapter_number, "locked_level": 1, "tasks": []}
            )
            chapter["title"] = payload["chapter_title"]
            chapter["number"] = chapter_number
            tasks = chapter.setdefault("tasks", [])
            main_answer = payload["main_answer"]
            alt_answers = payload.get("alt_answers", [])
            all_answers = [main_answer, *alt_answers]
            new_task = {
                "id": max([int(t.get("id", 0)) for t in tasks], default=0) + 1,
                "title": payload["task_title"],
                "xp": int(payload["xp"]),
                "exp": int(payload["xp"]),
                "difficulty": payload["difficulty"],
                "description": payload["description"],
                "hint": payload["hint"],
                "main_answer": main_answer,
                "alt_answers": alt_answers,
                "accepted_outputs": all_answers,
                "output_example": payload.get("output_example", ""),
                "tags": payload.get("tags", []),
                "show_solution": True,
                "daily_limit": 0,
                "bonus_first_try_xp": 0,
                "testcases": [{"input": "", "accepted_outputs": all_answers}],
            }
            tasks.append(new_task)
            self.assignment_store.save(data)
            self._set_undo(modal_i.user.id, before, "add_task_redesign")
            self.add_task_sessions.pop(modal_i.user.id, None)
            embed = discord.Embed(title="✅ เพิ่มโจทย์สำเร็จ", color=discord.Color.dark_blue())
            embed.add_field(name="ชื่อโจทย์", value=new_task["title"], inline=False)
            embed.add_field(name="บทเรียน", value=f"บทที่ {chapter_number} {chapter['title']}", inline=False)
            embed.add_field(name="ระดับ", value=str(new_task["difficulty"]), inline=True)
            embed.add_field(name="รางวัล", value=f"{new_task['xp']} XP", inline=True)
            embed.add_field(name="รายละเอียด", value=new_task["description"][:1000], inline=False)
            await modal_i.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_modal(เพิ่มโจทย์หน้า1โมดัล(page1))

    @app_commands.command(name="ลบโจทย์", description="ลบโจทย์ในบทเรียน")
    async def delete_task_th(self, interaction: discord.Interaction) -> None:
        if not self._is_admin(interaction):
            await interaction.response.send_message("❌ คำสั่งนี้สำหรับแอดมินเท่านั้น", ephemeral=True)
            return
        await self._start_delete_flow(interaction)

    @app_commands.command(name="แก้ไขโจทย์", description="แก้ไขโจทย์ในบทเรียน")
    async def edit_task_th(self, interaction: discord.Interaction) -> None:
        if not self._is_admin(interaction):
            await interaction.response.send_message("❌ คำสั่งนี้สำหรับแอดมินเท่านั้น", ephemeral=True)
            return
        await self._start_edit_flow(interaction)

    @app_commands.command(name="แอดมิน", description="เปิดแผงควบคุมแอดมิน")
    async def adminpanel_th(self, interaction: discord.Interaction) -> None:
        await self.adminpanel(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
