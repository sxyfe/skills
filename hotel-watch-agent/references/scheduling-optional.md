# 定时任务：外部 cron + Agent

Skill **不绑定** IM。推荐 **外部 cron 触发 + Agent 格式化告警/处理异常**。

## 产出物

| 文件 | 说明 |
|------|------|
| `{slug}-watch-config.json` | 监控参数（只读） |
| `{slug}-hotel-watch.json` | 运行时 state |
| `{slug}-loop-prompt.txt` | Agent 每轮指令 |
| `{slug}-cron-prompt.txt` | crontab 安装说明 |

生成：

```bash
python3 scripts/render_loop_prompt.py --config path/to/watch-config.json --mode both
```

多任务合并：

```bash
python3 scripts/render_loop_prompt.py --combine cfg-a.json cfg-b.json -o ./data
```

## 推荐架构

```
┌──────────┐     cron      ┌─────────────────────┐
│ crontab  │──────────────▶│ run_watch_round.py  │
└──────────┘               │  (--confirm)        │
                           └──────────┬──────────┘
                                      │
                           triggered? │
                              yes     │     no
                               ▼      │      ▼
                    ┌──────────────┐  │  静默写 state
                    │ Agent CLI    │  │
                    │ 格式化三链告警│  │
                    └──────────────┘  │
```

## 方式 A · 脚本优先（省 token）

```bash
0 8 * * * python3 .../run_watch_round.py -c ... -s ... --confirm -o /tmp/round.json && \
  jq -e '.triggered' /tmp/round.json && cursor agent --prompt "读 /tmp/round.json 发告警"
```

## 方式 B · 全 Agent 每轮

cron 唤起 Agent，粘贴 `{slug}-loop-prompt.txt` 内容；Agent 自行 estimate → confirm → run → 格式化。

适用于：需人工判断 plan 含餐、MCP 异常重试、组合触发说明。

## Agent 接入示例

| 环境 | 唤起方式 |
|------|----------|
| Cursor | `cursor agent --prompt "$(cat loop-prompt.txt)"` |
| Claude Code | 项目 cron + 同一 prompt 文件 |
| OpenClaw / QClaw | cron + skill 名 `hotel-watch-agent` |
| Codex | `crontab` + CLI |

## 建议

- 间隔 ≥12h，推荐 24h（`schedule.cron`: `0 8 * * *`）
- 每轮 API ≈ 酒店数 × 晚数 + search 扫描；**必须先 estimate 再 confirm**
- 启用 `silentUnlessTriggered` 减少无效打扰

## 与 Cursor /loop 的关系

Cursor 内置 `/loop` 仍可用（读 loop-prompt.txt），但 **外部 cron 更稳定**、不依赖 IDE 常开。
