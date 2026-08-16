#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}
BILI_HOSTS = {"bilibili.com", "www.bilibili.com", "m.bilibili.com", "b23.tv", "www.b23.tv"}


def detect_source(value: str) -> str:
    path = Path(value).expanduser()
    if path.exists() and path.is_file():
        return "local"
    text = value.strip()
    if re.fullmatch(r"BV[0-9A-Za-z]+", text):
        return "bilibili"
    host = (urlparse(text).hostname or "").lower()
    if host in YOUTUBE_HOSTS or host.endswith(".youtube.com"):
        return "youtube"
    if host in BILI_HOSTS or host.endswith(".bilibili.com"):
        return "bilibili"
    raise SystemExit(f"无法判断来源（需要 YouTube / B 站链接，或本地视频文件）: {value}")


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cleaned = re.sub(r"\n{3,}", "\n\n", text.strip()) + "\n"
    path.write_text(cleaned, encoding="utf-8")
    return path


def parse_clock(value: str) -> float:
    text = value.strip().replace(",", ".")
    parts = text.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def srt_or_vtt_to_segments(path: Path) -> list[tuple[float, float, str]]:
    segments: list[tuple[float, float, str]] = []
    start = end = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal start, end, buf
        text = re.sub(r"<[^>]+>", "", " ".join(buf)).strip()
        if start is not None and end is not None and text:
            if not segments or segments[-1][2] != text:
                segments.append((start, end, text))
        start = end = None
        buf = []

    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
            if not line:
                flush()
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if "-->" in line:
            flush()
            left, right = line.split("-->", 1)
            right = right.split(" ")[0]
            try:
                start = parse_clock(left)
                end = parse_clock(right)
            except ValueError:
                start = end = None
            continue
        buf.append(line)
    flush()
    return segments


def srt_or_vtt_to_text(path: Path) -> str:
    return "\n".join(text for _, _, text in srt_or_vtt_to_segments(path))


def timed_text(segments: list[tuple[float, float, str]]) -> str:
    return "\n".join(f"[{start:7.2f} -> {end:7.2f}] {text}" for start, end, text in segments)


def write_transcript_pair(out_dir: Path, plain: str, timed: str | None = None) -> Path:
    dest = write_text(out_dir / "transcript.txt", plain)
    if timed:
        write_text(out_dir / "transcript-timed.txt", timed)
    return dest


def find_first(out_dir: Path, names: list[str]) -> Path | None:
    for name in names:
        hits = sorted(out_dir.rglob(name))
        if hits:
            return hits[0]
    return None


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def transcript_from_youtube(url: str, out_dir: Path, baoyu_dir: Path) -> dict[str, str]:
    bun = shutil.which("bun")
    script = baoyu_dir / "scripts" / "main.ts"
    if not bun or not script.exists():
        raise SystemExit("找不到 baoyu-youtube-transcript（需要 bun 和 scripts/main.ts）")
    out_dir.mkdir(parents=True, exist_ok=True)
    result = run(
        [
            bun,
            str(script),
            url,
            "--languages",
            "zh,zh-Hans,zh-CN,en",
            "--output-dir",
            str(out_dir),
        ]
    )
    if result.returncode != 0:
        raise SystemExit((result.stderr or result.stdout or "YouTube 字幕提取失败")[-2000:])
    md = find_first(out_dir, ["transcript.md"])
    if not md:
        raise SystemExit("baoyu-youtube-transcript 跑完了，但没有 transcript.md")
    dest = write_transcript_pair(out_dir, md.read_text(encoding="utf-8"))
    return {"source": "baoyu-youtube-transcript", "transcript": str(dest), "raw": str(md)}


def transcript_from_ytdlp_subs(url: str, out_dir: Path) -> dict[str, str]:
    yt = shutil.which("yt-dlp")
    if not yt:
        raise SystemExit("找不到 yt-dlp")
    out_dir.mkdir(parents=True, exist_ok=True)
    tmpl = str(out_dir / "source.%(ext)s")
    result = run(
        [
            yt,
            "--no-playlist",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-format",
            "vtt",
            "--sub-langs",
            "zh.*,zh,en.*",
            "-o",
            tmpl,
            url,
        ]
    )
    if result.returncode != 0:
        raise SystemExit((result.stderr or result.stdout or "yt-dlp 拉字幕失败")[-2000:])
    vtts = sorted(out_dir.glob("*.vtt"))
    if not vtts:
        raise SystemExit("这条视频没有可下载的字幕轨")
    preferred = [p for p in vtts if ".zh" in p.name.lower()] or vtts
    raw = preferred[0]
    segs = srt_or_vtt_to_segments(raw)
    dest = write_transcript_pair(out_dir, "\n".join(t for _, _, t in segs), timed_text(segs))
    return {"source": "yt-dlp-subs", "transcript": str(dest), "raw": str(raw)}


def transcript_from_parser(url: str, out_dir: Path, parser_dir: Path, skip_asr: bool) -> dict[str, str]:
    env = os.environ.copy()
    src = str(parser_dir / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    env["PATH"] = "/usr/local/bin:/opt/homebrew/bin:" + env.get("PATH", "")
    cmd = [
        "python3",
        "-m",
        "video_subtitle_parser",
        url,
        "--platform",
        "auto",
        "--out-dir",
        str(out_dir),
    ]
    if skip_asr:
        cmd.append("--skip-asr")
    result = run(cmd, env=env)
    if result.returncode != 0:
        raise SystemExit((result.stderr or result.stdout or "video-subtitle-parser 失败")[-2000:])
    hits = sorted(out_dir.glob("*_transcript_turbo_clean.txt"))
    clean = hits[0] if hits else find_first(out_dir, ["*_transcript_turbo_clean.txt"])
    if not clean:
        raise SystemExit("video-subtitle-parser 没有产出 *_transcript_turbo_clean.txt（多半没有字幕，且 ASR 未启用）")
    dest = write_transcript_pair(out_dir, clean.read_text(encoding="utf-8"))
    timed_src = find_first(out_dir, ["*_segments_clean.md", "*.vtt", "*.srt"])
    if timed_src and timed_src.suffix.lower() in {".vtt", ".srt"}:
        write_text(out_dir / "transcript-timed.txt", timed_text(srt_or_vtt_to_segments(timed_src)))
    return {
        "source": "video-subtitle-parser",
        "transcript": str(dest),
        "raw": str(clean),
    }


def extract_embedded_subs(video: Path, out_dir: Path) -> Path | None:
    probe = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,codec_name",
            "-of",
            "json",
            str(video),
        ]
    )
    if probe.returncode != 0:
        return None
    data = json.loads(probe.stdout or "{}")
    subs = [s for s in data.get("streams") or [] if s.get("codec_type") == "subtitle"]
    if not subs:
        return None
    srt = out_dir / "embedded.srt"
    result = run(
        ["ffmpeg", "-y", "-i", str(video), "-map", "0:s:0", str(srt)]
    )
    if result.returncode != 0 or not srt.exists() or srt.stat().st_size == 0:
        return None
    return srt


def transcript_from_local(video: Path, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    embedded = extract_embedded_subs(video, out_dir)
    if embedded:
        segs = srt_or_vtt_to_segments(embedded)
        dest = write_transcript_pair(out_dir, "\n".join(t for _, _, t in segs), timed_text(segs))
        return {"source": "ffmpeg-embedded-subs", "transcript": str(dest), "raw": str(embedded)}

    try:
        import mlx_whisper  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "本地视频没有内嵌字幕。音频转写需要 mlx-whisper。\n"
            "在 Apple Silicon 上安装：python3 -m pip install mlx-whisper\n"
            "或改用带字幕的 YouTube / B 站链接。"
        ) from exc

    audio = out_dir / "audio.wav"
    extract = run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(audio),
        ]
    )
    if extract.returncode != 0:
        raise SystemExit(extract.stderr[-2000:] if extract.stderr else "抽取音轨失败")
    result = mlx_whisper.transcribe(str(audio), language="zh", verbose=False)
    text = (result.get("text") or "").strip()
    if not text and result.get("segments"):
        text = "\n".join(
            (seg.get("text") or "").strip()
            for seg in result["segments"]
            if (seg.get("text") or "").strip()
        )
    if not text:
        raise SystemExit("mlx-whisper 没有转写出文本")
    timed_lines = []
    for seg in result.get("segments") or []:
        piece = (seg.get("text") or "").strip()
        if piece:
            timed_lines.append(f"[{float(seg.get('start') or 0):7.2f} -> {float(seg.get('end') or 0):7.2f}] {piece}")
    dest = write_transcript_pair(out_dir, text, "\n".join(timed_lines) if timed_lines else None)
    return {"source": "mlx-whisper", "transcript": str(dest), "raw": str(audio)}


def fetch_transcript(source: str, out_dir: Path, cfg: dict) -> dict[str, str]:
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    kind = detect_source(source)
    skills = cfg.get("skills") or {}
    baoyu = Path(skills.get("baoyu_youtube_transcript") or "").expanduser()
    parser = Path(skills.get("video_subtitle_parser") or "").expanduser()

    if kind == "youtube":
        errors: list[str] = []
        try:
            return transcript_from_youtube(source, out_dir / "youtube", baoyu)
        except SystemExit as exc:
            errors.append(str(exc))
        if parser.exists():
            try:
                return transcript_from_parser(source, out_dir / "parser", parser, skip_asr=True)
            except SystemExit as exc:
                errors.append(str(exc))
        try:
            return transcript_from_ytdlp_subs(source, out_dir / "ytdlp")
        except SystemExit as exc:
            errors.append(str(exc))
            raise SystemExit("YouTube 文稿提取失败:\n" + "\n---\n".join(errors)) from exc

    if kind == "bilibili":
        errors = []
        if parser.exists():
            try:
                return transcript_from_parser(source, out_dir / "parser", parser, skip_asr=True)
            except SystemExit as exc:
                errors.append(str(exc))
        try:
            return transcript_from_ytdlp_subs(source, out_dir / "ytdlp")
        except SystemExit as exc:
            errors.append(str(exc))
            raise SystemExit("B 站文稿提取失败:\n" + "\n---\n".join(errors)) from exc

    return transcript_from_local(Path(source).expanduser().resolve(), out_dir / "local")


if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ledger import load_config

    skill_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="抽取 YouTube / B 站 / 本地视频文稿")
    parser.add_argument("--url", default=None)
    parser.add_argument("--video", default=None)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    source = args.url or args.video
    if not source:
        raise SystemExit("需要 --url 或 --video")
    info = fetch_transcript(source, Path(args.out_dir), load_config(skill_dir))
    print(json.dumps(info, ensure_ascii=False, indent=2))
