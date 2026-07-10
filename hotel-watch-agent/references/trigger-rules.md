# 触发规则

## 单层触发（hotel × date）

对比 `lastSnapshot`（优先）与 `baseline`，规则来自 `triggers` + `budgetTiers[].triggers` + `hotelOverrides[].triggers`。

| 规则 | 配置键 | 条件 |
|------|--------|------|
| 售罄回补 | `restock: true` | 上轮 `available=false` → 本轮有价且 ≤ tier 预算 |
| 绝对价 | `priceBelow` | 最低价 ≤ 阈值 |
| 降幅金额 | `dropAmount` | 较上轮/baseline 降 ≥ N 元 |
| 降幅比例 | `dropPercent` | 降 ≥ N% |
| 含二食 | `halfBoard: true` | plan 命中二食关键词且 ≤ 预算 |

## 双层 budgetTiers

`watchlist.tier` 命中 `budgetTiers.*.watchlistTiers` 时，使用该层的 `maxPricePerNight` 与 `triggers`。

示例：A 层 chain/resort ≤700；B 层 ryokan ≤800 + halfBoard。

## 组合触发 compositeTriggers

### distinct-hotels-per-night

每个入住日各选一家 **不同** 酒店，均满足 tier/价格/含餐约束；`minDistinct` 默认为入住日数量。

用途：「四晚凑齐四家不同传统旅馆且均 ≤800」。

### all-nights-same-hotel-below

同一酒店在所有入住日均 ≤ 预算。

### hotel-date-price-cross

指定 `hotelId` + `date`，价格 ≤ `targetPrice`，且 baseline ≥ `fromPriceMin`（可选）。

亦可通过 `hotelOverrides.dateRules` 配置单晚特例。

## 优先级

告警可标注 `high` / `medium` / `low`（restock、hotel-date-price-cross 默认 high）。

## 静默与防重复

- `schedule.silentUnlessTriggered: true` → 无触发只写 state
- `alertsSent` 按 `hotelId|date|rule` 去重；价格继续下降可再次触发 drop 类规则

## 离线测试

```bash
python3 scripts/evaluate_triggers.py --config watch-config.json --state state.json \
  --hotel-id 617324 --date 2027-02-08 --price 750 --available
```

组合触发需跑完整轮：`run_watch_round.py --estimate-only` 后 `--confirm`。
