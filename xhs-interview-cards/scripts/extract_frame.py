#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


def which_or_die(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"找不到 {name}，请先安装")
    return path


def video_duration(video: Path) -> float:
    ffprobe = which_or_die("ffprobe")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout or "{}")
    return float(data.get("format", {}).get("duration") or 0)


def parse_time(value: object) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace(",", ".")
    parts = text.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except ValueError:
        return None


def card_requested_time(card: dict) -> float | None:
    for key in ("time", "timestamp", "start"):
        parsed = parse_time(card.get(key))
        if parsed is not None:
            return parsed
    return None


def spread_unique_times(times: list[float], duration: float, min_gap: float) -> list[float]:
    lo, hi = 1.0, max(1.0, duration - 1.0)
    out: list[float] = []
    for raw in times:
        t = min(max(raw, lo), hi)
        if any(abs(t - prev) < min_gap for prev in out):
            found: float | None = None
            limit = max(1, int(duration) + 1)
            for delta in range(1, limit):
                for cand in (t + delta, t - delta):
                    if lo <= cand <= hi and all(abs(cand - prev) >= min_gap for prev in out):
                        found = float(cand)
                        break
                if found is not None:
                    break
            if found is not None:
                t = found
        out.append(t)
    return out


def resolve_card_times(cards: list[dict], duration: float) -> list[float]:
    n = max(1, len(cards))
    min_gap = max(3.0, min(8.0, duration / max(n * 2, 1)))
    requested: list[float] = []
    for i, card in enumerate(cards):
        t = card_requested_time(card)
        if t is None:
            t = duration * (0.10 + 0.80 * (i + 0.5) / n)
        requested.append(t)
    return spread_unique_times(requested, duration, min_gap)


def extract_frame(video: Path, out: Path, timestamp: str | None = None, percent: float = 0.2) -> Path:
    ffmpeg = which_or_die("ffmpeg")
    if not timestamp:
        duration = video_duration(video)
        seconds = max(1.0, duration * percent) if duration > 0 else 8.0
        timestamp = f"{seconds:.2f}"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        timestamp,
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not out.exists():
        raise SystemExit(result.stderr[-2000:] or "截帧失败")
    return out


def extract_frame_image(video: Path, seconds: float) -> Image.Image:
    ffmpeg = which_or_die("ffmpeg")
    timestamp = f"{max(0.0, seconds):.2f}"
    cmd = [
        ffmpeg,
        "-ss",
        timestamp,
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-",
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        err = (result.stderr or b"").decode("utf-8", errors="ignore")[-2000:]
        raise SystemExit(err or f"截帧失败: {timestamp}s")
    return Image.open(io.BytesIO(result.stdout)).convert("RGB")


def _signature(im: Image.Image) -> list[int]:
    return list(im.convert("L").resize((64, 36), Image.Resampling.BILINEAR).getdata())


def _mse(a: list[int], b: list[int]) -> float:
    if not a or len(a) != len(b):
        return 0.0
    return sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)


def extract_distinct_card_images(
    video: Path,
    cards: list[dict],
    min_mse: float = 18.0,
) -> list[Image.Image]:
    duration = video_duration(video)
    if duration <= 0:
        raise SystemExit("无法读取视频时长，不能按金句时段截帧")
    bases = resolve_card_times(cards, duration)
    offsets = (0.0, 1.6, -1.6, 3.2, -3.2, 5.0, 8.0, -5.0, 12.0, -8.0)
    images: list[Image.Image] = []
    used: list[list[int]] = []
    lo, hi = 1.0, max(1.0, duration - 1.0)
    for base in bases:
        chosen: Image.Image | None = None
        chosen_sig: list[int] | None = None
        best: tuple[float, Image.Image, list[int]] | None = None
        for offset in offsets:
            t = min(max(base + offset, lo), hi)
            im = extract_frame_image(video, t)
            sig = _signature(im)
            if not used:
                chosen, chosen_sig = im, sig
                break
            score = min(_mse(sig, prev) for prev in used)
            if best is None or score > best[0]:
                best = (score, im, sig)
            if score >= min_mse:
                chosen, chosen_sig = im, sig
                break
        if chosen is None and best is not None:
            chosen, chosen_sig = best[1], best[2]
        if chosen is None or chosen_sig is None:
            chosen = extract_frame_image(video, base)
            chosen_sig = _signature(chosen)
        images.append(chosen)
        used.append(chosen_sig)
    return images


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="从视频截取一帧")
    parser.add_argument("--video", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--time", default=None, help="如 00:01:12 或秒数")
    parser.add_argument("--percent", type=float, default=0.2)
    args = parser.parse_args()
    path = extract_frame(Path(args.video), Path(args.out), args.time, args.percent)
    print(path)
    sys.stdout.flush()
