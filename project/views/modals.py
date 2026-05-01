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
    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler
        self.language = discord.ui.TextInput(label="ภาษา (c / python)", required=True, max_length=10, placeholder="c หรือ python")
        self.chapter = discord.ui.TextInput(label="Chapter (เช่น chapter1)", required=True, max_length=30, placeholder="chapter1")
        self.task_title = discord.ui.TextInput(label="ชื่อโจทย์", required=True, max_length=120)
        self.difficulty = discord.ui.TextInput(label="Difficulty (easy/medium/hard)", required=True, max_length=10, placeholder="easy")
        self.exp = discord.ui.TextInput(label="EXP", required=True, max_length=10, placeholder="20")
        for item in (self.language, self.chapter, self.task_title, self.difficulty, self.exp):
            self.add_item(item)

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
    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler
        self.description_input = discord.ui.TextInput(label="คำอธิบายโจทย์", style=discord.TextStyle.paragraph, required=True, max_length=1000)
        self.hint_input = discord.ui.TextInput(label="Hint", required=False, max_length=300)
        self.example_code = discord.ui.TextInput(label="Example Code", style=discord.TextStyle.paragraph, required=False, max_length=1200)
        self.coins = discord.ui.TextInput(label="Coins Reward", required=True, max_length=10, placeholder="5")
        for item in (self.description_input, self.hint_input, self.example_code, self.coins):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            payload = {
                "description": str(self.description_input.value).strip(),
                "hint": str(self.hint_input.value).strip(),
                "example_code": str(self.example_code.value).strip(),
                "coins": int(str(self.coins.value).strip() or "5"),
            }
            await self.on_submit_handler(interaction, payload)
        except Exception as exc:
            await interaction.response.send_message(f"⚠️ ข้อมูลหน้า 2 ไม่ถูกต้อง: {exc}", ephemeral=True)


class AddTaskPageThreeModal(discord.ui.Modal, title="➕ เพิ่มโจทย์ - หน้า 3/3"):
    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler
        self.accepted_outputs = discord.ui.TextInput(label="Accepted Outputs (คั่นด้วย ,)", style=discord.TextStyle.paragraph, required=True, max_length=1200)
        self.required_keywords = discord.ui.TextInput(label="Required Keywords (คั่นด้วย ,)", required=False, max_length=300)
        self.forbidden_keywords = discord.ui.TextInput(label="Forbidden Keywords (คั่นด้วย ,)", required=False, max_length=300)
        self.time_limit = discord.ui.TextInput(label="Time Limit (วินาที)", required=True, max_length=10, placeholder="2")
        self.memory_limit = discord.ui.TextInput(label="Memory Limit (MB)", required=True, max_length=10, placeholder="128")
        for item in (self.accepted_outputs, self.required_keywords, self.forbidden_keywords, self.time_limit, self.memory_limit):
            self.add_item(item)

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


class เพิ่มโจทย์หน้า1โมดัล(discord.ui.Modal, title="เพิ่มโจทย์ • หน้า 1/3"):
    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler
        self.language = discord.ui.TextInput(label="ภาษา (c หรือ python)", required=True, max_length=10, placeholder="c")
        self.chapter_title = discord.ui.TextInput(label="ชื่อบทเรียน", required=True, max_length=120, placeholder="พื้นฐานภาษา C")
        self.chapter_number = discord.ui.TextInput(label="บทเรียนที่เท่าไหร่", required=True, max_length=3, placeholder="1")
        self.task_title = discord.ui.TextInput(label="ชื่อโจทย์", required=True, max_length=120, placeholder="Hello World")
        self.xp = discord.ui.TextInput(label="XP ที่ได้รับ", required=True, max_length=10, placeholder="20")
        for item in (self.language, self.chapter_title, self.chapter_number, self.task_title, self.xp):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        payload = {
            "language": str(self.language.value).strip().lower(),
            "chapter_title": str(self.chapter_title.value).strip(),
            "chapter_number": int(str(self.chapter_number.value).strip()),
            "task_title": str(self.task_title.value).strip(),
            "xp": int(str(self.xp.value).strip()),
        }
        if payload["language"] not in {"c", "python"}:
            raise ValueError("ภาษาใช้ได้เฉพาะ c หรือ python")
        await self.on_submit_handler(interaction, payload)


class เพิ่มโจทย์หน้า2โมดัล(discord.ui.Modal, title="เพิ่มโจทย์ • หน้า 2/3"):
    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler
        self.description = discord.ui.TextInput(label="รายละเอียดโจทย์", style=discord.TextStyle.paragraph, required=True, max_length=1200)
        self.hint = discord.ui.TextInput(label="Hint", required=False, max_length=300, placeholder="ใช้ printf()")
        self.difficulty = discord.ui.TextInput(label="ระดับความยาก (ง่าย/กลาง/ยาก)", required=True, max_length=10, placeholder="ง่าย")
        self.output_example = discord.ui.TextInput(label="ตัวอย่าง Output", required=False, max_length=500, placeholder="Hello World")
        self.tags = discord.ui.TextInput(label="Tag (คั่นด้วย ,)", required=False, max_length=300, placeholder="printf, พื้นฐาน")
        for item in (self.description, self.hint, self.difficulty, self.output_example, self.tags):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        payload = {
            "description": str(self.description.value).strip(),
            "hint": str(self.hint.value).strip(),
            "difficulty": str(self.difficulty.value).strip(),
            "output_example": str(self.output_example.value).strip(),
            "tags": [item.strip() for item in str(self.tags.value).split(",") if item.strip()],
        }
        await self.on_submit_handler(interaction, payload)


class เพิ่มโจทย์หน้า3โมดัล(discord.ui.Modal, title="เพิ่มโจทย์ • หน้า 3/3"):
    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, Any]], Any]) -> None:
        super().__init__(timeout=600)
        self.on_submit_handler = on_submit_handler
        self.main_answer = discord.ui.TextInput(label="คำตอบหลัก (โค้ดเต็ม)", style=discord.TextStyle.paragraph, required=True, max_length=3000)
        self.alt1 = discord.ui.TextInput(label="คำตอบอื่นที่ถูก #1", required=False, max_length=500)
        self.alt2 = discord.ui.TextInput(label="คำตอบอื่นที่ถูก #2", required=False, max_length=500)
        self.alt3 = discord.ui.TextInput(label="คำตอบอื่นที่ถูก #3", required=False, max_length=500)
        self.alt4 = discord.ui.TextInput(label="คำตอบอื่นที่ถูก #4", required=False, max_length=500)
        for item in (self.main_answer, self.alt1, self.alt2, self.alt3, self.alt4):
            self.add_item(item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        payload = {
            "main_answer": str(self.main_answer.value).strip(),
            "alt_answers": [v for v in [str(self.alt1.value).strip(), str(self.alt2.value).strip(), str(self.alt3.value).strip(), str(self.alt4.value).strip()] if v],
        }
        await self.on_submit_handler(interaction, payload)
