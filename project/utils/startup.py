"""ระบบตรวจสอบความพร้อมก่อนบอทเริ่มทำงาน"""

from __future__ import annotations

from pathlib import Path


def ensure_runtime_ready(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    required_files = [data_dir / "assignments.json", data_dir / "users.json"]
    for path in required_files:
        if not path.exists():
            path.write_text("{}", encoding="utf-8")
