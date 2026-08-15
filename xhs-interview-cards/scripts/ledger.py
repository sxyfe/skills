#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


SKILL_SEARCH_ROOTS = (
    ".claude/skills",
    ".cursor/skills",
    ".codex/skills",
    ".agents/skills",
    ".openclaw/skills",
    ".qclaw/skills",
)


def discover_skill(name: str) -> str | None:
    home = Path.home()
    for root in SKILL_SEARCH_ROOTS:
        path = home / root / name
        if path.exists():
            return str(path.resolve())
    return None


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(skill_dir: Path) -> dict[str, Any]:
    cfg: dict[str, Any] = {
        "content_root": str(Path.home() / "xhs-interview-cards-output"),
        "canvas": [1080, 1440],
        "hero_ratio": 0.36,
        "cooldown_days": 7,
        "skills": {},
    }
    for name in ("config.json", "config.local.json"):
        path = skill_dir / name
        if path.exists():
            cfg = _merge(cfg, json.loads(path.read_text(encoding="utf-8")))
    env_root = os.environ.get("XHS_INTERVIEW_CONTENT_ROOT")
    if env_root:
        cfg["content_root"] = env_root
    skills = cfg.setdefault("skills", {})
    if not skills.get("baoyu_youtube_transcript"):
        found = discover_skill("baoyu-youtube-transcript")
        if found:
            skills["baoyu_youtube_transcript"] = found
    if not skills.get("video_subtitle_parser"):
        found = discover_skill("video-subtitle-parser")
        if found:
            skills["video_subtitle_parser"] = found
    return cfg


def content_root(cfg: dict[str, Any]) -> Path:
    return Path(cfg["content_root"]).expanduser()


def ledger_path(cfg: dict[str, Any]) -> Path:
    return content_root(cfg) / "_ledger.json"


def load_ledger(cfg: dict[str, Any]) -> dict[str, Any]:
    path = ledger_path(cfg)
    if not path.exists():
        return {
            "version": 1,
            "cooldown_days": int(cfg.get("cooldown_days", 7)),
            "entries": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(cfg: dict[str, Any], ledger: dict[str, Any]) -> None:
    path = ledger_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


_PUNCT = dict.fromkeys(map(ord, "，。！？、；：""''《》【】（）—…·,.!?;:\"'()[]{}"), None)


def normalize_quote(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.translate(_PUNCT)
    text = re.sub(r"\s+", "", text)
    return text.lower()


def quotes_overlap(a: str, b: str, min_len: int = 8) -> bool:
    na, nb = normalize_quote(a), normalize_quote(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if len(na) >= min_len and len(nb) >= min_len:
        return na in nb or nb in na
    return False


def used_quotes(ledger: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for entry in ledger.get("entries", []):
        out.extend(entry.get("quotes") or [])
    return out


def colliding_quotes(candidates: list[str], ledger: dict[str, Any]) -> list[tuple[str, str]]:
    existing = used_quotes(ledger)
    hits: list[tuple[str, str]] = []
    for c in candidates:
        for e in existing:
            if quotes_overlap(c, e):
                hits.append((c, e))
                break
    return hits


def parse_day(value: str) -> date:
    return date.fromisoformat(value[:10])


def on_cooldown(
    ledger: dict[str, Any],
    account: str,
    person: str,
    today: date | None = None,
) -> dict[str, Any] | None:
    today = today or date.today()
    days = int(ledger.get("cooldown_days") or 7)
    person_n = normalize_quote(person)
    latest: dict[str, Any] | None = None
    latest_day: date | None = None
    for entry in ledger.get("entries", []):
        if entry.get("account") != account:
            continue
        if normalize_quote(entry.get("person") or "") != person_n:
            continue
        try:
            d = parse_day(entry.get("date") or "")
        except ValueError:
            continue
        if latest_day is None or d > latest_day:
            latest_day = d
            latest = entry
    if latest_day is None or latest is None:
        return None
    until = latest_day + timedelta(days=days)
    if today < until:
        return {
            "entry": latest,
            "last_date": latest_day.isoformat(),
            "until": until.isoformat(),
            "days_left": (until - today).days,
        }
    return None


def slug_title(text: str, max_len: int = 36) -> str:
    text = re.sub(r'[\\/:*?"<>|\n\r]+', "", text)
    text = re.sub(r"\s+", "", text.strip())
    return text[:max_len] or "untitled"


def make_output_dir(cfg: dict[str, Any], account: str, day: str, person: str, title: str) -> Path:
    name = f"{day}-{slug_title(person)}-{slug_title(title)}"
    path = content_root(cfg) / account / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def record_entry(cfg: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    ledger = load_ledger(cfg)
    collisions = colliding_quotes(entry.get("quotes") or [], ledger)
    if collisions:
        raise ValueError(
            "金句与历史重复: " + " | ".join(f"{a} ≈ {b}" for a, b in collisions[:5])
        )
    cool = on_cooldown(ledger, entry["account"], entry["person"])
    if cool and not entry.get("force") and not entry.get("same_interview_split"):
        raise ValueError(
            f"{entry['person']} 在 {entry['account']} 冷却中，"
            f"上次 {cool['last_date']}，直到 {cool['until']}"
        )
    entry = dict(entry)
    entry.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
    entry.pop("force", None)
    ledger.setdefault("entries", []).append(entry)
    save_ledger(cfg, ledger)
    return entry
