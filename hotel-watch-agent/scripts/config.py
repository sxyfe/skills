"""Skill 根目录、配置与 RollingGo Key 加载（酒店 MCP）。"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "https://mcp.rollinggo.cn"
HOTEL_MCP_PATH = "/mcp"
KEY_APPLY_URL = "https://rollinggo.store/docs"
MAX_HOTELS_PER_TASK = 10


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str

    @property
    def hotel_mcp_url(self) -> str:
        return f"{self.base_url.rstrip("/")}{HOTEL_MCP_PATH}"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _token_from_mcp_json(server: str = "RollingGo-Hotel") -> str | None:
    mcp = Path.home() / ".cursor/mcp.json"
    if not mcp.exists():
        return None
    try:
        data = json.loads(mcp.read_text(encoding="utf-8"))
        auth = data["mcpServers"][server]["headers"]["Authorization"]
        return auth.split(" ", 1)[1]
    except (KeyError, IndexError, json.JSONDecodeError):
        return None


def load_settings() -> Settings:
    _load_dotenv(SKILL_ROOT / ".env")
    api_key = os.environ.get("ROLLINGGO_API_KEY") or _token_from_mcp_json() or ""
    base_url = (os.environ.get("ROLLINGGO_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    return Settings(api_key=api_key, base_url=base_url)


def missing_key_message() -> str:
    return (
        "未配置 RollingGo API Key。\n"
        f"1. 在 {KEY_APPLY_URL} 申请 Key（格式 mcp_...）\n"
        "2. 复制 .env.example 为 .env 并填入 ROLLINGGO_API_KEY\n"
        "   或配置 templates/mcp.json.example 到 Agent 的 MCP 设置\n"
        "3. 运行: python3 scripts/check_rollinggo_hotel.py"
    )


def ensure_api_key() -> Settings:
    settings = load_settings()
    if not settings.api_key:
        print(missing_key_message(), file=sys.stderr)
        sys.exit(1)
    return settings


def setup_scripts_path() -> None:
    p = str(SCRIPTS_DIR)
    if p not in sys.path:
        sys.path.insert(0, p)
