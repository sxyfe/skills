#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


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
