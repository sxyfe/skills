"""RollingGo 酒店 MCP HTTP 客户端。"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from config import Settings


class RollingGoHotelClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        }).encode()
        req = urllib.request.Request(
            self._settings.hotel_mcp_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self._settings.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read())
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        text = payload["result"]["content"][0]["text"]
        return json.loads(text)

    def get_hotel_search_tags(self) -> Any:
        return self.call("getHotelSearchTags", {})

    def search_hotels(self, **kwargs: Any) -> Any:
        return self.call("searchHotels", kwargs)

    def get_hotel_detail(self, **kwargs: Any) -> Any:
        return self.call("getHotelDetail", kwargs)
