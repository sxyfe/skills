#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def fetch_video(url: str, out: Path) -> Path:
    yt = shutil.which("yt-dlp")
    if not yt:
        raise SystemExit("找不到 yt-dlp。请改用本地视频文件，或先安装 yt-dlp")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        yt,
        "--no-playlist",
        "--no-warnings",
        "--restrict-filenames",
        "-f",
        "bv*[height<=1080]+ba/b[height<=1080]/b",
        "--merge-output-format",
        "mp4",
        "-o",
        str(out),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "公开页下载失败，请改用本地视频。\n"
            + (result.stderr or result.stdout or "")[-2000:]
        )
    if not out.exists():
        matches = list(out.parent.glob(out.stem + ".*"))
        if matches:
            return matches[0]
        raise SystemExit("下载结束但没找到视频文件")
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="下载已确认的公开访谈视频")
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    print(fetch_video(args.url, Path(args.out)))
