"""房型匹配、plan 解析、触发判定、API 预估、组合触发。"""
from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

HALF_BOARD_KEYWORDS = (
    "一泊二食", "二食", "2食", "夕食", "会席", "dinner", "half board",
    "breakfast and dinner", "full board",
)

ROOM_TYPE_PRESETS: dict[str, list[str]] = {
    "大床": ["大床", "king", "double bed", "1 大床", "queen"],
    "双床": ["双床", "twin", "2 单人床", "2 single"],
    "海景": ["海景", "sea view", "seaside", "ocean"],
    "和室": ["和室", "日式", "japanese-style", "japanese style", "tatami"],
    "床位": ["床位", "round bed"],
    "胶囊": ["胶囊", "capsule"],
}

HIGH_COST_THRESHOLD = 100


def checkout_from_checkin(check_in: str, stay_nights: int = 1) -> str:
    d = datetime.strptime(check_in, "%Y-%m-%d").date()
    return (d + timedelta(days=stay_nights)).isoformat()


def plan_text(plan: dict[str, Any]) -> str:
    parts = [
        plan.get("roomName") or "",
        plan.get("roomNameCn") or "",
        plan.get("ratePlanName") or "",
        plan.get("bedTypeDescription") or "",
    ]
    return " ".join(p for p in parts if p).lower()


def matches_room_preferences(plan: dict[str, Any], prefs: dict[str, Any] | None) -> bool:
    if not prefs:
        return True
    text = plan_text(plan)
    for ex in prefs.get("excludeKeywords") or []:
        if ex.lower() in text:
            return False
    keywords = prefs.get("keywords") or []
    if not keywords:
        return True
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in text:
            return True
        for aliases in ROOM_TYPE_PRESETS.values():
            if kw in aliases or kw_lower in [a.lower() for a in aliases]:
                if any(a.lower() in text for a in aliases):
                    return True
    return False


def detect_half_board(plan: dict[str, Any]) -> bool:
    name = (plan.get("ratePlanName") or "").lower()
    if any(k in name for k in ("room only", "basic", "bedsonly", "素泊", "breakfast only")):
        return False
    combined = plan_text(plan)
    return any(k.lower() in combined for k in HALF_BOARD_KEYWORDS)


def pick_best_plan(plans: list[dict[str, Any]], prefs: dict[str, Any] | None) -> dict[str, Any] | None:
    eligible = [p for p in plans if p.get("totalPrice") is not None and matches_room_preferences(p, prefs)]
    if not eligible:
        return None
    return min(eligible, key=lambda p: float(p["totalPrice"]))


def rollinggo_detail_url(hotel_id, check_in, check_out, adult_count=2, room_count=1) -> str:
    return (
        f"https://rollinggo.cn/pages/hotel/detail/index"
        f"?id={hotel_id}&checkInDate={check_in}&checkOutDate={check_out}"
        f"&roomCount={room_count}&adultCount={adult_count}"
    )


def extract_urls_from_obj(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, str) and obj.startswith("http"):
        found.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            found.extend(extract_urls_from_obj(v))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(extract_urls_from_obj(item))
    return found


def classify_booking_links(detail: dict[str, Any], hotel_name: str = "", city: str = "") -> dict[str, str | None]:
    urls = extract_urls_from_obj(detail)
    rollinggo = detail.get("bookingUrl")
    ctrip = next((u for u in urls if "ctrip.com" in u or "trip.com" in u), None)
    qunar = next((u for u in urls if "qunar.com" in u), None)
    if not rollinggo and detail.get("hotelId"):
        check_in = detail.get("checkIn", "")
        check_out = detail.get("checkOut", "")
        if check_in and check_out:
            rollinggo = rollinggo_detail_url(detail["hotelId"], check_in, check_out)
    if not ctrip and hotel_name:
        q = re.sub(r"\s+", "+", f"{hotel_name} {city}".strip())
        ctrip = f"https://hotels.ctrip.com/hotels/list?keyword={q}"
    if not qunar and hotel_name:
        qunar = f"https://hotel.qunar.com/city/jp/#fromDate={detail.get('checkIn', '')}"
    return {"ctrip": ctrip, "qunar": qunar, "rollinggo": rollinggo}


def parse_detail_snapshot(
    detail: dict[str, Any],
    *,
    prefs: dict[str, Any] | None,
    hotel_tier: str = "",
    hotel_name: str = "",
    city: str = "",
) -> dict[str, Any]:
    plans = detail.get("roomRatePlans") or []
    best = pick_best_plan(plans, prefs)
    links = classify_booking_links(detail, hotel_name, city)
    if not best:
        return {
            "price": None,
            "available": False,
            "halfBoard": None,
            "tier": hotel_tier,
            "matchedRoomPlan": None,
            "links": links,
            "bookingUrl": links.get("rollinggo") or detail.get("bookingUrl"),
        }
    hb = detect_half_board(best)
    return {
        "price": float(best["totalPrice"]),
        "available": True,
        "halfBoard": hb,
        "tier": hotel_tier,
        "matchedRoomPlan": {
            "roomNameCn": best.get("roomNameCn"),
            "ratePlanName": best.get("ratePlanName"),
            "totalPrice": best.get("totalPrice"),
            "bedTypeDescription": best.get("bedTypeDescription"),
        },
        "links": links,
        "bookingUrl": links.get("rollinggo") or detail.get("bookingUrl"),
    }


def _merge_triggers(*layers: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for layer in layers:
        if not layer:
            continue
        merged.update({k: v for k, v in layer.items() if v is not None})
    return merged


def resolve_tier_key(cfg: dict[str, Any], hotel_tier: str) -> str | None:
    tiers = cfg.get("budgetTiers") or {}
    if not tiers:
        return None
    for key, spec in tiers.items():
        allowed = spec.get("watchlistTiers") or []
        if hotel_tier in allowed:
            return key
    return None


def budget_for_hotel(cfg: dict[str, Any], hotel_tier: str) -> float | None:
    tier_key = resolve_tier_key(cfg, hotel_tier)
    if tier_key:
        return (cfg["budgetTiers"][tier_key].get("maxPricePerNight"))
    return (cfg.get("budget") or {}).get("maxPricePerNight")


def triggers_for_hotel(cfg: dict[str, Any], hotel_id: str, hotel_tier: str) -> dict[str, Any]:
    global_tr = cfg.get("triggers") or {}
    tier_tr: dict[str, Any] = {}
    tier_key = resolve_tier_key(cfg, hotel_tier)
    if tier_key:
        tier_tr = (cfg["budgetTiers"][tier_key].get("triggers") or {})
    override_tr = ((cfg.get("hotelOverrides") or {}).get(hotel_id) or {}).get("triggers") or {}
    return _merge_triggers(global_tr, tier_tr, override_tr)


def hotel_matches_tiers(hotel_tier: str, allowed: list[str] | None) -> bool:
    if not allowed:
        return True
    return hotel_tier in allowed


def evaluate_triggers(*, prev, current, baseline, triggers, budget_max) -> list[str]:
    fired: list[str] = []
    price = current.get("price")
    available = current.get("available")
    prev_avail = (prev or {}).get("available")
    prev_price = (prev or {}).get("price")

    if triggers.get("restock") and prev_avail is False and available and price is not None:
        if budget_max is None or price <= budget_max:
            fired.append("restock")

    if triggers.get("priceBelow") is not None and price is not None:
        if price <= triggers["priceBelow"]:
            fired.append("price-below")

    ref_price = prev_price if prev_price is not None else (baseline or {}).get("price")
    if price is not None and ref_price is not None:
        drop = ref_price - price
        if triggers.get("dropAmount") is not None and drop >= triggers["dropAmount"]:
            fired.append("drop-amount")
        if triggers.get("dropPercent") is not None and ref_price > 0:
            if drop / ref_price * 100 >= triggers["dropPercent"]:
                fired.append("drop-percent")

    if triggers.get("halfBoard") and current.get("halfBoard") is True:
        if price is not None and (budget_max is None or price <= budget_max):
            fired.append("half-board")

    return fired


def alert_key(hotel_id: str, date: str, rule: str) -> str:
    return f"{hotel_id}|{date}|{rule}"


def should_send_alert(
    alerts_sent: list[dict[str, Any]],
    key: str,
    price: float | None,
    *,
    allow_price_drop_repeat: bool = True,
) -> bool:
    for item in alerts_sent:
        if item.get("key") != key:
            continue
        if not allow_price_drop_repeat:
            return False
        prev_price = item.get("price")
        if price is not None and prev_price is not None and price < prev_price:
            return True
        return False
    return True


def evaluate_hotel_date_rules(
    cfg: dict[str, Any],
    hotel_id: str,
    date: str,
    current: dict[str, Any],
    baseline: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """单酒店单日晚特例（hotelOverrides.dateRules + composite hotel-date-price-cross）。"""
    fired: list[dict[str, Any]] = []
    override = (cfg.get("hotelOverrides") or {}).get(hotel_id) or {}
    date_rule = (override.get("dateRules") or {}).get(date) or {}
    price = current.get("price")
    base_price = (baseline or {}).get("price")

    target = date_rule.get("targetPrice")
    from_min = date_rule.get("fromPriceMin")
    if target is not None and price is not None and price <= target:
        if from_min is None or (base_price is not None and base_price >= from_min):
            fired.append({
                "id": f"override-{hotel_id}-{date}",
                "type": "hotel-date-price-cross",
                "priority": date_rule.get("priority", "high"),
                "hotelId": hotel_id,
                "date": date,
                "price": price,
                "targetPrice": target,
            })

    for ct in cfg.get("compositeTriggers") or []:
        if ct.get("type") != "hotel-date-price-cross":
            continue
        if str(ct.get("hotelId")) != str(hotel_id):
            continue
        if ct.get("date") and ct["date"] != date:
            continue
        target_p = ct.get("targetPrice")
        from_p = ct.get("fromPriceMin")
        if target_p is not None and price is not None and price <= target_p:
            if from_p is None or (base_price is not None and base_price >= from_p):
                fired.append({
                    "id": ct["id"],
                    "type": ct["type"],
                    "priority": ct.get("priority", "high"),
                    "hotelId": hotel_id,
                    "date": date,
                    "price": price,
                    "targetPrice": target_p,
                })
    return fired


def evaluate_composite_triggers(
    cfg: dict[str, Any],
    snapshots: dict[str, dict[str, dict[str, Any]]],
    *,
    composite_state: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """跨晚/跨酒店组合触发。snapshots: hotelId -> date -> snapshot"""
    fired: list[dict[str, Any]] = []
    dates = (cfg.get("dates") or {}).get("checkInDates") or []
    watchlist = cfg.get("watchlist") or {}

    for ct in cfg.get("compositeTriggers") or []:
        ctype = ct.get("type")
        cid = ct.get("id", ctype)

        if ctype == "distinct-hotels-per-night":
            min_distinct = ct.get("minDistinct") or len(dates)
            max_price = ct.get("maxPricePerNight")
            allowed_tiers = ct.get("watchlistTiers") or ([ct["tier"]] if ct.get("tier") else None)
            require_hb = ct.get("requireHalfBoard", False)

            assignment: dict[str, str] = {}
            used: set[str] = set()
            ok = True
            for d in dates:
                candidates: list[tuple[str, float]] = []
                for hid, meta in watchlist.items():
                    if hid in used:
                        continue
                    tier = meta.get("tier", "")
                    if not hotel_matches_tiers(tier, allowed_tiers):
                        continue
                    snap = (snapshots.get(hid) or {}).get(d) or {}
                    if not snap.get("available") or snap.get("price") is None:
                        continue
                    if require_hb and snap.get("halfBoard") is not True:
                        continue
                    price = float(snap["price"])
                    tier_max = budget_for_hotel(cfg, tier)
                    cap = max_price if max_price is not None else tier_max
                    if cap is not None and price > cap:
                        continue
                    candidates.append((hid, price))
                if not candidates:
                    ok = False
                    break
                candidates.sort(key=lambda x: x[1])
                pick = candidates[0][0]
                assignment[d] = pick
                used.add(pick)

            if ok and len(used) >= min_distinct:
                prev_ok = (composite_state or {}).get(cid, {}).get("satisfied")
                if not prev_ok:
                    fired.append({
                        "id": cid,
                        "type": ctype,
                        "priority": ct.get("priority", "medium"),
                        "assignment": assignment,
                        "distinctCount": len(used),
                    })

        elif ctype == "all-nights-same-hotel-below":
            max_price = ct.get("maxPricePerNight")
            allowed_tiers = ct.get("watchlistTiers") or ([ct["tier"]] if ct.get("tier") else None)
            for hid, meta in watchlist.items():
                tier = meta.get("tier", "")
                if not hotel_matches_tiers(tier, allowed_tiers):
                    continue
                cap = max_price if max_price is not None else budget_for_hotel(cfg, tier)
                if cap is None:
                    continue
                all_ok = True
                for d in dates:
                    snap = (snapshots.get(hid) or {}).get(d) or {}
                    if not snap.get("available") or snap.get("price") is None:
                        all_ok = False
                        break
                    if float(snap["price"]) > cap:
                        all_ok = False
                        break
                if all_ok:
                    prev_ok = (composite_state or {}).get(f"{cid}:{hid}", {}).get("satisfied")
                    if not prev_ok:
                        fired.append({
                            "id": f"{cid}:{hid}",
                            "type": ctype,
                            "priority": ct.get("priority", "medium"),
                            "hotelId": hid,
                            "hotelName": meta.get("name"),
                            "maxPrice": cap,
                        })
    return fired


def estimate_api_calls(cfg: dict[str, Any]) -> dict[str, int]:
    watchlist = cfg.get("watchlist") or {}
    dates = (cfg.get("dates") or {}).get("checkInDates") or []
    n_hotels = len(watchlist)
    n_dates = len(dates)
    detail_calls = n_hotels * n_dates

    search_cfg = cfg.get("search") or {}
    search_enabled = search_cfg.get("enabled", True)
    search_calls = 0
    if search_enabled:
        places = search_cfg.get("places") or [cfg.get("meta", {}).get("place", "")]
        places = [p for p in places if p]
        tiers = cfg.get("budgetTiers") or {}
        scans_per_date = max(1, len(tiers)) if tiers else 1
        search_calls = n_dates * len(places) * scans_per_date

    total = detail_calls + search_calls
    return {
        "getHotelDetail": detail_calls,
        "searchHotels": search_calls,
        "total": total,
        "hotels": n_hotels,
        "dates": n_dates,
    }


def empty_state(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    slug = (cfg or {}).get("meta", {}).get("slug", "")
    return {
        "meta": {"version": 2, "slug": slug, "lastCheckAt": None},
        "baseline": {},
        "lastSnapshot": {},
        "alertsSent": [],
        "lastRunTriggers": [],
        "compositeState": {},
    }


def init_baseline_if_missing(state: dict[str, Any], hotel_id: str, date: str, snap: dict[str, Any]) -> None:
    base = state.setdefault("baseline", {})
    hotel_base = base.setdefault(hotel_id, {})
    if date not in hotel_base and snap.get("available") and snap.get("price") is not None:
        hotel_base[date] = deepcopy(snap)
