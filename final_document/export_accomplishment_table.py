#!/usr/bin/env python3
"""Render the accomplishment table as a transparent PNG for poster.md."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "accomplishment_table.png"

HEADERS = ("成就名稱", "內容", "分數")
ROWS = (
    ("終場清道夫", "協助關主場復", "50分"),
    (
        "全隊到齊",
        "全隊以足球先發陣容的形式合影，並手持紀念旗（可向關主索取範例照片）",
        "50分",
    ),
)

# Column widths in px (name, description, points)
COL_WIDTHS = (150, 520, 72)
PAD_X = 14
PAD_Y = 10
ROW_H = 44
HEADER_H = 38
BORDER = "#bdbdbd"
HEADER_BG = "#e8f5e9"
HEADER_FG = "#1b5e20"
TEXT_FG = "#212121"
FONT_CANDIDATES = (
    "PingFang TC",
    "Heiti TC",
    "Songti TC",
    "STHeiti",
    "Arial Unicode MS",
)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for family in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(family, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines or [""]


def render() -> Path:
    font_header = _load_font(18, bold=True)
    font_body = _load_font(16)
    font_body_sm = _load_font(15)

    width = sum(COL_WIDTHS) + 2
    # Measure wrapped second row
    tmp = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(tmp)
    wrapped = _wrap(tdraw, ROWS[1][1], font_body_sm, COL_WIDTHS[1] - 2 * PAD_X)
    row2_h = max(ROW_H, PAD_Y * 2 + len(wrapped) * 22)
    height = HEADER_H + ROW_H + row2_h + 2

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x = 0
    # Header
    for i, (title, w) in enumerate(zip(HEADERS, COL_WIDTHS)):
        draw.rectangle([x, 0, x + w, HEADER_H], fill=HEADER_BG, outline=BORDER)
        draw.text((x + PAD_X, 9), title, fill=HEADER_FG, font=font_header)
        x += w

    # Row 1
    y1 = HEADER_H
    x = 0
    for i, (cell, w) in enumerate(zip(ROWS[0], COL_WIDTHS)):
        draw.rectangle([x, y1, x + w, y1 + ROW_H], fill=(0, 0, 0, 0), outline=BORDER)
        font = font_body if i != 2 else font_body
        draw.text((x + PAD_X, y1 + 11), cell, fill=TEXT_FG, font=font)
        x += w

    # Row 2 (wrapped description)
    y2 = y1 + ROW_H
    x = 0
    for i, (cell, w) in enumerate(zip(ROWS[1], COL_WIDTHS)):
        draw.rectangle([x, y2, x + w, y2 + row2_h], fill=(0, 0, 0, 0), outline=BORDER)
        if i == 1:
            ty = y2 + PAD_Y
            for line in wrapped:
                draw.text((x + PAD_X, ty), line, fill=TEXT_FG, font=font_body_sm)
                ty += 22
        else:
            draw.text((x + PAD_X, y2 + 11), cell, fill=TEXT_FG, font=font_body)
        x += w

    img.save(OUT, "PNG")
    return OUT


if __name__ == "__main__":
    path = render()
    print(f"Wrote {path}")
