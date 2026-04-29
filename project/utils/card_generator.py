"""สร้างการ์ดโปรไฟล์ด้วย Pillow"""

from __future__ import annotations

import random
from io import BytesIO
from pathlib import Path

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    key = (size, bold)
    if key not in _font_cache:
        path = ASSETS / "fonts" / ("bold.ttf" if bold else "regular.ttf")
        try:
            _font_cache[key] = ImageFont.truetype(str(path), size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


async def fetch_avatar(user: discord.User) -> Image.Image:
    try:
        avatar_url = user.display_avatar.with_size(128).url
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url, timeout=10) as resp:
                data = await resp.read()
        return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        return Image.new("RGBA", (128, 128), (90, 90, 90, 255))


def make_circle_avatar(avatar: Image.Image, size: int = 120, border_color: tuple[int, int, int] = (255, 215, 0), border_width: int = 4) -> Image.Image:
    avatar = avatar.resize((size, size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size + border_width * 2, size + border_width * 2), (0, 0, 0, 0))
    out.paste(avatar, (border_width, border_width), mask)
    draw = ImageDraw.Draw(out)
    draw.ellipse((0, 0, out.width - 1, out.height - 1), outline=border_color + (255,), width=border_width)
    return out


def create_gradient_bg(width: int, height: int, color_start: tuple[int, int, int], color_end: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    for x in range(width):
        t = x / max(1, width - 1)
        r = int(color_start[0] + (color_end[0] - color_start[0]) * t)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * t)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * t)
        draw.line((x, 0, x, height), fill=(r, g, b))
    for _ in range(500):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        c = random.randint(-8, 8)
        rr, gg, bb = img.getpixel((x, y))
        img.putpixel((x, y), (max(0, min(255, rr + c)), max(0, min(255, gg + c)), max(0, min(255, bb + c))))
    return img


def draw_progress_bar(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, height: int, progress: float, fill_color: tuple[int, int, int], empty_color: tuple[int, int, int], radius: int = 8) -> None:
    draw.rounded_rectangle((x, y, x + width, y + height), radius=radius, fill=empty_color)
    fill_width = int(width * max(0.0, min(1.0, progress)))
    if fill_width > 0:
        draw.rounded_rectangle((x, y, x + fill_width, y + height), radius=radius, fill=fill_color)
        shine = tuple(min(255, int(ch * 1.2)) for ch in fill_color)
        draw.rounded_rectangle((x + 2, y + 2, x + fill_width - 2, y + height // 2), radius=radius, fill=shine)


def draw_stats_grid(draw: ImageDraw.ImageDraw, img: Image.Image, stats: list[dict[str, str]], theme: dict, x: int, y: int, width: int) -> None:
    box_w, gap = (width - 30) // 4, 10
    for idx, item in enumerate(stats[:4]):
        bx = x + idx * (box_w + gap)
        overlay = Image.new("RGBA", (box_w, 80), (0, 0, 0, 110))
        img.paste(overlay, (bx, y), overlay)
        draw.rounded_rectangle((bx, y, bx + box_w, y + 80), radius=10, outline=theme["accent"], width=2)
        draw.text((bx + 10, y + 8), f"{item['icon']} {item['label']}", font=get_font(16, True), fill=theme["text"])
        draw.text((bx + 10, y + 42), item["value"], font=get_font(20, True), fill=theme["accent"])


def calc_exp_progress(exp: int, level: int) -> tuple[int, int, float]:
    base = max(0, (level - 1) * 100)
    need = 100
    cur = max(0, exp - base)
    return cur, need, min(1.0, cur / max(1, need))


def fmt_num(n: int) -> str:
    if n >= 10000:
        return f"{n//1000}K"
    return f"{n:,}"


def generate_badge_fallback(rank: str) -> Image.Image:
    theme = RANK_THEMES.get(rank, RANK_THEMES["Bronze"])
    badge = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.ellipse((4, 4, 76, 76), fill=theme["accent"] + (240,), outline=(255, 255, 255, 220), width=3)
    draw.text((30, 25), rank[:1], font=get_font(28, True), fill=(0, 0, 0))
    return badge


def get_rank_badge(rank: str) -> Image.Image:
    if rank not in _badge_cache:
        path = ASSETS / "rank_badges" / f"{rank.lower()}.png"
        try:
            _badge_cache[rank] = Image.open(path).convert("RGBA").resize((80, 80))
        except Exception:
            _badge_cache[rank] = generate_badge_fallback(rank)
    return _badge_cache[rank]


async def generate_profile_card(user: discord.User, user_data: dict) -> BytesIO:
    rank = str(user_data.get("rank", "Bronze"))
    theme = RANK_THEMES.get(rank, RANK_THEMES["Bronze"])
    bg = create_gradient_bg(900, 300, theme["bg_gradient"][0], theme["bg_gradient"][1]).convert("RGBA")
    overlay = Image.new("RGBA", (900, 300), theme["overlay"])
    bg.alpha_composite(overlay)
    draw = ImageDraw.Draw(bg)

    avatar = await fetch_avatar(user)
    circle = make_circle_avatar(avatar, border_color=theme["accent"])
    glow = circle.filter(ImageFilter.GaussianBlur(3))
    bg.paste(glow, (24, 24), glow)
    bg.paste(circle, (30, 30), circle)

    coding_lv = int(user_data.get("coding_level", 1))
    chat_lv = int(user_data.get("chat_level", 1))
    coding_exp = int(user_data.get("coding_exp", 0))
    cur, need, ratio = calc_exp_progress(coding_exp, coding_lv)

    draw.text((180, 30), user.display_name, font=get_font(34, True), fill=theme["text"])
    draw.text((180, 72), f"Lv.{coding_lv} Coding  •  Lv.{chat_lv} Chat", font=get_font(20), fill=theme["text"])
    draw.text((180, 108), f"⭐ EXP {fmt_num(cur)} / {fmt_num(need)}", font=get_font(18), fill=theme["text"])
    draw_progress_bar(draw, 180, 140, 520, 24, ratio, theme["bar_fill"], theme["bar_empty"])
    draw.text((710, 140), f"{int(ratio*100)}%", font=get_font(18, True), fill=theme["text"])

    accuracy = (int(user_data.get("tasks_cleared", 0)) / max(1, int(user_data.get("tasks_attempted", 0)))) * 100
    stats = [
        {"icon": "🪙", "label": "Coins", "value": fmt_num(int(user_data.get('coins', 0)))},
        {"icon": "✅", "label": "Tasks", "value": str(int(user_data.get('tasks_cleared', 0)))},
        {"icon": "🔥", "label": "Streak", "value": f"{int(user_data.get('streak', 0))} Days"},
        {"icon": "🎯", "label": "Acc", "value": f"{accuracy:.0f}%"},
    ]
    draw_stats_grid(draw, bg, stats, theme, 180, 200, 680)
    badge = get_rank_badge(rank)
    bg.paste(badge, (790, 20), badge)

    out = BytesIO()
    bg.save(out, format="PNG")
    out.seek(0)
    return out
