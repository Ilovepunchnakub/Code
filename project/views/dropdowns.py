"""Dropdown components สำหรับระบบเรียนและแอดมิน"""

from __future__ import annotations

from typing import Any, Callable

import discord


class TaskDropdown(discord.ui.Select):
    """Dropdown เลือกโจทย์ในบทเรียน"""

    def __init__(self, tasks: list[dict[str, Any]], on_pick: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        self.tasks = tasks
        self.on_pick = on_pick

        options = [
            discord.SelectOption(
                label=f"ข้อ {task.get('id')}: {task.get('title')}",
                description=f"{task.get('difficulty', 'easy').upper()} | EXP {task.get('exp', 0)}",
                value=str(task.get("id")),
            )
            for task in tasks[:25]
        ]

        super().__init__(placeholder="เลือกโจทย์ที่ต้องการทำ", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        """เรียก callback เมื่อผู้ใช้เลือกโจทย์"""

        task_id = int(self.values[0])
        task = next((item for item in self.tasks if int(item.get("id", 0)) == task_id), None)
        if task is None:
            await interaction.response.send_message("❌ ไม่พบโจทย์ที่เลือก", ephemeral=True)
            return
        await self.on_pick(interaction, task)


class TaskAdminDropdown(discord.ui.Select):
    """Dropdown สำหรับเลือกโจทย์ในหน้าแก้ไข/ลบของแอดมิน"""

    def __init__(self, options_payload: list[dict[str, str]], on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        self.on_pick = on_pick
        options = [
            discord.SelectOption(
                label=item["label"][:100],
                value=item["value"],
                description=item.get("description", "")[:100],
            )
            for item in options_payload[:25]
        ]
        super().__init__(placeholder="เลือกโจทย์สำหรับจัดการ", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        """คืนค่า key ของโจทย์ที่ถูกเลือก"""

        await self.on_pick(interaction, self.values[0])
