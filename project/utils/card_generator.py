"""สร้างภาพโปรไฟล์การ์ดด้วย Pillow"""

from __future__ import annotations

import random
from io import BytesIO
from pathlib import Path
from typing import Any

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = Path(__file__).resolve().parents[1]

RANK_THEMES = {
    "Bronze": {"bg_gradient": [(101, 67, 33), (139, 90, 43)], "accent": (205, 127, 50), "text": (255, 235, 205), "bar_fill": (205, 127, 50), "bar_empty": (80, 50, 20), "overlay": (0, 0, 0, 120)},
    "Silver": {"bg_gradient": [(70, 80, 90), (100, 110, 120)], "accent": (192, 192, 192), "text": (240, 240, 255), "bar_fill": (192, 192, 192), "bar_empty": (50, 60, 70), "overlay": (0, 0, 0, 100)},
    "Gold": {"bg_gradient": [(120, 80, 0), (180, 130, 10)], "accent": (255, 215, 0), "text": (255, 250, 200), "bar_fill": (255, 215, 0), "bar_empty": (80, 55, 0), "overlay": (0, 0, 0, 110)},
    "Platinum": {"bg_gradient": [(0, 80, 100), (0, 140, 160)], "accent": (100, 255, 240), "text": (220, 255, 255), "bar_fill": (100, 255, 240), "bar_empty": (0, 60, 80), "overlay": (0, 0, 0, 100)},
    "Diamond": {"bg_gradient": [(0, 50, 120), (30, 100, 200)], "accent": (80, 200, 255), "text": (210, 240, 255), "bar_fill": (80, 200, 255), "bar_empty": (0, 30, 80), "overlay": (0, 0, 0, 110)},
    "Master": {"bg_gradient": [(60, 0, 100), (120, 0, 180)], "accent": (200, 100, 255), "text": (240, 210, 255), "bar_fill": (200, 100, 255), "bar_empty": (40, 0, 70), "overlay": (0, 0, 0, 120)},
    "Legend": {"bg_gradient": [(150, 30, 0), (220, 80, 0)], "accent": (255, 120, 30), "text": (255, 240, 220), "bar_fill": (255, 150, 30), "bar_empty": (100, 20, 0), "overlay": (0, 0, 0, 130)},
}

_font_cache: dict[tuple[int, bool], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
_badge_cache: dict[str, Image.Image] = {}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    key = (size, bold)
    if key not in _font_cache:
        path = BASE / "assets" / "fonts" / ("bold.ttf" if bold else "regular.ttf")
        try:
            _font_cache[key] = ImageFont.truetype(str(path), size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


async def fetch_avatar(user: discord.User) -> Image.Image:
    try:
        avatar_url = user.display_avatar.with_size(128).url
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url, timeout=8) as resp:
                data = await resp.read()
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        return Image.new("RGBA", (128, 128), (120, 120, 120, 255))


def make_circle_avatar(avatar: Image.Image, size: int = 120, border_color: tuple[int, int, int] = (255, 215, 0), border_width: int = 4) -> Image.Image:
    avatar = avatar.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size + border_width * 2, size + border_width * 2), (0, 0, 0, 0))
    out.paste(avatar, (border_width, border_width), mask)
    draw = ImageDraw.Draw(out)
    draw.ellipse((0, 0, out.width - 1, out.height - 1), outline=border_color + (255,), width=border_width)
    return out


def create_gradient_bg(width: int, height: int, color_start: tuple[int, int, int], color_end: tuple[int, int, int]) -> Image.Image:
    base = Image.new("RGB", (width, height), color_start)
    draw = ImageDraw.Draw(base)
    for x in range(width):
        t = x / max(1, width - 1)
        r = int(color_start[0] * (1 - t) + color_end[0] * t)
        g = int(color_start[1] * (1 - t) + color_end[1] * t)
        b = int(color_start[2] * (1 - t) + color_end[2] * t)
        draw.line((x, 0, x, height), fill=(r, g, b))
    for _ in range(2000):
        px = random.randint(0, width - 1)
        py = random.randint(0, height - 1)
        noise = random.randint(-8, 8)
        r, g, b = base.getpixel((px, py))
        base.putpixel((px, py), (max(0, min(255, r + noise)), max(0, min(255, g + noise)), max(0, min(255, b + noise))))
    return base


def draw_progress_bar(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, progress: float, fill_color: tuple[int, int, int], empty_color: tuple[int, int, int], radius: int = 8) -> None:
    draw.rounded_rectangle((x, y, x + width, y + height), radius=radius, fill=empty_color)
    fill_w = int(max(0.0, min(1.0, progress)) * width)
    if fill_w > 0:
        draw.rounded_rectangle((x, y, x + fill_w, y + height), radius=radius, fill=fill_color)
        draw.rounded_rectangle((x, y, x + fill_w, y + height // 2), radius=radius, fill=(255, 255, 255, 40))


def draw_stats_grid(draw: ImageDraw.ImageDraw, img: Image.Image, stats: list[dict[str, str]], theme: dict[str, Any], x: int, y: int, width: int) -> None:
    box_w = width // 4 - 8
    for idx, stat in enumerate(stats):
        bx = x + idx * (box_w + 8)
        panel = Image.new("RGBA", (box_w, 76), (0, 0, 0, 100))
        img.paste(panel, (bx, y), panel)
        draw.rounded_rectangle((bx, y, bx + box_w, y + 76), radius=10, outline=theme["accent"] + (200,), width=2)
        draw.text((bx + 10, y + 8), stat["icon"], font=get_font(18, True), fill=theme["text"])
        draw.text((bx + 40, y + 8), stat["label"], font=get_font(14), fill=theme["text"])
        draw.text((bx + 10, y + 40), stat["value"], font=get_font(18, True), fill=theme["accent"])


def calc_exp_progress(exp: int, level: int) -> tuple[int, int, float]:
    current_base = max(0, (level - 1) * 100)
    next_base = level * 100
    current = max(0, exp - current_base)
    needed = max(1, next_base - current_base)
    return current, needed, min(1.0, current / needed)


def fmt_num(n: int) -> str:
    if n >= 10000:
        return f"{n // 1000}K"
    return f"{n:,}"


def generate_badge_fallback(rank: str) -> Image.Image:
    theme = RANK_THEMES.get(rank, RANK_THEMES["Bronze"])
    badge = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.ellipse((0, 0, 79, 79), fill=theme["accent"] + (255,))
    draw.ellipse((4, 4, 75, 75), outline=(255, 255, 255, 180), width=2)
    draw.text((30, 24), rank[0], font=get_font(28, True), fill=(0, 0, 0))
    return badge


def get_rank_badge(rank: str) -> Image.Image:
    if rank not in _badge_cache:
        path = BASE / "assets" / "rank_badges" / f"{rank.lower()}.png"
        try:
            _badge_cache[rank] = Image.open(path).convert("RGBA").resize((80, 80))
        except Exception:
            _badge_cache[rank] = generate_badge_fallback(rank)
    return _badge_cache[rank]


async def generate_profile_card(user: discord.User, user_data: dict[str, Any]) -> BytesIO:
    rank = str(user_data.get("rank", "Bronze"))
    theme = RANK_THEMES.get(rank, RANK_THEMES["Bronze"])
    bg = create_gradient_bg(900, 300, theme["bg_gradient"][0], theme["bg_gradient"][1]).convert("RGBA")
    overlay = Image.new("RGBA", bg.size, theme["overlay"])
    bg.alpha_composite(overlay)
    draw = ImageDraw.Draw(bg)

    avatar = await fetch_avatar(user)
    avatar_circle = make_circle_avatar(avatar, border_color=theme["accent"])
    glow = Image.new("RGBA", avatar_circle.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((2, 2, avatar_circle.width - 2, avatar_circle.height - 2), fill=theme["accent"] + (90,))
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    bg.alpha_composite(glow, (26, 26))
    bg.alpha_composite(avatar_circle, (30, 30))

    coding_exp = int(user_data.get("coding_exp", user_data.get("exp", 0)))
    coding_level = int(user_data.get("coding_level", max(1, coding_exp // 100 + 1)))
    chat_level = int(user_data.get("chat_level", max(1, int(user_data.get("chat_exp", 0)) // 100 + 1)))
    current, needed, ratio = calc_exp_progress(coding_exp, coding_level)

    draw.text((180, 38), user.display_name, font=get_font(32, True), fill=theme["text"])
    draw.text((180, 78), f"Lv.{coding_level} Coding  •  Lv.{chat_level} Chat", font=get_font(20), fill=theme["accent"])
    draw.text((180, 118), f"⭐ EXP {fmt_num(current)} / {fmt_num(needed)}", font=get_font(18), fill=theme["text"])
    draw_progress_bar(draw, 180, 150, 470, 24, ratio, theme["bar_fill"], theme["bar_empty"])
    draw.text((660, 150), f"{int(ratio * 100)}%", font=get_font(16, True), fill=theme["text"])

    accuracy = int((int(user_data.get("tasks_cleared", 0)) / max(1, int(user_data.get("tasks_attempted", 1)))) * 100)
    stats = [
        {"icon": "🪙", "label": "Coins", "value": fmt_num(int(user_data.get("coins", 0)))},
        {"icon": "✅", "label": "Tasks", "value": str(user_data.get("tasks_cleared", 0))},
        {"icon": "🔥", "label": "Streak", "value": f"{user_data.get('streak', 0)} Days"},
        {"icon": "🎯", "label": "Acc", "value": f"{accuracy}%"},
    ]
    draw_stats_grid(draw, bg, stats, theme, 180, 205, 660)

    bg.alpha_composite(get_rank_badge(rank), (790, 20))

    output = BytesIO()
    bg.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output
