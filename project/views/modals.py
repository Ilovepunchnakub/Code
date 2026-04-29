"""Modal components สำหรับส่งโค้ดและจัดการโจทย์แบบหลายหน้า"""

from __future__ import annotations

from typing import Any, Callable

import discord


class SubmitCodeModal(discord.ui.Modal):
    code_input = discord.ui.TextInput(label="วางโค้ดของคุณที่นี่...", style=discord.TextStyle.paragraph, required=True, max_length=4000)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, str], Any], language: str = "python") -> None:
        title = "🧠 เขียนเฉพาะใน main()" if language == "c" else "🧠 เขียนคำสั่ง Python"
        super().__init__(title=title, timeout=300)
        self.on_submit_handler = on_submit_handler
        if language == "c":
            self.code_input.placeholder = "printf(\"Hello World\");"
        else:
            self.code_input.placeholder = "print(\"Hello World\")"

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.on_submit_handler(interaction, str(self.code_input.value))


class AddTaskPageOneModal(discord.ui.Modal, title="➕ เพิ่มโจทย์ - หน้า 1/3"):
    language = discord.ui.TextInput(label="ภาษา (c / python)", required=True, max_length=10)
    chapter = discord.ui.TextInput(label="Chapter (เช่น chapter1)", required=True, max_length=30)
    task_title = discord.ui.TextInput(label="ชื่อโจทย์", required=True, max_length=120)
    difficulty = discord.ui.TextInput(label="Difficulty (easy/medium/hard)", required=True, max_length=10)
    exp = discord.ui.TextInput(label="EXP", required=True, max_length=10)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            payload = {
                "language": str(self.language.value).strip().lower(),
                "chapter": str(self.chapter.value).strip(),
                "title": str(self.task_title.value).strip(),
                "difficulty": str(self.difficulty.value).strip().lower(),
                "exp": int(str(self.exp.value).strip() or "20"),
            }
            if payload["language"] not in {"c", "python"}:
                raise ValueError("ภาษาใช้ได้เฉพาะ c หรือ python")
            await self.on_submit_handler(interaction, payload)
        except Exception as exc:
            await interaction.response.send_message(f"⚠️ ข้อมูลหน้า 1 ไม่ถูกต้อง: {exc}", ephemeral=True)


class AddTaskPageTwoModal(discord.ui.Modal, title="➕ เพิ่มโจทย์ - หน้า 2/3"):
    description_input = discord.ui.TextInput(label="คำอธิบายโจทย์", style=discord.TextStyle.paragraph, required=True, max_length=1000)
    hint = discord.ui.TextInput(label="Hint", required=False, max_length=300)
    example_code = discord.ui.TextInput(label="Example Code", style=discord.TextStyle.paragraph, required=False, max_length=1200)
    coins = discord.ui.TextInput(label="Coins Reward", required=True, max_length=10)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            payload = {
                "description": str(self.description_input.value).strip(),
                "hint": str(self.hint.value).strip(),
                "example_code": str(self.example_code.value).strip(),
                "coins": int(str(self.coins.value).strip() or "5"),
            }
            await self.on_submit_handler(interaction, payload)
        except Exception as exc:
            await interaction.response.send_message(f"⚠️ ข้อมูลหน้า 2 ไม่ถูกต้อง: {exc}", ephemeral=True)


class AddTaskPageThreeModal(discord.ui.Modal, title="➕ เพิ่มโจทย์ - หน้า 3/3"):
    accepted_outputs = discord.ui.TextInput(label="Accepted Outputs (คั่นด้วย ,)", style=discord.TextStyle.paragraph, required=True, max_length=1200)
    required_keywords = discord.ui.TextInput(label="Required Keywords (คั่นด้วย ,)", required=False, max_length=300)
    forbidden_keywords = discord.ui.TextInput(label="Forbidden Keywords (คั่นด้วย ,)", required=False, max_length=300)
    time_limit = discord.ui.TextInput(label="Time Limit (วินาที)", required=True, max_length=10)
    memory_limit = discord.ui.TextInput(label="Memory Limit (MB)", required=True, max_length=10)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            payload = {
                "accepted_outputs": [v.strip() for v in str(self.accepted_outputs.value).split(",") if v.strip()],
                "required_keywords": [v.strip() for v in str(self.required_keywords.value).split(",") if v.strip()],
                "forbidden_keywords": [v.strip() for v in str(self.forbidden_keywords.value).split(",") if v.strip()],
                "time_limit": int(str(self.time_limit.value).strip() or "2"),
                "memory_limit": int(str(self.memory_limit.value).strip() or "128"),
            }
            await self.on_submit_handler(interaction, payload)
        except Exception as exc:
            await interaction.response.send_message(f"⚠️ ข้อมูลหน้า 3 ไม่ถูกต้อง: {exc}", ephemeral=True)


class EditSimpleModal(discord.ui.Modal):
    value_input = discord.ui.TextInput(label="ค่าใหม่", style=discord.TextStyle.paragraph, required=True, max_length=1500)

    def __init__(self, title: str, label: str, on_submit_handler: Callable[[discord.Interaction, str], Any], value: str = "") -> None:
        super().__init__(title=title, timeout=300)
        self.value_input.label = label
        self.value_input.default = value[:1500]
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.on_submit_handler(interaction, str(self.value_input.value).strip())


class EditRewardModal(discord.ui.Modal, title="⭐ แก้ไขรางวัล"):
    exp = discord.ui.TextInput(label="EXP", required=True, max_length=10)
    coins = discord.ui.TextInput(label="Coins", required=True, max_length=10)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, int]], Any], exp_default: int, coins_default: int) -> None:
        super().__init__(timeout=300)
        self.exp.default = str(exp_default)
        self.coins.default = str(coins_default)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.on_submit_handler(interaction, {"exp": int(str(self.exp.value)), "coins": int(str(self.coins.value))})


class EditJudgeModal(discord.ui.Modal, title="⚙️ แก้ไข Judge"):
    accepted_outputs = discord.ui.TextInput(label="Accepted Outputs (คั่นด้วย ,)", style=discord.TextStyle.paragraph, required=True, max_length=1200)
    required_keywords = discord.ui.TextInput(label="Required Keywords (คั่นด้วย ,)", required=False, max_length=300)
    forbidden_keywords = discord.ui.TextInput(label="Forbidden Keywords (คั่นด้วย ,)", required=False, max_length=300)
    time_limit = discord.ui.TextInput(label="Time Limit", required=True, max_length=10)
    memory_limit = discord.ui.TextInput(label="Memory Limit", required=True, max_length=10)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any], task: dict[str, Any]) -> None:
        super().__init__(timeout=300)
        self.accepted_outputs.default = ", ".join(task.get("accepted_outputs", []))[:1200]
        self.required_keywords.default = ", ".join(task.get("required_keywords", []))[:300]
        self.forbidden_keywords.default = ", ".join(task.get("forbidden_keywords", []))[:300]
        self.time_limit.default = str(task.get("time_limit", 2))
        self.memory_limit.default = str(task.get("memory_limit", 128))
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.on_submit_handler(
            interaction,
            {
                "accepted_outputs": [v.strip() for v in str(self.accepted_outputs.value).split(",") if v.strip()],
                "required_keywords": [v.strip() for v in str(self.required_keywords.value).split(",") if v.strip()],
                "forbidden_keywords": [v.strip() for v in str(self.forbidden_keywords.value).split(",") if v.strip()],
                "time_limit": int(str(self.time_limit.value)),
                "memory_limit": int(str(self.memory_limit.value)),
            },
        )


class BulkImportModal(discord.ui.Modal, title="📥 Bulk Import Chapter"):
    language = discord.ui.TextInput(label="ภาษา (c / python)", required=True, max_length=10)
    chapter = discord.ui.TextInput(label="Chapter Key", required=True, max_length=30)
    title_input = discord.ui.TextInput(label="Chapter Title", required=True, max_length=100)
    tasks_json = discord.ui.TextInput(label="Tasks JSON (list)", style=discord.TextStyle.paragraph, required=True, max_length=3900)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        payload = {
            "language": str(self.language.value).strip().lower(),
            "chapter": str(self.chapter.value).strip(),
            "title": str(self.title_input.value).strip(),
            "tasks_json": str(self.tasks_json.value),
        }
        await self.on_submit_handler(interaction, payload)
