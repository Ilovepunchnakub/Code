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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(deepcopy(self.default_data))

    def load(self) -> dict[str, Any]:
        with self._lock:
            with self.path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def save(self, data: dict[str, Any]) -> None:
        with self._lock:
            with self.path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)


class AssignmentStore(JsonDatabase):
    """คลาสดูแลข้อมูลโจทย์เรียนเขียนโปรแกรม"""

    SCHEMA_VERSION = 3

    def __init__(self, path: Path) -> None:
        default_data = {
            "schema_version": self.SCHEMA_VERSION,
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
                            "required_keywords": ["print"],
                            "forbidden_keywords": ["import os"],
                            "hint": "ใช้ฟังก์ชัน print()",
                            "example_code": "print('Hello World')",
                            "testcases": [{"input": "", "accepted_outputs": ["Hello World", "hello world"]}],
                            "time_limit": 2,
                            "memory_limit": 128,
                            "compare_mode": "normalized",
                            "float_tolerance": 1e-6,
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
                            "required_keywords": ["printf", "puts"],
                            "forbidden_keywords": ["goto"],
                            "hint": "ใช้ printf() หรือ puts()",
                            "example_code": "#include <stdio.h>\nint main(){printf(\"Hello C\\n\");}",
                            "testcases": [{"input": "", "accepted_outputs": ["Hello C", "hello c"]}],
                            "time_limit": 2,
                            "memory_limit": 128,
                            "compare_mode": "normalized",
                            "float_tolerance": 1e-6,
                        }
                    ],
                }
            },
        }
        super().__init__(path=path, default_data=default_data)

    def load(self) -> dict[str, Any]:
        data = super().load()
        normalized = self.normalize_schema(data)
        if normalized != data:
            super().save(normalized)
        return normalized

    def save(self, data: dict[str, Any]) -> None:
        super().save(self.normalize_schema(data))

    def normalize_schema(self, data: dict[str, Any]) -> dict[str, Any]:
        raw = deepcopy(data)
        raw["schema_version"] = self.SCHEMA_VERSION

        for language, chapters in list(raw.items()):
            if language == "schema_version" or not isinstance(chapters, dict):
                continue
            for chapter_key, chapter_data in chapters.items():
                if not isinstance(chapter_data, dict):
                    chapters[chapter_key] = {"title": chapter_key, "number": 1, "locked_level": 1, "tasks": []}
                    continue
                tasks = chapter_data.get("tasks", [])
                normalized_tasks = []
                for task in tasks:
                    t = dict(task)
                    if "required_keywords_any" in t and "required_keywords" not in t:
                        t["required_keywords"] = t.pop("required_keywords_any")
                    if "time_limit_sec" in t and "time_limit" not in t:
                        t["time_limit"] = t.pop("time_limit_sec")
                    if "memory_limit_mb" in t and "memory_limit" not in t:
                        t["memory_limit"] = t.pop("memory_limit_mb")

                    t.pop("required_keywords_any", None)
                    t.pop("time_limit_sec", None)
                    t.pop("memory_limit_mb", None)

                    # unify reward fields
                    if "xp" not in t and "exp" in t:
                        t["xp"] = int(t.get("exp", 20))
                    if "exp" not in t and "xp" in t:
                        t["exp"] = int(t.get("xp", 20))
                    if "coins" not in t:
                        t["coins"] = 5

                    # unify answer fields for redesigned schema
                    accepted_outputs = t.get("accepted_outputs", [""])
                    if "main_answer" not in t:
                        t["main_answer"] = str(accepted_outputs[0]) if accepted_outputs else ""
                    if "alt_answers" not in t:
                        t["alt_answers"] = [str(v) for v in accepted_outputs[1:5]]
                    all_answers = [t["main_answer"], *[str(v) for v in t.get("alt_answers", []) if str(v).strip()]]
                    t["accepted_outputs"] = [item for item in all_answers if item.strip()] or [""]

                    t.setdefault("required_keywords", [])
                    t.setdefault("forbidden_keywords", [])
                    t.setdefault("testcases", [{"input": "", "accepted_outputs": t["accepted_outputs"]}])
                    t.setdefault("time_limit", 2)
                    t.setdefault("memory_limit", 128)
                    t.setdefault("compare_mode", "normalized")
                    t.setdefault("float_tolerance", 1e-6)
                    t.setdefault("show_solution", True)
                    t.setdefault("daily_limit", 0)
                    t.setdefault("bonus_first_try_xp", 0)
                    t.setdefault("output_example", "")
                    t.setdefault("tags", [])
                    normalized_tasks.append(t)
                chapter_data["tasks"] = normalized_tasks
                chapter_data.setdefault("title", chapter_key)
                if "number" not in chapter_data:
                    suffix = "".join(ch for ch in str(chapter_key) if ch.isdigit())
                    chapter_data["number"] = int(suffix) if suffix else 1
                chapter_data.setdefault("locked_level", 1)

        return raw


class UserStore(JsonDatabase):
    """คลาสดูแลข้อมูลผู้ใช้ เกม และความคืบหน้า"""

    def __init__(self, path: Path) -> None:
        super().__init__(path=path, default_data={"schema_version": 1})

    def ensure_user(self, user_id: int, name: str) -> dict[str, Any]:
        data = self.load()
        data.setdefault("schema_version", 1)
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
        data = self.load()
        data[str(user_id)] = user_data
        self.save(data)
