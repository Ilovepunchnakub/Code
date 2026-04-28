"""Modal components สำหรับส่งโค้ดและจัดการโจทย์"""

from __future__ import annotations

from typing import Any, Callable

import discord


class SubmitCodeModal(discord.ui.Modal, title="ส่งคำตอบของคุณ"):
    """Modal รับโค้ดจากผู้เรียน"""

    code_input = discord.ui.TextInput(
        label="วางโค้ดของคุณที่นี่...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000,
    )

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, str], Any]) -> None:
        super().__init__(timeout=300)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """ส่งโค้ดต่อไปยัง handler กลาง"""

        await self.on_submit_handler(interaction, str(self.code_input.value))


class AddTaskModal(discord.ui.Modal, title="➕ เพิ่มโจทย์ใหม่"):
    """Modal เพิ่มโจทย์ใหม่แบบครบฟิลด์หลัก"""

    language = discord.ui.TextInput(label="ภาษา (python/c)", required=True, max_length=10)
    chapter = discord.ui.TextInput(label="Chapter key (เช่น chapter1)", required=True, max_length=20)
    title_input = discord.ui.TextInput(label="ชื่อโจทย์", required=True, max_length=100)
    difficulty = discord.ui.TextInput(label="Difficulty (easy/medium/hard)", required=True, max_length=10)
    description = discord.ui.TextInput(label="คำอธิบาย", style=discord.TextStyle.paragraph, required=True, max_length=600)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, str]], Any]) -> None:
        super().__init__(timeout=300)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """เก็บข้อมูลพื้นฐานแล้วส่งต่อไปสร้างโจทย์"""

        payload = {
            "language": str(self.language.value).strip().lower(),
            "chapter": str(self.chapter.value).strip(),
            "title": str(self.title_input.value).strip(),
            "difficulty": str(self.difficulty.value).strip().lower(),
            "description": str(self.description.value).strip(),
        }
        await self.on_submit_handler(interaction, payload)


class EditTaskModal(discord.ui.Modal, title="✏️ แก้ไขโจทย์"):
    """Modal แก้ไขฟิลด์หลักของโจทย์"""

    title_input = discord.ui.TextInput(label="ชื่อโจทย์ใหม่", required=False, max_length=100)
    description = discord.ui.TextInput(label="คำอธิบายใหม่", style=discord.TextStyle.paragraph, required=False, max_length=600)
    difficulty = discord.ui.TextInput(label="Difficulty ใหม่", required=False, max_length=10)
    accepted_output = discord.ui.TextInput(label="Accepted Output ใหม่", required=False, max_length=200)

    def __init__(self, on_submit_handler: Callable[[discord.Interaction, dict[str, str]], Any]) -> None:
        super().__init__(timeout=300)
        self.on_submit_handler = on_submit_handler

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """ส่งข้อมูลที่แก้ไขแล้วให้ service"""

        payload = {
            "title": str(self.title_input.value).strip(),
            "description": str(self.description.value).strip(),
            "difficulty": str(self.difficulty.value).strip().lower(),
            "accepted_output": str(self.accepted_output.value).strip(),
        }
        await self.on_submit_handler(interaction, payload)
