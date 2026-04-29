"""โมดูลสร้างโจทย์อัตโนมัติ (Template AI Generator)"""

from __future__ import annotations

from random import choice


def generate_task(language: str, difficulty: str) -> dict:
    """สร้างโจทย์ตัวอย่างใหม่ตามภาษา/ความยาก"""

    language = language.lower()
    difficulty = difficulty.lower()

    templates = {
        "easy": {"title": "Sum Two Numbers", "description": "รับตัวเลข 2 จำนวน แล้วแสดงผลรวม", "accepted_outputs": ["15"], "hint": "ใช้การรับ input และบวกค่า", "testcases": [{"input": "7 8", "accepted_outputs": ["15"]}]},
        "medium": {"title": "Even Odd Checker", "description": "รับจำนวนเต็ม 1 ค่า แล้วแสดง EVEN หรือ ODD", "accepted_outputs": ["EVEN"], "hint": "ใช้ if-else และเครื่องหมาย %", "testcases": [{"input": "10", "accepted_outputs": ["EVEN"]}]},
        "hard": {"title": "Prime Detector", "description": "รับจำนวนเต็ม 1 ค่า แล้วแสดง PRIME หรือ NOT PRIME", "accepted_outputs": ["PRIME"], "hint": "ลองวนลูปหารตั้งแต่ 2 ถึง sqrt(n)", "testcases": [{"input": "13", "accepted_outputs": ["PRIME"]}]},
    }

    pack = templates.get(difficulty, templates["easy"])
    task_id = choice(range(1000, 9999))
    required = ["print"] if language == "python" else ["printf", "puts"]
    example = "print(a+b)" if language == "python" else "printf(\"%d\\n\", a+b);"

    return {
        "id": task_id,
        "title": pack["title"],
        "difficulty": difficulty,
        "exp": {"easy": 20, "medium": 50, "hard": 120}.get(difficulty, 20),
        "coins": {"easy": 5, "medium": 10, "hard": 20}.get(difficulty, 5),
        "description": pack["description"],
        "accepted_outputs": pack["accepted_outputs"],
        "required_keywords": required,
        "forbidden_keywords": ["goto"] if language == "c" else [],
        "hint": pack["hint"],
        "example_code": example,
        "testcases": pack["testcases"],
        "time_limit": 2,
        "memory_limit": 128,
    }
