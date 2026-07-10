#!/usr/bin/env python3
"""预估监控任务 API 次数与耗时（不调用 MCP）。"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from config import setup_scripts_path
from hotel_utils import HIGH_COST_THRESHOLD, estimate_api_calls

setup_scripts_path()

AVG_LATENCY_SEC = 1.2
CONCURRENCY = 3


def estimate_seconds(total: int) -> int:
    return max(1, math.ceil(total / CONCURRENCY) * AVG_LATENCY_SEC)


def main() -> None:
    p = argparse.ArgumentParser(description="预估酒店监控 API 次数")
    p.add_argument("--config", "-c", type=Path, required=True)
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    est = estimate_api_calls(cfg)
    eta = estimate_seconds(est["total"])
    over_threshold = est["total"] > HIGH_COST_THRESHOLD

    payload = {
        **est,
        "estimated_seconds": eta,
        "high_cost_threshold": HIGH_COST_THRESHOLD,
        "requires_confirm": over_threshold,
        "summary_zh": (
            f"预估 API {est['total']} 次（getHotelDetail {est['getHotelDetail']} + "
            f"searchHotels {est['searchHotels']}），约 {eta}s"
        ),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["summary_zh"])
        if over_threshold:
            print(
                f"⚠ 超过 {HIGH_COST_THRESHOLD} 次，执行前须加 --confirm",
                file=sys.stderr,
            )

    sys.exit(0 if not over_threshold else 2)


if __name__ == "__main__":
    main()
