"""Views เฉพาะฝั่ง Admin Panel"""

from __future__ import annotations

from typing import Any, Callable

import discord


class AdminPanelView(discord.ui.View):
    """ปุ่มหลักของ Admin Panel"""

    def __init__(
        self,
        on_add: Callable[[discord.Interaction], Any],
        on_edit: Callable[[discord.Interaction], Any],
        on_delete: Callable[[discord.Interaction], Any],
        on_change_chapter: Callable[[discord.Interaction], Any],
        on_reward: Callable[[discord.Interaction], Any],
        on_judge: Callable[[discord.Interaction], Any],
        on_view_all: Callable[[discord.Interaction], Any],
        on_ai: Callable[[discord.Interaction], Any],
        on_duplicate: Callable[[discord.Interaction], Any],
        on_bulk: Callable[[discord.Interaction], Any],
        on_rollback: Callable[[discord.Interaction], Any],
    ) -> None:
        super().__init__(timeout=600)
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_change_chapter = on_change_chapter
        self.on_reward = on_reward
        self.on_judge = on_judge
        self.on_view_all = on_view_all
        self.on_ai = on_ai
        self.on_duplicate = on_duplicate
        self.on_bulk = on_bulk
        self.on_rollback = on_rollback

    @discord.ui.button(label="➕ เพิ่มโจทย์", style=discord.ButtonStyle.success, row=0)
    async def add(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_add(interaction)

    @discord.ui.button(label="✏️ แก้ไขโจทย์", style=discord.ButtonStyle.primary, row=0)
    async def edit(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_edit(interaction)

    @discord.ui.button(label="🗑️ ลบโจทย์", style=discord.ButtonStyle.danger, row=0)
    async def delete(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_delete(interaction)

    @discord.ui.button(label="📂 เปลี่ยน Chapter", style=discord.ButtonStyle.secondary, row=0)
    async def chapter(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_change_chapter(interaction)

    @discord.ui.button(label="⭐ ตั้งค่ารางวัล", style=discord.ButtonStyle.secondary, row=0)
    async def reward(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_reward(interaction)

    @discord.ui.button(label="⚙️ ตั้งค่า Judge", style=discord.ButtonStyle.secondary, row=1)
    async def judge(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_judge(interaction)

    @discord.ui.button(label="👁️ ดูโจทย์ทั้งหมด", style=discord.ButtonStyle.secondary, row=1)
    async def view_all(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_view_all(interaction)

    @discord.ui.button(label="🤖 AI สร้างโจทย์", style=discord.ButtonStyle.success, row=1)
    async def ai(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_ai(interaction)

    @discord.ui.button(label="📄 Duplicate", style=discord.ButtonStyle.primary, row=1)
    async def duplicate(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_duplicate(interaction)

    @discord.ui.button(label="📦 Bulk Import/Export", style=discord.ButtonStyle.primary, row=1)
    async def bulk(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_bulk(interaction)

    @discord.ui.button(label="↩️ Undo ล่าสุด", style=discord.ButtonStyle.danger, row=2)
    async def rollback(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_rollback(interaction)


class SelectView(discord.ui.View):
    def __init__(self, placeholder: str, options: list[discord.SelectOption], on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(timeout=300)
        self.add_item(SelectMenu(placeholder=placeholder, options=options, on_pick=on_pick))


class SelectMenu(discord.ui.Select):
    def __init__(self, placeholder: str, options: list[discord.SelectOption], on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(placeholder=placeholder, options=options[:25], min_values=1, max_values=1)
        self.on_pick = on_pick

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.on_pick(interaction, self.values[0])


class EditFieldView(discord.ui.View):
    def __init__(self, on_select: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(timeout=300)
        self.on_select = on_select

    @discord.ui.button(label="✏️ ชื่อโจทย์", style=discord.ButtonStyle.primary)
    async def title(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_select(interaction, "title")

    @discord.ui.button(label="📝 คำอธิบาย", style=discord.ButtonStyle.primary)
    async def description(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_select(interaction, "description")

    @discord.ui.button(label="⭐ คะแนน", style=discord.ButtonStyle.secondary)
    async def reward(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_select(interaction, "reward")

    @discord.ui.button(label="💡 Hint", style=discord.ButtonStyle.secondary)
    async def hint(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_select(interaction, "hint")

    @discord.ui.button(label="⚙️ Judge", style=discord.ButtonStyle.secondary)
    async def judge(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_select(interaction, "judge")

    @discord.ui.button(label="🗑️ ลบ", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_select(interaction, "delete")


class ConfirmSaveView(discord.ui.View):
    def __init__(self, on_confirm: Callable[[discord.Interaction], Any]) -> None:
        super().__init__(timeout=300)
        self.on_confirm = on_confirm

    @discord.ui.button(label="✅ ยืนยันบันทึก", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_confirm(interaction)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="ยกเลิกการบันทึกแล้ว", embed=None, view=None)


class BulkActionView(discord.ui.View):
    def __init__(self, on_export: Callable[[discord.Interaction], Any], on_import: Callable[[discord.Interaction], Any]) -> None:
        super().__init__(timeout=300)
        self.on_export = on_export
        self.on_import = on_import

    @discord.ui.button(label="📤 Export Chapter", style=discord.ButtonStyle.primary)
    async def export(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_export(interaction)

    @discord.ui.button(label="📥 Import Chapter", style=discord.ButtonStyle.success)
    async def import_btn(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_import(interaction)
