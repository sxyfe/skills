#!/usr/bin/env python3
"""从 watch-config 渲染 loop/cron Agent prompt。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import SKILL_ROOT, setup_scripts_path
from hotel_utils import HIGH_COST_THRESHOLD, estimate_api_calls

setup_scripts_path()

LOOP_TEMPLATE = SKILL_ROOT / "templates" / "loop-prompt.template.txt"
CRON_TEMPLATE = SKILL_ROOT / "templates" / "cron-agent-prompt.template.txt"


def render_loop_prompt(cfg: dict, config_path: Path, state_path: Path) -> str:
    schedule = cfg.get("schedule") or {}
    silent = schedule.get("silentUnlessTriggered", True)
    silent_rule = (
        "有触发才在对话里回复用户并格式化告警（用 templates/alert-message.template.md）；"
        "无触发则只更新 JSON，输出 NO_REPLY。"
        if silent
        else "每轮简要汇报查价摘要。"
    )
    est = estimate_api_calls(cfg)
    skill_root = SKILL_ROOT

    if LOOP_TEMPLATE.exists():
        tpl = LOOP_TEMPLATE.read_text(encoding="utf-8")
        return (
            tpl.replace("{{CONFIG_PATH}}", str(config_path))
            .replace("{{STATE_PATH}}", str(state_path))
            .replace("{{SILENT_RULE}}", silent_rule)
            .replace("{{SKILL_ROOT}}", str(skill_root))
            .replace("{{ESTIMATED_API}}", str(est["total"]))
            .replace("{{HIGH_COST_THRESHOLD}}", str(HIGH_COST_THRESHOLD))
        )

    return f"""执行 hotel-watch-agent 监控一轮。

1. 读配置：{config_path}
2. 读/写状态：{state_path}
3. 先运行预估（若用户未确认）：
   python3 {skill_root}/scripts/estimate_watch.py --config {config_path}
4. 向用户展示预估 API {est['total']} 次；超过阈值须确认后执行：
   python3 {skill_root}/scripts/run_watch_round.py --config {config_path} --state {state_path} --confirm
5. 若 triggered=true，按 alert-message 模板格式化三链告警；否则 {silent_rule}
"""


def render_cron_prompt(cfg: dict, config_path: Path, state_path: Path) -> str:
    schedule = cfg.get("schedule") or {}
    cron = schedule.get("cron", "0 8 * * *")
    interval = schedule.get("interval", "24h")
    skill_root = SKILL_ROOT
    slug = (cfg.get("meta") or {}).get("slug", "hotel-watch")

    if CRON_TEMPLATE.exists():
        tpl = CRON_TEMPLATE.read_text(encoding="utf-8")
        return (
            tpl.replace("{{SLUG}}", slug)
            .replace("{{CONFIG_PATH}}", str(config_path))
            .replace("{{STATE_PATH}}", str(state_path))
            .replace("{{SKILL_ROOT}}", str(skill_root))
            .replace("{{CRON}}", cron)
            .replace("{{INTERVAL}}", interval)
        )

    return f"""# {slug} · 外部 cron + Agent 定时监控

## crontab 示例（{cron}，约 {interval} 一次）

```bash
{ cron } /usr/bin/env bash -lc 'cursor agent --prompt "$(cat {config_path.parent}/{slug}-cron-prompt.txt)"' >> ~/.logs/{slug}-watch.log 2>&1
```

或先跑脚本、有告警再唤 Agent：

```bash
{ cron } python3 {skill_root}/scripts/run_watch_round.py --config {config_path} --state {state_path} --confirm --output /tmp/{slug}-round.json && \\
  if jq -e '.triggered' /tmp/{slug}-round.json >/dev/null; then \\
    cursor agent --prompt "读 /tmp/{slug}-round.json，按 hotel-watch-agent 告警模板回复用户"; \\
  fi
```

## Agent 每轮必做

1. `python3 {skill_root}/scripts/estimate_watch.py --config {config_path}`（配置变更时）
2. `python3 {skill_root}/scripts/run_watch_round.py --config {config_path} --state {state_path} --confirm`
3. 解析 stdout JSON：`triggered` 为 true 时格式化告警（携程/去哪儿/RollingGo 三链）
4. `silentUnlessTriggered=true` 且无触发 → 不打扰用户
"""


def render_combined_prompt(configs: list[tuple[Path, Path]], out_path: Path) -> str:
    blocks = ["# 多任务酒店监控（合并一轮）\n", "按顺序执行各任务；任一任务有触发则汇总回复。\n"]
    for i, (cfg_path, state_path) in enumerate(configs, 1):
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        slug = cfg.get("meta", {}).get("slug", cfg_path.stem)
        blocks.append(f"## {i}. {slug}\n")
        blocks.append(f"- 配置：`{cfg_path}`\n")
        blocks.append(f"- 状态：`{state_path}`\n")
        blocks.append(render_loop_prompt(cfg, cfg_path, state_path))
        blocks.append("\n---\n")
    text = "\n".join(blocks)
    out_path.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    p = argparse.ArgumentParser(description="渲染 loop/cron Agent prompt")
    p.add_argument("--config", "-c", type=Path)
    p.add_argument("--state", "-s", type=Path, help="默认 config.meta.stateFile")
    p.add_argument("--mode", choices=["loop", "cron", "both"], default="both")
    p.add_argument("-o", "--output-dir", type=Path, help="输出目录，默认 config 同目录")
    p.add_argument("--combine", nargs="+", type=Path, help="合并多个 config 路径")
    args = p.parse_args()

    if args.combine:
        pairs: list[tuple[Path, Path]] = []
        for cp in args.combine:
            cfg = json.loads(cp.read_text(encoding="utf-8"))
            sp = args.state or Path((cfg.get("meta") or {}).get("stateFile", ""))
            pairs.append((cp, sp))
        out_dir = args.output_dir or pairs[0][0].parent
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = "combined-hotel-watch"
        out = out_dir / f"{slug}-loop-prompt.txt"
        print(render_combined_prompt(pairs, out))
        print(f"已写入: {out}")
        return

    if not args.config:
        p.error("须指定 --config 或 --combine")

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    slug = (cfg.get("meta") or {}).get("slug", "hotel-watch")
    state_path = args.state or Path((cfg.get("meta") or {}).get("stateFile", f"{slug}-hotel-watch.json"))
    out_dir = args.output_dir or args.config.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in ("loop", "both"):
        lp = out_dir / f"{slug}-loop-prompt.txt"
        lp.write_text(render_loop_prompt(cfg, args.config, state_path), encoding="utf-8")
        print(f"已写入: {lp}")

    if args.mode in ("cron", "both"):
        cp = out_dir / f"{slug}-cron-prompt.txt"
        cp.write_text(render_cron_prompt(cfg, args.config, state_path), encoding="utf-8")
        print(f"已写入: {cp}")


if __name__ == "__main__":
    main()
