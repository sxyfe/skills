#!/usr/bin/env python3
"""Generate transparent caption PNGs (rounded handwritten print defaults).

Usage:
  python make_captions.py --shots shots.json --out out/captions
  python make_captions.py --shots shots.json --out out/captions --font /path/to.ttf

shots.json example:
  [{"id": 1, "text": "第一句旁白。"}, {"id": 2, "text": "第二句\\n可两行。"}]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
DEFAULT_SIZE = 42
TOP_RATIO = 0.065
LINE_GAP_EXTRA = 18  # loose leading on top of glyph height
COLOR = (34, 34, 34, 255)
OUTLINE = (255, 255, 255, 200)

SKILL_ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = [
    SKILL_ROOT / "assets" / "fonts" / "ZCOOLKuaiLe-Regular.ttf",
    SKILL_ROOT / "assets" / "fonts" / "RoundedHandwrite.ttf",
    SKILL_ROOT / "assets" / "fonts" / "RoundedHandwrite.otf",
    Path("/Library/Fonts/站酷快乐体.ttf"),
    Path("/System/Library/Fonts/Supplemental/Kaiti.ttc"),
    Path("/System/Library/Fonts/Supplemental/Songti.ttc"),
]


def resolve_font(path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path))
    candidates.extend(FONT_CANDIDATES)
    for p in candidates:
        if not p.exists():
            continue
        try:
            if p.suffix.lower() == ".ttc":
                return ImageFont.truetype(str(p), size=size, index=0)
            return ImageFont.truetype(str(p), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_one(text: str, font: ImageFont.ImageFont) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = int(H * TOP_RATIO)
    for line in text.split("\n"):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (W - tw) // 2
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            draw.text((x + dx, y + dy), line, font=font, fill=OUTLINE)
        draw.text((x, y), line, font=font, fill=COLOR)
        y += th + LINE_GAP_EXTRA
    return img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", required=True, help="JSON list of {id,text}")
    ap.add_argument("--out", required=True, help="output directory for cap_XX.png")
    ap.add_argument("--font", default=None, help="override font path")
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    args = ap.parse_args()

    shots = json.loads(Path(args.shots).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    font = resolve_font(args.font, args.size)

    for item in shots:
        sid = int(item["id"])
        text = str(item["text"])
        path = out / f"cap_{sid:02d}.png"
        render_one(text, font).save(path)
        print(path)


if __name__ == "__main__":
    main()
