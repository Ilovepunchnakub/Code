"""โมดูลจัดการข้อมูล JSON สำหรับ assignments และ users แบบปลอดภัย"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Any


class JsonDatabase:
    """คลาสฐานสำหรับอ่าน/เขียนไฟล์ JSON พร้อม lock กันข้อมูลชนกัน"""

    def __init__(self, path: Path, default_data: dict[str, Any]) -> None:
        self.path = path
        self.default_data = default_data
        self._lock = Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """สร้างไฟล์เริ่มต้นหากยังไม่มี"""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(deepcopy(self.default_data))

    def load(self) -> dict[str, Any]:
        """อ่านข้อมูล JSON ปัจจุบันจากไฟล์"""

        with self._lock:
            with self.path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def save(self, data: dict[str, Any]) -> None:
        """เขียนข้อมูล JSON ลงไฟล์แบบจัดรูปอ่านง่าย"""

        with self._lock:
            with self.path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)


class AssignmentStore(JsonDatabase):
    """คลาสดูแลข้อมูลโจทย์เรียนเขียนโปรแกรม"""

    def __init__(self, path: Path) -> None:
        default_data = {
            "python": {
                "chapter1": {
                    "title": "พื้นฐาน Python",
                    "locked_level": 1,
                    "tasks": [
                        {
                            "id": 1,
                            "title": "Hello World",
                            "difficulty": "easy",
                            "exp": 20,
                            "coins": 5,
                            "description": "แสดงคำว่า Hello World",
                            "accepted_outputs": ["Hello World", "hello world", "HELLO WORLD"],
                            "required_keywords_any": ["print"],
                            "forbidden_keywords": ["import os"],
                            "hint": "ใช้ฟังก์ชัน print()",
                            "example_code": "print('Hello World')",
                            "testcases": [{"input": "", "accepted_outputs": ["Hello World", "hello world"]}],
                            "time_limit_sec": 2,
                            "memory_limit_mb": 128,
                        }
                    ],
                }
            },
            "c": {
                "chapter1": {
                    "title": "พื้นฐานภาษา C",
                    "locked_level": 1,
                    "tasks": [
                        {
                            "id": 1,
                            "title": "Hello C",
                            "difficulty": "easy",
                            "exp": 20,
                            "coins": 5,
                            "description": "แสดงคำว่า Hello C",
                            "accepted_outputs": ["Hello C", "hello c"],
                            "required_keywords_any": ["printf", "puts"],
                            "forbidden_keywords": ["goto"],
                            "hint": "ใช้ printf() หรือ puts()",
                            "example_code": "#include <stdio.h>\nint main(){printf(\"Hello C\\n\");}",
                            "testcases": [{"input": "", "accepted_outputs": ["Hello C", "hello c"]}],
                            "time_limit_sec": 2,
                            "memory_limit_mb": 128,
                        }
                    ],
                }
            },
        }
        super().__init__(path=path, default_data=default_data)


class UserStore(JsonDatabase):
    """คลาสดูแลข้อมูลผู้ใช้ เกม และความคืบหน้า"""

    def __init__(self, path: Path) -> None:
        super().__init__(path=path, default_data={})

    def ensure_user(self, user_id: int, name: str) -> dict[str, Any]:
        """สร้างโปรไฟล์ผู้ใช้หากยังไม่มี แล้วคืนข้อมูลล่าสุด"""

        data = self.load()
        key = str(user_id)
        if key not in data:
            data[key] = {
                "user_id": user_id,
                "name": name,
                "level": 1,
                "exp": 0,
                "rank": "Bronze",
                "coins": 0,
                "completed_tasks": {},
                "daily_streak": 0,
                "badges": [],
                "combo_count": 0,
                "attempted": 0,
                "correct": 0,
                "wrong_submissions": 0,
                "used_hint_count": 0,
                "viewed_chapters": [],
                "languages_cleared": {"python": 0, "c": 0},
                "difficulty_clears": {"easy": 0, "medium": 0, "hard": 0},
                "achievements": [],
                "daily": {"date": "", "claimed": False, "week_day": 0},
                "login": {"last_date": "", "consecutive_days": 0, "total_days": 0},
                "inventory": {"titles": [], "boost_until": "", "save_streak": 0, "profile_theme": "Blue Neon"},
                "stats": {
                    "first_try_clear": 0,
                    "no_hint_clear": 0,
                    "perfect_output": 0,
                    "retry_after_fail": 0,
                    "first_submission_done": False,
                    "first_fail_done": False,
                    "started_at": date.today().isoformat(),
                },
            }
            self.save(data)
        return data[key]

    def update_user(self, user_id: int, user_data: dict[str, Any]) -> None:
        """อัปเดตข้อมูลผู้ใช้รายคน"""

        data = self.load()
        data[str(user_id)] = user_data
        self.save(data)
