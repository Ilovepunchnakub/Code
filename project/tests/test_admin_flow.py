from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from cogs.admin import AdminCog
from utils.database import AssignmentStore


def _sample_task() -> dict:
    return {
        "id": 1,
        "title": "T1",
        "description": "desc",
        "difficulty": "easy",
        "exp": 20,
        "coins": 5,
        "accepted_outputs": ["ok"],
        "required_keywords": [],
        "forbidden_keywords": [],
        "hint": "h",
        "example_code": "",
        "time_limit": 2,
        "memory_limit": 128,
        "testcases": [{"input": "", "accepted_outputs": ["ok"]}],
    }


def test_apply_edit_reward_and_judge() -> None:
    cog = AdminCog(bot=object())
    task = _sample_task()
    cog._apply_task_edit(task, "reward", {"exp": 99, "coins": 11})
    assert task["exp"] == 99 and task["coins"] == 11

    cog._apply_task_edit(
        task,
        "judge",
        {
            "accepted_outputs": ["A", "B"],
            "required_keywords": ["print"],
            "forbidden_keywords": ["os.system"],
            "time_limit": 3,
            "memory_limit": 256,
        },
    )
    assert task["accepted_outputs"] == ["A", "B"]
    assert task["time_limit"] == 3
    assert task["main_answer"] == "A"
    assert task["alt_answers"] == ["B"]

    cog._apply_task_edit(task, "main_answer", "MAIN")
    assert task["accepted_outputs"][0] == "MAIN"

    cog._apply_task_edit(task, "alt_answers", "X\nY")
    assert task["alt_answers"] == ["X", "Y"]


def test_assignment_store_schema_migration(tmp_path: Path) -> None:
    path = tmp_path / "assignments.json"
    store = AssignmentStore(path)
    data = store.load()
    task = data["python"]["chapter1"]["tasks"][0]
    task.pop("required_keywords", None)
    task.pop("time_limit", None)
    task.pop("memory_limit", None)
    task["required_keywords_any"] = ["print"]
    task["time_limit_sec"] = 7
    task["memory_limit_mb"] = 64
    store.save(data)

    migrated = store.load()
    task = migrated["python"]["chapter1"]["tasks"][0]
    assert "required_keywords_any" not in task
    assert "time_limit_sec" not in task
    assert task["time_limit"] == 7


def test_assignment_store_new_schema_fields(tmp_path: Path) -> None:
    path = tmp_path / "assignments.json"
    store = AssignmentStore(path)
    data = store.load()
    task = data["c"]["chapter1"]["tasks"][0]
    task.pop("xp", None)
    task["exp"] = 42
    task["accepted_outputs"] = ["A", "B", "C"]
    task.pop("main_answer", None)
    task.pop("alt_answers", None)
    data["c"]["chapter1"].pop("number", None)
    store.save(data)

    migrated = store.load()
    t = migrated["c"]["chapter1"]["tasks"][0]
    assert t["xp"] == 42 and t["exp"] == 42
    assert t["main_answer"] == "A"
    assert t["alt_answers"][:2] == ["B", "C"]
    assert migrated["c"]["chapter1"]["number"] == 1


def test_diff_preview_output() -> None:
    cog = AdminCog(bot=object())
    before = _sample_task()
    after = deepcopy(before)
    after["title"] = "T2"
    diff = cog._build_diff_text(before, after)
    assert "title" in diff and "T1" in diff and "T2" in diff
