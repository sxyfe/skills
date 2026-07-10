#!/usr/bin/env python3
"""从 getHotelDetail 响应或 JSON 文件提取携程/去哪儿/RollingGo 链接。"""
from __future__ import annotations

import argparse
import json
import sys

from config import setup_scripts_path
from hotel_utils import classify_booking_links

setup_scripts_path()


def main() -> None:
    p = argparse.ArgumentParser(description="提取酒店下单三链")
    p.add_argument("input", help="getHotelDetail JSON 文件路径，或 - 表示 stdin")
    p.add_argument("--hotel-name", default="")
    p.add_argument("--city", default="")
    args = p.parse_args()
    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    detail = json.loads(raw)
    links = classify_booking_links(detail, args.hotel_name, args.city)
    print(json.dumps(links, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
