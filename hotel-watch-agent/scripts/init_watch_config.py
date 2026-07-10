#!/usr/bin/env python3
"""分步 CLI 访谈，生成 watch-config.json、loop/cron prompt 与初始 state。"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config import MAX_HOTELS_PER_TASK, SKILL_ROOT, setup_scripts_path
from hotel_utils import empty_state, estimate_api_calls, HIGH_COST_THRESHOLD

setup_scripts_path()


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def ask_yes(prompt: str, default: bool = False) -> bool:
    d = "Y/n" if default else "y/N"
    val = input(f"{prompt} ({d}): ").strip().lower()
    if not val:
        return default
    return val in ("y", "yes", "是")


def parse_dates(raw: str) -> list[str]:
    return [d.strip() for d in raw.replace("，", ",").split(",") if d.strip()]


def parse_hotel_ids(raw: str) -> dict[str, dict]:
    wl: dict[str, dict] = {}
    for part in raw.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            hid, rest = part.split(":", 1)
            if "/" in rest:
                name, tier = rest.rsplit("/", 1)
            else:
                name, tier = rest, "unknown"
        else:
            hid, name, tier = part, f"Hotel {part}", "unknown"
        wl[hid.strip()] = {"name": name.strip(), "tier": tier.strip()}
    return wl


def load_preset(name: str) -> dict:
    path = SKILL_ROOT / "templates" / "presets" / f"{name}.json"
    if not path.exists():
        print(f"预设不存在: {path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def run_interactive(out_dir: Path, preset: dict | None = None) -> Path:
    print("\n=== 酒店价格监控 · 分步配置（全球通用）===\n")

    if preset:
        print(f"已加载预设: {preset.get('meta', {}).get('note', '')}\n")

    country = ask("1. 国家二字码（ISO，如 JP/CN/US）", (preset or {}).get("meta", {}).get("countryCode", "JP"))
    place = ask("   城市/区域/酒店地标", (preset or {}).get("meta", {}).get("place", ""))
    hotel_raw = ask("   监控酒店（hotelId:名称/tier，逗号分隔，最多10家）", "")
    watchlist = parse_hotel_ids(hotel_raw)
    if len(watchlist) > MAX_HOTELS_PER_TASK:
        print(f"错误：超过 {MAX_HOTELS_PER_TASK} 家，请删减或拆成多个任务。", file=sys.stderr)
        sys.exit(1)

    dates_raw = ask("2. 入住日（逗号分隔，每入住日查 1 晚）", "")
    check_ins = parse_dates(dates_raw)
    adults = int(ask("   成人数", "2") or "2")
    rooms = int(ask("   房间数", "1") or "1")

    dual_tier = ask_yes("3. 是否使用 A/B 双层预算（如公共温泉 vs 传统旅馆）", bool(preset and preset.get("budgetTiers")))
    budget_tiers = None
    budget_single = None
    if dual_tier:
        a_max = float(ask("   A 层每晚上限（CNY）", "700") or "700")
        b_max = float(ask("   B 层每晚上限（CNY）", "800") or "800")
        a_tags = ask("   A 层 search 必选标签（逗号，可空）", "公共温泉")
        budget_tiers = {
            "A": {
                "label": "A层",
                "maxPricePerNight": a_max,
                "watchlistTiers": ["onsen-hotel", "resort", "chain"],
                "triggers": {"priceBelow": a_max, "dropAmount": 50, "dropPercent": 10, "restock": True},
                "search": {"requiredTags": [t.strip() for t in a_tags.split(",") if t.strip()], "maxPricePerNight": a_max},
            },
            "B": {
                "label": "B层",
                "maxPricePerNight": b_max,
                "watchlistTiers": ["ryokan"],
                "triggers": {"priceBelow": b_max, "dropAmount": 50, "dropPercent": 10, "restock": True, "halfBoard": True},
                "search": {"maxPricePerNight": b_max},
            },
        }
    else:
        budget = ask("3. 每晚价格上限（CNY）", "")
        budget_single = float(budget) if budget else None

    room_kw = ask("4. 房型关键词（逗号，可空；大床/双床/海景/和室等）", "")
    room_ex = ask("   排除关键词（可空）", "")

    print("\n5. 通知阈值（全局默认；双层时各 tier 已含部分规则）")
    restock = ask_yes("   监控售罄→有房", True)
    drop_amt = ask("   降价 ≥（元，可空）", "50")
    drop_pct = ask("   降价 ≥（%，可空）", "10")
    half_board = ask_yes("   含二食 plan 告警（单层或未用 B 层时）", False)

    composite = ask_yes("\n6. 启用组合触发（跨晚凑齐不同酒店）", dual_tier)
    composite_triggers = []
    if composite:
        composite_triggers.append({
            "id": f"{place or 'watch'}-distinct-nights",
            "type": "distinct-hotels-per-night",
            "priority": "medium",
            "watchlistTiers": ["ryokan"] if dual_tier else None,
            "maxPricePerNight": budget_tiers["B"]["maxPricePerNight"] if budget_tiers else budget_single,
            "minDistinct": len(check_ins),
            "requireHalfBoard": dual_tier,
        })

    schedule = ask_yes("\n7. 是否配置定时监控（外部 cron + Agent）", False)
    interval = "24h"
    cron = "0 8 * * *"
    silent = True
    if schedule:
        interval = ask("8. 定时间隔描述（如 12h / 24h）", "24h")
        cron = ask("   cron 表达式", "0 8 * * *")
        silent = ask_yes("   无触发时静默", True)

    slug = ask("\n任务 slug（文件名）", place.replace(" ", "-") or "hotel-watch")
    config_path = out_dir / f"{slug}-watch-config.json"
    state_path = out_dir / f"{slug}-hotel-watch.json"

    triggers: dict = {}
    if not dual_tier:
        if budget_single is not None:
            triggers["priceBelow"] = budget_single
        if drop_amt:
            triggers["dropAmount"] = float(drop_amt)
        if drop_pct:
            triggers["dropPercent"] = float(drop_pct)
        if restock:
            triggers["restock"] = True
        if half_board:
            triggers["halfBoard"] = True
    elif restock:
        triggers["restock"] = True

    cfg = {
        "meta": {
            "slug": slug,
            "maxHotels": MAX_HOTELS_PER_TASK,
            "createdAt": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "place": place,
            "countryCode": country,
            "currency": "CNY",
            "stateFile": str(state_path),
            "configFile": str(config_path),
        },
        "watchlist": watchlist,
        "dates": {
            "checkInDates": check_ins,
            "stayNights": 1,
            "occupancy": {"adultCount": adults, "roomCount": rooms},
        },
        "roomPreferences": {
            "keywords": [k.strip() for k in room_kw.split(",") if k.strip()],
            "excludeKeywords": [k.strip() for k in room_ex.split(",") if k.strip()],
            "matchFields": ["roomName", "roomNameCn", "bedTypeDescription", "ratePlanName"],
        },
        "triggers": triggers,
        "compositeTriggers": composite_triggers,
        "hotelOverrides": {},
        "schedule": {
            "enabled": schedule,
            "interval": interval,
            "silentUnlessTriggered": silent,
            "cron": cron,
        },
        "search": {
            "enabled": True,
            "placeType": ask("search placeType（城市/景点/酒店等）", "城市"),
            "places": [place] if place else [],
            "size": 15,
        },
    }
    if budget_tiers:
        cfg["budgetTiers"] = budget_tiers
    else:
        cfg["budget"] = {"maxPricePerNight": budget_single}

    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已写入: {config_path}")

    if not state_path.exists():
        state_path.write_text(json.dumps(empty_state(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"已初始化状态: {state_path}")

    est = estimate_api_calls(cfg)
    print(f"\n预估每轮 API: {est['total']} 次（detail {est['getHotelDetail']} + search {est['searchHotels']}）")
    if est["total"] > HIGH_COST_THRESHOLD:
        print(f"⚠ 超过 {HIGH_COST_THRESHOLD} 次，执行监控前须用户确认并加 --confirm")

    if schedule:
        import subprocess
        subprocess.run([
            sys.executable,
            str(SKILL_ROOT / "scripts" / "render_loop_prompt.py"),
            "--config", str(config_path),
            "--state", str(state_path),
            "--output-dir", str(out_dir),
        ], check=False)

    return config_path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output-dir", default=str(SKILL_ROOT / "output"))
    p.add_argument("--preset", choices=["generic-worldwide", "jp-onsen-dual-tier"], help="从预设壳开始")
    args = p.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    preset = load_preset(args.preset) if args.preset else None
    run_interactive(out, preset)


if __name__ == "__main__":
    main()
