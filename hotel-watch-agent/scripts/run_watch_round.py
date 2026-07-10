#!/usr/bin/env python3
"""执行一轮酒店监控：MCP 查价 → 更新 state → 输出触发结果。"""
from __future__ import annotations

import argparse
import json
import math
import sys
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from config import ensure_api_key, setup_scripts_path
from hotel_utils import (
    HIGH_COST_THRESHOLD,
    alert_key,
    budget_for_hotel,
    checkout_from_checkin,
    empty_state,
    estimate_api_calls,
    evaluate_composite_triggers,
    evaluate_hotel_date_rules,
    evaluate_triggers,
    init_baseline_if_missing,
    parse_detail_snapshot,
    should_send_alert,
    triggers_for_hotel,
)
from rollinggo_client import RollingGoHotelClient

setup_scripts_path()

AVG_LATENCY_SEC = 1.2
CONCURRENCY = 3
TZ_CN = timezone(timedelta(hours=8))


def estimate_seconds(total: int) -> int:
    return max(1, math.ceil(total / CONCURRENCY) * AVG_LATENCY_SEC)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_state_path(cfg: dict[str, Any], explicit: Path | None) -> Path:
    if explicit:
        return explicit
    raw = (cfg.get("meta") or {}).get("stateFile")
    if not raw:
        raise SystemExit("未指定 --state 且 config.meta.stateFile 为空")
    return Path(raw).expanduser()


def build_search_args(cfg: dict[str, Any], check_in: str, tier_spec: dict[str, Any] | None) -> dict[str, Any]:
    meta = cfg.get("meta") or {}
    dates = cfg.get("dates") or {}
    occ = dates.get("occupancy") or {}
    search = cfg.get("search") or {}
    tier_search = (tier_spec or {}).get("search") or {}

    max_price = tier_search.get("maxPricePerNight") or tier_spec.get("maxPricePerNight")
    if max_price is None:
        max_price = (cfg.get("budget") or {}).get("maxPricePerNight")

    tags = tier_search.get("requiredTags") or search.get("requiredTags") or []
    place = meta.get("place") or (search.get("places") or [""])[0]
    place_type = search.get("placeType") or "城市"

    args: dict[str, Any] = {
        "countryCode": meta.get("countryCode", "CN"),
        "place": place,
        "placeType": place_type,
        "checkInParam": {
            "checkInDate": check_in,
            "stayNights": dates.get("stayNights", 1),
            "adultCount": occ.get("adultCount", 2),
        },
        "originQuery": (
            f"{meta.get('place', place)} {check_in} 入住"
            f"{dates.get('stayNights', 1)}晚，{occ.get('adultCount', 2)}成人"
        ),
        "size": search.get("size", 15),
    }
    if tags or max_price is not None:
        args["hotelTags"] = {}
        if tags:
            args["hotelTags"]["requiredTags"] = tags
        if max_price is not None:
            args["hotelTags"]["maxPricePerNight"] = max_price
    return args


def run_searches(client: RollingGoHotelClient, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    search_cfg = cfg.get("search") or {}
    if search_cfg.get("enabled") is False:
        return []

    dates = (cfg.get("dates") or {}).get("checkInDates") or []
    places = search_cfg.get("places") or [cfg.get("meta", {}).get("place", "")]
    places = [p for p in places if p]
    tiers = cfg.get("budgetTiers") or {}
    tier_specs = list(tiers.values()) if tiers else [None]
    results: list[dict[str, Any]] = []

    for check_in in dates:
        for place in places:
            for tier_spec in tier_specs:
                args = build_search_args(cfg, check_in, tier_spec)
                args["place"] = place
                try:
                    data = client.search_hotels(**args)
                    results.append({"checkIn": check_in, "place": place, "data": data})
                except Exception as exc:
                    results.append({"checkIn": check_in, "place": place, "error": str(exc)})
    return results


def fetch_details(client: RollingGoHotelClient, cfg: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    watchlist = cfg.get("watchlist") or {}
    dates = (cfg.get("dates") or {}).get("checkInDates") or []
    dates_cfg = cfg.get("dates") or {}
    stay = dates_cfg.get("stayNights", 1)
    occ = dates_cfg.get("occupancy") or {}
    prefs = cfg.get("roomPreferences")
    meta = cfg.get("meta") or {}
    city = meta.get("place", "")

    snapshots: dict[str, dict[str, dict[str, Any]]] = {}
    for hid, hotel in watchlist.items():
        snapshots[hid] = {}
        for check_in in dates:
            check_out = checkout_from_checkin(check_in, stay)
            try:
                detail = client.get_hotel_detail(
                    hotelId=int(hid),
                    dateParam={"checkInDate": check_in, "checkOutDate": check_out},
                    occupancyParam={
                        "adultCount": occ.get("adultCount", 2),
                        "roomCount": occ.get("roomCount", 1),
                        "childCount": occ.get("childCount", 0),
                    },
                    localeParam={
                        "countryCode": meta.get("countryCode", "CN"),
                        "currency": meta.get("currency", "CNY"),
                    },
                )
                snap = parse_detail_snapshot(
                    detail,
                    prefs=prefs,
                    hotel_tier=hotel.get("tier", ""),
                    hotel_name=hotel.get("name", ""),
                    city=city,
                )
            except Exception as exc:
                snap = {
                    "price": None,
                    "available": False,
                    "halfBoard": None,
                    "tier": hotel.get("tier", ""),
                    "error": str(exc),
                }
            snapshots[hid][check_in] = snap
    return snapshots


def process_round(cfg: dict[str, Any], state: dict[str, Any], snapshots: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    watchlist = cfg.get("watchlist") or {}
    alerts: list[dict[str, Any]] = []
    trigger_ids: list[str] = []
    alerts_sent = state.setdefault("alertsSent", [])
    composite_state = state.setdefault("compositeState", {})
    last_snapshot = state.setdefault("lastSnapshot", {})

    for hid, hotel in watchlist.items():
        tier = hotel.get("tier", "")
        tr = triggers_for_hotel(cfg, hid, tier)
        budget = budget_for_hotel(cfg, tier)
        for date, snap in (snapshots.get(hid) or {}).items():
            prev = (last_snapshot.get(hid) or {}).get(date)
            baseline = (state.get("baseline") or {}).get(hid, {}).get(date)

            for rule in evaluate_triggers(
                prev=prev, current=snap, baseline=baseline,
                triggers=tr, budget_max=budget,
            ):
                key = alert_key(hid, date, rule)
                if should_send_alert(alerts_sent, key, snap.get("price")):
                    alerts.append({
                        "key": key,
                        "rule": rule,
                        "priority": "high" if rule == "restock" else "medium",
                        "hotelId": hid,
                        "hotelName": hotel.get("name"),
                        "date": date,
                        "snapshot": snap,
                    })
                    trigger_ids.append(key)

            for item in evaluate_hotel_date_rules(cfg, hid, date, snap, baseline):
                key = alert_key(hid, date, item["id"])
                if should_send_alert(alerts_sent, key, snap.get("price")):
                    alerts.append({**item, "key": key, "hotelName": hotel.get("name"), "snapshot": snap})
                    trigger_ids.append(item["id"])

            init_baseline_if_missing(state, hid, date, snap)
            last_snapshot.setdefault(hid, {})[date] = {
                k: snap[k] for k in ("price", "available", "halfBoard", "tier", "matchedRoomPlan", "links", "bookingUrl")
                if k in snap
            }

    composite_fired = evaluate_composite_triggers(cfg, snapshots, composite_state=composite_state)
    for item in composite_fired:
        cid = item["id"]
        if not composite_state.get(cid, {}).get("satisfied"):
            alerts.append(item)
            trigger_ids.append(cid)
            composite_state[cid] = {"satisfied": True, "at": datetime.now(TZ_CN).isoformat()}

    now = datetime.now(TZ_CN).isoformat()
    for a in alerts:
        if "key" in a:
            alerts_sent.append({"key": a["key"], "at": now, "price": (a.get("snapshot") or {}).get("price")})

    state["lastRunTriggers"] = trigger_ids
    state.setdefault("meta", {})["lastCheckAt"] = now
    return {"alerts": alerts, "triggerCount": len(alerts), "triggerIds": trigger_ids}


def main() -> None:
    parser = argparse.ArgumentParser(description="执行一轮酒店价格监控")
    parser.add_argument("--config", "-c", type=Path, required=True)
    parser.add_argument("--state", "-s", type=Path, help="状态 JSON，默认读 config.meta.stateFile")
    parser.add_argument("--confirm", action="store_true", help=f"确认执行高成本监控（>{HIGH_COST_THRESHOLD} 次 API）")
    parser.add_argument("--estimate-only", action="store_true", help="仅预估，不查价")
    parser.add_argument("--skip-search", action="store_true", help="跳过 searchHotels 广度扫描")
    parser.add_argument("--output", "-o", type=Path, help="写入完整轮次结果 JSON")
    args = parser.parse_args()

    cfg = load_json(args.config)
    state_path = resolve_state_path(cfg, args.state)
    est = estimate_api_calls(cfg)
    if args.skip_search:
        est = {**est, "searchHotels": 0, "total": est["getHotelDetail"]}
    eta = estimate_seconds(est["total"])

    print(
        f"预估 API: {est['total']} 次（detail {est['getHotelDetail']} + search {est['searchHotels']}）| 约 {eta}s",
        flush=True,
    )

    if args.estimate_only:
        print(json.dumps({**est, "estimated_seconds": eta}, ensure_ascii=False, indent=2))
        return

    if est["total"] > HIGH_COST_THRESHOLD and not args.confirm:
        print(
            f"拒绝执行：预估 {est['total']} 次超过 {HIGH_COST_THRESHOLD}。"
            f"请向用户展示预估并加 --confirm 后重试。",
            file=sys.stderr,
        )
        sys.exit(1)

    settings = ensure_api_key()
    client = RollingGoHotelClient(settings)

    if state_path.exists():
        state = load_json(state_path)
    else:
        state = empty_state(cfg)

    search_results: list[dict[str, Any]] = []
    if not args.skip_search and (cfg.get("search") or {}).get("enabled", True):
        search_results = run_searches(client, cfg)

    snapshots = fetch_details(client, cfg)
    round_result = process_round(cfg, state, snapshots)
    state.setdefault("meta", {})["lastApiEstimate"] = est
    save_json(state_path, state)

    silent = (cfg.get("schedule") or {}).get("silentUnlessTriggered", True)
    payload = {
        "stateFile": str(state_path),
        "estimatedApi": est,
        "searchSummary": [{"checkIn": r.get("checkIn"), "place": r.get("place"), "error": r.get("error")} for r in search_results],
        "silentUnlessTriggered": silent,
        "triggered": round_result["triggerCount"] > 0,
        **round_result,
    }

    if args.output:
        save_json(args.output, payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if silent and round_result["triggerCount"] == 0:
        print("NO_ALERT: 无触发，已静默更新状态。", file=sys.stderr)
        sys.exit(0)
    if round_result["triggerCount"] > 0:
        sys.exit(0)


if __name__ == "__main__":
    main()
