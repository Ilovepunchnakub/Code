"""Button Views สำหรับ flow การเรียน เกม และแอดมิน"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

import discord

from views.dropdowns import TaskAdminDropdown, TaskDropdown


class OwnerOnlyView(discord.ui.View):
    """View ที่จำกัดสิทธิ์เฉพาะเจ้าของคำสั่ง"""

    def __init__(self, owner_id: int, timeout: float = 300) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("⚠️ เมนูนี้เป็นของผู้ใช้ที่เรียกคำสั่งเท่านั้น", ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True


class LanguageView(OwnerOnlyView):
    def __init__(self, owner_id: int, on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(owner_id=owner_id)
        self.on_pick = on_pick

    @discord.ui.button(label="🔵 ภาษา C", style=discord.ButtonStyle.primary)
    async def pick_c(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "c")

    @discord.ui.button(label="🐍 ภาษา Python", style=discord.ButtonStyle.primary)
    async def pick_python(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "python")


class ChapterView(OwnerOnlyView):
    def __init__(self, owner_id: int, chapters: dict[str, Any], on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(owner_id=owner_id)
        icons = ["📘", "📗", "📙", "📕", "📒"]
        for index, chapter_key in enumerate(chapters.keys()):
            button = discord.ui.Button(
                label=f"{icons[index % len(icons)]} บทที่ {index + 1} {chapters[chapter_key].get('title', '')}"[:80],
                style=discord.ButtonStyle.secondary,
            )

            async def callback(interaction: discord.Interaction, key: str = chapter_key) -> None:
                await on_pick(interaction, key)

            button.callback = callback  # type: ignore[method-assign]
            self.add_item(button)


class TaskView(OwnerOnlyView):
    def __init__(self, owner_id: int, tasks: list[dict[str, Any]], on_pick: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(owner_id=owner_id)
        self.add_item(TaskDropdown(tasks=tasks, on_pick=on_pick))


class QuestCardView(OwnerOnlyView):
    def __init__(
        self,
        owner_id: int,
        on_submit: Callable[[discord.Interaction], Any],
        on_hint: Callable[[discord.Interaction], Any],
        on_solution: Callable[[discord.Interaction], Any],
        on_back: Callable[[discord.Interaction], Any],
    ) -> None:
        super().__init__(owner_id=owner_id)
        self._on_submit = on_submit
        self._on_hint = on_hint
        self._on_solution = on_solution
        self._on_back = on_back

    @discord.ui.button(label="📝 ส่งงาน", style=discord.ButtonStyle.success)
    async def submit(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_submit(interaction)

    @discord.ui.button(label="💡 Hint", style=discord.ButtonStyle.secondary)
    async def hint(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_hint(interaction)

    @discord.ui.button(label="📘 ดูเฉลย", style=discord.ButtonStyle.primary)
    async def solution(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_solution(interaction)

    @discord.ui.button(label="🔙 กลับ", style=discord.ButtonStyle.danger)
    async def back(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_back(interaction)


class ShopView(OwnerOnlyView):
    ITEMS = {
        "title_gold": {"name": "🏅 Gold Title", "cost": 100},
        "exp_boost": {"name": "🔥 EXP Boost 1 วัน", "cost": 150},
        "purple_badge": {"name": "💜 Rare Badge", "cost": 220},
        "save_streak": {"name": "🛡️ Save Streak", "cost": 250},
    }

    def __init__(self, owner_id: int, on_buy: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(owner_id=owner_id)
        self.on_buy = on_buy

    @discord.ui.button(label="🏅 ซื้อ Title", style=discord.ButtonStyle.primary)
    async def buy_title(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_buy(interaction, "title_gold")

    @discord.ui.button(label="🔥 ซื้อ EXP Boost", style=discord.ButtonStyle.primary)
    async def buy_boost(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_buy(interaction, "exp_boost")

    @discord.ui.button(label="💜 Rare Badge", style=discord.ButtonStyle.primary)
    async def buy_badge(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_buy(interaction, "purple_badge")

    @discord.ui.button(label="🛡️ Save Streak", style=discord.ButtonStyle.secondary)
    async def buy_save_streak(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_buy(interaction, "save_streak")


class ProfileActionView(OwnerOnlyView):
    """ปุ่มเสริมหน้าโปรไฟล์"""

    def __init__(
        self,
        owner_id: int,
        on_theme: Callable[[discord.Interaction], Any],
        on_badges: Callable[[discord.Interaction], Any],
        on_stats: Callable[[discord.Interaction], Any],
        on_rank: Callable[[discord.Interaction], Any],
    ) -> None:
        super().__init__(owner_id=owner_id)
        self.on_theme = on_theme
        self.on_badges = on_badges
        self.on_stats = on_stats
        self.on_rank = on_rank

    @discord.ui.button(label="🎨 เปลี่ยนธีม", style=discord.ButtonStyle.primary)
    async def theme(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_theme(interaction)

    @discord.ui.button(label="🏅 ดู Badge", style=discord.ButtonStyle.secondary)
    async def badges(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_badges(interaction)

    @discord.ui.button(label="📈 สถิติ", style=discord.ButtonStyle.secondary)
    async def stats(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_stats(interaction)

    @discord.ui.button(label="🏆 ดูอันดับ", style=discord.ButtonStyle.success)
    async def rank(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_rank(interaction)


class ThemeSelectView(OwnerOnlyView):
    THEMES = ["Blue Neon", "Gold Royal", "Dark Hacker", "Purple Mythic", "Crimson Dragon"]

    def __init__(self, owner_id: int, on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(owner_id=owner_id)
        self.on_pick = on_pick
        for theme in self.THEMES:
            button = discord.ui.Button(label=theme, style=discord.ButtonStyle.secondary)

            async def callback(interaction: discord.Interaction, selected: str = theme) -> None:
                await self.on_pick(interaction, selected)

            button.callback = callback  # type: ignore[method-assign]
            self.add_item(button)


class RankCategoryView(discord.ui.View):
    """ปุ่มเลือกหมวด leaderboard"""

    def __init__(self, on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(timeout=300)
        self.on_pick = on_pick

    @discord.ui.button(label="🏆 รวมทั้งหมด", style=discord.ButtonStyle.primary)
    async def all(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "all")

    @discord.ui.button(label="🐍 Python", style=discord.ButtonStyle.secondary)
    async def python(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "python")

    @discord.ui.button(label="💻 C Language", style=discord.ButtonStyle.secondary)
    async def c_lang(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "c")

    @discord.ui.button(label="🔥 Streak", style=discord.ButtonStyle.secondary)
    async def streak(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "streak")

    @discord.ui.button(label="💰 Coins", style=discord.ButtonStyle.secondary)
    async def coins(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "coins")

    @discord.ui.button(label="🎯 Accuracy", style=discord.ButtonStyle.secondary)
    async def accuracy(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_pick(interaction, "accuracy")


class AdminPanelView(discord.ui.View):
    def __init__(
        self,
        on_add: Callable[[discord.Interaction], Any],
        on_edit: Callable[[discord.Interaction], Any],
        on_delete: Callable[[discord.Interaction], Any],
        on_manage_chapter: Callable[[discord.Interaction], Any],
        on_set_score: Callable[[discord.Interaction], Any],
        on_view_all: Callable[[discord.Interaction], Any],
        on_generate_ai: Callable[[discord.Interaction], Any],
        on_analytics: Callable[[discord.Interaction], Any],
    ) -> None:
        super().__init__(timeout=600)
        self._on_add = on_add
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._on_manage_chapter = on_manage_chapter
        self._on_set_score = on_set_score
        self._on_view_all = on_view_all
        self._on_generate_ai = on_generate_ai
        self._on_analytics = on_analytics

    @discord.ui.button(label="➕ เพิ่มโจทย์", style=discord.ButtonStyle.success)
    async def add(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_add(interaction)

    @discord.ui.button(label="✏️ แก้ไขโจทย์", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_edit(interaction)

    @discord.ui.button(label="🗑️ ลบโจทย์", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_delete(interaction)

    @discord.ui.button(label="📂 จัดการบทเรียน", style=discord.ButtonStyle.secondary)
    async def chapter(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_manage_chapter(interaction)

    @discord.ui.button(label="📊 ตั้งค่าคะแนน", style=discord.ButtonStyle.secondary)
    async def score(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_set_score(interaction)

    @discord.ui.button(label="👁️ ดูโจทย์ทั้งหมด", style=discord.ButtonStyle.secondary)
    async def view_all(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_view_all(interaction)

    @discord.ui.button(label="🤖 AI สร้างโจทย์", style=discord.ButtonStyle.success)
    async def ai(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_generate_ai(interaction)

    @discord.ui.button(label="📈 สถิติโจทย์", style=discord.ButtonStyle.primary)
    async def analytics(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._on_analytics(interaction)


class AdminSelectView(discord.ui.View):
    def __init__(self, options_payload: list[dict[str, str]], on_pick: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(timeout=300)
        self.add_item(TaskAdminDropdown(options_payload=options_payload, on_pick=on_pick))


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, on_confirm: Callable[[discord.Interaction], Any], on_cancel: Callable[[discord.Interaction], Any]) -> None:
        super().__init__(timeout=120)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

    @discord.ui.button(label="✅ ยืนยันลบ", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_confirm(interaction)

    @discord.ui.button(label="❎ ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_cancel(interaction)


def daily_reset_if_needed(user_data: dict[str, Any], today_iso: str | None = None) -> None:
    """รีเซ็ต daily progress หากเปลี่ยนวัน"""

    today = today_iso or date.today().isoformat()
    daily = user_data.setdefault("daily", {"date": "", "claimed": False, "week_day": 0})
    if daily.get("date") != today:
        daily["claimed"] = False


class SubmissionPreviewView(OwnerOnlyView):
    def __init__(
        self,
        owner_id: int,
        on_confirm: Callable[[discord.Interaction], Any],
        on_edit: Callable[[discord.Interaction], Any],
        on_hint: Callable[[discord.Interaction], Any],
        on_cancel: Callable[[discord.Interaction], Any],
    ) -> None:
        super().__init__(owner_id=owner_id)
        self.on_confirm = on_confirm
        self.on_edit = on_edit
        self.on_hint = on_hint
        self.on_cancel = on_cancel

    @discord.ui.button(label="✅ ตรวจคำตอบ", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_confirm(interaction)

    @discord.ui.button(label="✏️ แก้ไขใหม่", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_edit(interaction)

    @discord.ui.button(label="💡 Hint", style=discord.ButtonStyle.secondary)
    async def hint(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_hint(interaction)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self.on_cancel(interaction)
