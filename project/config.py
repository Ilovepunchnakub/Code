"""ค่าคอนฟิกและตัวช่วยอ่าน ENV สำหรับบอท"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BOT_NAME = "Coding Arena Bot"
BOT_VERSION = "v2.1"

COLORS = {
    "main": 0x1A237E,
    "success": 0x2E7D32,
    "warning": 0xF57F17,
    "error": 0xC62828,
    "info": 0x0288D1,
    "premium": 0x6A0DAD,
}

EMOJIS = {
    "c": "💻",
    "python": "🐍",
    "exp": "⭐",
    "coins": "🪙",
    "hint": "💡",
    "pass": "✅",
    "fail": "❌",
    "error": "⚠️",
    "streak": "🔥",
    "rank": "🏆",
}


@dataclass(frozen=True, slots=True)
class AppSettings:
    token: str
    app_env: str
    data_dir: Path
    auto_sync_commands: bool


def _to_bool(raw: str | None, default: bool = True) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_token() -> str:
    for key in ("DISCORD_TOKEN", "DISCORD_BOT_TOKEN", "BOT_TOKEN"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    raise RuntimeError("ไม่พบ Discord Token กรุณาตั้งค่า DISCORD_TOKEN หรือ DISCORD_BOT_TOKEN หรือ BOT_TOKEN")


def load_settings() -> AppSettings:
    data_dir_raw = os.getenv("BOT_DATA_DIR", "").strip()
    data_dir = Path(data_dir_raw).resolve() if data_dir_raw else Path(__file__).resolve().parent
    return AppSettings(
        token=_resolve_token(),
        app_env=os.getenv("APP_ENV", "development").strip().lower(),
        data_dir=data_dir,
        auto_sync_commands=_to_bool(os.getenv("AUTO_SYNC_COMMANDS"), default=True),
    )
