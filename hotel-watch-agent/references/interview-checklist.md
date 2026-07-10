# 分步需求访谈清单（全球通用）

信息不全时 **逐步询问**，不要一次抛出全部问题。

## 步骤 0 · 预设（可选）

| 预设 | 适用 |
|------|------|
| `generic-worldwide` | 任意国家/城市/商务或度假 |
| `jp-onsen-dual-tier` | 日本温泉 A/B 双层 |

```bash
python3 scripts/init_watch_config.py --preset jp-onsen-dual-tier -o ./output
```

## 步骤 1 · 地点与酒店

- **国家二字码**（JP / CN / US / TH …）
- 城市、温泉区、地标或具体酒店
- 监控清单：`hotelId:名称/tier`，**最多 10 家**
- `tier` 自定义标签，与 `budgetTiers.watchlistTiers` 对应（如 ryokan / chain / resort）

## 步骤 2 · 日期与人数

- 入住日列表（默认每入住日 **1 晚**，非连住）
- 成人数、房间数、儿童（可选）

## 步骤 3 · 预算

**单层**：每晚上限 CNY，用户自定。

**双层 A/B**（可选）：
- A 层：设施标签 + 较低预算（如公共温泉 ≤700）
- B 层：高优先级类型 + 较高预算（如 ryokan + 二食 ≤800）

## 步骤 4 · 房型偏好

| 用户说法 | 写入 keywords |
|----------|---------------|
| 大床/双床/海景/和室/床位/胶囊 | 同名或见 room-type-matching.md |

## 步骤 5 · 通知阈值

- 单层：`triggers.*`
- 双层：各 tier 自带 triggers，全局可补 restock
- **组合**：是否启用 `distinct-hotels-per-night`（跨晚凑不同酒店）

## 步骤 6 · 单酒店特例（可选）

`hotelOverrides`：售罄高优先级、指定日期目标价。

## 步骤 7 · 定时（外部 cron + Agent）

- 间隔建议 ≥12h，推荐 24h
- `silentUnlessTriggered`：有触发才回复
- 产出 `{slug}-loop-prompt.txt` 与 `{slug}-cron-prompt.txt`

## 步骤 8 · API 预估与确认

**Agent MUST**（与 flight-monitor-agent 一致）：

1. 运行 `estimate_watch.py --config ... --json`
2. 向用户展示预估 API 次数与约计耗时
3. 超过 **100 次** 且无用户明确确认 → **拒绝执行** `run_watch_round.py`
4. 用户确认后加 `--confirm` 执行

CLI 向导：`python3 scripts/init_watch_config.py`
