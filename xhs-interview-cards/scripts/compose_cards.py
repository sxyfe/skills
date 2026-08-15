#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

FONT_CANDIDATES = [
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("/System/Library/Fonts/STHeiti Light.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),
    ("/Library/Fonts/Arial Unicode.ttf", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf", 0),
    ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    last_error: Exception | None = None
    for path, index in FONT_CANDIDATES:
        if not Path(path).exists():
            continue
        try:
            return ImageFont.truetype(path, size=size, index=index)
        except OSError as exc:
            last_error = exc
    raise SystemExit(f"找不到中文字体: {last_error}")


def cover_crop(im: Image.Image, width: int, height: int, y_bias: float = 0.22) -> Image.Image:
    scale = max(width / im.width, height / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - width) // 2)
    max_top = max(0, nh - height)
    top = int(max_top * y_bias)
    return im.crop((left, top, left + width, top + height))


def wrap_line(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if font.getlength(text) <= max_width:
        return [text]
    lines: list[str] = []
    buf = ""
    for ch in text:
        trial = buf + ch
        if font.getlength(trial) <= max_width:
            buf = trial
        else:
            if buf:
                lines.append(buf)
            buf = ch
    if buf:
        lines.append(buf)
    return lines


def fit_font(text: str, max_width: int, start: int, min_size: int = 28) -> ImageFont.FreeTypeFont:
    for size in range(start, min_size - 1, -1):
        font = load_font(size)
        if font.getlength(text) <= max_width:
            return font
    return load_font(min_size)


def darken(im: Image.Image, factor: float = 0.42) -> Image.Image:
    return ImageEnhance.Brightness(im).enhance(factor)


def draw_centered(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, font: ImageFont.FreeTypeFont) -> None:
    x0, y0, x1, y1 = box
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = x0 + (x1 - x0 - tw) // 2 - bbox[0]
    y = y0 + (y1 - y0 - th) // 2 - bbox[1]
    for dx, dy in ((2, 2), (1, 1), (-1, 1), (1, -1)):
        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))


def compose_card(
    source: Image.Image,
    lines: list[str],
    canvas: tuple[int, int] = (1080, 1440),
    hero_ratio: float = 0.36,
) -> Image.Image:
    width, height = canvas
    hero_h = int(height * hero_ratio)
    strip_area = height - hero_h
    n = max(1, len(lines))
    strip_h = strip_area // n
    remainder = strip_area - strip_h * n

    # 横屏访谈：人物帧铺满上方主图，不要先裁成 3:4 再切头顶
    hero = cover_crop(source, width, hero_h, y_bias=0.38)
    strip_src = darken(cover_crop(source, width, strip_h, y_bias=0.72), 0.5)
    strip_src = strip_src.filter(ImageFilter.GaussianBlur(radius=0.6))

    canvas_im = Image.new("RGB", (width, height), (8, 8, 8))
    canvas_im.paste(hero, (0, 0))
    y = hero_h
    for i, line in enumerate(lines):
        h = strip_h + (remainder if i == n - 1 else 0)
        band = strip_src.resize((width, h), Image.Resampling.LANCZOS).convert("RGBA")
        overlay = Image.new("RGBA", (width, h), (0, 0, 0, 118))
        merged = Image.alpha_composite(band, overlay).convert("RGB")
        canvas_im.paste(merged, (0, y))
        draw = ImageDraw.Draw(canvas_im)
        font = fit_font(line, width - 96, start=42 if i == 0 else 38)
        draw_centered(draw, (48, y, width - 48, y + h), line, font)
        y += h
    return canvas_im


def flatten_card(card: dict) -> list[str]:
    lines: list[str] = []
    header = (card.get("header") or "").strip()
    if header:
        lines.append(header)
    for raw in card.get("lines") or []:
        text = str(raw).strip()
        if text:
            lines.append(text)
    font = load_font(38)
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap_line(line, font, 1080 - 96))
    if len(wrapped) < 8:
        raise SystemExit(f"切片行数太少（{len(wrapped)}），请拆成 8～12 行短句")
    if len(wrapped) > 14:
        wrapped = wrapped[:14]
    return wrapped


def compose_from_json(frame_path: Path, cards_path: Path, out_dir: Path, canvas=(1080, 1440), hero_ratio=0.36) -> list[Path]:
    source = Image.open(frame_path).convert("RGB")
    payload = json.loads(cards_path.read_text(encoding="utf-8"))
    cards = payload.get("cards") if isinstance(payload, dict) else payload
    if not cards:
        raise SystemExit("cards.json 里没有 cards")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, card in enumerate(cards, start=1):
        lines = flatten_card(card)
        image = compose_card(source, lines, canvas=canvas, hero_ratio=hero_ratio)
        path = out_dir / f"{i:02d}.png"
        image.save(path, "PNG", optimize=True)
        written.append(path)
    return written


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="一帧切成花卷式访谈金句图")
    parser.add_argument("--frame", required=True)
    parser.add_argument("--cards", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1440)
    parser.add_argument("--hero-ratio", type=float, default=0.36)
    args = parser.parse_args()
    paths = compose_from_json(
        Path(args.frame),
        Path(args.cards),
        Path(args.out_dir),
        canvas=(args.width, args.height),
        hero_ratio=args.hero_ratio,
    )
    for path in paths:
        print(path)
    sys.stdout.flush()
