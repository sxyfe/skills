#!/usr/bin/env python3
"""RollingGo 酒店 MCP 连通性自检。"""
from __future__ import annotations

import sys
import urllib.error

from config import ensure_api_key, setup_scripts_path
from rollinggo_client import RollingGoHotelClient

setup_scripts_path()


def main() -> None:
    settings = ensure_api_key()
    client = RollingGoHotelClient(settings)
    try:
        data = client.get_hotel_search_tags()
        tags = data if isinstance(data, list) else data.get("tags") or data.get("data") or []
        count = len(tags) if isinstance(tags, list) else 1
        print(f"OK: RollingGo 酒店 MCP 连通正常（getHotelSearchTags 返回 {count} 项）")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"连接失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
