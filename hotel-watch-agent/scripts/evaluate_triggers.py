#!/usr/bin/env python3
"""读取 watch-config + state，评估是否触发（不调用 MCP）。"""
from __future__ import annotations

import argparse
import json
import sys

from config import setup_scripts_path
from hotel_utils import (
    budget_for_hotel,
    evaluate_triggers,
    triggers_for_hotel,
)

setup_scripts_path()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--hotel-id", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--price", type=float)
    p.add_argument("--available", action="store_true")
    p.add_argument("--half-board", action="store_true")
    args = p.parse_args()

    cfg = json.loads(open(args.config, encoding="utf-8").read())
    state = json.loads(open(args.state, encoding="utf-8").read())
    hotel_tier = (cfg.get("watchlist") or {}).get(args.hotel_id, {}).get("tier", "")
    triggers = triggers_for_hotel(cfg, args.hotel_id, hotel_tier)
    budget = budget_for_hotel(cfg, hotel_tier)

    prev = (state.get("lastSnapshot") or {}).get(args.hotel_id, {}).get(args.date)
    baseline = (state.get("baseline") or {}).get(args.hotel_id, {}).get(args.date)
    current = {
        "price": args.price,
        "available": args.available,
        "halfBoard": args.half_board,
    }
    fired = evaluate_triggers(
        prev=prev, current=current, baseline=baseline,
        triggers=triggers, budget_max=budget,
    )
    print(json.dumps({"fired": fired}, ensure_ascii=False))


if __name__ == "__main__":
    main()
